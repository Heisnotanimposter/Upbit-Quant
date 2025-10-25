"""
Configuration management for UPbit Quantitative Trading Platform.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator


class Config(BaseSettings):
    """Configuration class using Pydantic for validation and environment variable management."""
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///upbit_quant.db", env="DATABASE_URL")
    database_engine: str = Field(default="django.db.backends.sqlite3", env="DATABASE_ENGINE")
    database_name: str = Field(default="upbit_quant", env="DATABASE_NAME")
    database_user: str = Field(default="", env="DATABASE_USER")
    database_password: str = Field(default="", env="DATABASE_PASSWORD")
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    
    # Django Settings
    secret_key: str = Field(default="django-insecure-change-me", env="SECRET_KEY")
    debug: bool = Field(default=False, env="DEBUG")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")
    
    # API Keys
    upbit_access_key: str = Field(default="", env="UPBIT_ACCESS_KEY")
    upbit_secret_key: str = Field(default="", env="UPBIT_SECRET_KEY")
    binance_api_key: str = Field(default="", env="BINANCE_API_KEY")
    binance_secret_key: str = Field(default="", env="BINANCE_SECRET_KEY")
    alpha_vantage_api_key: str = Field(default="", env="ALPHA_VANTAGE_API_KEY")
    
    # Trading Configuration
    default_initial_balance: float = Field(default=10000.0, env="DEFAULT_INITIAL_BALANCE")
    max_position_size: float = Field(default=1000.0, env="MAX_POSITION_SIZE")
    risk_tolerance: float = Field(default=0.02, env="RISK_TOLERANCE")
    trading_fee: float = Field(default=0.0005, env="TRADING_FEE")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/upbit_quant.log", env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # ML/AI Configuration
    model_path: str = Field(default="models/", env="MODEL_PATH")
    training_data_path: str = Field(default="data/training/", env="TRAINING_DATA_PATH")
    prediction_horizon: int = Field(default=24, env="PREDICTION_HORIZON")
    
    # Web Scraping Configuration
    request_delay: float = Field(default=1.0, env="REQUEST_DELAY")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    timeout: int = Field(default=30, env="TIMEOUT")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Email Configuration
    email_host: str = Field(default="smtp.gmail.com", env="EMAIL_HOST")
    email_port: int = Field(default=587, env="EMAIL_PORT")
    email_use_tls: bool = Field(default=True, env="EMAIL_USE_TLS")
    email_host_user: str = Field(default="", env="EMAIL_HOST_USER")
    email_host_password: str = Field(default="", env="EMAIL_HOST_PASSWORD")
    
    # Monitoring Configuration
    prometheus_port: int = Field(default=8000, env="PROMETHEUS_PORT")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    
    # Project Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    models_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "models")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("allowed_hosts", pre=True)
    def parse_allowed_hosts(cls, v: Union[str, list]) -> list:
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("log_level", pre=True)
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("risk_tolerance", "trading_fee", pre=True)
    def validate_positive_float(cls, v: float) -> float:
        """Validate that float values are positive."""
        if v < 0:
            raise ValueError("Value must be positive")
        return v
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize configuration with environment variables."""
        super().__init__(**kwargs)
        
        # Create necessary directories
        self._create_directories()
        
        # Load environment variables from .env file if it exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    
    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [self.data_dir, self.logs_dir, self.models_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for Django."""
        return {
            "ENGINE": self.database_engine,
            "NAME": self.database_name,
            "USER": self.database_user,
            "PASSWORD": self.database_password,
            "HOST": self.database_host,
            "PORT": self.database_port,
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {
            "url": self.redis_url,
        }
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration."""
        return {
            "host": self.email_host,
            "port": self.email_port,
            "use_tls": self.email_use_tls,
            "user": self.email_host_user,
            "password": self.email_host_password,
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug


# Global configuration instance
config = Config()
