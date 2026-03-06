"""
Markdown renderer: converts canonical Conversation objects into .md files.

Output contract:
  - YAML frontmatter with source, conversation_id, created_at
  - H1 title
  - Each message as H2 with role emoji (toggleable)
  - Attachments listed in a sub-section
  - One file per conversation
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from conversation_to_md.core.models import Attachment, Conversation, Message


@dataclass
class RenderOptions:
    """User-toggleable rendering settings."""

    include_timestamps: bool = True
    include_system_messages: bool = False
    emoji_headers: bool = True
    output_structure: str = "structured"  # "flat" or "structured"


ROLE_EMOJI = {
    "user": "\U0001f9d1",       # person
    "assistant": "\U0001f916",  # robot
    "system": "\u2699\ufe0f",   # gear
    "tool": "\U0001f527",       # wrench
}

ROLE_LABEL = {
    "user": "User",
    "assistant": "Assistant",
    "system": "System",
    "tool": "Tool",
}


def render_conversation(conv: Conversation, options: RenderOptions) -> str:
    """Render a single Conversation into a Markdown string."""
    parts: List[str] = []

    # --- YAML frontmatter ---
    parts.append("---")
    parts.append(f"source: {conv.source}")
    parts.append(f"conversation_id: {conv.id}")
    if conv.created_at:
        parts.append(f"created_at: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if conv.metadata:
        for key, value in conv.metadata.items():
            parts.append(f"{key}: {value}")
    parts.append("---")
    parts.append("")

    # --- Title ---
    title = conv.title or "Untitled Conversation"
    parts.append(f"# {title}")
    parts.append("")

    # --- Messages ---
    for msg in conv.messages:
        if msg.role == "system" and not options.include_system_messages:
            continue

        header = _message_header(msg, options)
        parts.append(header)
        parts.append("")

        if options.include_timestamps and msg.created_at:
            parts.append(f"*{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}*")
            parts.append("")

        if msg.content:
            parts.append(msg.content)
            parts.append("")

        if msg.attachments:
            parts.append("**Attachments:**")
            for att in msg.attachments:
                parts.append(f"- [{att.name}] ({att.type}: {att.reference})")
            parts.append("")

    return "\n".join(parts)


def _message_header(msg: Message, options: RenderOptions) -> str:
    """Build the H2 header line for a message."""
    label = ROLE_LABEL.get(msg.role, msg.role.title())
    if options.emoji_headers:
        emoji = ROLE_EMOJI.get(msg.role, "\u2753")
        return f"## {emoji} {label}"
    return f"## {label}"


def write_conversations(
    conversations: List[Conversation],
    output_dir: Path,
    options: RenderOptions,
) -> List[Path]:
    """
    Write each conversation to a separate .md file.

    Returns the list of paths written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    for idx, conv in enumerate(conversations):
        md_text = render_conversation(conv, options)
        filename = _safe_filename(conv, idx)

        if options.output_structure == "structured":
            folder = output_dir / conv.source
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / filename
        else:
            path = output_dir / filename

        path.write_text(md_text, encoding="utf-8")
        written.append(path)

    return written


def _safe_filename(conv: Conversation, index: int) -> str:
    """Generate a filesystem-safe filename from a conversation."""
    title = conv.title or "untitled"
    # Strip characters that are problematic in filenames
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
    safe = safe.strip()[:80]
    if not safe:
        safe = "untitled"

    date_prefix = ""
    if conv.created_at:
        date_prefix = conv.created_at.strftime("%Y-%m-%d") + "_"

    return f"{date_prefix}{safe}_{index:04d}.md"
