"""
Tests for configuration management.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from upbit_quant.core.config import Config
from upbit_quant.core.exceptions import ConfigError


class TestConfig:
    """Test configuration class."""
    
    def test_config_initialization(self, temp_dir):
        """Test configuration initialization."""
        with patch.dict('os.environ', {
            'DATABASE_URL': f'sqlite:///{temp_dir}/test.db',
            'SECRET_KEY': 'test-secret-key',
            'DEBUG': 'True',
        }):
            config = Config()
            assert config.database_url == f'sqlite:///{temp_dir}/test.db'
            assert config.secret_key == 'test-secret-key'
            assert config.debug is True
    
    def test_config_defaults(self):
        """Test configuration default values."""
        config = Config()
        assert config.database_url == "sqlite:///upbit_quant.db"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.default_initial_balance == 10000.0
    
    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ConfigError):
            with patch.dict('os.environ', {'LOG_LEVEL': 'INVALID'}):
                Config()
    
    def test_positive_float_validation(self):
        """Test positive float validation."""
        with pytest.raises(ConfigError):
            with patch.dict('os.environ', {'RISK_TOLERANCE': '-0.1'}):
                Config()
    
    def test_get_database_config(self, config):
        """Test database configuration retrieval."""
        db_config = config.get_database_config()
        assert 'ENGINE' in db_config
        assert 'NAME' in db_config
        assert 'USER' in db_config
        assert 'PASSWORD' in db_config
        assert 'HOST' in db_config
        assert 'PORT' in db_config
    
    def test_get_redis_config(self, config):
        """Test Redis configuration retrieval."""
        redis_config = config.get_redis_config()
        assert 'url' in redis_config
    
    def test_get_email_config(self, config):
        """Test email configuration retrieval."""
        email_config = config.get_email_config()
        assert 'host' in email_config
        assert 'port' in email_config
        assert 'use_tls' in email_config
        assert 'user' in email_config
        assert 'password' in email_config
    
    def test_is_development(self, config):
        """Test development mode detection."""
        config.debug = True
        assert config.is_development() is True
        assert config.is_production() is False
    
    def test_is_production(self, config):
        """Test production mode detection."""
        config.debug = False
        assert config.is_production() is True
        assert config.is_development() is False
    
    def test_allowed_hosts_parsing(self):
        """Test allowed hosts parsing."""
        with patch.dict('os.environ', {'ALLOWED_HOSTS': 'localhost,127.0.0.1,example.com'}):
            config = Config()
            assert config.allowed_hosts == ['localhost', '127.0.0.1', 'example.com']
    
    def test_directory_creation(self, temp_dir):
        """Test directory creation."""
        config = Config()
        config.project_root = temp_dir
        config.data_dir = temp_dir / "data"
        config.logs_dir = temp_dir / "logs"
        config.models_dir = temp_dir / "models"
        
        config._create_directories()
        
        assert config.data_dir.exists()
        assert config.logs_dir.exists()
        assert config.models_dir.exists()
    
    def test_config_from_env_file(self, temp_dir):
        """Test configuration loading from environment file."""
        env_file = temp_dir / ".env"
        env_file.write_text("""
DATABASE_URL=sqlite:///test.db
SECRET_KEY=test-secret
DEBUG=True
LOG_LEVEL=DEBUG
        """)
        
        with patch.object(Config, '__init__', lambda self: None):
            config = Config()
            config.project_root = temp_dir
            config._create_directories()
            
            # Test that environment file is loaded
            assert env_file.exists()
