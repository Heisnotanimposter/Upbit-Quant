import unittest
from src.core.risk_manager import RiskManager

class TestRiskManager(unittest.TestCase):

    def setUp(self):
        self.config = {
            "max_portfolio_allocation_pct": 20.0,
            "max_open_positions": 3,
            "default_stop_loss_pct": 3.0,
            "trailing_stop_activation_pct": 4.0,
            "trailing_stop_distance_pct": 2.0,
            "daily_max_drawdown_pct": 5.0,
            "min_order_krw": 5000
        }
        self.risk = RiskManager(self.config)

    def test_circuit_breaker(self):
        self.risk.initialize_daily_equity(10_000_000.0)

        # Normal equity (9.8M = 2% drawdown) -> No circuit breaker
        triggered, _ = self.risk.check_circuit_breaker(9_800_000.0)
        self.assertFalse(triggered)

        # Severe loss (9.4M = 6% drawdown) -> Circuit breaker triggered
        triggered, reason = self.risk.check_circuit_breaker(9_400_000.0)
        self.assertTrue(triggered)
        self.assertIn("Circuit Breaker", reason)

    def test_position_sizing(self):
        # 10M available, 20% max allocation = 2M base, scaled by 0.5 AI multiplier = 1M
        size = self.risk.calculate_position_size(available_krw=10_000_000.0, current_price=50_000_000.0, ai_multiplier=0.5)
        self.assertEqual(size, 1_000_000.0)

    def test_fat_finger_limit_blocking(self):
        # Request allocation > 10M hard cap -> returns 0.0
        size = self.risk.calculate_position_size(available_krw=100_000_000.0, current_price=50_000_000.0, ai_multiplier=1.0)
        self.assertEqual(size, 0.0)

    def test_trailing_stop(self):
        entry = 100.0
        # Price at 101.0 -> no sell, peak 101
        sell, peak, stop = self.risk.evaluate_trailing_stop(entry_price=entry, current_price=101.0, current_peak=100.0, current_stop_loss=97.0)
        self.assertFalse(sell)
        self.assertEqual(peak, 101.0)

        # Price hits 105.0 (+5% profit) -> trailing stop activates (105 * 0.98 = 102.9)
        sell, peak, stop = self.risk.evaluate_trailing_stop(entry_price=entry, current_price=105.0, current_peak=101.0, current_stop_loss=97.0)
        self.assertFalse(sell)
        self.assertEqual(peak, 105.0)
        self.assertAlmostEqual(stop, 102.9, places=2)

        # Price drops to 102.0 (below updated stop 102.9) -> Sell triggered
        sell, peak, stop = self.risk.evaluate_trailing_stop(entry_price=entry, current_price=102.0, current_peak=105.0, current_stop_loss=102.9)
        self.assertTrue(sell)

if __name__ == "__main__":
    unittest.main()
