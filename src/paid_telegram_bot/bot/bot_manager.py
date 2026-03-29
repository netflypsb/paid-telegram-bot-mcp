"""Bot lifecycle management — configure, start, stop, status with long-polling."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Any, Optional

from telegram import Bot, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from ..config import get_config
from ..database.database import get_db
from ..database.models import User
from ..database.user_repo import UserRepo
from ..database.usage_repo import UsageRepo

logger = logging.getLogger(__name__)

MAX_RECENT_MESSAGES = 200


class BotManager:
    """Manages a single Telegram bot instance."""

    def __init__(self):
        self._app: Optional[Application] = None
        self._bot: Optional[Bot] = None
        self._running = False
        self._started_at: Optional[datetime] = None
        self._bot_info: Optional[dict[str, Any]] = None
        self._recent_messages: deque[dict[str, Any]] = deque(maxlen=MAX_RECENT_MESSAGES)
        self._polling_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def bot(self) -> Optional[Bot]:
        return self._bot

    @property
    def app(self) -> Optional[Application]:
        return self._app

    @property
    def recent_messages(self) -> list[dict[str, Any]]:
        return list(self._recent_messages)

    def get_status(self) -> dict[str, Any]:
        """Get current bot status."""
        uptime = None
        if self._started_at:
            uptime = str(datetime.utcnow() - self._started_at)

        return {
            "running": self._running,
            "bot_info": self._bot_info,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "uptime": uptime,
            "recent_messages_count": len(self._recent_messages),
        }

    async def configure(self, token: str, **kwargs: Any) -> dict[str, Any]:
        """Configure the bot with a token and optional settings."""
        config = get_config()
        config.bot.token = token

        for key in ("access_mode", "group_mode", "group_activation",
                     "welcome_message", "max_outbound_per_hour_free"):
            if key in kwargs:
                setattr(config.bot, key, kwargs[key])

        config.save()

        # Validate token by calling getMe
        try:
            bot = Bot(token=token)
            me = await bot.get_me()
            info = {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "is_bot": me.is_bot,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
            }
            return {"status": "configured", "bot": info}
        except Exception as e:
            return {"status": "error", "message": f"Invalid token: {e}"}

    async def start(self) -> dict[str, Any]:
        """Start the Telegram bot with long-polling."""
        if self._running:
            return {"status": "already_running", **self.get_status()}

        config = get_config()
        token = config.bot.token
        if not token:
            return {"status": "error", "message": "No bot token configured. Use bot_configure first."}

        try:
            self._app = (
                ApplicationBuilder()
                .token(token)
                .build()
            )

            # Register handlers
            self._app.add_handler(CommandHandler("start", self._handle_start))
            self._app.add_handler(CommandHandler("help", self._handle_help))
            self._app.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )

            # Initialize and get bot info
            await self._app.initialize()
            self._bot = self._app.bot
            me = await self._bot.get_me()
            self._bot_info = {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
            }

            # Start polling in a background task
            await self._app.start()
            self._polling_task = asyncio.create_task(self._run_polling())

            self._running = True
            self._started_at = datetime.utcnow()

            logger.info("Bot started: @%s", me.username)
            return {"status": "started", **self.get_status()}

        except Exception as e:
            logger.error("Failed to start bot: %s", e)
            self._running = False
            return {"status": "error", "message": str(e)}

    async def _run_polling(self) -> None:
        """Run the updater polling loop."""
        try:
            updater = self._app.updater  # type: ignore
            await updater.start_polling(drop_pending_updates=True)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Polling error: %s", e)
            self._running = False

    async def stop(self) -> dict[str, Any]:
        """Stop the Telegram bot."""
        if not self._running:
            return {"status": "not_running"}

        try:
            if self._polling_task:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass

            if self._app:
                if self._app.updater and self._app.updater.running:
                    await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()

            self._running = False
            self._app = None
            self._bot = None
            stopped_at = datetime.utcnow()
            uptime = str(stopped_at - self._started_at) if self._started_at else "unknown"
            self._started_at = None
            self._bot_info = None

            logger.info("Bot stopped. Uptime: %s", uptime)
            return {"status": "stopped", "uptime": uptime}

        except Exception as e:
            logger.error("Error stopping bot: %s", e)
            self._running = False
            return {"status": "error", "message": str(e)}

    async def _handle_start(self, update: Update, context: Any) -> None:
        """Handle /start command — register user."""
        if not update.effective_user or not update.effective_chat:
            return

        user = update.effective_user
        config = get_config()

        # Register user in database
        try:
            db = await get_db()
            user_repo = UserRepo(db)
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            await user_repo.upsert(db_user)
        except Exception as e:
            logger.error("Failed to register user: %s", e)

        await update.effective_chat.send_message(config.bot.welcome_message)

    async def _handle_help(self, update: Update, context: Any) -> None:
        """Handle /help command."""
        if not update.effective_chat:
            return
        help_text = (
            "<b>Available Commands</b>\n\n"
            "/start — Start the bot\n"
            "/help — Show this help message\n"
        )
        await update.effective_chat.send_message(help_text, parse_mode="HTML")

    async def _handle_message(self, update: Update, context: Any) -> None:
        """Handle incoming text messages — store and track."""
        if not update.effective_user or not update.message or not update.message.text:
            return

        user = update.effective_user
        msg = update.message

        # Store in recent messages buffer
        msg_data = {
            "message_id": msg.message_id,
            "chat_id": msg.chat_id,
            "from_user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
            },
            "text": msg.text,
            "date": msg.date.isoformat() if msg.date else None,
        }
        self._recent_messages.append(msg_data)

        # Update user activity and log usage
        try:
            db = await get_db()
            user_repo = UserRepo(db)
            usage_repo = UsageRepo(db)
            await user_repo.update_last_active(user.id)
            await usage_repo.log_event(
                telegram_id=user.id,
                event_type="message_received",
                chat_id=msg.chat_id,
                details=msg.text[:200],
            )

            # Store message for history search
            await db.execute(
                """INSERT INTO messages (telegram_id, chat_id, message_id, text, direction, timestamp)
                   VALUES (?, ?, ?, ?, 'incoming', ?)""",
                (user.id, msg.chat_id, msg.message_id, msg.text,
                 datetime.utcnow().isoformat()),
            )
            await db.commit()
        except Exception as e:
            logger.error("Failed to log message: %s", e)

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> dict[str, Any]:
        """Send a text message via the bot."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}

        try:
            msg = await self._bot.send_message(chat_id=chat_id, text=text, **kwargs)

            # Log outbound message
            try:
                db = await get_db()
                usage_repo = UsageRepo(db)
                await usage_repo.log_event(
                    telegram_id=0,
                    event_type="message_sent",
                    chat_id=chat_id,
                    details=text[:200],
                )
                await db.execute(
                    """INSERT INTO messages (telegram_id, chat_id, message_id, text, direction, timestamp)
                       VALUES (0, ?, ?, ?, 'outgoing', ?)""",
                    (chat_id, msg.message_id, text, datetime.utcnow().isoformat()),
                )
                await db.commit()
            except Exception as e:
                logger.error("Failed to log sent message: %s", e)

            return {
                "status": "sent",
                "message_id": msg.message_id,
                "chat_id": chat_id,
            }
        except Exception as e:
            return {"error": str(e)}

    async def send_photo(self, chat_id: int, photo: str, caption: str = "", **kwargs: Any) -> dict[str, Any]:
        """Send a photo via the bot."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}
        try:
            msg = await self._bot.send_photo(
                chat_id=chat_id, photo=photo, caption=caption or None, **kwargs
            )
            return {"status": "sent", "message_id": msg.message_id, "chat_id": chat_id}
        except Exception as e:
            return {"error": str(e)}

    async def send_document(self, chat_id: int, document: str, caption: str = "", **kwargs: Any) -> dict[str, Any]:
        """Send a document via the bot."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}
        try:
            msg = await self._bot.send_document(
                chat_id=chat_id, document=document, caption=caption or None, **kwargs
            )
            return {"status": "sent", "message_id": msg.message_id, "chat_id": chat_id}
        except Exception as e:
            return {"error": str(e)}

    async def get_chat_info(self, chat_id: int) -> dict[str, Any]:
        """Get information about a chat."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}
        try:
            chat = await self._bot.get_chat(chat_id)
            return {
                "id": chat.id,
                "type": chat.type,
                "title": chat.title,
                "username": chat.username,
                "first_name": chat.first_name,
                "last_name": chat.last_name,
                "description": chat.description,
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_me(self) -> dict[str, Any]:
        """Get bot info."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}
        try:
            me = await self._bot.get_me()
            return {
                "id": me.id,
                "is_bot": me.is_bot,
                "first_name": me.first_name,
                "username": me.username,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
                "supports_inline_queries": me.supports_inline_queries,
            }
        except Exception as e:
            return {"error": str(e)}

    async def set_commands(self, commands: list[dict[str, str]]) -> dict[str, Any]:
        """Register bot commands with Telegram."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}
        try:
            from telegram import BotCommand
            bot_commands = [
                BotCommand(command=c["command"], description=c["description"])
                for c in commands
            ]
            await self._bot.set_my_commands(bot_commands)
            return {"status": "commands_set", "count": len(bot_commands)}
        except Exception as e:
            return {"error": str(e)}

    async def reply_to_message(
        self, chat_id: int, message_id: int, text: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Reply to a specific message."""
        if not self._bot:
            return {"error": "Bot not running. Use bot_start first."}
        try:
            msg = await self._bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=message_id,
                **kwargs,
            )
            return {"status": "sent", "message_id": msg.message_id, "chat_id": chat_id}
        except Exception as e:
            return {"error": str(e)}


# Singleton
_manager: Optional[BotManager] = None


def get_bot_manager() -> BotManager:
    """Get or create the global BotManager instance."""
    global _manager
    if _manager is None:
        _manager = BotManager()
    return _manager
