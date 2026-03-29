"""Tests for license key verification and tier gating."""

import json
from unittest.mock import patch, MagicMock

import pytest

from paid_telegram_bot.license import (
    verify,
    is_licensed,
    require_license,
    reset_cache,
    SERVER_SLUG,
    PURCHASE_URL,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset license cache before each test."""
    reset_cache()
    yield
    reset_cache()


@patch("paid_telegram_bot.license.verify_license")
def test_verify_valid_key(mock_verify):
    mock_verify.return_value = {"valid": True, "reason": "active"}
    result = verify()
    assert result["valid"] is True
    mock_verify.assert_called_once_with(slug=SERVER_SLUG)


@patch("paid_telegram_bot.license.verify_license")
def test_verify_invalid_key(mock_verify):
    mock_verify.return_value = {"valid": False, "reason": "expired"}
    result = verify()
    assert result["valid"] is False


@patch("paid_telegram_bot.license.verify_license")
def test_verify_caches_result(mock_verify):
    mock_verify.return_value = {"valid": True, "reason": "active"}
    verify()
    verify()
    verify()
    # Should only call the API once
    mock_verify.assert_called_once()


@patch("paid_telegram_bot.license.verify_license")
def test_is_licensed_true(mock_verify):
    mock_verify.return_value = {"valid": True, "reason": "active"}
    assert is_licensed() is True


@patch("paid_telegram_bot.license.verify_license")
def test_is_licensed_false(mock_verify):
    mock_verify.return_value = {"valid": False, "reason": "missing_key"}
    assert is_licensed() is False


@patch("paid_telegram_bot.license.verify_license")
def test_require_license_with_valid_key(mock_verify):
    mock_verify.return_value = {"valid": True, "reason": "active"}
    result = require_license("user_list")
    assert result is None  # None means access granted


@patch("paid_telegram_bot.license.verify_license")
def test_require_license_without_key(mock_verify):
    mock_verify.return_value = {"valid": False, "reason": "missing_key"}
    result = require_license("user_list")
    assert result is not None
    data = json.loads(result)
    assert data["error"] == "premium_required"
    assert "user_list" in data["message"]
    assert PURCHASE_URL in data["purchase_url"]


def test_sdk_not_installed():
    """Test graceful handling when mcp-marketplace-license is not installed."""
    with patch.dict("sys.modules", {"mcp_marketplace_license": None}):
        reset_cache()
        # Force re-import path by clearing cache
        from paid_telegram_bot import license as lic
        lic._license_cache = None
        # The ImportError path in verify() handles missing SDK
        result = lic.verify()
        assert result["valid"] is False
