"""Database package — SQLite data layer for users, usage, payments, and config."""

from .database import Database, get_db

__all__ = ["Database", "get_db"]
