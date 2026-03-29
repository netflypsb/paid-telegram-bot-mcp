"""Security event logging and queries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from .database import Database


class SecurityRepo:
    """Repository for security event operations."""

    def __init__(self, db: Database):
        self._db = db

    async def log_event(
        self,
        event_type: str,
        telegram_id: Optional[int] = None,
        severity: str = "info",
        details: str = "",
    ) -> None:
        """Log a security event."""
        await self._db.execute(
            """INSERT INTO security_events (event_type, telegram_id, severity, details, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (event_type, telegram_id, severity, details, datetime.utcnow().isoformat()),
        )
        await self._db.commit()

    async def get_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        telegram_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query security events with filters."""
        conditions = []
        params: list = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if telegram_id:
            conditions.append("telegram_id = ?")
            params.append(telegram_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        return await self._db.fetchall(
            f"SELECT * FROM security_events {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(params),
        )

    async def count_recent(self, event_type: str, hours: int = 24) -> int:
        """Count recent events of a type."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        row = await self._db.fetchone(
            """SELECT COUNT(*) as cnt FROM security_events
               WHERE event_type = ? AND created_at >= ?""",
            (event_type, since),
        )
        return row["cnt"] if row else 0
