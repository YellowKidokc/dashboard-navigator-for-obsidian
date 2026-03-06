#!/bin/bash
# Theophysics Manager - Linux/Mac Run Script

cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run install.sh first"
    exit 1
fi

echo "Starting Theophysics Manager..."
echo ""

source venv/bin/activate
python3 main.py

