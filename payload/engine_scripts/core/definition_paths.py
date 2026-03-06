"""
Shared definition/glossary path discovery helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Set

SKIP_PATH_TOKENS = (".obsidian", "node_modules", ".git", "__pycache__")
DEFINITION_FOLDER_NAMES = {"glossary", "lexicon", "definitions", "4_lexicon"}

# Preferred order for active definition folders.
KNOWN_DEFINITION_DIRS = [
    ("00_SYSTEM", "Glossary"),
    ("02_LIBRARY", "Glossary"),
    ("02_LIBRARY", "4_LEXICON"),
    ("99_MATH_APPENDIX", "Definitions"),
    ("00_AXIOMS",),
]


def is_skipped_path(path: Path, vault_path: Path, include_archive: bool = False) -> bool:
    """Return True if the path should be excluded from definition scans."""
    try:
        rel_parts = [p.lower() for p in path.relative_to(vault_path).parts]
    except Exception:
        rel_parts = [p.lower() for p in path.parts]

    if any(token in part for token in SKIP_PATH_TOKENS for part in rel_parts):
        return True

    if not include_archive:
        if any(part in {"_archive", "archive"} or part.startswith("_archive") for part in rel_parts):
            return True

    return False


def discover_definition_dirs(
    vault_path: Path,
    include_global_search: bool = True,
    include_archive: bool = False,
) -> List[Path]:
    """
    Discover candidate definition folders in priority order.

    Priority:
    1. Known canonical locations.
    2. Optional vault-wide folder-name discovery.
    3. Fallback to 00_SYSTEM/Glossary even if it does not exist yet.
    """
    discovered: List[Path] = []
    seen: Set[str] = set()

    def _add(path: Path):
        key = str(path.resolve() if path.exists() else path).lower()
        if key not in seen:
            seen.add(key)
            discovered.append(path)

    # Known folders first.
    for parts in KNOWN_DEFINITION_DIRS:
        candidate = vault_path.joinpath(*parts)
        if candidate.exists() and candidate.is_dir():
            _add(candidate)

    # Optional fallback discovery by folder name.
    if include_global_search and vault_path.exists():
        extra: List[Path] = []
        for folder in vault_path.rglob("*"):
            if not folder.is_dir():
                continue
            if is_skipped_path(folder, vault_path, include_archive=include_archive):
                continue
            if folder.name.lower() in DEFINITION_FOLDER_NAMES:
                extra.append(folder)

        for folder in sorted(extra, key=lambda p: str(p).lower()):
            _add(folder)

    # No existing location yet: return a sensible writable target.
    if not discovered:
        _add(vault_path / "00_SYSTEM" / "Glossary")

    return discovered


def primary_definition_dir(
    vault_path: Path,
    include_global_search: bool = True,
    include_archive: bool = False,
) -> Path:
    """Get the highest-priority definition folder."""
    return discover_definition_dirs(
        vault_path=vault_path,
        include_global_search=include_global_search,
        include_archive=include_archive,
    )[0]

