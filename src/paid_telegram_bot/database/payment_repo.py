"""Payment recording and queries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from .database import Database


class PaymentRepo:
    """Repository for payment operations."""

    def __init__(self, db: Database):
        self._db = db

    async def record(
        self,
        telegram_id: int,
        plan_id: Optional[str],
        amount_cents: int,
        currency: str = "USD",
        payment_method: str = "stripe",
        telegram_payment_charge_id: Optional[str] = None,
        provider_payment_charge_id: Optional[str] = None,
    ) -> int:
        """Record a payment. Returns the payment ID."""
        cursor = await self._db.execute(
            """INSERT INTO payments (telegram_id, plan_id, amount_cents, currency,
                                     payment_method, telegram_payment_charge_id,
                                     provider_payment_charge_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?)""",
            (telegram_id, plan_id, amount_cents, currency, payment_method,
             telegram_payment_charge_id, provider_payment_charge_id,
             datetime.utcnow().isoformat()),
        )
        await self._db.commit()
        return cursor.lastrowid  # type: ignore

    async def list_payments(
        self,
        telegram_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List payments with optional user filter."""
        if telegram_id:
            return await self._db.fetchall(
                "SELECT * FROM payments WHERE telegram_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (telegram_id, limit, offset),
            )
        return await self._db.fetchall(
            "SELECT * FROM payments ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )

    async def get_revenue(
        self,
        period: str = "monthly",
    ) -> dict[str, Any]:
        """Get revenue report."""
        if period == "monthly":
            now = datetime.utcnow()
            since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        elif period == "all_time":
            since = "2000-01-01T00:00:00"
        else:
            since = (datetime.utcnow() - timedelta(days=30)).isoformat()

        row = await self._db.fetchone(
            """SELECT COALESCE(SUM(amount_cents), 0) as total_cents,
                      COUNT(*) as transaction_count
               FROM payments
               WHERE status = 'completed' AND created_at >= ?""",
            (since,),
        )

        return {
            "period": period,
            "total_cents": row["total_cents"] if row else 0,
            "total_formatted": f"${(row['total_cents'] if row else 0) / 100:.2f}",
            "transaction_count": row["transaction_count"] if row else 0,
        }
