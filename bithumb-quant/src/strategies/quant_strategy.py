import pandas as pd
import numpy as np
import ta
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("QuantStrategy")

class QuantStrategy:
    """
    Multi-timeframe Quantitative Strategy:
    Larry Williams Volatility Breakout + EMA Trend Filter + RSI Overbought Guard + Gemini Regime.
    """

    def __init__(self, strategy_config: Dict[str, Any]):
        self.k_noise_ratio = strategy_config.get("k_noise_ratio", 0.5)
        self.ema_fast_period = strategy_config.get("ema_fast_period", 5)
        self.ema_slow_period = strategy_config.get("ema_slow_period", 20)
        self.rsi_period = strategy_config.get("rsi_period", 14)
        self.rsi_max_buy = strategy_config.get("rsi_max_buy", 70)
        self.atr_period = strategy_config.get("atr_period", 14)

    def analyze_candlesticks(self, candles: List[List[Any]]) -> Optional[Dict[str, Any]]:
        """
        Parses raw Bithumb OHLCV candle list into a pandas DataFrame and calculates technical indicators.
        Candle list format: [Timestamp, Open, Close, High, Low, Volume]
        """
        if not candles or len(candles) < self.ema_slow_period + 5:
            logger.warning("Insufficient candlestick data for strategy calculation.")
            return None

        df = pd.DataFrame(candles, columns=["timestamp", "open", "close", "high", "low", "volume"])
        df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)

        # Technical Indicators
        df["ema_fast"] = ta.trend.ema_indicator(df["close"], window=self.ema_fast_period)
        df["ema_slow"] = ta.trend.ema_indicator(df["close"], window=self.ema_slow_period)
        df["rsi"] = ta.momentum.rsi(df["close"], window=self.rsi_period)
        df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=self.atr_period)

        # Volatility Breakout Range Calculation (from previous completed candle)
        prev_candle = df.iloc[-2]
        current_candle = df.iloc[-1]

        prev_range = prev_candle["high"] - prev_candle["low"]
        target_price = current_candle["open"] + (prev_range * self.k_noise_ratio)

        current_price = current_candle["close"]
        ema_fast_val = current_candle["ema_fast"]
        ema_slow_val = current_candle["ema_slow"]
        rsi_val = current_candle["rsi"]
        atr_val = current_candle["atr"]

        return {
            "current_price": current_price,
            "target_price": target_price,
            "prev_high": prev_candle["high"],
            "prev_low": prev_candle["low"],
            "prev_range": prev_range,
            "ema_fast": ema_fast_val,
            "ema_slow": ema_slow_val,
            "rsi": rsi_val,
            "atr": atr_val,
            "is_uptrend": bool(ema_fast_val > ema_slow_val),
            "is_rsi_safe": bool(rsi_val < self.rsi_max_buy)
        }

    def generate_signal(self, metrics: Dict[str, Any], ai_regime: str = "NEUTRAL") -> Dict[str, Any]:
        """
        Determines trading signal (BUY, SELL, HOLD) based on quant metrics and Gemini AI regime.
        """
        if not metrics:
            return {"signal": "HOLD", "reason": "No market metrics available"}

        current_price = metrics["current_price"]
        target_price = metrics["target_price"]
        is_uptrend = metrics["is_uptrend"]
        is_rsi_safe = metrics["is_rsi_safe"]

        # Gemini Regime Filters
        if ai_regime in ("HALT", "HIGH_VOLATILITY_RISK"):
            return {
                "signal": "HOLD",
                "reason": f"AI Studio Advisory HALT (Market Regime: {ai_regime})"
            }

        # Entry Conditions (Volatility Breakout + Trend + RSI)
        is_breakout = current_price >= target_price

        if is_breakout and is_uptrend and is_rsi_safe:
            return {
                "signal": "BUY",
                "target_price": target_price,
                "reason": f"Breakout Triggered! Price ({current_price:,.0f} KRW) >= Target ({target_price:,.0f} KRW) | Uptrend: True | RSI: {metrics['rsi']:.1f}"
            }

        return {
            "signal": "HOLD",
            "reason": f"Price ({current_price:,.0f}) below Target ({target_price:,.0f}) or filters failed (Uptrend={is_uptrend}, RSI_Safe={is_rsi_safe})"
        }
