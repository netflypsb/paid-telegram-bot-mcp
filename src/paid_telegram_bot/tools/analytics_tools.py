"""Pro-tier Analytics & Admin tools (license required)."""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..database.database import get_db
from ..database.user_repo import UserRepo
from ..database.usage_repo import UsageRepo
from ..database.payment_repo import PaymentRepo
from ..database.security_repo import SecurityRepo
from ..license import require_license

logger = logging.getLogger(__name__)


def register_analytics_tools(mcp: FastMCP) -> None:
    """Register all analytics and admin tools on the MCP server."""

    @mcp.tool()
    async def analytics_dashboard() -> str:
        """Get the full analytics dashboard: users, revenue, messages, and trends."""
        err = require_license("analytics_dashboard")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)
        usage_repo = UsageRepo(db)
        payment_repo = PaymentRepo(db)

        total_users = await user_repo.count()
        free_users = await user_repo.count(role="free")
        subscribers = await user_repo.count(role="subscriber")
        blocked_users = await user_repo.count(role="blocked")

        monthly_revenue = await payment_repo.get_revenue("monthly")
        all_time_revenue = await payment_repo.get_revenue("all_time")
        messages_by_day = await usage_repo.get_messages_by_day(days=30)

        return json.dumps({
            "users": {
                "total": total_users,
                "free": free_users,
                "subscribers": subscribers,
                "blocked": blocked_users,
            },
            "revenue": {
                "monthly": monthly_revenue,
                "all_time": all_time_revenue,
            },
            "messages_by_day": messages_by_day,
        }, indent=2)

    @mcp.tool()
    async def analytics_usage(telegram_id: int) -> str:
        """Get per-user usage statistics.

        Args:
            telegram_id: The Telegram user ID to get stats for
        """
        err = require_license("analytics_usage")
        if err:
            return err

        db = await get_db()
        usage_repo = UsageRepo(db)
        stats = await usage_repo.get_user_stats(telegram_id)
        return json.dumps(stats, indent=2)

    @mcp.tool()
    async def broadcast_message(text: str, parse_mode: str = "HTML") -> str:
        """Send a message to ALL bot users. Use with care.

        Args:
            text: The message text to broadcast
            parse_mode: Parse mode - 'HTML' or 'Markdown' (default 'HTML')
        """
        err = require_license("broadcast_message")
        if err:
            return err

        manager = get_bot_manager()
        if not manager.bot:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        db = await get_db()
        user_repo = UserRepo(db)
        users = await user_repo.list_all(limit=10000)

        sent = 0
        failed = 0
        for user in users:
            if user["role"] == "blocked":
                continue
            try:
                await manager.bot.send_message(
                    chat_id=user["telegram_id"],
                    text=text,
                    parse_mode=parse_mode,
                )
                sent += 1
            except Exception:
                failed += 1

        return json.dumps({
            "status": "broadcast_complete",
            "sent": sent,
            "failed": failed,
            "total_users": len(users),
        }, indent=2)

    @mcp.tool()
    async def security_log(limit: int = 50) -> str:
        """View recent security events.

        Args:
            limit: Maximum number of events to return (default 50)
        """
        err = require_license("security_log")
        if err:
            return err

        db = await get_db()
        security_repo = SecurityRepo(db)
        events = await security_repo.get_events(limit=limit)
        return json.dumps({"count": len(events), "events": events}, indent=2)

    @mcp.tool()
    async def security_get_events(
        event_type: str = "",
        severity: str = "",
        telegram_id: int = 0,
        limit: int = 50,
    ) -> str:
        """Query security events with filters.

        Args:
            event_type: Filter by type - 'login', 'block', 'unblock', 'rate_limit', 'suspicious', 'invite_created', 'invite_revoked'
            severity: Filter by severity - 'info', 'warning', 'critical'
            telegram_id: Filter by Telegram user ID (0 for all)
            limit: Maximum number of events to return
        """
        err = require_license("security_get_events")
        if err:
            return err

        db = await get_db()
        security_repo = SecurityRepo(db)
        events = await security_repo.get_events(
            event_type=event_type or None,
            severity=severity or None,
            telegram_id=telegram_id or None,
            limit=limit,
        )
        return json.dumps({"count": len(events), "events": events}, indent=2)
