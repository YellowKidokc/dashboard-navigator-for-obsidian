"""Tests for the Markdown renderer."""

from datetime import datetime, timezone

from conversation_to_md.core.models import Attachment, Conversation, Message
from conversation_to_md.core.renderer import RenderOptions, render_conversation


def _make_conversation(**kwargs):
    defaults = dict(
        id="test-1",
        source="chatgpt",
        title="Test Conversation",
        created_at=datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        messages=[
            Message(
                role="user",
                content="What is 2+2?",
                created_at=datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            ),
            Message(
                role="assistant",
                content="2+2 equals 4.",
                created_at=datetime(2025, 6, 15, 12, 0, 5, tzinfo=timezone.utc),
            ),
        ],
    )
    defaults.update(kwargs)
    return Conversation(**defaults)


def test_basic_render():
    conv = _make_conversation()
    options = RenderOptions()
    md = render_conversation(conv, options)

    assert "---" in md
    assert "source: chatgpt" in md
    assert "conversation_id: test-1" in md
    assert "# Test Conversation" in md
    assert "What is 2+2?" in md
    assert "2+2 equals 4." in md


def test_emoji_headers():
    conv = _make_conversation()

    md_with = render_conversation(conv, RenderOptions(emoji_headers=True))
    assert "\U0001f9d1" in md_with  # person emoji
    assert "\U0001f916" in md_with  # robot emoji

    md_without = render_conversation(conv, RenderOptions(emoji_headers=False))
    assert "\U0001f9d1" not in md_without
    assert "## User" in md_without
    assert "## Assistant" in md_without


def test_no_timestamps():
    conv = _make_conversation()
    md = render_conversation(conv, RenderOptions(include_timestamps=False))
    # Frontmatter still has created_at, but per-message italic timestamps
    # like *2025-06-15 12:00:00* should be absent from the message body.
    lines_with_inline_ts = [
        line for line in md.splitlines()
        if line.startswith("*2025-06-15")
    ]
    assert len(lines_with_inline_ts) == 0


def test_system_messages_excluded_by_default():
    conv = _make_conversation(
        messages=[
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hi"),
        ]
    )
    md = render_conversation(conv, RenderOptions(include_system_messages=False))
    assert "You are helpful." not in md
    assert "Hi" in md


def test_system_messages_included():
    conv = _make_conversation(
        messages=[
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hi"),
        ]
    )
    md = render_conversation(conv, RenderOptions(include_system_messages=True))
    assert "You are helpful." in md


def test_attachments():
    conv = _make_conversation(
        messages=[
            Message(
                role="user",
                content="See this image.",
                attachments=[
                    Attachment(type="image", name="photo.png", reference="img_001")
                ],
            )
        ]
    )
    md = render_conversation(conv, RenderOptions())
    assert "Attachments:" in md
    assert "photo.png" in md
