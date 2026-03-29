"""AI request concurrency queue with position notifications.

Controls how many concurrent LLM requests the bot processes,
with FIFO queuing and timeout handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RequestQueue:
    """Concurrency-controlled queue for AI/LLM requests."""

    def __init__(self, max_concurrent: int = 3, timeout: float = 120.0):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent
        self._timeout = timeout
        self._waiting: list[int] = []  # telegram_ids waiting
        self._active_count = 0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "max_concurrent": self._max_concurrent,
            "active": self._active_count,
            "waiting": len(self._waiting),
            "timeout": self._timeout,
        }

    async def acquire(self, telegram_id: int = 0) -> int:
        """Acquire a slot. Returns the queue position (0 = immediately acquired)."""
        self._waiting.append(telegram_id)
        position = len(self._waiting)

        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self._timeout)
        except asyncio.TimeoutError:
            if telegram_id in self._waiting:
                self._waiting.remove(telegram_id)
            raise

        if telegram_id in self._waiting:
            self._waiting.remove(telegram_id)
        self._active_count += 1
        return 0

    def release(self) -> None:
        """Release a slot."""
        self._active_count = max(0, self._active_count - 1)
        self._semaphore.release()

    def get_position(self, telegram_id: int) -> int:
        """Get the current queue position for a user (1-based, 0 = not waiting)."""
        try:
            return self._waiting.index(telegram_id) + 1
        except ValueError:
            return 0
