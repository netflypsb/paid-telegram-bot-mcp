"""User CRUD operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .database import Database
from .models import User


class UserRepo:
    """Repository for user data operations."""

    def __init__(self, db: Database):
        self._db = db

    async def upsert(self, user: User) -> None:
        """Insert or update a user."""
        await self._db.execute(
            """INSERT INTO users (telegram_id, username, first_name, last_name,
                                  role, plan_id, credits, joined_at, last_active_at,
                                  subscription_expires_at, is_approved, referral_code, invited_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                   username = excluded.username,
                   first_name = excluded.first_name,
                   last_name = excluded.last_name,
                   last_active_at = excluded.last_active_at""",
            (user.telegram_id, user.username, user.first_name, user.last_name,
             user.role, user.plan_id, user.credits, user.joined_at,
             user.last_active_at, user.subscription_expires_at,
             int(user.is_approved), user.referral_code, user.invited_by),
        )
        await self._db.commit()

    async def get(self, telegram_id: int) -> Optional[dict[str, Any]]:
        """Get a user by Telegram ID."""
        return await self._db.fetchone(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )

    async def list_all(
        self,
        role: Optional[str] = None,
        plan_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List users with optional filters."""
        conditions = []
        params: list = []

        if role:
            conditions.append("role = ?")
            params.append(role)
        if plan_id:
            conditions.append("plan_id = ?")
            params.append(plan_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        return await self._db.fetchall(
            f"SELECT * FROM users {where} ORDER BY joined_at DESC LIMIT ? OFFSET ?",
            tuple(params),
        )

    async def count(self, role: Optional[str] = None) -> int:
        """Count users, optionally filtered by role."""
        if role:
            row = await self._db.fetchone(
                "SELECT COUNT(*) as cnt FROM users WHERE role = ?", (role,)
            )
        else:
            row = await self._db.fetchone("SELECT COUNT(*) as cnt FROM users")
        return row["cnt"] if row else 0

    async def update_role(self, telegram_id: int, role: str) -> bool:
        """Update a user's role."""
        cursor = await self._db.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?", (role, telegram_id)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def update_plan(self, telegram_id: int, plan_id: str, expires_at: Optional[str] = None) -> bool:
        """Update a user's plan."""
        cursor = await self._db.execute(
            "UPDATE users SET plan_id = ?, subscription_expires_at = ? WHERE telegram_id = ?",
            (plan_id, expires_at, telegram_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def update_last_active(self, telegram_id: int) -> None:
        """Touch last_active_at timestamp."""
        await self._db.execute(
            "UPDATE users SET last_active_at = ? WHERE telegram_id = ?",
            (datetime.utcnow().isoformat(), telegram_id),
        )
        await self._db.commit()

    async def block(self, telegram_id: int) -> bool:
        """Block a user."""
        return await self.update_role(telegram_id, "blocked")

    async def unblock(self, telegram_id: int) -> bool:
        """Unblock a user (set back to free)."""
        return await self.update_role(telegram_id, "free")

    async def get_inactive(self, days: int = 30) -> list[dict[str, Any]]:
        """Get users inactive for more than N days."""
        return await self._db.fetchall(
            """SELECT * FROM users
               WHERE julianday('now') - julianday(last_active_at) > ?
               AND role != 'blocked'""",
            (days,),
        )
