#!/usr/bin/env python3
"""
Build or update a compact media callout block in markdown notes.

Behavior:
- Inserts a "[!media]" callout near top of note (before first thematic rule) if missing.
- Replaces existing media block between marker comments if present.
- Handles missing links gracefully with "Coming soon" text.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

START = "<!-- MEDIA_CALLOUT_START -->"
END = "<!-- MEDIA_CALLOUT_END -->"
DISCLAIMER = "If a link is missing here, it has not been published yet."


def _link_or_placeholder(label: str, url: str) -> str:
    url = (url or "").strip()
    if url:
        return f"[{label}]({url})"
    return "_Coming soon_"


def build_block(
    podcast_a_url: str,
    podcast_b_url: str,
    audio_url: str,
    drive_url: str,
    axioms_url: str,
    podcast_a_label: str,
    podcast_b_label: str,
    audio_label: str,
    drive_label: str,
    axioms_label: str,
) -> str:
    podcast_a = _link_or_placeholder(podcast_a_label, podcast_a_url)
    podcast_b = _link_or_placeholder(podcast_b_label, podcast_b_url)
    audio = _link_or_placeholder(audio_label, audio_url)
    drive = _link_or_placeholder(drive_label, drive_url)
    axioms = _link_or_placeholder(axioms_label, axioms_url)

    lines = [
        START,
        "> [!info]- Listen, Watch and Download",
        ">",
        "> **Podcasts**",
        f"> - Debate Format: {podcast_a}",
        f"> - Deep Dive: {podcast_b}",
        ">",
        "> **Audio**",
        f"> - Narration: {audio}",
        ">",
        "> **Downloads**",
        f"> - Drive / Files: {drive}",
        ">",
        "> **Canonical**",
        f"> - Axiom Index: {axioms}",
        ">",
        f"> *{DISCLAIMER}*",
        END,
        "",
    ]
    return "\n".join(lines)


def upsert_media_block(note_text: str, block: str) -> str:
    if START in note_text and END in note_text:
        before, rest = note_text.split(START, 1)
        _, after = rest.split(END, 1)
        cleaned = before.rstrip() + "\n\n" + after.lstrip("\n")
        note_text = cleaned

    # Preferred insertion: immediately after structural index callout.
    lines = note_text.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith("> [!abstract]-") and "Structural Index" in line:
            start_idx = i
            break
    if start_idx is not None:
        end_idx = start_idx + 1
        while end_idx < len(lines):
            ln = lines[end_idx]
            if ln.startswith(">") or not ln.strip():
                end_idx += 1
                continue
            break
        insert_at = end_idx
        block_lines = block.strip().splitlines()
        new_lines = lines[:insert_at] + [""] + block_lines + [""] + lines[insert_at:]
        return "\n".join(new_lines).rstrip() + "\n"

    # Fallback insertion: after YAML frontmatter if present.
    if note_text.startswith("---\n"):
        close_idx = note_text.find("\n---\n", 4)
        if close_idx != -1:
            insert_at = close_idx + len("\n---\n")
            return note_text[:insert_at].rstrip() + "\n\n" + block.strip() + "\n\n" + note_text[insert_at:].lstrip("\n")

    return note_text.rstrip() + "\n\n" + block.strip() + "\n"


def run(
    note_path: Path,
    podcast_a_url: str,
    podcast_b_url: str,
    audio_url: str,
    drive_url: str,
    podcast_a_label: str,
    podcast_b_label: str,
    audio_label: str,
    drive_label: str,
    write: bool,
    axioms_url: str = "",
    axioms_label: str = "Canonical Axioms",
) -> str:
    if not note_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    current = note_path.read_text(encoding="utf-8", errors="replace")
    block = build_block(
        podcast_a_url=podcast_a_url,
        podcast_b_url=podcast_b_url,
        audio_url=audio_url,
        drive_url=drive_url,
        axioms_url=axioms_url,
        podcast_a_label=podcast_a_label,
        podcast_b_label=podcast_b_label,
        audio_label=audio_label,
        drive_label=drive_label,
        axioms_label=axioms_label,
    )
    updated = upsert_media_block(current, block)

    if write:
        note_path.write_text(updated, encoding="utf-8")

    return block


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and insert media callout block")
    parser.add_argument("--note", required=True, help="Path to markdown note")
    parser.add_argument("--podcast-a-url", default="", help="Podcast A URL")
    parser.add_argument("--podcast-b-url", default="", help="Podcast B URL")
    parser.add_argument("--audio-url", default="", help="Regular narration audio URL")
    parser.add_argument("--drive-url", default="", help="Drive/download folder URL")
    parser.add_argument("--axioms-url", default="", help="Canonical axioms index URL")
    parser.add_argument("--podcast-a-label", default="Debate Cut")
    parser.add_argument("--podcast-b-label", default="Deep Dive")
    parser.add_argument("--audio-label", default="Word-for-word Narration")
    parser.add_argument("--drive-label", default="Download Folder")
    parser.add_argument("--axioms-label", default="Canonical Axioms")
    parser.add_argument("--dry-run", action="store_true", help="Print block only, do not write")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    note = Path(args.note)
    block = run(
        note_path=note,
        podcast_a_url=args.podcast_a_url,
        podcast_b_url=args.podcast_b_url,
        audio_url=args.audio_url,
        drive_url=args.drive_url,
        axioms_url=args.axioms_url,
        podcast_a_label=args.podcast_a_label,
        podcast_b_label=args.podcast_b_label,
        audio_label=args.audio_label,
        drive_label=args.drive_label,
        axioms_label=args.axioms_label,
        write=not args.dry_run,
    )
    print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
