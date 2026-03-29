"""SQLite database connection, migrations, and core operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from ..config import get_config

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    role TEXT NOT NULL DEFAULT 'free',
    plan_id TEXT,
    credits INTEGER NOT NULL DEFAULT 0,
    joined_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    subscription_expires_at TEXT,
    is_approved INTEGER NOT NULL DEFAULT 1,
    referral_code TEXT,
    invited_by INTEGER
);

-- Usage logs table
CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    chat_id INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);
CREATE INDEX IF NOT EXISTS idx_usage_logs_telegram_id ON usage_logs(telegram_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);

-- Plans table
CREATE TABLE IF NOT EXISTS plans (
    plan_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price_cents INTEGER NOT NULL DEFAULT 0,
    price_stars INTEGER NOT NULL DEFAULT 0,
    billing_period TEXT NOT NULL DEFAULT 'monthly',
    message_limit INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    plan_id TEXT,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    payment_method TEXT NOT NULL DEFAULT 'stripe',
    telegram_payment_charge_id TEXT,
    provider_payment_charge_id TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TEXT NOT NULL,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);
CREATE INDEX IF NOT EXISTS idx_payments_telegram_id ON payments(telegram_id);

-- Security events table
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    telegram_id INTEGER,
    severity TEXT NOT NULL DEFAULT 'info',
    details TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at);

-- Invite codes table
CREATE TABLE IF NOT EXISTS invite_codes (
    code TEXT PRIMARY KEY,
    plan_id TEXT,
    created_by INTEGER NOT NULL,
    max_uses INTEGER NOT NULL DEFAULT 0,
    used_count INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT,
    revoked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- Messages table (for chat history search)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    direction TEXT NOT NULL DEFAULT 'incoming',
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- FTS5 virtual table for full-text search on messages
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text,
    content=messages,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, text) VALUES('delete', old.id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, text) VALUES('delete', old.id, old.text);
    INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
END;

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);
"""

DEFAULT_PLANS_SQL = """
INSERT OR IGNORE INTO plans (plan_id, name, description, price_cents, price_stars, billing_period, message_limit, is_active, created_at)
VALUES
    ('free', 'Free', 'Basic access with limited messages', 0, 0, 'monthly', 100, 1, datetime('now')),
    ('basic', 'Basic', 'Standard access for regular users', 500, 250, 'monthly', 1000, 1, datetime('now')),
    ('pro', 'Pro', 'Full access with high limits', 2000, 1000, 'monthly', 5000, 1, datetime('now')),
    ('enterprise', 'Enterprise', 'Unlimited access for power users', 5000, 2500, 'monthly', 0, 1, datetime('now'));
"""


class Database:
    """Async SQLite database wrapper."""

    def __init__(self, db_path: Path | str | None = None):
        if db_path is None:
            db_path = get_config().db_path
        self._db_path = str(db_path)
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Open database connection and run migrations."""
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._migrate()
        logger.info("Database connected: %s", self._db_path)

    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("Database closed")

    async def _migrate(self) -> None:
        """Run schema migrations."""
        assert self._conn is not None
        await self._conn.executescript(SCHEMA_SQL)

        # Check if schema_version has a row
        cursor = await self._conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            await self._conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,)
            )
            # Seed default plans
            await self._conn.executescript(DEFAULT_PLANS_SQL)
        await self._conn.commit()

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get the active connection. Raises if not connected."""
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a single SQL statement."""
        return await self.conn.execute(sql, params)

    async def executemany(self, sql: str, params_seq: list[tuple]) -> aiosqlite.Cursor:
        """Execute a SQL statement for each set of params."""
        return await self.conn.executemany(sql, params_seq)

    async def fetchone(self, sql: str, params: tuple = ()) -> Optional[dict[str, Any]]:
        """Execute and fetch one row as a dict."""
        cursor = await self.conn.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute and fetch all rows as dicts."""
        cursor = await self.conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.conn.commit()


# Singleton
_db: Optional[Database] = None


async def get_db() -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.connect()
    return _db


async def close_db() -> None:
    """Close the global database instance."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
