"""
Grok (X / Twitter) export adapter.

Handles Grok conversation exports from the X platform data export.
The exact format depends on the export version, but typically includes
JSON files with conversation threads and message objects.
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
    unix_to_datetime,
)


def parse(extracted_dir: Path) -> List[Conversation]:
    """Parse Grok/X export files into canonical conversations."""
    conversations: List[Conversation] = []

    for json_file in extracted_dir.rglob("*.json"):
        convos = _parse_json_file(json_file)
        conversations.extend(convos)

    return conversations


def _parse_json_file(filepath: Path) -> List[Conversation]:
    """Parse a single Grok JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []

    if not isinstance(data, list):
        data = [data]

    conversations: List[Conversation] = []

    # Check if this is a flat list of messages (grouped by conversation_id)
    # or a list of conversation objects
    if data and isinstance(data[0], dict):
        if "conversation_id" in data[0] and "messages" not in data[0]:
            # Flat message list — group by conversation_id
            return _parse_flat_messages(data)
        else:
            # Conversation objects
            for raw_conv in data:
                conv = _parse_conversation(raw_conv)
                if conv is not None:
                    conversations.append(conv)

    return conversations


def _parse_conversation(raw: dict) -> Optional[Conversation]:
    """Convert a single Grok conversation object."""
    if not isinstance(raw, dict):
        return None

    conv_id = sanitize_id(
        raw.get("id") or raw.get("conversation_id") or raw.get("thread_id")
    )
    title = raw.get("title") or raw.get("name") or "Grok Conversation"
    created_at = iso_to_datetime(raw.get("created_at")) or unix_to_datetime(
        raw.get("create_time") or raw.get("timestamp")
    )

    raw_messages = raw.get("messages", []) or raw.get("turns", [])
    messages = []
    for raw_msg in raw_messages:
        msg = _parse_message(raw_msg)
        if msg is not None:
            messages.append(msg)

    if not messages:
        return None

    return Conversation(
        id=conv_id,
        source="grok",
        title=title,
        created_at=created_at,
        messages=messages,
    )


def _parse_message(raw_msg: dict) -> Optional[Message]:
    """Parse a single Grok message."""
    if not isinstance(raw_msg, dict):
        return None

    role_raw = (
        raw_msg.get("role", "")
        or raw_msg.get("sender", "")
        or raw_msg.get("author", "")
    )
    role_map = {
        "user": "user",
        "human": "user",
        "grok": "assistant",
        "assistant": "assistant",
        "model": "assistant",
        "system": "system",
    }
    role = role_map.get(role_raw.lower(), "assistant")

    text = ""
    if "text" in raw_msg:
        text = clean_content(raw_msg["text"])
    elif "content" in raw_msg:
        text = clean_content(raw_msg["content"])
    elif "message" in raw_msg:
        text = clean_content(raw_msg["message"])

    if not text:
        return None

    created_at = iso_to_datetime(raw_msg.get("created_at")) or unix_to_datetime(
        raw_msg.get("timestamp") or raw_msg.get("create_time")
    )

    return Message(role=role, content=text, created_at=created_at)


def _parse_flat_messages(raw_messages: List[dict]) -> List[Conversation]:
    """
    Handle Grok exports where messages are a flat list with conversation_id fields.
    Group them into conversations.
    """
    from collections import defaultdict

    grouped: dict = defaultdict(list)
    for msg in raw_messages:
        if isinstance(msg, dict):
            cid = msg.get("conversation_id", "unknown")
            grouped[cid].append(msg)

    conversations = []
    for cid, msgs in grouped.items():
        # Sort by timestamp if available
        msgs.sort(
            key=lambda m: m.get("timestamp") or m.get("created_at") or ""
        )

        messages = []
        for raw_msg in msgs:
            m = _parse_message(raw_msg)
            if m is not None:
                messages.append(m)

        if messages:
            first_ts = None
            for m in msgs:
                ts = iso_to_datetime(m.get("created_at")) or unix_to_datetime(
                    m.get("timestamp")
                )
                if ts:
                    first_ts = ts
                    break

            conversations.append(
                Conversation(
                    id=sanitize_id(cid),
                    source="grok",
                    title="Grok Conversation",
                    created_at=first_ts,
                    messages=messages,
                )
            )

    return conversations
