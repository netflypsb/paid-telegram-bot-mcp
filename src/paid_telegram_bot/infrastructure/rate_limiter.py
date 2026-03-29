"""Token bucket rate limiter for Telegram API calls.

Enforces:
- Global rate limit: 30 messages/second (Telegram's cap)
- Per-chat spacing: ~1 message/second
- 429 retry_after handling with automatic backoff

Full implementation in Phase 4. Currently provides pass-through.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Token bucket rate limiter for outbound Telegram messages."""

    def __init__(
        self,
        rate: float = 30.0,
        capacity: int = 30,
        per_chat_interval: float = 1.0,
    ):
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._per_chat_interval = per_chat_interval
        self._chat_last_sent: dict[int, float] = {}
        self._paused_until: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self, chat_id: int = 0) -> None:
        """Wait until a token is available, then consume one."""
        async with self._lock:
            now = time.monotonic()

            # Handle 429 pause
            if now < self._paused_until:
                wait = self._paused_until - now
                logger.warning("Rate limiter paused for %.1fs (429 backoff)", wait)
                await asyncio.sleep(wait)
                now = time.monotonic()

            # Refill tokens
            elapsed = now - self._last_refill
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._last_refill = now

            # Wait for token
            while self._tokens < 1.0:
                wait = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
                self._last_refill = now

            # Per-chat spacing
            if chat_id and chat_id in self._chat_last_sent:
                since_last = now - self._chat_last_sent[chat_id]
                if since_last < self._per_chat_interval:
                    await asyncio.sleep(self._per_chat_interval - since_last)

            # Consume token
            self._tokens -= 1.0
            if chat_id:
                self._chat_last_sent[chat_id] = time.monotonic()

    def pause_for(self, seconds: float) -> None:
        """Pause the rate limiter (called when a 429 is received)."""
        self._paused_until = time.monotonic() + seconds
        logger.warning("Rate limiter paused for %.1fs due to 429", seconds)

    @property
    def available_tokens(self) -> float:
        """Current available tokens (approximate)."""
        elapsed = time.monotonic() - self._last_refill
        return min(self._capacity, self._tokens + elapsed * self._rate)
