!pip install pyupbit
!pip install streamlit

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime  # For real-time data updates
import pyupbit  # For real-time crypto data 

ticker = kwr_tickers[0]  # Example: Get the first ticker
market_codes = upbit.get_market_all(isDetails=False)
krw_tickers = [code for code in market_codes if code.startswith("KRW-")]
df = upbit.get_ohlcv(ticker, interval="minute60", count=50)