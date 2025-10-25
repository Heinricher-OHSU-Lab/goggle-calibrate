#!/bin/bash
#
# Goggle Calibration Experiment Launcher
# Double-click this file from Finder to run the experiment
#
# This file can be copied to Desktop or anywhere else for easy access
#

# Determine project location
# Use GOGGLE_CALIBRATE_ROOT environment variable if set, otherwise use default
if [ -n "$GOGGLE_CALIBRATE_ROOT" ]; then
    PROJECT_DIR="$GOGGLE_CALIBRATE_ROOT"
else
    PROJECT_DIR="$HOME/Documents/src/goggle-calibrate"
fi

# Change to the project directory
cd "$PROJECT_DIR" || {
    echo "Error: Could not find project directory at $PROJECT_DIR"
    echo ""
    echo "Please set the GOGGLE_CALIBRATE_ROOT environment variable to the correct path."
    echo "Add this to your ~/.zshrc or ~/.bash_profile:"
    echo "  export GOGGLE_CALIBRATE_ROOT=\"/path/to/goggle-calibrate\""
    echo ""
    read -p "Press Enter to exit..."
    exit 1
}

# Run the calibration script
./scripts/run_calibrate.sh