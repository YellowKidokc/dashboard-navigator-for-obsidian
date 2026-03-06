# scripts/generate_stages.py
"""
Batch generator for Theophysics 110-Stage Framework.
Uses stage_engine with Ollama integration for auto-YAML.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.settings import SettingsManager
from engine.stage_engine import StageEngine
from engine.ai_engine import AIEngine
from engine.database_engine import DatabaseEngine


# =============================================================================
# STAGE DEFINITIONS
# =============================================================================

# Part I: Foundations (1-10)
PART_I_STAGES = [
    {"stage_num": 1, "movement": "Ontological Foundation", "physics_parallel": "It from Bit"},
    {"stage_num": 2, "movement": "Information Primacy", "physics_parallel": "Shannon Entropy"},
    {"stage_num": 3, "movement": "The Observer Requirement", "physics_parallel": "Measurement Problem"},
    {"stage_num": 4, "movement": "Causal Closure", "physics_parallel": "Conservation Laws"},
    {"stage_num": 5, "movement": "Modal Necessity", "physics_parallel": "Physical Constants"},
    {"stage_num": 6, "movement": "Emergence Hierarchy", "physics_parallel": "Phase Transitions"},
    {"stage_num": 7, "movement": "Temporal Asymmetry", "physics_parallel": "Arrow of Time"},
    {"stage_num": 8, "movement": "Boundary Conditions", "physics_parallel": "Initial Conditions"},
    {"stage_num": 9, "movement": "Self-Reference Paradox", "physics_parallel": "Gödel Incompleteness"},
    {"stage_num": 10, "movement": "The Necessity of Transcendence", "physics_parallel": "External Observer"},
]

# Part II: Divine Domain (11-30) - Heavy Griffiths E&M parallels
PART_II_STAGES = [
    {"stage_num": 11, "movement": "The Aseity Constraint", "physics_parallel": "Uncaused Field"},
    {"stage_num": 12, "movement": "Non-Local Primacy", "physics_parallel": "Action at Distance"},
    {"stage_num": 13, "movement": "Singularity of Intent", "physics_parallel": "Initial Potential Φ"},
    {"stage_num": 14, "movement": "Triune Coherence", "physics_parallel": "3-Phase Symmetry (Trinity as Eigenstates)"},
    {"stage_num": 15, "movement": "Scalar Sovereignty", "physics_parallel": "Field Strength |χ|"},
    {"stage_num": 16, "movement": "Divine Simplicity", "physics_parallel": "Information Minimization"},
    {"stage_num": 17, "movement": "Logos Logic Gate", "physics_parallel": "Universal If/Then (John 1:1)"},
    {"stage_num": 18, "movement": "Omniscience as Data-Set", "physics_parallel": "Total Kolmogorov Complexity"},
    {"stage_num": 19, "movement": "Eternal Persistence", "physics_parallel": "Unitary Evolution"},
    {"stage_num": 20, "movement": "The Holiness Gradient", "physics_parallel": "Potential Difference V"},
    {"stage_num": 21, "movement": "Separation of Essence", "physics_parallel": "Boundary Conditions"},
    {"stage_num": 22, "movement": "Emanation Vector", "physics_parallel": "Poynting Vector S (Glory)"},
    {"stage_num": 23, "movement": "Frequency of Word", "physics_parallel": "Wave-Nature f=E/h"},
    {"stage_num": 24, "movement": "Immutable Law", "physics_parallel": "Constants c, ℏ"},
    {"stage_num": 25, "movement": "Intercessory Induction", "physics_parallel": "Magnetic Induction"},
    {"stage_num": 26, "movement": "Covenant Bond", "physics_parallel": "Strong Interaction"},
    {"stage_num": 27, "movement": "Divine Superposition", "physics_parallel": "Both/And Grace/Justice"},
    {"stage_num": 28, "movement": "Infinite Bandwidth", "physics_parallel": "Holy Spirit Field Capacity"},
    {"stage_num": 29, "movement": "Judgment Operator", "physics_parallel": "Wavefunction Collapse"},
    {"stage_num": 30, "movement": "Kingdom Topology", "physics_parallel": "Geometry of New Jerusalem"},
]

# Part III: Spiritual Dynamics (31-50)
PART_III_STAGES = [
    {"stage_num": 31, "movement": "χ-Field Definition", "physics_parallel": "Field Theory Basics"},
    {"stage_num": 32, "movement": "Spiritual Wavelength", "physics_parallel": "de Broglie λ = h/p"},
    {"stage_num": 33, "movement": "Grace Amplitude", "physics_parallel": "Wave Amplitude"},
    {"stage_num": 34, "movement": "Sin as Phase Disruption", "physics_parallel": "Destructive Interference"},
    {"stage_num": 35, "movement": "Repentance as Re-phasing", "physics_parallel": "Constructive Interference"},
    {"stage_num": 36, "movement": "Faith Resonance", "physics_parallel": "Driven Oscillator"},
    {"stage_num": 37, "movement": "Prayer Transmission", "physics_parallel": "Signal Propagation"},
    {"stage_num": 38, "movement": "Angelic Operators", "physics_parallel": "Messenger Particles"},
    {"stage_num": 39, "movement": "Demonic Damping", "physics_parallel": "Dissipative Forces"},
    {"stage_num": 40, "movement": "Spiritual Warfare", "physics_parallel": "Field Interference"},
    {"stage_num": 41, "movement": "Anointing Transfer", "physics_parallel": "Energy Transfer"},
    {"stage_num": 42, "movement": "Prophetic Prediction", "physics_parallel": "Deterministic Chaos"},
    {"stage_num": 43, "movement": "Miracle as Singularity", "physics_parallel": "Discontinuous Jump"},
    {"stage_num": 44, "movement": "Healing Restoration", "physics_parallel": "Error Correction"},
    {"stage_num": 45, "movement": "Gifts Distribution", "physics_parallel": "Energy Level Occupation"},
    {"stage_num": 46, "movement": "Body of Christ Coherence", "physics_parallel": "Bose-Einstein Condensate"},
    {"stage_num": 47, "movement": "Church as Antenna", "physics_parallel": "Collective Resonance"},
    {"stage_num": 48, "movement": "Worship Amplification", "physics_parallel": "Stimulated Emission"},
    {"stage_num": 49, "movement": "Revival Cascade", "physics_parallel": "Chain Reaction"},
    {"stage_num": 50, "movement": "Kingdom Expansion", "physics_parallel": "Diffusion Dynamics"},
]

# Part IV: Human Ontology (51-70)
PART_IV_STAGES = [
    {"stage_num": 51, "movement": "Soul Definition", "physics_parallel": "Bound State"},
    {"stage_num": 52, "movement": "Consciousness Emergence", "physics_parallel": "Integrated Information Φ"},
    {"stage_num": 53, "movement": "Free Will Degrees", "physics_parallel": "Phase Space"},
    {"stage_num": 54, "movement": "Memory as State Vector", "physics_parallel": "Quantum State"},
    {"stage_num": 55, "movement": "Emotion as Energy", "physics_parallel": "Kinetic Energy"},
    {"stage_num": 56, "movement": "Reason as Logic Gate", "physics_parallel": "Boolean Operations"},
    {"stage_num": 57, "movement": "Intuition Channel", "physics_parallel": "Quantum Tunneling"},
    {"stage_num": 58, "movement": "Conscience Detector", "physics_parallel": "Threshold Function"},
    {"stage_num": 59, "movement": "Heart Orientation", "physics_parallel": "Spin State"},
    {"stage_num": 60, "movement": "Mind-Body Bridge", "physics_parallel": "Coupling Constant"},
    {"stage_num": 61, "movement": "Spirit-Soul Interface", "physics_parallel": "Boundary Layer"},
    {"stage_num": 62, "movement": "Death Transition", "physics_parallel": "Phase Transition"},
    {"stage_num": 63, "movement": "Resurrection Body", "physics_parallel": "Higher Eigenstate"},
    {"stage_num": 64, "movement": "Identity Persistence", "physics_parallel": "Conserved Quantity"},
    {"stage_num": 65, "movement": "Relational Entanglement", "physics_parallel": "Quantum Entanglement"},
    {"stage_num": 66, "movement": "Inheritance Transfer", "physics_parallel": "Genetic Information"},
    {"stage_num": 67, "movement": "Generational Momentum", "physics_parallel": "Inertia"},
    {"stage_num": 68, "movement": "Calling Trajectory", "physics_parallel": "Geodesic Path"},
    {"stage_num": 69, "movement": "Sanctification Process", "physics_parallel": "Annealing"},
    {"stage_num": 70, "movement": "Glorification Limit", "physics_parallel": "Asymptotic State"},
]

# Part V: Material World (71-90)
PART_V_STAGES = [
    {"stage_num": 71, "movement": "Creation Ex Nihilo", "physics_parallel": "Vacuum Fluctuation"},
    {"stage_num": 72, "movement": "Cosmic Fine-Tuning", "physics_parallel": "Anthropic Principle"},
    {"stage_num": 73, "movement": "Light Creation", "physics_parallel": "Photon Genesis"},
    {"stage_num": 74, "movement": "Matter Formation", "physics_parallel": "Baryogenesis"},
    {"stage_num": 75, "movement": "Life Origin", "physics_parallel": "Abiogenesis"},
    {"stage_num": 76, "movement": "Evolution Direction", "physics_parallel": "Entropy Gradient"},
    {"stage_num": 77, "movement": "Humanity Emergence", "physics_parallel": "Complexity Threshold"},
    {"stage_num": 78, "movement": "Fall Thermodynamics", "physics_parallel": "Entropy Increase"},
    {"stage_num": 79, "movement": "Curse Propagation", "physics_parallel": "Decay Rate"},
    {"stage_num": 80, "movement": "Flood Reset", "physics_parallel": "System Restart"},
    {"stage_num": 81, "movement": "Nations Dispersion", "physics_parallel": "Diffusion"},
    {"stage_num": 82, "movement": "Israel Selection", "physics_parallel": "Resonance Peak"},
    {"stage_num": 83, "movement": "Incarnation Event", "physics_parallel": "Field Manifestation"},
    {"stage_num": 84, "movement": "Cross Mechanics", "physics_parallel": "Energy Exchange"},
    {"stage_num": 85, "movement": "Resurrection Physics", "physics_parallel": "State Transformation"},
    {"stage_num": 86, "movement": "Ascension Dynamics", "physics_parallel": "Dimensional Shift"},
    {"stage_num": 87, "movement": "Pentecost Distribution", "physics_parallel": "Field Permeation"},
    {"stage_num": 88, "movement": "Church Age Dynamics", "physics_parallel": "Steady State"},
    {"stage_num": 89, "movement": "Tribulation Perturbation", "physics_parallel": "System Instability"},
    {"stage_num": 90, "movement": "Second Coming Event", "physics_parallel": "Phase Transition"},
]

# Part VI: Synthesis & χ = Christ (91-110)
PART_VI_STAGES = [
    {"stage_num": 91, "movement": "χ-Field Summary", "physics_parallel": "Field Unification"},
    {"stage_num": 92, "movement": "Equation Integration", "physics_parallel": "Unified Field Theory"},
    {"stage_num": 93, "movement": "Predictive Power", "physics_parallel": "Falsifiability"},
    {"stage_num": 94, "movement": "Experimental Protocol", "physics_parallel": "Measurement Design"},
    {"stage_num": 95, "movement": "Theological Consistency", "physics_parallel": "Internal Coherence"},
    {"stage_num": 96, "movement": "Scientific Compatibility", "physics_parallel": "External Coherence"},
    {"stage_num": 97, "movement": "Objection Responses", "physics_parallel": "Error Analysis"},
    {"stage_num": 98, "movement": "Edge Cases", "physics_parallel": "Boundary Behavior"},
    {"stage_num": 99, "movement": "Future Predictions", "physics_parallel": "Extrapolation"},
    {"stage_num": 100, "movement": "χ = Christ Thesis", "physics_parallel": "Central Identity"},
    {"stage_num": 101, "movement": "Logos Mathematics", "physics_parallel": "Divine Calculus"},
    {"stage_num": 102, "movement": "Trinity Eigenstates", "physics_parallel": "Three-State System"},
    {"stage_num": 103, "movement": "Incarnation Mechanics", "physics_parallel": "Field Collapse"},
    {"stage_num": 104, "movement": "Atonement Thermodynamics", "physics_parallel": "Entropy Transfer"},
    {"stage_num": 105, "movement": "Resurrection Proof", "physics_parallel": "State Verification"},
    {"stage_num": 106, "movement": "Ascension Topology", "physics_parallel": "Dimensional Mapping"},
    {"stage_num": 107, "movement": "Return Prediction", "physics_parallel": "Trajectory Analysis"},
    {"stage_num": 108, "movement": "Eternal State", "physics_parallel": "Ground State"},
    {"stage_num": 109, "movement": "New Creation Physics", "physics_parallel": "New Phase Space"},
    {"stage_num": 110, "movement": "Omega Point", "physics_parallel": "Convergence Limit"},
]

ALL_STAGES = PART_I_STAGES + PART_II_STAGES + PART_III_STAGES + PART_IV_STAGES + PART_V_STAGES + PART_VI_STAGES


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("  THEOPHYSICS 110-STAGE GENERATOR")
    print("=" * 60)
    print()
    
    # Load settings
    settings = SettingsManager()
    settings.load()
    
    # Initialize engines
    try:
        db = DatabaseEngine(settings)
    except:
        db = None
        print("⚠ Database not connected (continuing without)")
    
    try:
        ai = AIEngine(settings, db)
        status = ai.is_available()
        print(f"AI Status: OpenAI={status['openai']}, Anthropic={status['anthropic']}, Ollama={status['ollama']}")
    except Exception as e:
        ai = None
        print(f"⚠ AI Engine not available: {e}")
    
    # Create stage engine
    stage_engine = StageEngine(settings, db, ai)
    
    # Menu
    print()
    print("Options:")
    print("  1. Generate ALL 110 stages")
    print("  2. Generate Part I only (1-10)")
    print("  3. Generate Part II only (11-30)")
    print("  4. Generate Part III only (31-50)")
    print("  5. Generate Part IV only (51-70)")
    print("  6. Generate Part V only (71-90)")
    print("  7. Generate Part VI only (91-110)")
    print("  8. Generate single stage")
    print("  9. Test Ollama YAML generation")
    print("  0. Exit")
    print()
    
    choice = input("Select option: ").strip()
    
    if choice == "1":
        print(f"\nGenerating all {len(ALL_STAGES)} stages...")
        created = stage_engine.batch_create_stages(ALL_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "2":
        print(f"\nGenerating Part I ({len(PART_I_STAGES)} stages)...")
        created = stage_engine.batch_create_stages(PART_I_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "3":
        print(f"\nGenerating Part II ({len(PART_II_STAGES)} stages)...")
        created = stage_engine.batch_create_stages(PART_II_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "4":
        print(f"\nGenerating Part III ({len(PART_III_STAGES)} stages)...")
        created = stage_engine.batch_create_stages(PART_III_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "5":
        print(f"\nGenerating Part IV ({len(PART_IV_STAGES)} stages)...")
        created = stage_engine.batch_create_stages(PART_IV_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "6":
        print(f"\nGenerating Part V ({len(PART_V_STAGES)} stages)...")
        created = stage_engine.batch_create_stages(PART_V_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "7":
        print(f"\nGenerating Part VI ({len(PART_VI_STAGES)} stages)...")
        created = stage_engine.batch_create_stages(PART_VI_STAGES)
        print(f"\n✓ Created {len(created)} stage files")
        
    elif choice == "8":
        stage_num = int(input("Enter stage number (1-110): "))
        movement = input("Enter movement title: ")
        physics = input("Enter physics parallel: ")
        path = stage_engine.create_stage_file(stage_num, movement, physics)
        print(f"\n✓ Created: {path}")
        
    elif choice == "9":
        if ai and ai.ollama_available:
            print("\nTesting Ollama YAML generation...")
            test_content = """# Stage 14: Triune Coherence
            
This stage establishes the mathematical necessity of Trinity structure.
The three independent differential operations in vector calculus 
(gradient, divergence, curl) parallel the three Persons."""
            
            yaml_result = ai.generate_yaml_frontmatter(test_content, "stage")
            print("\nGenerated YAML:")
            print("---")
            print(yaml_result)
            print("---")
        else:
            print("\n⚠ Ollama not available. Download from: https://ollama.ai")
            print("  Then run: ollama pull llama3.2")
    
    elif choice == "0":
        print("Exiting...")
        return
    
    else:
        print("Invalid option")
    
    print()
    print("Output directory:", stage_engine.output_dir)


if __name__ == "__main__":
    main()
