import ccxt
import pandas as pd
import datetime
import streamlit as st

@st.cache_data(ttl=60)
def fetch_upbit_tickers():
    """Fetches all tickers from UPbit currently available."""
    exchange = ccxt.upbit()
    markets = exchange.load_markets()
    krw_markets = {sym: market for sym, market in markets.items() if market['quote'] == 'KRW'}
    return krw_markets

@st.cache_data(ttl=300)
def fetch_ohlcv(symbol, timeframe='1d', limit=100):
    """Fetches OHLCV data for a specific UPbit symbol."""
    exchange = ccxt.upbit()
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def fetch_order_book(symbol, limit=20):
    """Fetches real-time Level 2 order book data for a specific UPbit symbol."""
    exchange = ccxt.upbit()
    try:
        order_book = exchange.fetch_order_book(symbol, limit=limit)
        return order_book
    except Exception as e:
        print(f"Error fetching order book for {symbol}: {e}")
        return None
