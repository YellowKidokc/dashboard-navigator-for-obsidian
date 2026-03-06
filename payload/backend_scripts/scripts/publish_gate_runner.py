#!/usr/bin/env python3
"""
Publish Gate Runner
===================
A lightweight pre-publish layer for Theophysics articles.

What it does:
1) Runs structural readiness checks
2) Ensures media callout exists (optional)
3) Generates publish-ready output via callout_to_footnote converter
4) Writes JSON + markdown readiness report
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from callout_to_footnote import convert_article  # type: ignore
from scripts.build_media_callout_block import run as upsert_media_callout  # type: ignore


def has(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def readiness_checks(text: str) -> dict:
    checks = {
        "has_structural_index": has(text, "[!abstract]-") and has(text, "structural index"),
        "has_media_callout": has(text, "[!info]-") and has(text, "listen, watch") and has(text, "downloads"),
        "has_ring2": has(text, "## Ring 2"),
        "has_ring3": has(text, "## Ring 3"),
        "has_audit": has(text, "## The Audit") or has(text, "The Audit"),
    }
    checks["ready_for_publish"] = all(checks.values())
    return checks


def write_reports(report: dict, report_json: Path, report_md: Path) -> None:
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)

    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Publish Gate Report",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Input: `{report['input']}`",
        f"- Output: `{report['output']}`",
        "",
        "## Checks",
    ]
    for k, v in report["checks"].items():
        icon = "PASS" if v else "FAIL"
        lines.append(f"- {icon} `{k}`")

    lines.append("")
    lines.append(f"## Verdict: {'READY' if report['checks']['ready_for_publish'] else 'NEEDS WORK'}")

    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run publish gate checks + conversion")
    parser.add_argument("--input", required=True, help="Input markdown note path")
    parser.add_argument("--output", help="Output publish-ready markdown path")
    parser.add_argument("--ensure-media", action="store_true", help="Insert/update media callout before conversion")
    parser.add_argument("--report-json", help="Output JSON report path")
    parser.add_argument("--report-md", help="Output markdown report path")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise FileNotFoundError(f"Input not found: {src}")

    out = Path(args.output) if args.output else src.with_name(src.stem + "_published.md")
    report_json = Path(args.report_json) if args.report_json else out.with_name(out.stem + "_publish_gate.json")
    report_md = Path(args.report_md) if args.report_md else out.with_name(out.stem + "_publish_gate.md")

    if args.ensure_media:
        upsert_media_callout(
            note_path=src,
            podcast_a_url="",
            podcast_b_url="",
            audio_url="",
            drive_url="",
            podcast_a_label="Debate Format",
            podcast_b_label="Deep Dive",
            audio_label="Article Narration",
            drive_label="Downloads",
            axioms_url="[[00_Canonical/CANONICAL_INDEX|Canonical Axiom Index]]",
            axioms_label="Canonical Axiom Index",
            write=True,
        )

    convert_article(str(src), str(out))

    current = src.read_text(encoding="utf-8", errors="replace")
    checks = readiness_checks(current)

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input": str(src),
        "output": str(out),
        "checks": checks,
    }
    write_reports(report, report_json, report_md)

    print(f"Publish output: {out}")
    print(f"Report JSON: {report_json}")
    print(f"Report MD: {report_md}")
    print(f"Ready: {checks['ready_for_publish']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
