class UPbitQuantError(Exception):
    """Base exception for the project."""
    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class TradingError(UPbitQuantError):
    """Execution related errors."""
    def __init__(self, message, error_code="TRADING_ERROR"):
        super().__init__(message, error_code)

class DataError(UPbitQuantError):
    """Data fetching related errors."""
    def __init__(self, message, error_code="DATA_ERROR"):
        super().__init__(message, error_code)

class ConfigError(UPbitQuantError):
    """Configuration related errors."""
    def __init__(self, message, error_code="CONFIG_ERROR"):
        super().__init__(message, error_code)

class APIError(UPbitQuantError):
    """API related errors."""
    def __init__(self, message, error_code="API_ERROR", status_code=None):
        super().__init__(message, error_code)
        self.status_code = status_code

class ValidationError(UPbitQuantError):
    """Validation related errors."""
    def __init__(self, message, error_code="VALIDATION_ERROR"):
        super().__init__(message, error_code)

class ModelError(UPbitQuantError):
    """Model related errors."""
    def __init__(self, message, error_code="MODEL_ERROR"):
        super().__init__(message, error_code)

class DatabaseError(UPbitQuantError):
    """Database related errors."""
    def __init__(self, message, error_code="DATABASE_ERROR"):
        super().__init__(message, error_code)

class NetworkError(UPbitQuantError):
    """Network related errors."""
    def __init__(self, message, error_code="NETWORK_ERROR"):
        super().__init__(message, error_code)
