"""
Math Translation Engine
======================
Scans documents for mathematical equations and applies translations from the
math translation table. Outputs documents with equations isolated in callout boxes
and prepares text for TTS audio generation.
"""

import re
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil


class MathTranslationEngine:
    """
    Engine for processing documents with mathematical equations.
    - Scans folders for markdown documents
    - Detects LaTeX equations
    - Applies translations from Excel table
    - Outputs formatted documents with callout boxes
    - Prepares TTS-ready text
    """
    
    def __init__(self, settings_mgr, db_engine):
        self.settings = settings_mgr
        self.db = db_engine
        self.translation_table: Dict[str, str] = {}
        self.symbol_table: Dict[str, str] = {}
        self.bridge_rows: List[Dict[str, str]] = []
        self.translation_columns: Tuple[str, str] = ("", "")
        self.backend_root = Path(__file__).resolve().parent.parent
        self.excel_path = self._resolve_translation_table_path()
        self.bridge_path = self._resolve_bridge_table_path()
        if not self.excel_path:
            # Keep a stable default path even when missing.
            self.excel_path = self.backend_root / "data" / "MATH_TRANSLATION_TABLE.xlsx"
        self.load_translation_table()
        self.load_bridge_table()

    def _resolve_translation_table_path(self) -> Optional[Path]:
        """Resolve best available translation table path."""
        candidates: List[Path] = []

        # Optional explicit override from settings.
        if self.settings and hasattr(self.settings, "get"):
            try:
                configured = self.settings.get("math", "translation_table_path", "")
                if configured:
                    candidates.append(Path(configured))
            except Exception:
                pass

        # Optional explicit override from environment.
        env_path = os.getenv("MATH_TRANSLATION_TABLE", "").strip()
        if env_path:
            candidates.append(Path(env_path))

        # Explicit user-selected source.
        candidates.append(Path("D:/01_Axioms/04_REFERENCE/MATH_TRANSLATION_TABLE.csv"))

        # Preferred directories (highest quality files first).
        preferred_dirs = [
            Path("O:/999_IGNORE/Obsidian Programs/TTS/Pipeline/config"),
            self.backend_root / "data",
            Path("O:/Theophysics_Backend/TTS_Engines/TTS_Pipeline/config"),
            Path("O:/Theophysics_Backend/TTS_Pipeline"),
            Path("O:/Theophysics_Backend/Python_Backend/Backend Python/data"),
        ]

        preferred_names = [
            "MATH_TRANSLATION_TABLE.csv",
            "MATH_TRANSLATION_MASTER_FIXED.xlsx",
            "MATH_TRANSLATION_MASTER.xlsx",
            "MATH_TRANSLATION_TABLE_UPDATED (1).xlsx",
            "MATH_TRANSLATION_TABLE_UPDATED.xlsx",
            "MATH_TRANSLATION_TABLE.xlsx",
        ]

        for base in preferred_dirs:
            for name in preferred_names:
                candidates.append(base / name)

        # Last-resort glob fallback in preferred directories.
        for base in preferred_dirs:
            try:
                if base.exists():
                    for file in base.glob("MATH_TRANSLATION*.xlsx"):
                        candidates.append(file)
            except Exception:
                pass

        seen = set()
        for path in candidates:
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            if path.exists():
                return path
        return None

    def _resolve_bridge_table_path(self) -> Optional[Path]:
        """Resolve theology-physics bridge table path."""
        candidates: List[Path] = []

        if self.settings and hasattr(self.settings, "get"):
            try:
                configured = self.settings.get("math", "bridge_table_path", "")
                if configured:
                    candidates.append(Path(configured))
            except Exception:
                pass

        env_path = os.getenv("THEOLOGY_PHYSICS_BRIDGE", "").strip()
        if env_path:
            candidates.append(Path(env_path))

        preferred_dirs = [
            Path("O:/999_IGNORE/Obsidian Programs/TTS/Pipeline/config"),
            self.backend_root / "data",
            Path("O:/Theophysics_Backend/TTS_Engines/TTS_Pipeline/config"),
            Path("O:/Theophysics_Backend/TTS_Pipeline/config"),
        ]
        for base in preferred_dirs:
            candidates.append(base / "THEOLOGY_PHYSICS_BRIDGE.xlsx")

        seen = set()
        for path in candidates:
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            if path.exists():
                return path
        return None

    def _detect_translation_columns(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """Detect latex/audio columns safely. Prevent id/source_file misreads."""
        cols = [str(c).strip() for c in df.columns]
        lower = {c: c.lower() for c in cols}

        latex_col = None
        audio_col = None

        # Strict name-based detection first with priority order.
        latex_priority = [
            "latex",
            "symbol_latex",
            "equation",
            "formula",
            "math",
        ]
        audio_priority = [
            "tts_audio",
            "audio",
            "spoken",
            "basic_translation",
            "medium_translation",
            "academic_translation",
            "translation",
            "english",
        ]

        for want in latex_priority:
            for col in cols:
                name = lower[col]
                if name == want or name.endswith(f"_{want}") or want in name:
                    latex_col = col
                    break
            if latex_col:
                break

        for want in audio_priority:
            for col in cols:
                name = lower[col]
                if name == want or name.endswith(f"_{want}") or want in name:
                    audio_col = col
                    break
            if audio_col:
                break

        # Heuristic fallback only if one side missing.
        if latex_col is None:
            best_score = 0.0
            best_col = None
            for col in cols:
                series = df[col].dropna().astype(str).head(120)
                if series.empty:
                    continue
                latex_hits = series.str.contains(r"(\\|\\$|=|\\^|_|\\{|\\})", regex=True).mean()
                numeric_hits = series.str.fullmatch(r"\d+(\.\d+)?").mean()
                score = float(latex_hits) - float(numeric_hits)
                if score > best_score:
                    best_score = score
                    best_col = col
            if best_col is not None and best_score >= 0.35:
                latex_col = best_col

        if audio_col is None:
            best_score = 0.0
            best_col = None
            for col in cols:
                if col == latex_col:
                    continue
                series = df[col].dropna().astype(str).head(120)
                if series.empty:
                    continue
                textish = series.str.contains(r"\s").mean()
                looks_like_path = series.str.contains(r"\.xlsx$|\.csv$|\\|/", regex=True, case=False).mean()
                avg_len = series.map(len).mean()
                score = float(textish) + (0.5 if avg_len > 12 else 0.0) - float(looks_like_path)
                if score > best_score:
                    best_score = score
                    best_col = col
            if best_col is not None and best_score >= 0.40:
                audio_col = best_col

        return latex_col, audio_col
    
    def load_translation_table(self) -> bool:
        """Load the math translation table from Excel."""
        # Clear stale entries before each load/reload.
        self.translation_table.clear()
        self.symbol_table.clear()
        self.translation_columns = ("", "")

        if not self.excel_path.exists():
            print(f"[WARN] Translation table not found at {self.excel_path}")
            return False
        
        try:
            if self.excel_path.suffix.lower() == ".csv":
                df = pd.read_csv(self.excel_path)
            else:
                df = pd.read_excel(self.excel_path)
            latex_col, audio_col = self._detect_translation_columns(df)
            if not latex_col or not audio_col:
                print(
                    f"[ERROR] Could not detect valid latex/audio columns in {self.excel_path.name}. "
                    f"Columns: {list(df.columns)}"
                )
                return False
            self.translation_columns = (str(latex_col), str(audio_col))
            
            for _, row in df.iterrows():
                latex = str(row[latex_col]).strip()
                audio = str(row[audio_col]).strip()
                
                if latex and audio and latex != 'nan' and audio != 'nan':
                    # Store both with and without $ delimiters
                    self.translation_table[latex] = audio
                    self.translation_table[latex.replace('$', '').strip()] = audio
                    clean = latex.replace('$', '').strip()
                    if self._looks_like_symbol(clean):
                        self.symbol_table[clean] = audio
            
            print(f"[INFO] Loaded {len(self.translation_table)} translation pairs")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load translation table: {e}")
            return False

    def _looks_like_symbol(self, text: str) -> bool:
        t = text.strip()
        if not t:
            return False
        if any(ch in t for ch in ["=", "+", "-", "/", "*", " "]):
            return False
        # Typical symbol forms: \chi, G(t), C_{child}, Phi
        return bool(re.fullmatch(r"[\\A-Za-z][\\A-Za-z0-9_{}()]*", t))

    def _symbol_fallback_translation(self, clean_eq: str) -> Optional[str]:
        if not self.symbol_table:
            return None

        rendered = clean_eq

        # Replace longer symbols first.
        for sym, meaning in sorted(self.symbol_table.items(), key=lambda kv: len(kv[0]), reverse=True):
            if len(sym) < 2:
                continue
            rendered = rendered.replace(sym, f" {meaning} ")

        # Operator verbalization.
        replacements = [
            (r"\\cdot", " times "),
            (r"\\times", " times "),
            (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 over \2"),
            (r"\\geq", " greater than or equal to "),
            (r"\\leq", " less than or equal to "),
            (r"\\neq", " not equal to "),
            (r"=", " equals "),
            (r"\+", " plus "),
            (r"-", " minus "),
            (r"\*", " times "),
            (r"/", " over "),
            (r"\^2", " squared "),
            (r"\^3", " cubed "),
            (r"_\{([^}]+)\}", r" sub \1 "),
            (r"_([A-Za-z0-9]+)", r" sub \1 "),
        ]
        for pattern, repl in replacements:
            rendered = re.sub(pattern, repl, rendered)

        rendered = re.sub(r"[{}]", " ", rendered)
        rendered = re.sub(r"\s+", " ", rendered).strip()

        # Must include at least one mapped symbol phrase to be useful.
        if rendered == clean_eq or len(rendered) < 3:
            return None
        return rendered

    def load_bridge_table(self) -> bool:
        """Load theology-physics bridge table as separate conceptual dataset."""
        self.bridge_rows.clear()
        if not self.bridge_path or not self.bridge_path.exists():
            return False
        try:
            df = pd.read_excel(self.bridge_path)
            required = {"physics_concept", "theological_doctrine", "plain_english"}
            cols = {str(c).strip() for c in df.columns}
            if not required.issubset(cols):
                print(
                    f"[WARN] Bridge table columns unexpected in {self.bridge_path.name}: {list(df.columns)}"
                )
                return False
            for _, row in df.iterrows():
                physics = str(row.get("physics_concept", "")).strip()
                theology = str(row.get("theological_doctrine", "")).strip()
                plain = str(row.get("plain_english", "")).strip()
                if physics and theology and plain and physics != "nan" and plain != "nan":
                    self.bridge_rows.append(
                        {
                            "physics_concept": physics,
                            "theological_doctrine": theology,
                            "plain_english": plain,
                            "scripture_ref": str(row.get("scripture_ref", "")).strip(),
                            "jsc_paper": str(row.get("jsc_paper", "")).strip(),
                            "logos_paper": str(row.get("logos_paper", "")).strip(),
                        }
                    )
            if self.bridge_rows:
                print(f"[INFO] Loaded {len(self.bridge_rows)} bridge mappings")
            return len(self.bridge_rows) > 0
        except Exception as e:
            print(f"[WARN] Failed to load bridge table: {e}")
            return False
    
    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Scan a folder for markdown files."""
        if not folder_path.exists():
            return []
        
        md_files = []
        for file in folder_path.rglob("*.md"):
            md_files.append(file)
        
        return md_files
    
    def detect_equations(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect LaTeX equations in text.
        Returns list of (equation, start_pos, end_pos) tuples.
        """
        equations = []
        
        # Pattern for display math $$...$$
        display_pattern = r'\$\$(.*?)\$\$'
        for match in re.finditer(display_pattern, text, re.DOTALL):
            equations.append((match.group(0), match.start(), match.end()))
        
        # Pattern for inline math $...$
        inline_pattern = r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)'
        for match in re.finditer(inline_pattern, text):
            # Skip if it looks like currency
            content = match.group(1)
            if not re.match(r'^\s*\d+[\d,\.]*\s*$', content):
                equations.append((match.group(0), match.start(), match.end()))
        
        return equations
    
    def translate_equation(self, equation: str) -> Optional[str]:
        """Translate a LaTeX equation to spoken text."""
        # Clean the equation
        clean_eq = equation.replace('$', '').strip()
        
        # Try exact match
        if clean_eq in self.translation_table:
            return self.translation_table[clean_eq]
        
        # Try with $ delimiters
        if equation in self.translation_table:
            return self.translation_table[equation]
        
        # Try fuzzy matching (simple containment)
        for key, value in self.translation_table.items():
            if clean_eq in key or key in clean_eq:
                if len(key) > 8:  # Avoid short spurious matches
                    return value

        # Symbol-table fallback (for symbol-level CSVs).
        fallback = self._symbol_fallback_translation(clean_eq)
        if fallback:
            return fallback
        
        return None
    
    def process_document(self, input_path: Path, output_path: Path) -> Dict:
        """
        Process a single document:
        1. Detect equations
        2. Apply translations
        3. Format with callout boxes
        4. Save to output path
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            equations = self.detect_equations(content)
            translated_count = 0
            untranslated_count = 0
            
            # Process equations in reverse order to maintain positions
            for eq, start, end in reversed(equations):
                translation = self.translate_equation(eq)
                
                if translation:
                    translated_count += 1
                    # Obsidian-native two-callout format:
                    # 1) visible equation block
                    # 2) collapsed spoken translation block
                    callout = "\n> [!math] Equation\n"
                    callout += f"> {eq}\n\n"
                    callout += "> [!info]- Spoken Translation\n"
                    callout += f"> {translation}\n\n"
                    
                    # Replace equation with callout
                    content = content[:start] + callout + content[end:]
                else:
                    untranslated_count += 1
            
            # Save processed document
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'input_path': str(input_path),
                'output_path': str(output_path),
                'equations_found': len(equations),
                'translated': translated_count,
                'untranslated': untranslated_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_path': str(input_path)
            }
    
    def process_folder(self, input_folder: Path, output_folder: Path) -> Dict:
        """
        Process all markdown files in a folder.
        Maintains folder structure in output.
        """
        results = {
            'files_processed': 0,
            'equations_found': 0,
            'equations_translated': 0,
            'failed': 0,
            'files': []
        }
        
        md_files = self.scan_folder(input_folder)
        
        for md_file in md_files:
            # Calculate relative path to maintain structure
            rel_path = md_file.relative_to(input_folder)
            output_path = output_folder / rel_path
            
            result = self.process_document(md_file, output_path)
            results['files'].append(result)
            
            if result['success']:
                results['files_processed'] += 1
                results['equations_found'] += result['equations_found']
                results['equations_translated'] += result['translated']
            else:
                results['failed'] += 1
        
        return results
    
    def generate_tts_text(self, processed_file: Path) -> str:
        """
        Extract TTS-ready text from a processed document.
        Removes visual equations, keeps only spoken translations.
        """
        try:
            with open(processed_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract spoken text from callouts
            tts_text = content

            # New format: math block + collapsed spoken block.
            new_callout_pattern = (
                r'> \[!math\].*?\n'
                r'> .*?\n\n'
                r'> \[!info\]-\s*Spoken Translation\n'
                r'> (.*?)\n'
            )

            def replace_new_callout(match):
                spoken = match.group(1)
                return f" {spoken} "

            tts_text = re.sub(new_callout_pattern, replace_new_callout, tts_text, flags=re.DOTALL)

            # Legacy format compatibility.
            legacy_callout_pattern = r'> \[!math\].*?\n> \*\*Visual:\*\*\n> (.*?)\n>\n> \*\*Spoken:\*\*\n> (.*?)\n'

            def replace_legacy_callout(match):
                spoken = match.group(2)
                return f" {spoken} "

            tts_text = re.sub(legacy_callout_pattern, replace_legacy_callout, tts_text, flags=re.DOTALL)
            
            # Remove any remaining LaTeX
            tts_text = re.sub(r'\$\$.*?\$\$', '', tts_text, flags=re.DOTALL)
            tts_text = re.sub(r'\$.*?\$', '', tts_text)
            
            # Clean up markdown
            tts_text = re.sub(r'#+ ', '', tts_text)
            tts_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', tts_text)
            tts_text = re.sub(r'\*([^*]+)\*', r'\1', tts_text)
            
            # Clean whitespace
            tts_text = re.sub(r'\n{3,}', '\n\n', tts_text)
            tts_text = re.sub(r' {2,}', ' ', tts_text)
            
            return tts_text.strip()
            
        except Exception as e:
            return f"Error generating TTS text: {e}"
    
    def get_statistics(self) -> Dict:
        """Get statistics about the translation table."""
        return {
            'total_translations': len(self.translation_table),
            'table_loaded': len(self.translation_table) > 0,
            'excel_path': str(self.excel_path),
            'excel_exists': self.excel_path.exists()
        }
    
    def get_translation_stats(self) -> Dict:
        """Get translation table statistics for UI display."""
        return {
            'loaded': len(self.translation_table) > 0,
            'count': len(self.translation_table),
            'excel_path': str(self.excel_path),
            'excel_exists': self.excel_path.exists(),
            'latex_column': self.translation_columns[0],
            'translation_column': self.translation_columns[1],
            'bridge_path': str(self.bridge_path) if self.bridge_path else "",
            'bridge_exists': bool(self.bridge_path and self.bridge_path.exists()),
            'bridge_loaded': len(self.bridge_rows) > 0,
            'bridge_count': len(self.bridge_rows),
        }
    
    def remove_translations_from_file(self, file_path: Path) -> Dict:
        """
        Remove all math translation callouts from a file.
        Restores original equations without translations.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            callouts_removed = 0

            # New callout pattern.
            new_callout_pattern = (
                r'> \[!math\].*?\n'
                r'> (\$\$?.*?\$\$?)\n\n'
                r'> \[!info\]-\s*Spoken Translation\n'
                r'> .*?\n'
            )

            def replace_new_with_equation(match):
                nonlocal callouts_removed
                callouts_removed += 1
                equation = match.group(1)
                return f"\n{equation}\n"

            content = re.sub(new_callout_pattern, replace_new_with_equation, content, flags=re.DOTALL)

            # Legacy callout compatibility.
            legacy_pattern = r'> \[!math\] Mathematical Equation\n> \*\*Visual:\*\*\n> (\$\$?.*?\$\$?)\n>\n> \*\*Spoken:\*\*\n> .*?\n'
            content = re.sub(legacy_pattern, replace_new_with_equation, content, flags=re.DOTALL)

            # Legacy inline translation format compatibility.
            inline_pattern = r' \[(\$.*?\$) → .*?\] '
            content = re.sub(inline_pattern, r' \1 ', content)
            
            # Clean up extra whitespace
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'callouts_removed': callouts_removed,
                    'modified': True
                }
            else:
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'callouts_removed': 0,
                    'modified': False
                }
                
        except Exception as e:
            return {
                'success': False,
                'file_path': str(file_path),
                'error': str(e)
            }
    
    def remove_translations_from_folder(self, folder_path: Path) -> Dict:
        """
        Remove all math translations from all markdown files in a folder.
        """
        results = {
            'files_processed': 0,
            'files_cleaned': 0,
            'callouts_removed': 0,
            'failed': 0,
            'files': []
        }
        
        md_files = self.scan_folder(folder_path)
        
        for md_file in md_files:
            result = self.remove_translations_from_file(md_file)
            results['files'].append(result)
            
            if result['success']:
                results['files_processed'] += 1
                results['callouts_removed'] += result['callouts_removed']
                if result['modified']:
                    results['files_cleaned'] += 1
            else:
                results['failed'] += 1
        
        return results
