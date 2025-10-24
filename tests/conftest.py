"""
Pytest configuration and fixtures for UPbit Quantitative Trading Platform.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch

from upbit_quant.core.config import Config
from upbit_quant.core.logger import get_logger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config(temp_dir):
    """Create a test configuration."""
    with patch.dict('os.environ', {
        'DATABASE_URL': f'sqlite:///{temp_dir}/test.db',
        'SECRET_KEY': 'test-secret-key',
        'DEBUG': 'True',
        'LOG_LEVEL': 'DEBUG',
    }):
        config = Config()
        config.project_root = temp_dir
        config.data_dir = temp_dir / "data"
        config.logs_dir = temp_dir / "logs"
        config.models_dir = temp_dir / "models"
        yield config


@pytest.fixture
def logger():
    """Create a test logger."""
    return get_logger("test")


@pytest.fixture
def sample_prices():
    """Sample price data for testing."""
    return [
        Decimal('100.00'),
        Decimal('105.00'),
        Decimal('110.00'),
        Decimal('108.00'),
        Decimal('112.00'),
        Decimal('115.00'),
        Decimal('113.00'),
        Decimal('118.00'),
        Decimal('120.00'),
        Decimal('122.00'),
    ]


@pytest.fixture
def sample_symbols():
    """Sample trading symbols for testing."""
    return ['BTC', 'ETH', 'ADA', 'BNB', 'XRP']


@pytest.fixture
def mock_api_response():
    """Mock API response for testing."""
    return {
        'symbol': 'BTC-KRW',
        'price': '50000000',
        'volume': '100.5',
        'timestamp': '2023-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_trading_data():
    """Sample trading data for testing."""
    return {
        'symbol': 'BTC-KRW',
        'prices': [50000000, 50500000, 51000000, 50800000, 51200000],
        'volumes': [100.5, 120.3, 95.7, 110.2, 105.8],
        'timestamps': [
            '2023-01-01T00:00:00Z',
            '2023-01-01T01:00:00Z',
            '2023-01-01T02:00:00Z',
            '2023-01-01T03:00:00Z',
            '2023-01-01T04:00:00Z',
        ]
    }


@pytest.fixture
def mock_trading_env():
    """Mock trading environment for testing."""
    env = Mock()
    env.prices = [100, 105, 110, 108, 112, 115, 113, 118, 120, 122]
    env.initial_balance = 10000
    env.current_step = 0
    env.balance = 10000
    return env


@pytest.fixture
def mock_q_learning_bot():
    """Mock Q-learning bot for testing."""
    bot = Mock()
    bot.q_table = {}
    bot.alpha = 0.5
    bot.gamma = 0.6
    bot.epsilon = 0.1
    bot.action_space = Mock()
    bot.action_space.n = 3
    bot.action_space.sample.return_value = 0
    return bot


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        'database_url': 'sqlite:///test.db',
        'secret_key': 'test-secret-key',
        'debug': True,
        'log_level': 'DEBUG',
        'default_initial_balance': 10000.0,
        'max_position_size': 1000.0,
        'risk_tolerance': 0.02,
        'trading_fee': 0.0005,
    }


@pytest.fixture
def sample_validation_data():
    """Sample validation data for testing."""
    return {
        'valid_prices': ['100.50', 100.50, 100, Decimal('100.50')],
        'invalid_prices': ['abc', -100, None, ''],
        'valid_symbols': ['BTC', 'ETH', 'BTC-KRW', 'ADA-USDT'],
        'invalid_symbols': ['', 'btc', 'BTC-', '123', None],
        'valid_timestamps': [
            '2023-01-01T00:00:00Z',
            '2023-01-01T00:00:00+00:00',
            1672531200,
            '2023-01-01 00:00:00'
        ],
        'invalid_timestamps': ['invalid', None, '', '2023-13-01'],
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test names
        if "test_" in item.name and "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        elif "test_" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to certain tests
        if any(keyword in item.name for keyword in ["slow", "performance", "benchmark"]):
            item.add_marker(pytest.mark.slow)
