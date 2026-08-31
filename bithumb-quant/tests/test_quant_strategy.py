import unittest
from src.strategies.quant_strategy import QuantStrategy

class TestQuantStrategy(unittest.TestCase):

    def setUp(self):
        self.config = {
            "k_noise_ratio": 0.5,
            "ema_fast_period": 5,
            "ema_slow_period": 20,
            "rsi_period": 14,
            "rsi_max_buy": 70,
            "atr_period": 14
        }
        self.strategy = QuantStrategy(self.config)

    def test_analyze_candlesticks_insufficient_data(self):
        result = self.strategy.analyze_candlesticks([])
        self.assertIsNone(result)

    def test_analyze_candlesticks_valid(self):
        # Generate 30 mock OHLCV candles
        candles = []
        base_price = 50000000.0
        for i in range(30):
            candles.append([
                1600000000 + i * 86400,
                base_price + i * 100000,       # Open
                base_price + i * 100000 + 500, # Close
                base_price + i * 100000 + 1000,# High
                base_price + i * 100000 - 500, # Low
                10.5                           # Volume
            ])

        metrics = self.strategy.analyze_candlesticks(candles)
        self.assertIsNotNone(metrics)
        self.assertIn("current_price", metrics)
        self.assertIn("target_price", metrics)
        self.assertTrue(metrics["is_uptrend"])

    def test_generate_signal_buy(self):
        metrics = {
            "current_price": 52000000.0,
            "target_price": 51000000.0,
            "is_uptrend": True,
            "is_rsi_safe": True,
            "rsi": 55.0
        }
        res = self.strategy.generate_signal(metrics, ai_regime="BULL_TREND")
        self.assertEqual(res["signal"], "BUY")

    def test_generate_signal_ai_halt(self):
        metrics = {
            "current_price": 52000000.0,
            "target_price": 51000000.0,
            "is_uptrend": True,
            "is_rsi_safe": True,
            "rsi": 55.0
        }
        res = self.strategy.generate_signal(metrics, ai_regime="HALT")
        self.assertEqual(res["signal"], "HOLD")

if __name__ == "__main__":
    unittest.main()
