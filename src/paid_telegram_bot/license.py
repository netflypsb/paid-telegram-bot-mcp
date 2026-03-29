"""License key verification + tier gating via mcp-marketplace-license SDK.

Uses the freemium pattern: free tools work without a key,
Pro tools return a helpful error if no valid key is present.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SERVER_SLUG = "paid-telegram-bot"
PURCHASE_URL = f"https://mcp-marketplace.io/servers/{SERVER_SLUG}"

# Cache the last verification result to avoid hammering the API
_license_cache: dict | None = None


def verify() -> dict:
    """Verify the current license key.

    Returns a dict with at least {"valid": bool, "reason": str}.
    Results are cached for the process lifetime.
    """
    global _license_cache
    if _license_cache is not None:
        return _license_cache

    try:
        from mcp_marketplace_license import verify_license
        result = verify_license(slug=SERVER_SLUG)
    except ImportError:
        logger.warning(
            "mcp-marketplace-license SDK not installed. "
            "Pro features disabled. Install with: pip install mcp-marketplace-license"
        )
        result = {"valid": False, "reason": "sdk_not_installed"}
    except Exception as e:
        logger.warning("License verification failed: %s", e)
        result = {"valid": False, "reason": f"verification_error: {e}"}

    _license_cache = result
    return result


def is_licensed() -> bool:
    """Quick check: is the current license valid?"""
    return verify().get("valid", False)


def require_license(tool_name: str) -> Optional[str]:
    """Gate a Pro tool behind license verification.

    Returns None if licensed (allow access), or an error JSON string if not.
    """
    result = verify()
    if result.get("valid"):
        return None
    return json.dumps({
        "error": "premium_required",
        "message": (
            f"'{tool_name}' requires a Pro license key. "
            f"Free tier includes 12 basic tools. "
            f"Get a license at {PURCHASE_URL}"
        ),
        "purchase_url": PURCHASE_URL,
    })


def reset_cache() -> None:
    """Reset license cache (for testing or re-verification)."""
    global _license_cache
    _license_cache = None
