"""
Main conversion pipeline.

Orchestrates: ZIP extract -> detect source -> adapter parse -> render markdown.
This is the single entry point for the entire conversion process.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from conversation_to_md.adapters import chatgpt, claude, gemini, generic, grok
from conversation_to_md.core.detect import detect_source
from conversation_to_md.core.models import Conversation
from conversation_to_md.core.renderer import RenderOptions, write_conversations
from conversation_to_md.utils.unzip import extract_zip, extract_zip_from_bytes

# Adapter registry: source key -> parse function
ADAPTERS = {
    "chatgpt": chatgpt.parse,
    "claude": claude.parse,
    "gemini": gemini.parse,
    "grok": grok.parse,
    "unknown": generic.parse,
}


def convert_zip(
    zip_path: Path,
    output_dir: Path,
    options: Optional[RenderOptions] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[Path], str]:
    """
    Full pipeline: ZIP file -> Markdown files.

    Args:
        zip_path: Path to the ZIP file to convert
        output_dir: Directory where .md files will be written
        options: Rendering options (defaults to sensible defaults)
        progress_callback: Optional function called with status messages

    Returns:
        Tuple of (list of written file paths, detected source name)
    """
    if options is None:
        options = RenderOptions()

    def _log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    _log("Extracting ZIP archive...")
    extracted_dir = extract_zip(zip_path)

    try:
        return _process_extracted(extracted_dir, output_dir, options, _log)
    finally:
        # Clean up temp directory
        shutil.rmtree(extracted_dir, ignore_errors=True)


def convert_zip_bytes(
    data: bytes,
    output_dir: Path,
    options: Optional[RenderOptions] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[List[Path], str]:
    """
    Full pipeline from raw bytes (e.g. Streamlit upload).

    Same as convert_zip but accepts bytes instead of a file path.
    """
    if options is None:
        options = RenderOptions()

    def _log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    _log("Extracting ZIP archive...")
    extracted_dir = extract_zip_from_bytes(data)

    try:
        return _process_extracted(extracted_dir, output_dir, options, _log)
    finally:
        shutil.rmtree(extracted_dir, ignore_errors=True)


def _process_extracted(
    extracted_dir: Path,
    output_dir: Path,
    options: RenderOptions,
    log: Callable[[str], None],
) -> Tuple[List[Path], str]:
    """Process an already-extracted directory through detection, parsing, rendering."""
    log("Detecting source provider...")
    source = detect_source(extracted_dir)
    log(f"Detected source: {source}")

    adapter = ADAPTERS.get(source, generic.parse)
    log(f"Parsing conversations with {source} adapter...")
    conversations: List[Conversation] = adapter(extracted_dir)
    log(f"Found {len(conversations)} conversation(s)")

    if not conversations:
        return [], source

    log("Rendering Markdown files...")
    written = write_conversations(conversations, output_dir, options)
    log(f"Wrote {len(written)} Markdown file(s)")

    return written, source
