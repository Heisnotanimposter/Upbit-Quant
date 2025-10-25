"""
Custom exceptions for UPbit Quantitative Trading Platform.
"""


class UPbitQuantError(Exception):
    """Base exception for UPbit Quantitative Trading Platform."""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TradingError(UPbitQuantError):
    """Exception raised for trading-related errors."""
    
    def __init__(self, message: str, error_code: str = "TRADING_ERROR"):
        super().__init__(message, error_code)


class DataError(UPbitQuantError):
    """Exception raised for data-related errors."""
    
    def __init__(self, message: str, error_code: str = "DATA_ERROR"):
        super().__init__(message, error_code)


class ConfigError(UPbitQuantError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, error_code: str = "CONFIG_ERROR"):
        super().__init__(message, error_code)


class APIError(UPbitQuantError):
    """Exception raised for API-related errors."""
    
    def __init__(self, message: str, error_code: str = "API_ERROR", status_code: int = None):
        self.status_code = status_code
        super().__init__(message, error_code)


class ValidationError(UPbitQuantError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code)


class ModelError(UPbitQuantError):
    """Exception raised for ML model-related errors."""
    
    def __init__(self, message: str, error_code: str = "MODEL_ERROR"):
        super().__init__(message, error_code)


class DatabaseError(UPbitQuantError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, error_code: str = "DATABASE_ERROR"):
        super().__init__(message, error_code)


class NetworkError(UPbitQuantError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, error_code: str = "NETWORK_ERROR"):
        super().__init__(message, error_code)
