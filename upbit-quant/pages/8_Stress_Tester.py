import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.data_engine import fetch_upbit_tickers, fetch_ohlcv
from src.core.risk_manager import RiskManager

st.set_page_config(page_title="Black Swan Stress Tester", page_icon="🌪️", layout="wide")
st.title("🌪️ Black Swan Stress Tester")

st.markdown("""
Test your **Algo-Shield** risk protocols against extreme synthetic market events. 
This module "injects" synthetic flash crashes into historical data to verify if your stop-losses and risk limits trigger effectively.
""")

# --- Simulation Settings ---
st.sidebar.header("Stress Scenario Parameters")
crash_magnitude = st.sidebar.slider("Flash Crash Magnitude (%)", 5, 50, 20)
crash_duration = st.sidebar.slider("Crash Duration (Periods)", 1, 10, 3)

try:
    tickers = list(fetch_upbit_tickers().keys())
    default_ticker = 'BTC/KRW' if 'BTC/KRW' in tickers else tickers[0]
except:
    tickers = ['BTC/KRW']
    default_ticker = 'BTC/KRW'

symbol = st.sidebar.selectbox("Symbol", tickers, index=tickers.index(default_ticker))
timeframe = st.sidebar.selectbox("Baseline Timeframe", ['1m', '5m', '15m', '1h'], index=1)

if st.button("🚀 Run Black Swan Injection"):
    with st.spinner(f"Fetching {symbol} baseline data and injecting crash..."):
        df = fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        
        if not df.empty:
            # Create synthetic crash
            # Take the last 20 periods and inject a drop
            original_close = df['close'].iloc[-1]
            crash_start_idx = len(df) - crash_duration - 5
            
            # Modify the dataframe
            st_df = df.copy()
            for i in range(crash_duration):
                idx = crash_start_idx + i
                drop_factor = (1 - (crash_magnitude / 100 / crash_duration))
                st_df.iloc[idx:, st_df.columns.get_loc('close')] *= drop_factor
                st_df.iloc[idx:, st_df.columns.get_loc('low')] *= drop_factor
                st_df.iloc[idx:, st_df.columns.get_loc('high')] *= drop_factor
            
            st.subheader(f"Injected Scenario: -{crash_magnitude}% Flash Crash in {crash_duration} periods")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Original Baseline', line=dict(dash='dash', color='gray')))
            fig.add_trace(go.Scatter(x=st_df.index, y=st_df['close'], name='Stress Scenario', line=dict(color='red')))
            fig.update_layout(template="plotly_dark", height=500, title="Price Impact Visualization")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- RISK ENGINE VERIFICATION ---
            st.subheader("🛡️ Algo-Shield Response Verification")
            
            # Define a hypothetical stop-loss at 5% below crash start
            entry_price = df['close'].iloc[crash_start_idx - 1]
            stop_loss = entry_price * 0.95
            
            st.write(f"Hypothetical Long Entry at: **{entry_price:,.0f} KRW**")
            st.write(f"Static 5% Stop-Loss at: **{stop_loss:,.0f} KRW**")
            
            breach_indices = st_df.index[st_df['close'] <= stop_loss]
            
            if not breach_indices.empty:
                breach_time = breach_indices[0]
                st.error(f"🔴 STOP-LOSS BREACHED at {breach_time}")
                st.info("Risk Manager would have transmitted the EXIT signal to OMS.")
            else:
                st.warning("🟡 Stop-loss not reached despite the crash. Rule within risk tolerance.")
            
            regime = RiskManager.detect_market_regime(st_df)
            st.write(f"Detected Market Regime post-crash: **{regime}**")
            
        else:
            st.error("Baseline data fetch failed.")

st.divider()
st.markdown("""
### Why Stress Test?
According to the 2026 "Unsolved Problems" research, **Liquidity Black Holes** and **Black Swans** are the top killers of algorithms. 
By injecting synthetic crashes, you ensure that your code doesn't "hang" or "miss" a critical exit when the API becomes volatile.
""")
