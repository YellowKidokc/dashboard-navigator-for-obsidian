"""Tests for normalization utilities."""

from datetime import datetime, timezone

from conversation_to_md.utils.normalize import (
    clean_content,
    iso_to_datetime,
    sanitize_id,
    strip_html,
    unix_to_datetime,
)


def test_unix_to_datetime():
    dt = unix_to_datetime(1700000000.0)
    assert dt is not None
    assert dt.year == 2023

    assert unix_to_datetime(None) is None
    assert unix_to_datetime("garbage") is None


def test_iso_to_datetime():
    dt = iso_to_datetime("2025-01-15T10:30:00Z")
    assert dt is not None
    assert dt.year == 2025
    assert dt.month == 1
    assert dt.tzinfo is not None

    dt2 = iso_to_datetime("2025-01-15T10:30:00+00:00")
    assert dt2 is not None

    assert iso_to_datetime(None) is None
    assert iso_to_datetime("") is None
    assert iso_to_datetime("not-a-date") is None


def test_strip_html():
    assert strip_html("<p>Hello</p>") == "Hello"
    assert strip_html("&amp; test") == "& test"
    assert strip_html("<div><span>nested</span></div>") == "nested"


def test_clean_content():
    assert clean_content(None) == ""
    assert clean_content("  hello  ") == "hello"
    assert clean_content(["part1", "part2"]) == "part1\npart2"
    assert clean_content([{"text": "from dict"}]) == "from dict"


def test_sanitize_id():
    assert sanitize_id(None) == "unknown"
    assert sanitize_id("") == "unknown"
    assert sanitize_id("abc-123") == "abc-123"
