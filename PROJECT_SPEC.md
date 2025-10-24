# Goggle Calibration Experiment - Project Specification

## Overview
PsychoPy-based experiment to determine light discomfort threshold using adaptive staircase methodology. The experiment presents light stimuli through goggles that fully cover the subject's eyes and determines the brightness level at which subjects report discomfort.

This is intended for prelimary data collection to get a calibration for typical light levels that will cause discomfort.

## Target Platform
- **Development**: MacOS 26 (Tahoe)
- **Deployment**: macOS 12 (Monterey)
- **Python Version**: 3.10.15 (required for deployment compatibility)
- **Key Dependency**: PsychoPy 2025.1.1 (Suggestion from PsychoPy web site for stable deployments)

### Why These Versions?
- Python 3.10 is the recommended version for PsychoPy stability
- Avoid Python 3.11+ due to limited PsychoPy dependency support

## Project Structure
```
goggle-calibrate/
├── calibration.py        # Main experiment script
├── requirements.txt      # Python dependencies
├── README.md             # User documentation
├── PROJECT_SPEC.md       # This file - development specification
├── .gitignore
├── venv/                 # Virtual environment (gitignored)
├── calibration_test_data/ # User data directoy for development (contents gitignored)
└── scripts/
    ├── setup.sh          # Initial environment setup
    └── run_calibrate.sh # Launch script

~/Documents/Calibration/  # User data directory for production use (NOT in repo)
├── data/                 # Experimental CSV and .psydat files
├── logs/                 # Runtime logs
└── config/
    └── calibrate_config.json
```

## Hardware Interface

### Light Goggles
- **Control Range**: 0-255 (integer values)
  - 0 = off
  - 255 = maximum brightness
- **Interface**: 
  - Serial port (specified in config) to light controller hardware
  - Protocol is to send a LF delimited string with the numeric value to set the goggle to
- **Assumptions**: 
  - Levels are approximately linear from perception standpoint.
  - May require perceptual transformation based on collected data so should be configurable.
- **Coverage**: Goggles fully cover subject's eyes (no screen-based fixation possible)

## Experiment Methodology

### Staircase Procedure (Initial)
- **Algorithm**: Adaptive staircase (1-up-1-down rule)
- **Target**: 50% discomfort threshold
- **Parameters** (configurable via JSON):
  - Start value: 128 (middle of range)
  - Step sizes: [32, 16, 8, 4, 2, 1] (progressively smaller)
  - Number of trials: 30
  - Min/max values: 0-255
- Note: All the above should be settable in config

### Trial Flow
1. Pre-stimulus delay (6s, configurable)
2. Light stimulus presentation (2s, configurable)
3. Goggles turn off
4. Experimenter asks subject: "Was that uncomfortable?"
5. Experimenter presses Y (uncomfortable) or no input (comfortable)
6. Inter-trial interval (6s, configurable)

### Experimenter Control
- **No subject interaction with computer**
- Experimenter conducts all keyboard input
- Experimenter provides verbal instructions to subject
- Display shows experimenter-facing information only:
  - Current trial number
  - Light level being tested
  - Number of reversals so far
  - Response prompt

## Configuration System

### Config File Location
`~/Documents/Calibration/config/experiment_config.json` (default)

Shoud be able to change it in config.

### Config Schema

TBD

### Config Behavior
- Auto-created with defaults if missing
- User-editable for adjusting experiment parameters
- Changes persist across sessions

## Data Storage

### Location
All data stored in `~/Documents/Calibration/` (NOT in git repo)

### Output Files

**Naming Scheme:**

File names should be designed such that sort order is:
- By participan ID
- Then by session ID
- Then by date with most recent last

**Per Session:**
- `{participant}_{session}_{timestamp}.csv` - Trial-by-trial data
- `{participant}_{session}_{timestamp}_staircase.psydat` - Staircase object (for analysis)
- `logs/experiment_{timestamp}.log` - Complete runtime log

**CSV Columns:**
- `goggle_level` - Brightness level presented (0-255)
- `uncomfortable` - Response (1=yes, 0=no)
- `trial_number` - Sequential trial count
- `reversals_so_far` - Cumulative reversal count
- Plus standard PsychoPy metadata

### Threshold Calculation
- Average of last 6 reversal points (if ≥6 reversals)
- Otherwise, average all reversal points

## Dependencies

### Core Requirements
```
psychopy==2025.1.1
numpy==TBD
pandas>=2.0.0
```

### Why These Constraints?
- PsychoPy 2025.1.1: Stable release suggested by PsychoPy
- NumPy >=1.24.0: Compatibility with PsychoPy dependencies
- Pandas >=2.0.0: For data analysis (latest stable)

## Deployment

### Installation Method
- pyenv for Python version management
- Virtual environment (venv) for isolation
- Automated setup via `scripts/setup.sh`

### Launch Method
- Desktop launcher (`.command` file or Automator app)
- Calls `scripts/run_calibrate.sh`
- All output logged to `~/Documents/Calibration/logs/`

### User Requirements
- macOS Monterey or later
- pyenv installed
- No Python expertise required (run from desktop icon)

## Development Workflow

### Initial Setup
```bash
# Install pyenv if needed
brew install pyenv

# Clone and setup
git clone  goggle-calibrate
cd goggle-calibrate
./scripts/setup.sh
```

### Running During Development
```bash
source venv/bin/activate
python experiment.py
```

### Testing
- Test on both development (macOS 26) and deployment (macOS Monterey) systems
- Timing precion only needs do be with in 0.1 second
- Test full trial flow with experimenter workflow
- Validate data file creation and format

## Future Enhancements

### High Priority
- TBD

### Lower Priority
- Multiple staircase algorithms (QUEST, Psi)
- Real-time staircase visualization
- Batch analysis scripts for multiple sessions
- Practice trials before actual experiment

## Code Style
- Python 3.10+ idioms
- Type hints required
- PEP 8 formatting
- Clear variable names for readability by research staff
- Comments explaining psychophysics methodology where relevant
- Black formatting before each commit

## Safety Considerations
- Always ensure goggles set to 0 on program exit (even on crash)
- ESC key immediately aborts and turns off goggles
- Maximum brightness level (255) should be validated as safe before deployment
- Consider adding brightness limits in config

## Notes for AI Assistant
- This is research software for a psychology lab.
- Non-technical staff will run experiments - prioritize reliability over features.
- Data integrity is paramount - ensure all trials are logged even on errors.
- Alway make sure you check the most recent version of documentation.  Do not rely on old information.