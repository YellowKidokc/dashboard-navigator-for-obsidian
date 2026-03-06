"""
Generic fallback adapter.

Handles unrecognized exports by making a best-effort attempt to extract
conversations from JSON or plain text files.

This is the adapter of last resort — it tries common structural patterns
and produces something reasonable even from unfamiliar formats.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from conversation_to_md.core.models import Conversation, Message
from conversation_to_md.utils.normalize import (
    clean_content,
    iso_to_datetime,
    sanitize_id,
    strip_html,
    unix_to_datetime,
)


def parse(extracted_dir: Path) -> List[Conversation]:
    """Best-effort parse of unknown export files."""
    conversations: List[Conversation] = []

    # Try JSON files
    for json_file in extracted_dir.rglob("*.json"):
        convos = _try_json(json_file)
        conversations.extend(convos)

    if conversations:
        return conversations

    # Try HTML files
    for html_file in extracted_dir.rglob("*.html"):
        conv = _try_html(html_file)
        if conv is not None:
            conversations.append(conv)

    if conversations:
        return conversations

    # Try plain text files
    for txt_file in extracted_dir.rglob("*.txt"):
        conv = _try_text(txt_file)
        if conv is not None:
            conversations.append(conv)

    return conversations


def _try_json(filepath: Path) -> List[Conversation]:
    """Attempt to parse a JSON file as conversation data."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []

    if not isinstance(data, (list, dict)):
        return []

    items = data if isinstance(data, list) else [data]
    conversations = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        conv = _extract_generic_conversation(item, filepath.stem, idx)
        if conv is not None:
            conversations.append(conv)

    return conversations


def _extract_generic_conversation(
    raw: dict, fallback_title: str, index: int
) -> Optional[Conversation]:
    """Try to build a Conversation from a generic dict structure."""
    # Look for messages under common key names
    message_keys = ["messages", "turns", "chat_messages", "entries", "data", "items"]
    raw_messages = None
    for key in message_keys:
        if key in raw and isinstance(raw[key], list):
            raw_messages = raw[key]
            break

    if raw_messages is None:
        return None

    messages = []
    for raw_msg in raw_messages:
        msg = _extract_generic_message(raw_msg)
        if msg is not None:
            messages.append(msg)

    if not messages:
        return None

    conv_id = sanitize_id(
        raw.get("id") or raw.get("uuid") or raw.get("conversation_id") or str(index)
    )
    title = (
        raw.get("title") or raw.get("name") or raw.get("subject") or fallback_title
    )
    created_at = iso_to_datetime(raw.get("created_at")) or unix_to_datetime(
        raw.get("create_time") or raw.get("timestamp")
    )

    return Conversation(
        id=conv_id,
        source="unknown",
        title=title,
        created_at=created_at,
        messages=messages,
    )


def _extract_generic_message(raw_msg) -> Optional[Message]:
    """Try to build a Message from a generic dict."""
    if not isinstance(raw_msg, dict):
        if isinstance(raw_msg, str):
            return Message(role="unknown", content=raw_msg)
        return None

    # Detect role
    role_raw = (
        raw_msg.get("role", "")
        or raw_msg.get("sender", "")
        or raw_msg.get("author", "")
        or raw_msg.get("from", "")
    )
    role_map = {
        "user": "user",
        "human": "user",
        "assistant": "assistant",
        "ai": "assistant",
        "bot": "assistant",
        "model": "assistant",
        "system": "system",
        "grok": "assistant",
    }
    role = role_map.get(str(role_raw).lower(), "user" if "user" in str(role_raw).lower() else "assistant")

    # Detect content
    text = ""
    for key in ["content", "text", "message", "body", "value"]:
        if key in raw_msg:
            text = clean_content(raw_msg[key])
            if text:
                break

    if not text:
        return None

    created_at = iso_to_datetime(
        raw_msg.get("created_at") or raw_msg.get("timestamp_str")
    ) or unix_to_datetime(
        raw_msg.get("timestamp") or raw_msg.get("create_time")
    )

    return Message(role=role, content=text, created_at=created_at)


def _try_html(filepath: Path) -> Optional[Conversation]:
    """Attempt to extract a conversation from an HTML file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return None

    text = strip_html(content)
    if len(text) < 50:
        return None

    return Conversation(
        id=sanitize_id(filepath.stem),
        source="unknown",
        title=filepath.stem,
        messages=[Message(role="user", content=text)],
        metadata={"original_format": "html"},
    )


def _try_text(filepath: Path) -> Optional[Conversation]:
    """Attempt to extract a conversation from a plain text file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return None

    if len(content.strip()) < 50:
        return None

    return Conversation(
        id=sanitize_id(filepath.stem),
        source="unknown",
        title=filepath.stem,
        messages=[Message(role="user", content=content.strip())],
        metadata={"original_format": "text"},
    )
