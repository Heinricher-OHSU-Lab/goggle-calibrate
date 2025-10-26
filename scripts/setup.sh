#!/bin/bash
# Setup script for Goggle Calibration Experiment - Production Deployment
# This script installs Python 3.10.19 via pyenv and sets up the virtual environment
# For development: configure PyCharm to use Python 3.10.19 and .venv directory
#
# IMPORTANT: This script has been updated to work around the pypi-search dependency issue
# in PsychoPy 2023.2.3. PsychoPy is installed with --no-deps, then dependencies are
# installed separately from requirements-deps.txt

set -e  # Exit on error

echo "=== Goggle Calibration Experiment - Production Setup ==="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"

# Check for pyenv
echo "Checking for pyenv..."
if ! command -v pyenv &> /dev/null; then
    echo "ERROR: pyenv is not installed"
    echo "Please install pyenv first:"
    echo "  brew install pyenv"
    echo ""
    echo "Then add to your shell profile (~/.zshrc or ~/.bash_profile):"
    echo '  export PYENV_ROOT="$HOME/.pyenv"'
    echo '  export PATH="$PYENV_ROOT/bin:$PATH"'
    echo '  eval "$(pyenv init -)"'
    exit 1
fi

echo " pyenv found"

# Check if Python 3.10.19 is installed
PYTHON_VERSION="3.10.19"
echo ""
echo "Checking for Python ${PYTHON_VERSION}..."

if ! pyenv versions | grep -q "${PYTHON_VERSION}"; then
    echo "Python ${PYTHON_VERSION} not found. Installing..."
    pyenv install "${PYTHON_VERSION}"
    echo " Python ${PYTHON_VERSION} installed"
else
    echo " Python ${PYTHON_VERSION} already installed"
fi

# Set local Python version for this project
echo ""
echo "Setting Python ${PYTHON_VERSION} as local version for this project..."
pyenv local "${PYTHON_VERSION}"
echo " Local Python version set"

# Get the pyenv Python path
PYTHON_PATH=$(pyenv which python)
echo "Using Python: ${PYTHON_PATH}"

# Create virtual environment
VENV_DIR="${PROJECT_DIR}/.venv"
echo ""
echo "Creating virtual environment at ${VENV_DIR}..."

if [ -d "${VENV_DIR}" ]; then
    echo "Virtual environment already exists. Removing old environment..."
    rm -rf "${VENV_DIR}"
fi

"${PYTHON_PATH}" -m venv "${VENV_DIR}"
echo " Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install PsychoPy and dependencies using workaround script
echo ""
"${SCRIPT_DIR}/install_psychopy.sh"

# Create production data directories
echo ""
echo "Creating production data directories..."
DATA_BASE="${HOME}/Documents/Calibration"
mkdir -p "${DATA_BASE}/data"
mkdir -p "${DATA_BASE}/logs"
mkdir -p "${DATA_BASE}/config"
echo " Created directories at ${DATA_BASE}"

# Verify installation
echo ""
echo "Verifying installation..."
python --version
echo ""
python -c "import psychopy; print(f'PsychoPy version: {psychopy.__version__}')"

echo ""
echo "=== Production Setup Complete ==="
echo ""
echo "To run the experiment, use the launch script:"
echo "  ./scripts/run_calibrate.sh"
echo ""
echo "Data will be stored in: ${DATA_BASE}"
echo ""
