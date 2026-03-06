#!/usr/bin/env python3
"""
Vault scaffold generator for Theophysics.

Builds folder structures with optional control kits, markdown scaffolding,
AAA redirect launchers, review staging, and audit artifacts.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


TRI_LAYER_STRUCTURE: Dict[str, List[str]] = {
    "00AI": [
        "01_Ethos",
        "02_Roles",
        "03_Prompt_Library",
        "04_Workflows",
        "05_Verification",
        "06_Distillation",
        "07_Modeling_Frameworks",
        "08_Critique_Protocols",
        "09_Experiments",
    ],
    "00System": [
        "01_Ontology_Domain_Map",
        "02_Claim_Trace_Graph",
        "03_Taxonomy_Naming",
        "04_Note_Data_Model",
        "05_Linking_Maps",
        "06_Paper_Model_Spine",
        "07_Governance_Change_Control",
        "08_Quality_Scoring_Model",
    ],
    "00OS": [
        "01_Rhythm",
        "02_Pipelines",
        "03_Execution_Modes",
        "04_Review_Maintenance",
        "05_Archive_Recovery",
    ],
}


DEFAULT_MARKDOWN_FILES = [
    "00_README_FIRST.md",
    "01_NAVIGATION_MAP.md",
    "02_DASHBOARD_LOCAL.md",
    "03_FOLDER_CONTRACT.md",
    "04_CHANGELOG.md",
    "05_STATUS.md",
    "06_LINKS_TO_MAIN_SYSTEM.md",
]

REVIEW_FOLDER_NAME = "ZZZ_FOLDER_REVIEW"
REVIEW_LOG_TEMPLATE = "REVIEW_LOG_TEMPLATE.csv"
STRUCTURAL_HEALTH_FILE = "STRUCTURAL_HEALTH.md"
ID_CONVENTION_FILE = "ID_CONVENTION.md"


def _launcher_contents() -> str:
    # This .bat searches upward for 00_SYSTEM\\01_ENGINE\\scripts\\AAA\\run_aaa.ps1
    return (
        "@echo off\n"
        "setlocal EnableExtensions\n"
        "set \"CTX=%~dp0\"\n"
        "set \"P=%CTX%\"\n"
        ":find\n"
        "if exist \"%P%00_SYSTEM\\01_ENGINE\\scripts\\AAA\\run_aaa.ps1\" (\n"
        "  set \"AAA=%P%00_SYSTEM\\01_ENGINE\\scripts\\AAA\\run_aaa.ps1\"\n"
        "  goto run\n"
        ")\n"
        "for %%I in (\"%P%..\\\") do set \"N=%%~fI\"\n"
        "if /I \"%N%\"==\"%P%\" goto fallback\n"
        "set \"P=%N%\"\n"
        "goto find\n"
        ":fallback\n"
        "set \"AAA=O:\\_Theophysics_v3\\00_SYSTEM\\01_ENGINE\\scripts\\AAA\\run_aaa.ps1\"\n"
        ":run\n"
        "powershell -NoProfile -ExecutionPolicy Bypass -File \"%AAA%\" -ContextFolder \"%CTX%\"\n"
        "endlocal\n"
    )


def _slug_title(filename: str) -> str:
    return filename.replace(".md", "").replace("_", " ").strip()


def markdown_stub(filename: str, parent: Path, yaml_placeholders: bool) -> str:
    title = _slug_title(filename)
    if yaml_placeholders:
        return (
            "---\n"
            f"title: {title}\n"
            "status: draft\n"
            "owner: \n"
            f"last_updated: {dt.datetime.now().date().isoformat()}\n"
            "tags: []\n"
            "---\n\n"
            f"# {title}\n\n"
            f"Parent Folder: `{parent}`\n\n"
            "Notes:\n"
            "- \n"
        )
    return (
        f"# {title}\n\n"
        f"Parent Folder: `{parent}`\n\n"
        "Status: draft\n"
    )


def id_convention_stub(layer: str) -> str:
    return (
        "# ID Convention\n\n"
        f"Layer: `{layer}`\n\n"
        "Use stable IDs so renames do not break references.\n\n"
        "## Suggested Pattern\n"
        "`THP-<LAYER>-<DOMAIN>-<YYYY>-<NNNN>`\n\n"
        "Examples:\n"
        "- `THP-AI-PROMPT-2026-0001`\n"
        "- `THP-SYS-MODEL-2026-0012`\n"
        "- `THP-OS-PROTOCOL-2026-0003`\n"
    )


def structural_health_stub(folder_name: str, yaml_placeholders: bool) -> str:
    frontmatter = ""
    if yaml_placeholders:
        frontmatter = (
            "---\n"
            "status: draft\n"
            "type: structural-health\n"
            f"folder: {folder_name}\n"
            f"updated: {dt.datetime.now().date().isoformat()}\n"
            "---\n\n"
        )
    return (
        frontmatter
        + "# STRUCTURAL HEALTH\n\n"
        + f"Folder: `{folder_name}`\n\n"
        + "| Metric | Value | Target | Notes |\n"
        + "|---|---:|---:|---|\n"
        + "| Folder count | TBD | <= TBD | |\n"
        + "| Orphan note count | TBD | 0 | |\n"
        + "| Broken link count | TBD | 0 | |\n"
        + "| Average score | TBD | >= TBD | |\n"
        + "| Lowest score | TBD | >= TBD | |\n"
        + "| Publish-ready count | TBD | >= TBD | |\n"
        + "\n"
        + "Last checked: TBD\n"
    )


@dataclass
class Action:
    kind: str
    path: Path
    note: str = ""
    status: str = "planned"


@dataclass
class Plan:
    root: Path
    dry_run: bool
    actions: List[Action] = field(default_factory=list)

    def add(self, kind: str, path: Path, note: str = "", status: str = "planned") -> None:
        self.actions.append(Action(kind=kind, path=path, note=note, status=status))

    def ensure_dir(self, path: Path) -> None:
        if path.exists():
            self.add("skip_dir", path, "exists", status="skipped")
            return
        if self.dry_run:
            self.add("mkdir", path, status="planned")
            return
        path.mkdir(parents=True, exist_ok=True)
        self.add("mkdir", path, status="applied")

    def write_file(self, path: Path, content: str, overwrite: bool = False) -> None:
        if path.exists() and not overwrite:
            self.add("skip_file", path, "exists", status="skipped")
            return
        if self.dry_run:
            self.add("write_file", path, status="planned")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.add("write_file", path, status="applied")

    def write_csv(self, path: Path, headers: Sequence[str]) -> None:
        if path.exists():
            self.add("skip_file", path, "exists", status="skipped")
            return
        if self.dry_run:
            self.add("write_csv", path, status="planned")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(list(headers))
        self.add("write_csv", path, status="applied")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Theophysics vault scaffolds.")
    parser.add_argument("--root", default=r"O:\_Theophysics_v3", help="Root folder to modify.")
    parser.add_argument("--dry-run", action="store_true", help="Plan actions without creating files.")
    parser.add_argument("--interactive", action="store_true", help="Run interactive prompts.")

    parser.add_argument("--tri-layer", action="store_true", help="Create 00AI/00System/00OS preset.")
    parser.add_argument(
        "--layers",
        nargs="*",
        choices=["00AI", "00System", "00OS"],
        default=[],
        help="Create only selected top layers.",
    )
    parser.add_argument("--full-vault", action="store_true", help="Apply kit to all top-level folders.")
    parser.add_argument("--partial", action="store_true", help="Apply kit only to selected folders.")

    parser.add_argument("--custom-folders", nargs="*", default=[], help="Custom relative folder paths.")
    parser.add_argument("--custom-file", help="Text file with one relative folder path per line.")
    parser.add_argument("--kit-targets", nargs="*", default=[], help="Specific folders to receive control kits.")
    parser.add_argument("--all-top-level-kit", action="store_true", help="Apply kit to every top-level folder.")

    parser.add_argument("--add-markdown", action="store_true", help="Create markdown scaffolding.")
    parser.add_argument("--include-markdown", dest="add_markdown", action="store_true")
    parser.add_argument("--add-review", action="store_true", help="Create review staging folders and csv.")
    parser.add_argument("--include-control-kit", dest="add_review", action="store_true")
    parser.add_argument("--add-launcher", action="store_true", help="Add AAA_MENU.bat launcher.")
    parser.add_argument("--include-launcher", dest="add_launcher", action="store_true")

    parser.add_argument("--yaml-placeholders", action="store_true", help="Add YAML placeholders in md stubs.")
    parser.add_argument("--include-yaml-placeholders", dest="yaml_placeholders", action="store_true")
    parser.add_argument("--add-id-convention", action="store_true", help="Create ID_CONVENTION.md in controls.")
    parser.add_argument("--include-id-convention", dest="add_id_convention", action="store_true")
    parser.add_argument(
        "--add-structural-health",
        action="store_true",
        help="Create STRUCTURAL_HEALTH.md in each major domain target.",
    )
    parser.add_argument("--include-structural-health", dest="add_structural_health", action="store_true")
    parser.add_argument(
        "--markdown-files",
        nargs="*",
        default=[],
        help="Override markdown scaffolding names (defaults used if omitted).",
    )
    return parser.parse_args()


def yn(question: str, default: bool = True) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input(question + suffix).strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes"}


def prompt_multiline(prompt: str) -> List[str]:
    print(prompt)
    print("Enter one path per line. Blank line to finish.")
    rows: List[str] = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        rows.append(line)
    return rows


def load_custom_file(path: Path) -> List[str]:
    rows: List[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        rows.append(s)
    return rows


def control_folder_name(layer_name: str) -> str:
    clean = layer_name.replace("00", "").replace(" ", "").strip("_")
    clean = clean.upper() if clean else "ROOT"
    return f"THEOPHYSICS_{clean}_CONTROL"


def create_layers(plan: Plan, layers: Sequence[str]) -> List[Path]:
    roots: List[Path] = []
    for layer in layers:
        if layer not in TRI_LAYER_STRUCTURE:
            continue
        top_path = plan.root / layer
        plan.ensure_dir(top_path)
        roots.append(top_path)
        for child in TRI_LAYER_STRUCTURE[layer]:
            plan.ensure_dir(top_path / child)
    return roots


def create_custom_folders(plan: Plan, rel_paths: Iterable[str]) -> List[Path]:
    made: List[Path] = []
    for rel in rel_paths:
        rel_clean = rel.strip().strip("\\/").replace("/", "\\")
        if not rel_clean:
            continue
        p = plan.root / rel_clean
        plan.ensure_dir(p)
        made.append(p)
    return made


def apply_control_kit(
    plan: Plan,
    target: Path,
    add_launcher: bool,
    add_markdown: bool,
    markdown_files: Sequence[str],
    add_review: bool,
    yaml_placeholders: bool,
    add_id_convention: bool,
    add_structural_health: bool,
) -> None:
    cdir = target / control_folder_name(target.name)
    plan.ensure_dir(cdir)

    if add_markdown:
        names = list(markdown_files) if markdown_files else list(DEFAULT_MARKDOWN_FILES)
        for name in names:
            plan.write_file(
                cdir / name,
                markdown_stub(filename=name, parent=target, yaml_placeholders=yaml_placeholders),
            )

    if add_id_convention:
        plan.write_file(cdir / ID_CONVENTION_FILE, id_convention_stub(target.name))

    if add_review:
        review_dir = cdir / REVIEW_FOLDER_NAME
        plan.ensure_dir(review_dir)
        plan.write_csv(
            review_dir / REVIEW_LOG_TEMPLATE,
            headers=["timestamp", "action", "source", "destination", "reason"],
        )

    if add_structural_health:
        plan.write_file(
            target / STRUCTURAL_HEALTH_FILE,
            structural_health_stub(folder_name=target.name, yaml_placeholders=yaml_placeholders),
        )

    if add_launcher:
        plan.write_file(target / "AAA_MENU.bat", _launcher_contents())


def print_summary(plan: Plan) -> None:
    print("")
    print(f"Root: {plan.root}")
    print(f"Dry run: {plan.dry_run}")
    print(f"Actions: {len(plan.actions)}")
    by_kind: Dict[str, int] = {}
    for a in plan.actions:
        by_kind[a.kind] = by_kind.get(a.kind, 0) + 1
    for kind in sorted(by_kind):
        print(f"- {kind}: {by_kind[kind]}")
    print("")
    for a in plan.actions[:120]:
        note = f" ({a.note})" if a.note else ""
        print(f"[{a.kind}] {a.path}{note}")
    if len(plan.actions) > 120:
        print(f"... {len(plan.actions) - 120} more")


def ensure_audit_dir(root: Path) -> Path:
    if root.exists():
        return root
    return Path.cwd()


def write_audit_outputs(plan: Plan, config: dict) -> tuple[Path, Path]:
    now = dt.datetime.now()
    audit_dir = ensure_audit_dir(plan.root)
    manifest_path = audit_dir / f"_VAULT_BUILD_MANIFEST_{now:%Y-%m-%d_%H%M%S}.json"
    log_path = audit_dir / f"_VAULT_BUILD_LOG_{now:%Y-%m-%d_%H%M%S}.csv"

    # CSV action log
    with log_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["kind", "status", "path", "note"])
        for a in plan.actions:
            writer.writerow([a.kind, a.status, str(a.path), a.note])

    by_kind: Dict[str, int] = {}
    for a in plan.actions:
        by_kind[a.kind] = by_kind.get(a.kind, 0) + 1

    manifest = {
        "manifest_version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "root": str(plan.root),
        "audit_dir": str(audit_dir),
        "dry_run": plan.dry_run,
        "config": config,
        "summary": {
            "total_actions": len(plan.actions),
            "by_kind": by_kind,
            "applied_or_planned": [
                str(a.path)
                for a in plan.actions
                if a.kind in {"mkdir", "write_file", "write_csv"} and a.status in {"applied", "planned"}
            ],
            "skipped": [str(a.path) for a in plan.actions if a.status == "skipped"],
        },
        "actions": [
            {"kind": a.kind, "status": a.status, "path": str(a.path), "note": a.note}
            for a in plan.actions
        ],
    }
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    return manifest_path, log_path


def interactive_main() -> int:
    root_raw = input(r"Root path [O:\_Theophysics_v3]: ").strip()
    root = Path(root_raw if root_raw else r"O:\_Theophysics_v3")

    dry = yn("Dry run first?", default=True)
    full_vault = yn("Full vault mode?", default=False)

    layer_raw = input("Which layers? (comma list: 00AI,00System,00OS) [00AI,00System,00OS]: ").strip()
    if not layer_raw:
        layer_names = ["00AI", "00System", "00OS"]
    else:
        layer_names = [x.strip() for x in layer_raw.split(",") if x.strip() in TRI_LAYER_STRUCTURE]
    if not layer_names:
        layer_names = ["00AI", "00System", "00OS"]

    include_markdown = yn("Include markdown scaffolding?", default=True)
    include_control_kit = yn("Include control kit (review folders + logs)?", default=True)
    include_launcher = yn("Include AAA redirect script?", default=True)
    yaml_placeholders = yn("Include YAML placeholders in markdown files?", default=True) if include_markdown else False
    include_id_convention = yn("Include ID_CONVENTION.md?", default=True)
    include_structural_health = yn("Include STRUCTURAL_HEALTH.md in each major folder?", default=True)

    plan = Plan(root=root, dry_run=dry)
    created_roots = create_layers(plan, layer_names)

    # Optional partial custom adds
    custom = prompt_multiline("Custom extra folder paths (optional):")
    if custom:
        create_custom_folders(plan, custom)

    # Target set for control kit
    if full_vault and root.exists():
        targets = [d for d in root.iterdir() if d.is_dir()]
    else:
        targets = list(created_roots)
        extra_targets = prompt_multiline("Extra control-kit targets (relative to root, optional):")
        for rel in extra_targets:
            targets.append(root / rel)

    dedup: Dict[str, Path] = {}
    for t in targets:
        dedup[str(t)] = t
    targets = list(dedup.values())

    for target in targets:
        apply_control_kit(
            plan=plan,
            target=target,
            add_launcher=include_launcher,
            add_markdown=include_markdown,
            markdown_files=[],
            add_review=include_control_kit,
            yaml_placeholders=yaml_placeholders,
            add_id_convention=include_id_convention,
            add_structural_health=include_structural_health,
        )

    config = {
        "mode": "interactive",
        "full_vault": full_vault,
        "layers": layer_names,
        "include_markdown": include_markdown,
        "include_control_kit": include_control_kit,
        "include_launcher": include_launcher,
        "yaml_placeholders": yaml_placeholders,
        "include_id_convention": include_id_convention,
        "include_structural_health": include_structural_health,
        "targets": [str(t) for t in targets],
        "custom_folders": custom,
    }
    manifest_path, log_path = write_audit_outputs(plan, config)

    print_summary(plan)
    print("")
    print(f"Manifest: {manifest_path}")
    print(f"Log: {log_path}")
    return 0


def cli_main(args: argparse.Namespace) -> int:
    root = Path(args.root)
    plan = Plan(root=root, dry_run=args.dry_run)

    layers = list(args.layers)
    if args.tri_layer and not layers:
        layers = ["00AI", "00System", "00OS"]
    created_roots: List[Path] = []
    if layers:
        created_roots.extend(create_layers(plan, layers))

    custom_rows = list(args.custom_folders)
    if args.custom_file:
        custom_rows.extend(load_custom_file(Path(args.custom_file)))
    if custom_rows:
        create_custom_folders(plan, custom_rows)

    targets: List[Path] = []
    if args.full_vault or args.all_top_level_kit:
        if root.exists():
            targets.extend([d for d in root.iterdir() if d.is_dir()])
    if args.kit_targets:
        targets.extend([root / t for t in args.kit_targets])
    if not args.full_vault and not args.all_top_level_kit and not args.kit_targets:
        targets.extend(created_roots)

    dedup: Dict[str, Path] = {}
    for t in targets:
        dedup[str(t)] = t
    targets = list(dedup.values())

    for target in targets:
        apply_control_kit(
            plan=plan,
            target=target,
            add_launcher=args.add_launcher,
            add_markdown=args.add_markdown,
            markdown_files=args.markdown_files,
            add_review=args.add_review,
            yaml_placeholders=args.yaml_placeholders,
            add_id_convention=args.add_id_convention,
            add_structural_health=args.add_structural_health,
        )

    config = {
        "mode": "cli",
        "root": str(root),
        "dry_run": args.dry_run,
        "full_vault": args.full_vault or args.all_top_level_kit,
        "partial": args.partial,
        "layers": layers,
        "custom_folders": custom_rows,
        "targets": [str(t) for t in targets],
        "include_markdown": args.add_markdown,
        "include_control_kit": args.add_review,
        "include_launcher": args.add_launcher,
        "yaml_placeholders": args.yaml_placeholders,
        "include_id_convention": args.add_id_convention,
        "include_structural_health": args.add_structural_health,
    }
    manifest_path, log_path = write_audit_outputs(plan, config)

    print_summary(plan)
    print("")
    print(f"Manifest: {manifest_path}")
    print(f"Log: {log_path}")
    return 0


def main() -> int:
    args = parse_args()
    no_cli_intent = (
        not args.tri_layer
        and not args.layers
        and not args.custom_folders
        and not args.custom_file
        and not args.kit_targets
        and not args.full_vault
        and not args.partial
        and not args.all_top_level_kit
    )
    if args.interactive or no_cli_intent:
        return interactive_main()
    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
