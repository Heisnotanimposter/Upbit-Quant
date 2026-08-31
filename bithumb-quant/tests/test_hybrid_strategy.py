import unittest
import numpy as np
from datetime import datetime, timedelta
from src.strategies.rl_strategy import RLStrategy
from src.strategies.hybrid_strategy import HybridAIRLStrategy

class TestHybridAIRLStrategy(unittest.TestCase):

    def setUp(self):
        # Generate 35 mock candles
        self.candles = []
        base_price = 50_000_000.0
        for i in range(35):
            self.candles.append([
                1600000000000 + (i * 180000),
                base_price + (i * 50000),
                base_price + (i * 50000) + 10000,
                base_price + (i * 50000) + 20000,
                base_price + (i * 50000) - 10000,
                10.0
            ])

        self.config = {
            "model_path": "models/rl_agent_dueling_dqn.pt",
            "target_net_profit_pct": 0.35,
            "exchange_fee_pct": 0.04,
            "slippage_buffer_pct": 0.06,
            "max_hold_time_minutes": 25
        }
        self.hybrid = HybridAIRLStrategy(self.config)

    def test_rl_strategy_state_extraction(self):
        rl_strat = RLStrategy(model_path="non_existent_dummy.pt")
        state_vec = rl_strat.extract_state_vector(self.candles)
        self.assertIsNotNone(state_vec)
        self.assertEqual(len(state_vec), 9)

        action = rl_strat.predict_action(state_vec)
        self.assertIn(action, [0, 1, 2])

    def test_hybrid_analyze_candlesticks(self):
        metrics = self.hybrid.analyze_candlesticks(self.candles)
        self.assertIsNotNone(metrics)
        self.assertIn("current_price", metrics)
        self.assertIn("rl_action", metrics)
        self.assertIn("state_vector", metrics)

    def test_hybrid_generate_signal_ai_halt(self):
        metrics = self.hybrid.analyze_candlesticks(self.candles)
        sig = self.hybrid.generate_signal(metrics, ai_regime="HALT")
        self.assertEqual(sig["signal"], "HOLD")
        self.assertIn("HALT", sig["reason"])

    def test_hybrid_exit_condition_take_profit(self):
        entry = 50_000_000.0
        now_str = datetime.now().isoformat()
        # Price hits +1% (exceeds hurdle ~0.49%)
        res = self.hybrid.check_exit_condition(entry_price=entry, current_price=50_500_000.0, opened_at_str=now_str)
        self.assertTrue(res["should_exit"])
        self.assertEqual(res["exit_type"], "TAKE_PROFIT")

    def test_hybrid_exit_condition_timeout(self):
        entry = 50_000_000.0
        old_time = (datetime.now() - timedelta(minutes=30)).isoformat()
        res = self.hybrid.check_exit_condition(entry_price=entry, current_price=50_050_000.0, opened_at_str=old_time)
        self.assertTrue(res["should_exit"])
        self.assertEqual(res["exit_type"], "TIMEOUT_RECYCLE")

if __name__ == "__main__":
    unittest.main()
