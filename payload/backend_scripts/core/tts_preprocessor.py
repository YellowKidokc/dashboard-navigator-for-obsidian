"""
TTS-Ready Pipeline - Transform Markdown into speech-optimized text
Formal logic implementation for text-to-speech preparation
"""

import re
from typing import Dict, Any


class TTSPreprocessor:
    """
    Universal TTS preparation pipeline.
    Transforms Markdown into speech-optimized text.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize preprocessor with configuration.
        
        Args:
            config: Configuration options
                - strip_latex: bool (default True)
                - verbalize_latex: bool (default False)
                - keep_bullets: bool (default True)
                - expand_acronyms: bool (default True)
                - split_long_sentences: bool (default True)
                - max_sentence_length: int (default 30 words)
        """
        self.config = config or {}
        self.strip_latex = self.config.get('strip_latex', True)
        self.verbalize_latex = self.config.get('verbalize_latex', False)
        self.keep_bullets = self.config.get('keep_bullets', True)
        self.expand_acronyms = self.config.get('expand_acronyms', True)
        self.split_long_sentences = self.config.get('split_long_sentences', True)
        self.max_sentence_length = self.config.get('max_sentence_length', 30)
        
        # Acronym dictionary (first use only)
        self.acronyms_used = set()
        self.acronym_expansions = {
            'IIT': 'I I T, integrated information theory',
            'TTS': 'T T S, text to speech',
            'AI': 'A I, artificial intelligence',
            'QM': 'Q M, quantum mechanics',
            'GR': 'G R, general relativity',
            'PDF': 'P D F',
            'API': 'A P I',
            'GUI': 'G U I, graphical user interface'
        }
    
    def process(self, markdown_text: str) -> str:
        """
        Main pipeline: transform Markdown into TTS-ready text.
        
        Args:
            markdown_text: Raw Markdown text
        
        Returns:
            TTS-optimized text
        """
        text = markdown_text
        
        # 1. Remove Markdown control characters
        text = self._strip_formatting(text)
        
        # 2. Convert headings to pauses
        text = self._convert_headings(text)
        
        # 3. Convert lists
        text = self._convert_lists(text)
        
        # 4. Handle LaTeX
        if self.strip_latex:
            text = self._strip_latex(text)
        elif self.verbalize_latex:
            text = self._verbalize_latex(text)
        
        # 5. Normalize paragraph breaks
        text = self._normalize_paragraphs(text)
        
        # 6. Expand acronyms (first use)
        if self.expand_acronyms:
            text = self._expand_acronyms(text)
        
        # 7. Remove footnotes, citations, links
        text = self._remove_citations(text)
        
        # 8. Handle emphasis
        text = self._handle_emphasis(text)
        
        # 9. Split long sentences
        if self.split_long_sentences:
            text = self._split_long_sentences(text)
        
        # 10. Insert rhetorical pacing
        text = self._insert_pacing(text)
        
        # Final cleanup
        text = self._final_cleanup(text)
        
        return text
    
    def _strip_formatting(self, text: str) -> str:
        """Remove all Markdown formatting symbols."""
        # Code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)
        
        # HTML blocks
        text = re.sub(r'<[^>]+>', '', text)
        
        # Bold, italic, strikethrough
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
        text = re.sub(r'~~([^~]+)~~', r'\1', text)      # ~~strike~~
        
        # Images: ![alt](url) or ![[image.png]]
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'!\[\[([^\]]+)\]\]', '', text)
        
        return text
    
    def _convert_headings(self, text: str) -> str:
        """Convert headings to plain text with pause."""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # Check if heading
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                heading_text = match.group(2)
                result.append(heading_text)
                result.append('')  # Blank line = pause
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _convert_lists(self, text: str) -> str:
        """Convert lists into spoken bullet structure."""
        if not self.keep_bullets:
            # Remove bullet markers
            text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
            return text
        
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # Check if list item
            if re.match(r'^\s*[-*•]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                result.append(line)
                result.append('')  # Short pause after bullet
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _strip_latex(self, text: str) -> str:
        """Remove all LaTeX math."""
        # Block math: $$ ... $$
        text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
        
        # Inline math: $ ... $
        text = re.sub(r'\$[^\$]+\$', '', text)
        
        return text
    
    def _verbalize_latex(self, text: str) -> str:
        """Convert simple LaTeX to verbal math."""
        # Simple replacements
        replacements = {
            r'\+': ' plus ',
            r'-': ' minus ',
            r'\*': ' times ',
            r'=': ' equals ',
            r'\\sum': ' the sum of ',
            r'\\int': ' the integral of ',
            r'\\frac': ' fraction ',
            r'\\pi': ' pi ',
            r'\\Delta': ' delta ',
            r'\\lambda': ' lambda ',
            r'\\chi': ' chi ',
            r'\\psi': ' psi ',
            r'\\Psi': ' psi ',
            r'\^': ' to the power of ',
            r'_': ' subscript '
        }
        
        # Apply replacements to inline math only
        def replace_inline_math(match):
            math_text = match.group(1)
            for pattern, replacement in replacements.items():
                math_text = re.sub(pattern, replacement, math_text)
            return math_text
        
        text = re.sub(r'\$([^\$]+)\$', replace_inline_math, text)
        
        # Block math - just remove
        text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
        
        return text
    
    def _normalize_paragraphs(self, text: str) -> str:
        """Normalize paragraph breaks."""
        # Collapse multiple blank lines to single
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _expand_acronyms(self, text: str) -> str:
        """Expand acronyms on first use."""
        for acronym, expansion in self.acronym_expansions.items():
            if acronym not in self.acronyms_used:
                # Find first occurrence
                pattern = r'\b' + re.escape(acronym) + r'\b'
                match = re.search(pattern, text)
                if match:
                    # Replace first occurrence with expansion
                    text = re.sub(pattern, expansion, text, count=1)
                    self.acronyms_used.add(acronym)
        
        return text
    
    def _remove_citations(self, text: str) -> str:
        """Remove footnotes, citations, and links."""
        # Footnotes: [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Links: [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Wikilinks: [[link]] → link
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        
        # Raw URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        
        return text
    
    def _handle_emphasis(self, text: str) -> str:
        """Convert emphasis to tiny pauses."""
        # Already stripped formatting symbols
        # Could add hair spaces here if needed
        return text
    
    def _split_long_sentences(self, text: str) -> str:
        """Split long sentences at natural boundaries."""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            sentences = re.split(r'([.!?])', line)
            current_sentence = ''
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                punctuation = sentences[i+1] if i+1 < len(sentences) else ''
                
                word_count = len(sentence.split())
                
                if word_count > self.max_sentence_length:
                    # Split at commas, semicolons, or dashes
                    parts = re.split(r'([,;—])', sentence)
                    for j in range(0, len(parts), 2):
                        part = parts[j]
                        separator = parts[j+1] if j+1 < len(parts) else ''
                        current_sentence += part + separator
                        
                        if len(part.split()) > 10:
                            result.append(current_sentence.strip())
                            current_sentence = ''
                    
                    current_sentence += punctuation
                else:
                    current_sentence += sentence + punctuation
            
            if current_sentence.strip():
                result.append(current_sentence.strip())
        
        return '\n'.join(result)
    
    def _insert_pacing(self, text: str) -> str:
        """Insert rhetorical pacing markers."""
        # Add blank line before major transitions
        text = re.sub(r'\.\s+(However|But|Therefore|Thus|Moreover|Furthermore)', r'.\n\n\1', text)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass."""
        # Remove excessive whitespace
        text = re.sub(r' +', ' ', text)
        
        # Remove blank lines at start/end
        text = text.strip()
        
        # Ensure proper spacing
        text = re.sub(r'\n\n+', '\n\n', text)
        
        return text
    
    def get_config_description(self) -> str:
        """Get human-readable description of current config."""
        return f"""TTS Preprocessor Configuration:
- Strip LaTeX: {self.strip_latex}
- Verbalize LaTeX: {self.verbalize_latex}
- Keep Bullets: {self.keep_bullets}
- Expand Acronyms: {self.expand_acronyms}
- Split Long Sentences: {self.split_long_sentences}
- Max Sentence Length: {self.max_sentence_length} words
"""

