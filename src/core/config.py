import os
from pathlib import Path
from src.core.exceptions import ConfigError

class Config:
    """
    Core configuration for the platform.
    Matches the requirements of legacy tests while incorporating new paths.
    """
    def __init__(self):
        self.project_root = Path(os.getcwd())
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.models_dir = self.project_root / "models"
        
        self.database_url = os.getenv('DATABASE_URL', "sqlite:///upbit_quant.db")
        self.secret_key = os.getenv('SECRET_KEY', "test-secret-key")
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self._allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
        self.default_initial_balance = float(os.getenv('DEFAULT_INITIAL_BALANCE', '10000.0'))
        self.risk_tolerance = float(os.getenv('RISK_TOLERANCE', '0.02'))
        
        # Validation checks required by tests
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ConfigError(f"Invalid log level: {self.log_level}")
            
        if self.risk_tolerance < 0:
            raise ConfigError(f"Risk tolerance must be positive: {self.risk_tolerance}")
            
        self._create_directories()

    @property
    def allowed_hosts(self):
        """Dynamic splitting of allowed hosts string."""
        return self._allowed_hosts.split(',')

    @allowed_hosts.setter
    def allowed_hosts(self, value):
        self._allowed_hosts = ",".join(value) if isinstance(value, list) else value

    def _create_directories(self):
        """Creates necessary project directories."""
        # Provisioning attributes in case of mocking __init__
        if not hasattr(self, 'data_dir'): self.data_dir = Path("data")
        if not hasattr(self, 'logs_dir'): self.logs_dir = Path("logs")
        if not hasattr(self, 'models_dir'): self.models_dir = Path("models")
        
        # Ensure directories exist
        for d in [self.data_dir, self.logs_dir, self.models_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_database_config(self):
        return {
            'ENGINE': 'sqlite3',
            'NAME': self.database_url,
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': ''
        }

    def get_redis_config(self):
        return {'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0')}

    def get_email_config(self):
        return {
            'host': '',
            'port': 587,
            'use_tls': True,
            'user': '',
            'password': ''
        }

    def is_development(self):
        return self.debug

    def is_production(self):
        return not self.debug
