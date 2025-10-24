"""
Tests for custom exceptions.
"""

import pytest

from upbit_quant.core.exceptions import (
    UPbitQuantError,
    TradingError,
    DataError,
    ConfigError,
    APIError,
    ValidationError,
    ModelError,
    DatabaseError,
    NetworkError,
)


class TestUPbitQuantError:
    """Test base exception class."""
    
    def test_base_exception_creation(self):
        """Test base exception creation."""
        error = UPbitQuantError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code is None
    
    def test_base_exception_with_error_code(self):
        """Test base exception with error code."""
        error = UPbitQuantError("Test error message", "TEST_ERROR")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"


class TestTradingError:
    """Test trading error exception."""
    
    def test_trading_error_creation(self):
        """Test trading error creation."""
        error = TradingError("Trading failed")
        assert str(error) == "Trading failed"
        assert error.message == "Trading failed"
        assert error.error_code == "TRADING_ERROR"
    
    def test_trading_error_inheritance(self):
        """Test trading error inheritance."""
        error = TradingError("Trading failed")
        assert isinstance(error, UPbitQuantError)


class TestDataError:
    """Test data error exception."""
    
    def test_data_error_creation(self):
        """Test data error creation."""
        error = DataError("Data validation failed")
        assert str(error) == "Data validation failed"
        assert error.message == "Data validation failed"
        assert error.error_code == "DATA_ERROR"
    
    def test_data_error_inheritance(self):
        """Test data error inheritance."""
        error = DataError("Data validation failed")
        assert isinstance(error, UPbitQuantError)


class TestConfigError:
    """Test configuration error exception."""
    
    def test_config_error_creation(self):
        """Test configuration error creation."""
        error = ConfigError("Configuration invalid")
        assert str(error) == "Configuration invalid"
        assert error.message == "Configuration invalid"
        assert error.error_code == "CONFIG_ERROR"
    
    def test_config_error_inheritance(self):
        """Test configuration error inheritance."""
        error = ConfigError("Configuration invalid")
        assert isinstance(error, UPbitQuantError)


class TestAPIError:
    """Test API error exception."""
    
    def test_api_error_creation(self):
        """Test API error creation."""
        error = APIError("API request failed")
        assert str(error) == "API request failed"
        assert error.message == "API request failed"
        assert error.error_code == "API_ERROR"
        assert error.status_code is None
    
    def test_api_error_with_status_code(self):
        """Test API error with status code."""
        error = APIError("API request failed", "API_ERROR", 404)
        assert str(error) == "API request failed"
        assert error.message == "API request failed"
        assert error.error_code == "API_ERROR"
        assert error.status_code == 404
    
    def test_api_error_inheritance(self):
        """Test API error inheritance."""
        error = APIError("API request failed")
        assert isinstance(error, UPbitQuantError)


class TestValidationError:
    """Test validation error exception."""
    
    def test_validation_error_creation(self):
        """Test validation error creation."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.message == "Validation failed"
        assert error.error_code == "VALIDATION_ERROR"
    
    def test_validation_error_inheritance(self):
        """Test validation error inheritance."""
        error = ValidationError("Validation failed")
        assert isinstance(error, UPbitQuantError)


class TestModelError:
    """Test model error exception."""
    
    def test_model_error_creation(self):
        """Test model error creation."""
        error = ModelError("Model training failed")
        assert str(error) == "Model training failed"
        assert error.message == "Model training failed"
        assert error.error_code == "MODEL_ERROR"
    
    def test_model_error_inheritance(self):
        """Test model error inheritance."""
        error = ModelError("Model training failed")
        assert isinstance(error, UPbitQuantError)


class TestDatabaseError:
    """Test database error exception."""
    
    def test_database_error_creation(self):
        """Test database error creation."""
        error = DatabaseError("Database connection failed")
        assert str(error) == "Database connection failed"
        assert error.message == "Database connection failed"
        assert error.error_code == "DATABASE_ERROR"
    
    def test_database_error_inheritance(self):
        """Test database error inheritance."""
        error = DatabaseError("Database connection failed")
        assert isinstance(error, UPbitQuantError)


class TestNetworkError:
    """Test network error exception."""
    
    def test_network_error_creation(self):
        """Test network error creation."""
        error = NetworkError("Network connection failed")
        assert str(error) == "Network connection failed"
        assert error.message == "Network connection failed"
        assert error.error_code == "NETWORK_ERROR"
    
    def test_network_error_inheritance(self):
        """Test network error inheritance."""
        error = NetworkError("Network connection failed")
        assert isinstance(error, UPbitQuantError)


class TestExceptionHierarchy:
    """Test exception hierarchy."""
    
    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from UPbitQuantError."""
        exceptions = [
            TradingError("test"),
            DataError("test"),
            ConfigError("test"),
            APIError("test"),
            ValidationError("test"),
            ModelError("test"),
            DatabaseError("test"),
            NetworkError("test"),
        ]
        
        for exception in exceptions:
            assert isinstance(exception, UPbitQuantError)
    
    def test_exception_catching(self):
        """Test exception catching."""
        try:
            raise TradingError("Trading failed")
        except UPbitQuantError as e:
            assert str(e) == "Trading failed"
            assert e.error_code == "TRADING_ERROR"
        
        try:
            raise DataError("Data failed")
        except UPbitQuantError as e:
            assert str(e) == "Data failed"
            assert e.error_code == "DATA_ERROR"
