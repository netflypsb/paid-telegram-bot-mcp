"""Telegram HTML formatting and message splitting.

Telegram Bot API uses a subset of HTML for formatting:
<b>bold</b>, <i>italic</i>, <u>underline</u>, <s>strikethrough</s>,
<code>inline code</code>, <pre>code block</pre>, <a href="url">link</a>

Messages are limited to 4096 characters. This module handles splitting.
"""

from __future__ import annotations

import re
from typing import Optional

TELEGRAM_MAX_LENGTH = 4096
SPLIT_MARGIN = 100  # leave margin for split indicators


def markdown_to_html(text: str) -> str:
    """Convert basic Markdown to Telegram HTML.

    Handles: **bold**, *italic*, `code`, ```code blocks```, [text](url)
    """
    # Code blocks first (to avoid processing inside them)
    text = re.sub(r"```(\w*)\n(.*?)```", r"<pre>\2</pre>", text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic (single asterisk, but not inside HTML tags)
    text = re.sub(r"(?<![<\w])\*(.+?)\*(?![>\w])", r"<i>\1</i>", text)
    # Links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Strikethrough
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

    return text


def split_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Split a long message into Telegram-safe chunks.

    Tries to split at paragraph boundaries, then sentence boundaries,
    then word boundaries, as a last resort at max_length.
    """
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Find the best split point
        split_at = _find_split_point(remaining, max_length - SPLIT_MARGIN)
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    return chunks


def _find_split_point(text: str, max_pos: int) -> int:
    """Find the best position to split text at or before max_pos."""
    # Try paragraph break
    pos = text.rfind("\n\n", 0, max_pos)
    if pos > max_pos // 2:
        return pos + 2

    # Try line break
    pos = text.rfind("\n", 0, max_pos)
    if pos > max_pos // 2:
        return pos + 1

    # Try sentence end
    for pattern in [". ", "! ", "? "]:
        pos = text.rfind(pattern, 0, max_pos)
        if pos > max_pos // 2:
            return pos + 2

    # Try word boundary
    pos = text.rfind(" ", 0, max_pos)
    if pos > max_pos // 4:
        return pos + 1

    # Hard split
    return max_pos


def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_user_mention(user_id: int, name: str) -> str:
    """Create an HTML user mention link."""
    safe_name = escape_html(name)
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
