"""
ZIP extraction utility.

Safely extracts a ZIP file to a temporary directory.
Handles nested ZIPs and basic path-traversal protection.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path


def extract_zip(zip_path: Path) -> Path:
    """
    Extract a ZIP to a temporary directory and return that directory's Path.

    The caller is responsible for cleaning up the temp directory when done.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="conv_export_"))
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Guard against path traversal (zip slip)
            target = (tmp_dir / member.filename).resolve()
            if not str(target).startswith(str(tmp_dir.resolve())):
                raise ValueError(f"Path traversal detected in ZIP: {member.filename}")
        zf.extractall(tmp_dir)
    return tmp_dir


def extract_zip_from_bytes(data: bytes) -> Path:
    """
    Extract a ZIP from raw bytes (e.g. from a Streamlit file uploader).

    Writes to a temp file first, then extracts.
    """
    tmp_zip = Path(tempfile.mktemp(suffix=".zip", prefix="conv_upload_"))
    tmp_zip.write_bytes(data)
    try:
        return extract_zip(tmp_zip)
    finally:
        tmp_zip.unlink(missing_ok=True)
