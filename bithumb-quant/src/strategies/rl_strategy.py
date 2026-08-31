import os
import torch
import numpy as np
import pandas as pd
import ta
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.ml.rl_agent import RLAgent

logger = logging.getLogger("RLStrategy")

class RLStrategy:
    """
    Production Deep Reinforcement Learning Strategy Adapter.
    Extracts real-time financial features from live Bithumb candlestick streams
    and performs neural policy inference via trained Dueling Double DQN weights.
    """

    def __init__(self, model_path: str = "models/rl_agent_dueling_dqn.pt", state_dim: int = 9, action_dim: int = 3):
        self.model_path = model_path
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.agent = RLAgent(state_dim=self.state_dim, action_dim=self.action_dim)
        self.is_model_loaded = False

        self._load_weights()

    def _load_weights(self):
        if Path(self.model_path).exists():
            try:
                self.agent.load_model(self.model_path)
                self.is_model_loaded = True
                logger.info(f"Loaded trained RL model weights from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load RL model weights from {self.model_path}: {e}")
        else:
            logger.warning(f"RL model weights not found at {self.model_path}. Agent running with initialized weights.")

    def extract_state_vector(self, candles: List[List[Any]], current_position: Optional[Dict[str, Any]] = None) -> Optional[np.ndarray]:
        """
        Converts raw Bithumb candlestick list into the exact 9-dimensional state feature vector:
        [norm_ret_1, norm_ret_5, rsi_norm, macd_diff_norm, bb_percent_b, atr_ratio, ema_ratio, has_position, unrealized_pnl_pct]
        """
        if not candles or len(candles) < 25:
            return None

        df = pd.DataFrame(candles, columns=["timestamp", "open", "close", "high", "low", "volume"])
        df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)

        # 1. Price returns
        ret_1 = df["close"].pct_change().iloc[-1]
        ret_5 = df["close"].pct_change(5).iloc[-1]
        norm_ret_1 = np.clip(ret_1 * 100.0, -10.0, 10.0) / 10.0
        norm_ret_5 = np.clip(ret_5 * 100.0, -20.0, 20.0) / 20.0

        # 2. RSI (14)
        rsi = ta.momentum.rsi(df["close"], window=14).fillna(50).iloc[-1]
        rsi_norm = (rsi - 50.0) / 50.0

        # 3. MACD Diff
        macd_diff = ta.trend.macd_diff(df["close"]).fillna(0).iloc[-1]
        current_price = df["close"].iloc[-1]
        macd_diff_norm = np.clip(macd_diff / (current_price * 0.01 + 1e-9), -3.0, 3.0) / 3.0

        # 4. Bollinger Bands %B
        bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2.0)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        bb_range = bb_high - bb_low
        bb_percent_b = ((current_price - bb_low) / bb_range) if bb_range > 0 else 0.5

        # 5. ATR Ratio
        atr = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14).fillna(0).iloc[-1]
        atr_ratio = (atr / current_price) * 10.0 if current_price > 0 else 0.0

        # 6. Fast/Slow EMA Ratio
        ema_3 = ta.trend.ema_indicator(df["close"], window=3).fillna(df["close"]).iloc[-1]
        ema_9 = ta.trend.ema_indicator(df["close"], window=9).fillna(df["close"]).iloc[-1]
        ema_ratio = (ema_3 - ema_9) / current_price * 100.0 if current_price > 0 else 0.0

        # 7 & 8. Position Status & Unrealized PnL
        has_pos = 1.0 if current_position else 0.0
        unrealized_pnl_pct = 0.0
        if current_position and current_position.get("entry_price", 0) > 0:
            entry = current_position["entry_price"]
            unrealized_pnl_pct = ((current_price - entry) / entry) * 100.0

        norm_unrealized_pnl = np.clip(unrealized_pnl_pct / 5.0, -2.0, 2.0)

        features = [
            norm_ret_1, norm_ret_5, rsi_norm, macd_diff_norm,
            bb_percent_b, atr_ratio, ema_ratio, has_pos, norm_unrealized_pnl
        ]
        return np.array(features, dtype=np.float32)

    def predict_action(self, state_vector: np.ndarray) -> int:
        """
        Executes neural network inference to predict action:
        0: HOLD, 1: BUY, 2: SELL
        """
        if state_vector is None:
            return 0
        return self.agent.select_action(state_vector, evaluate=True)
