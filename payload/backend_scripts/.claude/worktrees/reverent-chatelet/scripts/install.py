#!/usr/bin/env python3
"""
Theophysics Manager - Universal Installation Script

This script handles:
- Python version checking
- Virtual environment creation
- Dependency installation
- Configuration setup
- Port availability checking
- Troubleshooting and error recovery

Works on: Windows, Linux, macOS, Replit, Cloud environments
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
import json
import socket

class Colors:
    """ANSI color codes for pretty output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")

def print_error(text):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {text}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {text}")

def check_python_version():
    """Check if Python version is 3.10+"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    print_info(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 10):
        print_error(f"Python 3.10+ required, you have {version.major}.{version.minor}")
        print_info("Please upgrade Python: https://www.python.org/downloads/")
        return False
    
    print_success("Python version OK")
    return True

def check_port_available(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port(start_port=8000, end_port=9000):
    """Find an available port in range"""
    print_info(f"Scanning for available port ({start_port}-{end_port})...")
    
    for port in range(start_port, end_port):
        if check_port_available(port):
            print_success(f"Found available port: {port}")
            return port
    
    print_warning(f"No ports available in range {start_port}-{end_port}")
    return None

def create_venv():
    """Create virtual environment"""
    print_header("Setting Up Virtual Environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        response = input("Recreate? (y/n): ").strip().lower()
        if response != 'y':
            print_info("Skipping venv creation")
            return True
        
        print_info("Removing old venv...")
        import shutil
        shutil.rmtree(venv_path)
    
    print_info("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create venv: {e}")
        print_info("Trying alternative method...")
        
        try:
            subprocess.run([sys.executable, "-m", "virtualenv", "venv"], check=True)
            print_success("Virtual environment created (using virtualenv)")
            return True
        except:
            print_error("Could not create virtual environment")
            print_info("Install virtualenv: pip install virtualenv")
            return False

def get_pip_command():
    """Get the correct pip command for the platform"""
    if platform.system() == "Windows":
        return str(Path("venv/Scripts/pip.exe"))
    else:
        return str(Path("venv/bin/pip"))

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    pip_cmd = get_pip_command()
    
    print_info("Upgrading pip...")
    try:
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        print_success("pip upgraded")
    except:
        print_warning("Could not upgrade pip (continuing anyway)")
    
    print_info("Installing requirements...")
    try:
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install some dependencies")
        print_info("Trying individual installation...")
        
        # Try installing core dependencies individually
        core_deps = [
            "PySide6>=6.6.0",
            "pyyaml>=6.0",
            "numpy>=1.24.0"
        ]
        
        for dep in core_deps:
            try:
                subprocess.run([pip_cmd, "install", dep], check=True)
                print_success(f"Installed {dep}")
            except:
                print_error(f"Failed to install {dep}")
        
        # Optional dependencies
        print_info("Installing optional AI dependencies...")
        optional_deps = [
            "openai>=1.10.0",
            "anthropic>=0.18.0",
            "psycopg[binary]>=3.1.0"
        ]
        
        for dep in optional_deps:
            try:
                subprocess.run([pip_cmd, "install", dep], check=False)
                print_success(f"Installed {dep}")
            except:
                print_warning(f"Could not install {dep} (optional)")
        
        return True

def create_config():
    """Create default configuration"""
    print_header("Creating Configuration")
    
    config_file = Path("theophysics_config.json")
    
    if config_file.exists():
        print_warning("Configuration file already exists")
        response = input("Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print_info("Keeping existing configuration")
            return True
    
    # Find available port
    port = find_available_port()
    if not port:
        port = 8000  # Default fallback
        print_warning(f"Using default port {port} (may need manual adjustment)")
    
    config = {
        "vault_path": None,
        "sqlite_path": None,
        "postgres_conn_str": None,
        "model_name": "gpt-4o",
        "server_port": port,
        "server_host": "localhost"
    }
    
    print_info(f"Creating config with port {port}...")
    config_file.write_text(json.dumps(config, indent=2))
    print_success("Configuration created")
    
    print_info("\nNext steps:")
    print("  1. Run the application: python main.py")
    print("  2. Select your Obsidian vault in the GUI")
    print("  3. (Optional) Set OPENAI_API_KEY environment variable for AI features")
    
    return True

def check_git():
    """Check if git is available"""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def create_gitignore():
    """Create .gitignore if it doesn't exist"""
    print_header("Git Setup")
    
    if not check_git():
        print_warning("Git not found (skipping .gitignore)")
        return True
    
    gitignore = Path(".gitignore")
    if gitignore.exists():
        print_success(".gitignore already exists")
        return True
    
    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Application
theophysics_config.json
*.db
*.db-journal
*.log

# AI Keys (NEVER commit these!)
.env
*.pem
*.key
credentials.json
"""
    
    gitignore.write_text(content)
    print_success(".gitignore created")
    return True

def run_tests():
    """Run quick tests to verify installation"""
    print_header("Running Tests")
    
    print_info("Testing imports...")
    tests = [
        ("PySide6", "PySide6.QtWidgets"),
        ("yaml", "yaml"),
        ("numpy", "numpy"),
    ]
    
    all_passed = True
    for name, module in tests:
        try:
            __import__(module)
            print_success(f"{name} OK")
        except ImportError:
            print_error(f"{name} FAILED")
            all_passed = False
    
    # Test optional modules
    print_info("\nTesting optional AI modules...")
    optional = [
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("psycopg", "psycopg"),
    ]
    
    for name, module in optional:
        try:
            __import__(module)
            print_success(f"{name} OK")
        except ImportError:
            print_warning(f"{name} not installed (optional)")
    
    return all_passed

def print_summary():
    """Print installation summary"""
    print_header("Installation Complete!")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}✓ Installation successful!{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Quick Start:{Colors.ENDC}")
    print("  1. Activate virtual environment:")
    
    if platform.system() == "Windows":
        print(f"     {Colors.OKCYAN}venv\\Scripts\\activate{Colors.ENDC}")
    else:
        print(f"     {Colors.OKCYAN}source venv/bin/activate{Colors.ENDC}")
    
    print("\n  2. Run the application:")
    print(f"     {Colors.OKCYAN}python main.py{Colors.ENDC}")
    
    print("\n  3. (Optional) Set up AI:")
    print(f"     {Colors.OKCYAN}set OPENAI_API_KEY=your-key-here{Colors.ENDC}  (Windows)")
    print(f"     {Colors.OKCYAN}export OPENAI_API_KEY=your-key-here{Colors.ENDC}  (Linux/Mac)")
    
    print(f"\n{Colors.BOLD}Documentation:{Colors.ENDC}")
    print(f"  - Quick Start: {Colors.OKCYAN}docs/QUICKSTART.md{Colors.ENDC}")
    print(f"  - Full Guide: {Colors.OKCYAN}docs/README_USER.md{Colors.ENDC}")
    print(f"  - Features: {Colors.OKCYAN}docs/FULL_FEATURES.md{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Need Help?{Colors.ENDC}")
    print("  - Check docs/INSTALLATION.md for detailed setup")
    print("  - Report issues on GitHub")
    
    print()

def main():
    """Main installation flow"""
    print_header("Theophysics Manager - Installation")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print_info(f"Project root: {project_root}")
    
    # Run installation steps
    steps = [
        ("Python Version Check", check_python_version),
        ("Virtual Environment", create_venv),
        ("Dependencies", install_dependencies),
        ("Configuration", create_config),
        ("Git Setup", create_gitignore),
        ("Tests", run_tests),
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print_error(f"Installation failed at: {step_name}")
                print_info("Check the error messages above for details")
                return 1
        except KeyboardInterrupt:
            print_error("\n\nInstallation cancelled by user")
            return 1
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    print_summary()
    return 0

if __name__ == "__main__":
    sys.exit(main())

