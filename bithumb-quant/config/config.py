import os
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.utils.security import SecurityGuard

logger = logging.getLogger("Config")

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    SecurityGuard.enforce_file_permissions(str(env_path), 0o600)
else:
    load_dotenv()

class Config:
    # Environment Variables
    BITHUMB_ACCESS_KEY = os.getenv("BITHUMB_ACCESS_KEY", "")
    BITHUMB_SECRET_KEY = os.getenv("BITHUMB_SECRET_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
    DB_PATH = os.getenv("DB_PATH", "bithumb_quant.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Load YAML Settings
    _settings_file = Path(__file__).resolve().parent / "settings.yaml"
    _settings = {}
    if _settings_file.exists():
        with open(_settings_file, "r", encoding="utf-8") as f:
            _settings = yaml.safe_load(f) or {}

    SYMBOLS = _settings.get("symbols", ["BTC_KRW", "ETH_KRW"])
    ACTIVE_STRATEGY = _settings.get("active_strategy", "hybrid_rl")
    HYBRID_RL_STRATEGY = _settings.get("hybrid_rl", {})
    HIGH_TURNOVER_STRATEGY = _settings.get("high_turnover_strategy", {})
    STRATEGY = _settings.get("strategy", {})
    RISK = _settings.get("risk", {})
    AI_ADVISOR = _settings.get("ai_advisor", {})

    @classmethod
    def validate(cls):
        """Validates critical settings and logs masked secrets."""
        logger.info(f"Loaded Config - Bithumb Access Key: {SecurityGuard.mask_secret(cls.BITHUMB_ACCESS_KEY)}")
        logger.info(f"Loaded Config - Gemini API Key: {SecurityGuard.mask_secret(cls.GEMINI_API_KEY)}")
        logger.info(f"Loaded Config - Telegram Bot Token: {SecurityGuard.mask_secret(cls.TELEGRAM_BOT_TOKEN)}")
        logger.info(f"Trading Mode: {'PAPER TRADING (SIMULATION)' if cls.DRY_RUN else 'REAL MONEY LIVE'}")

        # Enforce file permission hardening on SQLite DB if it exists
        if Path(cls.DB_PATH).exists():
            SecurityGuard.enforce_file_permissions(cls.DB_PATH, 0o600)

        if not cls.DRY_RUN:
            if not cls.BITHUMB_ACCESS_KEY or not cls.BITHUMB_SECRET_KEY:
                raise ValueError("LIVE TRADING ENABLED (DRY_RUN=false) but Bithumb API credentials are missing!")
        return True

config = Config()
