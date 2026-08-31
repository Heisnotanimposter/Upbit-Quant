import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.oms import get_upbit_client, fetch_wallet_balance, execute_market_order
from src.core.data_engine import fetch_upbit_tickers

st.set_page_config(page_title="Live OMS & Wallet", page_icon="🏦", layout="wide")
st.title("🏦 Live UPbit Portfolio & Order Management")

st.markdown("""
Connect securely to your personal UPbit account. This page enables real-time asset tracking and manual or algorithmic trade execution.   
**No actual trades are executed unless API keys are defined and Paper mode is OFF.**
""")

# --- PAPER MODE TOGGLE ---
st.sidebar.divider()
st.sidebar.subheader("Execution Mode")
paper_mode = st.sidebar.toggle("🛠️ Paper Trading Mode", value=True, help="Run trades without real money using a virtual wallet.")

if paper_mode:
    st.sidebar.info("PAPER MODE ACTIVE: Using Virtual Account.")
else:
    st.sidebar.warning("LIVE MODE ACTIVE: Real KRW at Risk!")

client = get_upbit_client()

if not client:
    st.error("""
    **API Client Not Connected**
    Please ensure that `.streamlit/secrets.toml` is filled correctly with your UPbit `access_key` and `secret_key`.
    """)
    st.stop()
    
# Layout for Authenticated users
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Wallet Balances")
    
    if paper_mode:
        if 'paper_wallet' not in st.session_state:
            st.session_state['paper_wallet'] = {'KRW': 10000000.0}
        balance = st.session_state['paper_wallet']
        st.write("*(Virtual Data)*")
    else:
        with st.spinner("Fetching Wallet Balance..."):
            balance = fetch_wallet_balance(client)
        
    if isinstance(balance, dict):
        if "KRW" in balance:
            st.metric(label="KRW Balance", value=f"{balance['KRW']:,.0f} ₩")
        for asset, amount in balance.items():
            if asset != "KRW":
                st.metric(label=f"{asset} Holdings", value=f"{amount:,.6f}")
    else:
        st.warning(balance)

with col2:
    st.subheader("Manual Execution Sandbox")
    st.markdown("Use this terminal to manually bypass algorithmic signaling and send market orders via CCXT.")
    
    with st.form("trade_form"):
        # Select ticker dynamically
        try:
            tickers = list(fetch_upbit_tickers().keys())
        except:
            tickers = ['BTC/KRW']
            
        symbol = st.selectbox("Symbol", tickers)
        
        c1, c2 = st.columns(2)
        side = c1.selectbox("Order Side", ['buy', 'sell'])
        # Amount in base currency
        base_asset = symbol.split('/')[0]
        amount = c2.number_input(f"Amount ({base_asset})", value=0.001, min_value=0.000001, step=0.001, format="%.6f")
        
        st.info("Market Buy orders on Upbit via CCXT might act differently if limit-taker rules apply (often specified by cost vs amount). Please test with small amounts.")
        
        submitted = st.form_submit_button(label="🚀 Execute Market Order", type="primary")
        if submitted:
            with st.spinner(f"Transmitting {side.upper()} order for {amount} {base_asset}..."):
                result = execute_market_order(client, symbol, side, amount, paper_mode=paper_mode)
                if isinstance(result, str) and "Error" in result:
                    st.error(result)
                else:
                    st.success("Order Response:")
                    st.json(result)

st.divider()
st.subheader("Algorithmic Bridge Info")
st.markdown("""
To connect an AI Strategy from the **Strategy Discovery** page:
1. Copy the generated `vectorbt` backtesting signals.
2. Adapt the signal array to fire real-time webhooks.
3. This instance's `execute_market_order` via `get_upbit_client()` allows direct python triggering.
""")
