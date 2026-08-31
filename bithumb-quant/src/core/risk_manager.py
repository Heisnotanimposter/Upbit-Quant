import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger("RiskManager")

class RiskManager:
    """
    Enforces risk constraints, position sizing, and circuit breaker logic for portfolio safety.
    """

    def __init__(self, risk_config: Dict[str, Any]):
        self.max_allocation_pct = risk_config.get("max_portfolio_allocation_pct", 20.0)
        self.max_open_positions = risk_config.get("max_open_positions", 3)
        self.default_stop_loss_pct = risk_config.get("default_stop_loss_pct", 3.0)
        self.trailing_stop_activation_pct = risk_config.get("trailing_stop_activation_pct", 4.0)
        self.trailing_stop_distance_pct = risk_config.get("trailing_stop_distance_pct", 2.0)
        self.daily_max_drawdown_pct = risk_config.get("daily_max_drawdown_pct", 5.0)
        self.min_order_krw = risk_config.get("min_order_krw", 5000)

        self.initial_daily_equity: float = 0.0
        self.is_circuit_breaker_active: bool = False
        self.pause_reason: str = ""

    def initialize_daily_equity(self, total_krw_equity: float):
        """Sets the baseline daily equity for drawdown tracking."""
        if self.initial_daily_equity == 0.0:
            self.initial_daily_equity = total_krw_equity
            logger.info(f"Initialized baseline daily equity: {self.initial_daily_equity:,.0f} KRW")

    def check_circuit_breaker(self, current_total_equity: float) -> Tuple[bool, str]:
        """
        Evaluates daily drawdown. If portfolio loss exceeds threshold, activates circuit breaker lock.
        """
        if self.is_circuit_breaker_active:
            return True, self.pause_reason

        if self.initial_daily_equity > 0:
            drawdown_pct = ((self.initial_daily_equity - current_total_equity) / self.initial_daily_equity) * 100.0
            if drawdown_pct >= self.daily_max_drawdown_pct:
                self.is_circuit_breaker_active = True
                self.pause_reason = f"Circuit Breaker Triggered: Daily Drawdown reached {drawdown_pct:.2f}% (Limit: {self.daily_max_drawdown_pct}%)."
                logger.critical(f"🚨 EMERGENCY: {self.pause_reason}")
                return True, self.pause_reason

        return False, ""

    def calculate_position_size(self, available_krw: float, current_price: float, ai_multiplier: float = 1.0) -> float:
        """
        Calculates trade allocation in KRW scaled by the Gemini AI risk multiplier.
        Includes fat-finger security cap validation.
        """
        if self.is_circuit_breaker_active or available_krw < self.min_order_krw:
            return 0.0

        # Base allocation amount
        allocated_krw = available_krw * (self.max_allocation_pct / 100.0)

        # Scale allocation using AI Studio Advisor multiplier (0.0 to 1.0)
        scaled_krw = allocated_krw * max(0.0, min(1.0, ai_multiplier))

        # Security check: Fat-finger hard limit guard (10,000,000 KRW max single trade cap)
        from src.utils.security import SecurityGuard
        if not SecurityGuard.check_fat_finger_cap(scaled_krw):
            return 0.0

        if scaled_krw < self.min_order_krw:
            logger.warning(f"Calculated position size ({scaled_krw:,.0f} KRW) is below minimum required order size ({self.min_order_krw} KRW). Skipping.")
            return 0.0

        return scaled_krw

    def can_open_new_position(self, current_open_count: int) -> bool:
        """Verifies if portfolio position capacity allows new entries."""
        if self.is_circuit_breaker_active:
            return False
        if current_open_count >= self.max_open_positions:
            logger.info(f"Max position limit reached ({current_open_count}/{self.max_open_positions}). Skipping new buy.")
            return False
        return True

    def calculate_stop_loss_price(self, entry_price: float) -> float:
        """Calculates initial hard stop-loss price."""
        return entry_price * (1.0 - (self.default_stop_loss_pct / 100.0))

    def evaluate_trailing_stop(self, entry_price: float, current_price: float, current_peak: float, current_stop_loss: float) -> Tuple[bool, float, float]:
        """
        Evaluates whether to update trailing stop loss or trigger trailing stop sell.
        Returns: (should_sell, new_peak_price, new_stop_loss_price)
        """
        new_peak = max(current_peak, current_price)
        profit_pct = ((current_price - entry_price) / entry_price) * 100.0

        # Hard stop-loss check
        if current_price <= current_stop_loss:
            return True, new_peak, current_stop_loss

        # Trailing stop activation check
        if profit_pct >= self.trailing_stop_activation_pct:
            trailing_stop_target = new_peak * (1.0 - (self.trailing_stop_distance_pct / 100.0))
            if trailing_stop_target > current_stop_loss:
                logger.info(f"Trailing stop updated: Price target {trailing_stop_target:,.0f} KRW (Peak: {new_peak:,.0f} KRW)")
                current_stop_loss = trailing_stop_target

        # Check if price dropped below updated trailing stop
        if current_price <= current_stop_loss:
            return True, new_peak, current_stop_loss

        return False, new_peak, current_stop_loss
