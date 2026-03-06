#!/usr/bin/env python3
"""
Build MASTER_EQ lossless transfer packs.

Outputs:
- 12 separate full files
- 12 separate no-python files
- combined short (no python)
- combined long (full)
- python code appendix
- source map CSV
- hypothesis/right-wrong/enigmas summary
- short + long zip bundles
"""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Source:
    sid: str
    title: str
    relative_path: str


SOURCES: tuple[Source, ...] = (
    Source("ME_P01", "Law 01 Gravity Sin", r"01_LAW_01_GRAVITY_SIN\LAW_01__Gravity_Sin.md"),
    Source("ME_P02", "Law 02 Motion Seeking", r"02_LAW_02_MOTION_SEEKING\LAW_02__Information_Theory_Divine_Logos.md"),
    Source("ME_P03", "Law 03 Energy Truth", r"03_LAW_03_ENERGY_TRUTH\LAW_03__Mathematical_Architecture_EQ_02_154.md"),
    Source("ME_P04", "Law 04 Entropy Corruption", r"04_LAW_04_ENTROPY_CORRUPTION\LAW_04__Twelve_Unified_Theories_CONV_01_286.md"),
    Source("ME_P05", "Law 05 Thermodynamics Grace", r"05_LAW_05_THERMODYNAMICS_GRACE\LAW_05__Thermodynamics_and_Grace_Story.md"),
    Source("ME_P06", "Law 06 Sowing Reaping", r"06_LAW_06_SOWING_REAPING\LAW_06__Th_Axiomatic_Understanding_Of_Grace_MATH_03_290.md"),
    Source("ME_P07", "Law 07 Relativity Perspective", r"07_LAW_07_RELATIVITY_PERSPECTIVE\LAW_07__File_Set_1.md"),
    Source("ME_P08", "Law 08 Quantum Freewill", r"08_LAW_08_QUANTUM_FREEWILL\LAW_08__Experimental_Predictions_VAL_01_299.md"),
    Source("ME_P09", "Law 09 Hidden Framework", r"09_LAW_09_HIDDEN_FRAMEWORK\LAW_09__Hidden_Framework_Story.md"),
    Source("ME_P10", "Law 10 Unified Christ", r"10_LAW_10_UNIFIED_CHRIST\LAW_10__Greatest_Achievement_CONC_02_305.md"),
    Source("ME_P11", "Master Equation Complete", r"D_01_Axioms_-_01_CANON_-_Master_EQ_-_MASTER_EQUATION_COMPLETE.md"),
    Source("ME_P12", "Master Equation Runthrough", r"00_LAW_INDEX\03_MASTER_EQUATION_RUNTHROUGH_V1_2026-02-17.md"),
)

PY_BLOCK_RE = re.compile(r"```(?:python|py)\s*\r?\n.*?```", re.IGNORECASE | re.DOTALL)


def safe_name(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\- ]", "", text).strip()
    return re.sub(r"\s+", "-", cleaned)


def line_count(text: str) -> int:
    return text.count("\n") + (1 if text else 0)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def zip_paths(zip_path: Path, paths: Iterable[Path], base_root: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(base_root))
            elif p.is_file():
                zf.write(p, p.relative_to(base_root))


def build(base: Path, timestamp: str | None = None) -> dict[str, str]:
    ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    pack = base / f"MASTER_EQ_LOSSLESS_PACK_{ts}"
    sep_no_py = pack / "01_SEPARATE_NO_PYTHON"
    sep_full = pack / "02_SEPARATE_FULL"
    combined = pack / "03_COMBINED"
    appendix = pack / "04_CODE_APPENDIX"
    meta = pack / "05_META"
    for d in (sep_no_py, sep_full, combined, appendix, meta):
        d.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, str | int]] = []
    py_blocks_accum: list[str] = []
    combined_short_parts = [
        "# MASTER_EQ Lossless Short Bundle (No Python Code)",
        "",
        f"Generated: {ts}",
        "",
    ]
    combined_long_parts = [
        "# MASTER_EQ Lossless Extended Bundle (Full)",
        "",
        f"Generated: {ts}",
        "",
    ]

    for s in SOURCES:
        src = base / s.relative_path
        if not src.exists():
            raise FileNotFoundError(f"Missing source: {src}")
        raw = src.read_text(encoding="utf-8", errors="replace")
        matches = list(PY_BLOCK_RE.finditer(raw))
        py_count = len(matches)

        no_py = raw
        if py_count:
            replacement = "\n".join(
                [
                    "```text",
                    f"[Python block moved to 04_CODE_APPENDIX/MASTER_EQ_PYTHON_CODE_APPENDIX_{ts}.md]",
                    "```",
                ]
            )
            no_py = PY_BLOCK_RE.sub(replacement, raw)

            for idx, m in enumerate(matches, start=1):
                py_blocks_accum.extend(
                    [
                        f"## {s.sid} - Block {idx}",
                        f"Source: {src}",
                        "",
                        m.group(0),
                        "",
                    ]
                )

        stem = f"{s.sid}_{safe_name(s.title)}"
        out_full = sep_full / f"{stem}_FULL.md"
        out_no_py = sep_no_py / f"{stem}_NO_PYTHON.md"

        full_doc = "\n".join([f"# {s.sid} - {s.title}", f"Source: {src}", "", raw])
        short_doc = "\n".join([f"# {s.sid} - {s.title}", f"Source: {src}", "", no_py])
        write_text(out_full, full_doc)
        write_text(out_no_py, short_doc)

        combined_long_parts.extend(["---", f"## {s.sid} - {s.title}", f"Source: {src}", "---", raw, ""])
        combined_short_parts.extend(["---", f"## {s.sid} - {s.title}", f"Source: {src}", "---", no_py, ""])

        manifest_rows.append(
            {
                "id": s.sid,
                "title": s.title,
                "source_path": str(src),
                "lines": line_count(raw),
                "python_blocks": py_count,
                "output_no_python": str(out_no_py),
                "output_full": str(out_full),
            }
        )

    combined_short_path = combined / f"MASTER_EQ_SHORT_LOSSLESS_NO_PYTHON_{ts}.md"
    combined_long_path = combined / f"MASTER_EQ_LONG_LOSSLESS_FULL_{ts}.md"
    write_text(combined_short_path, "\n".join(combined_short_parts))
    write_text(combined_long_path, "\n".join(combined_long_parts))

    py_appendix_path = appendix / f"MASTER_EQ_PYTHON_CODE_APPENDIX_{ts}.md"
    if not py_blocks_accum:
        py_blocks_accum = ["# Python Code Appendix", "", "No fenced python blocks were found in the selected 12 sources."]
    write_text(py_appendix_path, "\n".join(py_blocks_accum))

    manifest_path = meta / f"MASTER_EQ_SOURCE_MAP_{ts}.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "title", "source_path", "lines", "python_blocks", "output_no_python", "output_full"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    hyp_path = meta / f"MASTER_EQ_HYPOTHESIS_RIGHT_WRONG_ENIGMAS_{ts}.md"
    hyp_text = "\n".join(
        [
            "# Master Equation - Hypothesis, Right/Wrong, Enigmas",
            "",
            f"Generated: {ts}",
            "",
            "## Hypothesis",
            "- Reality coherence is represented by the Master Equation channel product integrated over domain.",
            "- Physical and spiritual formulations share structural symmetry with explicit agency asymmetry terms.",
            "",
            "## What We Got Right (Current Pass)",
            "- Structural symmetry checks passed in Wolfram for channel product invariance.",
            "- Lagrangian algebra checks passed for sign inversion and Euler-Lagrange derivation.",
            "- Ten-law folder architecture is in place and sequenced.",
            "",
            "## What We Got Wrong / Still Weak",
            "- Symbol drift risk remains across files (especially overloaded symbol usage).",
            "- Not all equation-heavy law files carry explicit source tags yet.",
            "- Empirical thresholds are not pre-registered yet.",
            "",
            "## Open Enigmas",
            "- Which 2-3 predictions should be first for hard falsification?",
            "- Which channels are directly measurable with currently available datasets?",
            "- How should cross-domain parameters be normalized without circular fitting?",
            "",
            "## Links",
            "- [[03_MASTER_EQUATION_RUNTHROUGH_V1_2026-02-17]]",
            "- [[04_MASTER_EQUATION_SYMBOL_DICTIONARY_V1]]",
            "- [[05_SYMBOL_DRIFT_SCAN_2026-02-17]]",
            "- [[06_ALLOWED_EQUATION_FORMS_V1]]",
        ]
    )
    write_text(hyp_path, hyp_text)

    readme_path = pack / "README.md"
    write_text(
        readme_path,
        "\n".join(
            [
                "# MASTER_EQ Lossless Pack",
                "",
                f"Generated: {ts}",
                "",
                "Contents:",
                "- 12 separate full files",
                "- 12 separate no-python files",
                "- one combined short lossless file (no python code)",
                "- one combined long lossless file (full)",
                "- one python-code appendix",
                "- source map manifest",
                "- hypothesis/right-wrong/enigmas summary",
            ]
        ),
    )

    zip_short = pack / f"MASTER_EQ_LOSSLESS_SHORT_{ts}.zip"
    zip_long = pack / f"MASTER_EQ_LOSSLESS_LONG_{ts}.zip"
    zip_paths(zip_short, [sep_no_py, combined_short_path, py_appendix_path, manifest_path, hyp_path, readme_path], pack)
    zip_paths(zip_long, [sep_full, combined_long_path, py_appendix_path, manifest_path, hyp_path, readme_path], pack)

    return {
        "PACK": str(pack),
        "COMBINED_SHORT": str(combined_short_path),
        "COMBINED_LONG": str(combined_long_path),
        "PY_APPENDIX": str(py_appendix_path),
        "MANIFEST": str(manifest_path),
        "HYP_FILE": str(hyp_path),
        "ZIP_SHORT": str(zip_short),
        "ZIP_LONG": str(zip_long),
        "SOURCES_COUNT": str(len(SOURCES)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MASTER_EQ lossless transfer pack.")
    parser.add_argument(
        "--base",
        default=r"O:\_Theophysics_v3\MASTER_EQ_CONSOLIDATED",
        help="Base folder for MASTER_EQ_CONSOLIDATED.",
    )
    parser.add_argument("--timestamp", default=None, help="Optional timestamp override, e.g. 20260217_130500")
    args = parser.parse_args()

    result = build(Path(args.base), args.timestamp)
    for k, v in result.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
