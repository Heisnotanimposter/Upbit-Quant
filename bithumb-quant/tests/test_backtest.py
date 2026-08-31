import unittest
import numpy as np
import pandas as pd
from src.backtest.trading_env import TradingEnvironment
from src.ml.rl_agent import RLAgent
from src.backtest.engine import BacktestEngine

class TestBacktestFramework(unittest.TestCase):

    def setUp(self):
        # Generate 60 mock candles
        candles = []
        base_price = 50_000_000.0
        for i in range(60):
            candles.append({
                "timestamp": 1600000000000 + (i * 180000),
                "open": base_price + (i * 50000),
                "close": base_price + (i * 50000) + 10000,
                "high": base_price + (i * 50000) + 20000,
                "low": base_price + (i * 50000) - 10000,
                "volume": 10.0
            })
        self.df = pd.DataFrame(candles)

    def test_trading_environment_transitions(self):
        env = TradingEnvironment(df=self.df, initial_balance=1_000_000.0, fee_pct=0.04)
        state = env.reset()
        self.assertEqual(len(state), env.state_dim)

        # Action 1: BUY
        next_state, reward, done, info = env.step(1)
        self.assertGreater(env.holdings, 0.0)
        self.assertEqual(env.cash, 0.0)
        self.assertGreater(env.total_fees_paid, 0.0)

        # Action 2: SELL
        next_state, reward, done, info = env.step(2)
        self.assertEqual(env.holdings, 0.0)
        self.assertGreater(env.cash, 0.0)

    def test_rl_agent_action_selection(self):
        env = TradingEnvironment(df=self.df, initial_balance=1_000_000.0)
        agent = RLAgent(state_dim=env.state_dim, action_dim=env.action_dim)

        state = env.reset()
        action = agent.select_action(state, evaluate=True)
        self.assertIn(action, [0, 1, 2])

    def test_backtest_engine_run_all(self):
        engine = BacktestEngine(df=self.df, initial_balance=1_000_000.0, fee_pct=0.04)
        results = engine.run_all()
        self.assertIn("Buy_and_Hold", results)
        self.assertIn("High_Turnover_Scalping", results)
        self.assertIn("Volatility_Breakout", results)
        self.assertIn("total_return_pct", results["Buy_and_Hold"])

if __name__ == "__main__":
    unittest.main()
