"""Usage tracking and limit enforcement."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from .database import Database


class UsageRepo:
    """Repository for usage tracking operations."""

    def __init__(self, db: Database):
        self._db = db

    async def log_event(
        self,
        telegram_id: int,
        event_type: str,
        chat_id: int = 0,
        details: Optional[str] = None,
    ) -> None:
        """Log a usage event."""
        await self._db.execute(
            """INSERT INTO usage_logs (telegram_id, event_type, chat_id, timestamp, details)
               VALUES (?, ?, ?, ?, ?)""",
            (telegram_id, event_type, chat_id, datetime.utcnow().isoformat(), details),
        )
        await self._db.commit()

    async def get_usage_count(
        self,
        telegram_id: int,
        event_type: str = "message_sent",
        period: str = "monthly",
    ) -> int:
        """Get usage count for a user within a billing period."""
        if period == "daily":
            since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            now = datetime.utcnow()
            since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            since = datetime.utcnow() - timedelta(hours=1)

        row = await self._db.fetchone(
            """SELECT COUNT(*) as cnt FROM usage_logs
               WHERE telegram_id = ? AND event_type = ? AND timestamp >= ?""",
            (telegram_id, event_type, since.isoformat()),
        )
        return row["cnt"] if row else 0

    async def get_hourly_outbound_count(self) -> int:
        """Get total outbound messages in the last hour (for free tier limit)."""
        since = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        row = await self._db.fetchone(
            """SELECT COUNT(*) as cnt FROM usage_logs
               WHERE event_type = 'message_sent' AND timestamp >= ?""",
            (since,),
        )
        return row["cnt"] if row else 0

    async def get_user_stats(self, telegram_id: int) -> dict[str, Any]:
        """Get usage statistics for a specific user."""
        total = await self._db.fetchone(
            "SELECT COUNT(*) as cnt FROM usage_logs WHERE telegram_id = ?",
            (telegram_id,),
        )
        monthly = await self.get_usage_count(telegram_id, "message_sent", "monthly")
        daily = await self.get_usage_count(telegram_id, "message_sent", "daily")

        return {
            "telegram_id": telegram_id,
            "total_events": total["cnt"] if total else 0,
            "messages_this_month": monthly,
            "messages_today": daily,
        }

    async def get_messages_by_day(self, days: int = 30) -> list[dict[str, Any]]:
        """Get message counts grouped by day for the last N days."""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return await self._db.fetchall(
            """SELECT date(timestamp) as day, COUNT(*) as count
               FROM usage_logs
               WHERE event_type IN ('message_sent', 'message_received')
               AND timestamp >= ?
               GROUP BY date(timestamp)
               ORDER BY day""",
            (since,),
        )
