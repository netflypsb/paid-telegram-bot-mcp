"""Typing indicator and emoji reaction lifecycle.

Provides continuous typing indicator while processing,
and emoji reaction lifecycle: received → thinking → working → done/error.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from telegram import Bot

logger = logging.getLogger(__name__)


class TypingIndicator:
    """Manages the typing indicator for a chat."""

    def __init__(self, bot: Bot, chat_id: int, interval: float = 4.0):
        self._bot = bot
        self._chat_id = chat_id
        self._interval = interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start sending typing action periodically."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the typing indicator."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        """Periodically send typing action."""
        while self._running:
            try:
                await self._bot.send_chat_action(
                    chat_id=self._chat_id, action="typing"
                )
            except Exception as e:
                logger.debug("Typing indicator error: %s", e)
            await asyncio.sleep(self._interval)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()


class ReactionLifecycle:
    """Emoji reaction lifecycle for message processing.

    Stages: received (👀) → thinking (🤔) → working (⚙️) → done (✅) / error (❌)
    """

    RECEIVED = "👀"
    THINKING = "🤔"
    WORKING = "⚙️"
    DONE = "✅"
    ERROR = "❌"

    def __init__(self, bot: Bot, chat_id: int, message_id: int):
        self._bot = bot
        self._chat_id = chat_id
        self._message_id = message_id

    async def set_reaction(self, emoji: str) -> None:
        """Set the reaction emoji on the message."""
        try:
            await self._bot.set_message_reaction(
                chat_id=self._chat_id,
                message_id=self._message_id,
                reaction=[{"type": "emoji", "emoji": emoji}],
            )
        except Exception as e:
            logger.debug("Failed to set reaction %s: %s", emoji, e)

    async def received(self) -> None:
        await self.set_reaction(self.RECEIVED)

    async def thinking(self) -> None:
        await self.set_reaction(self.THINKING)

    async def working(self) -> None:
        await self.set_reaction(self.WORKING)

    async def done(self) -> None:
        await self.set_reaction(self.DONE)

    async def error(self) -> None:
        await self.set_reaction(self.ERROR)
