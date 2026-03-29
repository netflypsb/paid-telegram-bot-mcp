"""Pro-tier Deep Links & Onboarding tools (license required)."""

from __future__ import annotations

import json
import logging
import secrets
import string
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from ..database.database import get_db
from ..database.security_repo import SecurityRepo
from ..license import require_license

logger = logging.getLogger(__name__)


def _generate_code(length: int = 8) -> str:
    """Generate a random invite code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def register_deeplink_tools(mcp: FastMCP) -> None:
    """Register all deep link tools on the MCP server."""

    @mcp.tool()
    async def deeplink_create_invite(
        plan_id: str = "",
        max_uses: int = 0,
        expires_in_days: int = 0,
    ) -> str:
        """Generate an invite link with optional plan assignment, max uses, and expiry.

        Args:
            plan_id: Plan to assign to users who use this invite (empty for default free)
            max_uses: Maximum number of times the invite can be used (0 = unlimited)
            expires_in_days: Number of days until the invite expires (0 = never)
        """
        err = require_license("deeplink_create_invite")
        if err:
            return err

        code = _generate_code()
        now = datetime.utcnow()
        expires_at = None
        if expires_in_days > 0:
            from datetime import timedelta
            expires_at = (now + timedelta(days=expires_in_days)).isoformat()

        db = await get_db()
        await db.execute(
            """INSERT INTO invite_codes (code, plan_id, created_by, max_uses, used_count,
                                         expires_at, revoked, created_at)
               VALUES (?, ?, 0, ?, 0, ?, 0, ?)""",
            (code, plan_id or None, max_uses, expires_at, now.isoformat()),
        )
        await db.commit()

        security_repo = SecurityRepo(db)
        await security_repo.log_event(
            event_type="invite_created",
            severity="info",
            details=f"Invite code {code} created. Plan: {plan_id or 'free'}, Max uses: {max_uses}",
        )

        # Build the deep link URL (requires bot username)
        from ..bot.bot_manager import get_bot_manager
        manager = get_bot_manager()
        bot_username = (manager._bot_info or {}).get("username", "YOUR_BOT")
        deep_link = f"https://t.me/{bot_username}?start=invite_{code}"

        return json.dumps({
            "status": "created",
            "code": code,
            "deep_link": deep_link,
            "plan_id": plan_id or "free",
            "max_uses": max_uses,
            "expires_at": expires_at,
        }, indent=2)

    @mcp.tool()
    async def deeplink_create_plan_link(plan_id: str) -> str:
        """Generate a direct plan purchase deep link.

        Args:
            plan_id: The plan ID to create a purchase link for
        """
        err = require_license("deeplink_create_plan_link")
        if err:
            return err

        from ..database.plan_repo import PlanRepo
        db = await get_db()
        plan_repo = PlanRepo(db)
        plan = await plan_repo.get(plan_id)
        if not plan:
            return json.dumps({"error": f"Plan '{plan_id}' not found."})

        from ..bot.bot_manager import get_bot_manager
        manager = get_bot_manager()
        bot_username = (manager._bot_info or {}).get("username", "YOUR_BOT")
        deep_link = f"https://t.me/{bot_username}?start=plan_{plan_id}"

        return json.dumps({
            "deep_link": deep_link,
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "price": f"${plan['price_cents'] / 100:.2f}",
        }, indent=2)

    @mcp.tool()
    async def deeplink_revoke_invite(code: str) -> str:
        """Revoke an invite code so it can no longer be used.

        Args:
            code: The invite code to revoke
        """
        err = require_license("deeplink_revoke_invite")
        if err:
            return err

        db = await get_db()
        cursor = await db.execute(
            "UPDATE invite_codes SET revoked = 1 WHERE code = ?", (code,)
        )
        await db.commit()

        if cursor.rowcount > 0:
            security_repo = SecurityRepo(db)
            await security_repo.log_event(
                event_type="invite_revoked",
                severity="info",
                details=f"Invite code {code} revoked",
            )
            return json.dumps({"status": "revoked", "code": code})
        return json.dumps({"error": f"Invite code '{code}' not found."})

    @mcp.tool()
    async def deeplink_list_invites(include_revoked: bool = False) -> str:
        """List all invite codes with their status.

        Args:
            include_revoked: Whether to include revoked invite codes (default False)
        """
        err = require_license("deeplink_list_invites")
        if err:
            return err

        db = await get_db()
        if include_revoked:
            invites = await db.fetchall(
                "SELECT * FROM invite_codes ORDER BY created_at DESC"
            )
        else:
            invites = await db.fetchall(
                "SELECT * FROM invite_codes WHERE revoked = 0 ORDER BY created_at DESC"
            )
        return json.dumps({"count": len(invites), "invites": invites}, indent=2)
