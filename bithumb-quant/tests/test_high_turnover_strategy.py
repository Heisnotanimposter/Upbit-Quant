import unittest
from datetime import datetime, timedelta
from src.strategies.high_turnover_strategy import HighTurnoverStrategy

class TestHighTurnoverStrategy(unittest.TestCase):

    def setUp(self):
        self.config = {
            "target_net_profit_pct": 0.35,
            "exchange_fee_pct": 0.04,
            "slippage_buffer_pct": 0.06,
            "ema_fast_period": 3,
            "ema_slow_period": 9,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "rsi_period": 14,
            "rsi_oversold_threshold": 42,
            "rsi_overbought_threshold": 68,
            "max_hold_time_minutes": 25
        }
        self.strategy = HighTurnoverStrategy(self.config)

    def test_fee_hurdle_calculation(self):
        # Round trip = (2 * 0.04) + 0.06 = 0.14%
        # Target net = 0.35% -> Gross hurdle = 0.14 + 0.35 = 0.49%
        hurdle = self.strategy.calculate_min_gross_hurdle_pct()
        self.assertAlmostEqual(hurdle, 0.49, places=3)

    def test_take_profit_price_guarantees_fee_coverage(self):
        entry_price = 1000.0
        tp_price = self.strategy.get_take_profit_price(entry_price)

        # TP must be exactly 1000 * 1.0049 = 1004.9
        self.assertAlmostEqual(tp_price, 1004.9, places=1)

        # Verify net return at TP price after fees:
        gross_return_pct = ((tp_price - entry_price) / entry_price) * 100.0
        total_costs_pct = (2.0 * self.config["exchange_fee_pct"]) + self.config["slippage_buffer_pct"]
        net_return_pct = gross_return_pct - total_costs_pct
        self.assertAlmostEqual(net_return_pct, self.config["target_net_profit_pct"], places=4)

    def test_exit_condition_take_profit_hit(self):
        entry = 1000.0
        now_str = datetime.now().isoformat()

        # Below TP -> holding
        res = self.strategy.check_exit_condition(entry_price=entry, current_price=1003.0, opened_at_str=now_str)
        self.assertFalse(res["should_exit"])

        # Above or at TP (1005.0 >= 1004.9) -> Exit TAKE_PROFIT
        res = self.strategy.check_exit_condition(entry_price=entry, current_price=1005.0, opened_at_str=now_str)
        self.assertTrue(res["should_exit"])
        self.assertEqual(res["exit_type"], "TAKE_PROFIT")

    def test_exit_condition_timeout_recycle(self):
        entry = 1000.0
        # Position opened 30 minutes ago (exceeds max_hold_time_minutes 25)
        old_time = (datetime.now() - timedelta(minutes=30)).isoformat()
        res = self.strategy.check_exit_condition(entry_price=entry, current_price=1001.0, opened_at_str=old_time)
        self.assertTrue(res["should_exit"])
        self.assertEqual(res["exit_type"], "TIMEOUT_RECYCLE")

if __name__ == "__main__":
    unittest.main()
