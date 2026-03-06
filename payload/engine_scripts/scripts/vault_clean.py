#!/usr/bin/env python3
"""
Vault Clean — Encoding & Whitespace Normalizer
================================================
Cleans markdown (and text) files for Obsidian vault hygiene:
  1) CRLF → LF line endings
  2) UTF-8 BOM removal
  3) Null byte removal
  4) Invisible Unicode cleanup (zero-width spaces, etc.)
  5) Excess blank lines (3+ consecutive → 2)
  6) Trailing whitespace per line
  7) Ensure file ends with single newline
  8) Filename cleanup (leading/trailing spaces in files & folders)

Usage:
    python vault_clean.py                          (interactive)
    python vault_clean.py --scan PATH              (dry run — report only)
    python vault_clean.py --fix PATH               (apply fixes)
    python vault_clean.py --fix PATH --ext .md .txt (custom extensions)
    python vault_clean.py --fix PATH --filenames   (also fix filenames)
"""

import os
import re
import sys
import argparse
from pathlib import Path
from collections import Counter

# ─── Config ───────────────────────────────────────────────────────────────────

DEFAULT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".csv",
                      ".xml", ".ini", ".ps1", ".bat", ".cmd", ".py",
                      ".ts", ".js", ".sh", ".log", ".css", ".html"}

SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "__pycache__",
             ".venv", "venv", ".DUPLICATE_TRASH", ".DUPLICATE_TRASH_PHASE2"}

# Invisible Unicode characters to strip (zero-width and control chars)
# Keeps normal whitespace (space, tab, newline) intact
INVISIBLE_CHARS = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\u200e": "LEFT-TO-RIGHT MARK",
    "\u200f": "RIGHT-TO-LEFT MARK",
    "\u2060": "WORD JOINER",
    "\u2061": "FUNCTION APPLICATION",
    "\u2062": "INVISIBLE TIMES",
    "\u2063": "INVISIBLE SEPARATOR",
    "\u2064": "INVISIBLE PLUS",
    "\ufeff": "BOM / ZERO WIDTH NO-BREAK SPACE",
    "\u00ad": "SOFT HYPHEN",
    "\u034f": "COMBINING GRAPHEME JOINER",
    "\u061c": "ARABIC LETTER MARK",
    "\u180e": "MONGOLIAN VOWEL SEPARATOR",
    "\u2028": "LINE SEPARATOR",
    "\u2029": "PARAGRAPH SEPARATOR",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
    "\u2066": "LEFT-TO-RIGHT ISOLATE",
    "\u2067": "RIGHT-TO-LEFT ISOLATE",
    "\u2068": "FIRST STRONG ISOLATE",
    "\u2069": "POP DIRECTIONAL ISOLATE",
}

INVISIBLE_REGEX = re.compile("[" + "".join(INVISIBLE_CHARS.keys()) + "]")


# ─── Scanner ──────────────────────────────────────────────────────────────────

class CleanResult:
    """Tracks what was found/fixed in a single file."""
    def __init__(self, path: str):
        self.path = path
        self.crlf = 0
        self.bom = False
        self.nulls = 0
        self.invisible = Counter()  # char -> count
        self.excess_blanks = 0
        self.trailing_ws = 0
        self.no_final_newline = False
        self.error = None

    @property
    def dirty(self) -> bool:
        return (self.crlf > 0 or self.bom or self.nulls > 0 or
                len(self.invisible) > 0 or self.excess_blanks > 0 or
                self.trailing_ws > 0 or self.no_final_newline)

    def summary(self) -> str:
        parts = []
        if self.bom:
            parts.append("BOM")
        if self.crlf:
            parts.append(f"CRLF({self.crlf})")
        if self.nulls:
            parts.append(f"NULL({self.nulls})")
        if self.invisible:
            total = sum(self.invisible.values())
            parts.append(f"INVIS({total})")
        if self.trailing_ws:
            parts.append(f"TRAIL({self.trailing_ws})")
        if self.excess_blanks:
            parts.append(f"BLANKS({self.excess_blanks})")
        if self.no_final_newline:
            parts.append("NO_EOF_NL")
        return " | ".join(parts) if parts else "clean"


def scan_file(filepath: str) -> CleanResult:
    """Scan a file and report issues without modifying it."""
    result = CleanResult(filepath)
    try:
        raw = Path(filepath).read_bytes()
    except Exception as e:
        result.error = str(e)
        return result

    # BOM check
    if raw.startswith(b"\xef\xbb\xbf"):
        result.bom = True
        raw = raw[3:]

    # Null bytes
    null_count = raw.count(b"\x00")
    if null_count:
        result.nulls = null_count
        raw = raw.replace(b"\x00", b"")

    # Decode
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception as e:
            result.error = f"Decode failed: {e}"
            return result

    # CRLF
    result.crlf = text.count("\r\n")

    # Invisible chars
    for match in INVISIBLE_REGEX.finditer(text):
        ch = match.group()
        name = INVISIBLE_CHARS.get(ch, f"U+{ord(ch):04X}")
        result.invisible[name] += 1

    # Line-level checks
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    consecutive_blanks = 0
    for line in lines:
        # Trailing whitespace (but not blank lines themselves)
        stripped = line.rstrip()
        if line != stripped and line.strip():
            result.trailing_ws += 1

        # Excess blank lines
        if stripped == "":
            consecutive_blanks += 1
            if consecutive_blanks > 2:
                result.excess_blanks += 1
        else:
            consecutive_blanks = 0

    # Final newline
    if text and not text.endswith("\n"):
        result.no_final_newline = True

    return result


def fix_file(filepath: str) -> CleanResult:
    """Fix all issues in a file. Returns what was fixed."""
    result = scan_file(filepath)
    if result.error or not result.dirty:
        return result

    try:
        raw = Path(filepath).read_bytes()
    except Exception as e:
        result.error = str(e)
        return result

    # BOM removal
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]

    # Null bytes
    raw = raw.replace(b"\x00", b"")

    # Decode
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    # CRLF → LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Invisible chars
    text = INVISIBLE_REGEX.sub("", text)

    # Line-level fixes
    lines = text.split("\n")
    cleaned_lines = []
    consecutive_blanks = 0

    for line in lines:
        stripped = line.rstrip()

        if stripped == "":
            consecutive_blanks += 1
            if consecutive_blanks <= 2:
                cleaned_lines.append("")
            # else: skip (collapse excess blanks)
        else:
            consecutive_blanks = 0
            cleaned_lines.append(stripped)

    # Rejoin
    text = "\n".join(cleaned_lines)

    # Strip trailing blank lines at end of file, ensure single final newline
    text = text.rstrip("\n") + "\n"

    # Write back as UTF-8, LF, no BOM
    Path(filepath).write_bytes(text.encode("utf-8"))

    return result


# ─── Filename Cleaner ─────────────────────────────────────────────────────────

def scan_filename_issues(root: str, skip_dirs: set) -> list:
    """Find files and folders with leading/trailing spaces or other issues."""
    issues = []
    root_path = Path(root)

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Skip excluded dirs
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        rel_dir = Path(dirpath).relative_to(root_path)

        # Check folder names
        for d in dirnames:
            clean = d.strip()
            if clean != d:
                issues.append({
                    "type": "folder",
                    "path": str(Path(dirpath) / d),
                    "original": d,
                    "cleaned": clean,
                    "issue": "leading/trailing spaces",
                })

        # Check file names
        for f in filenames:
            clean = f.strip()
            if clean != f:
                issues.append({
                    "type": "file",
                    "path": str(Path(dirpath) / f),
                    "original": f,
                    "cleaned": clean,
                    "issue": "leading/trailing spaces",
                })

    return issues


def fix_filenames(issues: list) -> tuple:
    """Rename files/folders to fix naming issues. Returns (success, errors)."""
    # Sort by path length descending so we rename deepest items first
    sorted_issues = sorted(issues, key=lambda x: len(x["path"]), reverse=True)
    success = 0
    errors = 0

    for item in sorted_issues:
        old_path = Path(item["path"])
        new_path = old_path.parent / item["cleaned"]

        if old_path.exists() and not new_path.exists():
            try:
                old_path.rename(new_path)
                success += 1
            except Exception as e:
                print(f"  ERROR renaming {old_path}: {e}")
                errors += 1
        elif new_path.exists() and old_path != new_path:
            print(f"  SKIP (target exists): {old_path.name} -> {item['cleaned']}")
            errors += 1

    return success, errors


# ─── Main Runner ──────────────────────────────────────────────────────────────

def run(target: str, mode: str = "scan", extensions: set = None,
        do_filenames: bool = False):
    """Run scan or fix on a target directory."""
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    target_path = Path(target)
    if not target_path.exists():
        print(f"ERROR: Path not found: {target}")
        return

    print()
    print("=" * 70)
    print(f"  VAULT CLEAN — {'SCAN (dry run)' if mode == 'scan' else 'FIX (applying changes)'}")
    print("=" * 70)
    print(f"  Target:     {target_path}")
    print(f"  Extensions: {', '.join(sorted(extensions))}")
    print(f"  Filenames:  {'yes' if do_filenames else 'no'}")
    print("=" * 70)
    print()

    # Collect files
    files = []
    for dirpath, dirnames, filenames in os.walk(target_path, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            ext = Path(f).suffix.lower()
            if ext in extensions:
                files.append(str(Path(dirpath) / f))

    print(f"  Found {len(files)} files to process\n")

    if not files and not do_filenames:
        print("  Nothing to do.")
        return

    # Process files
    results = []
    dirty_count = 0
    error_count = 0

    for i, fpath in enumerate(files, 1):
        if mode == "fix":
            r = fix_file(fpath)
        else:
            r = scan_file(fpath)

        results.append(r)

        if r.error:
            error_count += 1
        elif r.dirty:
            dirty_count += 1

        # Progress
        if i % 100 == 0 or i == len(files):
            print(f"  [{i}/{len(files)}] processed...", end="\r")

    print(f"  [{len(files)}/{len(files)}] processed.   ")
    print()

    # Report dirty files
    dirty_results = [r for r in results if r.dirty]
    if dirty_results:
        print(f"  {'Fixed' if mode == 'fix' else 'Issues in'} {len(dirty_results)} file(s):\n")
        for r in dirty_results[:100]:
            rel = str(Path(r.path).relative_to(target_path))
            print(f"    {rel}")
            print(f"      {r.summary()}")
        if len(dirty_results) > 100:
            print(f"\n    ... and {len(dirty_results) - 100} more")
    else:
        print("  All files clean!")

    # Report errors
    error_results = [r for r in results if r.error]
    if error_results:
        print(f"\n  Errors ({len(error_results)}):")
        for r in error_results[:20]:
            rel = str(Path(r.path).relative_to(target_path))
            print(f"    {rel}: {r.error}")

    # Filename issues
    if do_filenames:
        print(f"\n  Scanning filenames...")
        fn_issues = scan_filename_issues(target, SKIP_DIRS)
        if fn_issues:
            print(f"  Found {len(fn_issues)} filename issue(s):\n")
            for item in fn_issues[:50]:
                print(f"    [{item['type']}] \"{item['original']}\" -> \"{item['cleaned']}\"")
                print(f"      {item['path']}")

            if mode == "fix":
                print(f"\n  Fixing filenames...")
                s, e = fix_filenames(fn_issues)
                print(f"  Renamed: {s} | Errors: {e}")
            else:
                print(f"\n  (run with --fix to rename)")
        else:
            print("  All filenames clean!")

    # Summary
    print()
    print("=" * 70)
    print(f"  SUMMARY")
    print("=" * 70)

    # Aggregate stats
    totals = {
        "files_scanned": len(files),
        "files_dirty": dirty_count,
        "files_clean": len(files) - dirty_count - error_count,
        "errors": error_count,
        "crlf": sum(r.crlf for r in results),
        "bom": sum(1 for r in results if r.bom),
        "nulls": sum(r.nulls for r in results),
        "invisible": sum(sum(r.invisible.values()) for r in results),
        "trailing_ws": sum(r.trailing_ws for r in results),
        "excess_blanks": sum(r.excess_blanks for r in results),
        "no_final_nl": sum(1 for r in results if r.no_final_newline),
    }

    action = "Fixed" if mode == "fix" else "Found"
    print(f"  Files scanned:       {totals['files_scanned']:,}")
    print(f"  Files with issues:   {totals['files_dirty']:,}")
    print(f"  Files already clean: {totals['files_clean']:,}")
    print(f"  Errors:              {totals['errors']:,}")
    print()
    print(f"  {action}: CRLF line endings:   {totals['crlf']:,}")
    print(f"  {action}: BOM markers:         {totals['bom']:,}")
    print(f"  {action}: Null bytes:          {totals['nulls']:,}")
    print(f"  {action}: Invisible chars:     {totals['invisible']:,}")
    print(f"  {action}: Trailing whitespace: {totals['trailing_ws']:,}")
    print(f"  {action}: Excess blank lines:  {totals['excess_blanks']:,}")
    print(f"  {action}: Missing final NL:    {totals['no_final_nl']:,}")
    print("=" * 70)
    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Vault Clean — Encoding & Whitespace Normalizer")
    parser.add_argument("--scan", metavar="PATH",
                        help="Dry run: scan and report issues")
    parser.add_argument("--fix", metavar="PATH",
                        help="Apply fixes to all files")
    parser.add_argument("--ext", nargs="+", default=None,
                        help="File extensions to process (default: .md .txt etc.)")
    parser.add_argument("--filenames", action="store_true",
                        help="Also scan/fix filename spacing issues")
    args = parser.parse_args()

    # Determine mode and path
    if args.scan:
        mode = "scan"
        target = args.scan
    elif args.fix:
        mode = "fix"
        target = args.fix
    else:
        # Interactive menu
        print()
        print("=" * 50)
        print("  Vault Clean")
        print("=" * 50)
        print()
        print("  1) Scan (dry run — report only)")
        print("  2) Fix (apply all fixes)")
        print("  Q) Quit")
        print()
        choice = input("  Select: ").strip().upper()

        if choice == "1":
            mode = "scan"
        elif choice == "2":
            mode = "fix"
        else:
            print("  Bye.")
            return

        target = input("  Folder path: ").strip().strip('"')
        if not target:
            print("  No path given.")
            return

        fn = input("  Also fix filenames? (y/N): ").strip().lower()
        args.filenames = fn == "y"

    # Parse extensions
    extensions = DEFAULT_EXTENSIONS
    if args.ext:
        extensions = set()
        for e in args.ext:
            if not e.startswith("."):
                e = "." + e
            extensions.add(e.lower())

    target = target.strip().strip('"')

    # Confirm if fixing
    if mode == "fix":
        print(f"\n  About to FIX files in: {target}")
        confirm = input("  Proceed? (Y/n): ").strip().lower()
        if confirm == "n":
            print("  Aborted.")
            return

    run(target, mode=mode, extensions=extensions, do_filenames=args.filenames)


if __name__ == "__main__":
    main()
