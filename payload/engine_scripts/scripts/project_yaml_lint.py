#!/usr/bin/env python3
"""
Lint YAML frontmatter for project linkage and claim-trace fields.

Checks:
1) claim-bearing notes must link to at least one project ID
2) project IDs must exist in PROJECT_REGISTRY.csv
3) project_role must be one of: core, support, reference
4) evidence_links should be present on claim-bearing notes
5) falsification_test should be present for hypothesis-like claims
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


DEFAULT_REGISTRY = (
    r"O:\_Theophysics_v3\00_SYSTEM\00System\03_Taxonomy_Naming\PROJECT_REGISTRY.csv"
)
DEFAULT_VAULT = r"O:\_Theophysics_v3"

ALLOWED_PROJECT_ROLES = {"core", "support", "reference"}
HYPOTHESIS_LIKE = {"hypothesis", "lemma", "operationalization", "result", "interpretation"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project YAML lint checker")
    parser.add_argument("--vault-root", default=DEFAULT_VAULT, help="Vault root to scan")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="PROJECT_REGISTRY.csv path")
    parser.add_argument("--out-dir", default="", help="Output directory for lint report")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit code 1 if errors exist")
    parser.add_argument(
        "--include-glob",
        default="*.md",
        help="Glob pattern for notes (default: *.md)",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        help="Path substring to exclude (repeatable)",
    )
    return parser.parse_args()


def read_registry_ids(path: Path) -> Tuple[set, List[str]]:
    issues = []
    ids = set()
    if not path.exists():
        issues.append(f"Registry not found: {path}")
        return ids, issues
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if "project_id" not in (reader.fieldnames or []):
            issues.append("Registry missing required column: project_id")
            return ids, issues
        for row in reader:
            pid = (row.get("project_id") or "").strip()
            if pid:
                ids.add(pid)
    return ids, issues


def extract_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end == -1:
        return ""
    return text[4:end]


def parse_scalar(lines: Sequence[str], key: str) -> str:
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*)$", flags=re.IGNORECASE)
    for line in lines:
        m = pat.match(line)
        if not m:
            continue
        return m.group(1).strip().strip('"').strip("'")
    return ""


def parse_list(lines: Sequence[str], key: str) -> List[str]:
    values: List[str] = []
    pat_inline = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*)$", flags=re.IGNORECASE)

    for i, line in enumerate(lines):
        m = pat_inline.match(line)
        if not m:
            continue
        rest = m.group(1).strip()
        if rest.startswith("[") and rest.endswith("]"):
            body = rest[1:-1].strip()
            if body:
                for part in body.split(","):
                    v = part.strip().strip('"').strip("'")
                    if v:
                        values.append(v)
            return values
        if rest:
            for part in rest.split(","):
                v = part.strip().strip('"').strip("'")
                if v:
                    values.append(v)
            return values

        # block list
        j = i + 1
        while j < len(lines):
            s = lines[j]
            if re.match(r"^\s*-\s+", s):
                v = re.sub(r"^\s*-\s+", "", s).strip().strip('"').strip("'")
                if v:
                    values.append(v)
                j += 1
                continue
            if s.strip() == "":
                j += 1
                continue
            break
        return values
    return values


def normalize_claim_role(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace("-", "_")


def should_exclude(path: Path, excludes: Sequence[str]) -> bool:
    p = str(path).lower()
    for ex in excludes:
        if ex and ex.lower() in p:
            return True
    return False


def lint_note(
    rel_path: str,
    fm: str,
    known_project_ids: set,
) -> List[Tuple[str, str, str, str, str]]:
    """
    Returns list of tuples:
    (severity, issue, field, detail, recommendation)
    """
    issues: List[Tuple[str, str, str, str, str]] = []
    lines = fm.splitlines()

    claim_role_raw = parse_scalar(lines, "claim_role")
    claim_role = normalize_claim_role(claim_role_raw) if claim_role_raw else ""

    project_id = parse_scalar(lines, "project_id")
    project_ids = parse_list(lines, "project_ids")
    combined_project_ids = []
    if project_id:
        combined_project_ids.append(project_id)
    combined_project_ids.extend(project_ids)
    combined_project_ids = [p for p in combined_project_ids if p]

    project_role = parse_scalar(lines, "project_role").lower()
    evidence_links = parse_list(lines, "evidence_links")
    falsification_test = parse_scalar(lines, "falsification_test")

    if claim_role:
        if not combined_project_ids:
            issues.append(
                (
                    "ERROR",
                    "MISSING_PROJECT_LINK",
                    "project_id/project_ids",
                    "claim_role is present but no project linkage found",
                    "Add project_id or project_ids with valid registry IDs",
                )
            )
        if not evidence_links:
            issues.append(
                (
                    "WARN",
                    "MISSING_EVIDENCE_LINKS",
                    "evidence_links",
                    "claim_role present but evidence_links is empty",
                    "Add one or more evidence links or explicitly justify empty state",
                )
            )
        if claim_role in HYPOTHESIS_LIKE and not falsification_test:
            issues.append(
                (
                    "WARN",
                    "MISSING_FALSIFICATION_TEST",
                    "falsification_test",
                    f"{claim_role} note has no falsification test",
                    "Add a concrete falsification condition with threshold/timeline",
                )
            )

    if project_role and project_role not in ALLOWED_PROJECT_ROLES:
        issues.append(
            (
                "ERROR",
                "INVALID_PROJECT_ROLE",
                "project_role",
                f"project_role='{project_role}' is not allowed",
                "Use one of: core, support, reference",
            )
        )

    for pid in combined_project_ids:
        if pid not in known_project_ids:
            issues.append(
                (
                    "ERROR",
                    "UNKNOWN_PROJECT_ID",
                    "project_id/project_ids",
                    f"{pid} is not present in PROJECT_REGISTRY.csv",
                    "Add this project ID to registry or correct typo in YAML",
                )
            )

    # minor hygiene warning
    if project_ids and not project_id:
        issues.append(
            (
                "WARN",
                "MISSING_PRIMARY_PROJECT_ID",
                "project_id",
                "project_ids exists without primary project_id",
                "Set project_id as primary and keep remaining links in project_ids",
            )
        )

    return issues


def main() -> int:
    args = parse_args()
    vault_root = Path(args.vault_root)
    registry_path = Path(args.registry)
    out_dir = Path(args.out_dir) if args.out_dir else registry_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    project_ids, registry_issues = read_registry_ids(registry_path)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = out_dir / f"PROJECT_YAML_LINT_{ts}.csv"

    rows: List[List[str]] = []
    for msg in registry_issues:
        rows.append(["ERROR", "<registry>", "REGISTRY_ERROR", "registry", msg, "Fix registry file first"])

    scanned = 0
    with_frontmatter = 0
    for md in vault_root.rglob(args.include_glob):
        if should_exclude(md, args.exclude_path):
            continue
        scanned += 1
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            rows.append(["WARN", str(md), "READ_ERROR", "", "Could not read file", "Check file permissions"])
            continue

        fm = extract_frontmatter(text)
        if not fm:
            continue
        with_frontmatter += 1
        rel = str(md.relative_to(vault_root))
        issues = lint_note(rel_path=rel, fm=fm, known_project_ids=project_ids)
        for sev, issue, field, detail, rec in issues:
            rows.append([sev, rel, issue, field, detail, rec])

    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["severity", "file", "issue", "field", "detail", "recommendation"])
        writer.writerows(rows)

    errors = sum(1 for r in rows if r[0] == "ERROR")
    warns = sum(1 for r in rows if r[0] == "WARN")

    print(f"Vault root: {vault_root}")
    print(f"Registry: {registry_path}")
    print(f"Scanned markdown files: {scanned}")
    print(f"Files with frontmatter: {with_frontmatter}")
    print(f"Errors: {errors} | Warnings: {warns}")
    print(f"Report: {out_csv}")

    if args.fail_on_error and errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
