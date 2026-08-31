#!/usr/bin/env python3
"""
Integration & Real-Time Data Test Runner for Bithumb Quant Bot.
Verifies live API connection, strategy indicators, Gemini AI advisor, SQLite DB state, and security guards.
"""

import sys
import unittest
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TestRunner")

from config.config import config
from src.api.bithumb_client import BithumbClient
from src.api.gemini_advisor import GeminiAdvisor
from src.core.state_db import StateDB
from src.core.risk_manager import RiskManager
from src.strategies.quant_strategy import QuantStrategy
from src.utils.security import SecurityGuard

def run_unit_tests():
    logger.info("==================================================")
    logger.info("🧪 Step 1: Running Automated Unit Test Suite...")
    logger.info("==================================================")
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        logger.error("❌ Unit tests FAILED!")
        return False
    logger.info("✅ All Unit Tests Passed Successfully!\n")
    return True

def run_real_time_dry_run():
    logger.info("==================================================")
    logger.info("🌐 Step 2: Executing Live Market Data Dry-Run Test...")
    logger.info("==================================================")

    # 1. Test Security Guards
    logger.info("🔒 Testing Security Guards...")
    SecurityGuard.enforce_file_permissions(".env", 0o600)
    logger.info(f"Masked Bithumb Key: {SecurityGuard.mask_secret(config.BITHUMB_ACCESS_KEY)}")
    logger.info(f"Masked Gemini Key:  {SecurityGuard.mask_secret(config.GEMINI_API_KEY)}")

    # 2. Test Bithumb Public API Data Fetching
    client = BithumbClient(config.BITHUMB_ACCESS_KEY, config.BITHUMB_SECRET_KEY, dry_run=True)
    logger.info("📊 Fetching live market tickers from Bithumb...")

    market_summary = {}
    strategy = QuantStrategy(config.STRATEGY)
    from src.strategies.high_turnover_strategy import HighTurnoverStrategy
    high_turnover = HighTurnoverStrategy(config.HIGH_TURNOVER_STRATEGY)

    logger.info(f"Fee Hurdle Config: Min Gross Profit = +{high_turnover.min_gross_hurdle_pct:.3f}% (Net: +{high_turnover.target_net_profit_pct}%)")

    for symbol in config.SYMBOLS:
        curr_code = symbol.split("_")[0]
        ticker = client.get_ticker(curr_code)
        if ticker:
            close_price = float(ticker.get("closing_price", 0))
            tp_price = high_turnover.get_take_profit_price(close_price)
            logger.info(f"  • {symbol} Live Price: {close_price:,.0f} KRW | Fee-Adjusted TP Target: {tp_price:,.0f} KRW (+{high_turnover.min_gross_hurdle_pct:.2f}%)")
            market_summary[symbol] = {
                "current_price": close_price,
                "24h_change_rate": float(ticker.get("fluctate_rate_24H", 0)),
                "24h_volume": float(ticker.get("units_traded_24H", 0))
            }

        # Test high-turnover 3m candlestick data & signals
        candles_3m = client.get_candlestick(curr_code, interval="3m")
        if candles_3m:
            metrics_3m = high_turnover.analyze_candlesticks(candles_3m)
            if metrics_3m:
                sig_3m = high_turnover.generate_signal(metrics_3m, ai_regime="BULL_TREND")
                logger.info(f"    ↳ Scalp 3m: EMA_Fast={metrics_3m['ema_fast']:,.0f} | RSI={metrics_3m['rsi']:.1f} | Signal={sig_3m['signal']}")

            # Test Hybrid AI-RL Strategy
            from src.strategies.hybrid_strategy import HybridAIRLStrategy
            hybrid_strat = HybridAIRLStrategy(config.HYBRID_RL_STRATEGY)
            hybrid_metrics = hybrid_strat.analyze_candlesticks(candles_3m)
            if hybrid_metrics:
                hybrid_sig = hybrid_strat.generate_signal(hybrid_metrics, ai_regime="BULL_TREND")
                logger.info(f"    ↳ 🧠 Hybrid AI-RL (Dueling DQN): RL_Action={hybrid_metrics.get('rl_action')} | Signal={hybrid_sig['signal']}")

    # 3. Test Gemini Advisor
    logger.info("\n🧠 Testing Google AI Studio (Gemini) Advisor...")
    advisor = GeminiAdvisor(config.GEMINI_API_KEY, model_name=config.AI_ADVISOR.get("model_name", "gemini-2.5-flash"))
    regime_res = advisor.evaluate_market_regime(market_summary)
    logger.info(f"Gemini Evaluation Result: Regime={regime_res.get('regime')}, Multiplier={regime_res.get('position_multiplier')}, Reason={regime_res.get('reasoning')}")

    # 4. Test SQLite DB State Persistence
    test_db_path = "test_bithumb_quant.db"
    logger.info(f"\n💾 Testing SQLite DB Persistence on {test_db_path}...")
    db = StateDB(db_path=test_db_path)
    db.save_position("BTC_KRW", entry_price=50000000.0, amount=0.1, invested_krw=5000000.0, stop_loss_price=48500000.0)

    pos = db.get_position("BTC_KRW")
    assert pos is not None, "Failed to retrieve position from test DB!"
    logger.info(f"DB Test Verified: Retrieved position {pos['symbol']} @ {pos['entry_price']:,.0f} KRW")

    db.close_position("BTC_KRW")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    logger.info("\n🎉 Real-Time Dry-Run Test Completed Successfully!")
    return True

if __name__ == "__main__":
    success_unit = run_unit_tests()
    if not success_unit:
        sys.exit(1)

    success_dry = run_real_time_dry_run()
    if not success_dry:
        sys.exit(1)

    print("\n✅ ALL TESTS PASSED SUCCESSFULLY! SYSTEM IS READY FOR DEPLOYMENT.")
