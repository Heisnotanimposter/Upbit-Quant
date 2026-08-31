import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Tuple
from src.backtest.trading_env import TradingEnvironment
from src.ml.rl_agent import RLAgent
from src.strategies.high_turnover_strategy import HighTurnoverStrategy
from src.strategies.quant_strategy import QuantStrategy

logger = logging.getLogger("BacktestEngine")

class BacktestEngine:
    """
    Multi-strategy backtesting engine evaluating RL agent, High-Turnover scalping,
    Volatility Breakout, and Buy & Hold with exact fee and slippage modeling.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 1_000_000.0,
        fee_pct: float = 0.04,
        slippage_pct: float = 0.05
    ):
        self.df = df.copy()
        self.initial_balance = initial_balance
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct

    def run_all(self, rl_agent: RLAgent = None) -> Dict[str, Any]:
        """Runs backtesting across all 4 strategy models and returns comparative performance metrics."""
        results = {}

        # 1. Buy & Hold Benchmark
        results["Buy_and_Hold"] = self._run_buy_and_hold()

        # 2. Volatility Breakout Strategy
        results["Volatility_Breakout"] = self._run_volatility_breakout()

        # 3. High-Turnover Seed Compounding Strategy
        results["High_Turnover_Scalping"] = self._run_high_turnover()

        # 4. Reinforcement Learning Agent
        if rl_agent:
            results["RL_Agent"] = self._run_rl_agent(rl_agent)

        return results

    def _calculate_metrics(self, equity_curve: List[float], trades: List[Dict[str, Any]], total_fees: float) -> Dict[str, Any]:
        eq = np.array(equity_curve)
        if len(eq) == 0:
            return {}

        initial = self.initial_balance
        final = eq[-1]
        total_return_pct = ((final - initial) / initial) * 100.0

        # Drawdown
        peaks = np.maximum.accumulate(eq)
        drawdowns = (peaks - eq) / peaks
        max_drawdown_pct = np.max(drawdowns) * 100.0

        # Daily Returns & Sharpe / Sortino
        returns = np.diff(eq) / eq[:-1]
        mean_ret = np.mean(returns) if len(returns) > 0 else 0
        std_ret = np.std(returns) if len(returns) > 0 else 1e-6
        downside_std = np.std(returns[returns < 0]) if np.sum(returns < 0) > 0 else 1e-6

        # Annualized Sharpe (assuming 3m candles ~ 175,200 periods per year)
        periods_per_year = 365 * 24 * (60 / 3)  # approx 3m
        sharpe_ratio = (mean_ret / (std_ret + 1e-9)) * np.sqrt(periods_per_year) if std_ret > 0 else 0.0
        sortino_ratio = (mean_ret / (downside_std + 1e-9)) * np.sqrt(periods_per_year) if downside_std > 0 else 0.0

        # Trade Stats
        closed_trades = [t for t in trades if t.get("type") == "SELL" and "pnl_krw" in t]
        total_closed = len(closed_trades)
        wins = [t for t in closed_trades if t.get("pnl_krw", 0) > 0]
        losses = [t for t in closed_trades if t.get("pnl_krw", 0) <= 0]
        win_rate_pct = (len(wins) / total_closed * 100.0) if total_closed > 0 else 0.0

        gross_profit = sum([t["pnl_krw"] for t in wins]) if wins else 0.0
        gross_loss = abs(sum([t["pnl_krw"] for t in losses])) if losses else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

        # Turnover Volume
        turnover_volume = sum([t.get("price", 0) * t.get("units", 0) for t in trades])
        turnover_multiplier = turnover_volume / initial if initial > 0 else 0.0

        return {
            "initial_balance": initial,
            "final_equity": final,
            "total_return_pct": total_return_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": float(np.clip(sharpe_ratio, -10.0, 100.0)),
            "sortino_ratio": float(np.clip(sortino_ratio, -10.0, 100.0)),
            "win_rate_pct": win_rate_pct,
            "profit_factor": profit_factor,
            "total_trades": len(trades),
            "closed_trades_count": total_closed,
            "total_fees_paid_krw": total_fees,
            "turnover_volume_krw": turnover_volume,
            "turnover_multiplier": turnover_multiplier,
            "equity_curve": equity_curve,
            "trades": trades
        }

    def _run_buy_and_hold(self) -> Dict[str, Any]:
        prices = self.df["close"].values
        initial_price = prices[0] * (1.0 + (self.slippage_pct / 100.0))
        fee = self.initial_balance * (self.fee_pct / 100.0)
        units = (self.initial_balance - fee) / initial_price

        equity_curve = [(units * p) for p in prices]
        exit_fee = equity_curve[-1] * (self.fee_pct / 100.0)
        equity_curve[-1] -= exit_fee

        trades = [
            {"step": 0, "type": "BUY", "price": initial_price, "units": units, "fee": fee},
            {"step": len(prices) - 1, "type": "SELL", "price": prices[-1], "units": 0, "fee": exit_fee, "pnl_krw": equity_curve[-1] - self.initial_balance}
        ]
        return self._calculate_metrics(equity_curve, trades, fee + exit_fee)

    def _run_rl_agent(self, agent: RLAgent) -> Dict[str, Any]:
        env = TradingEnvironment(
            df=self.df,
            initial_balance=self.initial_balance,
            fee_pct=self.fee_pct,
            slippage_pct=self.slippage_pct
        )
        state = env.reset()
        done = False
        equity_curve = [env.initial_balance]

        while not done:
            action = agent.select_action(state, evaluate=True)
            next_state, reward, done, info = env.step(action)
            state = next_state
            equity_curve.append(info["equity"])

        return self._calculate_metrics(equity_curve, env.trades, env.total_fees_paid)

    def _run_high_turnover(self) -> Dict[str, Any]:
        strategy = HighTurnoverStrategy({
            "target_net_profit_pct": 0.35,
            "exchange_fee_pct": self.fee_pct,
            "slippage_buffer_pct": self.slippage_pct,
            "max_hold_time_minutes": 25
        })

        cash = self.initial_balance
        holdings = 0.0
        entry_price = 0.0
        open_step = 0
        total_fees = 0.0
        equity_curve = [cash]
        trades = []

        fee_rate = self.fee_pct / 100.0
        slip_rate = self.slippage_pct / 100.0

        for i in range(25, len(self.df)):
            candle_slice = self.df.iloc[:i+1][["timestamp", "open", "close", "high", "low", "volume"]].values.tolist()
            metrics = strategy.analyze_candlesticks(candle_slice)
            current_price = self.df.iloc[i]["close"]

            # Exit Check
            if holdings > 0:
                elapsed_steps = i - open_step
                tp_price = strategy.get_take_profit_price(entry_price)
                is_timeout = elapsed_steps >= (25 / 3)  # approx 8 candles for 25m

                if current_price >= tp_price or is_timeout:
                    effective_price = current_price * (1.0 - slip_rate)
                    gross = holdings * effective_price
                    fee = gross * fee_rate
                    cash = gross - fee
                    pnl_krw = cash - (holdings * entry_price)
                    pnl_pct = ((effective_price - entry_price) / entry_price) * 100.0
                    total_fees += fee

                    trades.append({
                        "step": i,
                        "type": "SELL",
                        "price": effective_price,
                        "units": 0,
                        "fee": fee,
                        "pnl_krw": pnl_krw,
                        "pnl_pct": pnl_pct,
                        "reason": "Take Profit" if current_price >= tp_price else "Timeout Recycle"
                    })
                    holdings = 0.0
                    entry_price = 0.0

            # Entry Check
            elif cash > 0 and metrics:
                sig = strategy.generate_signal(metrics)
                if sig["signal"] == "BUY":
                    effective_price = current_price * (1.0 + slip_rate)
                    fee = cash * fee_rate
                    net_invest = cash - fee
                    holdings = net_invest / effective_price
                    entry_price = effective_price
                    cash = 0.0
                    open_step = i
                    total_fees += fee

                    trades.append({
                        "step": i,
                        "type": "BUY",
                        "price": effective_price,
                        "units": holdings,
                        "fee": fee
                    })

            equity = cash + (holdings * current_price)
            equity_curve.append(equity)

        return self._calculate_metrics(equity_curve, trades, total_fees)

    def _run_volatility_breakout(self) -> Dict[str, Any]:
        strategy = QuantStrategy({
            "k_noise_ratio": 0.5,
            "ema_fast_period": 5,
            "ema_slow_period": 20,
            "rsi_period": 14,
            "rsi_max_buy": 70
        })

        cash = self.initial_balance
        holdings = 0.0
        entry_price = 0.0
        total_fees = 0.0
        equity_curve = [cash]
        trades = []

        fee_rate = self.fee_pct / 100.0
        slip_rate = self.slippage_pct / 100.0

        for i in range(25, len(self.df)):
            candle_slice = self.df.iloc[:i+1][["timestamp", "open", "close", "high", "low", "volume"]].values.tolist()
            metrics = strategy.analyze_candlesticks(candle_slice)
            current_price = self.df.iloc[i]["close"]

            if holdings > 0:
                # Stop loss (3%) or trend reversal
                if current_price <= entry_price * 0.97 or (metrics and not metrics["is_uptrend"]):
                    effective_price = current_price * (1.0 - slip_rate)
                    gross = holdings * effective_price
                    fee = gross * fee_rate
                    cash = gross - fee
                    pnl_krw = cash - (holdings * entry_price)
                    pnl_pct = ((effective_price - entry_price) / entry_price) * 100.0
                    total_fees += fee

                    trades.append({
                        "step": i,
                        "type": "SELL",
                        "price": effective_price,
                        "units": 0,
                        "fee": fee,
                        "pnl_krw": pnl_krw,
                        "pnl_pct": pnl_pct
                    })
                    holdings = 0.0
                    entry_price = 0.0

            elif cash > 0 and metrics:
                sig = strategy.generate_signal(metrics)
                if sig["signal"] == "BUY":
                    effective_price = current_price * (1.0 + slip_rate)
                    fee = cash * fee_rate
                    net_invest = cash - fee
                    holdings = net_invest / effective_price
                    entry_price = effective_price
                    cash = 0.0
                    total_fees += fee

                    trades.append({
                        "step": i,
                        "type": "BUY",
                        "price": effective_price,
                        "units": holdings,
                        "fee": fee
                    })

            equity = cash + (holdings * current_price)
            equity_curve.append(equity)

        return self._calculate_metrics(equity_curve, trades, total_fees)
