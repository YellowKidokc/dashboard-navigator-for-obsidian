import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "over",
    "under",
    "about",
    "between",
    "within",
    "without",
    "are",
    "was",
    "were",
    "been",
    "being",
    "have",
    "has",
    "had",
    "not",
    "but",
    "you",
    "your",
    "our",
    "their",
    "they",
    "them",
    "its",
    "his",
    "her",
    "she",
    "him",
    "can",
    "could",
    "should",
    "would",
    "may",
    "might",
    "will",
    "shall",
    "than",
    "then",
    "also",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_prompt_schema(path: Path | None) -> dict:
    if path:
        return json.loads(read_text(path))
    return {
        "current_paper_summary": "",
        "target_folder": "",
        "search_instruction": {
            "type": "semantic+symbolic",
            "time_range": "",
            "depth_preference": "maximal-contextual",
            "recall_fallback": True,
            "query_expansion_rules": [],
        },
        "output_structure": {
            "type": "Markdown",
            "sections": [],
        },
    }


def collect_inputs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files = []
    for ext in ("*.md", "*.txt"):
        files.extend(input_path.rglob(ext))
    return sorted(files)


def tokenize(text: str) -> list[str]:
    tokens = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower()).split()
    return [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]


def extract_summary(text: str) -> tuple[str, list[str], list[str]]:
    lines = [line.strip() for line in text.splitlines()]
    paragraphs = []
    buf = []
    for line in lines:
        if not line:
            if buf:
                paragraphs.append(" ".join(buf))
                buf = []
            continue
        if not line.startswith("#"):
            buf.append(line)
    if buf:
        paragraphs.append(" ".join(buf))

    summary = " ".join(paragraphs[:2])[:900].strip()
    headings = [line.lstrip("# ").strip() for line in lines if line.startswith("#")]
    tokens = tokenize(text)
    freq = {}
    for tok in tokens:
        freq[tok] = freq.get(tok, 0) + 1
    keywords = [t for t, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:12]]
    return summary, keywords, headings


def parse_time_range(time_range: str) -> tuple[dt.date | None, dt.date | None]:
    if "to" not in time_range:
        return None, None
    left, right = [part.strip() for part in time_range.split("to", 1)]
    try:
        start = dt.date.fromisoformat(left)
        end = dt.date.fromisoformat(right)
        return start, end
    except ValueError:
        return None, None


def load_memory_entries(memory_source: Path | None) -> list[dict]:
    if not memory_source:
        return []
    entries = []
    if memory_source.is_file():
        if memory_source.suffix.lower() == ".jsonl":
            for line in read_text(memory_source).splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = obj.get("content") or ""
                if not content:
                    continue
                entries.append(
                    {
                        "id": obj.get("id") or str(len(entries) + 1),
                        "date": obj.get("date"),
                        "source": obj.get("source") or memory_source.as_posix(),
                        "content": content,
                    }
                )
        else:
            entries.append(
                {
                    "id": "1",
                    "date": None,
                    "source": memory_source.as_posix(),
                    "content": read_text(memory_source),
                }
            )
        return entries

    for file_path in memory_source.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".md", ".txt"}:
            continue
        mtime = dt.date.fromtimestamp(file_path.stat().st_mtime).isoformat()
        entries.append(
            {
                "id": str(len(entries) + 1),
                "date": mtime,
                "source": file_path.as_posix(),
                "content": read_text(file_path),
            }
        )
    return entries


def score_entry(entry: dict, query_tokens: list[str], query_phrases: list[str]) -> int:
    text = entry["content"].lower()
    token_hits = sum(1 for tok in set(query_tokens) if tok in text)
    phrase_hits = sum(1 for phrase in query_phrases if phrase.lower() in text)
    return token_hits + (phrase_hits * 2)


def search_chat_memory(
    summary: str,
    schema: dict,
    entries: list[dict],
    max_queries: int,
) -> list[dict]:
    search_cfg = schema.get("search_instruction", {})
    expansions = search_cfg.get("query_expansion_rules", [])
    recall_fallback = bool(search_cfg.get("recall_fallback", True))
    time_range = search_cfg.get("time_range", "")
    start_date, end_date = parse_time_range(time_range)

    summary_tokens = tokenize(summary)
    base_query = " ".join(summary_tokens[:10])
    queries = [base_query] + expansions
    queries = [q for q in queries if q][:max_queries]

    def in_time_range(entry_date: str | None) -> bool:
        if not entry_date or not start_date or not end_date:
            return True
        try:
            d = dt.date.fromisoformat(entry_date[:10])
        except ValueError:
            return True
        return start_date <= d <= end_date

    results = {}
    for query in queries:
        query_tokens = tokenize(query)
        if not query_tokens:
            continue
        query_phrases = [query]
        for entry in entries:
            if not in_time_range(entry.get("date")):
                continue
            score = score_entry(entry, query_tokens, query_phrases)
            if score <= 0:
                continue
            key = (entry["source"], entry["content"][:200])
            prev = results.get(key)
            if not prev or score > prev["score"]:
                results[key] = {
                    "score": score,
                    "entry": entry,
                }

    if recall_fallback and len(results) < 3:
        for query in expansions:
            query_tokens = tokenize(query)
            if not query_tokens:
                continue
            for entry in entries:
                if not in_time_range(entry.get("date")):
                    continue
                score = score_entry(entry, query_tokens, [query])
                if score <= 0:
                    continue
                key = (entry["source"], entry["content"][:200])
                prev = results.get(key)
                if not prev or score > prev["score"]:
                    results[key] = {
                        "score": score,
                        "entry": entry,
                    }

    ranked = sorted(results.values(), key=lambda item: item["score"], reverse=True)
    output = []
    for item in ranked:
        entry = item["entry"]
        entry_copy = dict(entry)
        entry_copy["score"] = item["score"]
        output.append(entry_copy)
    return output


def excerpt(text: str, limit: int = 260) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_overlay(
    input_path: Path,
    summary: str,
    keywords: list[str],
    headings: list[str],
    matches: list[dict],
    schema: dict,
    output_path: Path,
) -> str:
    sections = schema.get("output_structure", {}).get("sections", [])
    summary_terms = set(keywords)
    match_terms = []
    for match in matches:
        match_terms.extend(tokenize(match["content"]))
    match_terms_set = set(match_terms)

    reused_terms = sorted(summary_terms & match_terms_set)
    new_terms = sorted(match_terms_set - summary_terms)

    found_echoes = []
    for match in matches[:8]:
        source = match.get("source", "unknown")
        date = match.get("date") or "unknown-date"
        found_echoes.append(f"- {source} ({date}) {excerpt(match['content'])}")

    links = sorted({m.get("source", "") for m in matches if m.get("source")})
    if not summary:
        summary = "No summary extracted."

    lines = []
    lines.append("# AI CodeX Overlay")
    lines.append(f"source: {input_path.as_posix()}")
    lines.append("")

    if "Summary of Paper" in sections:
        lines.append("[!summary] Summary of Paper")
        lines.append(summary)
        if headings:
            lines.append("")
            lines.append("Headings: " + ", ".join(headings[:8]))
        if keywords:
            lines.append("")
            lines.append("Key terms: " + ", ".join(keywords))
        lines.append("")

    if "Found Contextual Echoes" in sections:
        lines.append("[!context] Found Contextual Echoes")
        lines.extend(found_echoes or ["- No contextual echoes found."])
        lines.append("")

    if "Unique Terminology or Framing Reused" in sections:
        lines.append("[!context] Unique Terminology or Framing Reused")
        if reused_terms:
            lines.append("Reused terms: " + ", ".join(reused_terms[:12]))
        else:
            lines.append("Reused terms: none detected")
        lines.append("")

    if "Additional Depth Extracted" in sections:
        lines.append("[!context] Additional Depth Extracted")
        if new_terms:
            lines.append("Additional terms: " + ", ".join(new_terms[:12]))
        else:
            lines.append("Additional terms: none detected")
        lines.append("")

    if "Final Summary" in sections:
        lines.append("[!summary] Final Summary")
        lines.append(
            f"Found {len(matches)} contextual echoes across {len(links)} sources."
        )
        lines.append("")

    if "Links to Original Threads" in sections:
        lines.append("[!origin_links] Links to Original Threads")
        if links:
            lines.extend([f"- {link}" for link in links])
        else:
            lines.append("- No sources linked.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def append_meta_index(meta_index_path: Path, input_path: Path, output_path: Path, matches: list[dict]) -> None:
    meta_index_path.parent.mkdir(parents=True, exist_ok=True)
    now = dt.date.today().isoformat()
    lines = []
    lines.append(f"## {now}")
    lines.append(f"- Paper: {input_path.as_posix()}")
    lines.append(f"- Overlay: {output_path.as_posix()}")
    for match in matches[:10]:
        source = match.get("source", "unknown")
        score = match.get("score", 0)
        lines.append(f"- Match: {source} (score={score})")
    lines.append("")
    existing = ""
    if meta_index_path.exists():
        existing = meta_index_path.read_text(encoding="utf-8", errors="replace")
    meta_index_path.write_text(existing + "\n".join(lines), encoding="utf-8", errors="replace")


def resolve_output_path(input_path: Path, output_name: str, multi_file: bool) -> Path:
    if not multi_file:
        return input_path.parent / output_name
    if output_name != "AI_CodeX_Overlay.md":
        return input_path.parent / output_name
    safe_name = f"AI_CodeX_Overlay_{input_path.stem}.md"
    return input_path.parent / safe_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AI CodeX overlays for papers.")
    parser.add_argument("--input", required=True, help="Path to a .md/.txt file or folder.")
    parser.add_argument("--prompt-schema", help="Path to a prompt schema JSON file.")
    parser.add_argument(
        "--output-name",
        default="AI_CodeX_Overlay.md",
        help="Output filename to use per paper.",
    )
    parser.add_argument(
        "--memory-source",
        help="Path to memory source folder or .jsonl file for local search.",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=5,
        help="Maximum number of search queries to run.",
    )
    parser.add_argument(
        "--log-meta-index",
        action="store_true",
        help="Append links to a meta_index.md file.",
    )
    parser.add_argument(
        "--meta-index",
        default="meta_index.md",
        help="Path to meta_index.md when --log-meta-index is set.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input path not found: {input_path}")

    schema_path = Path(args.prompt_schema) if args.prompt_schema else None
    schema = load_prompt_schema(schema_path)
    memory_source = Path(args.memory_source) if args.memory_source else None
    entries = load_memory_entries(memory_source)

    inputs = collect_inputs(input_path)
    if not inputs:
        raise SystemExit("No input files found.")

    multi_file = len(inputs) > 1
    for file_path in inputs:
        text = read_text(file_path)
        summary, keywords, headings = extract_summary(text)
        matches = search_chat_memory(summary, schema, entries, args.max_queries)
        output_path = resolve_output_path(file_path, args.output_name, multi_file)
        overlay = build_overlay(
            file_path, summary, keywords, headings, matches, schema, output_path
        )
        output_path.write_text(overlay, encoding="utf-8", errors="replace")
        if args.log_meta_index:
            meta_index_path = Path(args.meta_index)
            append_meta_index(meta_index_path, file_path, output_path, matches)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
