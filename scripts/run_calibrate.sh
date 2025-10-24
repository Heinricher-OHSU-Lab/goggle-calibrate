#!/bin/bash
# Launch script for Goggle Calibration Experiment
# This script activates the virtual environment and runs the experiment

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found at .venv/"
    echo "Please run scripts/setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if Python and dependencies are available
if ! python -c "import psychopy" 2>/dev/null; then
    echo "ERROR: PsychoPy not found in virtual environment"
    echo "Please run scripts/setup.sh to install dependencies"
    exit 1
fi

# Run the experiment
echo "Starting Goggle Calibration Experiment..."
echo ""

python calibrate.py

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "Experiment completed successfully"
else
    echo "Experiment exited with code $EXIT_CODE"
fi

exit $EXIT_CODE