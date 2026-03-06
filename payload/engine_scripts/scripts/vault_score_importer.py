"""
vault_score_importer.py
-----------------------
Scans any folder in the Theophysics vault for CDCM/CKG scoring files,
imports all new scores into Master Theophysics Obsidian VAULT.xlsx,
then optionally cleans up the source files.

Usage:
    python vault_score_importer.py                        # scan current dir
    python vault_score_importer.py "O:/path/to/folder"   # scan specific folder
    python vault_score_importer.py --clean                # import + delete source files
    python vault_score_importer.py "O:/path" --clean      # both

Handles 3 file formats automatically:
  1. CDCM Master   (Collection, Paper, CDCM_Score, Grade, Sec_A...Sec_K)
  2. CDCM Detail   (*_CDCM_*.csv  with  #, SECTION, SUB-CRITERION, OPENAI_SCORE, OPENAI_NOTES)
  3. CKG Compare   (CKG_Comparison_*.csv  with  paper_id, raw_score, final_score ...)
"""

import os, sys, csv, re
from datetime import datetime
import openpyxl

# ── Config ──────────────────────────────────────────────────────────────────
VAULT_EXCEL = r'C:\Users\lowes\OneDrive\Desktop\Master Theophysics Obsidian VAULT.xlsx'
REGISTRY_SHEET = 'PAPER REGISTRY (2)'
LOG_FILE = r'C:\Users\lowes\OneDrive\Desktop\vault_import_log.txt'

# ── Helpers ──────────────────────────────────────────────────────────────────

def to_cds(score):
    return round(float(score) / 10, 1)

def get_zone(cds_score):
    if cds_score >= 8:   return 'PUBLISH'
    elif cds_score >= 6: return 'REFINE'
    elif cds_score >= 4: return 'TRIAGE'
    else:                return 'SHELVE'

def get_action(z):
    return {
        'PUBLISH': 'Final polish -> submit',
        'REFINE':  'Peer review & tighten',
        'TRIAGE':  'Evaluate: develop or shelve?',
        'SHELVE':  'Major revision needed'
    }[z]

def get_status(grade):
    g = str(grade)
    if g.startswith('A'):   return 'canonical'
    elif g.startswith('B'): return 'validated'
    elif g in ('C+', 'C'):  return 'draft'
    else:                   return 'needs-work'

def get_confidence(grade):
    return {
        'A': 0.92, 'A-': 0.88, 'B+': 0.82, 'B': 0.78,
        'C+': 0.65, 'C': 0.60, 'D': 0.50
    }.get(str(grade), 0.60)

def score_to_grade(score):
    s = float(score)
    if s >= 85:  return 'A'
    elif s >= 80: return 'A-'
    elif s >= 75: return 'B+'
    elif s >= 70: return 'B'
    elif s >= 65: return 'C+'
    elif s >= 55: return 'C'
    else:         return 'D'

def get_weakest(sec_scores):
    """sec_scores = dict like {'A': 7.5, 'B': 6.0, ...}"""
    items = sorted(sec_scores.items(), key=lambda x: x[1])[:2]
    if items:
        return 'Improve: ' + ', '.join('Sec-{}({:.1f})'.format(k, v) for k, v in items)
    return ''

def clean_paper_name(filename):
    """Strip timestamp and _CDCM_ suffix from filename to get paper name."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'_CDCM_\d{8}_\d{6}$', '', name)
    name = re.sub(r'_CKG_\d{8}_\d{6}$', '', name)
    return name.strip()

def make_obsidian_link(paper):
    return '[[{}]]'.format(paper)

def detect_format(filepath):
    """Return 'cdcm_master', 'cdcm_detail', 'ckg', or None."""
    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            header = f.readline().strip().lower()
        if 'collection' in header and 'cdcm_score' in header:
            return 'cdcm_master'
        elif 'sub-criterion' in header and 'openai_score' in header:
            return 'cdcm_detail'
        elif 'paper_id' in header and 'final_score' in header and 'tier1' in header:
            return 'ckgcomp'
        else:
            return None
    except Exception:
        return None

# ── Parsers ──────────────────────────────────────────────────────────────────

def parse_cdcm_master(filepath):
    """Returns list of dicts ready to insert into registry."""
    rows = []
    with open(filepath, encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                cdcm = float(r.get('CDCM_Score', 0))
                grade = r.get('Grade', 'C')
                sec_scores = {}
                for ltr in 'ABCDEFGHIJK':
                    v = r.get('Sec_' + ltr, '')
                    if v and v != '':
                        try:
                            sec_scores[ltr] = float(v)
                        except ValueError:
                            pass
                cds_val = to_cds(cdcm)
                z = get_zone(cds_val)
                rows.append({
                    'title':      r.get('Paper', '').strip(),
                    'series':     r.get('Collection', '').strip(),
                    'domain':     'Theophysics',
                    'cds':        cds_val,
                    'zone':       z,
                    'action':     get_action(z),
                    'status':     get_status(grade),
                    'confidence': get_confidence(grade),
                    'weak':       get_weakest(sec_scores),
                    'notes':      'CDCM: {} | Grade: {}'.format(cdcm, grade),
                    'source':     filepath,
                    'fmt':        'cdcm_master',
                })
            except Exception as e:
                continue
    return rows

def parse_cdcm_detail(filepath):
    """Single-paper CDCM detail file. Compute section averages -> overall score."""
    paper_name = clean_paper_name(os.path.basename(filepath))
    collection = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
    sec_buckets = {}
    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for r in reader:
                criterion_id = r.get('#', '').strip()
                if not criterion_id:
                    continue
                section_ltr = criterion_id[0].upper()
                score_str = r.get('OPENAI_SCORE', '').strip()
                if score_str:
                    try:
                        val = float(score_str)
                        sec_buckets.setdefault(section_ltr, []).append(val)
                    except ValueError:
                        pass
    except Exception:
        return []

    if not sec_buckets:
        return []

    sec_avgs = {k: round(sum(v) / len(v), 2) for k, v in sec_buckets.items()}
    overall = round(sum(sec_avgs.values()) / len(sec_avgs) * 10, 1)
    grade = score_to_grade(overall)
    cds_val = to_cds(overall)
    z = get_zone(cds_val)
    return [{
        'title':      paper_name,
        'series':     collection,
        'domain':     'Theophysics',
        'cds':        cds_val,
        'zone':       z,
        'action':     get_action(z),
        'status':     get_status(grade),
        'confidence': get_confidence(grade),
        'weak':       get_weakest(sec_avgs),
        'notes':      'CDCM Detail computed: {}/100 | Grade: {}'.format(overall, grade),
        'source':     filepath,
        'fmt':        'cdcm_detail',
    }]

def parse_ckg(filepath):
    """CKG Comparison CSV: paper_id, raw_score, final_score, tier1-5."""
    rows = []
    collection = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
    try:
        with open(filepath, encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    final = float(r.get('final_score', 0))
                    title = r.get('paper_id', '').strip()
                    if not title:
                        continue
                    # CKG is scored 0-10 directly
                    cds_val = round(final, 1)
                    cdcm_equiv = cds_val * 10
                    grade = score_to_grade(cdcm_equiv)
                    z = get_zone(cds_val)
                    rows.append({
                        'title':      title,
                        'series':     collection,
                        'domain':     'Theophysics',
                        'cds':        cds_val,
                        'zone':       z,
                        'action':     get_action(z),
                        'status':     get_status(grade),
                        'confidence': get_confidence(grade),
                        'weak':       '',
                        'notes':      'CKG Score: {}/10 | Raw: {}'.format(final, r.get('raw_score', '')),
                        'source':     filepath,
                        'fmt':        'ckgcomp',
                    })
                except Exception:
                    continue
    except Exception:
        pass
    return rows

# ── Scan folder ───────────────────────────────────────────────────────────────

def scan_folder(folder):
    """Return list of (filepath, format) for all scoring files found."""
    found = []
    skip_patterns = ['cdcm_master_all_papers', '~$']
    for dirpath, dirs, files in os.walk(folder):
        for f in files:
            fl = f.lower()
            fp = os.path.join(dirpath, f)
            # Skip temp/lock files
            if any(p in fl for p in skip_patterns):
                continue
            if not fl.endswith('.csv'):
                continue
            fmt = detect_format(fp)
            if fmt:
                found.append((fp, fmt))
    return found

# ── Import to Excel ───────────────────────────────────────────────────────────

def load_existing_titles(ws):
    """Get set of already-registered paper titles (lowercased)."""
    titles = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[1]:
            titles.add(str(row[1]).strip().lower())
    return titles

def append_row(ws, next_row, idx, entry):
    pid = 'IMP-{:03d}'.format(idx)
    data = [
        pid,
        entry['title'],
        entry['series'],
        entry['domain'],
        entry['cds'],
        None,
        None,
        entry['zone'],
        entry['action'],
        entry['status'],
        None,
        None,
        datetime.today(),
        '',
        make_obsidian_link(entry['title']),
        entry['weak'],
        entry['confidence'],
        entry['notes'],
    ]
    for col_idx, val in enumerate(data, start=1):
        ws.cell(row=next_row, column=col_idx, value=val)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    do_clean = '--clean' in args
    args = [a for a in args if a != '--clean']
    scan_dir = args[0] if args else os.getcwd()

    print('=' * 60)
    print('VAULT SCORE IMPORTER')
    print('Scan folder : {}'.format(scan_dir))
    print('Clean after : {}'.format('YES' if do_clean else 'NO (run with --clean to delete source files)'))
    print('=' * 60)

    # Scan
    print('\nScanning for scoring files...')
    found_files = scan_folder(scan_dir)
    print('Found {} scoring files'.format(len(found_files)))
    fmt_counts = {}
    for _, fmt in found_files:
        fmt_counts[fmt] = fmt_counts.get(fmt, 0) + 1
    for fmt, count in fmt_counts.items():
        print('  {:15s}: {}'.format(fmt, count))

    if not found_files:
        print('\nNothing to import. Exiting.')
        return

    # Load workbook
    print('\nLoading vault Excel...')
    wb = openpyxl.load_workbook(VAULT_EXCEL)
    ws = wb[REGISTRY_SHEET]

    existing = load_existing_titles(ws)
    print('Already registered: {} papers'.format(len(existing)))

    # Find next empty row
    next_row = 2
    for r in range(ws.max_row, 1, -1):
        if any(ws.cell(row=r, column=c).value is not None for c in range(1, 19)):
            next_row = r + 1
            break

    # Parse and import
    imported = []
    skipped = []
    errors = []
    import_idx = 1
    processed_files = []

    for filepath, fmt in found_files:
        try:
            if fmt == 'cdcm_master':
                entries = parse_cdcm_master(filepath)
            elif fmt == 'cdcm_detail':
                entries = parse_cdcm_detail(filepath)
            elif fmt == 'ckgcomp':
                entries = parse_ckg(filepath)
            else:
                continue

            file_imported = 0
            for entry in entries:
                title_key = entry['title'].strip().lower()
                if not title_key:
                    continue
                if title_key in existing:
                    skipped.append(entry['title'])
                else:
                    append_row(ws, next_row + import_idx - 1, import_idx, entry)
                    existing.add(title_key)
                    imported.append(entry['title'])
                    import_idx += 1
                    file_imported += 1

            processed_files.append((filepath, file_imported))

        except Exception as e:
            errors.append('{}: {}'.format(os.path.basename(filepath), str(e)))

    # Save
    if imported:
        print('\nSaving {} new entries to vault Excel...'.format(len(imported)))
        wb.save(VAULT_EXCEL)
        print('Saved.')
    else:
        print('\nNo new entries to add — all papers already registered.')

    # Report
    print('\n' + '=' * 60)
    print('IMPORT SUMMARY')
    print('=' * 60)
    print('  Imported : {} new papers'.format(len(imported)))
    print('  Skipped  : {} already in registry'.format(len(skipped)))
    print('  Errors   : {}'.format(len(errors)))
    if errors:
        for e in errors:
            print('    ERROR: {}'.format(e))

    # Write log
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write('VAULT SCORE IMPORT LOG\n')
        log.write('Run: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        log.write('Folder: {}\n\n'.format(scan_dir))
        log.write('IMPORTED ({}):\n'.format(len(imported)))
        for t in imported:
            log.write('  + {}\n'.format(t))
        log.write('\nSKIPPED ({}):\n'.format(len(skipped)))
        for t in skipped:
            log.write('  ~ {}\n'.format(t))
        if errors:
            log.write('\nERRORS:\n')
            for e in errors:
                log.write('  ! {}\n'.format(e))
        log.write('\nFILES PROCESSED:\n')
        for fp, count in processed_files:
            log.write('  [{}] {}\n'.format(count, fp))

    print('\nLog saved to: {}'.format(LOG_FILE))

    # Clean up source files
    if do_clean:
        print('\n' + '=' * 60)
        print('CLEANING UP SOURCE FILES')
        print('=' * 60)
        deleted = 0
        failed = 0
        for filepath, _ in found_files:
            try:
                os.remove(filepath)
                deleted += 1
            except Exception as e:
                print('  Could not delete {}: {}'.format(os.path.basename(filepath), e))
                failed += 1
        print('Deleted: {}  |  Failed: {}'.format(deleted, failed))

        # Also remove empty OpenAI_DATA directories
        print('\nRemoving empty OpenAI_DATA folders...')
        removed_dirs = 0
        for dirpath, dirs, files in os.walk(scan_dir, topdown=False):
            if os.path.basename(dirpath) == 'OpenAI_DATA':
                try:
                    remaining = os.listdir(dirpath)
                    if not remaining:
                        os.rmdir(dirpath)
                        removed_dirs += 1
                except Exception:
                    pass
        print('Removed {} empty OpenAI_DATA folders'.format(removed_dirs))
    else:
        print('\nTip: Run again with --clean to delete the {} source files'.format(len(found_files)))

    print('\nDone.')

if __name__ == '__main__':
    main()
