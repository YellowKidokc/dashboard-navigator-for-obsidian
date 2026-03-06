# engine/__init__.py
"""
Theophysics Research Manager - Engine Package
Contains all backend processing modules
"""

__version__ = "2.2.0"

# Import engines for easy access
from .knowledge_acquisition_engine import (
    KnowledgeAcquisitionEngine,
    EnhancedEntityExtractor,
    SourceLookup,
    ContentDownloader,
    PDFScanner,
    scan_papers_in_directory,
)

from .enhanced_definition_engine import (
    EnhancedDefinitionEngine,
    VaultIndexer,
    DriftDetector,
    ExternalComparator,
)

from .stage_engine import (
    StageEngine,
    create_stage,
)

