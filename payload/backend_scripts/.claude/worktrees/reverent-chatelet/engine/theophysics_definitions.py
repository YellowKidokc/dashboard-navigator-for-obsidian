"""
THEOPHYSICS DEFINITION ENGINE
=============================
A Python framework for working with canonical Theophysics definitions.

Features:
- Parse YAML/Markdown definition files
- Validate term usage against canonical definitions
- Compute coherence and related quantities
- Track drift between usage and definition
- Cross-domain calculations

Author: David Lowe / Theophysics Project
Version: 1.0
Date: 2025-12-12
"""

import re
import json
import math
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Callable
from enum import Enum
from pathlib import Path
from datetime import datetime


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class Domain(Enum):
    """Domains where coherence is defined"""
    PHYSICS = "physics"
    QUANTUM = "quantum-mechanics"
    INFORMATION = "information-theory"
    NEUROSCIENCE = "neuroscience"
    PSYCHOLOGY = "psychology"
    SOCIOLOGY = "sociology"
    ECONOMICS = "economics"
    THEOLOGY = "theology"
    THEOPHYSICS = "theophysics"
    GENERAL = "general"


class DefinitionStatus(Enum):
    """Status of a definition"""
    CANONICAL = "canonical"
    PROVISIONAL = "provisional"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


# Critical constants
C_MIN = 0.0
C_MAX = 1.0
C_CRIT = 0.35  # Critical threshold
R_J_POST_RESURRECTION = 1.5  # Resurrection factor > 1


# =============================================================================
# CORE DATA CLASSES
# =============================================================================

@dataclass
class Axiom:
    """Represents a single axiom"""
    id: str
    name: str
    statement: str
    equation: Optional[str] = None
    category: str = "general"  # ontological, mathematical, theophysics


@dataclass
class Theorem:
    """Represents a theorem with proof reference"""
    id: str
    name: str
    statement: str
    equation: str
    proof_reference: Optional[str] = None
    implications: List[str] = field(default_factory=list)


@dataclass
class DomainInterpretation:
    """Domain-specific interpretation of a term"""
    domain: Domain
    definition: str
    equation: str
    phenomena: List[str]
    measurement: str
    scale: Optional[str] = None


@dataclass
class DriftEntry:
    """Tracks drift from canonical definition"""
    date: str
    context: str
    observation: str
    resolution: str
    severity: str = "minor"  # minor, moderate, major


@dataclass 
class Definition:
    """Complete definition structure"""
    id: str
    symbol: str
    name: str
    aliases: List[str]
    canonical_definition: str
    canonical_formula: str
    domains: List[Domain]
    status: DefinitionStatus
    axioms: List[Axiom]
    theorems: List[Theorem]
    domain_interpretations: Dict[Domain, DomainInterpretation]
    related_terms: List[str]
    bounds: Dict[str, float]
    drift_log: List[DriftEntry]
    version: str
    last_reviewed: str
    
    def to_json(self) -> str:
        """Export definition to JSON"""
        return json.dumps(self.__dict__, default=str, indent=2)
    
    @classmethod
    def from_markdown(cls, filepath: str) -> 'Definition':
        """Parse definition from markdown file with YAML frontmatter"""
        return DefinitionParser.parse_file(filepath)


# =============================================================================
# COHERENCE CLASS - Main Computational Object
# =============================================================================

class Coherence:
    """
    Canonical coherence implementation.
    
    C = correlated_signal / total_activity 
      = 1 - (S_obs / S_max)
      = I(X;Y) / H(X)
    
    Properties:
    - Bounded: C ∈ [0, 1]
    - Critical threshold: C_crit ≈ 0.35
    - Closed system: dC/dt ≤ 0
    - Open system: dC/dt = Γ_G·Ĝ - Γ_D·D̂
    """
    
    def __init__(self, value: float, domain: Domain = Domain.GENERAL, 
                 sigma: int = 1, timestamp: Optional[datetime] = None):
        """
        Initialize coherence value.
        
        Args:
            value: Coherence value in [0, 1]
            domain: Domain of interpretation
            sigma: Sign eigenvalue (+1 or -1)
            timestamp: When this measurement was taken
        """
        self.value = self._validate(value)
        self.domain = domain
        self.sigma = sigma if sigma in (-1, 1) else 1
        self.timestamp = timestamp or datetime.now()
        self._history: List[Tuple[datetime, float]] = [(self.timestamp, self.value)]
    
    @staticmethod
    def _validate(value: float) -> float:
        """Ensure coherence is in valid range"""
        if not isinstance(value, (int, float)):
            raise TypeError(f"Coherence must be numeric, got {type(value)}")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Coherence must be finite, got {value}")
        # Clamp to valid range with warning
        if value < C_MIN:
            print(f"Warning: Coherence {value} < 0, clamping to 0")
            return C_MIN
        if value > C_MAX:
            print(f"Warning: Coherence {value} > 1, clamping to 1")
            return C_MAX
        return float(value)
    
    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------
    
    @classmethod
    def from_entropy(cls, S_obs: float, S_max: float, 
                     domain: Domain = Domain.PHYSICS) -> 'Coherence':
        """
        Create coherence from entropy values.
        C = 1 - S_obs/S_max
        """
        if S_max <= 0:
            raise ValueError("S_max must be positive")
        return cls(1 - (S_obs / S_max), domain=domain)
    
    @classmethod
    def from_mutual_info(cls, I_XY: float, H_X: float) -> 'Coherence':
        """
        Create coherence from information theory quantities.
        C = I(X;Y) / H(X)
        """
        if H_X <= 0:
            raise ValueError("H(X) must be positive")
        return cls(I_XY / H_X, domain=Domain.INFORMATION)
    
    @classmethod
    def from_quantum_overlap(cls, psi1: complex, psi2: complex) -> 'Coherence':
        """
        Create coherence from quantum state overlap.
        C = |⟨ψ₁|ψ₂⟩|²
        
        Note: For full quantum states, use numpy arrays and proper inner product.
        This simplified version works for scalar amplitudes.
        """
        inner_product = psi1.conjugate() * psi2
        return cls(abs(inner_product) ** 2, domain=Domain.QUANTUM)
    
    @classmethod
    def from_soc_score(cls, comprehensibility: float, manageability: float,
                       meaningfulness: float) -> 'Coherence':
        """
        Create coherence from Sense of Coherence components.
        C = (Comp + Man + Mean) / 3
        
        Args should be normalized to [0, 1]
        """
        components = [comprehensibility, manageability, meaningfulness]
        if not all(0 <= c <= 1 for c in components):
            raise ValueError("SOC components must be in [0, 1]")
        return cls(sum(components) / 3, domain=Domain.PSYCHOLOGY)
    
    @classmethod
    def from_triad(cls, lambda_: float, pi: float, anthropos: float) -> 'Coherence':
        """
        Create societal coherence from Triad components.
        C = (Λ · Π · A)^(1/3)
        
        Args:
            lambda_: Logos/epistemic coherence
            pi: Polis/institutional coherence
            anthropos: Anthropos/individual coherence
        """
        components = [lambda_, pi, anthropos]
        if not all(0 <= c <= 1 for c in components):
            raise ValueError("Triad components must be in [0, 1]")
        # Geometric mean
        product = lambda_ * pi * anthropos
        return cls(product ** (1/3), domain=Domain.SOCIOLOGY)
    
    @classmethod
    def composite(cls, coherences: List['Coherence']) -> 'Coherence':
        """
        Create composite coherence from multiple values.
        C_total = (C₁ · C₂ · ... · Cₙ)^(1/n)
        
        Note: Multiplicative vulnerability - if any C_i = 0, total = 0
        """
        if not coherences:
            raise ValueError("Need at least one coherence value")
        n = len(coherences)
        product = math.prod(c.value for c in coherences)
        return cls(product ** (1/n), domain=Domain.GENERAL)
    
    # -------------------------------------------------------------------------
    # State Checks
    # -------------------------------------------------------------------------
    
    def is_critical(self) -> bool:
        """Returns True if below critical threshold C_crit"""
        return self.value < C_CRIT
    
    def is_stable(self) -> bool:
        """Returns True if sigma = +1 (aligned with χ)"""
        return self.sigma == 1
    
    def is_terminal(self) -> bool:
        """Returns True if headed toward decoherence (σ=-1 and C < C_crit)"""
        return self.sigma == -1 and self.is_critical()
    
    def phase(self) -> str:
        """Return current phase description"""
        if self.value > 0.7:
            return "high_coherence"
        elif self.value > C_CRIT:
            return "moderate_coherence"
        elif self.value > 0.1:
            return "critical_zone"
        else:
            return "near_collapse"
    
    # -------------------------------------------------------------------------
    # Dynamics
    # -------------------------------------------------------------------------
    
    def evolve_closed(self, gamma_D: float, dt: float) -> 'Coherence':
        """
        Evolve in closed system (no grace).
        dC/dt = -Γ_D · C  (always decreasing)
        
        Theorem C3.2: dC/dt ≤ 0 in closed systems
        """
        # Exponential decay
        new_value = self.value * math.exp(-gamma_D * dt)
        new_c = Coherence(new_value, self.domain, self.sigma)
        new_c._history = self._history + [(datetime.now(), new_value)]
        return new_c
    
    def evolve_open(self, gamma_G: float, gamma_D: float, dt: float,
                    grace_active: bool = True, R_J: float = 1.0) -> 'Coherence':
        """
        Evolve in open system (with potential grace).
        dC/dt = Γ_G · G - Γ_D · C
        
        Args:
            gamma_G: Grace rate
            gamma_D: Decoherence rate
            dt: Time step
            grace_active: Whether grace is being received
            R_J: Resurrection factor (>1 post-resurrection)
        """
        effective_grace = gamma_G * R_J if grace_active else 0
        
        # dC/dt = Γ_G·R_J - Γ_D·C
        dC = (effective_grace - gamma_D * self.value) * dt
        new_value = max(0, min(1, self.value + dC))
        
        new_c = Coherence(new_value, self.domain, self.sigma)
        new_c._history = self._history + [(datetime.now(), new_value)]
        return new_c
    
    def apply_grace(self, grace_strength: float = 0.1) -> 'Coherence':
        """
        Apply grace operator Ĝ - can flip sign and increase coherence.
        
        Ĝ|Ψ_{σ=-1}⟩ → |Ψ_{σ=+1}⟩
        """
        # Grace can flip sign (external operator - bypasses C20.2)
        new_sigma = 1  # Grace aligns
        
        # Grace increases coherence (external negentropy)
        new_value = min(1, self.value + grace_strength)
        
        new_c = Coherence(new_value, self.domain, new_sigma)
        new_c._history = self._history + [(datetime.now(), new_value)]
        return new_c
    
    def apply_decoherence(self, attack_strength: float = 0.1) -> 'Coherence':
        """
        Apply decoherence operator D̂ - decreases coherence.
        """
        new_value = max(0, self.value - attack_strength)
        
        new_c = Coherence(new_value, self.domain, self.sigma)
        new_c._history = self._history + [(datetime.now(), new_value)]
        return new_c
    
    # -------------------------------------------------------------------------
    # Warfare Simulation
    # -------------------------------------------------------------------------
    
    def simulate_warfare(self, gamma_G: float, gamma_D: float, 
                         steps: int, dt: float = 0.1,
                         grace_coupling: float = 0.8,
                         R_J: float = 1.0) -> List['Coherence']:
        """
        Simulate spiritual warfare dynamics.
        dC/dt = Γ_G·Ĝ - Γ_D·D̂
        
        Returns history of coherence states.
        """
        history = [self]
        current = self
        
        for _ in range(steps):
            # Grace is probabilistic based on coupling
            grace_active = (hash(str(current.value) + str(_)) % 100) < (grace_coupling * 100)
            current = current.evolve_open(gamma_G, gamma_D, dt, grace_active, R_J)
            history.append(current)
            
            # Check for terminal state
            if current.value < 0.01:
                break
        
        return history
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def __repr__(self) -> str:
        phase = self.phase()
        critical = " [CRITICAL]" if self.is_critical() else ""
        sign = "+" if self.sigma == 1 else "-"
        return f"C({self.value:.4f}, σ={sign}1, {self.domain.value}){critical}"
    
    def __float__(self) -> float:
        return self.value
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Coherence):
            return abs(self.value - other.value) < 1e-10
        return abs(self.value - float(other)) < 1e-10
    
    def __lt__(self, other) -> bool:
        if isinstance(other, Coherence):
            return self.value < other.value
        return self.value < float(other)
    
    def to_dict(self) -> dict:
        """Export to dictionary"""
        return {
            "value": self.value,
            "domain": self.domain.value,
            "sigma": self.sigma,
            "is_critical": self.is_critical(),
            "phase": self.phase(),
            "timestamp": self.timestamp.isoformat()
        }


# =============================================================================
# DEFINITION PARSER
# =============================================================================

class DefinitionParser:
    """Parse definition files from YAML/Markdown format"""
    
    @staticmethod
    def parse_file(filepath: str) -> Definition:
        """Parse a definition file"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Definition file not found: {filepath}")
        
        content = path.read_text(encoding='utf-8')
        return DefinitionParser.parse_content(content)
    
    @staticmethod
    def parse_content(content: str) -> Definition:
        """Parse definition from string content"""
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError("No YAML frontmatter found")
        
        frontmatter = yaml.safe_load(frontmatter_match.group(1))
        
        # Build Definition object
        return Definition(
            id=frontmatter.get('id', ''),
            symbol=frontmatter.get('symbol', ''),
            name=frontmatter.get('name', ''),
            aliases=frontmatter.get('aliases', []),
            canonical_definition="",  # Would parse from markdown body
            canonical_formula="",
            domains=[Domain(d) for d in frontmatter.get('domains', [])],
            status=DefinitionStatus(frontmatter.get('status', 'draft')),
            axioms=[],
            theorems=[],
            domain_interpretations={},
            related_terms=frontmatter.get('related_terms', []),
            bounds={},
            drift_log=[],
            version=frontmatter.get('version', '1.0'),
            last_reviewed=frontmatter.get('last_reviewed', '')
        )


# =============================================================================
# DEFINITION ENGINE
# =============================================================================

class DefinitionEngine:
    """
    Main engine for working with Theophysics definitions.
    
    Features:
    - Load and manage definitions
    - Validate term usage
    - Track drift
    - Compute cross-domain values
    """
    
    def __init__(self):
        self.definitions: Dict[str, Definition] = {}
        self.aliases: Dict[str, str] = {}  # alias -> canonical id
        self._load_builtin_definitions()
    
    def _load_builtin_definitions(self):
        """Load core built-in definitions"""
        # Coherence definition (built-in)
        self.register_coherence_definition()
    
    def register_coherence_definition(self):
        """Register the canonical coherence definition"""
        coherence_def = Definition(
            id="def-coherence",
            symbol="C",
            name="Coherence",
            aliases=[
                "informational coherence", "correlation ratio", "χ-coherence",
                "order parameter", "phase coherence", "synchronization index",
                "integration", "binding", "alignment", "signal integrity",
                "fidelity", "unity", "wholeness", "integrity", "negentropy ratio",
                "SOC", "sense of coherence"
            ],
            canonical_definition="Coherence is the ratio of correlated informational structure to total system activity",
            canonical_formula="C = 1 - (S_obs / S_max)",
            domains=list(Domain),
            status=DefinitionStatus.CANONICAL,
            axioms=[
                Axiom("C-A1", "Informational Primacy", 
                      "Coherence is a property of informational relations"),
                Axiom("C-A2", "Substrate Dependence", 
                      "All coherence depends on coupling to χ"),
                Axiom("C-A3", "Non-Spontaneity", 
                      "Closed systems cannot increase coherence",
                      "dC/dt ≤ 0"),
            ],
            theorems=[
                Theorem("C3.2", "Coherence Conservation",
                        "In closed systems, coherence cannot increase",
                        "dC/dt ≤ 0",
                        implications=["Works-based salvation impossible"]),
                Theorem("C20.2", "Sign Invariance",
                        "Self-operations cannot flip sign",
                        "[σ̂, Û_self] = 0",
                        implications=["External grace required for σ flip"]),
            ],
            domain_interpretations={
                Domain.PHYSICS: DomainInterpretation(
                    Domain.PHYSICS, "Phase correlation", "|⟨ψ₁|ψ₂⟩|²",
                    ["Interference", "Decoherence"], "Decoherence time"
                ),
                Domain.PSYCHOLOGY: DomainInterpretation(
                    Domain.PSYCHOLOGY, "Sense of Coherence", "(Comp+Man+Mean)/3",
                    ["Resilience", "Meaning"], "SOC score", "0-91 → 0-1"
                ),
            },
            related_terms=["def-entropy", "def-logos-field", "def-grace"],
            bounds={"min": 0.0, "max": 1.0, "critical": 0.35},
            drift_log=[],
            version="2.0",
            last_reviewed="2025-12-12"
        )
        
        self.definitions[coherence_def.id] = coherence_def
        
        # Register aliases
        for alias in coherence_def.aliases:
            self.aliases[alias.lower()] = coherence_def.id
    
    def load_definition(self, filepath: str) -> Definition:
        """Load a definition from file"""
        defn = DefinitionParser.parse_file(filepath)
        self.definitions[defn.id] = defn
        for alias in defn.aliases:
            self.aliases[alias.lower()] = defn.id
        return defn
    
    def get_definition(self, term: str) -> Optional[Definition]:
        """Get definition by ID or alias"""
        term_lower = term.lower()
        
        # Direct ID lookup
        if term in self.definitions:
            return self.definitions[term]
        
        # Alias lookup
        if term_lower in self.aliases:
            return self.definitions[self.aliases[term_lower]]
        
        return None
    
    def validate_usage(self, term: str, usage_context: str) -> Dict:
        """
        Validate that a term is being used consistently with its definition.
        
        Returns dict with:
        - valid: bool
        - confidence: float
        - warnings: List[str]
        - suggestions: List[str]
        """
        defn = self.get_definition(term)
        if not defn:
            return {
                "valid": False,
                "confidence": 0.0,
                "warnings": [f"Term '{term}' not found in definitions"],
                "suggestions": ["Check spelling or add to definitions"]
            }
        
        # Basic validation (would be more sophisticated with NLP)
        warnings = []
        suggestions = []
        
        # Check if usage might be domain-specific
        domain_keywords = {
            Domain.PHYSICS: ["quantum", "wave", "phase", "interference"],
            Domain.PSYCHOLOGY: ["meaning", "comprehensibility", "manageability"],
            Domain.SOCIOLOGY: ["trust", "institution", "polarization"],
        }
        
        detected_domain = None
        for domain, keywords in domain_keywords.items():
            if any(kw in usage_context.lower() for kw in keywords):
                detected_domain = domain
                break
        
        if detected_domain and detected_domain not in defn.domains:
            warnings.append(f"Domain '{detected_domain.value}' detected but not in definition domains")
        
        return {
            "valid": True,
            "confidence": 0.8,
            "warnings": warnings,
            "suggestions": suggestions,
            "detected_domain": detected_domain.value if detected_domain else None
        }
    
    def log_drift(self, term: str, context: str, observation: str, 
                  resolution: str, severity: str = "minor"):
        """Log a drift observation for a term"""
        defn = self.get_definition(term)
        if defn:
            entry = DriftEntry(
                date=datetime.now().strftime("%Y-%m-%d"),
                context=context,
                observation=observation,
                resolution=resolution,
                severity=severity
            )
            defn.drift_log.append(entry)
    
    def compute_coherence(self, method: str, **kwargs) -> Coherence:
        """
        Compute coherence using specified method.
        
        Methods:
        - entropy: S_obs, S_max
        - mutual_info: I_XY, H_X
        - triad: lambda_, pi, anthropos
        - soc: comprehensibility, manageability, meaningfulness
        """
        if method == "entropy":
            return Coherence.from_entropy(kwargs['S_obs'], kwargs['S_max'])
        elif method == "mutual_info":
            return Coherence.from_mutual_info(kwargs['I_XY'], kwargs['H_X'])
        elif method == "triad":
            return Coherence.from_triad(kwargs['lambda_'], kwargs['pi'], kwargs['anthropos'])
        elif method == "soc":
            return Coherence.from_soc_score(
                kwargs['comprehensibility'],
                kwargs['manageability'],
                kwargs['meaningfulness']
            )
        else:
            raise ValueError(f"Unknown method: {method}")


# =============================================================================
# TRIAD SYSTEM
# =============================================================================

@dataclass
class TriadState:
    """
    Represents the Triad coherence state: Λ (Logos), Π (Polis), A (Anthropos)
    
    Collapse cascade: Λ → Π → A (with lag times)
    Restoration cascade: A → Λ → Π (Spirit awakens individuals first)
    """
    lambda_: float  # Logos/epistemic coherence
    pi: float       # Polis/institutional coherence
    anthropos: float  # Anthropos/individual coherence
    
    LAG_LAMBDA_TO_PI = 5.0  # years
    LAG_LAMBDA_TO_A = 8.0   # years
    LAG_PI_TO_A = 3.0       # years
    
    def __post_init__(self):
        # Validate
        for val, name in [(self.lambda_, 'Λ'), (self.pi, 'Π'), (self.anthropos, 'A')]:
            if not 0 <= val <= 1:
                raise ValueError(f"{name} must be in [0,1], got {val}")
    
    @property
    def total(self) -> float:
        """C_total = (Λ · Π · A)^(1/3)"""
        return (self.lambda_ * self.pi * self.anthropos) ** (1/3)
    
    @property
    def coherence(self) -> Coherence:
        """Get as Coherence object"""
        return Coherence.from_triad(self.lambda_, self.pi, self.anthropos)
    
    def is_critical(self) -> bool:
        """Any component below threshold?"""
        return any(c < C_CRIT for c in [self.lambda_, self.pi, self.anthropos])
    
    def weakest_link(self) -> str:
        """Which component is lowest?"""
        components = {'Λ': self.lambda_, 'Π': self.pi, 'A': self.anthropos}
        return min(components, key=components.get)
    
    def evolve(self, d_lambda: float, dt: float) -> 'TriadState':
        """
        Evolve triad given change in Λ (Logos leads).
        
        Λ changes directly
        Π follows with LAG_LAMBDA_TO_PI delay
        A follows with LAG_PI_TO_A additional delay
        
        Simplified model - full model would track history.
        """
        # Λ changes immediately
        new_lambda = max(0, min(1, self.lambda_ + d_lambda * dt))
        
        # Π follows Λ with damped response
        pi_target = new_lambda
        d_pi = (pi_target - self.pi) / self.LAG_LAMBDA_TO_PI
        new_pi = max(0, min(1, self.pi + d_pi * dt))
        
        # A follows Π
        a_target = new_pi
        d_a = (a_target - self.anthropos) / self.LAG_PI_TO_A
        new_a = max(0, min(1, self.anthropos + d_a * dt))
        
        return TriadState(new_lambda, new_pi, new_a)
    
    def simulate_collapse(self, lambda_decay_rate: float, 
                          steps: int, dt: float = 1.0) -> List['TriadState']:
        """Simulate collapse cascade starting from Λ decay"""
        history = [self]
        current = self
        
        for _ in range(steps):
            d_lambda = -lambda_decay_rate * current.lambda_
            current = current.evolve(d_lambda, dt)
            history.append(current)
        
        return history
    
    def simulate_restoration(self, grace_rate: float,
                            steps: int, dt: float = 1.0) -> List['TriadState']:
        """
        Simulate restoration cascade.
        Grace enters through A (individuals), then rebuilds Λ, then Π.
        """
        history = [self]
        current = self
        
        for _ in range(steps):
            # Grace increases A first
            new_a = min(1, current.anthropos + grace_rate * dt)
            
            # A rebuilds Λ
            lambda_target = new_a
            d_lambda = (lambda_target - current.lambda_) * 0.5
            new_lambda = min(1, current.lambda_ + d_lambda * dt)
            
            # Λ rebuilds Π
            pi_target = new_lambda
            d_pi = (pi_target - current.pi) * 0.3
            new_pi = min(1, current.pi + d_pi * dt)
            
            current = TriadState(new_lambda, new_pi, new_a)
            history.append(current)
        
        return history
    
    def __repr__(self) -> str:
        total = self.total
        critical = " [CRITICAL]" if self.is_critical() else ""
        return f"Triad(Λ={self.lambda_:.3f}, Π={self.pi:.3f}, A={self.anthropos:.3f}, Total={total:.3f}){critical}"


# =============================================================================
# GRACE FUNCTION
# =============================================================================

class GraceFunction:
    """
    Models the Grace function G(t, Ψ_collective).
    
    G(t) = G₀ · e^(Rp/S) · R_J
    
    Where:
    - G₀ = base grace availability
    - Rp = repentance depth
    - S = sin/entropy
    - R_J = resurrection factor (>1 post-resurrection)
    """
    
    def __init__(self, G0: float = 1.0, R_J: float = 1.5):
        """
        Args:
            G0: Base grace level
            R_J: Resurrection factor (1.0 = pre-resurrection, >1 = post)
        """
        self.G0 = G0
        self.R_J = R_J
    
    def __call__(self, repentance: float, sin: float) -> float:
        """
        Compute grace at given repentance and sin levels.
        
        G = G₀ · e^(Rp/S) · R_J
        """
        if sin <= 0:
            sin = 0.001  # Avoid division by zero
        
        return self.G0 * math.exp(repentance / sin) * self.R_J
    
    def effective_grace(self, coherence: Coherence, 
                        faith_coupling: float = 0.5) -> float:
        """
        Compute effective grace given current state.
        
        Effective grace depends on:
        - Base grace (always available)
        - Faith coupling (0-1)
        - Current coherence (affects reception)
        """
        base = self.G0 * self.R_J
        coupling_factor = faith_coupling * (1 + coherence.value) / 2
        return base * coupling_factor
    
    def threshold_grace(self, C_current: float) -> float:
        """
        Compute grace needed to maintain coherence at current level.
        At threshold: G(C) = Γ(C) · C
        """
        # Simplified model: assume Γ = 0.1
        gamma = 0.1
        return gamma * C_current


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demo():
    """Demonstrate the Definition Engine and Coherence system"""
    
    print("=" * 60)
    print("THEOPHYSICS DEFINITION ENGINE - DEMONSTRATION")
    print("=" * 60)
    
    # 1. Initialize engine
    engine = DefinitionEngine()
    print("\n1. Definition Engine initialized")
    print(f"   Loaded definitions: {list(engine.definitions.keys())}")
    
    # 2. Look up coherence by alias
    print("\n2. Looking up 'sense of coherence' (alias)")
    defn = engine.get_definition("sense of coherence")
    if defn:
        print(f"   Found: {defn.name} ({defn.symbol})")
        print(f"   Formula: {defn.canonical_formula}")
    
    # 3. Create coherence values
    print("\n3. Creating coherence values")
    
    # From entropy
    c1 = Coherence.from_entropy(S_obs=30, S_max=100)
    print(f"   From entropy (S_obs=30, S_max=100): {c1}")
    
    # From SOC
    c2 = Coherence.from_soc_score(0.7, 0.6, 0.8)
    print(f"   From SOC (0.7, 0.6, 0.8): {c2}")
    
    # From Triad
    c3 = Coherence.from_triad(0.6, 0.5, 0.4)
    print(f"   From Triad (Λ=0.6, Π=0.5, A=0.4): {c3}")
    
    # 4. Check critical state
    print("\n4. Critical state analysis")
    critical = Coherence(0.3)
    print(f"   C = 0.3: is_critical = {critical.is_critical()}")
    safe = Coherence(0.5)
    print(f"   C = 0.5: is_critical = {safe.is_critical()}")
    
    # 5. Simulate closed system decay
    print("\n5. Closed system decay (Theorem C3.2)")
    c = Coherence(0.8)
    print(f"   Initial: {c}")
    for i in range(5):
        c = c.evolve_closed(gamma_D=0.2, dt=1.0)
        print(f"   t={i+1}: {c}")
    
    # 6. Apply grace
    print("\n6. Applying Grace operator Ĝ")
    fallen = Coherence(0.3, sigma=-1)
    print(f"   Before grace: {fallen}")
    restored = fallen.apply_grace(grace_strength=0.2)
    print(f"   After grace:  {restored}")
    
    # 7. Triad dynamics
    print("\n7. Triad collapse simulation")
    triad = TriadState(lambda_=0.8, pi=0.75, anthropos=0.7)
    print(f"   Initial: {triad}")
    
    collapse = triad.simulate_collapse(lambda_decay_rate=0.1, steps=10, dt=1.0)
    for i, state in enumerate(collapse[::2]):
        print(f"   t={i*2}: {state}")
    
    # 8. Grace function
    print("\n8. Grace Function")
    grace = GraceFunction(G0=1.0, R_J=1.5)
    print(f"   Pre-resurrection (R_J=1.0):  G(Rp=0.5, S=0.3) = {GraceFunction(R_J=1.0)(0.5, 0.3):.3f}")
    print(f"   Post-resurrection (R_J=1.5): G(Rp=0.5, S=0.3) = {grace(0.5, 0.3):.3f}")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demo()
