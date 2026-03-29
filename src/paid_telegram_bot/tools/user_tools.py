"""Pro-tier User & Access Management tools (license required)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from ..database.database import get_db
from ..database.user_repo import UserRepo
from ..database.security_repo import SecurityRepo
from ..license import require_license
from ..config import get_config

logger = logging.getLogger(__name__)


def register_user_tools(mcp: FastMCP) -> None:
    """Register all user management tools on the MCP server."""

    @mcp.tool()
    async def user_list(
        role: str = "",
        plan_id: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> str:
        """List all bot users with optional filters.

        Args:
            role: Filter by role - 'owner', 'subscriber', 'free', or 'blocked'
            plan_id: Filter by subscription plan ID
            limit: Maximum number of users to return (default 100)
            offset: Offset for pagination
        """
        err = require_license("user_list")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)
        users = await user_repo.list_all(
            role=role or None,
            plan_id=plan_id or None,
            limit=limit,
            offset=offset,
        )
        total = await user_repo.count(role=role or None)
        return json.dumps({
            "total": total,
            "count": len(users),
            "offset": offset,
            "users": users,
        }, indent=2)

    @mcp.tool()
    async def user_get(telegram_id: int) -> str:
        """Get detailed information for a specific bot user.

        Args:
            telegram_id: The Telegram user ID
        """
        err = require_license("user_get")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)
        user = await user_repo.get(telegram_id)
        if not user:
            return json.dumps({"error": "User not found", "telegram_id": telegram_id})
        return json.dumps(user, indent=2)

    @mcp.tool()
    async def user_block(telegram_id: int, reason: str = "") -> str:
        """Block a user from using the bot.

        Args:
            telegram_id: The Telegram user ID to block
            reason: Optional reason for blocking
        """
        err = require_license("user_block")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)
        security_repo = SecurityRepo(db)

        success = await user_repo.block(telegram_id)
        if success:
            await security_repo.log_event(
                event_type="block",
                telegram_id=telegram_id,
                severity="warning",
                details=f"User blocked. Reason: {reason or 'not specified'}",
            )
            return json.dumps({"status": "blocked", "telegram_id": telegram_id})
        return json.dumps({"error": "User not found", "telegram_id": telegram_id})

    @mcp.tool()
    async def user_unblock(telegram_id: int) -> str:
        """Unblock a previously blocked user.

        Args:
            telegram_id: The Telegram user ID to unblock
        """
        err = require_license("user_unblock")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)
        security_repo = SecurityRepo(db)

        success = await user_repo.unblock(telegram_id)
        if success:
            await security_repo.log_event(
                event_type="unblock",
                telegram_id=telegram_id,
                severity="info",
                details="User unblocked",
            )
            return json.dumps({"status": "unblocked", "telegram_id": telegram_id})
        return json.dumps({"error": "User not found", "telegram_id": telegram_id})

    @mcp.tool()
    async def user_update_tier(
        telegram_id: int,
        plan_id: str,
        expires_at: str = "",
    ) -> str:
        """Change a user's subscription tier/plan.

        Args:
            telegram_id: The Telegram user ID
            plan_id: The plan ID to assign (e.g. 'free', 'basic', 'pro', 'enterprise')
            expires_at: Optional ISO datetime when the subscription expires
        """
        err = require_license("user_update_tier")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)

        success = await user_repo.update_plan(
            telegram_id, plan_id, expires_at or None
        )
        if success:
            role = "subscriber" if plan_id != "free" else "free"
            await user_repo.update_role(telegram_id, role)
            return json.dumps({
                "status": "updated",
                "telegram_id": telegram_id,
                "plan_id": plan_id,
                "role": role,
            })
        return json.dumps({"error": "User not found", "telegram_id": telegram_id})

    @mcp.tool()
    async def access_set_mode(mode: str) -> str:
        """Set the bot's access control mode.

        Args:
            mode: Access mode - 'open' (anyone can use), 'whitelist' (only authorized users), or 'approval' (users must be approved)
        """
        err = require_license("access_set_mode")
        if err:
            return err

        if mode not in ("open", "whitelist", "approval"):
            return json.dumps({"error": "Invalid mode. Must be 'open', 'whitelist', or 'approval'."})

        config = get_config()
        config.bot.access_mode = mode
        config.save()
        return json.dumps({"status": "access_mode_set", "mode": mode})

    @mcp.tool()
    async def access_add_user(telegram_id: int) -> str:
        """Manually authorize a user (for whitelist/approval mode).

        Args:
            telegram_id: The Telegram user ID to authorize
        """
        err = require_license("access_add_user")
        if err:
            return err

        db = await get_db()
        user_repo = UserRepo(db)
        user = await user_repo.get(telegram_id)
        if not user:
            return json.dumps({"error": "User not found. They must /start the bot first."})

        await db.execute(
            "UPDATE users SET is_approved = 1 WHERE telegram_id = ?",
            (telegram_id,),
        )
        await db.commit()
        return json.dumps({"status": "authorized", "telegram_id": telegram_id})

    @mcp.tool()
    async def access_remove_user(telegram_id: int) -> str:
        """Remove a user's authorization (for whitelist/approval mode).

        Args:
            telegram_id: The Telegram user ID to de-authorize
        """
        err = require_license("access_remove_user")
        if err:
            return err

        db = await get_db()
        await db.execute(
            "UPDATE users SET is_approved = 0 WHERE telegram_id = ?",
            (telegram_id,),
        )
        await db.commit()
        return json.dumps({"status": "authorization_removed", "telegram_id": telegram_id})
