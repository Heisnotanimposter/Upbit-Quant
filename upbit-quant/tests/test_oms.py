import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.oms import execute_market_order

class TestOMS(unittest.TestCase):
    
    @patch('src.core.oms.fetch_wallet_balance')
    def test_execute_market_order_paper_mode(self, mock_balance):
        # Mock dependencies
        mock_client = MagicMock()
        mock_client.fetch_ticker.return_value = {'last': 100000.0}
        
        # Test paper mode execution
        result = execute_market_order(mock_client, "BTC/KRW", "buy", 1.0, paper_mode=True)
        
        self.assertIsInstance(result, dict)
        self.assertIn("paper_", result['id'])
        self.assertEqual(result['status'], 'closed')
        self.assertEqual(result['remark'], 'PAPER TRADE SIMULATION')
        
    @patch('src.core.oms.fetch_wallet_balance')
    def test_execute_market_order_risk_violation(self, mock_balance):
        # Mock balance to be very low
        mock_client = MagicMock()
        mock_client.fetch_ticker.return_value = {'last': 1000000.0}
        
        # Balance only 10,000 KRW
        mock_balance.return_value = {'KRW': 10000.0}
        
        # Order is 1 BTC (1M KRW) - should fail 3% rule
        result = execute_market_order(mock_client, "BTC/KRW", "buy", 1.0, paper_mode=False)
        
        self.assertIsInstance(result, str)
        self.assertIn("Risk Error", result)

if __name__ == '__main__':
    unittest.main()
