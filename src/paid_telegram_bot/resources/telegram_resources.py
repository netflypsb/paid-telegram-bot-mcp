"""MCP Resources — read-only data endpoints for agents.

Resources provide structured data that agents can access without
calling tools. Free resources work without a license key.
"""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..license import is_licensed

logger = logging.getLogger(__name__)


def register_resources(mcp: FastMCP) -> None:
    """Register all MCP resources on the server."""

    @mcp.resource("telegram://bot/status")
    async def bot_status_resource() -> str:
        """Current bot status and configuration (Free tier)."""
        manager = get_bot_manager()
        return json.dumps(manager.get_status(), indent=2)

    @mcp.resource("telegram://messages/recent")
    async def recent_messages_resource() -> str:
        """Recent messages received by the bot — last 50 (Free tier)."""
        manager = get_bot_manager()
        messages = manager.recent_messages[-50:]
        return json.dumps({"count": len(messages), "messages": messages}, indent=2)

    @mcp.resource("telegram://users")
    async def users_resource() -> str:
        """List of all bot users (Pro tier)."""
        if not is_licensed():
            return json.dumps({"error": "Pro license required to access user data."})

        from ..database.database import get_db
        from ..database.user_repo import UserRepo
        db = await get_db()
        user_repo = UserRepo(db)
        users = await user_repo.list_all(limit=500)
        total = await user_repo.count()
        return json.dumps({"total": total, "users": users}, indent=2)

    @mcp.resource("telegram://plans")
    async def plans_resource() -> str:
        """Available subscription plans (Pro tier)."""
        if not is_licensed():
            return json.dumps({"error": "Pro license required to access plan data."})

        from ..database.database import get_db
        from ..database.plan_repo import PlanRepo
        db = await get_db()
        plan_repo = PlanRepo(db)
        plans = await plan_repo.list_all()
        return json.dumps({"plans": plans}, indent=2)

    @mcp.resource("telegram://analytics")
    async def analytics_resource() -> str:
        """Analytics dashboard data (Pro tier)."""
        if not is_licensed():
            return json.dumps({"error": "Pro license required to access analytics."})

        from ..database.database import get_db
        from ..database.user_repo import UserRepo
        from ..database.payment_repo import PaymentRepo
        from ..database.usage_repo import UsageRepo

        db = await get_db()
        user_repo = UserRepo(db)
        payment_repo = PaymentRepo(db)
        usage_repo = UsageRepo(db)

        return json.dumps({
            "users": {
                "total": await user_repo.count(),
                "free": await user_repo.count(role="free"),
                "subscribers": await user_repo.count(role="subscriber"),
                "blocked": await user_repo.count(role="blocked"),
            },
            "revenue": await payment_repo.get_revenue("monthly"),
            "messages_by_day": await usage_repo.get_messages_by_day(30),
        }, indent=2)

    @mcp.resource("telegram://security/events")
    async def security_events_resource() -> str:
        """Recent security events (Pro tier)."""
        if not is_licensed():
            return json.dumps({"error": "Pro license required to access security events."})

        from ..database.database import get_db
        from ..database.security_repo import SecurityRepo
        db = await get_db()
        security_repo = SecurityRepo(db)
        events = await security_repo.get_events(limit=50)
        return json.dumps({"events": events}, indent=2)

    @mcp.resource("telegram://invites")
    async def invites_resource() -> str:
        """Active invite codes (Pro tier)."""
        if not is_licensed():
            return json.dumps({"error": "Pro license required to access invite codes."})

        from ..database.database import get_db
        db = await get_db()
        invites = await db.fetchall(
            "SELECT * FROM invite_codes WHERE revoked = 0 ORDER BY created_at DESC"
        )
        return json.dumps({"invites": invites}, indent=2)
