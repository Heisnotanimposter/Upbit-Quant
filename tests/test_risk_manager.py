import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.risk_manager import RiskManager

class TestRiskManager(unittest.TestCase):
    
    def setUp(self):
        self.rm = RiskManager(max_trade_risk=0.03)
        
    def test_validate_order_success(self):
        # Order cost is 1% of balance (Success)
        is_valid, reason = self.rm.validate_order("BTC/KRW", 1.0, 100000.0, "buy", 10000000.0)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Order clear for execution.")
        
    def test_validate_order_failure_too_large(self):
        # Order cost is 5% of balance (Failure - exceeds 3% rule)
        is_valid, reason = self.rm.validate_order("BTC/KRW", 1.0, 500000.0, "buy", 10000000.0)
        self.assertFalse(is_valid)
        self.assertIn("exceeds 3% max", reason)
        
    def test_detect_market_regime_bull(self):
        # Create a bullish dataframe
        prices = [100 + i for i in range(100)]
        df = pd.DataFrame({'close': prices, 'high': prices, 'low': prices})
        regime = RiskManager.detect_market_regime(df)
        self.assertIn("BULL", regime)

    def test_detect_market_regime_bear(self):
        # Create a bearish dataframe
        prices = [100 - i for i in range(100)]
        df = pd.DataFrame({'close': prices, 'high': prices, 'low': prices})
        regime = RiskManager.detect_market_regime(df)
        self.assertIn("BEAR", regime)

if __name__ == '__main__':
    unittest.main()
