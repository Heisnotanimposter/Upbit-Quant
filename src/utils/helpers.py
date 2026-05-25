from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from src.core.exceptions import ValidationError

def format_currency(amount, currency="USD", precision=2):
    """Formats an amount as currency."""
    try:
        val = Decimal(str(amount))
        sign = "$" if currency == "USD" else "₩"
        return f"{sign}{val:,.{precision}f}"
    except (InvalidOperation, ValueError):
        return f"Invalid amount: {amount}"

def calculate_percentage_change(old, new):
    """Calculates percentage change."""
    try:
        old_val, new_val = Decimal(str(old)), Decimal(str(new))
        if old_val == 0: raise ValidationError("Old value cannot be zero")
        return ((new_val - old_val) / old_val * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid values: {old}, {new}")

def safe_divide(n, d, default=0):
    """Divides n by d safely, returning default if d is zero."""
    try:
        num, den = Decimal(str(n)), Decimal(str(d))
        if den == 0: return default if default is not None else None
        return num / den
    except (InvalidOperation, ValueError):
        return default

def round_to_precision(val, precision=2):
    """Rounds a value to a specific precision."""
    try:
        return Decimal(str(val)).quantize(Decimal(f'1.{"0" * precision}'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal('0')

def format_percentage(val, precision=2):
    """Formats a value as a percentage string."""
    try:
        num = Decimal(str(val))
        return f"{num:.{precision}f}%"
    except (InvalidOperation, ValueError):
        return "0.00%"

def calculate_compound_interest(p, r, t):
    """Calculates compound interest."""
    try:
        p, r, t = Decimal(str(p)), Decimal(str(r)), Decimal(str(t))
        return p * (1 + r) ** t
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid values in compound interest: {p}, {r}, {t}")

def calculate_simple_interest(p, r, t):
    """Calculates simple interest."""
    try:
        p, r, t = Decimal(str(p)), Decimal(str(r)), Decimal(str(t))
        return p * r * t
    except (InvalidOperation, ValueError):
        raise ValidationError("Invalid simple interest values")

def calculate_moving_average(values, window):
    """Calculates a simple moving average of a list."""
    if not values or len(values) < window or window <= 0:
        raise ValidationError("Invalid values or window size")
    try:
        nums = [Decimal(str(v)) for v in values]
        return [sum(nums[i:i+window]) / window for i in range(len(nums) - window + 1)]
    except (InvalidOperation, ValueError):
        raise ValidationError("Invalid numeric values for MA")

def calculate_volatility(prices):
    """Calculates price volatility (standard deviation of returns)."""
    if len(prices) < 2: raise ValidationError("Insufficient data for volatility")
    try:
        df = pd.Series([float(p) for p in prices])
        returns = df.pct_change().dropna()
        return Decimal(str(returns.std())).quantize(Decimal('0.0001'))
    except Exception:
        raise ValidationError("Volatility calculation failed")

def normalize_data(values):
    """Normalizes data to 0-1 range."""
    if not values: return []
    if len(values) == 1: return [Decimal('0.50')]
    try:
        nums = [float(v) for v in values]
        min_v, max_v = min(nums), max(nums)
        if min_v == max_v: return [Decimal('0.50')] * len(values)
        norm = [(v - min_v) / (max_v - min_v) for v in nums]
        return [Decimal(str(v)).quantize(Decimal('0.01')) for v in norm]
    except Exception:
        raise ValidationError("Normalization failed")

def generate_timestamp():
    """Generates an ISO timestamp."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def parse_timestamp(ts):
    """Parses a timestamp string to datetime."""
    try:
        ts_str = str(ts).replace(' ', 'T')
        if not ts_str.endswith('Z') and '+' not in ts_str:
            ts_str += 'Z'
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except Exception:
        raise ValidationError(f"Could not parse timestamp: {ts}")

def deep_merge_dicts(d1, d2):
    """Deep merges two dictionaries."""
    result = d1.copy()
    for k, v in d2.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge_dicts(result[k], v)
        else:
            result[k] = v
    return result

def chunk_list(lst, size):
    """Splits a list into chunks."""
    if size <= 0: raise ValidationError("Chunk size must be positive")
    return [lst[i:i + size] for i in range(0, len(lst), size)]

def flatten_list(lst):
    """Flattens a nested list."""
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten_list(i))
        else:
            result.append(i)
    return result
