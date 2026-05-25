import pandas as pd
import numpy as np

def generate_volume_bars(df, volume_threshold=1000.0):
    """
    Groups standard OHLCV data into Volume Bars.
    Each bar represents 'volume_threshold' amount of activity rather than time.
    """
    if df.empty: return df
    
    # Cumulative volume logic
    df['cum_v'] = df['volume'].cumsum()
    df['v_group'] = (df['cum_v'] // volume_threshold).astype(int)
    
    # Aggregate by v_group
    v_bars = df.groupby('v_group').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Reset index and return
    v_bars.index = pd.RangeIndex(len(v_bars))
    return v_bars

def split_is_oos(df, is_ratio=0.7):
    """
    Splits the data into In-Sample (IS) and Out-of-Sample (OOS).
    IS is used for training/optimization, OOS for final robust validation.
    """
    split_idx = int(len(df) * is_ratio)
    is_df = df.iloc[:split_idx]
    oos_df = df.iloc[split_idx:]
    return is_df, oos_df
