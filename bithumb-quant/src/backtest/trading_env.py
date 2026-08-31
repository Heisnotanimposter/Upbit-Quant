import numpy as np
import pandas as pd
import ta
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger("TradingEnv")

class TradingEnvironment:
    """
    High-performance Gym-compatible financial trading environment for Reinforcement Learning.
    Features realistic fee modeling, slippage, feature matrix construction, and fee-penalized reward shaping.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 1_000_000.0,
        fee_pct: float = 0.04,
        slippage_pct: float = 0.05,
        drawdown_penalty_lambda: float = 0.5
    ):
        self.df_raw = df.copy()
        self.initial_balance = initial_balance
        self.fee_pct = fee_pct / 100.0
        self.slippage_pct = slippage_pct / 100.0
        self.drawdown_penalty_lambda = drawdown_penalty_lambda

        # Prepare technical features
        self.df = self._prepare_features(self.df_raw)
        self.feature_columns = [
            "norm_ret_1", "norm_ret_5", "rsi_norm", "macd_diff_norm",
            "bb_percent_b", "atr_ratio", "ema_ratio"
        ]
        self.state_dim = len(self.feature_columns) + 2  # + position_state (0 or 1) + unrealized_pnl_pct
        self.action_dim = 3  # 0: HOLD, 1: BUY, 2: SELL

        self.reset()

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().reset_index(drop=True)
        # Price returns
        df["ret_1"] = df["close"].pct_change().fillna(0)
        df["ret_5"] = df["close"].pct_change(5).fillna(0)
        df["norm_ret_1"] = np.clip(df["ret_1"] * 100.0, -10.0, 10.0) / 10.0
        df["norm_ret_5"] = np.clip(df["ret_5"] * 100.0, -20.0, 20.0) / 20.0

        # RSI
        rsi = ta.momentum.rsi(df["close"], window=14).fillna(50)
        df["rsi_norm"] = (rsi - 50.0) / 50.0  # Normalized [-1, 1]

        # MACD
        macd_diff = ta.trend.macd_diff(df["close"]).fillna(0)
        df["macd_diff_norm"] = np.clip(macd_diff / (df["close"] * 0.01), -3.0, 3.0) / 3.0

        # Bollinger Bands %B
        bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2.0)
        bb_high = bb.bollinger_hband()
        bb_low = bb.bollinger_lband()
        bb_range = (bb_high - bb_low).replace(0, np.nan)
        df["bb_percent_b"] = ((df["close"] - bb_low) / bb_range).fillna(0.5)

        # ATR
        atr = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14).fillna(0)
        df["atr_ratio"] = (atr / df["close"]).fillna(0) * 10.0

        # Fast/Slow EMA Ratio
        ema_3 = ta.trend.ema_indicator(df["close"], window=3).fillna(df["close"])
        ema_9 = ta.trend.ema_indicator(df["close"], window=9).fillna(df["close"])
        df["ema_ratio"] = (ema_3 - ema_9) / df["close"] * 100.0

        return df.dropna().reset_index(drop=True)

    def reset(self) -> np.ndarray:
        self.current_step = 20
        self.cash = self.initial_balance
        self.holdings = 0.0
        self.position_entry_price = 0.0
        self.peak_equity = self.initial_balance
        self.prev_equity = self.initial_balance
        self.total_fees_paid = 0.0
        self.trades = []
        return self._get_state()

    def _get_state(self) -> np.ndarray:
        current_row = self.df.iloc[self.current_step]
        features = [current_row[col] for col in self.feature_columns]

        current_price = current_row["close"]
        has_position = 1.0 if self.holdings > 0 else 0.0
        unrealized_pnl_pct = (
            ((current_price - self.position_entry_price) / self.position_entry_price) * 100.0
            if has_position > 0 and self.position_entry_price > 0 else 0.0
        )
        features.append(has_position)
        features.append(np.clip(unrealized_pnl_pct / 5.0, -2.0, 2.0))

        return np.array(features, dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        current_row = self.df.iloc[self.current_step]
        current_price = current_row["close"]
        fee_cost = 0.0

        # Action Execution: 0=HOLD, 1=BUY, 2=SELL
        if action == 1 and self.cash > 0:  # BUY
            effective_price = current_price * (1.0 + self.slippage_pct)
            invest_amount = self.cash
            fee_cost = invest_amount * self.fee_pct
            net_invest = invest_amount - fee_cost

            self.holdings = net_invest / effective_price
            self.position_entry_price = effective_price
            self.cash = 0.0
            self.total_fees_paid += fee_cost

            self.trades.append({
                "step": self.current_step,
                "timestamp": current_row.get("timestamp", 0),
                "type": "BUY",
                "price": effective_price,
                "units": self.holdings,
                "fee": fee_cost
            })

        elif action == 2 and self.holdings > 0:  # SELL
            effective_price = current_price * (1.0 - self.slippage_pct)
            gross_revenue = self.holdings * effective_price
            fee_cost = gross_revenue * self.fee_pct
            net_cash = gross_revenue - fee_cost

            pnl_krw = net_cash - (self.holdings * self.position_entry_price)
            pnl_pct = ((effective_price - self.position_entry_price) / self.position_entry_price) * 100.0

            self.cash = net_cash
            self.holdings = 0.0
            self.position_entry_price = 0.0
            self.total_fees_paid += fee_cost

            self.trades.append({
                "step": self.current_step,
                "timestamp": current_row.get("timestamp", 0),
                "type": "SELL",
                "price": effective_price,
                "units": 0,
                "fee": fee_cost,
                "pnl_krw": pnl_krw,
                "pnl_pct": pnl_pct
            })

        # Calculate current total equity
        current_equity = self.cash + (self.holdings * current_price)
        self.peak_equity = max(self.peak_equity, current_equity)
        drawdown = (self.peak_equity - current_equity) / self.peak_equity

        # Fee-Aware Reward Function
        equity_return = (current_equity - self.prev_equity) / self.prev_equity
        fee_penalty = (fee_cost / self.initial_balance) * 2.0
        drawdown_penalty = drawdown * self.drawdown_penalty_lambda

        reward = (equity_return * 10.0) - fee_penalty - (drawdown_penalty * 0.1)

        self.prev_equity = current_equity
        self.current_step += 1
        done = bool(self.current_step >= len(self.df) - 1 or current_equity <= self.initial_balance * 0.5)

        next_state = self._get_state() if not done else np.zeros(self.state_dim, dtype=np.float32)
        info = {
            "equity": current_equity,
            "cash": self.cash,
            "holdings": self.holdings,
            "total_fees": self.total_fees_paid,
            "trade_count": len(self.trades)
        }

        return next_state, float(reward), done, info
