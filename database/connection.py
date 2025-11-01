"""
Database Connection Management
Handles PostgreSQL/TimescaleDB and Redis connections
"""
import asyncio
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager
import redis.asyncio as aioredis
from loguru import logger

from config import get_settings
from .models import Base, create_all_tables


class DatabaseManager:
    """
    Manages database connections for both sync and async operations
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection string (uses settings if not provided)
        """
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url
        
        # Convert postgres:// to postgresql:// for SQLAlchemy 1.4+
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        
        # Sync engine and session
        self.engine = None
        self.SessionLocal = None
        
        # Async engine and session
        self.async_engine = None
        self.AsyncSessionLocal = None
        
        logger.info(f"Database manager initialized")
    
    def initialize_sync(self):
        """Initialize synchronous database engine"""
        if self.engine is None:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("✅ Sync database engine initialized")
    
    def initialize_async(self):
        """Initialize asynchronous database engine"""
        if self.async_engine is None:
            # Convert to async URL
            async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
            
            self.async_engine = create_async_engine(
                async_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False
            )
            self.AsyncSessionLocal = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("✅ Async database engine initialized")
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get synchronous database session (context manager)
        
        Usage:
            with db_manager.get_session() as session:
                # use session
                pass
        """
        if self.SessionLocal is None:
            self.initialize_sync()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncSession:
        """
        Get asynchronous database session (async context manager)
        
        Usage:
            async with db_manager.get_async_session() as session:
                # use session
                pass
        """
        if self.AsyncSessionLocal is None:
            self.initialize_async()
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {e}")
                raise
    
    def create_tables(self):
        """Create all database tables"""
        if self.engine is None:
            self.initialize_sync()
        
        create_all_tables(self.engine)
        logger.info("✅ Database tables created")
    
    async def create_tables_async(self):
        """Create tables asynchronously"""
        if self.async_engine is None:
            self.initialize_async()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created (async)")
    
    def setup_timescale_hypertables(self):
        """
        Set up TimescaleDB hypertables for time-series optimization
        
        Call this after create_tables() if using TimescaleDB
        """
        if self.engine is None:
            self.initialize_sync()
        
        with self.get_session() as session:
            # Convert tables to hypertables
            tables_to_convert = [
                ('options_flow', 'timestamp'),
                ('gamma_exposure', 'timestamp'),
                ('dark_pool_trades', 'timestamp'),
                ('institutional_activity', 'filing_date'),
                ('congress_trades', 'transaction_date'),
                ('short_interest', 'date'),
                ('scanner_alerts', 'timestamp'),
                ('market_data', 'timestamp'),
                ('scanner_runs', 'start_time')
            ]
            
            for table_name, time_column in tables_to_convert:
                try:
                    # Create hypertable
                    session.execute(f"""
                        SELECT create_hypertable(
                            '{table_name}',
                            '{time_column}',
                            if_not_exists => TRUE,
                            migrate_data => TRUE
                        );
                    """)
                    logger.info(f"✅ Hypertable created: {table_name}")
                    
                    # Set up compression policy (compress data older than 7 days)
                    session.execute(f"""
                        SELECT add_compression_policy(
                            '{table_name}',
                            INTERVAL '7 days',
                            if_not_exists => TRUE
                        );
                    """)
                    logger.info(f"✅ Compression policy set: {table_name}")
                    
                except Exception as e:
                    logger.warning(f"Could not convert {table_name} to hypertable: {e}")
            
            session.commit()
    
    def close(self):
        """Close all connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Sync database engine closed")
    
    async def close_async(self):
        """Close async connections"""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Async database engine closed")


class RedisManager:
    """
    Manages Redis connections for caching and real-time data
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis manager
        
        Args:
            redis_url: Redis connection string (uses settings if not provided)
        """
        self.settings = get_settings()
        self.redis_url = redis_url or self.settings.redis_url
        self.redis: Optional[aioredis.Redis] = None
        
        logger.info("Redis manager initialized")
    
    async def connect(self):
        """Connect to Redis"""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True,
                max_connections=20
            )
            logger.info("✅ Redis connected")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis disconnected")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if self.redis is None:
            await self.connect()
        return await self.redis.get(key)
    
    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ):
        """
        Set value in Redis
        
        Args:
            key: Redis key
            value: Value to store
            expire: Expiration time in seconds
        """
        if self.redis is None:
            await self.connect()
        
        await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """Delete key from Redis"""
        if self.redis is None:
            await self.connect()
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.redis is None:
            await self.connect()
        return await self.redis.exists(key) > 0
    
    async def set_json(
        self,
        key: str,
        value: dict,
        expire: Optional[int] = None
    ):
        """Store JSON data"""
        import json
        await self.set(key, json.dumps(value), expire=expire)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON data"""
        import json
        value = await self.get(key)
        return json.loads(value) if value else None
    
    async def publish(self, channel: str, message: str):
        """Publish message to channel"""
        if self.redis is None:
            await self.connect()
        await self.redis.publish(channel, message)
    
    async def subscribe(self, channel: str):
        """Subscribe to channel"""
        if self.redis is None:
            await self.connect()
        
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    async def flush_all(self):
        """Clear all Redis data (use with caution!)"""
        if self.redis is None:
            await self.connect()
        await self.redis.flushall()
        logger.warning("⚠️ Redis flushed - all data cleared!")


# Global instances
_db_manager: Optional[DatabaseManager] = None
_redis_manager: Optional[RedisManager] = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_redis_manager() -> RedisManager:
    """Get global Redis manager instance"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


if __name__ == '__main__':
    # Test database connection
    async def test():
        print("Testing database connection...")
        
        db = get_db_manager()
        
        try:
            # Test sync connection
            print("\n1. Testing sync connection...")
            db.initialize_sync()
            with db.get_session() as session:
                result = session.execute("SELECT 1")
                print(f"✅ Sync connection successful: {result.scalar()}")
            
            # Test async connection
            print("\n2. Testing async connection...")
            db.initialize_async()
            async with db.get_async_session() as session:
                result = await session.execute("SELECT 1")
                print(f"✅ Async connection successful: {result.scalar()}")
            
            # Test Redis
            print("\n3. Testing Redis connection...")
            redis = get_redis_manager()
            await redis.connect()
            await redis.set('test_key', 'test_value', expire=60)
            value = await redis.get('test_key')
            print(f"✅ Redis connection successful: {value}")
            await redis.disconnect()
            
            print("\n✅ All connection tests passed!")
        
        except Exception as e:
            print(f"\n❌ Connection test failed: {e}")
        
        finally:
            db.close()
    
    asyncio.run(test())
