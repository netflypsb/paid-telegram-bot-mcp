"""Plan CRUD operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .database import Database


class PlanRepo:
    """Repository for subscription plan operations."""

    def __init__(self, db: Database):
        self._db = db

    async def create(
        self,
        plan_id: str,
        name: str,
        description: str = "",
        price_cents: int = 0,
        price_stars: int = 0,
        billing_period: str = "monthly",
        message_limit: int = 0,
    ) -> dict[str, Any]:
        """Create a new plan."""
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            """INSERT INTO plans (plan_id, name, description, price_cents, price_stars,
                                  billing_period, message_limit, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (plan_id, name, description, price_cents, price_stars,
             billing_period, message_limit, now),
        )
        await self._db.commit()
        return await self.get(plan_id)  # type: ignore

    async def get(self, plan_id: str) -> Optional[dict[str, Any]]:
        """Get a plan by ID."""
        return await self._db.fetchone(
            "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)
        )

    async def list_all(self, active_only: bool = True) -> list[dict[str, Any]]:
        """List all plans."""
        if active_only:
            return await self._db.fetchall(
                "SELECT * FROM plans WHERE is_active = 1 ORDER BY price_cents"
            )
        return await self._db.fetchall("SELECT * FROM plans ORDER BY price_cents")

    async def update(self, plan_id: str, **kwargs: Any) -> bool:
        """Update plan fields."""
        allowed = {"name", "description", "price_cents", "price_stars",
                    "billing_period", "message_limit", "is_active"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [plan_id]

        cursor = await self._db.execute(
            f"UPDATE plans SET {set_clause} WHERE plan_id = ?", tuple(params)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def delete(self, plan_id: str) -> bool:
        """Soft-delete a plan (set inactive)."""
        return await self.update(plan_id, is_active=False)
