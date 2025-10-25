"""
Helper utilities for UPbit Quantitative Trading Platform.
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

from ..core.exceptions import ValidationError


def format_currency(amount: Union[float, int, Decimal], currency: str = "USD", precision: int = 2) -> str:
    """Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code
        precision: Decimal precision
        
    Returns:
        Formatted currency string
    """
    try:
        decimal_amount = Decimal(str(amount))
        formatted_amount = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        if currency.upper() == "USD":
            return f"${formatted_amount:,.{precision}f}"
        elif currency.upper() == "KRW":
            return f"₩{formatted_amount:,.{precision}f}"
        else:
            return f"{formatted_amount:,.{precision}fCHARACTERS"
    except (ValueError, TypeError):
        return f"Invalid amount: {amount}"


def calculate_percentage_change(old_value: Union[float, int, Decimal], new_value: Union[float, int, Decimal]) -> Decimal:
    """Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change as Decimal
        
    Raises:
        ValidationError: If old_value is zero
    """
    try:
        old_decimal = Decimal(str(old_value))
        new_decimal = Decimal(str(new_value))
        
        if old_decimal == 0:
            raise ValidationError("Cannot calculate percentage change with zero old value")
        
        change = ((new_decimal - old_decimal) / old_decimal) * 100
        return change.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid values for percentage calculation: {old_value}, {new_value}") from e


def safe_divide(numerator: Union[float, int, Decimal], denominator: Union[float, int, Decimal], default: Any = 0) -> Any:
    """Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if denominator is zero
        
    Returns:
        Division result or default value
    """
    try:
        numerator_decimal = Decimal(str(numerator))
        denominator_decimal = Decimal(str(denominator))
        
        if denominator_decimal == 0:
            return default
        
        return numerator_decimal / denominator_decimal
        
    except (ValueError, TypeError):
        return default


def round_to_precision(value: Union[float, int, Decimal], precision: int) -> Decimal:
    """Round value to specified precision.
    
    Args:
        value: Value to round
        precision: Number of decimal places
        
    Returns:
        Rounded Decimal value
    """
    try:
        decimal_value = Decimal(str(value))
        precision_decimal = Decimal('0.' + '0' * precision)
        return decimal_value.quantize(precision_decimal, rounding=ROUND_HALF_UP)
    except (ValueError, TypeError):
        return Decimal('0')


def format_percentage(value: Union[float, int, Decimal], precision: int = 2) -> str:
    """Format value as percentage string.
    
    Args:
        value: Value to format as percentage
        precision: Decimal precision
        
    Returns:
        Formatted percentage string
    """
    try:
        decimal_value = Decimal(str(value))
        rounded_value = round_to_precision(decimal_value, precision)
        return f"{rounded_value}%"
    except (ValueError, TypeError):
        return "0.00%"


def calculate_compound_interest(principal: Union[float, int, Decimal], rate: Union[float, int, Decimal], time_periods: int) -> Decimal:
    """Calculate compound interest.
    
    Args:
        principal: Initial principal amount
        rate: Interest rate (as decimal, e.g., 0.05 for 5%)
        time_periods: Number of time periods
        
    Returns:
        Final amount after compound interest
    """
    try:
        principal_decimal = Decimal(str(principal))
        rate_decimal = Decimal(str(rate))
        time_decimal = Decimal(str(time_periods))
        
        amount = principal_decimal * ((1 + rate_decimal) ** time_decimal)
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid values for compound interest calculation") from e


def calculate_simple_interest(principal: Union[float, int, Decimal], rate: Union[float, int, Decimal], time_periods: int) -> Decimal:
    """Calculate simple interest.
    
    Args:
        principal: Initial principal amount
        rate: Interest rate (as decimal, e.g., 0.05 for 5%)
        time_periods: Number of time periods
        
    Returns:
        Interest amount
    """
    try:
        principal_decimal = Decimal(str(principal))
        rate_decimal = Decimal(str(rate))
        time_decimal = Decimal(str(time_periods))
        
        interest = principal_decimal * rate_decimal * time_decimal
        return interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid values for simple interest calculation") from e


def calculate_moving_average(values: List[Union[float, int, Decimal]], window_size: int) -> List[Decimal]:
    """Calculate moving average for a list of values.
    
    Args:
        values: List of values
        window_size: Size of the moving window
        
    Returns:
        List of moving average values
    """
    if window_size <= 0 or window_size > len(values):
        raise ValidationError(f"Invalid window size: {window_size}")
    
    try:
        decimal_values = [Decimal(str(v)) for v in values]
        moving_averages = []
        
        for i in range(window_size - 1, len(decimal_values)):
            window_sum = sum(decimal_values[i - window_size + 1:i + 1])
            average = window_sum / Decimal(str(window_size))
            moving_averages.append(average.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return moving_averages
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid values for moving average calculation") from e


def calculate_volatility(prices: List[Union[float, int, Decimal]]) -> Decimal:
    """Calculate price volatility (standard deviation).
    
    Args:
        prices: List of price values
        
    Returns:
        Volatility as Decimal
    """
    if len(prices) < 2:
        raise ValidationError("Need at least 2 prices to calculate volatility")
    
    try:
        decimal_prices = [Decimal(str(p)) for p in prices]
        
        # Calculate mean
        mean = sum(decimal_prices) / Decimal(str(len(decimal_prices)))
        
        # Calculate variance
        variance = sum((p - mean) ** 2 for p in decimal_prices) / Decimal(str(len(decimal_prices)))
        
        # Calculate standard deviation
        volatility = variance.sqrt()
        
        return volatility.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid values for volatility calculation") from e


def normalize_data(values: List[Union[float, int, Decimal]]) -> List[Decimal]:
    """Normalize data to 0-1 range.
    
    Args:
        values: List of values to normalize
        
    Returns:
        List of normalized values
    """
    if not values:
        return []
    
    try:
        decimal_values = [Decimal(str(v)) for v in values]
        min_value = min(decimal_values)
        max_value = max(decimal_values)
        
        if max_value == min_value:
            return [Decimal('0.5')] * len(decimal_values)
        
        normalized = [(v - min_value) / (max_value - min_value) for v in decimal_values]
        return [n.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) for n in normalized]
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid values for normalization") from e


def generate_timestamp() -> str:
    """Generate current timestamp as ISO string.
    
    Returns:
        ISO timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        Datetime object
    """
    try:
        # Try parsing ISO format
        if 'T' in timestamp_str:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # Try parsing other common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    except Exception as e:
        raise ValidationError(f"Invalid timestamp format: {timestamp_str}") from e


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValidationError("Chunk size must be positive")
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """Flatten nested list.
    
    Args:
        nested_list: Nested list to flatten
        
    Returns:
        Flattened list
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result
