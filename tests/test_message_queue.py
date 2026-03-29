"""Tests for the priority message queue."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from paid_telegram_bot.infrastructure.message_queue import (
    MessageQueue,
    Priority,
)


@pytest.mark.asyncio
async def test_enqueue_and_stats():
    queue = MessageQueue()
    send_fn = AsyncMock()
    await queue.enqueue(send_fn, chat_id=1, priority=Priority.NORMAL)
    assert queue.depth == 1
    assert queue.stats["depth"] == 1


@pytest.mark.asyncio
async def test_worker_processes_messages():
    queue = MessageQueue()
    send_fn = AsyncMock()
    await queue.enqueue(send_fn, chat_id=1, priority=Priority.NORMAL)
    await queue.start()
    await asyncio.sleep(0.2)  # Give worker time to process
    await queue.stop()
    send_fn.assert_called_once()
    assert queue.stats["sent_count"] == 1


@pytest.mark.asyncio
async def test_priority_ordering():
    """Higher priority messages should be processed first."""
    queue = MessageQueue()
    order = []

    async def make_fn(label):
        async def fn():
            order.append(label)
        return fn

    # Enqueue low, then high — high should come first
    await queue.enqueue(await make_fn("low"), chat_id=1, priority=Priority.LOW)
    await queue.enqueue(await make_fn("high"), chat_id=1, priority=Priority.HIGH)
    await queue.enqueue(await make_fn("normal"), chat_id=1, priority=Priority.NORMAL)

    await queue.start()
    await asyncio.sleep(0.3)
    await queue.stop()

    # High (0) < Normal (1) < Low (2) in priority queue
    assert order[0] == "high"
    assert order[1] == "normal"
    assert order[2] == "low"


@pytest.mark.asyncio
async def test_stale_messages_dropped():
    queue = MessageQueue()
    send_fn = AsyncMock()
    await queue.enqueue(
        send_fn, chat_id=1, priority=Priority.NORMAL, max_age_seconds=0.0
    )
    await asyncio.sleep(0.05)  # Let it go stale
    await queue.start()
    await asyncio.sleep(0.2)
    await queue.stop()
    send_fn.assert_not_called()
    assert queue.stats["dropped_count"] == 1
