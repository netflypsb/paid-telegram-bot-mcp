"""Tests for the token bucket rate limiter."""

import asyncio
import time

import pytest

from paid_telegram_bot.infrastructure.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_acquire_does_not_block_when_tokens_available():
    limiter = TokenBucketRateLimiter(rate=30.0, capacity=30)
    start = time.monotonic()
    await limiter.acquire(chat_id=1)
    elapsed = time.monotonic() - start
    assert elapsed < 0.1  # Should be near-instant


@pytest.mark.asyncio
async def test_available_tokens_decrements():
    limiter = TokenBucketRateLimiter(rate=30.0, capacity=5)
    initial = limiter.available_tokens
    await limiter.acquire(chat_id=1)
    after = limiter.available_tokens
    assert after < initial


@pytest.mark.asyncio
async def test_pause_for_causes_delay():
    limiter = TokenBucketRateLimiter(rate=100.0, capacity=100)
    limiter.pause_for(0.2)  # Pause for 200ms
    start = time.monotonic()
    await limiter.acquire(chat_id=1)
    elapsed = time.monotonic() - start
    assert elapsed >= 0.15  # Should have waited at least ~200ms


@pytest.mark.asyncio
async def test_per_chat_spacing():
    limiter = TokenBucketRateLimiter(
        rate=100.0, capacity=100, per_chat_interval=0.2
    )
    await limiter.acquire(chat_id=42)
    start = time.monotonic()
    await limiter.acquire(chat_id=42)
    elapsed = time.monotonic() - start
    assert elapsed >= 0.15  # Should wait ~200ms between same-chat messages


@pytest.mark.asyncio
async def test_different_chats_no_spacing():
    limiter = TokenBucketRateLimiter(
        rate=100.0, capacity=100, per_chat_interval=0.5
    )
    await limiter.acquire(chat_id=1)
    start = time.monotonic()
    await limiter.acquire(chat_id=2)  # Different chat — no spacing
    elapsed = time.monotonic() - start
    assert elapsed < 0.1
