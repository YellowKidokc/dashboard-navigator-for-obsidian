"""
Source detection: identify which AI provider produced an export.

Scans extracted files for provider-specific markers.
Returns a provider key string used to dispatch to the correct adapter.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List


def detect_source(extracted_dir: Path) -> str:
    """
    Inspect the contents of an extracted ZIP and return a provider key.

    Returns one of: "chatgpt", "claude", "gemini", "grok", "unknown"

    Detection order is chosen to avoid false positives:
    1. Path-based checks (Gemini folder, Grok folder) — unambiguous
    2. Schema-based probing of JSON files — inspects actual structure
    """
    files = _list_files(extracted_dir)
    relative_paths = {str(f.relative_to(extracted_dir)) for f in files}

    # --- Gemini (path-based, checked first) ---
    # Google Takeout Gemini exports land in a "Gemini Apps/" folder
    for rp in relative_paths:
        if "gemini" in rp.lower():
            return "gemini"

    # --- Grok (path-based) ---
    for rp in relative_paths:
        if "grok" in rp.lower():
            return "grok"

    # --- Schema-based detection on JSON files ---
    # We probe every JSON file and check for provider-specific structure.
    # ChatGPT conversations have "mapping"; Claude has "chat_messages"/"uuid".
    for f in files:
        if f.suffix == ".json":
            result = _probe_json_schema(f)
            if result != "unknown":
                return result

    # --- Gemini HTML fallback ---
    for f in files:
        if f.suffix == ".html":
            if _probe_html_for_gemini(f):
                return "gemini"

    return "unknown"


def _list_files(directory: Path) -> List[Path]:
    """Recursively list all files under a directory."""
    result = []
    for root, _dirs, filenames in os.walk(directory):
        for fname in filenames:
            result.append(Path(root) / fname)
    return result


def _probe_json_schema(filepath: Path) -> str:
    """
    Inspect a JSON file's structure and return the most likely provider.

    Checks for ChatGPT (mapping), Claude (chat_messages/uuid+name),
    and Grok (grok markers) in that order.  Returns "unknown" if no match.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            raw = fh.read(200_000)
        stripped = raw.strip()
        if not (stripped.startswith("[") or stripped.startswith("{")):
            return "unknown"
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return "unknown"

    items = data if isinstance(data, list) else [data]
    for item in items[:5]:
        if not isinstance(item, dict):
            continue

        # ChatGPT: has "mapping" key with nested message nodes
        if "mapping" in item and isinstance(item["mapping"], dict):
            return "chatgpt"

        # Claude: has "chat_messages" or ("uuid" + "name")
        if "chat_messages" in item:
            return "claude"
        if "uuid" in item and "name" in item:
            return "claude"

        # Grok: "grok" appears in keys/values or X export structure
        if "grok" in json.dumps(item).lower():
            return "grok"
        if "sender" in item and "conversation_id" in item:
            return "grok"

    return "unknown"


def _probe_json_for_claude(filepath: Path) -> bool:
    """Check if a JSON file looks like a Claude export."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            # Read just enough to detect structure without loading entire file
            raw = fh.read(100_000)
        data = json.loads(raw) if raw.strip().startswith("[") or raw.strip().startswith("{") else None
        if data is None:
            return False

        # Claude exports are either a list of conversations or a single conversation
        items = data if isinstance(data, list) else [data]
        for item in items[:3]:
            if isinstance(item, dict):
                if "chat_messages" in item:
                    return True
                if "uuid" in item and "name" in item:
                    return True
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        pass
    return False


def _probe_html_for_gemini(filepath: Path) -> bool:
    """Check if an HTML file contains Gemini conversation markers."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(10_000)
        lower = head.lower()
        return "gemini" in lower or "bard" in lower or "google ai" in lower
    except OSError:
        return False


def _probe_json_for_grok(filepath: Path) -> bool:
    """Check if a JSON file looks like a Grok/X export."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            raw = fh.read(50_000)
        data = json.loads(raw)
        items = data if isinstance(data, list) else [data]
        for item in items[:3]:
            if isinstance(item, dict):
                if "grok" in json.dumps(item).lower():
                    return True
                # X export structure markers
                if "sender" in item and "conversation_id" in item:
                    return True
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        pass
    return False
