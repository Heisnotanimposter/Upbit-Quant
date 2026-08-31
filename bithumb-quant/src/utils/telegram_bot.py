import asyncio
import logging
import requests
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger("TelegramBot")

class TelegramNotifier:
    """
    Handles outbound push alerts and inbound command listeners for remote mobile management.
    """

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.command_callbacks: Dict[str, Callable] = {}
        self.last_update_id = 0
        self.is_running = False

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Sends instant push notification to user's Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.debug(f"[Telegram Disconnected] Alert: {text}")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def register_command(self, command: str, callback: Callable):
        """Registers a handler for incoming commands like /status, /balance, /pause, /resume."""
        self.command_callbacks[command.lower()] = callback

    async def start_command_listener(self):
        """Asynchronous polling loop to handle incoming commands from mobile Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.info("Telegram command listener disabled (bot_token/chat_id missing).")
            return

        self.is_running = True
        logger.info("Telegram Command Listener active. Ready for mobile remote commands.")

        while self.is_running:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"offset": self.last_update_id + 1, "timeout": 10}

                # Run blocking HTTP call in executor to keep event loop responsive
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: requests.get(url, params=params, timeout=15))

                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        for update in data.get("result", []):
                            self.last_update_id = update.get("update_id", self.last_update_id)
                            message = update.get("message", {})
                            text = message.get("text", "").strip()
                            sender_id = str(message.get("chat", {}).get("id", ""))

                            # Security Auth check: Only execute commands from authorized TELEGRAM_CHAT_ID
                            from src.utils.security import SecurityGuard
                            if text.startswith("/"):
                                if SecurityGuard.is_authorized_telegram_user(sender_id, self.chat_id):
                                    cmd = text.split()[0].lower()
                                    if cmd in self.command_callbacks:
                                        logger.info(f"Received authorized Telegram command: {cmd}")
                                        reply = await self.command_callbacks[cmd]()
                                        if reply:
                                            self.send_message(reply)
                                    else:
                                        self.send_message(f"❓ Unknown command: {cmd}\nAvailable: /status, /balance, /pause, /resume, /closeall")
                                else:
                                    logger.warning(f"Security: Blocked unauthorized command attempt '{text}' from Chat ID {sender_id}")

            except Exception as e:
                logger.warning(f"Telegram polling update error: {e}")

            await asyncio.sleep(2)

    def stop(self):
        self.is_running = False
