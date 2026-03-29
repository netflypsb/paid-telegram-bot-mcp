"""Pro-tier Subscription Plan management tools (license required)."""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from ..database.database import get_db
from ..database.plan_repo import PlanRepo
from ..license import require_license

logger = logging.getLogger(__name__)


def register_plan_tools(mcp: FastMCP) -> None:
    """Register all plan management tools on the MCP server."""

    @mcp.tool()
    async def plan_list(include_inactive: bool = False) -> str:
        """List all subscription plans.

        Args:
            include_inactive: Whether to include deactivated plans (default False)
        """
        err = require_license("plan_list")
        if err:
            return err

        db = await get_db()
        plan_repo = PlanRepo(db)
        plans = await plan_repo.list_all(active_only=not include_inactive)
        return json.dumps({"count": len(plans), "plans": plans}, indent=2)

    @mcp.tool()
    async def plan_create(
        plan_id: str,
        name: str,
        description: str = "",
        price_cents: int = 0,
        price_stars: int = 0,
        billing_period: str = "monthly",
        message_limit: int = 0,
    ) -> str:
        """Create a new subscription plan for your bot's users.

        Args:
            plan_id: Unique identifier for the plan (e.g. 'premium', 'gold')
            name: Display name for the plan
            description: Description of what the plan includes
            price_cents: Price in cents USD (e.g. 999 = $9.99)
            price_stars: Price in Telegram Stars
            billing_period: 'daily' or 'monthly' (default 'monthly')
            message_limit: Max messages per billing period (0 = unlimited)
        """
        err = require_license("plan_create")
        if err:
            return err

        db = await get_db()
        plan_repo = PlanRepo(db)

        existing = await plan_repo.get(plan_id)
        if existing:
            return json.dumps({"error": f"Plan '{plan_id}' already exists."})

        plan = await plan_repo.create(
            plan_id=plan_id,
            name=name,
            description=description,
            price_cents=price_cents,
            price_stars=price_stars,
            billing_period=billing_period,
            message_limit=message_limit,
        )
        return json.dumps({"status": "created", "plan": plan}, indent=2)

    @mcp.tool()
    async def plan_update(
        plan_id: str,
        name: str = "",
        description: str = "",
        price_cents: int = -1,
        price_stars: int = -1,
        message_limit: int = -1,
    ) -> str:
        """Update an existing subscription plan.

        Args:
            plan_id: The plan ID to update
            name: New display name (leave empty to keep current)
            description: New description (leave empty to keep current)
            price_cents: New price in cents (-1 to keep current)
            price_stars: New price in Stars (-1 to keep current)
            message_limit: New message limit (-1 to keep current)
        """
        err = require_license("plan_update")
        if err:
            return err

        db = await get_db()
        plan_repo = PlanRepo(db)

        kwargs = {}
        if name:
            kwargs["name"] = name
        if description:
            kwargs["description"] = description
        if price_cents >= 0:
            kwargs["price_cents"] = price_cents
        if price_stars >= 0:
            kwargs["price_stars"] = price_stars
        if message_limit >= 0:
            kwargs["message_limit"] = message_limit

        if not kwargs:
            return json.dumps({"error": "No fields to update."})

        success = await plan_repo.update(plan_id, **kwargs)
        if success:
            plan = await plan_repo.get(plan_id)
            return json.dumps({"status": "updated", "plan": plan}, indent=2)
        return json.dumps({"error": f"Plan '{plan_id}' not found."})

    @mcp.tool()
    async def plan_delete(plan_id: str) -> str:
        """Delete (deactivate) a subscription plan.

        Args:
            plan_id: The plan ID to deactivate
        """
        err = require_license("plan_delete")
        if err:
            return err

        if plan_id == "free":
            return json.dumps({"error": "Cannot delete the default free plan."})

        db = await get_db()
        plan_repo = PlanRepo(db)
        success = await plan_repo.delete(plan_id)
        if success:
            return json.dumps({"status": "deleted", "plan_id": plan_id})
        return json.dumps({"error": f"Plan '{plan_id}' not found."})
