"""
Math Translation Layer - Convert LaTeX to English using translation table
Reads from MATH_TRANSLATION_TABLE.csv and generates English explanations
"""

import re
import csv
from pathlib import Path
from typing import Dict, Tuple, List


class MathTranslator:
    """
    Translates LaTeX math to English using translation table.
    Generates three-layer explanations: Basic, Medium, Academic.
    """
    
    def __init__(self, csv_path: str = None):
        """
        Initialize translator with CSV table.
        
        Args:
            csv_path: Path to MATH_TRANSLATION_TABLE.csv
        """
        if csv_path is None:
            csv_path = r"C:\Users\Yellowkid\Desktop\MATH_TRANSLATION_TABLE.csv"
        
        self.csv_path = Path(csv_path)
        self.translation_table = {}
        self._load_table()
    
    def _load_table(self):
        """Load translation table from CSV."""
        if not self.csv_path.exists():
            print(f"⚠️ Warning: Translation table not found at {self.csv_path}")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    latex = row['Symbol_LaTeX'].strip()
                    if latex:
                        self.translation_table[latex] = {
                            'display': row['Symbol_Display'],
                            'category': row['Category'],
                            'name': row['Math_Name'],
                            'basic': row['Basic_Translation'],
                            'medium': row['Medium_Translation'],
                            'academic': row['Academic_Translation'],
                            'info_theory': row['Info_Theory_Equiv'],
                            'context': row['Context_Notes'],
                            'first_appears': row['First_Appears']
                        }
            
            print(f"✅ Loaded {len(self.translation_table)} math symbols")
        
        except Exception as e:
            print(f"❌ Error loading translation table: {e}")
    
    def translate_symbol(self, latex: str, level: str = 'basic') -> str:
        """
        Translate a single LaTeX symbol.
        
        Args:
            latex: LaTeX symbol (e.g., '\\chi', '\\nabla')
            level: Translation level ('basic', 'medium', 'academic')
        
        Returns:
            English translation
        """
        if latex in self.translation_table:
            entry = self.translation_table[latex]
            if level == 'basic':
                return entry['basic'] or entry['medium'] or entry['name']
            elif level == 'medium':
                return entry['medium'] or entry['basic'] or entry['name']
            else:  # academic
                return entry['academic'] or entry['medium'] or entry['name']
        
        # Fallback: just return the LaTeX
        return latex
    
    def translate_equation(
        self,
        latex_eq: str,
        level: str = 'basic',
        include_all_levels: bool = False
    ) -> str:
        """
        Translate an entire equation to English.
        
        Args:
            latex_eq: LaTeX equation string
            level: Default translation level
            include_all_levels: Include all three levels
        
        Returns:
            English translation(s)
        """
        # Simple symbol-by-symbol translation
        # This is a basic version - can be enhanced
        
        result = latex_eq
        
        # Replace known symbols
        for latex_symbol, info in self.translation_table.items():
            if latex_symbol in result:
                translation = self.translate_symbol(latex_symbol, level)
                # Replace LaTeX with English
                result = result.replace(latex_symbol, f"[{translation}]")
        
        # Clean up remaining LaTeX syntax
        result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1 divided by \2)', result)
        result = re.sub(r'\^', ' to the power of ', result)
        result = re.sub(r'_', ' subscript ', result)
        result = result.replace('{', '').replace('}', '')
        result = result.replace('\\', '')
        
        if include_all_levels:
            basic = self.translate_equation(latex_eq, 'basic', False)
            medium = self.translate_equation(latex_eq, 'medium', False)
            academic = self.translate_equation(latex_eq, 'academic', False)
            
            return f"""**Basic:** {basic}
**Medium:** {medium}
**Academic:** {academic}"""
        
        return result
    
    def add_translation_layer(
        self,
        text: str,
        level: str = 'basic',
        format_style: str = 'callout'
    ) -> str:
        """
        Add English translation layers below all LaTeX equations.
        
        Args:
            text: Markdown text with LaTeX
            level: Translation level
            format_style: 'callout', 'plain', or 'comment'
        
        Returns:
            Text with translation layers added
        """
        # Find all inline math: $...$
        inline_pattern = r'\$([^\$]+)\$'
        
        def replace_inline(match):
            latex = match.group(1)
            translation = self.translate_equation(latex, level)
            
            if format_style == 'callout':
                return f"{match.group(0)}\n\n> [!math-translation]\n> {translation}\n"
            elif format_style == 'plain':
                return f"{match.group(0)}\n*Translation: {translation}*\n"
            else:  # comment
                return f"{match.group(0)}\n<!-- {translation} -->\n"
        
        text = re.sub(inline_pattern, replace_inline, text)
        
        # Find all block math: $$...$$
        block_pattern = r'\$\$(.*?)\$\$'
        
        def replace_block(match):
            latex = match.group(1).strip()
            translation = self.translate_equation(latex, level)
            
            if format_style == 'callout':
                return f"{match.group(0)}\n\n> [!math-translation]\n> {translation}\n"
            elif format_style == 'plain':
                return f"{match.group(0)}\n\n**Translation:** {translation}\n"
            else:  # comment
                return f"{match.group(0)}\n<!-- {translation} -->\n"
        
        text = re.sub(block_pattern, replace_block, text, flags=re.DOTALL)
        
        return text
    
    def extract_translations_only(self, text: str, level: str = 'basic') -> str:
        """
        Extract only the English translations (for TTS).
        Removes LaTeX, keeps only translations.
        
        Args:
            text: Markdown text with LaTeX
            level: Translation level
        
        Returns:
            Text with LaTeX removed and translations in place
        """
        # Find all inline math: $...$
        inline_pattern = r'\$([^\$]+)\$'
        
        def replace_inline(match):
            latex = match.group(1)
            translation = self.translate_equation(latex, level)
            return f"\n{translation}\n"
        
        text = re.sub(inline_pattern, replace_inline, text)
        
        # Find all block math: $$...$$
        block_pattern = r'\$\$(.*?)\$\$'
        
        def replace_block(match):
            latex = match.group(1).strip()
            translation = self.translate_equation(latex, level)
            return f"\n\n{translation}\n\n"
        
        text = re.sub(block_pattern, replace_block, text, flags=re.DOTALL)
        
        return text
    
    def get_symbol_info(self, latex: str) -> Dict:
        """Get full info for a symbol."""
        return self.translation_table.get(latex, {})
    
    def list_all_symbols(self) -> List[str]:
        """Get list of all known LaTeX symbols."""
        return list(self.translation_table.keys())
    
    def search_symbols(self, query: str) -> List[Tuple[str, Dict]]:
        """Search symbols by name or translation."""
        query = query.lower()
        results = []
        
        for latex, info in self.translation_table.items():
            if (query in latex.lower() or
                query in info['name'].lower() or
                query in info['basic'].lower() or
                query in info['medium'].lower()):
                results.append((latex, info))
        
        return results

