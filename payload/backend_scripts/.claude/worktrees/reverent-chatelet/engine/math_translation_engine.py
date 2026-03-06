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
        self.excel_path = Path("O:/Theophysics_Backend/TTS_Pipeline/MATH_TRANSLATION_TABLE_UPDATED (1).xlsx")
        self.load_translation_table()
    
    def load_translation_table(self) -> bool:
        """Load the math translation table from Excel."""
        if not self.excel_path.exists():
            print(f"[WARN] Translation table not found at {self.excel_path}")
            return False
        
        try:
            df = pd.read_excel(self.excel_path)
            
            # Assume first column is LaTeX, last column is audio translation
            latex_col = df.columns[0]
            audio_col = df.columns[-1]
            
            for _, row in df.iterrows():
                latex = str(row[latex_col]).strip()
                audio = str(row[audio_col]).strip()
                
                if latex and audio and latex != 'nan' and audio != 'nan':
                    # Store both with and without $ delimiters
                    self.translation_table[latex] = audio
                    self.translation_table[latex.replace('$', '').strip()] = audio
            
            print(f"[INFO] Loaded {len(self.translation_table)} translation pairs")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load translation table: {e}")
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
                if len(key) > 5:  # Avoid short spurious matches
                    return value
        
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
                    # Create callout box with equation and translation
                    is_display = eq.startswith('$$')
                    
                    if is_display:
                        # Display math - use callout box
                        callout = f"\n> [!math] Mathematical Equation\n"
                        callout += f"> **Visual:**\n> {eq}\n>\n"
                        callout += f"> **Spoken:**\n> {translation}\n\n"
                    else:
                        # Inline math - simpler format
                        callout = f" [{eq} → {translation}] "
                    
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
            'total_files': 0,
            'processed': 0,
            'failed': 0,
            'total_equations': 0,
            'total_translated': 0,
            'total_untranslated': 0,
            'files': []
        }
        
        md_files = self.scan_folder(input_folder)
        results['total_files'] = len(md_files)
        
        for md_file in md_files:
            # Calculate relative path to maintain structure
            rel_path = md_file.relative_to(input_folder)
            output_path = output_folder / rel_path
            
            result = self.process_document(md_file, output_path)
            results['files'].append(result)
            
            if result['success']:
                results['processed'] += 1
                results['total_equations'] += result['equations_found']
                results['total_translated'] += result['translated']
                results['total_untranslated'] += result['untranslated']
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
            
            # Remove visual equation blocks but keep spoken parts
            callout_pattern = r'> \[!math\].*?\n> \*\*Visual:\*\*\n> (.*?)\n>\n> \*\*Spoken:\*\*\n> (.*?)\n'
            
            def replace_callout(match):
                spoken = match.group(2)
                return f" {spoken} "
            
            tts_text = re.sub(callout_pattern, replace_callout, tts_text, flags=re.DOTALL)
            
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
