# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Requirements Source

**ALWAYS read PROJECT_SPEC.md first** - it contains the complete, authoritative specification for this project including experiment methodology, configuration schema, data formats, hardware interface details, and all requirements.

This file (CLAUDE.md) provides Claude-specific guidance for working in this codebase.

## Working in This Repository

### Development Commands

```bash
# Initial setup
./scripts/setup.sh

# Activate virtual environment
source .venv/bin/activate

# Run experiment
python calibrate.py

# Format code before commits
black .
```

### Key Implementation Notes

**Virtual Environment**: The project uses `.venv/` (with dot prefix), not `venv/`

**Main Script Name**: `calibrate.py` (note: PROJECT_SPEC.md references `experiment.py` in one place - `calibrate.py` is correct)

**Data Directories**:
- Development testing: `calibration-test-data/` (in repo, gitignored)
- Production use: `~/Documents/Calibration/` (outside repo)

**Python Version**: Must use Python 3.10.x (managed via pyenv). Python 3.11+ will not work due to PsychoPy dependencies.

### Code Architecture Patterns

**Safety-Critical Hardware Control**: All code that controls the goggles must ensure they return to brightness level 0 on ANY exit path (normal exit, exceptions, keyboard interrupt). Use try/finally blocks or context managers.

**Configuration Loading**: The experiment is highly configurable via JSON. When implementing features, check if parameters should be configurable rather than hardcoded.

**Logging**: This is research software where data integrity is paramount. All trial data must be logged even if errors occur. Consider logging before state changes, not after.

**Experimenter-Facing UI**: Display output is for the experimenter operating the keyboard, not the subject. The subject wears goggles that fully cover their eyes and cannot see the screen.

### Testing Guidance

When implementing features, consider:
- What happens if this crashes mid-trial? (Are goggles left on?)
- What happens if config file is malformed? (Graceful defaults? Clear error?)
- What happens on ESC keypress? (Immediate abort and goggles off?)
- Are all trial outcomes logged to CSV even if experiment aborts?

### Documentation Standards

When asked to document code or add comments:
- Assume reader may be research staff, not just developers
- Explain psychophysics methodology where relevant (e.g., what "1-up-1-down" means)
- Be explicit about units (seconds, milliseconds, brightness 0-255)
- Document safety assumptions (e.g., "assumes goggles turned off before this call")
- Provide type hints where possible including in function signatures.
- Use Google style docstring for all functions
- 
### When Uncertain

- If requirements are unclear or not specified in PROJECT_SPEC.md, ask the user rather than making assumptions. This is research software where incorrect behavior could affect experimental validity or subject safety.
- It is very important to use most recent documenation for any dependencies used in this program.  Do not assume you have current information unless you have actually done a search.

## Pending Issues

### Qt/PsychoPy Initialization Crash

**Status**: Temporarily resolved by reverting to console input, but underlying issue not fully diagnosed.

**Issue**: When using PsychoPy's `DlgFromDict` GUI dialog for participant info input, the program crashes with Qt-related errors. The crash appears to be related to Qt initialization conflicts between PsychoPy and PyQt6.

**Current Workaround**: Participant and session IDs are now collected via console input (`get_participant_info_console()`) BEFORE creating the PsychoPy window. This avoids the Qt initialization conflict.

**Location**: `calibrate.py:96-127` (console input function), `calibrate.py:130-147` (called before UI creation)

**Future Investigation Needed**:
- Determine root cause of Qt initialization conflict
- Check if PsychoPy version upgrade would resolve issue
- Consider whether GUI dialog is actually needed for this use case
- If GUI is preferred, investigate proper Qt initialization order

**Related Files**:
- `calibrate.py` - main experiment script
- `experiment_ui.py:59-93` - contains unused `get_participant_info()` method with Qt dialog

**Note**: The program is currently working with console input. Only revisit if GUI dialog becomes a requirement.

### Slow Startup Time

**Status**: Investigated but no significant improvements found. Tabled for now.

**Issue**: Program takes noticeable time to start up, primarily due to PsychoPy initialization overhead (OpenGL, Qt backends, etc.).

**Optimizations Already Applied**:
- Set `PSYCHOPY_TIMING_MODE='simple'` before importing PsychoPy
- Disabled unnecessary PsychoPy plugins (`prefs.general['startUpPlugins'] = []`)
- Disabled audio library loading (`prefs.hardware['audioLib'] = []`)
- Using minimal selective imports (`from psychopy import prefs` instead of `import psychopy`)
- Removed unused imports (e.g., `core` from calibrate.py)

**Location**: `calibrate.py:12-28` (performance optimizations)

**Analysis**: Most startup time is inherent to PsychoPy window creation in `experiment_ui.py`, which requires loading OpenGL and Qt backends. This is unavoidable for a graphical experiment interface.

**Possible Future Optimizations** (if startup time becomes critical):
- Delay window creation until after participant info is entered (minor gain, code reorganization needed)
- Investigate if PsychoPy can run with even more minimal backends
- Consider alternative lightweight window libraries (major refactoring)

**Note**: Current startup time is acceptable for research use. Only revisit if it becomes a blocker for users.