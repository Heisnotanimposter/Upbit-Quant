import ccxt
import streamlit as st
import time
from src.core.risk_manager import RiskManager

def get_upbit_client():
    """Initializes and returns an authenticated ccxt upbit client based on user secrets."""
    if "upbit" in st.secrets and "access_key" in st.secrets["upbit"] and "secret_key" in st.secrets["upbit"]:
        ak = st.secrets["upbit"]["access_key"]
        sk = st.secrets["upbit"]["secret_key"]
        
        # Don't try auth if placeholder keys are still used
        if ak == "YOUR_UPBIT_ACCESS_KEY":
            return None
            
        exchange = ccxt.upbit({
            'apiKey': ak,
            'secret': sk,
            'enableRateLimit': True,
        })
        return exchange
    return None

def fetch_wallet_balance(client):
    try:
        balance = client.fetch_balance()
        # Filter for non-zero balances
        non_zero = {k: v for k, v in balance['total'].items() if v > 0}
        return non_zero
    except Exception as e:
        return f"Error fetching wallet: {e}"

def execute_market_order(client, symbol, side, amount, paper_mode=False):
    """
    Executes a market order on UPbit. 
    side: 'buy' or 'sell'
    amount: size in BASE currency (e.g. BTC if symbol is BTC/KRW)
    paper_mode: If True, simulates the order without sending to exchange.
    """
    try:
        # Fetch current price first
        ticker = client.fetch_ticker(symbol)
        price = ticker['last']
        
        # Determine current balance (from exchange or paper wallet)
        if not paper_mode:
            balance = fetch_wallet_balance(client)
            krw_balance = balance.get('KRW', 0)
        else:
            # Paper mode uses session state for balance simulation
            if 'paper_wallet' not in st.session_state:
                st.session_state['paper_wallet'] = {'KRW': 10000000.0} # 10M KRW default
            krw_balance = st.session_state['paper_wallet'].get('KRW', 0)
        
        # Risk Check (Algo-Shield)
        manager = RiskManager()
        is_valid, reason = manager.validate_order(symbol, amount, price, side, krw_balance)
        if not is_valid:
            return f"Risk Error: {reason}"
            
        if paper_mode:
            # Simulate execution with SLIPPAGE penalty (0.1% to 0.5% default)
            slippage = 0.001 # 0.1% slippage for standard simulation
            price_with_slippage = price * (1 + slippage) if side == 'buy' else price * (1 - slippage)
            cost = amount * price_with_slippage
            base_asset = symbol.split('/')[0]
            
            if side == 'buy':
                st.session_state['paper_wallet']['KRW'] -= cost
                st.session_state['paper_wallet'][base_asset] = st.session_state['paper_wallet'].get(base_asset, 0) + amount
            else:
                st.session_state['paper_wallet']['KRW'] += cost
                st.session_state['paper_wallet'][base_asset] = st.session_state['paper_wallet'].get(base_asset, 0) - amount
                
            return {
                'id': f'paper_{int(time.time())}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'price_executed': price_with_slippage,
                'status': 'closed',
                'remark': 'PAPER TRADE SIMULATION'
            }
            
        # Execute REAL CCXT order
        order = client.create_market_order(symbol, side, amount)
        return order
    except Exception as e:
        return f"Execution Error: {e}"
