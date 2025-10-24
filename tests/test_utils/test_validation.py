"""
Tests for validation utilities.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from upbit_quant.utils.validation import (
    validate_price,
    validate_symbol,
    validate_timestamp,
    validate_quantity,
    validate_percentage,
    validate_positive_number,
    validate_api_key,
    validate_email,
    validate_file_path,
)
from upbit_quant.core.exceptions import ValidationError


class TestValidatePrice:
    """Test price validation."""
    
    def test_valid_price_string(self):
        """Test valid price string."""
        assert validate_price("100.50") == Decimal('100.50')
        assert validate_price("100") == Decimal('100')
        assert validate_price("0") == Decimal('0')
    
    def test_valid_price_numeric(self):
        """Test valid price numeric types."""
        assert validate_price(100.50) == Decimal('100.50')
        assert validate_price(100) == Decimal('100')
        assert validate_price(Decimal('100.50')) == Decimal('100.50')
    
    def test_valid_price_with_currency(self):
        """Test valid price with currency symbols."""
        assert validate_price("$100.50") == Decimal('100.50')
        assert validate_price("₩100.50") == Decimal('100.50')
        assert validate_price("USD 100.50") == Decimal('100.50')
    
    def test_invalid_price_negative(self):
        """Test invalid negative price."""
        with pytest.raises(ValidationError):
            validate_price("-100.50")
        
        with pytest.raises(ValidationError):
            validate_price(-100.50)
    
    def test_invalid_price_format(self):
        """Test invalid price format."""
        with pytest.raises(ValidationError):
            validate_price("abc")
        
        with pytest.raises(ValidationError):
            validate_price("")
        
        with pytest.raises(ValidationError):
            validate_price(None)


class TestValidateSymbol:
    """Test symbol validation."""
    
    def test_valid_symbols(self):
        """Test valid trading symbols."""
        assert validate_symbol("BTC") == "BTC"
        assert validate_symbol("ETH") == "ETH"
        assert validate_symbol("BTC-KRW") == "BTC-KRW"
        assert validate_symbol("ADA-USDT") == "ADA-USDT"
        assert validate_symbol("btc") == "BTC"  # Should be uppercase
    
    def test_invalid_symbols(self):
        """Test invalid trading symbols."""
        with pytest.raises(ValidationError):
            validate_symbol("")
        
        with pytest.raises(ValidationError):
            validate_symbol("BTC-")
        
        with pytest.raises(ValidationError):
            validate_symbol("123")
        
        with pytest.raises(ValidationError):
            validate_symbol(None)
        
        with pytest.raises(ValidationError):
            validate_symbol("BTC@KRW")
    
    def test_symbol_length_limit(self):
        """Test symbol length limit."""
        long_symbol = "A" * 21  # Too long
        with pytest.raises(ValidationError):
            validate_symbol(long_symbol)


class TestValidateTimestamp:
    """Test timestamp validation."""
    
    def test_valid_iso_timestamps(self):
        """Test valid ISO timestamp strings."""
        dt = validate_timestamp("2023-01-01T00:00:00Z")
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None
        
        dt = validate_timestamp("2023-01-01T00:00:00+00:00")
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None
    
    def test_valid_datetime_objects(self):
        """Test valid datetime objects."""
        dt = datetime.now(timezone.utc)
        result = validate_timestamp(dt)
        assert result == dt
    
    def test_valid_unix_timestamps(self):
        """Test valid Unix timestamps."""
        dt = validate_timestamp(1672531200)  # 2023-01-01 00:00:00 UTC
        assert isinstance(dt, datetime)
        assert dt.year == 2023
    
    def test_invalid_timestamps(self):
        """Test invalid timestamps."""
        with pytest.raises(ValidationError):
            validate_timestamp("invalid")
        
        with pytest.raises(ValidationError):
            validate_timestamp("")
        
        with pytest.raises(ValidationError):
            validate_timestamp(None)
        
        with pytest.raises(ValidationError):
            validate_timestamp("2023-13-01")  # Invalid month
    
    def test_timestamp_range_validation(self):
        """Test timestamp range validation."""
        # Too old
        with pytest.raises(ValidationError):
            validate_timestamp("1999-01-01T00:00:00Z")
        
        # Too far in future
        with pytest.raises(ValidationError):
            validate_timestamp("2101-01-01T00:00:00Z")


class TestValidateQuantity:
    """Test quantity validation."""
    
    def test_valid_quantities(self):
        """Test valid quantities."""
        assert validate_quantity("100.50") == Decimal('100.50')
        assert validate_quantity(100.50) == Decimal('100.50')
        assert validate_quantity(100) == Decimal('100')
        assert validate_quantity(Decimal('100.50')) == Decimal('100.50')
    
    def test_invalid_quantities(self):
        """Test invalid quantities."""
        with pytest.raises(ValidationError):
            validate_quantity("0")
        
        with pytest.raises(ValidationError):
            validate_quantity("-100")
        
        with pytest.raises(ValidationError):
            validate_quantity("abc")
        
        with pytest.raises(ValidationError):
            validate_quantity("")


class TestValidatePercentage:
    """Test percentage validation."""
    
    def test_valid_percentages(self):
        """Test valid percentages."""
        assert validate_percentage("50") == Decimal('50')
        assert validate_percentage("50%") == Decimal('50')
        assert validate_percentage(50) == Decimal('50')
        assert validate_percentage(0) == Decimal('0')
        assert validate_percentage(100) == Decimal('100')
    
    def test_invalid_percentages(self):
        """Test invalid percentages."""
        with pytest.raises(ValidationError):
            validate_percentage("-10")
        
        with pytest.raises(ValidationError):
            validate_percentage("150")
        
        with pytest.raises(ValidationError):
            validate_percentage("abc")
        
        with pytest.raises(ValidationError):
            validate_percentage("")


class TestValidatePositiveNumber:
    """Test positive number validation."""
    
    def test_valid_positive_numbers(self):
        """Test valid positive numbers."""
        assert validate_positive_number("100.50", "test") == Decimal('100.50')
        assert validate_positive_number(100.50, "test") == Decimal('100.50')
        assert validate_positive_number(0, "test") == Decimal('0')
    
    def test_invalid_positive_numbers(self):
        """Test invalid positive numbers."""
        with pytest.raises(ValidationError):
            validate_positive_number("-100", "test")
        
        with pytest.raises(ValidationError):
            validate_positive_number("abc", "test")


class TestValidateApiKey:
    """Test API key validation."""
    
    def test_valid_api_keys(self):
        """Test valid API keys."""
        assert validate_api_key("valid_api_key_123") == "valid_api_key_123"
        assert validate_api_key("  valid_api_key_123  ") == "valid_api_key_123"
    
    def test_invalid_api_keys(self):
        """Test invalid API keys."""
        with pytest.raises(ValidationError):
            validate_api_key("")
        
        with pytest.raises(ValidationError):
            validate_api_key("short")
        
        with pytest.raises(ValidationError):
            validate_api_key(None)


class TestValidateEmail:
    """Test email validation."""
    
    def test_valid_emails(self):
        """Test valid email addresses."""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("  TEST@EXAMPLE.COM  ") == "test@example.com"
        assert validate_email("user.name@domain.co.uk") == "user.name@domain.co.uk"
    
    def test_invalid_emails(self):
        """Test invalid email addresses."""
        with pytest.raises(ValidationError):
            validate_email("invalid-email")
        
        with pytest.raises(ValidationError):
            validate_email("@example.com")
        
        with pytest.raises(ValidationError):
            validate_email("test@")
        
        with pytest.raises(ValidationError):
            validate_email("")
        
        with pytest.raises(ValidationError):
            validate_email(None)


class TestValidateFilePath:
    """Test file path validation."""
    
    def test_valid_file_paths(self):
        """Test valid file paths."""
        assert validate_file_path("data/file.csv") == "data/file.csv"
        assert validate_file_path("  data/file.csv  ") == "data/file.csv"
        assert validate_file_path("file.txt") == "file.txt"
    
    def test_invalid_file_paths(self):
        """Test invalid file paths."""
        with pytest.raises(ValidationError):
            validate_file_path("../file.csv")
        
        with pytest.raises(ValidationError):
            validate_file_path("/absolute/path")
        
        with pytest.raises(ValidationError):
            validate_file_path("")
        
        with pytest.raises(ValidationError):
            validate_file_path(None)
