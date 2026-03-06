#!/usr/bin/env python3
"""
Theory Downloader - Reads Excel file of consciousness theories,
downloads each URL, converts to clean Markdown, saves to output directory.

Usage:
  cd O:\_Theophysics_v3
  python _theory_downloader.py

Phase 1: Read Excel + dump contents
Phase 2: Install dependencies if needed
Phase 3: Download and convert each URL
"""
import json
import os
import re
import sys
import time
import subprocess

# ── Configuration ──────────────────────────────────────────────────────────
EXCEL_PATH = r"C:\Users\lowes\Downloads\landscape_consciousness_theories_links.xlsx"
OUTPUT_DIR = r"O:\999_IGNORE\Obsidian Programs\Theory_Downloader"
JSON_DUMP  = r"O:\_Theophysics_v3\_excel_output.json"
LOG_FILE   = r"O:\_Theophysics_v3\_download_log.txt"

# ── Phase 0: Install dependencies ─────────────────────────────────────────
def install_deps():
    deps = ["openpyxl", "requests", "beautifulsoup4", "html2text"]
    for dep in deps:
        try:
            pkg = dep.replace("beautifulsoup4", "bs4")
            __import__(pkg)
        except ImportError:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  Installed {dep}")

install_deps()

import openpyxl
import requests
import html2text
from bs4 import BeautifulSoup

# ── Phase 1: Read Excel ───────────────────────────────────────────────────
def read_excel():
    print(f"\n{'='*70}")
    print(f"PHASE 1: Reading Excel file")
    print(f"{'='*70}")
    print(f"  File: {EXCEL_PATH}")

    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active

    print(f"  Sheet: {ws.title}")
    print(f"  Dimensions: {ws.dimensions}")
    print(f"  Rows: {ws.max_row}, Cols: {ws.max_column}")

    # Read headers
    headers = []
    for cell in ws[1]:
        headers.append(cell.value)
    print(f"  Headers: {headers}")
    print()

    # Read all rows
    rows = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        row_data = {}
        for i, val in enumerate(row):
            if i < len(headers):
                row_data[str(headers[i]) if headers[i] else f"col_{i}"] = val
        # Skip completely empty rows
        if any(v is not None for v in row_data.values()):
            rows.append(row_data)

    print(f"  Total data rows: {len(rows)}")
    print(f"\n{'─'*70}")
    print("ALL ROWS:")
    print(f"{'─'*70}")
    for i, r in enumerate(rows, 1):
        print(f"\n  Row {i}:")
        for k, v in r.items():
            if v is not None:
                print(f"    {k}: {v}")

    # Dump to JSON
    with open(JSON_DUMP, "w", encoding="utf-8") as f:
        json.dump({"headers": headers, "total_rows": len(rows), "rows": rows},
                  f, indent=2, default=str, ensure_ascii=False)
    print(f"\n  JSON dump written to: {JSON_DUMP}")

    return headers, rows


# ── Phase 2: Extract URLs and names ──────────────────────────────────────
def extract_urls(headers, rows):
    """Find URL columns and name columns from the data."""
    print(f"\n{'='*70}")
    print(f"PHASE 2: Extracting URLs")
    print(f"{'='*70}")

    # Identify URL columns (look for columns containing http)
    url_cols = []
    name_cols = []
    category_cols = []

    for h in headers:
        if h is None:
            continue
        hl = str(h).lower()
        if any(kw in hl for kw in ["url", "link", "href", "website", "source", "reference"]):
            url_cols.append(str(h))
        if any(kw in hl for kw in ["name", "theory", "title", "label"]):
            name_cols.append(str(h))
        if any(kw in hl for kw in ["category", "type", "class", "group", "domain"]):
            category_cols.append(str(h))

    print(f"  URL columns detected: {url_cols}")
    print(f"  Name columns detected: {name_cols}")
    print(f"  Category columns detected: {category_cols}")

    # If no explicit URL column, scan all values for URLs
    entries = []

    if url_cols:
        for row in rows:
            for uc in url_cols:
                url = row.get(uc)
                if url and str(url).startswith("http"):
                    name = None
                    for nc in name_cols:
                        if row.get(nc):
                            name = str(row[nc])
                            break
                    category = None
                    for cc in category_cols:
                        if row.get(cc):
                            category = str(row[cc])
                            break
                    entries.append({
                        "url": str(url).strip(),
                        "name": name,
                        "category": category,
                        "row_data": {k: str(v) for k, v in row.items() if v is not None}
                    })
    else:
        print("  No explicit URL column found. Scanning all cells for URLs...")
        for row in rows:
            for h, v in row.items():
                if v and str(v).startswith("http"):
                    # Try to find a name from other columns
                    name = None
                    for h2, v2 in row.items():
                        if h2 != h and v2 and not str(v2).startswith("http"):
                            name = str(v2)
                            break
                    entries.append({
                        "url": str(v).strip(),
                        "name": name,
                        "category": None,
                        "row_data": {k: str(val) for k, val in row.items() if val is not None}
                    })

    # Deduplicate by URL
    seen = set()
    unique = []
    for e in entries:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    print(f"  Total URLs found: {len(entries)}")
    print(f"  Unique URLs: {len(unique)}")

    for i, e in enumerate(unique, 1):
        print(f"\n  [{i}] {e['name'] or '(no name)'}")
        print(f"      URL: {e['url']}")
        if e['category']:
            print(f"      Category: {e['category']}")

    return unique


# ── Phase 3: Download and convert ────────────────────────────────────────
def slugify(text, max_len=80):
    """Create a filesystem-safe slug from text."""
    if not text:
        return "unnamed"
    # Remove special chars
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text).strip('_')
    text = text[:max_len]
    return text or "unnamed"


def slug_from_url(url):
    """Create a filename slug from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if path:
        # Use last meaningful path segment
        parts = [p for p in path.split("/") if p and p not in ("index.html", "index.htm", "index.php")]
        if parts:
            return slugify(parts[-1])
    # Fall back to domain
    return slugify(parsed.netloc.replace("www.", ""))


def download_and_convert(url, timeout=30):
    """Download a URL and convert to clean markdown."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                               "aside", "iframe", "noscript", "form",
                               "button", "input", "select", "textarea"]):
        tag.decompose()

    # Remove common ad/nav class patterns
    for pattern in ["nav", "menu", "sidebar", "footer", "header", "ad-", "ads-",
                     "cookie", "popup", "modal", "banner", "social", "share",
                     "comment", "related"]:
        for el in soup.find_all(class_=re.compile(pattern, re.I)):
            el.decompose()
        for el in soup.find_all(id=re.compile(pattern, re.I)):
            el.decompose()

    # Try to find main content
    main = (soup.find("main") or
            soup.find("article") or
            soup.find("div", class_=re.compile(r"content|entry|post|article|body", re.I)) or
            soup.find("div", id=re.compile(r"content|entry|post|article|body", re.I)) or
            soup.body or
            soup)

    # Get page title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)

    # Convert to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.skip_internal_links = True
    h.inline_links = True
    h.protect_links = True
    h.wrap_links = False
    h.wrap_list_items = False
    h.unicode_snob = True

    markdown = h.handle(str(main))

    # Clean up excessive whitespace
    markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
    markdown = markdown.strip()

    return title, markdown


def process_all(entries):
    print(f"\n{'='*70}")
    print(f"PHASE 3: Downloading and converting")
    print(f"{'='*70}")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"  Output dir: {OUTPUT_DIR}")

    log_lines = []
    success = 0
    failed = 0
    skipped = 0

    for i, entry in enumerate(entries, 1):
        url = entry["url"]
        name = entry["name"]
        category = entry.get("category")

        # Build filename
        if name:
            fname = slugify(name)
        else:
            fname = slug_from_url(url)

        # Add category prefix if available
        if category:
            fname = slugify(category) + "__" + fname

        fpath = os.path.join(OUTPUT_DIR, fname + ".md")

        # Handle duplicates
        counter = 1
        while os.path.exists(fpath):
            fpath = os.path.join(OUTPUT_DIR, f"{fname}_{counter}.md")
            counter += 1

        print(f"\n  [{i}/{len(entries)}] {name or fname}")
        print(f"    URL: {url}")

        # Skip PDFs and non-HTML
        if any(url.lower().endswith(ext) for ext in [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip"]):
            msg = f"SKIPPED (non-HTML): {url}"
            print(f"    {msg}")
            log_lines.append(msg)
            skipped += 1

            # Still create a stub file
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"# {name or fname}\n\n")
                f.write(f"**Source:** {url}\n\n")
                if category:
                    f.write(f"**Category:** {category}\n\n")
                f.write(f"*This is a direct download link (PDF/document). Visit the URL to access the content.*\n")
                for k, v in entry.get("row_data", {}).items():
                    f.write(f"- **{k}:** {v}\n")
            continue

        try:
            title, markdown = download_and_convert(url)

            # Build the output markdown
            md_content = f"# {title or name or fname}\n\n"
            md_content += f"**Source:** [{url}]({url})\n"
            if name:
                md_content += f"**Theory:** {name}\n"
            if category:
                md_content += f"**Category:** {category}\n"

            # Add any extra metadata from row
            row_data = entry.get("row_data", {})
            extra_keys = [k for k in row_data if k not in ["url", "link", "URL", "Link"]]
            if extra_keys:
                md_content += "\n**Metadata:**\n"
                for k in extra_keys:
                    md_content += f"- {k}: {row_data[k]}\n"

            md_content += f"\n---\n\n{markdown}\n"

            with open(fpath, "w", encoding="utf-8") as f:
                f.write(md_content)

            size = len(markdown)
            msg = f"OK ({size:,} chars): {name or fname} -> {os.path.basename(fpath)}"
            print(f"    {msg}")
            log_lines.append(msg)
            success += 1

            # Be polite - small delay between requests
            time.sleep(1)

        except requests.exceptions.Timeout:
            msg = f"TIMEOUT: {url}"
            print(f"    {msg}")
            log_lines.append(msg)
            failed += 1
            # Write stub
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"# {name or fname}\n\n**Source:** {url}\n\n*Download timed out. Visit URL directly.*\n")

        except requests.exceptions.HTTPError as e:
            msg = f"HTTP ERROR {e.response.status_code}: {url}"
            print(f"    {msg}")
            log_lines.append(msg)
            failed += 1
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"# {name or fname}\n\n**Source:** {url}\n\n*HTTP Error {e.response.status_code}. Visit URL directly.*\n")

        except Exception as e:
            msg = f"ERROR ({type(e).__name__}: {e}): {url}"
            print(f"    {msg}")
            log_lines.append(msg)
            failed += 1
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(f"# {name or fname}\n\n**Source:** {url}\n\n*Error downloading: {e}*\n")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Total entries: {len(entries)}")
    print(f"  Successful:    {success}")
    print(f"  Failed:        {failed}")
    print(f"  Skipped:       {skipped}")
    print(f"  Output dir:    {OUTPUT_DIR}")
    print(f"  Files created: {success + failed + skipped}")

    # Write log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Theory Downloader Log\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total: {len(entries)} | Success: {success} | Failed: {failed} | Skipped: {skipped}\n")
        f.write(f"{'='*70}\n")
        for line in log_lines:
            f.write(line + "\n")

    print(f"  Log written to: {LOG_FILE}")


# ── Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*70)
    print("THEORY DOWNLOADER")
    print("="*70)

    headers, rows = read_excel()
    entries = extract_urls(headers, rows)

    if not entries:
        print("\nNo URLs found in the spreadsheet. Check the Excel structure.")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"Ready to download {len(entries)} URLs.")
    print(f"Output: {OUTPUT_DIR}")
    resp = input("Proceed? (y/n): ").strip().lower()
    if resp != "y":
        print("Aborted.")
        sys.exit(0)

    process_all(entries)
    print("\nDONE.")
