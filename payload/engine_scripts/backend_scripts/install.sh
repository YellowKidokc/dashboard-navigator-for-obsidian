#!/bin/bash
# Theophysics Manager - Linux/Mac Installation Script
# This calls the universal Python installer

echo ""
echo "============================================"
echo "   Theophysics Manager - Installation"
echo "============================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Run universal installer
python3 scripts/install.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation encountered errors."
    exit 1
fi

echo ""
echo "Installation complete!"
echo ""

