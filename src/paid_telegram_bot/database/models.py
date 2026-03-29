"""Data models for the database layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """A Telegram user who has interacted with the bot."""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "free"  # owner | subscriber | free | blocked
    plan_id: Optional[str] = None
    credits: int = 0
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    subscription_expires_at: Optional[str] = None
    is_approved: bool = True
    referral_code: Optional[str] = None
    invited_by: Optional[int] = None


@dataclass
class UsageLog:
    """A single usage event (message sent or received)."""
    id: Optional[int] = None
    telegram_id: int = 0
    event_type: str = "message_sent"  # message_sent | message_received | command | payment
    chat_id: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Optional[str] = None


@dataclass
class Plan:
    """A subscription plan offered by the bot."""
    plan_id: str = ""
    name: str = ""
    description: str = ""
    price_cents: int = 0  # price in cents (USD)
    price_stars: int = 0  # price in Telegram Stars
    billing_period: str = "monthly"  # daily | monthly
    message_limit: int = 0  # 0 = unlimited
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Payment:
    """A payment record."""
    id: Optional[int] = None
    telegram_id: int = 0
    plan_id: Optional[str] = None
    amount_cents: int = 0
    currency: str = "USD"
    payment_method: str = "stripe"  # stripe | stars
    telegram_payment_charge_id: Optional[str] = None
    provider_payment_charge_id: Optional[str] = None
    status: str = "completed"  # completed | refunded | failed
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SecurityEvent:
    """A security event log entry."""
    id: Optional[int] = None
    event_type: str = ""  # login | block | unblock | rate_limit | suspicious | invite_created | invite_revoked
    telegram_id: Optional[int] = None
    severity: str = "info"  # info | warning | critical
    details: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class InviteCode:
    """A deep link invite code."""
    code: str = ""
    plan_id: Optional[str] = None
    created_by: int = 0
    max_uses: int = 0  # 0 = unlimited
    used_count: int = 0
    expires_at: Optional[str] = None
    revoked: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Message:
    """A stored message for history search."""
    id: Optional[int] = None
    telegram_id: int = 0
    chat_id: int = 0
    message_id: int = 0
    text: str = ""
    direction: str = "incoming"  # incoming | outgoing
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
