"""
Settings and Configuration Management
Loads configuration from environment variables with validation
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # API Configuration
    uw_api_key: str = Field(..., description="Unusual Whales API key")
    uw_base_url: str = Field(default="https://api.unusualwhales.com", description="API base URL")
    uw_ws_url: str = Field(default="wss://api.unusualwhales.com/ws", description="WebSocket URL")
    
    # Database Configuration
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="uw_scanner")
    postgres_user: str = Field(default="uw_user")
    postgres_password: str = Field(default="")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)
    
    # Rate Limiting
    api_rate_limit: int = Field(default=100, description="Requests per minute")
    api_burst_limit: int = Field(default=20, description="Burst capacity")
    
    # Scanner Modes
    mode_1_enabled: bool = Field(default=True)
    mode_2_enabled: bool = Field(default=True)
    mode_3_enabled: bool = Field(default=True)
    
    # Mode 1: Intraday Settings
    intraday_tickers: str = Field(default="SPY,QQQ,IWM")
    intraday_update_interval: int = Field(default=60)
    intraday_gex_threshold: float = Field(default=1000000)
    intraday_flow_threshold: float = Field(default=250000)
    
    # Mode 2: Swing Trading Settings
    swing_min_dte: int = Field(default=30)
    swing_max_dte: int = Field(default=45)
    swing_min_premium: float = Field(default=250000)
    swing_vol_oi_ratio: float = Field(default=2.0)
    swing_max_tickers: int = Field(default=50)
    
    # Mode 3: Long-term Settings
    longterm_min_institution_size: float = Field(default=50000000)
    longterm_min_short_interest: float = Field(default=15)
    longterm_filing_lookback_days: int = Field(default=90)
    
    # Alert Configuration
    discord_webhook_url: Optional[str] = Field(default=None)
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)
    email_smtp_server: Optional[str] = Field(default="smtp.gmail.com")
    email_smtp_port: int = Field(default=587)
    email_from: Optional[str] = Field(default=None)
    email_to: Optional[str] = Field(default=None)
    email_password: Optional[str] = Field(default=None)
    
    # Alert Thresholds
    alert_priority_high: int = Field(default=90)
    alert_priority_medium: int = Field(default=70)
    alert_priority_low: int = Field(default=50)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/scanner.log")
    log_max_size: int = Field(default=100)
    log_backup_count: int = Field(default=10)
    
    # Dashboard
    dashboard_port: int = Field(default=8501)
    dashboard_host: str = Field(default="0.0.0.0")
    
    # Backtesting
    backtest_start_date: str = Field(default="2023-01-01")
    backtest_cache_enabled: bool = Field(default=True)
    
    # Performance
    max_workers: int = Field(default=4)
    cache_ttl: int = Field(default=300)
    websocket_reconnect_delay: int = Field(default=5)
    
    @property
    def intraday_ticker_list(self) -> List[str]:
        """Parse comma-separated ticker list."""
        return [t.strip().upper() for t in self.intraday_tickers.split(',') if t.strip()]
    
    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def postgres_url_async(self) -> str:
        """Generate async PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    @property
    def logs_dir(self) -> Path:
        """Get logs directory."""
        log_path = self.project_root / self.log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path.parent
    
    def validate_alerts_config(self) -> bool:
        """Check if at least one alert method is configured."""
        return any([
            self.discord_webhook_url,
            self.telegram_bot_token and self.telegram_chat_id,
            self.email_from and self.email_to
        ])


# Global settings instance
settings = Settings()
