"""
LaTeX/PDF Generator
Converts axioms to publication-ready LaTeX format
Generates professional academic papers from axiom markdown files
"""

import os
import re
from pathlib import Path
import yaml
from datetime import datetime

def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter from markdown content"""
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return {}
    return {}

def markdown_to_latex(text):
    """Convert markdown formatting to LaTeX"""
    if not text:
        return ""
    
    # Remove wiki links but keep text
    text = re.sub(r'\[\[.*?\|(.*?)\]\]', r'\1', text)
    text = re.sub(r'\[\[(.*?)\]\]', r'\1', text)
    
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    
    # Italic
    text = re.sub(r'\*(.*?)\*', r'\\textit{\1}', text)
    
    # Code/math inline
    text = re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)
    
    # Escape special LaTeX characters
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}'
    }
    
    for char, replacement in replacements.items():
        # Don't escape if already in LaTeX command
        if char not in ['\\', '{', '}']:
            text = text.replace(char, replacement)
    
    return text

def extract_section(content, section_name):
    """Extract content from a specific markdown section"""
    pattern = rf'^##\s+{re.escape(section_name)}\s*\n(.*?)(?=^##\s|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

class LaTeXGenerator:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.axioms = []
        
    def load_axioms(self, axiom_ids=None):
        """Load specific axioms or all axioms"""
        md_files = []
        for f in Path(self.axioms_folder).glob("*.md"):
            if f.is_file() and re.match(r'^\d{3}_', f.name):
                md_files.append(f)
        
        print(f"Loading axiom files...")
        
        for filepath in sorted(md_files):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = extract_yaml_frontmatter(content)
                axiom_id = metadata.get('axiom_id', '')
                
                # Filter if specific axioms requested
                if axiom_ids and axiom_id not in axiom_ids:
                    continue
                
                if axiom_id:
                    # Remove frontmatter from content
                    content_only = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
                    
                    self.axioms.append({
                        'axiom_id': axiom_id,
                        'file': filepath.name,
                        'chain_position': metadata.get('chain_position', 999),
                        'classification': str(metadata.get('classification', '')),
                        'status': metadata.get('status', ''),
                        'stage': metadata.get('stage', 0),
                        'metadata': metadata,
                        'content': content_only
                    })
            except Exception as e:
                print(f"Error loading {filepath.name}: {e}")
        
        # Sort by chain position
        self.axioms.sort(key=lambda x: x['chain_position'])
        
        print(f"✓ Loaded {len(self.axioms)} axioms\n")
    
    def generate_latex_document(self, title="Theophysics Axiom System", author=""):
        """Generate complete LaTeX document"""
        latex = []
        
        # Document class and packages
        latex.append(r"\documentclass[11pt,a4paper]{article}")
        latex.append(r"\usepackage[utf8]{inputenc}")
        latex.append(r"\usepackage[T1]{fontenc}")
        latex.append(r"\usepackage{amsmath,amssymb,amsthm}")
        latex.append(r"\usepackage{geometry}")
        latex.append(r"\usepackage{hyperref}")
        latex.append(r"\usepackage{graphicx}")
        latex.append(r"\usepackage{enumitem}")
        latex.append(r"\usepackage{fancyhdr}")
        latex.append(r"\usepackage{tocloft}")
        latex.append(r"")
        latex.append(r"\geometry{margin=1in}")
        latex.append(r"")
        
        # Custom theorem environments
        latex.append(r"\newtheorem{axiom}{Axiom}")
        latex.append(r"\newtheorem{theorem}{Theorem}")
        latex.append(r"\newtheorem{definition}{Definition}")
        latex.append(r"\newtheorem{proposition}{Proposition}")
        latex.append(r"\newtheorem{lemma}{Lemma}")
        latex.append(r"")
        
        # Title and author
        latex.append(r"\title{" + markdown_to_latex(title) + r"}")
        if author:
            latex.append(r"\author{" + markdown_to_latex(author) + r"}")
        latex.append(r"\date{" + datetime.now().strftime("%B %d, %Y") + r"}")
        latex.append(r"")
        
        # Begin document
        latex.append(r"\begin{document}")
        latex.append(r"\maketitle")
        latex.append(r"\tableofcontents")
        latex.append(r"\newpage")
        latex.append(r"")
        
        # Group axioms by stage
        by_stage = {}
        for axiom in self.axioms:
            stage = axiom['stage']
            if stage not in by_stage:
                by_stage[stage] = []
            by_stage[stage].append(axiom)
        
        # Generate content for each stage
        for stage in sorted(by_stage.keys()):
            latex.append(r"\section{Stage " + str(stage) + r"}")
            latex.append(r"")
            
            for axiom in by_stage[stage]:
                latex.extend(self.generate_axiom_latex(axiom))
                latex.append(r"")
        
        # End document
        latex.append(r"\end{document}")
        
        return "\n".join(latex)
    
    def generate_axiom_latex(self, axiom):
        """Generate LaTeX for a single axiom"""
        latex = []
        
        axiom_id = axiom['axiom_id']
        status = axiom['status']
        content = axiom['content']
        
        # Subsection for axiom
        latex.append(r"\subsection{" + axiom_id + r"}")
        latex.append(r"\label{axiom:" + axiom_id.replace('.', '_') + r"}")
        latex.append(r"")
        
        # Formal statement
        formal = extract_section(content, "Formal Statement")
        if formal:
            env_type = self.get_latex_environment(status)
            latex.append(r"\begin{" + env_type + r"}[" + axiom_id + r"]")
            latex.append(markdown_to_latex(formal))
            latex.append(r"\end{" + env_type + r"}")
            latex.append(r"")
        
        # Dependencies
        depends_on = axiom['metadata'].get('depends_on', [])
        if depends_on:
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            latex.append(r"\textbf{Depends on:} " + ", ".join(depends_on))
            latex.append(r"")
        
        # Physics Layer
        physics = extract_section(content, "Physics Layer")
        if physics:
            latex.append(r"\subsubsection*{Physics Layer}")
            latex.append(markdown_to_latex(physics[:500]))  # Limit length
            latex.append(r"")
        
        # Mathematical Layer
        math_layer = extract_section(content, "Mathematical Layer")
        if math_layer:
            latex.append(r"\subsubsection*{Mathematical Layer}")
            latex.append(markdown_to_latex(math_layer[:500]))  # Limit length
            latex.append(r"")
        
        return latex
    
    def get_latex_environment(self, status):
        """Get appropriate LaTeX environment for axiom type"""
        env_map = {
            'axiom': 'axiom',
            'theorem': 'theorem',
            'definition': 'definition',
            'proposition': 'proposition',
            'lemma': 'lemma',
            'property': 'proposition'
        }
        return env_map.get(status, 'axiom')
    
    def save_latex(self, output_file):
        """Save LaTeX document to file"""
        latex_content = self.generate_latex_document()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"✓ LaTeX file saved: {output_file}")
        print(f"\nTo compile to PDF, run:")
        print(f"  pdflatex {os.path.basename(output_file)}")
        print(f"  pdflatex {os.path.basename(output_file)}  (run twice for TOC)")

def main():
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    output_dir = r"O:\Theophysics_Backend\Python_Backend"
    
    print("=" * 80)
    print("LaTeX/PDF GENERATOR")
    print("=" * 80)
    print(f"\nSource: {axioms_folder}\n")
    
    generator = LaTeXGenerator(axioms_folder)
    
    # Load all axioms
    generator.load_axioms()
    
    # Generate LaTeX
    output_file = os.path.join(output_dir, "theophysics_axioms.tex")
    generator.save_latex(output_file)
    
    print(f"\n✓ LaTeX generation complete!")
    print(f"\nNote: You'll need a LaTeX distribution (e.g., MiKTeX, TeX Live)")
    print(f"to compile the .tex file to PDF.")

if __name__ == "__main__":
    main()
