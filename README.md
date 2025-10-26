# Goggle Calibration Experiment

PsychoPy-based experiment to determine light discomfort threshold using adaptive staircase methodology (1-up-1-down).

## Overview

This experiment presents light stimuli through goggles and uses an adaptive staircase procedure to converge on the brightness level at which subjects report discomfort approximately 50% of the time.

**Key Features:**
- Adaptive 1-up-1-down staircase procedure
- Serial port control of light goggles (brightness range 1-255; 0 for shutdown only)
- Safety-critical design: goggles automatically turn off on any exit
- Real-time data logging with immediate flush
- Experimenter-facing PsychoPy window interface
- Configurable timing and staircase parameters

## Requirements

- macOS 12 (Monterey) or later
- Python 3.10.19 (managed via pyenv)
- Serial port connection to light goggles

## Installation (Production)

1. Install pyenv if not already installed:
   ```bash
   brew install pyenv
   ```

2. Add to your shell profile (~/.zshrc or ~/.bash_profile):
   ```bash
   export PYENV_ROOT="$HOME/.pyenv"
   export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   ```

3. Clone repository and run setup:
   ```bash
   cd goggle-calibrate
   ./scripts/setup.sh
   ```

   This will:
   - Install Python 3.10.19 via pyenv
   - Create virtual environment at `.venv/`
   - Install all dependencies
   - Create data directories at `~/Documents/Calibration/`

## Running the Experiment

### Launch Methods

**Option 1: Desktop Launcher (Recommended for Production)**

Copy `scripts/Run Calibration.command` to your Desktop, then double-click it from Finder. This launches the experiment with all output logged to `~/Documents/Calibration/logs/`.

The launcher uses the `GOGGLE_CALIBRATE_ROOT` environment variable if set, otherwise defaults to `~/Documents/src/goggle-calibrate`. If your project is in a different location, add to your `~/.zshrc` or `~/.bash_profile`:
```bash
export GOGGLE_CALIBRATE_ROOT="/path/to/goggle-calibrate"
```

On first use, you may need to:
1. Right-click the file and select "Open" to bypass Gatekeeper
2. Allow execution in System Settings > Privacy & Security if prompted

**Option 2: Command Line (Production)**
```bash
./scripts/run_calibrate.sh
```

**Option 3: Development**
```bash
source .venv/bin/activate
python calibrate.py
```

## Configuration

Configuration file: `~/Documents/Calibration/config/experiment_config.json`

A default configuration is created automatically on first run. Edit this file to customize:

- **Hardware settings**: Serial port, baud rate, brightness range
- **Staircase parameters**: Start value, step sizes, target reversals, max trials
- **Timing**: Pre-stimulus delay, stimulus duration, inter-trial interval
- **Paths**: Data directory, log directory

## Data Output

All data is saved to `~/Documents/Calibration/`

### Files Created Per Session:
- `{participant}_{session}_{timestamp}.csv` - Trial-by-trial data
- `{participant}_{session}_{timestamp}_staircase.psydat` - Staircase object for analysis
- `logs/experiment_{timestamp}.log` - Complete runtime log

### CSV Columns:
- `trial_number` - Sequential trial count
- `goggle_level` - Brightness level tested (1-255)
- `uncomfortable` - Response (1=uncomfortable, 0=comfortable)
- `reversals_so_far` - Cumulative reversal count
- `timestamp` - Trial timestamp
- `participant_id` - Participant identifier
- `session_id` - Session identifier

## Experimenter Workflow

1. Launch experiment: `./scripts/run_calibrate.sh`
2. Enter participant ID and session ID when prompted
3. Read instructions on screen (press SPACE to continue)
4. Ensure subject is wearing goggles comfortably
5. Explain to subject: "You will see brief flashes of light. Please tell me only if a flash is uncomfortable."

### During Each Trial:
1. Wait for light stimulus (automatic)
2. Ask subject: "Uncomfortable?"
3. Press **Y** only if subject reports discomfort
4. No response = automatically recorded as comfortable after interval
5. Next trial begins automatically

### Controls:
- **Y** - Subject reports uncomfortable
- **No key** - Comfortable (automatic after inter-trial interval)
- **ESC** - Abort experiment (goggles turn off immediately)

## Testing

Run the test suite to verify installation:
```bash
source .venv/bin/activate
python test_experiment.py
```

This tests all components without requiring hardware (uses mocked serial port).

## Threshold Calculation

The experiment estimates the discomfort threshold by averaging the brightness levels at reversal points:
- If >=6 reversals: average of last 6 reversals
- If <6 reversals: average of all reversals

## Safety Features

- **Automatic shutdown**: Goggles turn off on program exit, crash, or Ctrl+C
- **ESC abort**: Immediate experiment termination with goggles off
- **Multiple safety layers**: atexit handlers, signal handlers, context managers
- **Data integrity**: Trial data flushed immediately to prevent data loss

## File Structure

```
goggle-calibrate/
   calibrate.py              # Main experiment script
   config.py                 # Configuration system
   goggles.py                # Goggles controller
   data_logger.py            # Data logging
   staircase.py              # Adaptive staircase
   experiment_ui.py          # PsychoPy interface
   test_experiment.py        # Test suite
   requirements.txt          # Python dependencies
   scripts/
      setup.sh             # Installation script
      run_calibrate.sh     # Launch script
   calibration-test-data/   # Development test data (gitignored)
   CLAUDE.md                # Claude Code guidance

~/Documents/Calibration/      # Production data (NOT in repo)
   data/                     # Experimental data files
   logs/                     # Runtime logs
   config/                   # Configuration file
```

## Troubleshooting

### Serial Port Issues
- Check serial port name in config: `~/Documents/Calibration/config/experiment_config.json`
- On Mac, list ports: `ls /dev/tty.*`
- On Windows, check Device Manager - Ports

### PsychoPy Issues
- Ensure Python 3.10.19 is being used: `python --version`
- Verify PsychoPy installed: `python -c "import psychopy; print(psychopy.__version__)"`
- Re-run setup if needed: `./scripts/setup.sh`

### Data Not Saving
- Check permissions on `~/Documents/Calibration/`
- Check log file for errors: `~/Documents/Calibration/logs/experiment_*.log`

## Development

For development in PyCharm:
1. Configure Python interpreter to use `.venv/`
2. Set working directory to project root
3. Run `calibrate.py` directly

### Development Mode Logging

By default, logs are only written to files in `~/Documents/Calibration/logs/` to avoid cluttering the experimenter's console. To enable console logging during development, set the `GOGGLE_DEV_MODE` environment variable to a log level:

```bash
# Enable console logging at INFO level for a single run
GOGGLE_DEV_MODE=INFO python calibrate.py

# Enable DEBUG level logging for detailed output
GOGGLE_DEV_MODE=DEBUG python calibrate.py

# Or set it in your shell session
export GOGGLE_DEV_MODE=INFO
python calibrate.py
```

Valid log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

See `CLAUDE.md` for guidance on working with Claude Code in this repository.

## Technical Details

- **Python Version**: 3.10.19 (required for PsychoPy compatibility)
- **PsychoPy Version**: 2025.1.1
- **Staircase Algorithm**: 1-up-1-down (targets 50% threshold)
- **Serial Protocol**: LF-delimited numeric strings (0-255)
- **Timing Precision**: +/- 0.1 second

## References

See `PROJECT_SPEC.md` for complete technical specification.
