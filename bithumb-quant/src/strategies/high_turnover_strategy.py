import pandas as pd
import numpy as np
import ta
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("HighTurnoverStrategy")

class HighTurnoverStrategy:
    """
    High-Turnover Seed Compounding Strategy (Intraday Rolling Scalping).
    Rapidly cycles small seed capital in short timeframes (1m/3m/5m), strictly enforcing
    that every target take-profit exceeds Bithumb exchange fees + slippage.
    """

    def __init__(self, config: Dict[str, Any]):
        self.target_net_profit_pct = config.get("target_net_profit_pct", 0.35)  # Desired net gain (e.g. +0.35%)
        self.exchange_fee_pct = config.get("exchange_fee_pct", 0.04)            # Bithumb fee per side (0.04%)
        self.slippage_buffer_pct = config.get("slippage_buffer_pct", 0.06)      # Slippage allowance (0.06%)
        self.ema_fast_period = config.get("ema_fast_period", 3)
        self.ema_slow_period = config.get("ema_slow_period", 9)
        self.bb_period = config.get("bb_period", 20)
        self.bb_std_dev = config.get("bb_std_dev", 2.0)
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_oversold_threshold = config.get("rsi_oversold_threshold", 42)
        self.rsi_overbought_threshold = config.get("rsi_overbought_threshold", 68)
        self.max_hold_time_minutes = config.get("max_hold_time_minutes", 25)

        # Calculate minimum gross profit % required to guarantee positive net return
        self.min_gross_hurdle_pct = self.calculate_min_gross_hurdle_pct()

    def calculate_min_gross_hurdle_pct(self) -> float:
        """
        Calculates the mandatory gross price increase (%) required to clear all fees.
        Round-trip fee = 2 * exchange_fee_pct + slippage_buffer_pct.
        Gross Hurdle = Round-trip fee + target_net_profit_pct.
        """
        round_trip_cost_pct = (2.0 * self.exchange_fee_pct) + self.slippage_buffer_pct
        gross_hurdle_pct = round_trip_cost_pct + self.target_net_profit_pct
        logger.info(
            f"High-Turnover Fee Hurdle Configured: Round-Trip Cost={round_trip_cost_pct:.3f}% "
            f"(2x{self.exchange_fee_pct}% + {self.slippage_buffer_pct}%) | "
            f"Target Net={self.target_net_profit_pct:.2f}% | Min Gross Target Hurdle={gross_hurdle_pct:.3f}%"
        )
        return gross_hurdle_pct

    def get_take_profit_price(self, entry_price: float) -> float:
        """Calculates exact fee-adjusted take profit limit price."""
        return entry_price * (1.0 + (self.min_gross_hurdle_pct / 100.0))

    def analyze_candlesticks(self, candles: List[List[Any]]) -> Optional[Dict[str, Any]]:
        """
        Calculates fast scalping indicators (EMA 3/9, Bollinger Bands, RSI).
        Candle list format: [Timestamp, Open, Close, High, Low, Volume]
        """
        if not candles or len(candles) < self.bb_period + 5:
            logger.warning("Insufficient candlestick data for High-Turnover scalping.")
            return None

        df = pd.DataFrame(candles, columns=["timestamp", "open", "close", "high", "low", "volume"])
        df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)

        # Technical Indicators
        df["ema_fast"] = ta.trend.ema_indicator(df["close"], window=self.ema_fast_period)
        df["ema_slow"] = ta.trend.ema_indicator(df["close"], window=self.ema_slow_period)
        df["rsi"] = ta.momentum.rsi(df["close"], window=self.rsi_period)

        bb = ta.volatility.BollingerBands(df["close"], window=self.bb_period, window_dev=self.bb_std_dev)
        df["bb_high"] = bb.bollinger_hband()
        df["bb_mid"] = bb.bollinger_mavg()
        df["bb_low"] = bb.bollinger_lband()
        df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)

        current = df.iloc[-1]
        prev = df.iloc[-2]

        current_price = current["close"]
        ema_fast = current["ema_fast"]
        ema_slow = current["ema_slow"]
        rsi_val = current["rsi"]
        bb_low = current["bb_low"]
        bb_mid = current["bb_mid"]
        atr = current["atr"]

        # Expected volatility headroom: ATR must be sufficiently large to hit micro-profit
        atr_pct = (atr / current_price) * 100.0 if current_price > 0 else 0.0

        return {
            "current_price": current_price,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "rsi": rsi_val,
            "bb_low": bb_low,
            "bb_mid": bb_mid,
            "atr": atr,
            "atr_pct": atr_pct,
            "is_ema_bullish_cross": bool(ema_fast > ema_slow and prev["ema_fast"] <= prev["ema_slow"]),
            "is_oversold_bounce": bool(current_price <= bb_low * 1.002 and rsi_val <= self.rsi_oversold_threshold),
            "is_rsi_safe": bool(rsi_val < self.rsi_overbought_threshold)
        }

    def generate_signal(self, metrics: Dict[str, Any], ai_regime: str = "NEUTRAL") -> Dict[str, Any]:
        """
        Evaluates micro-entry signals for fast seed turnover.
        """
        if not metrics:
            return {"signal": "HOLD", "reason": "No metrics available"}

        if ai_regime in ("HALT", "HIGH_VOLATILITY_RISK"):
            return {"signal": "HOLD", "reason": f"AI Studio Advisory HALT (Regime: {ai_regime})"}

        current_price = metrics["current_price"]
        is_ema_bull = metrics["is_ema_bullish_cross"]
        is_bounce = metrics["is_oversold_bounce"]
        is_rsi_safe = metrics["is_rsi_safe"]
        atr_pct = metrics.get("atr_pct", 0.0)

        # Volatility Headroom Guard: Only enter if market has enough movement to clear fee hurdle
        if atr_pct < (self.min_gross_hurdle_pct * 0.5):
            return {
                "signal": "HOLD",
                "reason": f"Market volatility too low (ATR {atr_pct:.2f}% < Hurdle {self.min_gross_hurdle_pct:.2f}%)"
            }

        # Entry condition: EMA bullish golden cross OR Bollinger Band oversold bounce
        if (is_ema_bull or is_bounce) and is_rsi_safe:
            target_tp_price = self.get_take_profit_price(current_price)
            return {
                "signal": "BUY",
                "current_price": current_price,
                "target_take_profit_price": target_tp_price,
                "min_gross_hurdle_pct": self.min_gross_hurdle_pct,
                "reason": (
                    f"Scalp Signal Triggered! ({'EMA Cross' if is_ema_bull else 'BB Dip Bounce'}) | "
                    f"Entry={current_price:,.0f} KRW -> Net Hurdle TP={target_tp_price:,.0f} KRW (+{self.min_gross_hurdle_pct:.2f}%) | "
                    f"RSI={metrics['rsi']:.1f}"
                )
            }

        return {"signal": "HOLD", "reason": "No entry trigger"}

    def check_exit_condition(self, entry_price: float, current_price: float, opened_at_str: str) -> Dict[str, Any]:
        """
        Evaluates whether to exit position based on:
        1. Target Take-Profit (>= Fee Hurdle).
        2. Timeout / Stale trade exit to free seed capital.
        """
        target_tp_price = self.get_take_profit_price(entry_price)
        current_gross_pnl_pct = ((current_price - entry_price) / entry_price) * 100.0

        # 1. Take-Profit Trigger (Guarantees net profit > fees)
        if current_price >= target_tp_price:
            net_profit_pct = current_gross_pnl_pct - (2.0 * self.exchange_fee_pct + self.slippage_buffer_pct)
            return {
                "should_exit": True,
                "reason": f"🎯 Fee-Adjusted Take-Profit Hit! Gross: +{current_gross_pnl_pct:.2f}% (Net: +{net_profit_pct:.2f}%)",
                "exit_type": "TAKE_PROFIT"
            }

        # 2. Staleness Timeout Check
        try:
            opened_at = datetime.fromisoformat(opened_at_str)
            elapsed_minutes = (datetime.now() - opened_at).total_seconds() / 60.0
            if elapsed_minutes >= self.max_hold_time_minutes:
                return {
                    "should_exit": True,
                    "reason": f"⏱️ Timeout Stale Position Exit ({elapsed_minutes:.1f}m >= {self.max_hold_time_minutes}m). Recycling seed capital.",
                    "exit_type": "TIMEOUT_RECYCLE"
                }
        except Exception as e:
            logger.warning(f"Error parsing opened_at timestamp '{opened_at_str}': {e}")

        return {"should_exit": False, "reason": "Holding"}
