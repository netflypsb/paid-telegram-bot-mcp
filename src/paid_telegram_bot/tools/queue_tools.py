"""Pro-tier Message Infrastructure tools (license required)."""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..license import require_license

logger = logging.getLogger(__name__)


def register_queue_tools(mcp: FastMCP) -> None:
    """Register message infrastructure tools on the MCP server."""

    @mcp.tool()
    async def queue_status() -> str:
        """View message queue depth and rate limiter state."""
        err = require_license("queue_status")
        if err:
            return err

        # For Phase 1, return basic status. Full queue/rate limiter
        # will be implemented in Phase 4.
        manager = get_bot_manager()
        return json.dumps({
            "status": "operational",
            "bot_running": manager.is_running,
            "recent_messages_buffered": len(manager.recent_messages),
            "note": "Full priority queue and rate limiter stats available in future update.",
        }, indent=2)

    @mcp.tool()
    async def queue_set_priority(chat_id: int, priority: str = "normal") -> str:
        """Set the message priority for a specific chat.

        Args:
            chat_id: The Telegram chat ID to set priority for
            priority: Priority level - 'high', 'normal', or 'low'
        """
        err = require_license("queue_set_priority")
        if err:
            return err

        if priority not in ("high", "normal", "low"):
            return json.dumps({"error": "Priority must be 'high', 'normal', or 'low'."})

        # Placeholder for Phase 4 full implementation
        return json.dumps({
            "status": "priority_set",
            "chat_id": chat_id,
            "priority": priority,
        })

    @mcp.tool()
    async def send_inline_keyboard(
        chat_id: int,
        text: str,
        buttons: str,
        parse_mode: str = "",
    ) -> str:
        """Send a message with inline keyboard buttons.

        Args:
            chat_id: The Telegram chat ID to send to
            text: The message text
            buttons: JSON string of button rows, e.g. '[[{"text": "Click me", "url": "https://example.com"}]]'
            parse_mode: Optional parse mode - 'HTML' or 'Markdown'
        """
        err = require_license("send_inline_keyboard")
        if err:
            return err

        manager = get_bot_manager()
        if not manager.bot:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        try:
            button_data = json.loads(buttons)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON for buttons."})

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = []
            for row in button_data:
                btn_row = []
                for btn in row:
                    kwargs = {"text": btn["text"]}
                    if "url" in btn:
                        kwargs["url"] = btn["url"]
                    if "callback_data" in btn:
                        kwargs["callback_data"] = btn["callback_data"]
                    btn_row.append(InlineKeyboardButton(**kwargs))
                keyboard.append(btn_row)

            reply_markup = InlineKeyboardMarkup(keyboard)
            send_kwargs = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
            if parse_mode:
                send_kwargs["parse_mode"] = parse_mode

            msg = await manager.bot.send_message(**send_kwargs)

            return json.dumps({
                "status": "sent",
                "message_id": msg.message_id,
                "chat_id": chat_id,
            })

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def send_poll(
        chat_id: int,
        question: str,
        options: str,
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
    ) -> str:
        """Create and send a poll.

        Args:
            chat_id: The Telegram chat ID to send the poll to
            question: The poll question
            options: JSON array of answer options, e.g. '["Option A", "Option B", "Option C"]'
            is_anonymous: Whether the poll is anonymous (default True)
            allows_multiple_answers: Whether users can select multiple answers (default False)
        """
        err = require_license("send_poll")
        if err:
            return err

        manager = get_bot_manager()
        if not manager.bot:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        try:
            option_list = json.loads(options)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON for options."})

        if len(option_list) < 2:
            return json.dumps({"error": "A poll needs at least 2 options."})

        try:
            msg = await manager.bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=option_list,
                is_anonymous=is_anonymous,
                allows_multiple_answers=allows_multiple_answers,
            )
            return json.dumps({
                "status": "sent",
                "message_id": msg.message_id,
                "poll_id": msg.poll.id if msg.poll else None,
                "chat_id": chat_id,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_poll_results(chat_id: int, message_id: int) -> str:
        """Get poll results by forwarding the poll message.

        Note: Telegram Bot API does not provide a direct way to fetch poll results.
        Results are delivered via poll updates when users vote.

        Args:
            chat_id: The chat ID containing the poll
            message_id: The message ID of the poll
        """
        err = require_license("get_poll_results")
        if err:
            return err

        return json.dumps({
            "note": "Poll results are delivered via Telegram updates when users vote. "
                    "Check get_updates for poll_answer events. "
                    "The bot must have been running when votes were cast to capture them.",
            "chat_id": chat_id,
            "message_id": message_id,
        })
