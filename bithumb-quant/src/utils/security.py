import os
import stat
import logging
from pathlib import Path

logger = logging.getLogger("Security")

class SecurityGuard:
    """
    Implements baseline security features:
    - Secret masking for logs/alerts
    - File permission hardening (0600 on secrets and databases)
    - Telegram caller authorization
    - Hard order cap (fat-finger protection)
    """

    @staticmethod
    def mask_secret(secret: str) -> str:
        """Masks sensitive strings so only first 2 and last 4 characters are visible."""
        if not secret:
            return "<NOT SET>"
        if len(secret) <= 6:
            return "***"
        return f"{secret[:2]}***{secret[-4:]}"

    @staticmethod
    def enforce_file_permissions(file_path: str, mode: int = 0o600):
        """Enforces restrictive read/write permissions on sensitive files (.env, .db)."""
        path = Path(file_path)
        if path.exists():
            try:
                os.chmod(path, mode)
                logger.info(f"Security: Applied file permission {oct(mode)} to {path.name}")
            except Exception as e:
                logger.warning(f"Security: Could not set permission on {path.name}: {e}")

    @staticmethod
    def is_authorized_telegram_user(caller_chat_id: str, expected_chat_id: str) -> bool:
        """Strictly validates Telegram user ID to prevent unauthorized remote commands."""
        if not expected_chat_id:
            logger.warning("Security Warning: TELEGRAM_CHAT_ID is not configured. Rejecting all commands.")
            return False
        is_match = str(caller_chat_id).strip() == str(expected_chat_id).strip()
        if not is_match:
            logger.warning(f"🚨 Security Alert: Unauthorized Telegram command attempt from Chat ID: {caller_chat_id}")
        return is_match

    @staticmethod
    def check_fat_finger_cap(amount_krw: float, max_hard_cap_krw: float = 10_000_000.0) -> bool:
        """Prevents accidental excessive trades above maximum hard cap."""
        if amount_krw > max_hard_cap_krw:
            logger.critical(
                f"🚨 FAT-FINGER GUARD TRIGGERED: Requested order amount ({amount_krw:,.0f} KRW) "
                f"exceeds hard cap limit ({max_hard_cap_krw:,.0f} KRW). Order BLOCKED."
            )
            return False
        return True
