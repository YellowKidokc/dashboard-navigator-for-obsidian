"""
Practicality Analyzer - Helps determine what's essential vs. over-engineered.
Acts as a filter between vision and implementation.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Complexity(Enum):
    """Complexity levels."""
    SIMPLE = "simple"  # < 1 hour
    MODERATE = "moderate"  # 1-4 hours
    COMPLEX = "complex"  # 4-8 hours
    VERY_COMPLEX = "very_complex"  # 8+ hours


class Priority(Enum):
    """Priority levels."""
    ESSENTIAL = "essential"  # Core functionality, can't work without it
    IMPORTANT = "important"  # Major value, but has workarounds
    NICE_TO_HAVE = "nice_to_have"  # Convenience, not critical
    FUTURE = "future"  # Can be added later


@dataclass
class FeatureAnalysis:
    """Analysis of a feature."""
    name: str
    description: str
    complexity: Complexity
    priority: Priority
    current_implementation: str
    simplified_alternative: str
    effort_saved: str  # e.g., "80% less code"
    value_lost: str  # What we lose by simplifying


class PracticalityAnalyzer:
    """Analyzes features and suggests practical simplifications."""
    
    def analyze_current_system(self) -> List[FeatureAnalysis]:
        """Analyze the current system and suggest simplifications."""
        analyses = []
        
        # Footnote System Analysis
        analyses.append(FeatureAnalysis(
            name="Footnote System",
            description="Auto-generates footnotes with academic + vault links",
            complexity=Complexity.COMPLEX,
            priority=Priority.IMPORTANT,
            current_implementation="""
            - Auto-detects vault links
            - Multiple academic sources per footnote
            - Complex text processing with regex
            - Full footnote management UI
            - Preview system
            """,
            simplified_alternative="""
            - Manual term list → simple footnote markers
            - One academic link per term (best match)
            - Simple text replacement
            - Basic UI: input text, list terms, get output
            - No preview needed, just copy result
            """,
            effort_saved="70% less code, 80% faster to build",
            value_lost="No multi-source links, manual vault links"
        ))
        
        # Definitions Classification Analysis
        analyses.append(FeatureAnalysis(
            name="Definitions Classification",
            description="Classification + folder organization for definitions",
            complexity=Complexity.MODERATE,
            priority=Priority.NICE_TO_HAVE,
            current_implementation="""
            - Classification dropdown with 10+ options
            - Folder organization with auto-creation
            - Metadata in markdown comments
            - Complex file structure
            """,
            simplified_alternative="""
            - Just phrase + definition + aliases (what we had)
            - Add classification later if needed
            - Simple flat file structure
            """,
            effort_saved="50% less code, no file management complexity",
            value_lost="No organization, but can add tags later"
        ))
        
        # Research Link Cascade Analysis
        analyses.append(FeatureAnalysis(
            name="Research Link Cascade",
            description="12-source cascade with priority ordering",
            complexity=Complexity.MODERATE,
            priority=Priority.IMPORTANT,
            current_implementation="""
            - 12 different sources
            - Drag-and-drop priority UI
            - Auto-fallback cascade
            - Custom link management
            """,
            simplified_alternative="""
            - Just 3 sources: Stanford, arXiv, Wikipedia
            - Fixed priority (Stanford → arXiv → Wikipedia)
            - Simple dropdown or checkbox
            """,
            effort_saved="60% less code, simpler UI",
            value_lost="Fewer sources, but covers 90% of use cases"
        ))
        
        return analyses
    
    def get_simplification_plan(self) -> Dict[str, str]:
        """Get a practical simplification plan."""
        return {
            "footnote_system": """
            SIMPLIFIED APPROACH:
            1. User pastes text
            2. User lists terms (one per line)
            3. System adds [1], [2], etc. after each term
            4. System generates simple footnote list at bottom
            5. Each footnote: term, one academic link (best match), optional vault link (manual)
            
            REMOVE:
            - Complex vault link detection
            - Multiple academic sources per footnote
            - Preview system
            - Footnote management UI
            
            KEEP:
            - Text processing
            - Simple footnote generation
            - Copy to clipboard
            """,
            
            "definitions": """
            SIMPLIFIED APPROACH:
            1. Phrase + Definition + Aliases (what we had)
            2. Add classification/folder later if actually needed
            
            REMOVE:
            - Classification dropdown
            - Folder organization
            - Complex file structure
            
            KEEP:
            - Basic definition management
            - Aliases
            """,
            
            "research_links": """
            SIMPLIFIED APPROACH:
            1. Three sources: Stanford, arXiv, Wikipedia
            2. Fixed priority order
            3. Simple checkbox: "Include Stanford", "Include arXiv", etc.
            
            REMOVE:
            - 9 extra sources
            - Drag-and-drop priority
            - Custom link management UI
            
            KEEP:
            - Link generation
            - Text processing
            """
        }
    
    def calculate_effort_reduction(self) -> Tuple[int, int]:
        """Calculate effort reduction from simplifications."""
        # Rough estimates
        current_effort = 100  # arbitrary units
        simplified_effort = 30  # 70% reduction
        
        return current_effort, simplified_effort
    
    def generate_report(self) -> str:
        """Generate a practical simplification report."""
        analyses = self.analyze_current_system()
        plan = self.get_simplification_plan()
        current, simplified = self.calculate_effort_reduction()
        
        report = ["=" * 60]
        report.append("PRACTICALITY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Current System Effort: {current} units")
        report.append(f"Simplified System Effort: {simplified} units")
        report.append(f"Effort Reduction: {((current - simplified) / current * 100):.0f}%")
        report.append("")
        report.append("=" * 60)
        report.append("FEATURE ANALYSES")
        report.append("=" * 60)
        report.append("")
        
        for analysis in analyses:
            report.append(f"📋 {analysis.name}")
            report.append(f"   Priority: {analysis.priority.value.upper()}")
            report.append(f"   Complexity: {analysis.complexity.value.upper()}")
            report.append(f"   Effort Saved: {analysis.effort_saved}")
            report.append(f"   Value Lost: {analysis.value_lost}")
            report.append("")
        
        report.append("=" * 60)
        report.append("SIMPLIFICATION PLANS")
        report.append("=" * 60)
        report.append("")
        
        for feature, plan_text in plan.items():
            report.append(f"🔧 {feature.upper().replace('_', ' ')}")
            report.append(plan_text)
            report.append("")
        
        report.append("=" * 60)
        report.append("RECOMMENDATION")
        report.append("=" * 60)
        report.append("")
        report.append("Build the simplified versions first.")
        report.append("Add complexity only if users actually need it.")
        report.append("90% of the value, 30% of the effort.")
        report.append("")
        
        return "\n".join(report)

