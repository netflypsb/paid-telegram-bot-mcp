"""Tests for MCP tool registration and license gating."""

import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from paid_telegram_bot.license import reset_cache


@pytest.fixture(autouse=True)
def clear_license_cache():
    reset_cache()
    yield
    reset_cache()


@patch("paid_telegram_bot.license.verify_license")
def test_pro_tool_blocked_without_license(mock_verify):
    """Pro tools should return premium_required error without a license."""
    mock_verify.return_value = {"valid": False, "reason": "missing_key"}
    from paid_telegram_bot.license import require_license
    result = require_license("user_list")
    assert result is not None
    data = json.loads(result)
    assert data["error"] == "premium_required"


@patch("paid_telegram_bot.license.verify_license")
def test_pro_tool_allowed_with_license(mock_verify):
    """Pro tools should return None (allowed) with a valid license."""
    mock_verify.return_value = {"valid": True, "reason": "active"}
    from paid_telegram_bot.license import require_license
    result = require_license("user_list")
    assert result is None


def test_formatter_markdown_to_html():
    from paid_telegram_bot.utils.formatter import markdown_to_html
    assert "<b>bold</b>" in markdown_to_html("**bold**")
    assert "<i>italic</i>" in markdown_to_html("*italic*")
    assert "<code>code</code>" in markdown_to_html("`code`")


def test_formatter_split_message():
    from paid_telegram_bot.utils.formatter import split_message
    short = "Hello"
    assert split_message(short) == [short]

    long = "a" * 5000
    chunks = split_message(long, max_length=4096)
    assert len(chunks) >= 2
    assert all(len(c) <= 4096 for c in chunks)


def test_formatter_escape_html():
    from paid_telegram_bot.utils.formatter import escape_html
    assert escape_html("<b>test</b>") == "&lt;b&gt;test&lt;/b&gt;"
    assert escape_html("a & b") == "a &amp; b"


def test_deep_link_parsing():
    from paid_telegram_bot.utils.deep_links import parse_deep_link
    invite = parse_deep_link("invite_ABC123")
    assert invite.link_type == "invite"
    assert invite.value == "ABC123"

    plan = parse_deep_link("plan_pro")
    assert plan.link_type == "plan"
    assert plan.value == "pro"

    ref = parse_deep_link("ref_user42")
    assert ref.link_type == "ref"
    assert ref.value == "user42"

    unknown = parse_deep_link("something_else")
    assert unknown.link_type == "unknown"


def test_deep_link_generation():
    from paid_telegram_bot.utils.deep_links import (
        generate_invite_link,
        generate_plan_link,
        generate_referral_link,
    )
    assert generate_invite_link("mybot", "ABC") == "https://t.me/mybot?start=invite_ABC"
    assert generate_plan_link("mybot", "pro") == "https://t.me/mybot?start=plan_pro"
    assert generate_referral_link("mybot", "ref1") == "https://t.me/mybot?start=ref_ref1"


def test_file_delivery_detect_media_type():
    from paid_telegram_bot.utils.file_delivery import detect_media_type
    assert detect_media_type("photo.jpg") == "photo"
    assert detect_media_type("photo.png") == "photo"
    assert detect_media_type("video.mp4") == "video"
    assert detect_media_type("song.mp3") == "audio"
    assert detect_media_type("file.pdf") == "document"
    assert detect_media_type("data.csv") == "document"
