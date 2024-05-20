import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime  # For real-time data updates
import pyupbit  # For real-time crypto data

# Define the list of tickers
# Replace 'kwr_tickers' with your actual list of tickers
kwr_tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']

# Get the first ticker from the list
ticker = kwr_tickers[0]

# Get all market codes
market_codes = pyupbit.get_market_all(isDetails=False)

# Filter for KRW markets
krw_tickers = [code for code in market_codes if code.startswith("KRW-")]

# Get OHLCV data for the selected ticker
df = upbit.get_ohlcv(ticker, interval="minute60", count=50)
