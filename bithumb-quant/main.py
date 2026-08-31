import sys
import signal
import asyncio
import logging
from pathlib import Path

from config.config import config
from src.core.engine import QuantTradingEngine

# Setup Logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "bithumb_quant.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("Main")

def main():
    logger.info("Initializing Bithumb Quant Auto-Trading Engine...")
    try:
        config.validate()
    except ValueError as e:
        logger.critical(f"Configuration Validation Error: {e}")
        sys.exit(1)

    engine = QuantTradingEngine()

    # Graceful Shutdown Signal Handler
    def handle_shutdown(signum, frame):
        logger.info(f"Received shutdown signal ({signum}). Terminating engine gracefully...")
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        logger.info("Engine stopped by user KeyboardInterrupt.")
    except Exception as e:
        logger.critical(f"Fatal Engine Failure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
