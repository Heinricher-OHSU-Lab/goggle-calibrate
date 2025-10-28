# Goggle Calibration Experiment - Project Specification

## Overview
PsychoPy-based experiment to determine light discomfort threshold using adaptive staircase methodology. The experiment presents light stimuli through goggles that fully cover the subject's eyes and determines the brightness level at which subjects report discomfort.

This is intended for preliminary data collection to get a calibration for typical light levels that will cause discomfort.

## Target Platform
- **Development**: macOS 26 (Tahoe)
- **Deployment**: macOS 12 (Monterey)
- **Python Version**: 3.10.19 (required for deployment compatibility)
- **Key Dependency**: PsychoPy 2023.2.3 (last version with PyQt5 support)

### Why These Versions?
- Python 3.10 is the recommended version for PsychoPy stability
- Avoid Python 3.11+ due to PsychoPy compatibility issues (removed deprecated NumPy APIs)
- PsychoPy 2023.2.3 is the last version with PyQt5, required for macOS Monterey compatibility
- PsychoPy 2024.x+ requires PyQt6, which is not compatible with macOS Monterey

## Project Structure
```
goggle-calibrate/
├── calibrate.py           # Main experiment script
├── config.py              # Configuration loader
├── data_logger.py         # Data logging and metadata management
├── experiment_ui.py       # PsychoPy UI interface
├── goggles.py             # Serial hardware controller
├── staircase.py           # Adaptive staircase manager
├── requirements.txt       # Python dependencies
├── README.md              # User documentation
├── PROJECT_SPEC.md        # This file - development specification
├── PLAN.md                # Implementation plan and status
├── CLAUDE.md              # Claude-specific guidance
├── .gitignore
├── .venv/                 # Virtual environment (gitignored)
├── calibration-test-data/ # Test data for development (contents gitignored)
├── tests/                 # Development test files (gitignored)
├── config_schema.json     # JSON schema for config validation
├── default_config.json    # Default configuration template
└── scripts/
    ├── setup.sh           # Initial environment setup
    ├── run_calibrate.sh   # Launch script
    ├── install_psychopy.sh # PsychoPy installation helper
    └── Run Calibration.command # Desktop launcher

~/Documents/Calibration/  # User data directory for production use (NOT in repo)
├── data/                  # Experimental CSV, .meta, and .psydat files
├── logs/                  # Runtime logs
└── config/
    └── experiment_config.json
```

## Hardware Interface

### Light Goggles
- **Control Range**: 0-255 (integer values)
  - 0 = off (only used for safety/shutdown, never for threshold testing)
  - 1-255 = test range (1 = minimum test brightness, 255 = maximum brightness)
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
- **Termination**: After 10 reversals (or 100 trials max as safety limit)
- **Parameters** (configurable via JSON):
  - Start value: 128 (middle of range)
  - Step sizes: [32, 16, 8, 4, 2, 1] (progressively smaller)
  - Target reversals: 10
  - Max trials: 100 (safety limit)
  - Min/max values: 1-255 (0 reserved for safety/shutdown only)
- Note: All the above should be settable in config

### Trial Flow
1. **Pre-stimulus delay** (6s, configurable) - Countdown displayed
2. **Light stimulus presentation** (2s, configurable) - Goggles turn ON at test brightness
3. **Goggles turn OFF** - Immediately after stimulus ends
4. **Inter-trial interval / Response period** (6s, configurable) - Experimenter asks subject
5. **Next trial begins** - Automatic after ITI completes

### Keyboard Response (Continuous Monitoring)
- **Monitoring period**: From stimulus start through end of ITI
- **Y key**: Subject reports uncomfortable
- **N key**: Subject reports comfortable
- **No key**: Defaults to comfortable
- **Last key pressed wins**: Experimenter can correct accidental keypresses
- **Real-time feedback**: Display shows current response state

### Experimenter Control
- **No subject interaction with computer**
- Experimenter conducts all keyboard input
- Experimenter provides verbal instructions to subject
- Display shows experimenter-facing information only:
  - Current trial number and total trials
  - Light level being tested
  - Number of reversals so far
  - Trial phase (stimulus/response)
  - Current response state (with ability to correct)
  - Instructions for keyboard input

## Configuration System

### Config File Location
`~/Documents/Calibration/config/experiment_config.json` (default)

### Config Schema
See `config_schema.json` and `default_config.json` for complete schema documentation. Configuration includes:
- Hardware settings (serial port, baud rate)
- Staircase parameters (start value, step sizes, reversals, max trials)
- Timing parameters (pre-delay, stimulus duration, ITI)
- File paths (data, logs, config directories)

### Config Behavior
- Auto-created with defaults if missing
- User-editable for adjusting experiment parameters
- Changes persist across sessions
- Validated against schema on load

## Data Storage

### Location
All data stored in `~/Documents/Calibration/` (NOT in git repo)

### Output Files

**Naming Scheme:**

File names should be designed such that sort order is:
- By participant ID
- Then by session ID
- Then by date with most recent last

**Per Session:**
- `{participant}_{session}_{timestamp}.csv` - Trial-by-trial data
- `{participant}_{session}_{timestamp}.meta` - Session metadata (INI format)
- `{participant}_{session}_{timestamp}_staircase.psydat` - Staircase object (for analysis)
- `logs/experiment_{timestamp}.log` - Complete runtime log

**CSV Columns:**
- `goggle_level` - Brightness level presented (0-255)
- `uncomfortable` - Response (1=uncomfortable, 0=comfortable)
- `trial_number` - Sequential trial count
- `reversals_so_far` - Cumulative reversal count
- `timestamp` - Trial timestamp

**Metadata File (.meta) Contents:**
- Session info (participant_id, session_id, timestamps)
- Experiment parameters (starting_intensity, config file path)
- System info (Python version, PsychoPy version)
- Results (final_threshold, total_trials, total_reversals, experiment_completed status)
- Tracks partial/aborted experiments for data integrity

### Threshold Calculation
- Average of last 6 reversal points (if ≥6 reversals)
- Otherwise, average all reversal points

## Dependencies

### Core Requirements
```
psychopy==2023.2.3
numpy<2.0
pyserial>=3.5
```

### Why These Constraints?
- **PsychoPy 2023.2.3**: Last version with PyQt5 support (required for macOS Monterey compatibility)
- **NumPy <2.0**: PsychoPy 2023.2.3 uses APIs removed in NumPy 2.0
- **pyserial >=3.5**: Required for serial port communication with goggles hardware

### Installation Notes
- PsychoPy 2023.2.3 has a missing dependency (`pypi-search`). Use `scripts/install_psychopy.sh` which handles the workaround automatically.
- See `PSYCHOPY_INSTALL.md` for manual installation details if needed.

## Deployment

### Installation Method
- pyenv for Python version management
- Virtual environment (`.venv/`) for isolation
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
git clone <repository> goggle-calibrate
cd goggle-calibrate
./scripts/setup.sh
```

### Running During Development
```bash
source .venv/bin/activate
python calibrate.py
```

### Testing
- Test on both development (macOS 26) and deployment (macOS Monterey) systems
- Timing precision only needs to be within 0.1 second
- Test full trial flow with experimenter workflow
- Validate data file creation and format (.csv, .meta, .psydat, .log)
- Test abort/safety mechanisms (ESC key, exceptions, crashes)

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