#!/bin/bash

# Setup script for nippan audit scripts
# This script sets up the Python environment and installs required dependencies

echo "Setting up Python environment for nippan audit scripts..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version (require 3.8+)
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "Python version $python_version is compatible."
else
    echo "Error: Python 3.8 or later is required. Current version: $python_version"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3."
    exit 1
fi

# Create virtual environment (optional but recommended)
read -p "Do you want to create a virtual environment? (recommended) [y/N]: " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Virtual environment created and activated."
    echo "To activate it later, run: source venv/bin/activate"
    echo "To deactivate, run: deactivate"
fi

# Install requirements
echo "Installing required Python packages..."
pip3 install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p files
mkdir -p results

# Check if directories were created
if [[ -d "files" && -d "results" ]]; then
    echo "✓ Directories created successfully"
else
    echo "Error: Could not create necessary directories"
    exit 1
fi

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure the ENV_URL and ENV_TOKEN in config.py"
echo "2. Place your input files in the 'files' directory"
echo "3. Run the audit script: python3 audit_report.py"
echo ""
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "Remember to activate the virtual environment before running the script:"
    echo "source venv/bin/activate"
fi
