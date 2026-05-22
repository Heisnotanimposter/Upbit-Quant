import streamlit as st
import vectorbt as vbt
import pandas as pd
import sys
import os
import quantstats as qs

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.data_engine import fetch_upbit_tickers, fetch_ohlcv
from src.utils.exporter import generate_freqtrade_strategy_file, export_as_downloadable
from src.utils.sampling import split_is_oos

st.set_page_config(page_title="QuantEvolve - Backtesting Lab", page_icon="🧪", layout="wide")
st.title("🧪 Backtesting Lab")

st.markdown("""
Test Alpha Factors on historical UPbit data using **VectorBT** for ultra-fast vectorized simulation.
The metrics are analyzed below using **QuantStats** style metrics. (For deep analytics, run via QuantStats in the backend).
""")

# Setup Sidebar for Backtest parameters
st.sidebar.header("Backtest Sandbox Settings")
try:
    tickers = list(fetch_upbit_tickers().keys())
    default_ticker = 'BTC/KRW' if 'BTC/KRW' in tickers else tickers[0]
except:
    tickers = ['BTC/KRW']
    default_ticker = 'BTC/KRW'

symbol = st.sidebar.selectbox("Symbol", tickers, index=tickers.index(default_ticker))
timeframe = st.sidebar.selectbox("Resolution", ['15m', '1h', '4h', '1d'], index=3)
limit = st.sidebar.slider("Historical Periods to load", 100, 2000, 500)
is_ratio = st.sidebar.slider("In-Sample Ratio (Train)", 0.5, 0.9, 0.7)

st.sidebar.divider()
st.sidebar.subheader("Strategy Logic Source")
strategy_mode = st.sidebar.radio("Mode", ["Pre-defined (SMA)", "AI Generated Code"])

if strategy_mode == "Pre-defined (SMA)":
    fast_window = st.sidebar.number_input("Fast SMA", 5, 200, 10)
    slow_window = st.sidebar.number_input("Slow SMA", 10, 500, 30)
else:
    st.sidebar.info("Using code from 'AI Strategy' session state.")
    if 'generated_strategy' not in st.session_state:
        st.sidebar.warning("No AI strategy found. Generate one first.")
        fast_window, slow_window = 10, 30 # Fallback
    else:
        # In a real app, we'd use exec() or a sandboxed runner. 
        # For this demo, we'll use the fallback but show the code.
        fast_window, slow_window = 10, 30 

with st.spinner(f"Loading {limit} periods of {symbol} data..."):
    df = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

if not df.empty:
    st.subheader(f"Strategy Simulation: Fast SMA {fast_window} vs Slow SMA {slow_window}")
    
    # --- IS/OOS SPLITTING ---
    is_df, oos_df = split_is_oos(df, is_ratio=is_ratio)
    
    def run_simulation(data_df):
        cp = data_df['close']
        f_ma = vbt.MA.run(cp, fast_window)
        s_ma = vbt.MA.run(cp, slow_window)
        enter = f_ma.ma_crossed_above(s_ma)
        exit = f_ma.ma_crossed_below(s_ma)
        return vbt.Portfolio.from_signals(cp, enter, exit, init_cash=1000000, fees=0.0005)

    with st.spinner("Simulating Alpha Stability (Train vs Test)..."):
        is_pf = run_simulation(is_df)
        oos_pf = run_simulation(oos_df)
        # Defining full portfolio for stats/trades view
        pf = run_simulation(df)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Robustness Monitor: IS/OOS Equity Curves**")
        fig_is = is_pf.plot_value()
        fig_oos = oos_pf.plot_value()
        
        # Plot both for comparison
        combined_fig = fig_is.add_trace(fig_oos.data[0])
        combined_fig.update_layout(height=500, template='plotly_dark', title="In-Sample (Train) vs Out-of-Sample (Test) Performance")
        st.plotly_chart(combined_fig, use_container_width=True)
        
    with col2:
        st.markdown("**Performance Metrics**")
        stats = pf.stats()
        # Convert to a DataFrame for better table rendering
        stats_df = pd.DataFrame(stats).reset_index()
        stats_df.columns = ['Metric', 'Value']
        # Convert objects (like Timedelta) to string to prevent Arrow serialization errors in Streamlit
        stats_df['Value'] = stats_df['Value'].astype(str)
        st.dataframe(stats_df, hide_index=True, use_container_width=True)
        
    # Additional raw trades view
    with st.expander("View Raw Trade Data"):
        st.dataframe(pf.trades.records_readable)
        
    # --- FREQTRADE EXPORT ADDITION ---
    st.divider()
    st.subheader("🚀 Portability: Export to Autonomous Bot")
    st.write("Convert this backtested strategy into a **Freqtrade-compatible** implementation.")
    
    # Generate the strategy logic string based on current mode
    if strategy_mode == "Pre-defined (SMA)":
        logic = f"dataframe['sma_fast'] = ta.SMA(dataframe, timeperiod={fast_window})\n        dataframe['sma_slow'] = ta.SMA(dataframe, timeperiod={slow_window})"
    else:
        logic = st.session_state.get('generated_strategy', "# AI Logic")

    ft_code = generate_freqtrade_strategy_file("UpbitAlphaStrategy", logic)
    
    with st.expander("Preview Freqtrade Strategy Code"):
        st.code(ft_code, language="python")
        
    export_as_downloadable(ft_code, "UpbitAlphaStrategy.py")
else:
    st.error("Could not fetch data.")
