import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.data_engine import fetch_upbit_tickers, fetch_ohlcv, fetch_order_book
from src.core.risk_manager import RiskManager
from src.utils.sampling import generate_volume_bars

st.set_page_config(page_title="Market Dashboard", page_icon="📈", layout="wide")
st.title("📈 UPbit Market Dashboard")

# Fetch available markets
try:
    krw_markets = fetch_upbit_tickers()
    symbols = list(krw_markets.keys())
except Exception as e:
    st.error(f"Failed to fetch UPbit tickers: {e}")
    st.stop()

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Asset Selection")
    selected_symbol = st.selectbox("Select Trading Pair", symbols, index=symbols.index('BTC/KRW') if 'BTC/KRW' in symbols else 0)
    timeframe = st.selectbox("Timeframe", ['1m', '5m', '15m', '1h', '4h', '1d'], index=5)
    limit = st.slider("Periods to Fetch", min_value=10, max_value=500, value=100)
    
    # --- VOLUME BAR SAMPLING ADDITION ---
    st.divider()
    sampling_mode = st.radio("Sampling Logic", ["Time Bars (Standard)", "Volume Bars (Structural Edge)"])
    if sampling_mode == "Volume Bars (Structural Edge)":
         vol_threshold = st.number_input("Volume per Bar (KRW)", value=10000000, step=1000000)
    # --- END VOLUME BAR SAMPLING ---
    
    # --- MARKET REGIME ADDITION ---
    st.divider()
    st.subheader("Algo-Shield Monitor")
    df_regime = fetch_ohlcv(selected_symbol, timeframe=timeframe, limit=100)
    regime = RiskManager.detect_market_regime(df_regime)
    
    if "BULL" in regime:
         st.success(f"**Market Regime**: {regime}")
    elif "BEAR" in regime:
         st.error(f"**Market Regime**: {regime}")
    else:
         st.warning(f"**Market Regime**: {regime}")
    # --- END MARKET REGIME ---

with col2:
    st.subheader(f"Market Data: {selected_symbol}")
    with st.spinner("Fetching historical data..."):
        df = fetch_ohlcv(selected_symbol, timeframe=timeframe, limit=limit)
        
        if sampling_mode == "Volume Bars (Structural Edge)":
             df = generate_volume_bars(df, volume_threshold=vol_threshold)
    
    if not df.empty:
        # Plot using Plotly Candlestick
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=selected_symbol)])

        fig.update_layout(
            title=f"{selected_symbol} Price History ({timeframe})",
            yaxis_title='Price (KRW)',
            xaxis_title='Time',
            template='plotly_dark', # using a sleek dark mode for aesthetics
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    # --- ORDER BOOK DEPTH ADDITION ---
    st.divider()
    st.subheader(f"Level 2 Order Book Depth: {selected_symbol}")
    ob = fetch_order_book(selected_symbol, limit=20)
    
    if ob and 'bids' in ob and 'asks' in ob:
        bids = pd.DataFrame(ob['bids'], columns=['price', 'amount'])
        asks = pd.DataFrame(ob['asks'], columns=['price', 'amount'])
        
        # Sort for visual depth (Bids: Highest first, Asks: Lowest first)
        bids = bids.sort_values('price', ascending=False)
        asks = asks.sort_values('price', ascending=True)
        
        # Calculate cumulative volume
        bids['cumulative'] = bids['amount'].cumsum()
        asks['cumulative'] = asks['amount'].cumsum()
        
        fig_ob = go.Figure()
        
        # Bid side (Green)
        fig_ob.add_trace(go.Scatter(x=bids['price'], y=bids['cumulative'], fill='tozeroy', 
                                   name='Bids', line=dict(color='green'), fillcolor='rgba(0,255,0,0.3)'))
        # Ask side (Red)
        fig_ob.add_trace(go.Scatter(x=asks['price'], y=asks['cumulative'], fill='tozeroy', 
                                   name='Asks', line=dict(color='red'), fillcolor='rgba(255,0,0,0.3)'))
        
        fig_ob.update_layout(
            title=f"{selected_symbol} Market Depth",
            xaxis_title='Price (KRW)',
            yaxis_title='Cumulative Volume',
            template='plotly_dark',
            height=400,
            showlegend=True,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_ob, use_container_width=True)
    else:
        st.warning("Order book data unavailable.")

    # --- END ORDER BOOK DEPTH ---
