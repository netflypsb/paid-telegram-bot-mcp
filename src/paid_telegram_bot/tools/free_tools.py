"""Free-tier MCP tools — 12 basic tools available without a license key.

Free tier limits: 1 bot, no multi-user management, no payments, no analytics,
max 50 messages/hour outbound.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..config import get_config
from ..database.database import get_db
from ..database.usage_repo import UsageRepo

logger = logging.getLogger(__name__)


def register_free_tools(mcp: FastMCP) -> None:
    """Register all free-tier tools on the MCP server."""

    @mcp.tool()
    async def bot_configure(
        token: str,
        welcome_message: str = "",
        access_mode: str = "",
    ) -> str:
        """Configure the Telegram bot with a token and optional settings.

        Args:
            token: Telegram bot token from @BotFather (required)
            welcome_message: Custom welcome message for /start command
            access_mode: Access mode - 'open', 'whitelist', or 'approval'
        """
        manager = get_bot_manager()
        kwargs: dict[str, Any] = {}
        if welcome_message:
            kwargs["welcome_message"] = welcome_message
        if access_mode:
            kwargs["access_mode"] = access_mode
        result = await manager.configure(token, **kwargs)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def bot_start() -> str:
        """Start the Telegram bot with long-polling.

        The bot must be configured with bot_configure first.
        Once started, the bot will receive and process messages in the background.
        """
        manager = get_bot_manager()
        result = await manager.start()
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def bot_stop() -> str:
        """Stop the running Telegram bot.

        Gracefully shuts down the bot and stops receiving messages.
        """
        manager = get_bot_manager()
        result = await manager.stop()
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def bot_status() -> str:
        """Get the current bot status including running state, username, and uptime."""
        manager = get_bot_manager()
        result = manager.get_status()
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def send_message(
        chat_id: int,
        text: str,
        parse_mode: str = "",
    ) -> str:
        """Send a text message to a Telegram chat.

        Args:
            chat_id: The Telegram chat ID to send the message to
            text: The message text to send (supports HTML formatting if parse_mode is 'HTML')
            parse_mode: Optional parse mode - 'HTML' or 'Markdown'
        """
        # Check free tier rate limit
        err = await _check_free_rate_limit()
        if err:
            return err

        manager = get_bot_manager()
        kwargs: dict[str, Any] = {}
        if parse_mode:
            kwargs["parse_mode"] = parse_mode
        result = await manager.send_message(chat_id, text, **kwargs)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def send_photo(
        chat_id: int,
        photo: str,
        caption: str = "",
    ) -> str:
        """Send a photo to a Telegram chat.

        Args:
            chat_id: The Telegram chat ID to send the photo to
            photo: URL of the photo or file_id from a previous message
            caption: Optional caption for the photo
        """
        err = await _check_free_rate_limit()
        if err:
            return err

        manager = get_bot_manager()
        result = await manager.send_photo(chat_id, photo, caption)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def send_document(
        chat_id: int,
        document: str,
        caption: str = "",
    ) -> str:
        """Send a document/file to a Telegram chat.

        Args:
            chat_id: The Telegram chat ID to send the document to
            document: URL of the document or file_id from a previous message
            caption: Optional caption for the document
        """
        err = await _check_free_rate_limit()
        if err:
            return err

        manager = get_bot_manager()
        result = await manager.send_document(chat_id, document, caption)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def get_updates(limit: int = 50) -> str:
        """Get recent incoming messages received by the bot.

        Args:
            limit: Maximum number of recent messages to return (default 50, max 200)
        """
        manager = get_bot_manager()
        if not manager.is_running:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        messages = manager.recent_messages
        if limit:
            messages = messages[-min(limit, 200):]
        return json.dumps({"count": len(messages), "messages": messages}, indent=2)

    @mcp.tool()
    async def get_chat_info(chat_id: int) -> str:
        """Get information about a Telegram chat or group.

        Args:
            chat_id: The Telegram chat ID to get info for
        """
        manager = get_bot_manager()
        result = await manager.get_chat_info(chat_id)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def set_commands(commands: str) -> str:
        """Register bot commands with Telegram (shown in the bot's command menu).

        Args:
            commands: JSON string of commands array, e.g. '[{"command": "start", "description": "Start the bot"}]'
        """
        manager = get_bot_manager()
        try:
            cmd_list = json.loads(commands)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON. Provide a JSON array of {command, description} objects."})

        result = await manager.set_commands(cmd_list)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def reply_to_message(
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = "",
    ) -> str:
        """Reply to a specific message in a Telegram chat.

        Args:
            chat_id: The Telegram chat ID
            message_id: The message ID to reply to
            text: The reply text
            parse_mode: Optional parse mode - 'HTML' or 'Markdown'
        """
        err = await _check_free_rate_limit()
        if err:
            return err

        manager = get_bot_manager()
        kwargs: dict[str, Any] = {}
        if parse_mode:
            kwargs["parse_mode"] = parse_mode
        result = await manager.reply_to_message(chat_id, message_id, text, **kwargs)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def get_me() -> str:
        """Get information about the bot itself (username, name, capabilities)."""
        manager = get_bot_manager()
        result = await manager.get_me()
        return json.dumps(result, indent=2)


async def _check_free_rate_limit() -> str | None:
    """Check if the free tier hourly rate limit has been exceeded.

    Returns an error JSON string if limit exceeded, None otherwise.
    """
    from ..license import is_licensed
    if is_licensed():
        return None

    try:
        config = get_config()
        db = await get_db()
        usage_repo = UsageRepo(db)
        hourly_count = await usage_repo.get_hourly_outbound_count()
        if hourly_count >= config.bot.max_outbound_per_hour_free:
            return json.dumps({
                "error": "rate_limit_exceeded",
                "message": (
                    f"Free tier limit: {config.bot.max_outbound_per_hour_free} "
                    f"outbound messages/hour. You've sent {hourly_count}. "
                    "Upgrade to Pro for unlimited messaging: "
                    "https://mcp-marketplace.io/servers/paid-telegram-bot"
                ),
            })
    except Exception as e:
        logger.warning("Rate limit check failed: %s", e)

    return None
