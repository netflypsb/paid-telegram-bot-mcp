"""Tests for the bot manager — lifecycle and status."""

import pytest

from paid_telegram_bot.bot.bot_manager import BotManager


def test_initial_status():
    manager = BotManager()
    status = manager.get_status()
    assert status["running"] is False
    assert status["bot_info"] is None
    assert status["started_at"] is None
    assert status["uptime"] is None
    assert status["recent_messages_count"] == 0


def test_is_running_initially_false():
    manager = BotManager()
    assert manager.is_running is False


def test_bot_initially_none():
    manager = BotManager()
    assert manager.bot is None


def test_recent_messages_initially_empty():
    manager = BotManager()
    assert manager.recent_messages == []


@pytest.mark.asyncio
async def test_stop_when_not_running():
    manager = BotManager()
    result = await manager.stop()
    assert result["status"] == "not_running"


@pytest.mark.asyncio
async def test_start_without_token():
    manager = BotManager()
    # Patch config to return empty token
    from unittest.mock import patch, MagicMock
    mock_config = MagicMock()
    mock_config.bot.token = ""
    with patch("paid_telegram_bot.bot.bot_manager.get_config", return_value=mock_config):
        result = await manager.start()
    assert result["status"] == "error"
    assert "No bot token" in result["message"]


@pytest.mark.asyncio
async def test_send_message_when_not_running():
    manager = BotManager()
    result = await manager.send_message(12345, "Hello")
    assert "error" in result


@pytest.mark.asyncio
async def test_get_me_when_not_running():
    manager = BotManager()
    result = await manager.get_me()
    assert "error" in result


@pytest.mark.asyncio
async def test_get_chat_info_when_not_running():
    manager = BotManager()
    result = await manager.get_chat_info(12345)
    assert "error" in result
