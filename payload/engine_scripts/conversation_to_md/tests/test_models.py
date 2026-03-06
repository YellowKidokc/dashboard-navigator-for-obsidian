"""Tests for the canonical data model."""

from datetime import datetime, timezone

from conversation_to_md.core.models import Attachment, Conversation, Message


def test_message_defaults():
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.created_at is None
    assert msg.attachments == []


def test_conversation_defaults():
    conv = Conversation(id="1", source="chatgpt", title="Test")
    assert conv.id == "1"
    assert conv.source == "chatgpt"
    assert conv.title == "Test"
    assert conv.created_at is None
    assert conv.messages == []
    assert conv.metadata == {}


def test_conversation_with_messages():
    msgs = [
        Message(role="user", content="Hi"),
        Message(
            role="assistant",
            content="Hello!",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
    ]
    conv = Conversation(
        id="abc",
        source="claude",
        title="Greeting",
        messages=msgs,
    )
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[1].created_at is not None


def test_attachment():
    att = Attachment(type="image", name="photo.png", reference="/tmp/photo.png")
    assert att.type == "image"
    assert att.name == "photo.png"
