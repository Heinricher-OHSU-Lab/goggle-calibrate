#!/bin/bash
# Install PsychoPy 2023.2.3 with workaround for pypi-search dependency issue
#
# PsychoPy 2023.2.3 is the last version that uses PyQt5 (required for macOS Monterey).
# However, it has a dependency on pypi-search which was removed from PyPI.
# This script works around the issue by installing PsychoPy without dependencies,
# then manually installing all required dependencies.

set -e  # Exit on error

echo "Installing PsychoPy 2023.2.3 (PyQt5 version for macOS Monterey compatibility)..."
echo ""

# Get the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Install PsychoPy without dependencies to avoid pypi-search issue
echo "Step 1: Installing PsychoPy without dependencies..."
pip install --no-deps psychopy==2023.2.3
echo "✓ PsychoPy 2023.2.3 installed"
echo ""

# Install all PsychoPy dependencies
echo "Step 2: Installing PsychoPy dependencies..."
pip install -r "${PROJECT_DIR}/requirements-deps.txt"
echo "✓ Dependencies installed"
echo ""

# Install additional dependencies needed by PsychoPy
echo "Step 3: Installing additional PsychoPy dependencies..."
pip install \
    astunparse \
    cryptography \
    esprima \
    ffpyplayer \
    gitpython \
    'jedi>=0.16' \
    opencv-python \
    pyobjc-core \
    'pyobjc-framework-Quartz<8.0' \
    python-gitlab \
    'python-vlc>=3.0.12118' \
    tables
echo "✓ Additional dependencies installed"
echo ""

# Verify installation
echo "Verifying installation..."
python -c "import psychopy; from psychopy import visual; import numpy as np; print(f'✓ PsychoPy {psychopy.__version__} with NumPy {np.__version__}')"
echo ""
echo "✓ PsychoPy installation complete!"