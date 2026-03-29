"""Pro-tier Event subscription tools (license required)."""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from ..license import require_license

logger = logging.getLogger(__name__)

MAX_EVENT_QUEUE_SIZE = 500


class EventManager:
    """Manages event subscriptions and an event queue for polling."""

    def __init__(self):
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._event_queue: deque[dict[str, Any]] = deque(maxlen=MAX_EVENT_QUEUE_SIZE)

    @property
    def subscriptions(self) -> dict[str, dict[str, Any]]:
        return dict(self._subscriptions)

    def subscribe(
        self,
        event_type: str,
        filters: Optional[dict[str, Any]] = None,
    ) -> str:
        """Subscribe to an event type."""
        sub_id = f"{event_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self._subscriptions[sub_id] = {
            "event_type": event_type,
            "filters": filters or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        return sub_id

    def unsubscribe(self, sub_id: str) -> bool:
        """Remove a subscription."""
        return self._subscriptions.pop(sub_id, None) is not None

    def push_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Push an event to the queue if anyone is subscribed."""
        for sub in self._subscriptions.values():
            if sub["event_type"] == event_type or sub["event_type"] == "*":
                self._event_queue.append({
                    "event_type": event_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                break

    def poll_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Poll and drain events from the queue."""
        events = []
        while self._event_queue and len(events) < limit:
            events.append(self._event_queue.popleft())
        return events


# Singleton
_event_manager: Optional[EventManager] = None


def get_event_manager() -> EventManager:
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager


def register_event_tools(mcp: FastMCP) -> None:
    """Register all event subscription tools on the MCP server."""

    @mcp.tool()
    async def subscribe_events(
        event_type: str,
        keyword_filter: str = "",
    ) -> str:
        """Subscribe to Telegram events to receive notifications via polling.

        Args:
            event_type: Event type to subscribe to - 'new_message', 'new_user', 'keyword_match', 'payment_received', or '*' for all
            keyword_filter: For 'keyword_match' events, the keyword to match on
        """
        err = require_license("subscribe_events")
        if err:
            return err

        valid_types = {"new_message", "new_user", "keyword_match", "payment_received", "*"}
        if event_type not in valid_types:
            return json.dumps({
                "error": f"Invalid event_type. Must be one of: {', '.join(sorted(valid_types))}"
            })

        em = get_event_manager()
        filters = {}
        if keyword_filter:
            filters["keyword"] = keyword_filter

        sub_id = em.subscribe(event_type, filters)
        return json.dumps({
            "status": "subscribed",
            "subscription_id": sub_id,
            "event_type": event_type,
            "filters": filters,
        }, indent=2)

    @mcp.tool()
    async def get_event_queue(limit: int = 50) -> str:
        """Poll for events from your subscriptions. Events are consumed once read.

        Args:
            limit: Maximum number of events to return (default 50)
        """
        err = require_license("get_event_queue")
        if err:
            return err

        em = get_event_manager()
        events = em.poll_events(limit)
        return json.dumps({
            "count": len(events),
            "events": events,
            "active_subscriptions": len(em.subscriptions),
        }, indent=2)

    @mcp.tool()
    async def history_search(
        query: str,
        chat_id: int = 0,
        limit: int = 50,
    ) -> str:
        """Search chat history with keyword/date filters using full-text search.

        Args:
            query: Search query (supports SQLite FTS5 syntax)
            chat_id: Filter by chat ID (0 for all chats)
            limit: Maximum number of results to return
        """
        err = require_license("history_search")
        if err:
            return err

        from ..database.database import get_db
        db = await get_db()

        if chat_id:
            results = await db.fetchall(
                """SELECT m.* FROM messages m
                   JOIN messages_fts ON m.id = messages_fts.rowid
                   WHERE messages_fts MATCH ? AND m.chat_id = ?
                   ORDER BY m.timestamp DESC LIMIT ?""",
                (query, chat_id, limit),
            )
        else:
            results = await db.fetchall(
                """SELECT m.* FROM messages m
                   JOIN messages_fts ON m.id = messages_fts.rowid
                   WHERE messages_fts MATCH ?
                   ORDER BY m.timestamp DESC LIMIT ?""",
                (query, limit),
            )

        return json.dumps({"count": len(results), "messages": results}, indent=2)

    @mcp.tool()
    async def history_export(
        chat_id: int,
        format: str = "json",
        limit: int = 1000,
    ) -> str:
        """Export chat history to a file.

        Args:
            chat_id: The chat ID to export history for
            format: Export format - 'json' or 'txt' (default 'json')
            limit: Maximum number of messages to export (default 1000)
        """
        err = require_license("history_export")
        if err:
            return err

        from ..database.database import get_db
        from ..config import get_config
        db = await get_db()

        messages = await db.fetchall(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp LIMIT ?",
            (chat_id, limit),
        )

        config = get_config()
        export_dir = config.files_path / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if format == "txt":
            file_path = export_dir / f"chat_{chat_id}_{timestamp}.txt"
            lines = []
            for msg in messages:
                direction = "→" if msg["direction"] == "outgoing" else "←"
                lines.append(f"[{msg['timestamp']}] {direction} {msg['text']}")
            file_path.write_text("\n".join(lines), encoding="utf-8")
        else:
            file_path = export_dir / f"chat_{chat_id}_{timestamp}.json"
            import json as json_mod
            file_path.write_text(
                json_mod.dumps(messages, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return json.dumps({
            "status": "exported",
            "file_path": str(file_path),
            "message_count": len(messages),
            "format": format,
        }, indent=2)
