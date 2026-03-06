"""
Enhanced Math Translation Engine v2
====================================
Multi-layer equation presentation system:
1. Raw equation (boxed)
2. Word-for-word symbolic reading
3. Plain English translation
4. Analogy (if 2+ components)
5. Component breakdown (if 3+ components)

Supports:
- OpenAI for real-time translation
- Ollama for batch overnight processing
- Caching to never translate twice
- Multiple output formats (Markdown, HTML, TTS)

Author: David Lowe / Theophysics Project
"""

import re
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class EquationBreakdown:
    """Complete breakdown of an equation."""
    latex: str
    word_for_word: str
    translation: str
    component_count: int
    components: List[Dict[str, str]]
    analogy: Optional[str] = None
    analogy_explanation: Optional[str] = None
    paper_ref: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class EquationCache:
    """Persistent cache for equation breakdowns."""
    
    def __init__(self, cache_path: Path = None):
        if cache_path is None:
            cache_path = Path("O:/Theophysics_Backend/Python_Backend/Backend Python/data/equation_cache.json")
        self.cache_path = cache_path
        self.cache = self._load()
    
    def _load(self) -> Dict[str, dict]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def get(self, latex: str) -> Optional[EquationBreakdown]:
        key = latex.strip()
        if key in self.cache:
            data = self.cache[key]
            return EquationBreakdown(**data)
        return None
    
    def set(self, latex: str, breakdown: EquationBreakdown):
        self.cache[latex.strip()] = breakdown.to_dict()
        self.save()
    
    def stats(self) -> Dict:
        return {
            'cached_equations': len(self.cache),
            'cache_path': str(self.cache_path)
        }


class AIProvider:
    """Abstract AI provider for equation translation."""
    
    def translate(self, latex: str, context: str = "") -> Optional[EquationBreakdown]:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI-based translation (fast, paid)."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.total_cost = 0.0
    
    def is_available(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "OPENAI_API_KEY not set"
        try:
            from openai import OpenAI
            return True, f"OpenAI ready ({self.model})"
        except ImportError:
            return False, "openai package not installed"
    
    def translate(self, latex: str, context: str = "") -> Optional[EquationBreakdown]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            prompt = self._build_prompt(latex, context)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            
            return EquationBreakdown(
                latex=latex,
                word_for_word=data.get('word_for_word', ''),
                translation=data.get('translation', ''),
                component_count=data.get('component_count', 1),
                components=data.get('components', []),
                analogy=data.get('analogy'),
                analogy_explanation=data.get('analogy_explanation'),
                paper_ref=context if context else None
            )
            
        except Exception as e:
            print(f"[OpenAI ERROR] {e}")
            return None
    
    def _system_prompt(self) -> str:
        return """You are a math translator for the Theophysics project. 
Convert mathematical equations into layered explanations for both visual documents and audio narration.

ALWAYS respond with valid JSON only, no other text."""
    
    def _build_prompt(self, latex: str, context: str = "") -> str:
        return f"""Analyze this equation and return a JSON object with these fields:

EQUATION: {latex}
{f"CONTEXT: {context}" if context else ""}

Return this exact JSON structure:
{{
  "word_for_word": "Read the equation symbol by symbol (e.g., 'Phi effective equals Phi max times e to the negative alpha S')",
  "translation": "Plain English explanation of what the equation means conceptually (under 40 words)",
  "component_count": <number of distinct variables/terms>,
  "components": [
    {{"symbol": "Φ_eff", "meaning": "effective consciousness - what you actually experience"}},
    {{"symbol": "α", "meaning": "sin sensitivity coefficient"}}
  ],
  "analogy": "A relatable real-world analogy (only if component_count >= 2, otherwise null)",
  "analogy_explanation": "Brief explanation of how the analogy maps to the equation (only if component_count >= 3, otherwise null)"
}}

Guidelines for the analogy:
- Use everyday objects: garden hoses, radio tuning, light through fog, bank accounts
- Make it visceral and memorable
- Connect each component to something tangible

Return ONLY the JSON, no other text."""


class OllamaProvider(AIProvider):
    """Ollama-based translation (slow, free, local)."""
    
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def is_available(self) -> Tuple[bool, str]:
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any(self.model in m.get('name', '') for m in models):
                    return True, f"Ollama ready ({self.model})"
                return False, f"Model {self.model} not found. Run: ollama pull {self.model}"
            return False, "Ollama not responding"
        except:
            return False, "Ollama not running. Start with: ollama serve"
    
    def translate(self, latex: str, context: str = "") -> Optional[EquationBreakdown]:
        try:
            import requests
            
            prompt = self._build_prompt(latex, context)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=120  # Longer timeout for local inference
            )
            
            if response.status_code == 200:
                content = response.json().get('response', '').strip()
                
                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    content = content[start:end]
                
                data = json.loads(content)
                
                return EquationBreakdown(
                    latex=latex,
                    word_for_word=data.get('word_for_word', ''),
                    translation=data.get('translation', ''),
                    component_count=data.get('component_count', 1),
                    components=data.get('components', []),
                    analogy=data.get('analogy'),
                    analogy_explanation=data.get('analogy_explanation'),
                    paper_ref=context if context else None
                )
            
            return None
            
        except Exception as e:
            print(f"[Ollama ERROR] {e}")
            return None
    
    def _build_prompt(self, latex: str, context: str = "") -> str:
        # Same prompt as OpenAI
        return OpenAIProvider._build_prompt(self, latex, context)


class EnhancedMathTranslationEngine:
    """
    Enhanced Math Translation Engine with multi-layer output.
    """
    
    def __init__(self, settings_mgr=None, db_engine=None, 
                 provider: str = "openai", api_key: str = None):
        self.settings = settings_mgr
        self.db = db_engine
        self.cache = EquationCache()
        
        # Initialize AI provider
        if provider == "openai":
            self.ai = OpenAIProvider(api_key=api_key)
        elif provider == "ollama":
            self.ai = OllamaProvider()
        else:
            self.ai = None
        
        # Load static translation table as fallback
        self.translation_table = self._load_translation_table()
    
    def _load_translation_table(self) -> Dict[str, str]:
        """Load existing translation table for simple lookups."""
        table = {}
        paths = [
            Path("O:/Theophysics_Backend/TTS_Engines/TTS_Pipeline/config/MATH_TRANSLATION_MASTER.xlsx"),
            Path("O:/Theophysics_Backend/TTS_Engines/TTS_Pipeline/config/MATH_TRANSLATION_MASTER_FIXED.xlsx"),
        ]
        
        for path in paths:
            if path.exists():
                try:
                    df = pd.read_excel(path)
                    for _, row in df.iterrows():
                        latex = str(row.get('latex', '')).strip()
                        audio = str(row.get('tts_audio', '')).strip()
                        if latex and audio and not audio.startswith('When we read'):
                            table[latex] = audio
                            table[latex.replace('$', '').strip()] = audio
                    print(f"[INFO] Loaded {len(table)} translations from {path.name}")
                    break
                except Exception as e:
                    print(f"[WARN] Failed to load {path}: {e}")
        
        return table
    
    def get_breakdown(self, latex: str, context: str = "", 
                      use_ai: bool = True) -> EquationBreakdown:
        """
        Get complete breakdown for an equation.
        
        1. Check cache
        2. Check static table (simple translation only)
        3. Call AI provider
        4. Cache result
        """
        # Check cache
        cached = self.cache.get(latex)
        if cached:
            return cached
        
        # Check static table for simple translation
        clean_latex = latex.replace('$', '').strip()
        if clean_latex in self.translation_table:
            # Create minimal breakdown from static table
            breakdown = EquationBreakdown(
                latex=latex,
                word_for_word=self._generate_word_for_word(latex),
                translation=self.translation_table[clean_latex],
                component_count=1,
                components=[],
                paper_ref=context
            )
            self.cache.set(latex, breakdown)
            return breakdown
        
        # Call AI
        if use_ai and self.ai:
            breakdown = self.ai.translate(latex, context)
            if breakdown:
                self.cache.set(latex, breakdown)
                return breakdown
        
        # Fallback: minimal breakdown
        return EquationBreakdown(
            latex=latex,
            word_for_word=self._generate_word_for_word(latex),
            translation="A mathematical equation from the Theophysics framework.",
            component_count=1,
            components=[],
            paper_ref=context
        )
    
    def _generate_word_for_word(self, latex: str) -> str:
        """Generate basic word-for-word reading."""
        text = latex.replace('$', '').strip()
        
        # Common replacements
        replacements = [
            (r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1 over \2'),
            (r'\\Phi', 'Phi'),
            (r'\\phi', 'phi'),
            (r'\\alpha', 'alpha'),
            (r'\\beta', 'beta'),
            (r'\\gamma', 'gamma'),
            (r'\\delta', 'delta'),
            (r'\\chi', 'chi'),
            (r'\\psi', 'psi'),
            (r'\\sigma', 'sigma'),
            (r'\\lambda', 'lambda'),
            (r'\\mu', 'mu'),
            (r'\\cdot', 'times'),
            (r'\\times', 'times'),
            (r'\\rightarrow', 'approaches'),
            (r'\\geq', 'is greater than or equal to'),
            (r'\\leq', 'is less than or equal to'),
            (r'\\neq', 'is not equal to'),
            (r'\\infty', 'infinity'),
            (r'\^', ' to the power of '),
            (r'_\{([^}]+)\}', r' sub \1'),
            (r'_([a-zA-Z0-9])', r' sub \1'),
            (r'\\text\{([^}]+)\}', r'\1'),
            (r'\\mathrm\{([^}]+)\}', r'\1'),
            (r'\\mathcal\{([^}]+)\}', r'\1'),
            (r'\{', ''),
            (r'\}', ''),
            (r'\\', ''),
        ]
        
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text)
        
        return text.strip()
    
    def format_markdown(self, breakdown: EquationBreakdown) -> str:
        """Format breakdown as Markdown callout box."""
        lines = []
        
        # Start callout
        lines.append("> [!math]+ Mathematical Equation")
        lines.append(">")
        
        # Raw equation
        lines.append("> **Equation:**")
        lines.append(f"> {breakdown.latex}")
        lines.append(">")
        
        # Word for word
        lines.append("> **Read as:**")
        lines.append(f"> *{breakdown.word_for_word}*")
        lines.append(">")
        
        # Translation
        lines.append("> **Meaning:**")
        lines.append(f"> {breakdown.translation}")
        
        # Analogy (if present)
        if breakdown.analogy:
            lines.append(">")
            lines.append("> **Analogy:**")
            lines.append(f"> 💡 {breakdown.analogy}")
            
            if breakdown.analogy_explanation:
                lines.append(f"> {breakdown.analogy_explanation}")
        
        # Components (if multiple)
        if breakdown.component_count >= 3 and breakdown.components:
            lines.append(">")
            lines.append("> **Components:**")
            for comp in breakdown.components:
                symbol = comp.get('symbol', '')
                meaning = comp.get('meaning', '')
                lines.append(f"> • `{symbol}` — {meaning}")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def format_html(self, breakdown: EquationBreakdown) -> str:
        """Format breakdown as HTML box."""
        html = ['<div class="math-breakdown">']
        
        # Equation
        html.append(f'  <div class="equation">{breakdown.latex}</div>')
        
        # Word for word
        html.append(f'  <div class="word-for-word"><em>{breakdown.word_for_word}</em></div>')
        
        # Translation
        html.append(f'  <div class="translation">{breakdown.translation}</div>')
        
        # Analogy
        if breakdown.analogy:
            html.append(f'  <div class="analogy">💡 {breakdown.analogy}</div>')
            if breakdown.analogy_explanation:
                html.append(f'  <div class="analogy-explain">{breakdown.analogy_explanation}</div>')
        
        # Components
        if breakdown.component_count >= 3 and breakdown.components:
            html.append('  <ul class="components">')
            for comp in breakdown.components:
                html.append(f'    <li><code>{comp.get("symbol", "")}</code> — {comp.get("meaning", "")}</li>')
            html.append('  </ul>')
        
        html.append('</div>')
        
        return "\n".join(html)
    
    def format_tts(self, breakdown: EquationBreakdown) -> str:
        """Format breakdown for TTS narration."""
        parts = []
        
        # Main translation
        parts.append(breakdown.translation)
        
        # Analogy (if present and useful)
        if breakdown.analogy and breakdown.component_count >= 2:
            parts.append(f"Think of it this way: {breakdown.analogy}")
        
        return " ".join(parts)
    
    def process_document(self, input_path: Path, output_path: Path,
                        use_ai: bool = True, format: str = "markdown") -> Dict:
        """
        Process a document, replacing equations with breakdowns.
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            equations = self._detect_equations(content)
            processed = 0
            
            # Process in reverse to maintain positions
            for eq, start, end in reversed(equations):
                breakdown = self.get_breakdown(eq, context=input_path.stem, use_ai=use_ai)
                
                if format == "markdown":
                    replacement = self.format_markdown(breakdown)
                elif format == "html":
                    replacement = self.format_html(breakdown)
                elif format == "tts":
                    replacement = self.format_tts(breakdown)
                else:
                    replacement = self.format_markdown(breakdown)
                
                content = content[:start] + replacement + content[end:]
                processed += 1
            
            # Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'input': str(input_path),
                'output': str(output_path),
                'equations_found': len(equations),
                'equations_processed': processed
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input': str(input_path)
            }
    
    def _detect_equations(self, text: str) -> List[Tuple[str, int, int]]:
        """Detect LaTeX equations in text."""
        equations = []
        
        # Display math $$...$$
        for match in re.finditer(r'\$\$(.*?)\$\$', text, re.DOTALL):
            equations.append((match.group(0), match.start(), match.end()))
        
        # Inline math $...$
        for match in re.finditer(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', text):
            content = match.group(1)
            if not re.match(r'^\s*\d+[\d,\.]*\s*$', content):  # Skip currency
                equations.append((match.group(0), match.start(), match.end()))
        
        return equations
    
    def process_folder_batch(self, input_folder: Path, output_folder: Path,
                            use_ai: bool = True, format: str = "markdown",
                            progress_callback=None) -> Dict:
        """
        Batch process a folder (for overnight Ollama runs).
        """
        results = {
            'files_processed': 0,
            'equations_processed': 0,
            'failed': 0,
            'files': []
        }
        
        md_files = list(input_folder.rglob("*.md"))
        total = len(md_files)
        
        for i, md_file in enumerate(md_files):
            if progress_callback:
                progress_callback(i + 1, total, md_file.name)
            
            rel_path = md_file.relative_to(input_folder)
            output_path = output_folder / rel_path
            
            result = self.process_document(md_file, output_path, use_ai=use_ai, format=format)
            results['files'].append(result)
            
            if result['success']:
                results['files_processed'] += 1
                results['equations_processed'] += result['equations_processed']
            else:
                results['failed'] += 1
        
        return results
    
    def get_stats(self) -> Dict:
        """Get engine statistics."""
        ai_status = "Not configured"
        if self.ai:
            available, msg = self.ai.is_available()
            ai_status = msg
        
        return {
            'cache': self.cache.stats(),
            'static_translations': len(self.translation_table),
            'ai_provider': type(self.ai).__name__ if self.ai else None,
            'ai_status': ai_status
        }


# Convenience function
def create_engine(provider: str = "openai", api_key: str = None) -> EnhancedMathTranslationEngine:
    """Create an engine with the specified provider."""
    return EnhancedMathTranslationEngine(provider=provider, api_key=api_key)


if __name__ == "__main__":
    # Quick test
    engine = create_engine(provider="openai")
    print("Engine stats:", engine.get_stats())
    
    # Test equation
    test_eq = r"$\Phi_{eff} = \Phi_{max} \cdot e^{-\alpha S}$"
    print(f"\nTesting: {test_eq}")
    
    breakdown = engine.get_breakdown(test_eq, context="H10", use_ai=True)
    print("\nMarkdown output:")
    print(engine.format_markdown(breakdown))
    
    print("\nTTS output:")
    print(engine.format_tts(breakdown))
