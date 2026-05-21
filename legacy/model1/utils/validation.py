"""
Validation utilities for UPbit Quantitative Trading Platform.
"""

import re
from datetime import datetime, timezone
from typing import Any, Union
from decimal import Decimal, InvalidOperation

from ..core.exceptions import ValidationError


def validate_price(price: Union[str, float, int, Decimal]) -> Decimal:
    """Validate and convert price to Decimal.
    
    Args:
        price: Price value to validate
        
    Returns:
        Decimal price value
        
    Raises:
        ValidationError: If price is invalid
    """
    try:
        if isinstance(price, str):
            # Remove any currency symbols and whitespace
            price = re.sub(r'[^\d.-]', '', price.strip())
        
        price_decimal = Decimal(str(price))
        
        if price_decimal < 0:
            raise ValidationError("Price cannot be negative")
            
        return price_decimal
        
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Invalid price format: {price}") from e


def validate_symbol(symbol: str) -> str:
    """Validate trading symbol format.
    
    Args:
        symbol: Trading symbol to validate
        
    Returns:
        Validated symbol in uppercase
        
    Raises:
        ValidationError: If symbol is invalid
    """
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string")
    
    symbol = symbol.strip().upper()
    
    if not symbol:
        raise ValidationError("Symbol cannot be empty")
    
    # Basic symbol format validation (alphanumeric, max 20 chars)
    if not re.match(r'^[A-Z0-9]{1,20}$', symbol):
        raise ValidationError(f"Invalid symbol format: {symbol}")
    
    return symbol


def validate_timestamp(timestamp: Union[str, datetime, int, float]) -> datetime:
    """Validate and convert timestamp to datetime.
    
    Args:
        timestamp: Timestamp to validate (ISO string, datetime, or Unix timestamp)
        
    Returns:
        Datetime object in UTC
        
    Raises:
        ValidationError: If timestamp is invalid
    """
    try:
        if isinstance(timestamp, str):
            # Try parsing ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        elif isinstance(timestamp, (int, float)):
            # Unix timestamp
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            raise ValidationError(f"Unsupported timestamp type: {type(timestamp)}")
        
        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Validate reasonable date range (2000 to 2100)
        if dt.year < 2000 or dt.year > 2100:
            raise ValidationError(f"Timestamp out of reasonable range: {dt}")
        
        return dt
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid timestamp format: {timestamp}") from e


def validate_quantity(quantity: Union[str, float, int, Decimal]) -> Decimal:
    """Validate trading quantity.
    
    Args:
        quantity: Quantity to validate
        
    Returns:
        Decimal quantity value
        
    Raises:
        ValidationError: If quantity is invalid
    """
    try:
        if isinstance(quantity, str):
            quantity = quantity.strip()
        
        qty_decimal = Decimal(str(quantity))
        
        if qty_decimal <= 0:
            raise ValidationError("Quantity must be positive")
            
        return qty_decimal
        
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Invalid quantity format: {quantity}") from e


def validate_percentage(percentage: Union[str, float, int, Decimal]) -> Decimal:
    """Validate percentage value.
    
    Args:
        percentage: Percentage to validate
        
    Returns:
        Decimal percentage value
        
    Raises:
        ValidationError: If percentage is invalid
    """
    try:
        if isinstance(percentage, str):
            percentage = percentage.strip().rstrip('%')
        
        pct_decimal = Decimal(str(percentage))
        
        if pct_decimal < 0 or pct_decimal > 100:
            raise ValidationError("Percentage must be between 0 and 100")
            
        return pct_decimal
        
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Invalid percentage format: {percentage}") from e


def validate_positive_number(value: Union[str, float, int, Decimal], field_name: str = "value") -> Decimal:
    """Validate positive number.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Decimal value
        
    Raises:
        ValidationError: If value is invalid
    """
    try:
        if isinstance(value, str):
            value = value.strip()
        
        decimal_value = Decimal(str(value))
        
        if decimal_value < 0:
            raise ValidationError(f"{field_name} cannot be negative")
            
        return decimal_value
        
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(f"Invalid {field_name} format: {value}") from e


def validate_api_key(api_key: str, key_name: str = "API key") -> str:
    """Validate API key format.
    
    Args:
        api_key: API key to validate
        key_name: Name of the API key for error messages
        
    Returns:
        Validated API key
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not isinstance(api_key, str):
        raise ValidationError(f"{key_name} must be a string")
    
    api_key = api_key.strip()
    
    if not api_key:
        raise ValidationError(f"{key_name} cannot be empty")
    
    if len(api_key) < 10:
        raise ValidationError(f"{key_name} is too short")
    
    return api_key


def validate_email(email: str) -> str:
    """Validate email format.
    
    Args:
        email: Email to validate
        
    Returns:
        Validated email
        
    Raises:
        ValidationError: If email is invalid
    """
    if not isinstance(email, str):
        raise ValidationError("Email must be a string")
    
    email = email.strip().lower()
    
    # Basic email regex validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    
    return email


def validate_file_path(file_path: str) -> str:
    """Validate file path.
    
    Args:
        file_path: File path to validate
        
    Returns:
        Validated file path
        
    Raises:
        ValidationError: If file path is invalid
    """
    if not isinstance(file_path, str):
        raise ValidationError("File path must be a string")
    
    file_path = file_path.strip()
    
    if not file_path:
        raise ValidationError("File path cannot be empty")
    
    # Basic path validation (no directory traversal)
    if '..' in file_path or file_path.startswith('/'):
        raise ValidationError(f"Invalid file path: {file_path}")
    
    return file_path
