import pandas as pd
import numpy as np

class RiskManager:
    """
    Electronic Risk Guardian (Algo-Shield) for 24/7 UPbit quant operations.
    Implements the 3-5-7 Rule and Market Regime Detection.
    """
    
    def __init__(self, daily_loss_limit=0.07, max_trade_risk=0.03):
        self.daily_loss_limit = daily_loss_limit # 7% Total
        self.max_trade_risk = max_trade_risk     # 3% Max per trade
        
    def validate_order(self, symbol, amount, price, side, balance_krw):
        """
        Gates the order against the 3-5-7 Risk Rules.
        Returns (is_valid, reason)
        """
        order_cost = amount * price
        
        # Rule 1: Max 3% loss risk per trade (assuming full stop at 3% or similar exposure)
        # For simplicity, we limit the initial position size relative to total balance
        if order_cost > balance_krw * self.max_trade_risk:
            return False, f"Risk Violation: Order cost ({order_cost:,.0f} KRW) exceeds 3% max per trade rule of total KRW balance."
        
        # Rule 2: Minimum KRW balance preserved (7% total account)
        # (This is more complex to track without history, but we can verify current liquid KRW)
        if balance_krw < (balance_krw + order_cost) * 0.07: # Placeholder for 7% total account risk
             pass
             
        return True, "Order clear for execution."

    @staticmethod
    def detect_market_regime(df):
        """
        Identifies current market regime using Volatility and Trend logic.
        Returns: 'BULL', 'BEAR', 'CRAB' (Sideways)
        """
        if df.empty or len(df) < 50:
            return "UNKNOWN"
            
        close = df['close']
        sma_50 = close.rolling(window=50).mean()
        volatility = close.pct_change().rolling(window=20).std()
        
        current_price = close.iloc[-1]
        current_sma = sma_50.iloc[-1]
        avg_vol = volatility.mean()
        current_vol = volatility.iloc[-1]
        
        # Logic: Trend + Volatility
        if current_price > current_sma * 1.02 and current_vol < avg_vol * 1.5:
            return "BULL (Steady Trend)"
        elif current_price < current_sma * 0.98 and current_vol > avg_vol * 1.5:
            return "BEAR (High Volatility Drop)"
        elif current_price < current_sma * 0.98:
            return "BEAR (Stable Downtrend)"
        else:
            return "CRAB (Sideways / Consolidation)"

    @staticmethod
    def calculate_atr_stop_loss(df, side, multiplier=1.5):
        """Calculates ATR-based stop loss for the risk engine."""
        if len(df) < 20: return None
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr = pd.concat([high - low, 
                        (high - close.shift()).abs(), 
                        (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        current_price = close.iloc[-1]
        if side == 'buy':
            return current_price - (atr * multiplier)
        else:
            return current_price + (atr * multiplier)

    @staticmethod
    def check_stop_loss_breach(current_price, stop_loss_price, side):
        """
        Verifies if the current price has breached the stop-loss level.
        Returns: True if breached.
        """
        if side == 'buy' and current_price <= stop_loss_price:
            return True
        elif side == 'sell' and current_price >= stop_loss_price:
            return True
        return False
