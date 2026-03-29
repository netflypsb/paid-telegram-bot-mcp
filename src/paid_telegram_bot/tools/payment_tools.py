"""Pro-tier Payment tools (license required)."""

from __future__ import annotations

import json
import logging
import os

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..database.database import get_db
from ..database.payment_repo import PaymentRepo
from ..database.plan_repo import PlanRepo
from ..license import require_license

logger = logging.getLogger(__name__)


def register_payment_tools(mcp: FastMCP) -> None:
    """Register all payment tools on the MCP server."""

    @mcp.tool()
    async def payment_send_invoice(
        chat_id: int,
        plan_id: str,
        payment_method: str = "stars",
    ) -> str:
        """Send a payment invoice to a user via Telegram Bot Payments API.

        Args:
            chat_id: The Telegram chat ID to send the invoice to
            plan_id: The subscription plan ID to create the invoice for
            payment_method: 'stripe' for fiat currency or 'stars' for Telegram Stars
        """
        err = require_license("payment_send_invoice")
        if err:
            return err

        manager = get_bot_manager()
        if not manager.bot:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        db = await get_db()
        plan_repo = PlanRepo(db)
        plan = await plan_repo.get(plan_id)
        if not plan:
            return json.dumps({"error": f"Plan '{plan_id}' not found."})

        try:
            if payment_method == "stars":
                # Telegram Stars payment
                await manager.bot.send_invoice(
                    chat_id=chat_id,
                    title=f"Subscribe to {plan['name']}",
                    description=plan["description"] or f"{plan['name']} subscription",
                    payload=f"plan:{plan_id}",
                    currency="XTR",
                    prices=[{"label": plan["name"], "amount": plan["price_stars"]}],
                )
            elif payment_method == "stripe":
                provider_token = os.environ.get("STRIPE_PROVIDER_TOKEN", "")
                if not provider_token:
                    return json.dumps({
                        "error": "STRIPE_PROVIDER_TOKEN not set. "
                                 "Configure it in your MCP environment."
                    })
                await manager.bot.send_invoice(
                    chat_id=chat_id,
                    title=f"Subscribe to {plan['name']}",
                    description=plan["description"] or f"{plan['name']} subscription",
                    payload=f"plan:{plan_id}",
                    provider_token=provider_token,
                    currency="USD",
                    prices=[{"label": plan["name"], "amount": plan["price_cents"]}],
                )
            else:
                return json.dumps({"error": "payment_method must be 'stripe' or 'stars'."})

            return json.dumps({
                "status": "invoice_sent",
                "chat_id": chat_id,
                "plan_id": plan_id,
                "method": payment_method,
            })

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def payment_list(
        telegram_id: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> str:
        """List payment history with optional user filter.

        Args:
            telegram_id: Filter by Telegram user ID (0 for all)
            limit: Maximum number of payments to return
            offset: Offset for pagination
        """
        err = require_license("payment_list")
        if err:
            return err

        db = await get_db()
        payment_repo = PaymentRepo(db)
        payments = await payment_repo.list_payments(
            telegram_id=telegram_id or None,
            limit=limit,
            offset=offset,
        )
        return json.dumps({"count": len(payments), "payments": payments}, indent=2)

    @mcp.tool()
    async def payment_get_revenue(period: str = "monthly") -> str:
        """Get a revenue report for the bot.

        Args:
            period: Report period - 'monthly' (current month) or 'all_time'
        """
        err = require_license("payment_get_revenue")
        if err:
            return err

        db = await get_db()
        payment_repo = PaymentRepo(db)
        revenue = await payment_repo.get_revenue(period=period)
        return json.dumps(revenue, indent=2)
