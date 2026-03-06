"""
Overnight Batch Math Translation Runner
========================================
Run this before bed. Uses Ollama (free, local) to process
all equations in your documents.

Usage:
    python run_overnight_math.py "O:\path\to\input" "O:\path\to\output"

Or just run it and it will prompt you.

Author: David Lowe / Theophysics Project
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add engine path
sys.path.insert(0, str(Path(__file__).parent))

from engine.math_translation_engine_v2 import EnhancedMathTranslationEngine

def main():
    print("="*60)
    print("OVERNIGHT MATH TRANSLATION BATCH PROCESSOR")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get paths
    if len(sys.argv) >= 3:
        input_folder = Path(sys.argv[1])
        output_folder = Path(sys.argv[2])
    else:
        print("Enter paths (or press Enter for defaults):")
        
        default_input = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_WORKING_PAPERS"
        input_str = input(f"Input folder [{default_input}]: ").strip()
        input_folder = Path(input_str) if input_str else Path(default_input)
        
        default_output = r"O:\Theophysics_Backend\TTS_Engines\TTS_Pipeline\PROCESSED"
        output_str = input(f"Output folder [{default_output}]: ").strip()
        output_folder = Path(output_str) if output_str else Path(default_output)
    
    print(f"\nInput:  {input_folder}")
    print(f"Output: {output_folder}")
    
    # Check input exists
    if not input_folder.exists():
        print(f"[ERROR] Input folder not found: {input_folder}")
        return 1
    
    # Count files
    md_files = list(input_folder.rglob("*.md"))
    print(f"\nFound {len(md_files)} markdown files")
    
    if not md_files:
        print("[WARN] No files to process")
        return 0
    
    # Choose provider
    print("\nProvider options:")
    print("  1. Ollama (FREE, local, slower - good for overnight)")
    print("  2. OpenAI (paid, fast)")
    
    choice = input("\nChoose (1/2) [1]: ").strip() or "1"
    
    if choice == "2":
        provider = "openai"
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key = input("Enter OpenAI API key: ").strip()
    else:
        provider = "ollama"
        api_key = None
    
    # Create engine
    print(f"\nInitializing {provider} engine...")
    engine = EnhancedMathTranslationEngine(provider=provider, api_key=api_key)
    
    # Check AI availability
    if engine.ai:
        available, msg = engine.ai.is_available()
        print(f"AI Status: {msg}")
        if not available:
            print("[ERROR] AI provider not available")
            return 1
    
    # Confirm
    print(f"\nReady to process {len(md_files)} files")
    print("This may take several hours with Ollama.")
    confirm = input("\nStart processing? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("Aborted.")
        return 0
    
    # Progress callback
    def show_progress(current, total, filename):
        pct = (current / total) * 100
        print(f"[{current}/{total}] ({pct:.1f}%) {filename}")
    
    # Process
    print("\n" + "="*60)
    print("PROCESSING...")
    print("="*60 + "\n")
    
    start_time = datetime.now()
    
    results = engine.process_folder_batch(
        input_folder=input_folder,
        output_folder=output_folder,
        use_ai=True,
        format="markdown",
        progress_callback=show_progress
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Summary
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"Duration: {duration}")
    print(f"Files processed: {results['files_processed']}")
    print(f"Equations processed: {results['equations_processed']}")
    print(f"Failed: {results['failed']}")
    print(f"\nOutput saved to: {output_folder}")
    print(f"Cache stats: {engine.cache.stats()}")
    
    # Save log
    log_path = output_folder / f"batch_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_path, 'w') as f:
        f.write(f"Batch Processing Log\n")
        f.write(f"====================\n")
        f.write(f"Started: {start_time}\n")
        f.write(f"Ended: {end_time}\n")
        f.write(f"Duration: {duration}\n")
        f.write(f"Provider: {provider}\n")
        f.write(f"Input: {input_folder}\n")
        f.write(f"Output: {output_folder}\n")
        f.write(f"\nResults:\n")
        f.write(f"  Files processed: {results['files_processed']}\n")
        f.write(f"  Equations processed: {results['equations_processed']}\n")
        f.write(f"  Failed: {results['failed']}\n")
    
    print(f"\nLog saved to: {log_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
