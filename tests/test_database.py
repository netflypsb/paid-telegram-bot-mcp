"""Tests for the database layer — models, repos, migrations."""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure tests use a temporary data directory
_test_dir = tempfile.mkdtemp(prefix="ptb_test_")
os.environ["PAID_TELEGRAM_BOT_DATA_DIR"] = _test_dir

from paid_telegram_bot.config import reset_config, get_config
from paid_telegram_bot.database.database import Database
from paid_telegram_bot.database.user_repo import UserRepo
from paid_telegram_bot.database.plan_repo import PlanRepo
from paid_telegram_bot.database.payment_repo import PaymentRepo
from paid_telegram_bot.database.usage_repo import UsageRepo
from paid_telegram_bot.database.security_repo import SecurityRepo
from paid_telegram_bot.database.models import User


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db(tmp_path):
    """Create a fresh database for each test."""
    db_path = tmp_path / "test.db"
    database = Database(db_path=db_path)
    await database.connect()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_database_connect_and_migrate(tmp_path):
    db_path = tmp_path / "test.db"
    database = Database(db_path=db_path)
    await database.connect()

    # Verify tables exist
    tables = await database.fetchall(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = {t["name"] for t in tables}
    assert "users" in table_names
    assert "plans" in table_names
    assert "payments" in table_names
    assert "usage_logs" in table_names
    assert "security_events" in table_names
    assert "invite_codes" in table_names
    assert "messages" in table_names
    assert "schema_version" in table_names

    await database.close()


@pytest.mark.asyncio
async def test_default_plans_seeded(db):
    plan_repo = PlanRepo(db)
    plans = await plan_repo.list_all(active_only=False)
    plan_ids = {p["plan_id"] for p in plans}
    assert "free" in plan_ids
    assert "basic" in plan_ids
    assert "pro" in plan_ids
    assert "enterprise" in plan_ids


@pytest.mark.asyncio
async def test_user_crud(db):
    user_repo = UserRepo(db)

    # Create user
    user = User(telegram_id=12345, username="testuser", first_name="Test")
    await user_repo.upsert(user)

    # Read
    fetched = await user_repo.get(12345)
    assert fetched is not None
    assert fetched["username"] == "testuser"
    assert fetched["role"] == "free"

    # Update role
    await user_repo.update_role(12345, "subscriber")
    fetched = await user_repo.get(12345)
    assert fetched["role"] == "subscriber"

    # Block
    await user_repo.block(12345)
    fetched = await user_repo.get(12345)
    assert fetched["role"] == "blocked"

    # Unblock
    await user_repo.unblock(12345)
    fetched = await user_repo.get(12345)
    assert fetched["role"] == "free"

    # List
    users = await user_repo.list_all()
    assert len(users) == 1

    # Count
    count = await user_repo.count()
    assert count == 1


@pytest.mark.asyncio
async def test_user_upsert_updates_existing(db):
    user_repo = UserRepo(db)

    user = User(telegram_id=99999, username="old_name", first_name="Old")
    await user_repo.upsert(user)

    user2 = User(telegram_id=99999, username="new_name", first_name="New")
    await user_repo.upsert(user2)

    fetched = await user_repo.get(99999)
    assert fetched["username"] == "new_name"

    count = await user_repo.count()
    assert count == 1


@pytest.mark.asyncio
async def test_plan_crud(db):
    plan_repo = PlanRepo(db)

    # Create
    plan = await plan_repo.create(
        plan_id="test_plan",
        name="Test Plan",
        description="A test plan",
        price_cents=999,
        price_stars=500,
        message_limit=1000,
    )
    assert plan["plan_id"] == "test_plan"
    assert plan["price_cents"] == 999

    # Update
    await plan_repo.update("test_plan", price_cents=1299)
    fetched = await plan_repo.get("test_plan")
    assert fetched["price_cents"] == 1299

    # Delete (soft)
    await plan_repo.delete("test_plan")
    fetched = await plan_repo.get("test_plan")
    assert fetched["is_active"] == 0


@pytest.mark.asyncio
async def test_payment_recording(db):
    payment_repo = PaymentRepo(db)

    payment_id = await payment_repo.record(
        telegram_id=12345,
        plan_id="pro",
        amount_cents=2000,
        currency="USD",
        payment_method="stripe",
    )
    assert payment_id is not None

    payments = await payment_repo.list_payments(telegram_id=12345)
    assert len(payments) == 1
    assert payments[0]["amount_cents"] == 2000

    revenue = await payment_repo.get_revenue("all_time")
    assert revenue["total_cents"] == 2000
    assert revenue["transaction_count"] == 1


@pytest.mark.asyncio
async def test_usage_tracking(db):
    usage_repo = UsageRepo(db)

    await usage_repo.log_event(
        telegram_id=12345,
        event_type="message_sent",
        chat_id=67890,
    )
    await usage_repo.log_event(
        telegram_id=12345,
        event_type="message_sent",
        chat_id=67890,
    )

    count = await usage_repo.get_usage_count(12345, "message_sent", "monthly")
    assert count == 2

    stats = await usage_repo.get_user_stats(12345)
    assert stats["total_events"] == 2


@pytest.mark.asyncio
async def test_security_events(db):
    security_repo = SecurityRepo(db)

    await security_repo.log_event(
        event_type="block",
        telegram_id=12345,
        severity="warning",
        details="User blocked for spam",
    )

    events = await security_repo.get_events(event_type="block")
    assert len(events) == 1
    assert events[0]["severity"] == "warning"

    count = await security_repo.count_recent("block", hours=24)
    assert count == 1
