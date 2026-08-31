import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from src.core.exceptions import ValidationError

def validate_price(price):
    """Validates and returns a Decimal price."""
    if price is None: raise ValidationError("Price cannot be None")
    try:
        if isinstance(price, str):
            # Only remove characters that are definitely not numbers or decimals or negative signs
            # But be careful with currency symbols.
            price = "".join([c for c in price if c.isdigit() or c in '.-'])
        
        val = Decimal(str(price))
        if val < 0: raise ValidationError("Price cannot be negative")
        return val
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid price format: {price}")

def validate_symbol(symbol):
    """Validates and returns an uppercase trading symbol."""
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string")
    
    symbol = symbol.strip().upper()
    
    # Strict checks for known invalid cases in tests
    if symbol.endswith('-'):
        raise ValidationError("Symbol cannot end with a dash")
    if re.match(r'^[0-9]+$', symbol):
        raise ValidationError("Symbol cannot be purely numeric")
    
    # Final regex check
    if not re.match(r'^[A-Z][A-Z0-9/-]{0,19}$', symbol):
        raise ValidationError(f"Invalid symbol format: {symbol}")
        
    return symbol

def validate_timestamp(ts):
    """Validates and returns a timezone-aware datetime object."""
    if ts is None: raise ValidationError("Timestamp cannot be None")
    try:
        if isinstance(ts, datetime):
            dt = ts
        elif isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            ts_str = str(ts).replace(' ', 'T')
            if not ts_str.endswith('Z') and '+' not in ts_str:
                ts_str += 'Z'
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        
        # Range check
        if dt.year < 2000 or dt.year > 2100:
            raise ValidationError("Timestamp out of range")
        return dt
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid timestamp: {ts}")

def validate_quantity(qty):
    """Validates and returns a positive Decimal quantity."""
    # We must be careful: validate_price(qty) might NOT raise if qty is -100 but we want it to raise for quantity too
    if qty is None: raise ValidationError("Quantity cannot be None")
    
    try:
        val = Decimal(str(qty))
        if val <= 0: raise ValidationError("Quantity must be greater than zero")
        return val
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid quantity: {qty}")

def validate_percentage(perc):
    """Validates and returns a Decimal percentage between 0 and 100."""
    if perc is None: raise ValidationError("Percentage cannot be None")
    try:
        if isinstance(perc, str):
            perc = perc.replace('%', '')
        val = Decimal(str(perc))
        if val < 0 or val > 100:
            raise ValidationError(f"Percentage must be between 0 and 100: {val}")
        return val
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid percentage: {perc}")

def validate_positive_number(val, name="Value"):
    """Generic positive number validator."""
    if val is None: raise ValidationError(f"{name} cannot be None")
    try:
        num = Decimal(str(val))
        if num < 0: raise ValidationError(f"{name} must be positive")
        return num
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid {name}: {val}")

def validate_api_key(key):
    """Validates API key length and content."""
    if not key or len(str(key).strip()) < 10:
        raise ValidationError("API Key is too short or empty")
    return str(key).strip()

def validate_email(email):
    """Simple email validator."""
    if not email or not re.match(r'[^@]+@[^@]+\.[^@]+', str(email)):
        raise ValidationError(f"Invalid email: {email}")
    return str(email).strip().lower()

def validate_file_path(path):
    """Validates that a file path is safe (not absolute or escaping)."""
    if not path or '..' in str(path) or str(path).startswith('/'):
        raise ValidationError(f"Invalid or unsafe file path: {path}")
    return str(path).strip()
