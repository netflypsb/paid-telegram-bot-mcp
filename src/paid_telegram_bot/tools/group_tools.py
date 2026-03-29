"""Pro-tier Group mode tools (license required)."""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..config import get_config
from ..license import require_license

logger = logging.getLogger(__name__)


def register_group_tools(mcp: FastMCP) -> None:
    """Register all group mode tools on the MCP server."""

    @mcp.tool()
    async def group_configure(
        enabled: bool = True,
        activation: str = "mention",
    ) -> str:
        """Configure group chat mode for the bot.

        Args:
            enabled: Whether group mode is enabled (default True)
            activation: How to activate the bot in groups - 'mention' (@ the bot) or 'command' (/ commands only)
        """
        err = require_license("group_configure")
        if err:
            return err

        if activation not in ("mention", "command"):
            return json.dumps({"error": "activation must be 'mention' or 'command'."})

        config = get_config()
        config.bot.group_mode = enabled
        config.bot.group_activation = activation
        config.save()

        return json.dumps({
            "status": "group_mode_configured",
            "enabled": enabled,
            "activation": activation,
        })

    @mcp.tool()
    async def group_list() -> str:
        """List all groups the bot is currently active in."""
        err = require_license("group_list")
        if err:
            return err

        from ..database.database import get_db
        db = await get_db()

        # Find unique group chats from messages
        groups = await db.fetchall(
            """SELECT DISTINCT chat_id, MAX(timestamp) as last_active
               FROM messages
               WHERE chat_id < 0
               GROUP BY chat_id
               ORDER BY last_active DESC
               LIMIT 100"""
        )

        # Try to enrich with chat info
        manager = get_bot_manager()
        enriched = []
        for g in groups:
            info = {"chat_id": g["chat_id"], "last_active": g["last_active"]}
            if manager.bot:
                try:
                    chat = await manager.bot.get_chat(g["chat_id"])
                    info["title"] = chat.title
                    info["type"] = chat.type
                    info["member_count"] = getattr(chat, "member_count", None)
                except Exception:
                    pass
            enriched.append(info)

        return json.dumps({"count": len(enriched), "groups": enriched}, indent=2)
