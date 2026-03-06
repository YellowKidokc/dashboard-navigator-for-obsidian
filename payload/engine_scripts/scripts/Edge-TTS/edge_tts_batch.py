#!/usr/bin/env python3
"""
Edge TTS Batch Processor
========================
Converts text/markdown files in input/ to MP3 using Microsoft Edge TTS.
Optionally merges all outputs into one master audio file.

Usage:
    python edge_tts_batch.py              # Process all files
    python edge_tts_batch.py --dry-run    # Preview only
"""

import os
import sys
import re
import asyncio
import pathlib
import datetime
import struct

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"


# ── Config parser ──────────────────────────────────────────────

def parse_config(path):
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    return cfg


# ── Markdown stripping ─────────────────────────────────────────

def strip_markdown(text):
    """Remove markdown formatting for cleaner TTS output."""
    # Remove YAML frontmatter
    text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Convert links to just text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove wikilinks, keep display text
    text = re.sub(r'\[\[([^|\]]+\|)?([^\]]+)\]\]', r'\2', text)
    # Remove headers markers but keep text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Remove LaTeX blocks (they sound terrible in TTS)
    text = re.sub(r'\$\$[^$]+\$\$', ' (equation) ', text, flags=re.DOTALL)
    text = re.sub(r'\$[^$]+\$', ' (equation) ', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── MP3 silence generator ─────────────────────────────────────

def generate_silence_mp3(duration_sec, output_path):
    """Generate a silent MP3 file using raw MPEG frames.
    No ffmpeg or pydub needed — writes valid MP3 silence directly."""
    # One MPEG1 Layer3 128kbps 44100Hz stereo frame = 417 bytes, ~26.12ms
    # Silent frame (all zeros in audio data)
    frame_header = bytes([0xFF, 0xFB, 0x90, 0x00])  # MPEG1, Layer3, 128kbps, 44100Hz, stereo
    frame_size = 417  # bytes per frame at 128kbps/44100Hz
    frame_duration = 0.02612  # seconds per frame

    num_frames = int(duration_sec / frame_duration) + 1
    silent_frame = frame_header + b'\x00' * (frame_size - len(frame_header))

    with open(output_path, 'wb') as f:
        for _ in range(num_frames):
            f.write(silent_frame)


# ── MP3 concatenation (no ffmpeg needed) ───────────────────────

def concatenate_mp3(file_list, output_path, silence_gap=1.5):
    """Concatenate MP3 files with silence gaps between them.
    Works by binary concatenation — valid for MP3 streams."""
    silence_path = output_path.parent / "_temp_silence.mp3"

    if silence_gap > 0:
        generate_silence_mp3(silence_gap, silence_path)

    with open(output_path, 'wb') as out:
        for i, mp3_path in enumerate(file_list):
            if i > 0 and silence_gap > 0 and silence_path.exists():
                out.write(silence_path.read_bytes())
            out.write(mp3_path.read_bytes())

    # Cleanup temp
    if silence_path.exists():
        silence_path.unlink()


# ── SRT merge ──────────────────────────────────────────────────

def merge_srt_files(srt_list, output_path):
    """Merge multiple SRT files with sequential numbering."""
    all_entries = []
    time_offset = 0.0

    for srt_path in srt_list:
        if not srt_path.exists():
            continue
        content = srt_path.read_text(encoding="utf-8")
        blocks = content.strip().split("\n\n")

        max_end = 0.0
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            # Parse timestamp line
            ts_line = lines[1]
            match = re.match(
                r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
                ts_line
            )
            if not match:
                continue
            g = [int(x) for x in match.groups()]
            start = g[0]*3600 + g[1]*60 + g[2] + g[3]/1000 + time_offset
            end = g[4]*3600 + g[5]*60 + g[6] + g[7]/1000 + time_offset
            max_end = max(max_end, end)
            text = "\n".join(lines[2:])
            all_entries.append((start, end, text))

        time_offset = max_end + 1.5  # gap between files

    # Write merged SRT
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (start, end, text) in enumerate(all_entries, 1):
            f.write(f"{i}\n")
            f.write(f"{_fmt_srt_time(start)} --> {_fmt_srt_time(end)}\n")
            f.write(f"{text}\n\n")


def _fmt_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ── Main TTS processing ───────────────────────────────────────

async def convert_file(filepath, voice, rate, volume, pitch, output_dir, subtitles=True):
    """Convert a single text/md file to MP3 using edge-tts."""
    import edge_tts

    text = filepath.read_text(encoding="utf-8")

    # Strip markdown if .md file
    if filepath.suffix.lower() == ".md":
        text = strip_markdown(text)

    if not text.strip():
        print(f"  SKIP (empty): {filepath.name}")
        return None, None

    # Build output filename
    stem = filepath.stem
    mp3_path = output_dir / f"{stem}.mp3"
    srt_path = output_dir / f"{stem}.srt"

    # Build edge-tts communicate object
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        volume=volume,
        pitch=pitch
    )

    # Generate audio
    sub_maker = edge_tts.SubMaker() if subtitles else None

    with open(mp3_path, "wb") as mp3_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary") and sub_maker is not None:
                sub_maker.feed(chunk)

    # Write subtitles
    if sub_maker is not None and subtitles:
        srt_content = sub_maker.get_srt()
        srt_path.write_text(srt_content, encoding="utf-8")
    else:
        srt_path = None

    size_kb = mp3_path.stat().st_size / 1024
    print(f"  OK : {filepath.name} -> {mp3_path.name} ({size_kb:.0f} KB)")

    return mp3_path, srt_path


async def main():
    dry_run = "--dry-run" in sys.argv

    # Parse config
    cfg = parse_config(CONFIG_PATH)
    voice = cfg.get("VOICE", "en-US-BrianMultilingualNeural")
    rate = cfg.get("RATE", "+0%")
    volume = cfg.get("VOLUME", "+0%")
    pitch = cfg.get("PITCH", "+0Hz")
    do_subtitles = cfg.get("SUBTITLES", "yes").lower() == "yes"
    do_merge = cfg.get("MERGE", "yes").lower() == "yes"
    master_name = cfg.get("MASTER_FILENAME", "theophysics_paper.mp3")
    silence_gap = float(cfg.get("SILENCE_GAP", "1.5"))

    # Find input files
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    extensions = {".txt", ".md"}
    input_files = sorted([
        f for f in INPUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ])

    if not input_files:
        print("  No .txt or .md files found in input/ folder.")
        print("  Drop your text files there and run again.")
        return

    # Display plan
    print(f"  Voice    : {voice}")
    print(f"  Rate     : {rate}")
    print(f"  Volume   : {volume}")
    print(f"  Pitch    : {pitch}")
    print(f"  Subs     : {'yes' if do_subtitles else 'no'}")
    print(f"  Merge    : {'yes' if do_merge else 'no'}")
    if do_merge:
        print(f"  Master   : {master_name}")
        print(f"  Gap      : {silence_gap}s between sections")
    print()
    print(f"  Files to process ({len(input_files)}):")
    for i, f in enumerate(input_files, 1):
        size = f.stat().st_size
        lines = len(f.read_text(encoding="utf-8").splitlines())
        print(f"    {i:3d}. {f.name}  ({size:,} bytes, {lines} lines)")
    print()

    if dry_run:
        print("  DRY RUN — no files will be generated.")
        return

    # Process each file
    print("  Processing ...")
    print()

    mp3_files = []
    srt_files = []

    for filepath in input_files:
        try:
            mp3_path, srt_path = await convert_file(
                filepath, voice, rate, volume, pitch,
                OUTPUT_DIR, subtitles=do_subtitles
            )
            if mp3_path:
                mp3_files.append(mp3_path)
            if srt_path:
                srt_files.append(srt_path)
        except Exception as e:
            print(f"  ERR: {filepath.name} — {e}")

    # Merge if requested
    if do_merge and len(mp3_files) > 1:
        print()
        print(f"  Merging {len(mp3_files)} files into {master_name} ...")
        master_path = OUTPUT_DIR / master_name
        concatenate_mp3(mp3_files, master_path, silence_gap=silence_gap)
        master_size = master_path.stat().st_size / 1024
        print(f"  MASTER : {master_path.name} ({master_size:.0f} KB)")

        # Merge subtitles too
        if srt_files:
            master_srt = OUTPUT_DIR / master_name.replace(".mp3", ".srt")
            merge_srt_files(srt_files, master_srt)
            print(f"  SUBS   : {master_srt.name}")

    elif do_merge and len(mp3_files) == 1:
        # Just one file, copy as master
        master_path = OUTPUT_DIR / master_name
        import shutil
        shutil.copy2(mp3_files[0], master_path)
        print(f"\n  Single file copied as master: {master_name}")

    # Summary
    print()
    total_size = sum(f.stat().st_size for f in mp3_files) / 1024
    print(f"  Total: {len(mp3_files)} MP3 files, {total_size:.0f} KB")


if __name__ == "__main__":
    asyncio.run(main())
