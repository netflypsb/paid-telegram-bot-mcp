"""Priority message queue for outbound Telegram messages.

Supports high/normal/low priority with stale message cleanup.
Full integration with rate limiter in Phase 4.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


@dataclass(order=True)
class QueuedMessage:
    priority: int
    timestamp: float = field(compare=True)
    chat_id: int = field(compare=False, default=0)
    send_fn: Any = field(compare=False, default=None)  # async callable
    max_age_seconds: float = field(compare=False, default=300.0)

    @property
    def is_stale(self) -> bool:
        return (time.monotonic() - self.timestamp) > self.max_age_seconds


class MessageQueue:
    """Priority-based outbound message queue."""

    def __init__(self):
        self._queue: asyncio.PriorityQueue[QueuedMessage] = asyncio.PriorityQueue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._sent_count = 0
        self._dropped_count = 0

    @property
    def depth(self) -> int:
        return self._queue.qsize()

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "depth": self.depth,
            "running": self._running,
            "sent_count": self._sent_count,
            "dropped_count": self._dropped_count,
        }

    async def enqueue(
        self,
        send_fn: Callable[[], Coroutine],
        chat_id: int = 0,
        priority: Priority = Priority.NORMAL,
        max_age_seconds: float = 300.0,
    ) -> None:
        """Add a message to the queue."""
        msg = QueuedMessage(
            priority=priority.value,
            timestamp=time.monotonic(),
            chat_id=chat_id,
            send_fn=send_fn,
            max_age_seconds=max_age_seconds,
        )
        await self._queue.put(msg)

    async def start(self) -> None:
        """Start the queue worker."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Message queue started")

    async def stop(self) -> None:
        """Stop the queue worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Message queue stopped")

    async def _worker(self) -> None:
        """Process messages from the queue."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                if msg.is_stale:
                    self._dropped_count += 1
                    logger.debug("Dropped stale message for chat %d", msg.chat_id)
                    continue

                try:
                    await msg.send_fn()
                    self._sent_count += 1
                except Exception as e:
                    logger.error("Failed to send queued message: %s", e)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
