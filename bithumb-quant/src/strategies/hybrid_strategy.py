import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.strategies.rl_strategy import RLStrategy
from src.strategies.high_turnover_strategy import HighTurnoverStrategy

logger = logging.getLogger("HybridStrategy")

class HybridAIRLStrategy:
    """
    Unified Hybrid AI-RL Quantitative Trading Strategy.
    Integrates Google AI Studio (Gemini) Macro Regime gating with Deep Reinforcement Learning
    micro-timing and mathematical Fee-Hurdle profit guarantees.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_path = config.get("model_path", "models/rl_agent_dueling_dqn.pt")
        self.target_net_profit_pct = config.get("target_net_profit_pct", 0.35)
        self.exchange_fee_pct = config.get("exchange_fee_pct", 0.04)
        self.slippage_buffer_pct = config.get("slippage_buffer_pct", 0.06)
        self.max_hold_time_minutes = config.get("max_hold_time_minutes", 25)

        # Initialize sub-strategies
        self.rl_strategy = RLStrategy(model_path=self.model_path)
        self.scalping_guard = HighTurnoverStrategy(config)
        self.min_gross_hurdle_pct = self.scalping_guard.min_gross_hurdle_pct

        logger.info(f"Initialized Hybrid AI-RL Strategy with Fee Hurdle: +{self.min_gross_hurdle_pct:.3f}% gross target.")

    def get_take_profit_price(self, entry_price: float) -> float:
        """Returns the fee-adjusted take profit price target."""
        return self.scalping_guard.get_take_profit_price(entry_price)

    def analyze_candlesticks(self, candles: List[List[Any]], current_position: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Extracts both technical indicator metrics and RL 9D state features.
        """
        if not candles or len(candles) < 25:
            return None

        # Extract RL state vector
        state_vec = self.rl_strategy.extract_state_vector(candles, current_position)
        # Extract traditional scalping metrics
        metrics = self.scalping_guard.analyze_candlesticks(candles)

        if metrics and state_vec is not None:
            # Predict action from trained neural network (0: HOLD, 1: BUY, 2: SELL)
            rl_action = self.rl_strategy.predict_action(state_vec)
            metrics["rl_action"] = rl_action
            metrics["state_vector"] = state_vec
            return metrics

        return None

    def generate_signal(self, metrics: Dict[str, Any], ai_regime: str = "NEUTRAL") -> Dict[str, Any]:
        """
        Generates trading signal by cross-validating Gemini macro regime with DRL neural policy.
        """
        if not metrics:
            return {"signal": "HOLD", "reason": "No market metrics available"}

        # 1. Tier 1 Gate: Google AI Studio Macro Regime
        if ai_regime in ("HALT", "HIGH_VOLATILITY_RISK"):
            return {
                "signal": "HOLD",
                "reason": f"Google AI Studio Macro Filter HALT (Regime: {ai_regime})"
            }

        current_price = metrics["current_price"]
        rl_action = metrics.get("rl_action", 0)
        atr_pct = metrics.get("atr_pct", 0.0)

        # 2. Tier 2 Gate: Volatility Headroom Check
        if atr_pct < (self.min_gross_hurdle_pct * 0.4):
            return {
                "signal": "HOLD",
                "reason": f"Insufficient volatility headroom (ATR {atr_pct:.2f}% < Hurdle {self.min_gross_hurdle_pct:.2f}%)"
            }

        # 3. Tier 3 Gate: Deep Reinforcement Learning Action Execution
        # Action 1 = BUY
        if rl_action == 1:
            target_tp_price = self.get_take_profit_price(current_price)
            return {
                "signal": "BUY",
                "current_price": current_price,
                "target_take_profit_price": target_tp_price,
                "min_gross_hurdle_pct": self.min_gross_hurdle_pct,
                "reason": (
                    f"🧠 DRL Neural Policy BUY Signal | "
                    f"Entry={current_price:,.0f} KRW -> Net Hurdle TP={target_tp_price:,.0f} KRW (+{self.min_gross_hurdle_pct:.2f}%) | "
                    f"Gemini Regime={ai_regime} | RSI={metrics['rsi']:.1f}"
                )
            }

        # Fallback to High-Turnover dip-bounce if RL confirms non-negative
        scalp_sig = self.scalping_guard.generate_signal(metrics, ai_regime=ai_regime)
        if scalp_sig["signal"] == "BUY" and rl_action != 2:
            return scalp_sig

        return {"signal": "HOLD", "reason": f"DRL Policy Holding (RL Action: {rl_action})"}

    def check_exit_condition(self, entry_price: float, current_price: float, opened_at_str: str, candles: List[List[Any]] = None) -> Dict[str, Any]:
        """
        Evaluates exit triggers:
        1. Fee-Adjusted Take-Profit Hit.
        2. DRL Neural Policy SELL signal (Action 2).
        3. Stale Position Timeout Seed Recycling.
        """
        target_tp_price = self.get_take_profit_price(entry_price)
        current_gross_pnl_pct = ((current_price - entry_price) / entry_price) * 100.0

        # 1. Take-Profit Execution
        if current_price >= target_tp_price:
            net_profit_pct = current_gross_pnl_pct - (2.0 * self.exchange_fee_pct + self.slippage_buffer_pct)
            return {
                "should_exit": True,
                "reason": f"🎯 Fee-Adjusted Take-Profit Hit! Gross: +{current_gross_pnl_pct:.2f}% (Net: +{net_profit_pct:.2f}%)",
                "exit_type": "TAKE_PROFIT"
            }

        # 2. DRL Neural Policy Immediate Exit Trigger (if in profit or momentum reversal)
        if candles and len(candles) >= 25:
            state_vec = self.rl_strategy.extract_state_vector(candles, {"entry_price": entry_price})
            if state_vec is not None:
                rl_action = self.rl_strategy.predict_action(state_vec)
                if rl_action == 2 and current_gross_pnl_pct > (2.0 * self.exchange_fee_pct):
                    return {
                        "should_exit": True,
                        "reason": f"🧠 DRL Neural Policy SELL Trigger (Securing +{current_gross_pnl_pct:.2f}% gain)",
                        "exit_type": "RL_POLICY_SELL"
                    }

        # 3. Timeout Seed Recycling
        try:
            opened_at = datetime.fromisoformat(opened_at_str)
            elapsed_minutes = (datetime.now() - opened_at).total_seconds() / 60.0
            if elapsed_minutes >= self.max_hold_time_minutes:
                return {
                    "should_exit": True,
                    "reason": f"⏱️ Timeout Stale Position Exit ({elapsed_minutes:.1f}m >= {self.max_hold_time_minutes}m). Recycling seed.",
                    "exit_type": "TIMEOUT_RECYCLE"
                }
        except Exception as e:
            logger.warning(f"Error checking opened_at timestamp: {e}")

        return {"should_exit": False, "reason": "Holding"}
