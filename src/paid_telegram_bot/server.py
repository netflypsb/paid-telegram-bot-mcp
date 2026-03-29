"""FastMCP server definition — wires together all tools, resources, and prompts.

This is the main entry point that creates the MCP server instance and
registers all components. Supports stdio transport (default) for
maximum MCP client compatibility.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from mcp.server.fastmcp import FastMCP

from .config import get_config
from .database.database import get_db, close_db

logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the FastMCP server with all tools, resources, and prompts."""

    mcp = FastMCP(
        "paid-telegram-bot",
        description=(
            "Enterprise Telegram bot management for any AI agent. "
            "40+ tools for bot lifecycle, user management, payments, "
            "analytics, deep links, and more. "
            "Free tier: 12 basic tools. Pro tier: all 40+ tools with license key."
        ),
    )

    # --- Register Free Tier Tools (12 tools, no license required) ---
    from .tools.free_tools import register_free_tools
    register_free_tools(mcp)

    # --- Register Pro Tier Tools (license required) ---
    from .tools.user_tools import register_user_tools
    from .tools.plan_tools import register_plan_tools
    from .tools.payment_tools import register_payment_tools
    from .tools.analytics_tools import register_analytics_tools
    from .tools.deeplink_tools import register_deeplink_tools
    from .tools.media_tools import register_media_tools
    from .tools.group_tools import register_group_tools
    from .tools.event_tools import register_event_tools
    from .tools.queue_tools import register_queue_tools

    register_user_tools(mcp)
    register_plan_tools(mcp)
    register_payment_tools(mcp)
    register_analytics_tools(mcp)
    register_deeplink_tools(mcp)
    register_media_tools(mcp)
    register_group_tools(mcp)
    register_event_tools(mcp)
    register_queue_tools(mcp)

    # --- Register MCP Resources ---
    from .resources.telegram_resources import register_resources
    register_resources(mcp)

    # --- Register MCP Prompts ---
    from .prompts.setup_prompts import register_prompts
    register_prompts(mcp)

    return mcp


async def _initialize() -> None:
    """Initialize server dependencies (database, config)."""
    config = get_config()
    config.ensure_dirs()
    await get_db()
    logger.info(
        "Server initialized. Data dir: %s | License: checking on first Pro tool call",
        config.data_dir,
    )


async def _shutdown() -> None:
    """Clean shutdown of server dependencies."""
    from .bot.bot_manager import get_bot_manager

    manager = get_bot_manager()
    if manager.is_running:
        logger.info("Stopping bot before shutdown...")
        await manager.stop()

    await close_db()
    logger.info("Server shut down cleanly.")


def run_server() -> None:
    """Run the MCP server with stdio transport."""
    # Configure logging — MCP uses stdout for protocol, logs go to stderr
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    logger.info("Starting Paid Telegram Bot MCP Server...")

    # Ensure config dirs exist synchronously before the event loop starts
    config = get_config()
    config.ensure_dirs()

    mcp = create_server()

    # The FastMCP.run() manages its own event loop.
    # Database initialization happens lazily on first tool call via get_db().
    # Bot shutdown is handled by the bot_stop tool or process exit.
    mcp.run(transport="stdio")
