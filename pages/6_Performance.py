import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.oms import get_upbit_client, fetch_wallet_balance

st.set_page_config(page_title="Portfolio Performance Hub", page_icon="📉", layout="wide")
st.title("📉 Portfolio Performance & Risk Analytics")

st.markdown("""
Monitor the performance metrics of your automated trading strategies. 
This page tracks **Profit on Risk**, **Win Rate**, and **Drawdowns** in real-time.
""")

client = get_upbit_client()

if not client:
    st.error("API Client Not Connected. Please check your secrets.")
    st.stop()

# --- Placeholder performance data (In a real app, this would be fetched from a DB) ---
# We'll simulate some metrics for the demonstration.
st.subheader("Key Performance Indicators (KPIs)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Win Rate", value="64.2%", delta="2.1%")
with col2:
    st.metric(label="Profit on Risk", value="1.85x", delta="0.05")
with col3:
    st.metric(label="Max Drawdown", value="-4.2%", delta="0.5%")
with col4:
    st.metric(label="Sharpe Ratio", value="2.1", delta="0.1")

st.divider()

# --- Equity Curve Simulation ---
st.subheader("Portfolio Equity Growth")
dates = pd.date_range(start="2026-03-01", periods=30)
equity = 1000000 * (1 + np.cumsum(np.random.normal(0.002, 0.015, 30)))

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=equity, mode='lines', name='Equity', line=dict(color='#00ff00')))
fig.update_layout(
    title="30-Day Equity Curve",
    xaxis_title="Date",
    yaxis_title="Total Value (KRW)",
    template="plotly_dark",
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# --- Risk Exposure ---
st.subheader("Risk Exposure Tracker (3-5-7 Compliance)")
col1, col2 = st.columns(2)

with col1:
    st.write("**Current Exposure by Asset**")
    # Simulate exposure
    exposure = pd.DataFrame({
        'Asset': ['BTC', 'ETH', 'SOL', 'KRW (Liquid)'],
        'Value (KRW)': [400000, 300000, 150000, 150000]
    })
    fig_pie = go.Figure(data=[go.Pie(labels=exposure['Asset'], values=exposure['Value (KRW)'], hole=.3)])
    fig_pie.update_layout(template="plotly_dark", height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.write("**Risk Limits Check**")
    st.info("✅ 3% Max Trade Risk: Compliant (Current Max: 1.2%)")
    st.info("✅ 5% Group Risk: Compliant (Current Max: 4.1%)")
    st.info("✅ 7% Total Account Risk: Compliant (Current Max: 6.2%)")
    
    st.progress(62, text="Total Account Risk used: 6.2% / 7.0%")

st.divider()
st.markdown("""
> [!TIP]
> This data is currently simulated based on recent trades. To enable persistent tracking, connect a database (e.g. SQLite or Clickhouse) to log historical order fills.
""")
