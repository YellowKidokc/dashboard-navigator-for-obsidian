#!/usr/bin/env python3
"""
Auto Audio Publisher for Genesis-to-Quantum
==========================================

Watches TTS OUTBOX for new MP3 files, stores them under 00_MEDIA,
optionally uploads to Google Drive, and updates article media callouts.

Main flow:
1) Detect new MP3 in OUTBOX
2) Infer article id (01..07) + media kind (narration/podcast)
3) Copy or move file to 00_MEDIA/Audio/GENESIS_TO_QUANTUM/Article_<id>/
4) (Optional) Upload to Google Drive and capture share link
5) Update GTQ note media callout block in article note(s)
6) Save state in JSON to avoid duplicate processing
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Local helper already in this project
from build_media_callout_block import run as upsert_media_block


DEFAULT_OUTBOX = Path(r"O:\999_IGNORE\Obsidian Programs\TTS\Pipeline\OUTBOX")
DEFAULT_SERIES_ROOT = Path(r"O:\_Theophysics_v3\04_THEOPYHISCS\The Convergence\GENESIS TO QUANTUM The Seven-Article Series")
DEFAULT_MEDIA_ROOT = Path(r"O:\_Theophysics_v3\00_MEDIA\Audio\GENESIS_TO_QUANTUM")
DEFAULT_STATE_FILE = Path(r"O:\_Theophysics_v3\00_MEDIA\Audio\GENESIS_TO_QUANTUM\audio_publish_state.json")

# Optional Drive defaults from existing pipeline scripts
DEFAULT_DRIVE_CREDENTIALS = Path(r"O:\Theophysics_Data\google-drive-credentials.json")
DEFAULT_DRIVE_FOLDER_ID = "1zYMngrdCrvs0le73Fgl8iODnAhWBLlia"
DEFAULT_AXIOMS_LINK = "[[00_Canonical/CANONICAL_INDEX|Canonical Axiom Index]]"
VALID_ARTICLE_IDS = {"01", "02", "03", "04", "05", "06", "07"}
TITLE_ID_HINTS = {
    "measurement that collapsed reality": "01",
    "genesis as quantum event": "01",
    "first quantum state": "02",
    "free will in two frames": "03",
    "day time began": "04",
    "why reality needs three": "05",
    "photon isnt watching you back": "06",
    "photon isn't watching you back": "06",
    "eraser and the cross": "07",
}


@dataclass
class UploadResult:
    success: bool
    url: str = ""
    file_id: str = ""
    message: str = ""


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "processed": {},
            "articles": {},
            "updated_at": None,
        }

    def save(self) -> None:
        self.data["updated_at"] = datetime.now().isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def fingerprint(self, p: Path) -> str:
        stat = p.stat()
        return f"{p.name}|{int(stat.st_mtime)}|{stat.st_size}"

    def is_processed(self, p: Path) -> bool:
        return self.fingerprint(p) in self.data["processed"]

    def mark_processed(self, p: Path, record: dict) -> None:
        self.data["processed"][self.fingerprint(p)] = record

    def article_entry(self, article_id: str) -> dict:
        art = self.data["articles"].setdefault(
            article_id,
            {
                "audio_narration": "",
                "podcast_debate": "",
                "podcast_deepdive": "",
                "downloads": "",
                "axioms_index": DEFAULT_AXIOMS_LINK,
                "notes": [],
                "items": [],
            },
        )
        return art


class DriveUploader:
    def __init__(self, credentials_path: Path, root_folder_id: str):
        self.credentials_path = credentials_path
        self.root_folder_id = root_folder_id
        self.service = None
        self.MediaFileUpload = None

    def init(self) -> None:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = service_account.Credentials.from_service_account_file(
            str(self.credentials_path),
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        self.service = build("drive", "v3", credentials=creds)
        self.MediaFileUpload = MediaFileUpload

    def ensure_folder(self, name: str, parent_id: str) -> str:
        query = (
            f"name='{name}' and '{parent_id}' in parents and "
            "mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        results = self.service.files().list(q=query, fields="files(id,name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]

        created = (
            self.service.files()
            .create(
                body={
                    "name": name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_id],
                },
                fields="id",
            )
            .execute()
        )
        return created["id"]

    def upload(self, local_file: Path, article_id: str) -> UploadResult:
        try:
            if self.service is None:
                self.init()

            folder_name = f"Article_{article_id}"
            article_folder = self.ensure_folder(folder_name, self.root_folder_id)

            query = f"name='{local_file.name}' and '{article_folder}' in parents and trashed=false"
            existing = self.service.files().list(q=query, fields="files(id,webViewLink)").execute().get("files", [])
            if existing:
                return UploadResult(True, url=existing[0].get("webViewLink", ""), file_id=existing[0]["id"], message="exists")

            media = self.MediaFileUpload(str(local_file), mimetype="audio/mpeg", resumable=True)
            file = (
                self.service.files()
                .create(
                    body={"name": local_file.name, "parents": [article_folder]},
                    media_body=media,
                    fields="id,webViewLink,webContentLink",
                )
                .execute()
            )

            self.service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"},
            ).execute()

            file_info = self.service.files().get(
                fileId=file["id"],
                fields="id,webViewLink,webContentLink",
            ).execute()

            return UploadResult(True, url=file_info.get("webViewLink", ""), file_id=file_info.get("id", ""), message="uploaded")
        except Exception as e:
            return UploadResult(False, message=str(e))


def infer_article_id(filename: str) -> Optional[str]:
    # Preferred: starts with 2-digit article id
    m = re.search(r"(?<!\d)(\d{2})(?=[ _-])", filename)
    if m and m.group(1) in VALID_ARTICLE_IDS:
        return m.group(1)

    # Fallback: infer from title hints
    lowered = filename.lower()
    for hint, aid in TITLE_ID_HINTS.items():
        if hint in lowered:
            return aid
    return None


def infer_media_kind(filename: str) -> str:
    f = filename.lower()
    if "podcast" in f and ("debate" in f or "vs" in f):
        return "podcast_debate"
    if "deep" in f or "dive" in f:
        return "podcast_deepdive"
    if "podcast" in f:
        return "podcast_deepdive"
    return "audio_narration"


def safe_slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._ -]", "", name).strip()
    s = re.sub(r"\s+", " ", s)
    return s or "audio"


def resolve_article_notes(series_root: Path, article_id: str) -> List[Path]:
    # Include both published + source if present; avoid reports/json
    candidates = sorted(series_root.glob(f"{article_id}_*.md"))
    notes: List[Path] = []
    for c in candidates:
        n = c.name.lower()
        if "publish_gate" in n or n.endswith("_media_block.md"):
            continue
        notes.append(c)
    return notes


def update_media_blocks_for_article(article_notes: List[Path], article_entry: dict, dry_run: bool) -> None:
    for note in article_notes:
        if dry_run:
            print(f"  [DRY] Would update media block: {note}")
            continue

        upsert_media_block(
            note_path=note,
            podcast_a_url=article_entry.get("podcast_debate", ""),
            podcast_b_url=article_entry.get("podcast_deepdive", ""),
            audio_url=article_entry.get("audio_narration", ""),
            drive_url=article_entry.get("downloads", ""),
            podcast_a_label="Debate Cut",
            podcast_b_label="Deep Dive",
            audio_label="Word-for-word Narration",
            drive_label="Download Folder",
            axioms_url=article_entry.get("axioms_index", DEFAULT_AXIOMS_LINK),
            axioms_label="Canonical Axiom Index",
            write=True,
        )
        print(f"  [OK] Updated media block: {note.name}")


def process_file(
    mp3_path: Path,
    outbox: Path,
    media_root: Path,
    series_root: Path,
    state: StateStore,
    uploader: Optional[DriveUploader],
    move_file: bool,
    dry_run: bool,
) -> bool:
    article_id = infer_article_id(mp3_path.name)
    if not article_id:
        print(f"[SKIP] Could not infer article id from: {mp3_path.name}")
        return False

    kind = infer_media_kind(mp3_path.name)
    article_notes = resolve_article_notes(series_root, article_id)

    dest_dir = media_root / f"Article_{article_id}"
    dest_name = safe_slug(mp3_path.name)
    dest_file = dest_dir / dest_name

    print(f"[PROCESS] {mp3_path.name}")
    print(f"  Article: {article_id} | Kind: {kind}")

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        if move_file:
            shutil.move(str(mp3_path), str(dest_file))
        else:
            shutil.copy2(str(mp3_path), str(dest_file))

    public_url = ""
    upload_status = "local-only"

    if uploader is not None:
        if dry_run:
            upload_status = "dry-run-upload"
            public_url = ""
            print(f"  [DRY] Would upload to Drive: {dest_file.name}")
        else:
            result = uploader.upload(dest_file, article_id=article_id)
            upload_status = result.message
            if result.success:
                public_url = result.url
                print(f"  [OK] Drive link: {public_url}")
            else:
                print(f"  [WARN] Upload failed, keeping local-only: {result.message}")

    entry = state.article_entry(article_id)
    if public_url:
        entry[kind] = public_url
    elif not entry.get(kind):
        # Fallback local vault path for Obsidian clickability
        entry[kind] = str(dest_file)

    entry["notes"] = [str(n) for n in article_notes]
    entry["items"].append(
        {
            "time": datetime.now().isoformat(),
            "source": str(mp3_path),
            "dest": str(dest_file),
            "kind": kind,
            "url": public_url,
            "upload_status": upload_status,
            "move_file": move_file,
        }
    )

    update_media_blocks_for_article(article_notes, entry, dry_run=dry_run)

    if not dry_run:
        record = {
            "article_id": article_id,
            "kind": kind,
            "dest": str(dest_file),
            "upload_status": upload_status,
            "time": datetime.now().isoformat(),
        }
        # Track original OUTBOX file fingerprint so copy-mode files are not reprocessed.
        state.mark_processed(mp3_path, record)
    return True


def run_once(args: argparse.Namespace, state: StateStore, uploader: Optional[DriveUploader]) -> int:
    if not args.outbox.exists():
        print(f"[ERROR] OUTBOX not found: {args.outbox}")
        return 1

    mp3_files = sorted(args.outbox.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
    if not mp3_files:
        print("[INFO] No MP3 files found in OUTBOX.")
        return 0

    # Ensure all articles use the same canonical axioms link for callout output.
    if args.axioms_url:
        for aid in VALID_ARTICLE_IDS:
            state.article_entry(aid)["axioms_index"] = args.axioms_url

    processed_now = 0
    for mp3 in mp3_files:
        lower_name = mp3.name.lower()
        if ".edgechunk" in lower_name:
            continue
        if state.is_processed(mp3):
            continue
        did_process = process_file(
            mp3_path=mp3,
            outbox=args.outbox,
            media_root=args.media_root,
            series_root=args.series_root,
            state=state,
            uploader=uploader,
            move_file=args.move,
            dry_run=args.dry_run,
        )
        if did_process:
            processed_now += 1
            if not args.dry_run:
                state.save()

    if processed_now == 0:
        print("[INFO] Nothing new to process.")
    else:
        print(f"[DONE] Processed {processed_now} new file(s).")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auto-publish GTQ audio to media + callouts")
    p.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    p.add_argument("--series-root", type=Path, default=DEFAULT_SERIES_ROOT)
    p.add_argument("--media-root", type=Path, default=DEFAULT_MEDIA_ROOT)
    p.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    p.add_argument("--watch", action="store_true", help="Keep watching for new MP3s")
    p.add_argument("--interval", type=int, default=20, help="Watch interval seconds")
    p.add_argument("--move", action="store_true", help="Move (not copy) files from OUTBOX")
    p.add_argument("--dry-run", action="store_true", help="Preview without writing")

    p.add_argument("--upload-drive", action="store_true", help="Upload to Google Drive and store public links")
    p.add_argument("--drive-credentials", type=Path, default=DEFAULT_DRIVE_CREDENTIALS)
    p.add_argument("--drive-folder-id", default=DEFAULT_DRIVE_FOLDER_ID)
    p.add_argument("--axioms-url", default=DEFAULT_AXIOMS_LINK, help="Canonical axioms link used in media callout")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    state = StateStore(args.state_file)
    uploader: Optional[DriveUploader] = None

    if args.upload_drive:
        if not args.drive_credentials.exists() and not args.dry_run:
            print(f"[ERROR] Drive credentials not found: {args.drive_credentials}")
            return 2
        uploader = DriveUploader(args.drive_credentials, args.drive_folder_id)

    print("[START] GTQ Audio Auto Publisher")
    print(f"  OUTBOX: {args.outbox}")
    print(f"  SERIES: {args.series_root}")
    print(f"  MEDIA:  {args.media_root}")
    print(f"  STATE:  {args.state_file}")
    print(f"  DRIVE:  {'on' if args.upload_drive else 'off'}")

    if not args.watch:
        code = run_once(args, state, uploader)
        state.save()
        return code

    try:
        while True:
            run_once(args, state, uploader)
            state.save()
            time.sleep(max(5, args.interval))
    except KeyboardInterrupt:
        print("\n[STOP] Watcher stopped by user.")
        state.save()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
