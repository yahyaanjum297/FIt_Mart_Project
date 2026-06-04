#!/bin/bash
echo "===================================="
echo "  FitMart Backend Launcher"
echo "===================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install from python.org"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Start server
echo ""
echo "Starting FitMart backend on http://localhost:8000"
echo "Swagger docs at http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""
python3 run.py
