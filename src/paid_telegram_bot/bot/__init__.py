"""Bot package — Telegram bot lifecycle and handlers."""

from .bot_manager import BotManager, get_bot_manager

__all__ = ["BotManager", "get_bot_manager"]
