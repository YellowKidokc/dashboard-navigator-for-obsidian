"""
CLI entry point for conversation-to-markdown conversion.

Usage:
    python -m conversation_to_md.cli input.zip [--output ./output] [--flat] [--no-timestamps] [--no-emoji] [--system]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from conversation_to_md.core.pipeline import convert_zip
from conversation_to_md.core.renderer import RenderOptions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert AI chat export ZIPs to Markdown files."
    )
    parser.add_argument("input", type=Path, help="Path to the ZIP file to convert")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("./output"),
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--flat", action="store_true",
        help="Flat output (no provider subfolders)"
    )
    parser.add_argument(
        "--no-timestamps", action="store_true",
        help="Omit timestamps from output"
    )
    parser.add_argument(
        "--no-emoji", action="store_true",
        help="Omit emoji from role headers"
    )
    parser.add_argument(
        "--system", action="store_true",
        help="Include system messages in output"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    options = RenderOptions(
        include_timestamps=not args.no_timestamps,
        include_system_messages=args.system,
        emoji_headers=not args.no_emoji,
        output_structure="flat" if args.flat else "structured",
    )

    def on_progress(msg: str) -> None:
        print(msg)

    written, source = convert_zip(args.input, args.output, options, on_progress)

    if not written:
        print("No conversations found.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone. {len(written)} file(s) written to {args.output}/")


if __name__ == "__main__":
    main()
