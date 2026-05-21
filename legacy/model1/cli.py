"""
Command-line interface for UPbit Quantitative Trading Platform.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from .core.logger import get_logger
from .core.config import config
from .core.exceptions import UPbitQuantError


logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="UPbit Quant")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config-file', '-c', type=click.Path(exists=True), help='Configuration file path')
def cli(verbose: bool, config_file: Optional[str]) -> None:
    """
    UPbit Quantitative Trading Platform CLI.
    
    A comprehensive quantitative trading platform for cryptocurrency markets.
    """
    if verbose:
        # Set log level to DEBUG
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    if config_file:
        # Load custom configuration
        config_path = Path(config_file)
        if config_path.exists():
            logger.info(f"Loading configuration from {config_path}")
        else:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)


@cli.command()
@click.option('--symbol', '-s', default='BTC-KRW', help='Trading symbol')
@click.option('--episodes', '-e', default=1000, help='Number of training episodes')
@click.option('--initial-balance', '-b', default=10000.0, help='Initial balance')
@click.option('--save-model', '-m', type=click.Path(), help='Path to save trained model')
def train(symbol: str, episodes: int, initial_balance: float, save_model: Optional[str]) -> None:
    """Train a trading bot using reinforcement learning."""
    try:
        from .main.trading_environment import TradingEnv
        from .ticker.trader1 import QLearningBot, QLearningConfig
        
        logger.info(f"Starting training for {symbol} with {episodes} episodes")
        
        # Create trading environment
        # Note: In practice, you would load real price data here
        import numpy as np
        prices = np.random.randn(1000).cumsum() + 100  # Mock price data
        prices = np.abs(prices)  # Ensure positive prices
        
        env = TradingEnv(
            prices=prices.tolist(),
            initial_balance=initial_balance
        )
        
        # Create Q-learning bot
        bot_config = QLearningConfig(
            alpha=0.5,
            gamma=0.6,
            epsilon=0.1
        )
        bot = QLearningBot(env.action_space, bot_config)
        
        # Training loop
        for episode in range(episodes):
            episode_metrics = bot.train_episode(env)
            
            if episode % 100 == 0:
                logger.info(f"Episode {episode}: {episode_metrics}")
        
        # Save model if requested
        if save_model:
            bot.save_model(save_model)
            logger.info(f"Model saved to {save_model}")
        
        # Print final performance
        performance = bot.get_performance_summary()
        logger.info(f"Training completed. Final performance: {performance}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise click.ClickException(f"Training failed: {e}")


@cli.command()
@click.option('--model-path', '-m', type=click.Path(exists=True), help='Path to trained model')
@click.option('--symbol', '-s', default='BTC-KRW', help='Trading symbol')
@click.option('--episodes', '-e', default=100, help='Number of test episodes')
def test(model_path: str, symbol: str, episodes: int) -> None:
    """Test a trained trading bot."""
    try:
        from .main.trading_environment import TradingEnv
        from .ticker.trader1 import QLearningBot
        
        logger.info(f"Testing model {model_path} for {symbol}")
        
        # Load trained model
        bot = QLearningBot(None)  # Will be set after loading
        bot.load_model(model_path)
        
        # Create test environment
        import numpy as np
        prices = np.random.randn(1000).cumsum() + 100
        prices = np.abs(prices)
        
        env = TradingEnv(prices=prices.tolist())
        
        # Test the bot
        total_reward = 0
        for episode in range(episodes):
            state = env.reset()
            done = False
            episode_reward = 0
            
            while not done:
                action = bot.get_action(state)
                state, reward, done, info = env.step(action)
                episode_reward += reward
            
            total_reward += episode_reward
        
        average_reward = total_reward / episodes
        logger.info(f"Test completed. Average reward: {average_reward:.2f}")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        raise click.ClickException(f"Testing failed: {e}")


@cli.command()
@click.option('--host', '-h', default='localhost', help='Host to bind to')
@click.option('--port', '-p', default=8501, help='Port to bind to')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
def web(host: str, port: int, debug: bool) -> None:
    """Start the web interface."""
    try:
        import subprocess
        import sys
        
        logger.info(f"Starting web interface on {host}:{port}")
        
        # Start Streamlit app
        cmd = [
            sys.executable, '-m', 'streamlit', 'run',
            'GUI/PythonUI/QuantStreamlit.py',
            '--server.address', host,
            '--server.port', str(port)
        ]
        
        if debug:
            cmd.extend(['--logger.level', 'debug'])
        
        subprocess.run(cmd)
        
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        raise click.ClickException(f"Failed to start web interface: {e}")


@cli.command()
def config_info() -> None:
    """Display current configuration information."""
    try:
        logger.info("Current configuration:")
        
        config_dict = {
            'Database URL': config.database_url,
            'Debug Mode': config.debug,
            'Log Level': config.log_level,
            'Initial Balance': config.default_initial_balance,
            'Max Position Size': config.max_position_size,
            'Risk Tolerance': config.risk_tolerance,
            'Trading Fee': config.trading_fee,
        }
        
        for key, value in config_dict.items():
            click.echo(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"Failed to display configuration: {e}")
        raise click.ClickException(f"Failed to display configuration: {e}")


@cli.command()
@click.option('--symbol', '-s', default='BTC-KRW', help='Symbol to fetch data for')
@click.option('--days', '-d', default=30, help='Number of days of data to fetch')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def fetch_data(symbol: str, days: int, output: Optional[str]) -> None:
    """Fetch market data for analysis."""
    try:
        import yfinance as yf
        import pandas as pd
        
        logger.info(f"Fetching {days} days of data for {symbol}")
        
        # Fetch data (this is a simplified example)
        # In practice, you would use the actual Upbit API
        ticker = yf.Ticker(symbol.replace('-', '-USD'))
        data = ticker.history(period=f"{days}d")
        
        if output:
            data.to_csv(output)
            logger.info(f"Data saved to {output}")
        else:
            click.echo(data.head())
        
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise click.ClickException(f"Failed to fetch data: {e}")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except UPbitQuantError as e:
        logger.error(f"UPbit Quant error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
