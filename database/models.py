"""
Database Models for UW Scanner
SQLAlchemy models for TimescaleDB/PostgreSQL
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, JSON, BigInteger,
    Index, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class FlowDirection(str, Enum):
    """Options flow direction"""
    CALL_BUY = "call_buy"
    CALL_SELL = "call_sell"
    PUT_BUY = "put_buy"
    PUT_SELL = "put_sell"
    UNKNOWN = "unknown"


class AlertType(str, Enum):
    """Scanner alert types"""
    FLOW_ALERT = "flow_alert"
    GEX_PIVOT = "gex_pivot"
    DARK_POOL = "dark_pool"
    INSTITUTIONAL = "institutional"
    CONGRESS = "congress"
    SHORT_SQUEEZE = "short_squeeze"
    EARNINGS = "earnings"
    CUSTOM = "custom"


class ScannerMode(str, Enum):
    """Scanner operating modes"""
    MODE_1_INTRADAY = "mode_1_intraday"
    MODE_2_SWING = "mode_2_swing"
    MODE_3_LONGTERM = "mode_3_longterm"


# ============================================================================
# CORE MODELS
# ============================================================================

class OptionsFlow(Base):
    """Options flow data (from flow alerts and full tape)"""
    __tablename__ = 'options_flow'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Contract details
    ticker = Column(String(10), nullable=False, index=True)
    option_symbol = Column(String(50), nullable=False)
    strike = Column(Float, nullable=False)
    expiry = Column(DateTime, nullable=False, index=True)
    option_type = Column(String(4), nullable=False)  # CALL or PUT
    
    # Flow metrics
    premium = Column(Float, nullable=False, index=True)
    volume = Column(Integer, nullable=False)
    open_interest = Column(Integer)
    direction = Column(SQLEnum(FlowDirection), nullable=False)
    
    # Execution details
    price = Column(Float)
    underlying_price = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    size = Column(Integer)
    
    # Greeks
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    iv = Column(Float)
    
    # Metadata
    exchange = Column(String(20))
    is_sweep = Column(Boolean, default=False)
    is_block = Column(Boolean, default=False)
    is_split = Column(Boolean, default=False)
    
    raw_data = Column(JSON)  # Store full API response
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_flow_ticker_time', 'ticker', 'timestamp'),
        Index('idx_flow_expiry_time', 'expiry', 'timestamp'),
        Index('idx_flow_premium', 'premium'),
    )


class GammaExposure(Base):
    """Gamma exposure data (GEX)"""
    __tablename__ = 'gamma_exposure'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    ticker = Column(String(10), nullable=False, index=True)
    strike = Column(Float, nullable=False)
    expiry = Column(DateTime, nullable=False)
    
    # Exposure values
    call_gex = Column(Float)
    put_gex = Column(Float)
    total_gex = Column(Float, index=True)
    
    call_dex = Column(Float)
    put_dex = Column(Float)
    total_dex = Column(Float)
    
    # Volume metrics
    call_volume = Column(Integer)
    put_volume = Column(Integer)
    call_oi = Column(Integer)
    put_oi = Column(Integer)
    
    # Position of strike relative to spot
    spot_price = Column(Float)
    distance_from_spot = Column(Float)
    is_atm = Column(Boolean, default=False)
    
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_gex_ticker_time', 'ticker', 'timestamp'),
        Index('idx_gex_strike', 'ticker', 'strike', 'timestamp'),
        Index('idx_gex_total', 'total_gex'),
    )


class DarkPoolTrade(Base):
    """Dark pool / off-exchange trades"""
    __tablename__ = 'dark_pool_trades'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    ticker = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    size = Column(Integer, nullable=False, index=True)
    value = Column(Float, nullable=False)  # price * size
    
    # Trade classification
    is_dark_pool = Column(Boolean, default=True)
    venue = Column(String(50))
    
    # Price context
    spot_price = Column(Float)
    price_vs_spot = Column(Float)  # percentage difference
    
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_dark_ticker_time', 'ticker', 'timestamp'),
        Index('idx_dark_size', 'size'),
    )


class InstitutionalActivity(Base):
    """Institutional holdings and activity"""
    __tablename__ = 'institutional_activity'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    filing_date = Column(DateTime, nullable=False, index=True)
    
    institution_name = Column(String(200), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    
    # Position details
    shares = Column(BigInteger)
    value = Column(BigInteger)  # in dollars
    percentage_of_portfolio = Column(Float)
    percentage_of_shares = Column(Float)
    
    # Change metrics
    change_in_shares = Column(BigInteger)
    change_in_value = Column(BigInteger)
    change_percentage = Column(Float)
    
    # Position type
    is_new_position = Column(Boolean, default=False)
    is_sold_out = Column(Boolean, default=False)
    is_increased = Column(Boolean, default=False)
    is_decreased = Column(Boolean, default=False)
    
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_inst_ticker_date', 'ticker', 'filing_date'),
        Index('idx_inst_name_date', 'institution_name', 'filing_date'),
    )


class CongressTrade(Base):
    """Congressional trades"""
    __tablename__ = 'congress_trades'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    disclosure_date = Column(DateTime, nullable=False, index=True)
    
    representative = Column(String(200), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    
    # Trade details
    transaction_type = Column(String(20))  # Purchase, Sale, Exchange
    amount_range = Column(String(50))  # e.g., "$1,001 - $15,000"
    amount_min = Column(BigInteger)
    amount_max = Column(BigInteger)
    
    # Additional info
    asset_description = Column(Text)
    committee = Column(String(200))
    party = Column(String(20))
    
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_congress_ticker_date', 'ticker', 'transaction_date'),
        Index('idx_congress_rep', 'representative', 'transaction_date'),
    )


class ShortInterest(Base):
    """Short interest data"""
    __tablename__ = 'short_interest'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    
    ticker = Column(String(10), nullable=False, index=True)
    
    # Short metrics
    short_interest = Column(BigInteger)
    short_percent_float = Column(Float, index=True)
    short_percent_outstanding = Column(Float)
    days_to_cover = Column(Float, index=True)
    
    # Volume data
    short_volume = Column(BigInteger)
    total_volume = Column(BigInteger)
    short_volume_ratio = Column(Float)
    
    # FTD data
    ftd_shares = Column(BigInteger)
    
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_short_ticker_date', 'ticker', 'date'),
        Index('idx_short_float', 'short_percent_float'),
    )


# ============================================================================
# SCANNER & ALERT MODELS
# ============================================================================

class ScannerAlert(Base):
    """Scanner-generated alerts"""
    __tablename__ = 'scanner_alerts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    
    # Alert classification
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    scanner_mode = Column(SQLEnum(ScannerMode), nullable=False, index=True)
    priority = Column(Integer, default=5, index=True)  # 1-10, higher = more important
    
    # Target
    ticker = Column(String(10), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Scoring
    composite_score = Column(Float, index=True)
    flow_score = Column(Float)
    gex_score = Column(Float)
    dark_pool_score = Column(Float)
    institutional_score = Column(Float)
    sentiment_score = Column(Float)
    
    # Alert metadata
    is_active = Column(Boolean, default=True)
    is_dismissed = Column(Boolean, default=False)
    is_notified = Column(Boolean, default=False)
    
    # Related data
    related_data = Column(JSON)  # Store related signals/data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_alert_ticker_time', 'ticker', 'timestamp'),
        Index('idx_alert_type_mode', 'alert_type', 'scanner_mode'),
        Index('idx_alert_score', 'composite_score'),
        Index('idx_alert_active', 'is_active', 'priority'),
    )


class Watchlist(Base):
    """User watchlists"""
    __tablename__ = 'watchlists'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Mode association
    scanner_mode = Column(SQLEnum(ScannerMode))
    
    # Tickers in this watchlist
    tickers = Column(JSON)  # List of tickers
    
    # Settings
    is_active = Column(Boolean, default=True)
    auto_update = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScannerRun(Base):
    """Track scanner execution history"""
    __tablename__ = 'scanner_runs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime)
    
    scanner_mode = Column(SQLEnum(ScannerMode), nullable=False, index=True)
    
    # Execution metrics
    tickers_scanned = Column(Integer)
    alerts_generated = Column(Integer)
    execution_time_ms = Column(Integer)
    
    # Status
    status = Column(String(20))  # success, failed, partial
    error_message = Column(Text)
    
    # Results summary
    results_summary = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketData(Base):
    """General market data cache"""
    __tablename__ = 'market_data'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    data_type = Column(String(50), nullable=False, index=True)  # e.g., 'market_tide', 'top_net_impact'
    ticker = Column(String(10), index=True)  # Optional, for ticker-specific data
    
    # Flexible data storage
    data = Column(JSON, nullable=False)
    
    # Cache management
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_market_type_ticker', 'data_type', 'ticker', 'timestamp'),
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_all_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)
    print("✅ All tables created")


def drop_all_tables(engine):
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(engine)
    print("⚠️ All tables dropped")


if __name__ == '__main__':
    from sqlalchemy import create_engine
    
    # Test database model creation
    print("Testing database models...")
    
    # Create in-memory SQLite for testing
    engine = create_engine('sqlite:///:memory:', echo=True)
    create_all_tables(engine)
    
    print("\n✅ Database models validated successfully!")
    print(f"\nTables created:")
    for table in Base.metadata.tables.keys():
        print(f"  • {table}")
