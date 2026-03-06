"""
Vault Health Engine
-------------------
Scan and maintain vault hygiene with actionable, reversible operations.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


SKIP_DIRS = {
    ".obsidian",
    ".git",
    ".trash",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".DUPLICATE_TRASH",
    ".DUPLICATE_TRASH_PHASE2",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".csv",
    ".xml",
    ".ini",
    ".ps1",
    ".bat",
    ".cmd",
    ".py",
    ".ts",
    ".js",
    ".sh",
    ".log",
    ".css",
    ".html",
}

MEDIA_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".bmp",
    ".pdf",
    ".mp3",
    ".mp4",
    ".wav",
    ".ogg",
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".docx",
    ".pptx",
}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+?)?\]\]")
EMBED_RE = re.compile(r"!\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

INVISIBLE_CHARS = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\u200e",
    "\u200f",
    "\u2060",
    "\u2061",
    "\u2062",
    "\u2063",
    "\u2064",
    "\ufeff",
    "\u00ad",
    "\u034f",
    "\u061c",
    "\u180e",
    "\u2028",
    "\u2029",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}
INVISIBLE_REGEX = re.compile("[" + "".join(INVISIBLE_CHARS) + "]")


def _should_skip_path(vault_root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(vault_root).parts
    except Exception:
        return True
    return any(part in SKIP_DIRS for part in parts)


def _iter_files(vault_root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(vault_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        root = Path(dirpath)
        for name in filenames:
            p = root / name
            if p.is_file() and not _should_skip_path(vault_root, p):
                yield p


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_index(vault_root: Path) -> Dict[str, Any]:
    md_files: List[Path] = []
    all_files: List[Path] = []
    name_map: Dict[str, List[Path]] = defaultdict(list)
    full_name_map: Dict[str, List[Path]] = defaultdict(list)

    for p in _iter_files(vault_root):
        all_files.append(p)
        name_map[p.stem.lower()].append(p)
        full_name_map[p.name.lower()].append(p)
        if p.suffix.lower() == ".md":
            md_files.append(p)

    return {
        "md_files": md_files,
        "all_files": all_files,
        "name_map": name_map,
        "full_name_map": full_name_map,
    }


def _resolve_wikilink(target: str, name_map: Dict[str, List[Path]], full_name_map: Dict[str, List[Path]]) -> bool:
    t = target.strip().lower()
    if not t:
        return True
    if t in name_map or t in full_name_map:
        return True
    if (t + ".md") in full_name_map:
        return True
    if t.replace(" ", "_") in name_map or t.replace("_", " ") in name_map:
        return True
    if "/" in target or "\\" in target:
        leaf = target.replace("\\", "/").split("/")[-1].strip().lower()
        if leaf in name_map or leaf in full_name_map or (leaf + ".md") in full_name_map:
            return True
    return False


def _resolve_embed(target: str, name_map: Dict[str, List[Path]], full_name_map: Dict[str, List[Path]]) -> bool:
    t = target.strip().lower()
    if not t:
        return True
    if t in full_name_map or t in name_map:
        return True
    if "/" in target or "\\" in target:
        leaf = target.replace("\\", "/").split("/")[-1].strip().lower()
        if leaf in full_name_map or leaf in name_map:
            return True
    return False


def _scan_broken_links(vault_root: Path, md_files: Sequence[Path], name_map: Dict[str, List[Path]], full_name_map: Dict[str, List[Path]]) -> List[Dict[str, Any]]:
    broken: List[Dict[str, Any]] = []
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = md.relative_to(vault_root).as_posix()
        for line_num, line in enumerate(content.splitlines(), 1):
            for m in WIKILINK_RE.finditer(line):
                target = m.group(1).strip()
                if not _resolve_wikilink(target, name_map, full_name_map):
                    broken.append({"file": rel, "line": line_num, "target": target, "type": "wikilink"})
    return broken


def _scan_dead_assets(vault_root: Path, md_files: Sequence[Path], name_map: Dict[str, List[Path]], full_name_map: Dict[str, List[Path]]) -> List[Dict[str, Any]]:
    dead: List[Dict[str, Any]] = []
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = md.relative_to(vault_root).as_posix()
        for line_num, line in enumerate(content.splitlines(), 1):
            for m in EMBED_RE.finditer(line):
                target = m.group(1).strip()
                if not _resolve_embed(target, name_map, full_name_map):
                    dead.append({"file": rel, "line": line_num, "target": target, "type": "embed"})
            for m in MD_IMAGE_RE.finditer(line):
                target = m.group(1).strip()
                if target.startswith("http://") or target.startswith("https://"):
                    continue
                if not _resolve_embed(target, name_map, full_name_map):
                    dead.append({"file": rel, "line": line_num, "target": target, "type": "md_image"})
    return dead


def _scan_orphans(vault_root: Path, md_files: Sequence[Path]) -> List[str]:
    referenced: set[str] = set()
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip().lower()
            if "/" in target:
                target = target.split("/")[-1]
            referenced.add(target)
            referenced.add(target.replace(" ", "_"))
            referenced.add(target.replace("_", " "))
        for m in EMBED_RE.finditer(content):
            target = m.group(1).strip().lower()
            if "/" in target:
                target = target.split("/")[-1]
            referenced.add(target)
        for m in MD_IMAGE_RE.finditer(content):
            target = m.group(1).strip().lower()
            if "/" in target:
                target = target.split("/")[-1]
            referenced.add(target)

    skip_names = {"readme", "overview", "index", "_vault_health", "manifest"}
    orphans: List[str] = []
    for md in md_files:
        stem = md.stem.lower()
        if stem in skip_names:
            continue
        name = md.name.lower()
        linked = (
            stem in referenced
            or name in referenced
            or stem.replace("_", " ") in referenced
            or stem.replace(" ", "_") in referenced
            or stem.replace("-", " ") in referenced
            or stem.replace("-", "_") in referenced
        )
        if not linked:
            orphans.append(md.relative_to(vault_root).as_posix())
    return sorted(orphans)


def _scan_encoding_issues(vault_root: Path, files: Sequence[Path]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for p in files:
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            raw = p.read_bytes()
        except Exception as e:
            issues.append(
                {
                    "path": p.relative_to(vault_root).as_posix(),
                    "decode_errors": 1,
                    "error": f"read failed: {e}",
                }
            )
            continue

        bom = raw.startswith(b"\xef\xbb\xbf")
        nulls = raw.count(b"\x00")
        crlf = raw.count(b"\r\n")
        decode_errors = 0
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            decode_errors = 1
            text = raw.decode("utf-8", errors="replace")

        invisible = len(INVISIBLE_REGEX.findall(text))

        trailing_ws = 0
        excess_blanks = 0
        missing_final_nl = False
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blank_run = 0
        for line in lines:
            stripped = line.rstrip()
            if line != stripped and line.strip():
                trailing_ws += 1
            if stripped == "":
                blank_run += 1
                if blank_run > 2:
                    excess_blanks += 1
            else:
                blank_run = 0
        if text and not text.endswith("\n"):
            missing_final_nl = True

        if any([bom, nulls, crlf, decode_errors, invisible, trailing_ws, excess_blanks, missing_final_nl]):
            issues.append(
                {
                    "path": p.relative_to(vault_root).as_posix(),
                    "bom": int(bom),
                    "nulls": nulls,
                    "crlf": crlf,
                    "decode_errors": decode_errors,
                    "invisible": invisible,
                    "trailing_ws": trailing_ws,
                    "excess_blanks": excess_blanks,
                    "missing_final_nl": int(missing_final_nl),
                }
            )
    return issues


def _scan_large_files(vault_root: Path, files: Sequence[Path], threshold_mb: float) -> List[Dict[str, Any]]:
    threshold = max(0.1, float(threshold_mb)) * 1024 * 1024
    large: List[Dict[str, Any]] = []
    for p in files:
        try:
            size = p.stat().st_size
        except Exception:
            continue
        if size >= threshold:
            large.append(
                {
                    "path": p.relative_to(vault_root).as_posix(),
                    "size": size,
                    "ext": p.suffix.lower() or "(no ext)",
                }
            )
    large.sort(key=lambda x: (-x["size"], x["path"]))
    return large


def _scan_duplicate_media(vault_root: Path, files: Sequence[Path], min_size_kb: int) -> List[Dict[str, Any]]:
    media_candidates: List[Path] = []
    min_bytes = max(1, int(min_size_kb)) * 1024
    for p in files:
        if p.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        try:
            size = p.stat().st_size
        except Exception:
            continue
        if size >= min_bytes:
            media_candidates.append(p)

    by_size: Dict[int, List[Path]] = defaultdict(list)
    for p in media_candidates:
        by_size[p.stat().st_size].append(p)

    groups: List[Dict[str, Any]] = []
    for size, same_size in by_size.items():
        if len(same_size) < 2:
            continue
        by_hash: Dict[str, List[Path]] = defaultdict(list)
        for p in same_size:
            try:
                by_hash[_file_hash(p)].append(p)
            except Exception:
                continue
        for h, dup_paths in by_hash.items():
            if len(dup_paths) < 2:
                continue
            rel_paths = sorted(p.relative_to(vault_root).as_posix() for p in dup_paths)
            canonical = rel_paths[0]
            duplicates = rel_paths[1:]
            groups.append(
                {
                    "hash": h,
                    "size": size,
                    "count": len(rel_paths),
                    "canonical": canonical,
                    "duplicates": duplicates,
                    "wasted_bytes": size * len(duplicates),
                }
            )

    groups.sort(key=lambda g: (-g["wasted_bytes"], -g["count"], g["canonical"]))
    return groups


def scan_vault_health(
    vault_path: str | Path,
    large_file_mb: float = 25.0,
    duplicate_media_min_kb: int = 64,
    include_broken_links: bool = True,
    include_dead_assets: bool = True,
    include_orphans: bool = True,
    include_encoding: bool = True,
    include_large_files: bool = True,
    include_duplicate_media: bool = True,
) -> Dict[str, Any]:
    vault_root = Path(vault_path).resolve()
    if not vault_root.exists() or not vault_root.is_dir():
        raise ValueError(f"Vault path not found or not a directory: {vault_root}")

    idx = _build_index(vault_root)
    md_files: List[Path] = idx["md_files"]
    all_files: List[Path] = idx["all_files"]
    name_map = idx["name_map"]
    full_name_map = idx["full_name_map"]

    broken_links = _scan_broken_links(vault_root, md_files, name_map, full_name_map) if include_broken_links else []
    dead_assets = _scan_dead_assets(vault_root, md_files, name_map, full_name_map) if include_dead_assets else []
    orphans = _scan_orphans(vault_root, md_files) if include_orphans else []
    encoding_issues = _scan_encoding_issues(vault_root, all_files) if include_encoding else []
    large_files = _scan_large_files(vault_root, all_files, large_file_mb) if include_large_files else []
    duplicate_media = _scan_duplicate_media(vault_root, all_files, duplicate_media_min_kb) if include_duplicate_media else []

    total_size = 0
    ext_counts: Counter[str] = Counter()
    for p in all_files:
        try:
            sz = p.stat().st_size
        except Exception:
            continue
        total_size += sz
        ext_counts[p.suffix.lower() or "(no ext)"] += 1

    return {
        "vault_path": str(vault_root),
        "scanned_at": dt.datetime.now().isoformat(timespec="seconds"),
        "total_files": len(all_files),
        "md_files": len(md_files),
        "total_size": total_size,
        "ext_counts": ext_counts.most_common(20),
        "broken_links": broken_links,
        "dead_assets": dead_assets,
        "orphans": orphans,
        "encoding_issues": encoding_issues,
        "large_files": large_files,
        "duplicate_media_groups": duplicate_media,
        "duplicate_media_files": sum(g["count"] for g in duplicate_media),
        "duplicate_media_wasted_bytes": sum(g["wasted_bytes"] for g in duplicate_media),
    }


def _fix_text_content(raw: bytes) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    raw = raw.replace(b"\x00", b"")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = INVISIBLE_REGEX.sub("", text)

    cleaned_lines: List[str] = []
    blank_run = 0
    for line in text.split("\n"):
        stripped = line.rstrip()
        if stripped == "":
            blank_run += 1
            if blank_run <= 2:
                cleaned_lines.append("")
        else:
            blank_run = 0
            cleaned_lines.append(stripped)

    text = "\n".join(cleaned_lines)
    text = text.rstrip("\n") + "\n"
    return text.encode("utf-8")


def apply_encoding_fixes(vault_path: str | Path, relative_paths: Sequence[str]) -> Dict[str, Any]:
    vault_root = Path(vault_path).resolve()
    fixed = 0
    skipped = 0
    errors: List[str] = []
    for rel in relative_paths:
        p = (vault_root / rel).resolve()
        if not p.exists() or not p.is_file():
            skipped += 1
            continue
        if _should_skip_path(vault_root, p):
            skipped += 1
            continue
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            skipped += 1
            continue
        try:
            before = p.read_bytes()
            after = _fix_text_content(before)
            if after != before:
                p.write_bytes(after)
                fixed += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append(f"{rel}: {e}")
    return {"fixed": fixed, "skipped": skipped, "errors": errors}


def stage_files(vault_path: str | Path, relative_paths: Sequence[str], staging_dir: str | Path | None = None) -> Dict[str, Any]:
    vault_root = Path(vault_path).resolve()
    if staging_dir is None:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        staging_root = vault_root / ".VAULT_HEALTH_STAGING" / stamp
    else:
        staging_root = Path(staging_dir).resolve()
    staging_root.mkdir(parents=True, exist_ok=True)

    moved = 0
    skipped = 0
    errors: List[str] = []
    manifest_rows: List[str] = []

    for rel in relative_paths:
        src = (vault_root / rel).resolve()
        if not src.exists() or not src.is_file():
            skipped += 1
            continue
        try:
            src.relative_to(vault_root)
        except Exception:
            skipped += 1
            continue
        dst = staging_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if dst.exists():
                dst = dst.with_name(f"{dst.stem}__dup{dst.suffix}")
            shutil.move(str(src), str(dst))
            moved += 1
            manifest_rows.append(f"{rel}\t{dst}")
        except Exception as e:
            errors.append(f"{rel}: {e}")

    manifest_path = staging_root / "MANIFEST.tsv"
    if manifest_rows:
        manifest_path.write_text("source_relative_path\tstaged_path\n" + "\n".join(manifest_rows), encoding="utf-8")

    return {
        "staging_root": str(staging_root),
        "moved": moved,
        "skipped": skipped,
        "errors": errors,
        "manifest": str(manifest_path) if manifest_rows else "",
    }


def delete_files(vault_path: str | Path, relative_paths: Sequence[str]) -> Dict[str, Any]:
    vault_root = Path(vault_path).resolve()
    deleted = 0
    skipped = 0
    errors: List[str] = []
    for rel in relative_paths:
        p = (vault_root / rel).resolve()
        if not p.exists() or not p.is_file():
            skipped += 1
            continue
        try:
            p.relative_to(vault_root)
        except Exception:
            skipped += 1
            continue
        try:
            p.unlink()
            deleted += 1
        except Exception as e:
            errors.append(f"{rel}: {e}")
    return {"deleted": deleted, "skipped": skipped, "errors": errors}


def write_health_report(scan_result: Dict[str, Any], output_path: str | Path | None = None) -> Path:
    vault_root = Path(scan_result["vault_path"])
    if output_path is None:
        output = vault_root / "_VAULT_HEALTH_ENGINE.md"
    else:
        output = Path(output_path)

    def fmt_size(num: int) -> str:
        if num >= 1_073_741_824:
            return f"{num / 1_073_741_824:.2f} GB"
        if num >= 1_048_576:
            return f"{num / 1_048_576:.1f} MB"
        if num >= 1024:
            return f"{num / 1024:.1f} KB"
        return f"{num} B"

    lines: List[str] = []
    lines.append("# Vault Health Engine Report")
    lines.append(f"**Generated:** {scan_result.get('scanned_at', '')}")
    lines.append(f"**Vault:** `{scan_result.get('vault_path', '')}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Total files | {scan_result.get('total_files', 0):,} |")
    lines.append(f"| Markdown files | {scan_result.get('md_files', 0):,} |")
    lines.append(f"| Total size | {fmt_size(int(scan_result.get('total_size', 0)))} |")
    lines.append(f"| Broken links | {len(scan_result.get('broken_links', [])):,} |")
    lines.append(f"| Dead assets | {len(scan_result.get('dead_assets', [])):,} |")
    lines.append(f"| Orphans | {len(scan_result.get('orphans', [])):,} |")
    lines.append(f"| Encoding issues | {len(scan_result.get('encoding_issues', [])):,} |")
    lines.append(f"| Large files | {len(scan_result.get('large_files', [])):,} |")
    lines.append(f"| Duplicate media groups | {len(scan_result.get('duplicate_media_groups', [])):,} |")
    lines.append(f"| Duplicate media wasted | {fmt_size(int(scan_result.get('duplicate_media_wasted_bytes', 0)))} |")
    lines.append("")

    lines.append("## Large Files (Top 50)")
    lines.append("")
    lines.append("| Size | Path |")
    lines.append("|---:|---|")
    for item in scan_result.get("large_files", [])[:50]:
        lines.append(f"| {fmt_size(int(item.get('size', 0)))} | `{item.get('path', '')}` |")
    lines.append("")

    lines.append("## Duplicate Media (Top 50 groups)")
    lines.append("")
    lines.append("| Count | Wasted | Canonical |")
    lines.append("|---:|---:|---|")
    for group in scan_result.get("duplicate_media_groups", [])[:50]:
        lines.append(
            f"| {group.get('count', 0)} | {fmt_size(int(group.get('wasted_bytes', 0)))} | `{group.get('canonical', '')}` |"
        )
    lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    return output
