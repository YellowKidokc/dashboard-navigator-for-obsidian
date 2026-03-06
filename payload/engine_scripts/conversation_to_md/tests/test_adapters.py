"""Tests for provider adapters using synthetic test data."""

import json
import tempfile
import zipfile
from pathlib import Path

from conversation_to_md.adapters import chatgpt, claude, gemini, grok, generic
from conversation_to_md.core.detect import detect_source


def _write_json(directory: Path, filename: str, data) -> Path:
    filepath = directory / filename
    filepath.write_text(json.dumps(data), encoding="utf-8")
    return filepath


# ---- ChatGPT ----

def _chatgpt_sample():
    """Minimal ChatGPT conversations.json structure."""
    return [
        {
            "id": "conv-001",
            "title": "Math Help",
            "create_time": 1700000000.0,
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["msg-1"],
                    "message": None,
                },
                "msg-1": {
                    "id": "msg-1",
                    "parent": "root",
                    "children": ["msg-2"],
                    "message": {
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["What is 2+2?"]},
                        "create_time": 1700000001.0,
                    },
                },
                "msg-2": {
                    "id": "msg-2",
                    "parent": "msg-1",
                    "children": [],
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"content_type": "text", "parts": ["4"]},
                        "create_time": 1700000002.0,
                    },
                },
            },
        }
    ]


def test_chatgpt_detection():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "conversations.json", _chatgpt_sample())
        assert detect_source(tmp_path) == "chatgpt"


def test_chatgpt_parse():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "conversations.json", _chatgpt_sample())
        convos = chatgpt.parse(tmp_path)

        assert len(convos) == 1
        conv = convos[0]
        assert conv.source == "chatgpt"
        assert conv.title == "Math Help"
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "What is 2+2?"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[1].content == "4"


# ---- Claude ----

def _claude_sample():
    return [
        {
            "uuid": "conv-c-001",
            "name": "Python Question",
            "created_at": "2025-01-15T10:00:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-c-1",
                    "sender": "human",
                    "text": "How do I read a file in Python?",
                    "created_at": "2025-01-15T10:00:01Z",
                },
                {
                    "uuid": "msg-c-2",
                    "sender": "assistant",
                    "text": "Use open() with a context manager.",
                    "created_at": "2025-01-15T10:00:05Z",
                },
            ],
        }
    ]


def test_claude_detection():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "conversations.json", _claude_sample())
        assert detect_source(tmp_path) == "claude"


def test_claude_parse():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "claude_export.json", _claude_sample())
        convos = claude.parse(tmp_path)

        assert len(convos) == 1
        conv = convos[0]
        assert conv.source == "claude"
        assert conv.title == "Python Question"
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"


# ---- Gemini ----

def _gemini_json_sample():
    return [
        {
            "id": "gem-001",
            "title": "Travel Planning",
            "messages": [
                {"role": "user", "text": "Plan a trip to Tokyo"},
                {"role": "model", "text": "Here is a 5-day itinerary for Tokyo..."},
            ],
        }
    ]


def test_gemini_detection_by_folder():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        gemini_dir = tmp_path / "Gemini Apps"
        gemini_dir.mkdir()
        _write_json(gemini_dir, "conversations.json", _gemini_json_sample())
        assert detect_source(tmp_path) == "gemini"


def test_gemini_json_parse():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "gemini_export.json", _gemini_json_sample())
        convos = gemini.parse(tmp_path)

        assert len(convos) == 1
        conv = convos[0]
        assert conv.source == "gemini"
        assert conv.title == "Travel Planning"
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"


# ---- Grok ----

def _grok_sample():
    return [
        {
            "conversation_id": "grok-001",
            "title": "Grok Chat",
            "messages": [
                {"role": "user", "text": "Tell me a joke"},
                {"role": "grok", "text": "Why did the chicken cross the road?"},
            ],
        }
    ]


def test_grok_parse():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "grok_conversations.json", _grok_sample())
        convos = grok.parse(tmp_path)

        assert len(convos) == 1
        conv = convos[0]
        assert conv.source == "grok"
        assert len(conv.messages) == 2
        assert conv.messages[1].role == "assistant"


# ---- Generic ----

def _generic_sample():
    return [
        {
            "id": "gen-001",
            "title": "Unknown Chat",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "ai", "content": "Hi there!"},
            ],
        }
    ]


def test_generic_parse():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_json(tmp_path, "chat.json", _generic_sample())
        convos = generic.parse(tmp_path)

        assert len(convos) == 1
        conv = convos[0]
        assert conv.source == "unknown"
        assert len(conv.messages) == 2


# ---- Full Pipeline ----

def test_full_pipeline_chatgpt():
    """End-to-end: create a ZIP, run pipeline, check output."""
    from conversation_to_md.core.pipeline import convert_zip

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create a ZIP with ChatGPT data
        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("conversations.json", json.dumps(_chatgpt_sample()))

        output_dir = tmp_path / "output"
        written, source = convert_zip(zip_path, output_dir)

        assert source == "chatgpt"
        assert len(written) == 1
        assert written[0].exists()

        content = written[0].read_text(encoding="utf-8")
        assert "source: chatgpt" in content
        assert "What is 2+2?" in content
        assert "4" in content


def test_full_pipeline_claude():
    """End-to-end with Claude data."""
    from conversation_to_md.core.pipeline import convert_zip

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        zip_path = tmp_path / "claude_export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("claude_data.json", json.dumps(_claude_sample()))

        output_dir = tmp_path / "output"
        written, source = convert_zip(zip_path, output_dir)

        assert source == "claude"
        assert len(written) == 1

        content = written[0].read_text(encoding="utf-8")
        assert "source: claude" in content
        assert "Python Question" in content
