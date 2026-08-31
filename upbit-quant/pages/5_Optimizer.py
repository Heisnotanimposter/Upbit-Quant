import streamlit as st
import vectorbt as vbt
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.data_engine import fetch_upbit_tickers, fetch_ohlcv
from src.utils.sampling import split_is_oos

st.set_page_config(page_title="QuantEvolve - Hyperparameter Optimizer", page_icon="🧬", layout="wide")
st.title("🧬 Strategy Optimizer (VectorBT Sweeps)")

st.markdown("""
Professional-grade strategy optimization using **VectorBT**. 
This page performs large-scale parameter sweeps across thousands of indicator combinations in parallel to find the most robust alpha factors.
""")

# --- Sidebar Configuration ---
st.sidebar.header("Optimization Workspace")
try:
    tickers = list(fetch_upbit_tickers().keys())
    default_ticker = 'BTC/KRW' if 'BTC/KRW' in tickers else tickers[0]
except:
    tickers = ['BTC/KRW']
    default_ticker = 'BTC/KRW'

symbol = st.sidebar.selectbox("Symbol", tickers, index=tickers.index(default_ticker))
timeframe = st.sidebar.selectbox("Timeframe", ['1h', '4h', '1d'], index=0)
limit = st.sidebar.slider("Historical Periods", 100, 2000, 1000)
is_ratio = st.sidebar.slider("IS/OOS Split Ratio", 0.5, 0.9, 0.7)

st.sidebar.divider()
st.sidebar.subheader("SMA Crossover Search Space")
fast_range = st.sidebar.slider("Fast SMA Range", 5, 50, (10, 20), step=2)
slow_range = st.sidebar.slider("Slow SMA Range", 20, 200, (30, 60), step=5)

# --- Execution ---
with st.spinner(f"Fetching {limit} data points for {symbol}..."):
    df = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

if not df.empty:
    close = df['close']
    
    st.info(f"🚀 Running optimization across **{len(range(fast_range[0], fast_range[1]+1, 2)) * len(range(slow_range[0], slow_range[1]+1, 5))}** parameter combinations...")
    
    with st.spinner("Executing vectorized IS/OOS simulation..."):
        is_df, oos_df = split_is_oos(df, is_ratio=is_ratio)
        
        # Define the parameter grids
        fast_sma_params = np.arange(fast_range[0], fast_range[1] + 1, 2)
        slow_sma_params = np.arange(slow_range[0], slow_range[1] + 1, 5)
        
        def run_backtest_all(target_df):
            cp = target_df['close']
            # Run MA with both parameter sets
            # We rename the column index names to prevent 'ma_window' collision
            f_ma = vbt.MA.run(cp, fast_sma_params).ma
            s_ma = vbt.MA.run(cp, slow_sma_params).ma
            
            f_ma.columns.name = 'fast_window'
            s_ma.columns.name = 'slow_window'
            
            # Broadcast against each other to create the grid (fast x slow)
            # By having different names, vbt will create a MultiIndex instead of trying to align
            ent = f_ma.vbt.crossed_above(s_ma, broadcast_kwargs=dict(index_from='both'))
            ext = f_ma.vbt.crossed_below(s_ma, broadcast_kwargs=dict(index_from='both'))
            
            return vbt.Portfolio.from_signals(cp, ent, ext, init_cash=1000000, fees=0.0005)

        is_pf = run_backtest_all(is_df)
        oos_pf = run_backtest_all(oos_df)
        
        # Calculate Returns for both
        is_returns = is_pf.total_return()
        oos_returns = oos_pf.total_return()
        
        # Robustness Score (Higher is better, meaning OOS performance matches IS)
        robustness = (oos_returns / is_returns).fillna(0)
        
        # Reshape for plotting
        # level=0 is 'fast_window', which becomes columns
        returns_unstacked = is_returns.unstack(level='fast_window')
        robustness_unstacked = robustness.unstack(level='fast_window')
        
    st.subheader("📊 Optimization Results: Strategy Heatmap")
    
    # Plot using Plotly Express
    fig_heat = px.imshow(
        returns_unstacked,
        labels=dict(x="Fast Window", y="Slow Window", color="In-Sample Return"),
        x=returns_unstacked.columns,
        y=returns_unstacked.index,
        color_continuous_scale="Viridis",
        title=f"In-Sample Return Heatmap ({symbol})"
    )
    fig_heat.update_layout(height=500, template="plotly_dark")
    st.plotly_chart(fig_heat, use_container_width=True)
    
    st.subheader("🧬 Alpha Robustness Heatmap (OOS / IS)")
    st.markdown("This heatmap shows the ratio of Out-of-Sample return to In-Sample return. **Bright zones** indicate parameters that generalized well to unseen data.")
    
    fig_robust = px.imshow(
        robustness_unstacked,
        labels=dict(x="Fast Window", y="Slow Window", color="Robustness Ratio"),
        x=robustness_unstacked.columns,
        y=robustness_unstacked.index,
        color_continuous_scale="Magma",
        title=f"Generalization Score ({symbol})"
    )
    fig_robust.update_layout(height=500, template="plotly_dark")
    st.plotly_chart(fig_robust, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    best_idx = is_returns.idxmax()
    with col1:
        st.success(f"**Optimal Parameters Found!**\n\n- Fast SMA: {best_idx[0]}\n- Slow SMA: {best_idx[1]}\n- Max IS Return: {is_returns.max()*100:.2f}%")
        
    with col2:
        st.markdown("**Metric Selection**")
        st.write("Current heatmap is based on *Total Return*. Future updates will support Sharpe Ratio and Maximum Drawdown sweeps.")

else:
    st.error("Data fetch failed. Please check network or API limits.")
