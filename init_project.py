"""
Project Initialization Script
Run this to set up the scanner for first use
"""
import asyncio
import sys
from pathlib import Path
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


def check_env_file():
    """Check if .env file exists"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            logger.warning("⚠️ .env file not found. Please copy .env.example to .env and configure it.")
            logger.info(f"Run: cp {env_example} {env_file}")
            return False
        else:
            logger.error("❌ .env.example not found!")
            return False
    
    logger.info("✅ .env file found")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'aiohttp',
        'sqlalchemy',
        'redis',
        'loguru',
        'pydantic',
        'websockets'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"❌ Missing packages: {', '.join(missing)}")
        logger.info("Run: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required packages installed")
    return True


def test_config():
    """Test configuration loading"""
    try:
        from config import get_settings
        settings = get_settings()
        
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"   API Base URL: {settings.uw_base_url}")
        logger.info(f"   Rate Limit: {settings.uw_rate_limit} req/s")
        logger.info(f"   Mode 1: {'Enabled' if settings.mode_1_enabled else 'Disabled'}")
        logger.info(f"   Mode 2: {'Enabled' if settings.mode_2_enabled else 'Disabled'}")
        logger.info(f"   Mode 3: {'Enabled' if settings.mode_3_enabled else 'Disabled'}")
        
        # Check API key
        if len(settings.uw_api_key) < 10:
            logger.warning("⚠️ API key looks invalid (too short)")
            return False
        
        logger.info(f"   API Key: {settings.uw_api_key[:10]}... (looks valid)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return False


async def test_database():
    """Test database connection"""
    try:
        from database import get_db_manager
        
        logger.info("Testing database connection...")
        db = get_db_manager()
        
        # Test sync connection
        db.initialize_sync()
        with db.get_session() as session:
            result = session.execute("SELECT 1")
            assert result.scalar() == 1
        
        logger.info("✅ Database connection successful")
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.info("Make sure PostgreSQL is running and DATABASE_URL is correct in .env")
        return False


async def test_redis():
    """Test Redis connection"""
    try:
        from database import get_redis_manager
        
        logger.info("Testing Redis connection...")
        redis = get_redis_manager()
        
        await redis.connect()
        await redis.set('test_init', '1', expire=10)
        value = await redis.get('test_init')
        assert value == '1'
        await redis.delete('test_init')
        await redis.disconnect()
        
        logger.info("✅ Redis connection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.info("Make sure Redis is running and REDIS_URL is correct in .env")
        return False


async def test_api():
    """Test API connection"""
    try:
        from api import UnusualWhalesClient
        
        logger.info("Testing Unusual Whales API connection...")
        
        async with UnusualWhalesClient() as client:
            # Try a simple endpoint
            try:
                result = await client.get_flow_alerts(ticker='SPY', limit=1)
                logger.info("✅ API connection successful")
                logger.info(f"   Retrieved {len(result.get('data', []))} flow alert(s)")
                return True
            except Exception as e:
                logger.error(f"❌ API request failed: {e}")
                logger.info("Check your API key in .env")
                return False
        
    except Exception as e:
        logger.error(f"❌ API client error: {e}")
        return False


def create_tables():
    """Create database tables"""
    try:
        from database import get_db_manager
        
        logger.info("Creating database tables...")
        db = get_db_manager()
        db.create_tables()
        logger.info("✅ Database tables created")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


def setup_timescale():
    """Set up TimescaleDB hypertables (optional)"""
    try:
        from database import get_db_manager
        
        logger.info("Setting up TimescaleDB hypertables...")
        db = get_db_manager()
        db.setup_timescale_hypertables()
        logger.info("✅ TimescaleDB hypertables configured")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ TimescaleDB setup skipped: {e}")
        logger.info("This is optional - regular PostgreSQL will work fine")
        return True  # Don't fail on this


def create_directories():
    """Create necessary directories"""
    dirs = ['logs', 'data', 'backups']
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    logger.info(f"✅ Created directories: {', '.join(dirs)}")


async def main():
    """Main initialization flow"""
    logger.info("=" * 60)
    logger.info("🐋 Unusual Whales Scanner - Initialization")
    logger.info("=" * 60)
    
    steps = []
    
    # 1. Check environment
    logger.info("\n📋 Step 1: Checking environment...")
    steps.append(("Environment file", check_env_file()))
    
    if not steps[-1][1]:
        logger.error("\n❌ Initialization failed. Please create .env file first.")
        return False
    
    steps.append(("Dependencies", check_dependencies()))
    
    if not steps[-1][1]:
        logger.error("\n❌ Initialization failed. Please install dependencies.")
        return False
    
    # 2. Test configuration
    logger.info("\n⚙️ Step 2: Testing configuration...")
    steps.append(("Configuration", test_config()))
    
    if not steps[-1][1]:
        logger.error("\n❌ Initialization failed. Please check your .env configuration.")
        return False
    
    # 3. Test connections
    logger.info("\n🔌 Step 3: Testing connections...")
    steps.append(("Database", await test_database()))
    steps.append(("Redis", await test_redis()))
    steps.append(("API", await test_api()))
    
    # 4. Set up database
    logger.info("\n🗄️ Step 4: Setting up database...")
    steps.append(("Tables", create_tables()))
    steps.append(("TimescaleDB", setup_timescale()))
    
    # 5. Create directories
    logger.info("\n📁 Step 5: Creating directories...")
    create_directories()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Initialization Summary")
    logger.info("=" * 60)
    
    for step_name, success in steps:
        status = "✅" if success else "❌"
        logger.info(f"{status} {step_name}")
    
    all_success = all(success for _, success in steps)
    
    if all_success:
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Initialization Complete!")
        logger.info("=" * 60)
        logger.info("\n✅ Your scanner is ready to use!")
        logger.info("\nNext steps:")
        logger.info("1. Review configuration in .env")
        logger.info("2. Run the scanner: python -m scanners.mode1_intraday (coming soon)")
        logger.info("3. Start dashboard: streamlit run dashboard/streamlit_app.py (coming soon)")
        logger.info("\nFor help, see README.md")
        return True
    else:
        logger.error("\n❌ Initialization incomplete. Please fix the errors above.")
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
