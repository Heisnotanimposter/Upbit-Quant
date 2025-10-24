"""
Tests for helper utilities.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from upbit_quant.utils.helpers import (
    format_currency,
    calculate_percentage_change,
    safe_divide,
    round_to_precision,
    format_percentage,
    calculate_compound_interest,
    calculate_simple_interest,
    calculate_moving_average,
    calculate_volatility,
    normalize_data,
    generate_timestamp,
    parse_timestamp,
    deep_merge_dicts,
    chunk_list,
    flatten_list,
)
from upbit_quant.core.exceptions import ValidationError


class TestFormatCurrency:
    """Test currency formatting."""
    
    def test_format_usd(self):
        """Test USD currency formatting."""
        assert format_currency(1000.50) == "$1,000.50"
        assert format_currency(1000000) == "$1,000,000.00"
        assert format_currency(0) == "$0.00"
    
    def test_format_krw(self):
        """Test KRW currency formatting."""
        assert format_currency(1000.50, "KRW") == "₩1,000.50"
        assert format_currency(1000000, "KRW") == "₩1,000,000.00"
    
    def test_format_with_precision(self):
        """Test currency formatting with precision."""
        assert format_currency(1000.123, "USD", 3) == "$1,000.123"
        assert format_currency(1000.123, "USD", 0) == "$1,000"
    
    def test_format_invalid_amount(self):
        """Test currency formatting with invalid amount."""
        assert format_currency("invalid") == "Invalid amount: invalid"


class TestCalculatePercentageChange:
    """Test percentage change calculation."""
    
    def test_positive_change(self):
        """Test positive percentage change."""
        change = calculate_percentage_change(100, 110)
        assert change == Decimal('10.00')
    
    def test_negative_change(self):
        """Test negative percentage change."""
        change = calculate_percentage_change(100, 90)
        assert change == Decimal('-10.00')
    
    def test_no_change(self):
        """Test no percentage change."""
        change = calculate_percentage_change(100, 100)
        assert change == Decimal('0.00')
    
    def test_zero_old_value(self):
        """Test percentage change with zero old value."""
        with pytest.raises(ValidationError):
            calculate_percentage_change(0, 100)
    
    def test_invalid_values(self):
        """Test percentage change with invalid values."""
        with pytest.raises(ValidationError):
            calculate_percentage_change("invalid", 100)


class TestSafeDivide:
    """Test safe division."""
    
    def test_normal_division(self):
        """Test normal division."""
        result = safe_divide(10, 2)
        assert result == Decimal('5')
    
    def test_division_by_zero(self):
        """Test division by zero."""
        result = safe_divide(10, 0)
        assert result == 0
        
        result = safe_divide(10, 0, default=None)
        assert result is None
    
    def test_invalid_values(self):
        """Test division with invalid values."""
        result = safe_divide("invalid", 2)
        assert result == 0


class TestRoundToPrecision:
    """Test rounding to precision."""
    
    def test_round_to_precision(self):
        """Test rounding to specified precision."""
        assert round_to_precision(1.2345, 2) == Decimal('1.23')
        assert round_to_precision(1.2355, 2) == Decimal('1.24')  # Round up
        assert round_to_precision(1.2345, 3) == Decimal('1.235')
    
    def test_round_invalid_value(self):
        """Test rounding invalid value."""
        assert round_to_precision("invalid", 2) == Decimal('0')


class TestFormatPercentage:
    """Test percentage formatting."""
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(50.123) == "50.12%"
        assert format_percentage(0) == "0.00%"
        assert format_percentage(100) == "100.00%"
    
    def test_format_percentage_with_precision(self):
        """Test percentage formatting with precision."""
        assert format_percentage(50.123, 1) == "50.1%"
        assert format_percentage(50.123, 3) == "50.123%"
    
    def test_format_invalid_percentage(self):
        """Test percentage formatting with invalid value."""
        assert format_percentage("invalid") == "0.00%"


class TestCalculateCompoundInterest:
    """Test compound interest calculation."""
    
    def test_compound_interest(self):
        """Test compound interest calculation."""
        amount = calculate_compound_interest(1000, 0.05, 2)
        assert amount == Decimal('1102.50')
    
    def test_compound_interest_zero_rate(self):
        """Test compound interest with zero rate."""
        amount = calculate_compound_interest(1000, 0, 2)
        assert amount == Decimal('1000.00')
    
    def test_invalid_values(self):
        """Test compound interest with invalid values."""
        with pytest.raises(ValidationError):
            calculate_compound_interest("invalid", 0.05, 2)


class TestCalculateSimpleInterest:
    """Test simple interest calculation."""
    
    def test_simple_interest(self):
        """Test simple interest calculation."""
        interest = calculate_simple_interest(1000, 0.05, 2)
        assert interest == Decimal('100.00')
    
    def test_simple_interest_zero_rate(self):
        """Test simple interest with zero rate."""
        interest = calculate_simple_interest(1000, 0, 2)
        assert interest == Decimal('0.00')
    
    def test_invalid_values(self):
        """Test simple interest with invalid values."""
        with pytest.raises(ValidationError):
            calculate_simple_interest("invalid", 0.05, 2)


class TestCalculateMovingAverage:
    """Test moving average calculation."""
    
    def test_moving_average(self):
        """Test moving average calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = calculate_moving_average(values, 3)
        expected = [Decimal('2.00'), Decimal('3.00'), Decimal('4.00'), 
                   Decimal('5.00'), Decimal('6.00'), Decimal('7.00'), 
                   Decimal('8.00'), Decimal('9.00')]
        assert result == expected
    
    def test_moving_average_invalid_window(self):
        """Test moving average with invalid window size."""
        with pytest.raises(ValidationError):
            calculate_moving_average([1, 2, 3], 0)
        
        with pytest.raises(ValidationError):
            calculate_moving_average([1, 2, 3], 5)
    
    def test_moving_average_invalid_values(self):
        """Test moving average with invalid values."""
        with pytest.raises(ValidationError):
            calculate_moving_average(["invalid", 2, 3], 2)


class TestCalculateVolatility:
    """Test volatility calculation."""
    
    def test_volatility(self):
        """Test volatility calculation."""
        prices = [100, 105, 110, 108, 112, 115, 113, 118, 120, 122]
        volatility = calculate_volatility(prices)
        assert isinstance(volatility, Decimal)
        assert volatility > 0
    
    def test_volatility_insufficient_data(self):
        """Test volatility with insufficient data."""
        with pytest.raises(ValidationError):
            calculate_volatility([100])
    
    def test_volatility_invalid_values(self):
        """Test volatility with invalid values."""
        with pytest.raises(ValidationError):
            calculate_volatility(["invalid", 105, 110])


class TestNormalizeData:
    """Test data normalization."""
    
    def test_normalize_data(self):
        """Test data normalization."""
        values = [1, 2, 3, 4, 5]
        result = normalize_data(values)
        assert result[0] == Decimal('0.00')
        assert result[-1] == Decimal('1.00')
        assert len(result) == len(values)
    
    def test_normalize_empty_data(self):
        """Test normalization of empty data."""
        result = normalize_data([])
        assert result == []
    
    def test_normalize_single_value(self):
        """Test normalization of single value."""
        result = normalize_data([5])
        assert result == [Decimal('0.50')]
    
    def test_normalize_identical_values(self):
        """Test normalization of identical values."""
        result = normalize_data([5, 5, 5])
        assert all(val == Decimal('0.50') for val in result)
    
    def test_normalize_invalid_values(self):
        """Test normalization with invalid values."""
        with pytest.raises(ValidationError):
            normalize_data(["invalid", 2, 3])


class TestGenerateTimestamp:
    """Test timestamp generation."""
    
    def test_generate_timestamp(self):
        """Test timestamp generation."""
        timestamp = generate_timestamp()
        assert isinstance(timestamp, str)
        assert 'T' in timestamp
        assert 'Z' in timestamp or '+' in timestamp


class TestParseTimestamp:
    """Test timestamp parsing."""
    
    def test_parse_iso_timestamp(self):
        """Test parsing ISO timestamp."""
        dt = parse_timestamp("2023-01-01T00:00:00Z")
        assert isinstance(dt, datetime)
        assert dt.year == 2023
    
    def test_parse_other_formats(self):
        """Test parsing other timestamp formats."""
        dt = parse_timestamp("2023-01-01 00:00:00")
        assert isinstance(dt, datetime)
        assert dt.year == 2023
    
    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamp."""
        with pytest.raises(ValidationError):
            parse_timestamp("invalid")


class TestDeepMergeDicts:
    """Test deep dictionary merging."""
    
    def test_deep_merge(self):
        """Test deep dictionary merging."""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        assert result == expected
    
    def test_deep_merge_overwrite(self):
        """Test deep dictionary merging with overwrite."""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"c": 3}, "d": 4}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": {"c": 3}, "d": 4}
        assert result == expected


class TestChunkList:
    """Test list chunking."""
    
    def test_chunk_list(self):
        """Test list chunking."""
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = chunk_list(lst, 3)
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        assert result == expected
    
    def test_chunk_list_invalid_size(self):
        """Test chunking with invalid size."""
        with pytest.raises(ValidationError):
            chunk_list([1, 2, 3], 0)
    
    def test_chunk_list_empty(self):
        """Test chunking empty list."""
        result = chunk_list([], 3)
        assert result == []


class TestFlattenList:
    """Test list flattening."""
    
    def test_flatten_list(self):
        """Test list flattening."""
        nested_list = [[1, 2], [3, 4], [5, 6]]
        result = flatten_list(nested_list)
        expected = [1, 2, 3, 4, 5, 6]
        assert result == expected
    
    def test_flatten_deeply_nested(self):
        """Test flattening deeply nested list."""
        nested_list = [[1, [2, 3]], [4, [5, [6, 7]]]]
        result = flatten_list(nested_list)
        expected = [1, 2, 3, 4, 5, 6, 7]
        assert result == expected
    
    def test_flatten_empty_list(self):
        """Test flattening empty list."""
        result = flatten_list([])
        assert result == []
