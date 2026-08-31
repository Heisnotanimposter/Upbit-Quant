#!/usr/bin/env python3
"""
CLI Runner for Bithumb Quant Backtest Simulation & Reinforcement Learning Training.
Supports full 1-year historical runs (e.g. 2025), custom seed scaling (e.g. 100 KRW), trade audit logging, and visual dashboards.
"""

import sys
import argparse
import logging
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BacktestRunner")

from src.backtest.data_loader import DataLoader
from src.backtest.trading_env import TradingEnvironment
from src.ml.rl_agent import RLAgent
from src.backtest.engine import BacktestEngine
from src.backtest.visualizer import BacktestVisualizer

def train_rl_agent(df: pd.DataFrame, episodes: int = 15, initial_balance: float = 100.0, fee_pct: float = 0.04) -> RLAgent:
    """Trains the Dueling Double DQN Reinforcement Learning agent across historical episodes."""
    logger.info("==================================================")
    logger.info(f"🧠 Training Deep Reinforcement Learning Agent ({episodes} Episodes | Seed: {initial_balance:,.2f} KRW)...")
    logger.info("==================================================")

    env = TradingEnvironment(df=df, initial_balance=initial_balance, fee_pct=fee_pct)
    agent = RLAgent(state_dim=env.state_dim, action_dim=env.action_dim)

    for ep in range(1, episodes + 1):
        state = env.reset()
        done = False
        total_reward = 0.0
        losses = []

        while not done:
            action = agent.select_action(state, evaluate=False)
            next_state, reward, done, info = env.step(action)
            agent.store_transition(state, action, reward, next_state, done)
            loss = agent.train_step()

            if loss > 0:
                losses.append(loss)
            state = next_state
            total_reward += reward

        final_eq = info["equity"]
        ret_pct = ((final_eq - initial_balance) / initial_balance) * 100.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        logger.info(
            f"Episode {ep:02d}/{episodes} | Return: {ret_pct:+.2f}% ({initial_balance:,.0f} -> {final_eq:,.2f} KRW) | "
            f"Reward: {total_reward:+.2f} | Trades: {info['trade_count']} | Loss: {avg_loss:.4f} | Epsilon: {agent.epsilon:.3f}"
        )

    # Save trained model weights
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    agent.save_model(str(model_dir / "rl_agent_dueling_dqn.pt"))
    return agent

def export_trade_logs(results: dict, symbol: str, interval: str, year: str = ""):
    """Exports granular trade audit ledger to CSV."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    suffix = f"_{year}" if year else ""
    for name, data in results.items():
        trades = data.get("trades", [])
        if trades:
            csv_path = log_dir / f"backtest_trades_{symbol}_{interval}{suffix}_{name}.csv"
            df_trades = pd.DataFrame(trades)
            df_trades.to_csv(csv_path, index=False)
            logger.info(f"Exported {len(df_trades)} trade logs for {name} to {csv_path}")

def print_terminal_summary(results: dict, initial_seed: float = 100.0, year_str: str = ""):
    """Prints a clean tabular performance overview to terminal."""
    header_title = f"2025 1-YEAR BACKTEST REPORT (Initial Seed: {initial_seed:,.2f} KRW)" if year_str == "2025" else f"BACKTEST REPORT (Initial Seed: {initial_seed:,.2f} KRW)"
    print("\n" + "=" * 125)
    print(f"📈 {header_title}")
    print("=" * 125)
    print(f"{'STRATEGY MODEL':<25} | {'START SEED':<12} | {'FINAL EQUITY':<14} | {'NET RETURN':<10} | {'MAX DD':<9} | {'SHARPE':<8} | {'WIN RATE':<9} | {'TURNOVER':<10} | {'FEES':<10}")
    print("=" * 125)

    for name, data in results.items():
        final_eq = data.get("final_equity", initial_seed)
        ret = data.get("total_return_pct", 0)
        mdd = data.get("max_drawdown_pct", 0)
        sharpe = data.get("sharpe_ratio", 0)
        win_rate = data.get("win_rate_pct", 0)
        turnover = data.get("turnover_multiplier", 0)
        fees = data.get("total_fees_paid_krw", 0)

        print(
            f"{name:<25} | {initial_seed:10,.2f} KRW | {final_eq:12,.2f} KRW | {ret:+9.2f}% | -{mdd:7.2f}% | "
            f"{sharpe:8.2f} | {win_rate:8.1f}% | {turnover:9.1f}x | {fees:8,.2f} KRW"
        )
    print("=" * 125 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Bithumb Quant 1-Year Backtesting & Reinforcement Learning")
    parser.add_argument("--symbol", type=str, default="BTC_KRW", help="Trading pair symbol (e.g. BTC_KRW, ETH_KRW)")
    parser.add_argument("--interval", type=str, default="24h", help="Candle interval (1h, 24h, 3m)")
    parser.add_argument("--year", type=int, default=2025, help="Backtest year filter (e.g. 2025 for 1-year trade)")
    parser.add_argument("--episodes", type=int, default=15, help="RL training episodes")
    parser.add_argument("--balance", type=float, default=100.0, help="Initial simulation seed capital in KRW (default: 100 KRW)")
    parser.add_argument("--fee", type=float, default=0.04, help="Bithumb fee % per trade (default 0.04)")
    parser.add_argument("--slippage", type=float, default=0.05, help="Estimated slippage % (default 0.05)")
    parser.add_argument("--force-download", action="store_true", help="Force fresh download of historical candles")
    args = parser.parse_args()

    # 1. Load historical dataset (supports full 1-year 2025)
    loader = DataLoader(cache_dir="data")
    df = loader.get_candlestick_data(symbol=args.symbol, interval=args.interval, year=args.year, force_download=args.force_download)

    if df.empty or len(df) < 50:
        logger.error(f"Failed to load sufficient historical data for {args.symbol} (Year: {args.year}).")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} candles for {args.symbol} (Time Range: {df['datetime'].min()} to {df['datetime'].max()}).")

    # 2. Train Reinforcement Learning Agent on 2025 historical data
    rl_agent = train_rl_agent(
        df=df,
        episodes=args.episodes,
        initial_balance=args.balance,
        fee_pct=args.fee
    )

    # 3. Run Comparative Multi-Strategy Simulation with 100 KRW initial seed
    logger.info("==================================================")
    logger.info(f"📊 Running 2025 1-Year Multi-Strategy Simulation (Seed: {args.balance:,.2f} KRW)...")
    logger.info("==================================================")
    engine = BacktestEngine(
        df=df,
        initial_balance=args.balance,
        fee_pct=args.fee,
        slippage_pct=args.slippage
    )
    results = engine.run_all(rl_agent=rl_agent)

    # 4. Print Tabular Summary & Export Trade Audit Ledger
    print_terminal_summary(results, initial_seed=args.balance, year_str=str(args.year))
    export_trade_logs(results, args.symbol, args.interval, str(args.year))

    # 5. Generate Interactive Visual Dashboard
    output_html = "backtest_results.html"
    BacktestVisualizer.generate_html_report(results, df, output_path=output_html)
    print(f"🎉 Interactive 2025 1-Year Backtest Dashboard created: file://{Path(output_html).resolve()}\n")

if __name__ == "__main__":
    main()
