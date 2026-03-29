"""Deep link generation and parsing utilities.

Telegram deep links follow the format: https://t.me/{bot_username}?start={payload}
Payload types:
- invite_{code} — invite code onboarding
- plan_{plan_id} — direct plan purchase
- ref_{referral_code} — referral tracking
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedDeepLink:
    """Result of parsing a deep link payload."""
    link_type: str  # invite | plan | ref | unknown
    value: str  # the code/plan_id/referral_code
    raw_payload: str


def generate_deep_link(bot_username: str, payload: str) -> str:
    """Generate a Telegram deep link URL."""
    return f"https://t.me/{bot_username}?start={payload}"


def generate_invite_link(bot_username: str, code: str) -> str:
    """Generate an invite deep link."""
    return generate_deep_link(bot_username, f"invite_{code}")


def generate_plan_link(bot_username: str, plan_id: str) -> str:
    """Generate a plan purchase deep link."""
    return generate_deep_link(bot_username, f"plan_{plan_id}")


def generate_referral_link(bot_username: str, referral_code: str) -> str:
    """Generate a referral tracking deep link."""
    return generate_deep_link(bot_username, f"ref_{referral_code}")


def parse_deep_link(payload: str) -> ParsedDeepLink:
    """Parse a /start payload into a structured deep link.

    Args:
        payload: The text after /start, e.g. 'invite_ABC123'

    Returns:
        ParsedDeepLink with type and value extracted.
    """
    if not payload:
        return ParsedDeepLink(link_type="unknown", value="", raw_payload="")

    if payload.startswith("invite_"):
        return ParsedDeepLink(
            link_type="invite",
            value=payload[7:],
            raw_payload=payload,
        )
    elif payload.startswith("plan_"):
        return ParsedDeepLink(
            link_type="plan",
            value=payload[5:],
            raw_payload=payload,
        )
    elif payload.startswith("ref_"):
        return ParsedDeepLink(
            link_type="ref",
            value=payload[4:],
            raw_payload=payload,
        )
    else:
        return ParsedDeepLink(
            link_type="unknown",
            value=payload,
            raw_payload=payload,
        )
