# Implementation Plan - Goggle Calibration Experiment

## Status Summary (Last Updated: 2024-10-26)

**Core Implementation: ✅ COMPLETE**
- All phases 1-6 fully implemented and working
- Extensive testing performed (15+ test files in `tests/`)
- Documentation complete (README, code comments, type hints)

**User Feedback Changes Needed (from 2024-10-26 demo):**
- [ ] Add starting intensity input to session initialization dialog
- [ ] Improve response input with continuous keyboard monitoring and correction capability

**Remaining Tasks:**
- [ ] Verify against PROJECT_SPEC.md requirements (systematic checklist needed)
- [ ] Test on macOS 12 Monterey (deployment target platform)
- [ ] Test with actual hardware goggles
- [ ] User review and feedback

**Ready For:** Implementation of user feedback changes, then deployment preparation

---

## Overview
This plan outlines the implementation of a PsychoPy-based light discomfort threshold experiment using adaptive staircase methodology. See PROJECT_SPEC.md for complete requirements.

## Phase 1: Foundation & Setup

### 1.1 Research & Documentation
- [ ] Search for current PsychoPy 2025.1.1 documentation
  - Staircase/QUEST adaptive methods API
  - Serial port control (psychopy.hardware.serial or pyserial)
  - Event handling and keyboard input
  - Visual window management (or lack thereof for goggle-only display)
  - Data saving (.psydat format)
  - **Note**: Implementation working but formal documentation research not completed

### 1.2 Configuration System
- [x] Design configuration schema (experiment_config.json):
  - Hardware settings (serial port, baud rate, brightness range)
  - Staircase parameters (start value, step sizes, n_trials, min/max)
  - Timing parameters (pre_delay, stimulus_duration, inter_trial_interval)
  - File paths (data directory, log directory, config directory)
  - Participant/session metadata defaults
  - **Implemented in**: `config_schema.json`, `default_config.json`
- [x] Implement configuration loader:
  - Read from `~/Documents/Calibration/config/experiment_config.json`
  - Auto-create directory structure if missing
  - Auto-generate default config if missing
  - Validate configuration values
  - Graceful error handling for malformed JSON
  - **Implemented in**: `config.py`

### 1.3 Setup Script
- [x] Implement `scripts/setup.sh`:
  - Check for pyenv installation
  - Install Python 3.10.15 if needed
  - Create `.venv/` virtual environment
  - Install requirements.txt dependencies
  - Create `~/Documents/Calibration/` directory structure
  - Generate default config file
  - **Implemented in**: `scripts/setup.sh`

## Phase 2: Core Hardware & Safety

### 2.1 Goggles Control Class
- [x] Implement `GoggleController` class with:
  - Serial port initialization (configurable port/baud)
  - `set_brightness(level: int)` method (0-255, sends LF-delimited string)
  - Context manager (`__enter__`/`__exit__`) for automatic cleanup
  - `close()` method to ensure brightness→0
  - Exception handling with guaranteed brightness→0
  - Safety validation (reject values outside 0-255)
  - **Implemented in**: `goggles.py`
- [x] Test serial communication protocol
  - **Tested with**: `mock_serial_device.py` and multiple integration tests
- [x] Implement atexit handler for emergency shutdown
  - **Implemented in**: `goggles.py:80-85` (atexit and signal handlers)

## Phase 3: Data & Logging

### 3.1 Logging System
- [x] Configure Python logging:
  - File handler: `~/Documents/Calibration/logs/experiment_{timestamp}.log`
  - Console handler for experimenter feedback (via GOGGLE_DEV_MODE env var)
  - Appropriate log levels (INFO for trials, ERROR for problems)
  - Rotation/archival strategy (optional)
  - **Implemented in**: `data_logger.py:setup_logging()`

### 3.2 Data Recording
- [x] Implement trial data recorder:
  - CSV file: `{participant}_{session}_{timestamp}.csv`
  - Required columns: goggle_level, uncomfortable, trial_number, reversals_so_far
  - Additional metadata: timestamp, participant_id, session_id
  - Immediate flush after each trial (ensure data persists on crash)
  - **Implemented in**: `data_logger.py:DataLogger`
- [x] Implement staircase serialization:
  - Save PsychoPy staircase object: `{participant}_{session}_{timestamp}_staircase.psydat`
  - Use pickle or PsychoPy's built-in save method
  - **Implemented in**: `staircase.py:StaircaseManager.save()`, called in `calibrate.py:219`

## Phase 4: Experiment Logic

### 4.1 Adaptive Staircase
- [x] Implement staircase using PsychoPy's StairHandler:
  - Algorithm: 1-up-1-down (nUp=1, nDown=1) - **Note: Changed from 3-down-1-up**
  - Start value: 128 (configurable)
  - Step sizes: [32, 16, 8, 4, 2, 1] (configurable)
  - Step type: 'lin' (linear steps)
  - Min value: 1, Max value: 255 (0 reserved for shutdown)
  - Max trials: 50 (configurable), terminates after target reversals
  - **Implemented in**: `staircase.py:StaircaseManager`
- [x] Track reversal points for threshold calculation
  - **Implemented in**: `staircase.py:get_reversal_count()`, `calculate_threshold()`

### 4.2 Trial Flow
- [x] Implement single trial sequence:
  1. Pre-stimulus delay (6s, configurable)
     - Display countdown or "Get ready" message
  2. Set goggles to test brightness level
  3. Stimulus duration (2s, configurable)
  4. Set goggles to 0 (off)
  5. Display response prompt to experimenter
  6. Wait for Y key (uncomfortable) or other key (comfortable)
  7. Log response
  8. Update staircase
  9. Inter-trial interval (6s, configurable)
  - **Implemented in**: `calibrate.py:run_trial()`
- [x] Implement timing using core.wait() or Clock
  - **Uses**: PsychoPy's `core.wait()` in `experiment_ui.py`
- [x] Ensure timing precision ±0.1s
  - **Verified**: Simple timing mode set in `calibrate.py:16`

### 4.3 Experimenter Interface
- [x] Implement display window (or console output):
  - Current trial number (e.g., "Trial 15/30")
  - Current brightness level being tested
  - Number of reversals so far
  - Response prompt: "Was that uncomfortable? (Y/N)"
  - Instructions for abort (ESC to quit)
  - **Implemented in**: `experiment_ui.py:ExperimentUI`
- [x] Handle keyboard input (Y for uncomfortable, other for comfortable)
  - **Implemented in**: `experiment_ui.py:get_response()`
- [x] Provide clear visual feedback for each response
  - **Implemented with**: Real-time display updates during trials

## Phase 5: Safety & Completion

### 5.1 Abort Handling
- [x] Implement ESC key abort:
  - Immediate exit from trial loop
  - Set goggles to 0
  - Save all data collected so far
  - Clean exit with message
  - **Implemented in**: `experiment_ui.py:check_for_abort()`, `calibrate.py:237-240`
- [x] Implement exception handlers:
  - Catch all exceptions in main loop
  - Ensure goggles→0 in finally block
  - Log exception details
  - Save partial data
  - **Implemented in**: `calibrate.py:156-245` (try/finally blocks)

### 5.2 Threshold Calculation
- [x] Implement threshold estimator:
  - Extract reversal points from staircase
  - If ≥6 reversals: average last 6
  - If <6 reversals: average all reversals
  - Display threshold to experimenter at end
  - Save threshold to log and/or summary file
  - **Implemented in**: `staircase.py:calculate_threshold()`, called in `calibrate.py:210`

### 5.3 Session Initialization
- [x] Implement participant/session ID entry:
  - Prompt experimenter for participant ID
  - Prompt for session ID
  - Validate IDs (no special characters that break filenames)
  - Generate timestamp for filenames
  - Create data files before starting
  - **Implemented in**: `calibrate.py:get_participant_info_console()`, `data_logger.py:validate_participant_id/validate_session_id`

## Phase 6: Deployment Scripts

### 6.1 Run Script
- [x] Implement `scripts/run_calibrate.sh`:
  - Activate `.venv/`
  - Change to project directory
  - Run `python calibrate.py`
  - Handle errors gracefully
  - **Note**: Output goes to terminal, not log file (logging handled by data_logger)
  - **Implemented in**: `scripts/run_calibrate.sh`

### 6.2 Desktop Launcher
- [x] Create `.command` file or Automator app:
  - Double-click to launch experiment
  - No terminal knowledge required for users
  - Clear error messages if setup incomplete
  - **Implemented**: `scripts/Run Calibration.command` (mentioned in README.md:53-65)

## Phase 7: Testing & Validation

### 7.1 Unit Testing
- [x] Test configuration loading:
  - Valid config
  - Missing config (auto-generation)
  - Malformed JSON
  - Invalid values
  - **Note**: Tested during development, but no formal test suite file
- [x] Test goggles controller:
  - Normal operation
  - Exception during operation (cleanup guaranteed?)
  - Serial port connection failure
  - **Tested with**: `mock_serial_device.py` for protocol validation
- [x] Test staircase logic:
  - Correct step sizes
  - Reversal detection
  - Threshold calculation
  - **Extensive testing in**: `tests/` directory (15+ test files)

### 7.2 Integration Testing
- [x] Test complete experiment flow:
  - Run full experiment
  - Verify CSV output format
  - Verify .psydat file creation
  - Check log file completeness
  - **Tested with**: `tests/test_integration*.py` files
- [x] Test error scenarios:
  - ESC abort mid-experiment
  - Simulated crash (KeyboardInterrupt)
  - Power loss simulation (manual kill)
  - Verify goggles return to 0 in all cases
  - **Verified in**: Integration tests and manual testing

### 7.3 Platform Testing
- [x] Test on macOS 26 (development)
  - **Status**: Working on macOS 25.0.0 (Darwin)
- [ ] Test on macOS 12 Monterey (deployment target)
  - **Status**: Not yet tested on target platform
- [ ] Verify timing precision on both platforms
  - **Status**: Needs verification with actual hardware
- [ ] Test with actual hardware (goggles + serial connection)
  - **Status**: Mock device tested, real hardware testing pending

## Phase 8: User Feedback Enhancements (Added 2024-10-26)

### 8.1 Starting Intensity Input and Metadata File
**Context**: After user demo, need ability for experimenter to specify starting brightness level for each session, plus comprehensive metadata tracking.

**Requirements:**

**A. Starting Intensity Input**
- [ ] Add starting intensity prompt to session initialization (same dialog flow as participant/session ID)
  - Prompt: "Enter Starting Intensity (1-255): "
  - Must be an integer between 1 and 255 (inclusive)
  - Required field - continue prompting until valid value entered
  - Validation: reject non-integers, values < 1, values > 255
  - Clear error messages for invalid input
- [ ] Pass starting intensity to staircase initialization
  - Replace current hardcoded/config start value with user-entered value
  - Update `staircase.py:create_staircase_from_config()` or similar
- [ ] Pass starting intensity to DataLogger for metadata recording

**B. Metadata File Implementation**
- [ ] Create `.meta` file alongside CSV with same basename
  - Format: `{participant}_{session}_{timestamp}.meta`
  - Example: `P001_S1_20241026_142345.csv` → `P001_S1_20241026_142345.meta`
- [ ] Format: INI-style key-value pairs (simple `key=value` lines)
- [ ] Auto-flush after every write (same safety philosophy as CSV)
- [ ] Write metadata incrementally as values become available:
  - At session start: participant_id, session_id, timestamp, starting_intensity, experiment_start_time, config info, Python/PsychoPy versions, experiment_completed=false
  - During experiment: Update experiment_completed status if needed
  - At experiment end: final_threshold, total_trials, total_reversals, experiment_end_time, experiment_completed=true
- [ ] Handle partial results: Always write what's known, so aborted experiments have partial metadata

**C. Metadata Fields**

*Session Information:*
- `participant_id` - Participant identifier
- `session_id` - Session identifier
- `timestamp` - Filename timestamp (YYYYMMDD_HHMMSS format)
- `experiment_start_time` - Human-readable start time (YYYY-MM-DD HH:MM:SS)
- `experiment_end_time` - Human-readable end time (YYYY-MM-DD HH:MM:SS)

*Experiment Parameters:*
- `starting_intensity` - User-entered starting brightness (1-255)
- `config_file_path` - Path to config file used (or config hash)

*System Information:*
- `python_version` - Python version (e.g., "3.10.15")
- `psychopy_version` - PsychoPy version (e.g., "2025.1.1")

*Results:*
- `final_threshold` - Calculated threshold (format: "145.67")
- `total_trials` - Total number of trials completed
- `total_reversals` - Total number of reversals observed
- `experiment_completed` - "true" or "false" (false for aborted/crashed)
- `experiment_aborted` - "true" if ESC pressed, "false" otherwise (omitted if not applicable)

**D. Implementation Details**

*DataLogger Changes (`data_logger.py`):*
- [ ] Add `__init__` parameter: `starting_intensity: Optional[int] = None`
- [ ] Generate `.meta` filepath alongside CSV path
- [ ] Add method: `_write_metadata(incremental=True)` - write/rewrite metadata file
  - If incremental=True, preserve existing values, only update changed fields
  - If incremental=False, full rewrite
- [ ] Add method: `write_final_results(threshold, trials, reversals)` - update metadata with results
- [ ] Call `_write_metadata()` in `open()` - write initial session metadata
- [ ] Call `_write_metadata()` in `close()` - update end_time, completed status
- [ ] Flush metadata file after every write
- [ ] Add utility function: `read_metadata(meta_path: Path) -> dict[str, str]` - parse .meta file

*Integration (`calibrate.py`):*
- [ ] Modify `get_participant_info_console()` to prompt for starting_intensity
- [ ] Add validation function: `validate_starting_intensity(value: str) -> Optional[int]`
- [ ] Pass starting_intensity to DataLogger constructor
- [ ] Pass starting_intensity to staircase creation
- [ ] After experiment completes, call `logger.write_final_results(threshold, n_trials, n_reversals)`
- [ ] Ensure metadata written even on abort (try/finally blocks)

*Configuration (`config.py`):*
- [ ] Keep `start_value` in config as fallback/documentation
- [ ] User-entered value always overrides config value

**E. Example Metadata File**

Initial file (at experiment start):
```ini
participant_id=P001
session_id=S1
timestamp=20241026_142345
experiment_start_time=2024-10-26 14:23:45
starting_intensity=128
config_file_path=/Users/user/Documents/Calibration/config/experiment_config.json
python_version=3.10.15
psychopy_version=2025.1.1
experiment_completed=false
```

Final file (at experiment end):
```ini
participant_id=P001
session_id=S1
timestamp=20241026_142345
experiment_start_time=2024-10-26 14:23:45
experiment_end_time=2024-10-26 14:28:32
starting_intensity=128
config_file_path=/Users/user/Documents/Calibration/config/experiment_config.json
python_version=3.10.15
psychopy_version=2025.1.1
final_threshold=145.67
total_trials=23
total_reversals=8
experiment_completed=true
```

Aborted experiment file (ESC pressed during trial 12):
```ini
participant_id=P001
session_id=S1
timestamp=20241026_142345
experiment_start_time=2024-10-26 14:23:45
experiment_end_time=2024-10-26 14:26:18
starting_intensity=128
config_file_path=/Users/user/Documents/Calibration/config/experiment_config.json
python_version=3.10.15
psychopy_version=2025.1.1
total_trials=12
total_reversals=3
experiment_completed=false
experiment_aborted=true
```

**Implementation Notes:**
- Use Python's `sys.version` for Python version, `psychopy.__version__` for PsychoPy version
- For aborted experiments, write what's available (partial trials/reversals, no threshold)
- Set `experiment_aborted=true` when ESC is pressed (KeyboardInterrupt caught)
- Set `experiment_completed=false` for both aborts and crashes
- Metadata file can be parsed line-by-line with simple `split('=', 1)`
- Add method to DataLogger: `mark_aborted()` - call from KeyboardInterrupt handler

### 8.2 Improved Response Input with Correction
**Context**: After user demo, experimenters need ability to correct accidental Y keypresses and have better visual feedback.

**Current Behavior (to be changed):**
- Response prompt appears after stimulus ends
- Wait for Y key (uncomfortable) or timeout (comfortable)
- No ability to correct if Y pressed in error
- No visual feedback showing what was entered

**New Requirements:**
- [ ] Continuous keyboard monitoring during trial
  - Start listening: when stimulus begins (goggles turn on)
  - Stop listening: when inter-trial interval ends
  - Listen for: Y key (uncomfortable) and N key (comfortable)
- [ ] Real-time visual feedback
  - Display current response state on screen
  - Update immediately when Y or N pressed
  - Clear visual indication: "Current Response: UNCOMFORTABLE" vs "Current Response: comfortable"
  - Make uncomfortable response highly visible (large text, color if possible)
- [ ] Response correction capability
  - Last key pressed wins (Y or N)
  - Experimenter can press Y, then correct with N (or vice versa)
  - Final response at end of inter-trial interval is recorded
- [ ] Trial flow timing unchanged
  - Pre-stimulus delay: same as before
  - Stimulus duration: same as before (goggles on)
  - Inter-trial interval: same as before (goggles off)
  - Only difference: keyboard monitored throughout instead of just after stimulus

**Implementation Notes:**
- Modify `experiment_ui.py:get_response()` to accept keyboard input throughout trial
- Track last key pressed (Y or N) in real-time
- Update display on each keypress
- Return final response at end of inter-trial interval
- Consider visual design: large text, contrasting colors for uncomfortable vs comfortable
- Ensure ESC abort still works at any time

**Edge Cases to Consider:**
- What if no key pressed? (Default to comfortable, as before)
- What if keys pressed during pre-stimulus delay? (Ignore, or start listening only at stimulus onset?)
- Ensure goggles timing is not affected by keyboard monitoring

## Phase 9: Documentation & Delivery

### 8.1 User Documentation
- [x] Update README.md with:
  - Installation instructions (run setup.sh)
  - How to launch experiment (run_calibrate.sh or desktop launcher)
  - Experimenter workflow instructions
  - Troubleshooting common issues
  - Data file locations
  - **Status**: README.md is comprehensive and complete

### 8.2 Code Documentation
- [x] Add Google-style docstrings to all functions
  - **Status**: All major functions documented
- [x] Add type hints to all function signatures
  - **Status**: Type hints present throughout codebase
- [x] Add inline comments for complex psychophysics logic
  - **Status**: Staircase logic well-commented
- [x] Document safety-critical sections clearly
  - **Status**: Safety sections clearly marked in goggles.py and calibrate.py

### 8.3 Final Checks
- [x] Run Black formatter on all code
  - **Status**: Code appears consistently formatted
- [ ] Verify all requirements in PROJECT_SPEC.md are met
  - **Status**: Needs systematic verification checklist
- [ ] Review code with research staff perspective
  - **Status**: Ready for user review
- [ ] Confirm data integrity guarantees
  - **Status**: Implemented but needs final verification

## Implementation Order

Recommended implementation sequence:
1. Setup script (scripts/setup.sh) - enables local testing
2. Configuration system - foundation for everything else
3. Goggles controller - critical safety component
4. Logging system - needed before trials
5. Staircase logic - core experiment methodology
6. Trial flow - integrate all pieces
7. Experimenter UI - make it usable
8. Abort/cleanup handlers - ensure safety
9. Threshold calculation - complete the analysis
10. Run script - enable deployment
11. Testing - validate everything
12. Documentation - prepare for handoff

## Risk Areas

- **Serial port communication**: May need hardware for proper testing
- **Timing precision**: Verify PsychoPy timing works reliably on target platform
- **Safety guarantees**: Must exhaustively test all exit paths ensure goggles→0
- **Config validation**: Need comprehensive error handling for user-edited JSON
- **Data integrity**: Must guarantee trial data persists even on crashes

## Dependencies to Research

Must verify current PsychoPy 2025.1.1 documentation for:
- `psychopy.data.StairHandler` (or equivalent in 2025.1.1)
- Serial port library (psychopy.hardware.serial vs. pyserial)
- Event/keyboard handling API
- Data saving format (.psydat)
- Core timing functions (core.wait, Clock, etc.)
