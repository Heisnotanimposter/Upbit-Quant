import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from config.config import config
from src.api.bithumb_client import BithumbClient
from src.api.gemini_advisor import GeminiAdvisor
from src.core.state_db import StateDB
from src.core.risk_manager import RiskManager
from src.strategies.quant_strategy import QuantStrategy
from src.strategies.high_turnover_strategy import HighTurnoverStrategy
from src.strategies.hybrid_strategy import HybridAIRLStrategy
from src.utils.telegram_bot import TelegramNotifier

logger = logging.getLogger("TradingEngine")

class QuantTradingEngine:
    """
    Master 24/7 Quantitative Trading Engine.
    Supports Hybrid AI-RL (Gemini + Dueling DQN), High-Turnover Seed Compounding, and Volatility Breakout.
    """

    def __init__(self):
        self.config = config
        self.bithumb = BithumbClient(
            access_key=config.BITHUMB_ACCESS_KEY,
            secret_key=config.BITHUMB_SECRET_KEY,
            dry_run=config.DRY_RUN
        )
        self.gemini = GeminiAdvisor(
            api_key=config.GEMINI_API_KEY,
            model_name=config.AI_ADVISOR.get("model_name", "gemini-2.5-flash")
        )
        self.db = StateDB(db_path=config.DB_PATH)
        self.risk = RiskManager(risk_config=config.RISK)

        # Strategy Selection
        self.active_strategy_type = getattr(config, "ACTIVE_STRATEGY", "hybrid_rl")
        if self.active_strategy_type == "hybrid_rl":
            self.strategy = HybridAIRLStrategy(config=config.HYBRID_RL_STRATEGY)
            self.tick_interval_sec = config.HYBRID_RL_STRATEGY.get("tick_interval_sec", 10)
            self.candle_interval = config.HYBRID_RL_STRATEGY.get("candle_interval", "3m")
            logger.info("Activated Production Hybrid AI-RL Strategy (Gemini + DRL Policy).")
        elif self.active_strategy_type == "high_turnover":
            self.strategy = HighTurnoverStrategy(config=config.HIGH_TURNOVER_STRATEGY)
            self.tick_interval_sec = config.HIGH_TURNOVER_STRATEGY.get("tick_interval_sec", 10)
            self.candle_interval = config.HIGH_TURNOVER_STRATEGY.get("candle_interval", "3m")
            logger.info("Activated High-Turnover Seed Compounding Strategy (Rule Scalping).")
        else:
            self.strategy = QuantStrategy(strategy_config=config.STRATEGY)
            self.tick_interval_sec = 60
            self.candle_interval = config.STRATEGY.get("candle_interval", "24h")
            logger.info("Activated Daily Volatility Breakout Strategy.")

        self.telegram = TelegramNotifier(
            bot_token=config.TELEGRAM_BOT_TOKEN,
            chat_id=config.TELEGRAM_CHAT_ID
        )

        self.is_paused = False
        self.running = False
        self.current_ai_regime = "NEUTRAL"
        self.current_ai_multiplier = 1.0
        self.last_ai_eval_time = 0.0
        self.ai_eval_interval_sec = config.AI_ADVISOR.get("evaluation_interval_hours", 2) * 3600

        # Register Telegram commands
        self.telegram.register_command("/status", self._handle_cmd_status)
        self.telegram.register_command("/balance", self._handle_cmd_balance)
        self.telegram.register_command("/model", self._handle_cmd_model)
        self.telegram.register_command("/pause", self._handle_cmd_pause)
        self.telegram.register_command("/resume", self._handle_cmd_resume)
        self.telegram.register_command("/closeall", self._handle_cmd_closeall)

    async def start(self):
        """Starts the 24/7 Trading Loop and background services."""
        self.running = True
        mode_str = "PAPER TRADING (SIMULATION)" if config.DRY_RUN else "🚨 LIVE REAL MONEY TRADING"
        logger.info(f"Starting Bithumb Quant Engine 24/7 | Strategy: {self.active_strategy_type} | Mode: {mode_str}")
        self.telegram.send_message(
            f"🚀 *Bithumb Quant Bot Started*\n"
            f"Strategy: `{self.active_strategy_type}` (Interval: `{self.candle_interval}`)\n"
            f"Mode: `{mode_str}`\n"
            f"Symbols: `{', '.join(config.SYMBOLS)}`"
        )

        # Initialize baseline equity
        balance_res = self.bithumb.get_balance("ALL")
        total_equity = self._calculate_total_equity(balance_res)
        self.risk.initialize_daily_equity(total_equity)

        # Start Telegram listener background task
        asyncio.create_task(self.telegram.start_command_listener())

        # Main 24/7 Event Loop
        while self.running:
            try:
                if not self.is_paused:
                    await self._run_trading_cycle()
                else:
                    logger.info("Engine is currently PAUSED.")
            except Exception as e:
                logger.error(f"Error in trading cycle loop: {e}", exc_info=True)
                self.telegram.send_message(f"⚠️ *Engine Warning*: `{str(e)}`")

            await asyncio.sleep(self.tick_interval_sec)

    async def _run_trading_cycle(self):
        """Executes a single market scan, position evaluation, and trade cycle."""
        # 1. Periodic Gemini AI Market Regime Check
        now = time.time()
        if now - self.last_ai_eval_time > self.ai_eval_interval_sec:
            await self._run_ai_regime_evaluation()
            self.last_ai_eval_time = now

        # 2. Check current balance & equity
        balance_data = self.bithumb.get_balance("ALL")
        total_equity = self._calculate_total_equity(balance_data)

        # 3. Check Daily Drawdown Circuit Breaker
        cb_triggered, cb_reason = self.risk.check_circuit_breaker(total_equity)
        if cb_triggered:
            self.is_paused = True
            self.telegram.send_message(f"🚨 *CIRCUIT BREAKER TRIGGERED*\n{cb_reason}\nPausing engine and liquidating all positions.")
            await self._liquidate_all_positions("Circuit Breaker Activated")
            return

        # 4. Monitor Open Positions (Fee-Adjusted Take-Profit, RL Policy Sells, Timeout)
        open_positions = self.db.get_all_open_positions()
        for pos in open_positions:
            symbol = pos["symbol"]
            curr_code = symbol.split("_")[0]
            ticker = self.bithumb.get_ticker(curr_code)
            if not ticker:
                continue

            current_price = float(ticker.get("closing_price", 0))
            candles = self.bithumb.get_candlestick(curr_code, interval=self.candle_interval)

            # Strategy-specific exit evaluation
            if self.active_strategy_type in ("hybrid_rl", "high_turnover"):
                if self.active_strategy_type == "hybrid_rl":
                    exit_eval = self.strategy.check_exit_condition(
                        entry_price=pos["entry_price"],
                        current_price=current_price,
                        opened_at_str=pos.get("opened_at", ""),
                        candles=candles
                    )
                else:
                    exit_eval = self.strategy.check_exit_condition(
                        entry_price=pos["entry_price"],
                        current_price=current_price,
                        opened_at_str=pos.get("opened_at", "")
                    )

                if exit_eval["should_exit"]:
                    await self._execute_sell(pos, current_price, exit_eval["reason"])
                    continue

            # Universal hard stop / trailing stop check
            should_sell, new_peak, new_stop = self.risk.evaluate_trailing_stop(
                entry_price=pos["entry_price"],
                current_price=current_price,
                current_peak=pos["trailing_peak"],
                current_stop_loss=pos["stop_loss_price"]
            )

            if should_sell:
                reason = "Trailing Stop Loss Hit" if current_price > pos["entry_price"] else "Hard Stop Loss Hit"
                await self._execute_sell(pos, current_price, reason)
            elif new_peak > pos["trailing_peak"] or new_stop > pos["stop_loss_price"]:
                self.db.update_trailing_peak(symbol, new_peak, new_stop)

        # 5. Scan Symbols for Buy Opportunities (Hybrid AI-RL or Scalping)
        available_krw = float(balance_data.get("data", {}).get("available_krw", 0))
        open_count = len(self.db.get_all_open_positions())

        if self.risk.can_open_new_position(open_count):
            for symbol in config.SYMBOLS:
                if self.db.get_position(symbol):
                    continue

                curr_code = symbol.split("_")[0]
                candles = self.bithumb.get_candlestick(curr_code, interval=self.candle_interval)
                if not candles:
                    continue

                if self.active_strategy_type == "hybrid_rl":
                    metrics = self.strategy.analyze_candlesticks(candles, current_position=None)
                else:
                    metrics = self.strategy.analyze_candlesticks(candles)

                signal_res = self.strategy.generate_signal(metrics, ai_regime=self.current_ai_regime)

                if signal_res["signal"] == "BUY":
                    target_krw = self.risk.calculate_position_size(available_krw, metrics["current_price"], self.current_ai_multiplier)
                    if target_krw >= self.risk.min_order_krw:
                        await self._execute_buy(curr_code, symbol, metrics["current_price"], target_krw, signal_res["reason"])
                        available_krw -= target_krw
                        break

    async def _run_ai_regime_evaluation(self):
        """Aggregates market stats and queries Google AI Studio."""
        logger.info("Executing Google AI Studio Market Regime Evaluation...")
        market_summary = {}

        for symbol in config.SYMBOLS:
            curr_code = symbol.split("_")[0]
            ticker = self.bithumb.get_ticker(curr_code)
            if ticker:
                market_summary[symbol] = {
                    "current_price": float(ticker.get("closing_price", 0)),
                    "24h_change_rate": float(ticker.get("fluctate_rate_24H", 0)),
                    "24h_volume": float(ticker.get("units_traded_24H", 0))
                }

        res = self.gemini.evaluate_market_regime(market_summary)
        self.current_ai_regime = res.get("regime", "NEUTRAL")
        self.current_ai_multiplier = res.get("position_multiplier", 1.0)
        reasoning = res.get("reasoning", "")

        self.db.log_ai_assessment(self.current_ai_regime, res.get("risk_level", "NEUTRAL"), self.current_ai_multiplier, reasoning)
        self.telegram.send_message(
            f"🧠 *Google AI Studio Advisory*\n"
            f"Regime: `{self.current_ai_regime}` | Multiplier: `{self.current_ai_multiplier:.2f}x`\n"
            f"Analysis: {reasoning}"
        )

    async def _execute_buy(self, order_currency: str, symbol: str, current_price: float, total_krw: float, reason: str):
        logger.info(f"Executing BUY for {symbol} | Amount: {total_krw:,.0f} KRW | Reason: {reason}")
        res = self.bithumb.place_market_buy(order_currency, total_krw)

        if res.get("status") == "0000":
            amount = total_krw / current_price
            stop_loss = self.risk.calculate_stop_loss_price(current_price)
            self.db.save_position(symbol, current_price, amount, total_krw, stop_loss)
            self.db.log_trade(symbol, "BUY", current_price, amount, total_krw, reason=reason)

            self.telegram.send_message(
                f"🟢 *BUY EXECUTED (Hybrid AI-RL)*\n"
                f"Symbol: `{symbol}`\n"
                f"Price: `{current_price:,.0f} KRW`\n"
                f"Amount: `{total_krw:,.0f} KRW`\n"
                f"Stop Loss Target: `{stop_loss:,.0f} KRW`\n"
                f"Reason: {reason}"
            )

    async def _execute_sell(self, position: Dict[str, Any], current_price: float, reason: str):
        symbol = position["symbol"]
        curr_code = symbol.split("_")[0]
        amount = position["amount"]
        entry_price = position["entry_price"]
        invested_krw = position["invested_krw"]

        revenue_krw = amount * current_price
        pnl_krw = revenue_krw - invested_krw
        pnl_pct = ((current_price - entry_price) / entry_price) * 100.0

        logger.info(f"Executing SELL for {symbol} | Price: {current_price:,.0f} KRW | PnL: {pnl_pct:+.2f}% | Reason: {reason}")
        res = self.bithumb.place_market_sell(curr_code, amount)

        if res.get("status") == "0000":
            self.db.close_position(symbol)
            self.db.log_trade(symbol, "SELL", current_price, amount, revenue_krw, pnl_krw=pnl_krw, pnl_pct=pnl_pct, reason=reason)

            emoji = "🔴" if pnl_krw < 0 else "🟢"
            self.telegram.send_message(
                f"{emoji} *SELL EXECUTED (Capital Recycled)*\n"
                f"Symbol: `{symbol}`\n"
                f"Exit Price: `{current_price:,.0f} KRW` (Entry: `{entry_price:,.0f}`)\n"
                f"Realized PnL: `{pnl_krw:+,.0f} KRW` (`{pnl_pct:+.2f}%`)\n"
                f"Reason: {reason}"
            )

    async def _liquidate_all_positions(self, reason: str):
        positions = self.db.get_all_open_positions()
        for pos in positions:
            symbol = pos["symbol"]
            curr_code = symbol.split("_")[0]
            ticker = self.bithumb.get_ticker(curr_code)
            curr_price = float(ticker.get("closing_price", pos["entry_price"])) if ticker else pos["entry_price"]
            await self._execute_sell(pos, curr_price, f"Emergency Close: {reason}")

    def _calculate_total_equity(self, balance_data: Dict[str, Any]) -> float:
        bdata = balance_data.get("data", {})
        total_krw = float(bdata.get("total_krw", 0))
        for pos in self.db.get_all_open_positions():
            curr_code = pos["symbol"].split("_")[0]
            ticker = self.bithumb.get_ticker(curr_code)
            if ticker:
                total_krw += pos["amount"] * float(ticker.get("closing_price", pos["entry_price"]))
            else:
                total_krw += pos["invested_krw"]
        return total_krw

    # --- TELEGRAM COMMAND HANDLERS ---

    async def _handle_cmd_status(self) -> str:
        open_pos = self.db.get_all_open_positions()
        stats = self.db.get_today_turnover_stats()
        status_str = "⏸️ PAUSED" if self.is_paused else "▶️ RUNNING"
        mode_str = "Paper Trading" if config.DRY_RUN else "REAL MONEY"
        pos_list = "\n".join([f"• `{p['symbol']}`: Entry `{p['entry_price']:,.0f} KRW`" for p in open_pos]) or "None"

        turnover_vol = stats.get("turnover_volume_krw", 0.0)
        base_seed = self.risk.initial_daily_equity or 1.0
        multiplier = turnover_vol / base_seed if base_seed > 0 else 0.0

        return (
            f"🤖 *Bithumb Quant Status*\n"
            f"Strategy: `{self.active_strategy_type}` | Status: {status_str}\n"
            f"Mode: `{mode_str}` | Gemini Regime: `{self.current_ai_regime}`\n"
            f"🔄 *Daily Turnover*: `{turnover_vol:,.0f} KRW` (`{multiplier:.1f}x Seed Rolling`)\n"
            f"📊 *Today's Record*: `{stats.get('trade_count', 0)} Trades` (Wins: `{stats.get('win_count', 0)}`)\n"
            f"Active Holdings:\n{pos_list}"
        )

    async def _handle_cmd_model(self) -> str:
        if self.active_strategy_type == "hybrid_rl":
            is_loaded = getattr(self.strategy.rl_strategy, "is_model_loaded", False)
            device = getattr(self.strategy.rl_strategy.agent, "device", "unknown")
            model_path = getattr(self.strategy, "model_path", "")
            return (
                f"🧠 *Deep RL Neural Model Status*\n"
                f"Architecture: `Dueling Double DQN (9 Features -> 3 Actions)`\n"
                f"Weights Loaded: `{'✅ ' + model_path if is_loaded else '⚠️ Not Found'}`\n"
                f"Compute Acceleration: `{device}`\n"
                f"Fee Hurdle Target: `+{self.strategy.min_gross_hurdle_pct:.2f}%`"
            )
        return f"Current active strategy is `{self.active_strategy_type}` (not using RL neural model)."

    async def _handle_cmd_balance(self) -> str:
        bdata = self.bithumb.get_balance("ALL")
        total_krw = self._calculate_total_equity(bdata)
        avail_krw = float(bdata.get("data", {}).get("available_krw", 0))
        stats = self.db.get_today_turnover_stats()
        return (
            f"💰 *Portfolio Balance & Compounding*\n"
            f"Total Equity: `{total_krw:,.0f} KRW`\n"
            f"Available Cash: `{avail_krw:,.0f} KRW`\n"
            f"Today Realized PnL: `{stats.get('realized_pnl_krw', 0):+,.0f} KRW`\n"
            f"Daily Traded Volume: `{stats.get('turnover_volume_krw', 0):,.0f} KRW`"
        )

    async def _handle_cmd_pause(self) -> str:
        self.is_paused = True
        return "⏸️ Engine orders have been PAUSED."

    async def _handle_cmd_resume(self) -> str:
        self.is_paused = False
        return "▶️ Engine orders have been RESUMED."

    async def _handle_cmd_closeall(self) -> str:
        await self._liquidate_all_positions("Manual Telegram Request /closeall")
        return "🚨 Liquidated all open positions into KRW."

    def stop(self):
        self.running = False
        self.telegram.stop()
