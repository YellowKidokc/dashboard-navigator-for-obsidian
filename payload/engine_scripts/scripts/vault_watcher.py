"""
vault_watcher.py — INBOX auto-cleaner + vault audit logger.

Modes:
    --inbox   Watch _INBOX/ for new .md/.txt files, clean & stamp them
    --audit   Log all vault file events to monthly CSV
    --all     Both watchers simultaneously
    --status  Show what's being watched
    --vault   Override vault root (default: O:\\_Theophysics_v3)

PM2:
    pm2 start "python vault_watcher.py --all" --name vault-watcher
"""

import argparse
import csv
import io
import os
import re
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, \
    FileModifiedEvent, FileDeletedEvent, FileMovedEvent

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_VAULT = Path(r"O:\_Theophysics_v3")
INBOX_REL = "_INBOX"
PROCESSED_REL = "_INBOX/_processed"
INBOX_LOG_NAME = "inbox_log.csv"
AUDIT_DIR_REL = "00_SYSTEM/01_ENGINE/scripts/output"
AUDIT_PREFIX = "vault_audit_log"
WATCHER_LOG_NAME = "watcher.log"

DEBOUNCE_SEC = 3.0
SETTLE_CHECKS = 2        # file size must be stable for this many checks
SETTLE_INTERVAL = 1.5    # seconds between settle checks

# Folders the audit logger should ignore
AUDIT_IGNORE = {".obsidian", ".git", ".trash", "_processed", "__pycache__", "output"}

# Extensions the inbox cleaner will process
INBOX_EXTENSIONS = {".md", ".txt"}

# Invisible / garbage characters to strip (keeps normal whitespace)
INVISIBLE_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f"           # C0 controls (keep \t \n \r)
    r"\u00ad\u200b-\u200f\u2028-\u202f\u2060\ufeff" # Unicode joiners, BOM, etc.
    r"\ufff9-\ufffb]"                                # interlinear annotations
)


# ---------------------------------------------------------------------------
# Logging helper — writes to console + rotating watcher.log
# ---------------------------------------------------------------------------
_log_lock = threading.Lock()
_log_path: Path | None = None


def init_log(vault: Path) -> None:
    global _log_path
    _log_path = vault / AUDIT_DIR_REL / WATCHER_LOG_NAME


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with _log_lock:
        print(line, flush=True)
        if _log_path:
            try:
                with open(_log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Encoding / cleanup helpers
# ---------------------------------------------------------------------------
def clean_text(raw: bytes) -> str:
    """Remove BOM, null bytes, invisible chars, normalise line endings."""
    # Decode — try utf-8-sig (strips BOM), fall back to latin-1
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    # Strip null bytes
    text = text.replace("\x00", "")

    # Strip invisible characters
    text = INVISIBLE_RE.sub("", text)

    # Normalise line endings → LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text


def ensure_yaml_frontmatter(text: str, filename: str) -> str:
    """If the file lacks YAML frontmatter, prepend a minimal block."""
    stripped = text.lstrip("\n")
    if stripped.startswith("---"):
        # Already has frontmatter — leave it alone
        return text

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = (
        "---\n"
        f"uuid: {uuid.uuid4()}\n"
        f"title: \"{filename}\"\n"
        f"created: {now}\n"
        "status: draft\n"
        "element_type: note\n"
        "---\n\n"
    )
    return fm + text


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------
def append_inbox_csv(csv_path: Path, row: dict) -> None:
    """Append a row to the inbox log CSV, creating headers if needed."""
    fields = ["timestamp", "original_name", "cleaned_name", "size_bytes",
              "issues_fixed", "destination"]
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        w.writerow(row)


def append_audit_csv(csv_path: Path, row: dict) -> None:
    """Append a row to the audit log CSV, creating headers if needed."""
    fields = ["timestamp", "event_type", "file_path", "file_size",
              "extension", "folder"]
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        w.writerow(row)


def audit_csv_path(vault: Path) -> Path:
    """Return monthly-rotated audit CSV path."""
    month = datetime.now().strftime("%Y-%m")
    return vault / AUDIT_DIR_REL / f"{AUDIT_PREFIX}_{month}.csv"


# ---------------------------------------------------------------------------
# File-settle check (network drive latency guard)
# ---------------------------------------------------------------------------
def wait_for_settle(path: Path) -> bool:
    """Wait until the file size stops changing. Returns False if file vanishes."""
    prev_size = -1
    stable_count = 0
    for _ in range(20):  # max ~30 seconds
        try:
            sz = path.stat().st_size
        except OSError:
            return False
        if sz == prev_size:
            stable_count += 1
            if stable_count >= SETTLE_CHECKS:
                return True
        else:
            stable_count = 0
        prev_size = sz
        time.sleep(SETTLE_INTERVAL)
    return True  # proceed anyway after timeout


# ---------------------------------------------------------------------------
# INBOX Handler
# ---------------------------------------------------------------------------
class InboxHandler(FileSystemEventHandler):
    """Watches _INBOX/ for new files, cleans them, moves to _processed/."""

    def __init__(self, vault: Path):
        super().__init__()
        self.vault = vault
        self.inbox = vault / INBOX_REL
        self.processed = vault / PROCESSED_REL
        self.csv_path = self.processed / INBOX_LOG_NAME
        self.processed.mkdir(parents=True, exist_ok=True)
        # Debounce: track scheduled files so we don't double-process
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        self._schedule(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._schedule(event.src_path)

    def _schedule(self, src_path: str):
        p = Path(src_path)
        # Only process target extensions
        if p.suffix.lower() not in INBOX_EXTENSIONS:
            return
        # Skip files already in _processed/
        try:
            p.relative_to(self.processed)
            return
        except ValueError:
            pass

        key = str(p)
        with self._lock:
            if key in self._pending:
                self._pending[key].cancel()
            timer = threading.Timer(DEBOUNCE_SEC, self._process, args=[p])
            timer.daemon = True
            timer.start()
            self._pending[key] = timer

    def _process(self, path: Path):
        with self._lock:
            self._pending.pop(str(path), None)

        if not path.exists():
            return

        log(f"INBOX: Processing {path.name}")

        # Wait for network write to finish
        if not wait_for_settle(path):
            log(f"INBOX: File vanished during settle: {path.name}")
            return

        try:
            raw = path.read_bytes()
        except OSError as e:
            log(f"INBOX: Read error {path.name}: {e}")
            return

        issues = []

        # --- Encoding cleanup ---
        if b"\x00" in raw:
            issues.append("null_bytes")
        if raw[:3] == b"\xef\xbb\xbf":
            issues.append("bom")
        if b"\r\n" in raw or b"\r" in raw:
            issues.append("crlf")

        text = clean_text(raw)

        # Check for invisible chars (compare before/after)
        text_no_invis = INVISIBLE_RE.sub("", text)
        if len(text_no_invis) < len(text):
            issues.append("invisible_chars")
            text = text_no_invis

        # --- YAML frontmatter ---
        stem = path.stem
        original_text = text
        text = ensure_yaml_frontmatter(text, stem)
        if text != original_text:
            issues.append("added_yaml")

        # --- Write cleaned file to _processed ---
        dest = self.processed / path.name
        # Handle name collision
        if dest.exists():
            ts = datetime.now().strftime("%H%M%S")
            dest = self.processed / f"{path.stem}_{ts}{path.suffix}"

        try:
            dest.write_text(text, encoding="utf-8", newline="\n")
        except OSError as e:
            log(f"INBOX: Write error {dest.name}: {e}")
            return

        # --- Remove original ---
        try:
            path.unlink()
        except OSError as e:
            log(f"INBOX: Could not delete original {path.name}: {e}")

        # --- Log to CSV ---
        append_inbox_csv(self.csv_path, {
            "timestamp": datetime.now().isoformat(),
            "original_name": path.name,
            "cleaned_name": dest.name,
            "size_bytes": dest.stat().st_size,
            "issues_fixed": "; ".join(issues) if issues else "none",
            "destination": str(dest),
        })

        log(f"INBOX: Done — {path.name} → {dest.name} (fixes: {', '.join(issues) or 'none'})")


# ---------------------------------------------------------------------------
# Audit Handler
# ---------------------------------------------------------------------------
class AuditHandler(FileSystemEventHandler):
    """Logs create/modify/delete/move events across the entire vault."""

    def __init__(self, vault: Path):
        super().__init__()
        self.vault = vault

    def _should_ignore(self, path_str: str) -> bool:
        parts = Path(path_str).parts
        return any(p.lower().lstrip("_") in AUDIT_IGNORE or p.lower() in AUDIT_IGNORE
                   for p in parts)

    def _log_event(self, event_type: str, path_str: str):
        if self._should_ignore(path_str):
            return
        p = Path(path_str)
        try:
            size = p.stat().st_size if p.exists() else 0
        except OSError:
            size = 0

        csv_path = audit_csv_path(self.vault)
        append_audit_csv(csv_path, {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "file_path": str(p),
            "file_size": size,
            "extension": p.suffix.lower(),
            "folder": str(p.parent),
        })

    def on_created(self, event):
        if not event.is_directory:
            self._log_event("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._log_event("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._log_event("deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._log_event("moved", event.src_path)
            self._log_event("moved_to", event.dest_path)


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------
def show_status(vault: Path):
    inbox = vault / INBOX_REL
    processed = vault / PROCESSED_REL
    inbox_csv = processed / INBOX_LOG_NAME
    audit_csv = audit_csv_path(vault)

    print(f"Vault:         {vault}")
    print(f"INBOX:         {inbox}  (exists: {inbox.is_dir()})")
    print(f"Processed:     {processed}  (exists: {processed.is_dir()})")
    print()

    if inbox_csv.exists():
        lines = sum(1 for _ in open(inbox_csv, encoding="utf-8")) - 1
        print(f"Inbox log:     {inbox_csv}  ({lines} entries)")
    else:
        print(f"Inbox log:     (not yet created)")

    if audit_csv.exists():
        lines = sum(1 for _ in open(audit_csv, encoding="utf-8")) - 1
        print(f"Audit log:     {audit_csv}  ({lines} entries)")
    else:
        print(f"Audit log:     (not yet created)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Vault Watcher — INBOX auto-cleaner + audit logger")
    parser.add_argument("--inbox", action="store_true",
                        help="Watch _INBOX/ for new files")
    parser.add_argument("--audit", action="store_true",
                        help="Log all vault file events to CSV")
    parser.add_argument("--all", action="store_true",
                        help="Run both --inbox and --audit")
    parser.add_argument("--status", action="store_true",
                        help="Show current watcher status")
    parser.add_argument("--vault", type=str, default=None,
                        help="Override vault root path")
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else DEFAULT_VAULT
    if not vault.is_dir():
        print(f"ERROR: Vault not found at {vault}", file=sys.stderr)
        sys.exit(1)

    if args.status:
        show_status(vault)
        return

    run_inbox = args.inbox or args.all
    run_audit = args.audit or args.all

    if not run_inbox and not run_audit:
        parser.print_help()
        sys.exit(1)

    init_log(vault)

    # Ensure output dirs exist
    (vault / AUDIT_DIR_REL).mkdir(parents=True, exist_ok=True)
    (vault / PROCESSED_REL).mkdir(parents=True, exist_ok=True)

    observers: list[Observer] = []

    if run_inbox:
        inbox_path = vault / INBOX_REL
        inbox_path.mkdir(parents=True, exist_ok=True)
        handler = InboxHandler(vault)
        obs = Observer()
        obs.schedule(handler, str(inbox_path), recursive=False)
        observers.append(obs)
        log(f"INBOX watcher started → {inbox_path}")

    if run_audit:
        handler = AuditHandler(vault)
        obs = Observer()
        obs.schedule(handler, str(vault), recursive=True)
        observers.append(obs)
        log(f"AUDIT watcher started → {vault}")

    for obs in observers:
        obs.start()

    log("Vault Watcher running. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Shutting down...")
    finally:
        for obs in observers:
            obs.stop()
        for obs in observers:
            obs.join()
        log("Vault Watcher stopped.")


if __name__ == "__main__":
    main()
