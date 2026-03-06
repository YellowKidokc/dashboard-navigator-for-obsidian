"""
Text normalization utilities.

Shared helpers for cleaning up content across adapters.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Optional


def unix_to_datetime(timestamp: Optional[float]) -> Optional[datetime]:
    """Convert a Unix timestamp (seconds) to a UTC datetime, or None."""
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


def iso_to_datetime(iso_string: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string, or return None."""
    if not iso_string:
        return None
    try:
        # Handle both Z suffix and +00:00 style
        cleaned = iso_string.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities. Returns plain text."""
    # Decode HTML entities first
    text = html.unescape(text)
    # Remove tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_content(text: Optional[str]) -> str:
    """Normalize message content: handle None, strip trailing whitespace."""
    if text is None:
        return ""
    if isinstance(text, list):
        # Some providers store content as a list of parts
        parts = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                # e.g. ChatGPT image_asset_pointer or tether_quote
                parts.append(part.get("text", str(part)))
        return "\n".join(parts).strip()
    return str(text).strip()


def sanitize_id(raw_id: Optional[str]) -> str:
    """Ensure we have a usable string ID."""
    if raw_id is None:
        return "unknown"
    return str(raw_id).strip() or "unknown"
