"""
Master Utility - Theophysics Axiom Analysis Suite
Runs all analysis tools and generates comprehensive reports
"""

import os
import sys
from datetime import datetime

# Import all our tools
try:
    import axioms_to_excel
    import prosecution_to_excel
    import cross_reference_validator
    import dependency_graph_generator
    import domain_analyzer
    import missing_content_detector
    import chain_validator
    import worldview_matrix_extractor
    import latex_pdf_generator
    import axiom_search_engine
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all tool scripts are in the same directory.")
    sys.exit(1)

class MasterUtility:
    def __init__(self):
        self.axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
        self.output_dir = r"O:\Theophysics_Backend\Python_Backend"
        self.results = {}
        
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(title.center(80))
        print("=" * 80 + "\n")
    
    def run_all_tools(self):
        """Run all analysis tools"""
        start_time = datetime.now()
        
        self.print_header("THEOPHYSICS MASTER UTILITY")
        print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Source: {self.axioms_folder}")
        print(f"Output: {self.output_dir}\n")
        
        tools = [
            ("Excel Database", self.run_excel_export),
            ("Cross-Reference Validation", self.run_cross_reference),
            ("Dependency Graph", self.run_dependency_graph),
            ("Domain Analysis", self.run_domain_analysis),
            ("Missing Content Detection", self.run_missing_content),
            ("Chain Validation", self.run_chain_validation),
            ("Worldview Matrix", self.run_worldview_matrix),
            ("LaTeX Generation", self.run_latex_generation)
        ]
        
        for i, (name, func) in enumerate(tools, 1):
            self.print_header(f"[{i}/{len(tools)}] {name}")
            try:
                func()
                self.results[name] = "✓ SUCCESS"
            except Exception as e:
                self.results[name] = f"✗ FAILED: {e}"
                print(f"Error: {e}")
        
        # Generate summary report
        self.generate_summary_report(start_time)
    
    def run_excel_export(self):
        """Run Excel database generation"""
        print("Generating Excel database...")
        # Note: Assumes axioms_to_excel.main() exists
        axioms_to_excel.main()
    
    def run_cross_reference(self):
        """Run cross-reference validation"""
        print("Running cross-reference validation...")
        validator = cross_reference_validator.AxiomValidator(self.axioms_folder)
        report = validator.run_all_validations()
        
        output_file = os.path.join(self.output_dir, "validation_report.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ Report saved: {output_file}")
    
    def run_dependency_graph(self):
        """Run dependency graph generation"""
        print("Generating dependency graphs...")
        generator = dependency_graph_generator.DependencyGraphGenerator(self.axioms_folder)
        generator.load_axioms()
        generator.build_graph()
        
        dot_file = os.path.join(self.output_dir, "axiom_dependencies.dot")
        html_file = os.path.join(self.output_dir, "axiom_dependencies.html")
        
        generator.generate_dot_file(dot_file)
        generator.generate_html_interactive(html_file)
        
        print(f"✓ DOT file: {dot_file}")
        print(f"✓ HTML file: {html_file}")
    
    def run_domain_analysis(self):
        """Run domain analysis"""
        print("Analyzing domains...")
        analyzer = domain_analyzer.DomainAnalyzer(self.axioms_folder)
        analyzer.load_axioms()
        
        report = analyzer.generate_domain_report()
        report_file = os.path.join(self.output_dir, "domain_analysis_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        excel_file = os.path.join(self.output_dir, "axioms_by_domain.xlsx")
        analyzer.generate_domain_excel(excel_file)
        
        print(f"✓ Report: {report_file}")
        print(f"✓ Excel: {excel_file}")
    
    def run_missing_content(self):
        """Run missing content detection"""
        print("Detecting missing content...")
        detector = missing_content_detector.MissingContentDetector(self.axioms_folder)
        detector.scan_all_files()
        
        report = detector.generate_report()
        priority = detector.generate_priority_list()
        
        report_file = os.path.join(self.output_dir, "missing_content_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n")
            f.write(priority)
        
        print(f"✓ Report saved: {report_file}")
    
    def run_chain_validation(self):
        """Run chain validation"""
        print("Validating axiom chain...")
        validator = chain_validator.ChainValidator(self.axioms_folder)
        report = validator.run_all_validations()
        
        report_file = os.path.join(self.output_dir, "chain_validation_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ Report saved: {report_file}")
    
    def run_worldview_matrix(self):
        """Run worldview matrix extraction"""
        print("Extracting worldview comparison matrix...")
        extractor = worldview_matrix_extractor.WorldviewMatrixExtractor(self.axioms_folder)
        extractor.load_and_analyze()
        
        report = extractor.generate_matrix_report()
        report_file = os.path.join(self.output_dir, "worldview_matrix_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        excel_file = os.path.join(self.output_dir, "worldview_comparison_matrix.xlsx")
        extractor.generate_matrix_excel(excel_file)
        
        print(f"✓ Report: {report_file}")
        print(f"✓ Excel: {excel_file}")
    
    def run_latex_generation(self):
        """Run LaTeX generation"""
        print("Generating LaTeX document...")
        generator = latex_pdf_generator.LaTeXGenerator(self.axioms_folder)
        generator.load_axioms()
        
        output_file = os.path.join(self.output_dir, "theophysics_axioms.tex")
        generator.save_latex(output_file)
        
        print(f"✓ LaTeX file: {output_file}")
    
    def generate_summary_report(self, start_time):
        """Generate summary report of all operations"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.print_header("EXECUTION SUMMARY")
        
        print(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration.total_seconds():.1f} seconds\n")
        
        print("RESULTS:")
        print("-" * 80)
        for tool, result in self.results.items():
            status = "✓" if "SUCCESS" in result else "✗"
            print(f"{status} {tool}: {result}")
        
        print("\n" + "=" * 80)
        
        success_count = sum(1 for r in self.results.values() if "SUCCESS" in r)
        total_count = len(self.results)
        
        if success_count == total_count:
            print("✓ ALL TOOLS COMPLETED SUCCESSFULLY")
        else:
            print(f"⚠️  {success_count}/{total_count} tools completed successfully")
        
        print("=" * 80)
        
        # Save summary to file
        summary_file = os.path.join(self.output_dir, "master_utility_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("THEOPHYSICS MASTER UTILITY - EXECUTION SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration.total_seconds():.1f} seconds\n\n")
            f.write("RESULTS:\n")
            f.write("-" * 80 + "\n")
            for tool, result in self.results.items():
                f.write(f"{tool}: {result}\n")
            f.write("\n" + "=" * 80 + "\n")
        
        print(f"\n✓ Summary saved: {summary_file}\n")

def show_menu():
    """Show interactive menu"""
    print("\n" + "=" * 80)
    print("THEOPHYSICS MASTER UTILITY - Interactive Menu".center(80))
    print("=" * 80)
    print("\n1. Run ALL tools (full analysis)")
    print("2. Excel Database Generation")
    print("3. Cross-Reference Validation")
    print("4. Dependency Graph Generation")
    print("5. Domain Analysis")
    print("6. Missing Content Detection")
    print("7. Chain Validation")
    print("8. Worldview Comparison Matrix")
    print("9. LaTeX/PDF Generation")
    print("10. Search Engine (Interactive)")
    print("0. Exit")
    print("\n" + "=" * 80)

def main():
    """Main entry point"""
    utility = MasterUtility()
    
    if len(sys.argv) > 1:
        # Command-line mode
        if sys.argv[1] == "--all":
            utility.run_all_tools()
        else:
            print("Usage: python master_utility.py [--all]")
    else:
        # Interactive menu mode
        while True:
            show_menu()
            choice = input("\nSelect option: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                utility.run_all_tools()
            elif choice == '2':
                utility.run_excel_export()
            elif choice == '3':
                utility.run_cross_reference()
            elif choice == '4':
                utility.run_dependency_graph()
            elif choice == '5':
                utility.run_domain_analysis()
            elif choice == '6':
                utility.run_missing_content()
            elif choice == '7':
                utility.run_chain_validation()
            elif choice == '8':
                utility.run_worldview_matrix()
            elif choice == '9':
                utility.run_latex_generation()
            elif choice == '10':
                axiom_search_engine.interactive_search()
            else:
                print("Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
