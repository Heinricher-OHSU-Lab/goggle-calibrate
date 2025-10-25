"""Experimenter-facing user interface for goggle calibration experiment.

This module provides a PsychoPy window-based interface for the experimenter
to control the experiment and monitor progress. The subject cannot see this
display (they wear goggles that fully cover their eyes).
"""

import logging
from typing import Optional

from psychopy import core, event, visual
from psychopy.gui import DlgFromDict


class ExperimentUI:
    """Experimenter-facing user interface using PsychoPy window.

    Displays trial information, instructions, and response prompts.
    Handles keyboard input from the experimenter.
    """

    def __init__(
        self,
        fullscreen: bool = False,
        show_instructions: bool = True
    ):
        """Initialize experimenter UI.

        Args:
            fullscreen: Run window in fullscreen mode
            show_instructions: Show initial instructions screen
        """
        self.fullscreen = fullscreen
        self.show_instructions_flag = show_instructions

        # Create window
        self.win = visual.Window(
            size=[1024, 768],
            fullscr=fullscreen,
            color='black',
            units='height',
            allowGUI=True
        )

        # Create text stimuli for different display modes
        self.text = visual.TextStim(
            win=self.win,
            text='',
            color='white',
            height=0.035,
            wrapWidth=0.9,
            alignText='left',
            anchorHoriz='left',
            pos=(-0.45, 0)
        )

        # Create clock for timing
        self.clock = core.Clock()

        logging.info(f"ExperimentUI initialized (fullscreen={fullscreen})")

    def get_participant_info(self) -> tuple[str, str]:
        """Get participant and session IDs from GUI dialog.

        Returns:
            Tuple of (participant_id, session_id)

        Raises:
            SystemExit: If dialog is cancelled
        """
        # Create dialog with text fields
        info = {
            'Participant ID': '',
            'Session ID': ''
        }

        dlg = DlgFromDict(
            dictionary=info,
            title='Goggle Calibration Experiment',
            order=['Participant ID', 'Session ID'],
            tip={
                'Participant ID': 'Enter participant identifier (letters, numbers, - and _ only)',
                'Session ID': 'Enter session identifier (letters, numbers, - and _ only)'
            }
        )

        if not dlg.OK:
            logging.info("Participant info dialog cancelled by user")
            raise SystemExit("Experiment cancelled by user")

        participant_id = info['Participant ID'].strip()
        session_id = info['Session ID'].strip()

        logging.info(f"Participant info entered: participant={participant_id}, session={session_id}")

        return participant_id, session_id

    def show_instructions(self, participant_id: str, session_id: str) -> None:
        """Display initial instructions to experimenter.

        Args:
            participant_id: Participant identifier
            session_id: Session identifier
        """
        if not self.show_instructions_flag:
            return

        instructions = f"""Goggle Calibration Experiment

Participant: {participant_id}
Session: {session_id}

EXPERIMENTER INSTRUCTIONS:

1. Ensure subject is wearing goggles comfortably

2. Explain to subject: "You will see brief flashes of light.
   Please tell me only if a flash is uncomfortable.
   If you don't say anything, I'll assume it was comfortable."

3. During each trial:
   - Wait for the light stimulus
   - Ask subject: "Uncomfortable?"
   - Press Y ONLY if subject reports discomfort
   - No response = comfortable (automatic after interval)

4. Press ESC at any time to abort

Press SPACE to begin experiment"""

        self.text.text = instructions
        self.text.draw()
        self.win.flip()

        # Wait for space bar
        event.waitKeys(keyList=['space'])
        logging.info("Instructions acknowledged, starting experiment")

    def show_trial_info(
        self,
        trial_number: int,
        total_trials: int,
        current_level: int,
        reversals: int
    ) -> None:
        """Display current trial information.

        Args:
            trial_number: Current trial number (1-indexed)
            total_trials: Total number of trials
            current_level: Brightness level being tested (0-255)
            reversals: Number of reversals so far
        """
        info_text = f"""Trial {trial_number} of {total_trials}

Brightness Level: {current_level}
Reversals: {reversals}

Preparing stimulus..."""

        self.text.text = info_text
        self.text.draw()
        self.win.flip()

        logging.debug(
            f"Displayed trial info: {trial_number}/{total_trials}, "
            f"level={current_level}, reversals={reversals}"
        )

    def show_countdown(self, seconds: float, message: str = "Starting in") -> None:
        """Display countdown timer.

        Args:
            seconds: Number of seconds to count down
            message: Message to display above countdown
        """
        start_time = self.clock.getTime()

        while True:
            elapsed = self.clock.getTime() - start_time
            remaining = seconds - elapsed

            if remaining <= 0:
                break

            countdown_text = f"""{message}

{remaining:.1f}s"""

            self.text.text = countdown_text
            self.text.draw()
            self.win.flip()

            # Check for abort
            keys = event.getKeys(keyList=['escape'])
            if 'escape' in keys:
                raise KeyboardInterrupt("Experiment aborted by experimenter")

            core.wait(0.05)  # Small delay to reduce CPU usage

    def show_stimulus_active(self, level: int, duration: float) -> None:
        """Display message while stimulus is active.

        Args:
            level: Brightness level being presented (0-255)
            duration: Duration of stimulus in seconds
        """
        stim_text = f"""STIMULUS ACTIVE

Brightness: {level}

Duration: {duration:.1f}s"""

        self.text.text = stim_text
        self.text.draw()
        self.win.flip()

        # Wait for duration, checking for abort
        start_time = self.clock.getTime()
        while (self.clock.getTime() - start_time) < duration:
            keys = event.getKeys(keyList=['escape'])
            if 'escape' in keys:
                raise KeyboardInterrupt("Experiment aborted by experimenter")
            core.wait(0.05)

    def get_response(
        self,
        trial_number: int,
        timeout: float
    ) -> bool:
        """Prompt experimenter for subject's response.

        Waits for the full timeout period. If 'Y' is pressed, registers as
        uncomfortable. If timeout elapses with no 'Y', registers as comfortable.
        This maintains consistent trial timing.

        Args:
            trial_number: Current trial number
            timeout: Maximum time to wait for response (seconds)

        Returns:
            True if uncomfortable (Y pressed), False if comfortable (no Y pressed)

        Raises:
            KeyboardInterrupt: If ESC is pressed
        """
        prompt_text = f"""Trial {trial_number}

Ask subject: "Uncomfortable?"

Press Y if YES (uncomfortable)
No response = comfortable

Time remaining: """

        start_time = self.clock.getTime()
        response = False  # Default to comfortable

        while True:
            elapsed = self.clock.getTime() - start_time
            remaining = timeout - elapsed

            if remaining <= 0:
                break

            # Update display with countdown
            display_text = prompt_text + f"{remaining:.1f}s"
            self.text.text = display_text
            self.text.draw()
            self.win.flip()

            # Check for keys
            keys = event.getKeys(keyList=['y', 'escape'])

            if 'escape' in keys:
                raise KeyboardInterrupt("Experiment aborted by experimenter")
            elif 'y' in keys:
                response = True
                # Don't break - wait for full timeout to maintain cadence
                logging.info(f"Trial {trial_number}: Response = UNCOMFORTABLE (at {elapsed:.1f}s)")

            core.wait(0.05)

        if not response:
            logging.info(f"Trial {trial_number}: Response = COMFORTABLE (no Y pressed)")

        return response

    def show_completion(
        self,
        n_trials: int,
        n_reversals: int,
        threshold: Optional[float]
    ) -> None:
        """Display experiment completion message.

        Args:
            n_trials: Number of trials completed
            n_reversals: Number of reversals achieved
            threshold: Estimated threshold (or None if not enough reversals)
        """
        if threshold is not None:
            threshold_str = f"{threshold:.1f}"
        else:
            threshold_str = "N/A (insufficient reversals)"

        completion_text = f"""Experiment Complete!

Trials completed: {n_trials}
Reversals: {n_reversals}
Estimated threshold: {threshold_str}

Press SPACE to exit"""

        self.text.text = completion_text
        self.text.draw()
        self.win.flip()

        # Wait for space bar
        event.waitKeys(keyList=['space'])
        logging.info("Completion screen acknowledged")

    def show_abort_message(self, message: str = "Experiment aborted") -> None:
        """Display abort message.

        Args:
            message: Message to display
        """
        abort_text = f"""{message}

Saving data...

Press SPACE to exit"""

        self.text.text = abort_text
        self.text.draw()
        self.win.flip()

        core.wait(2.0)  # Give time to read

        # Wait for space bar
        event.waitKeys(keyList=['space'])

    def show_error(self, error_message: str) -> None:
        """Display error message.

        Args:
            error_message: Error message to display
        """
        error_text = f"""ERROR

{error_message}

Press SPACE to exit"""

        self.text.text = error_text
        self.text.color = 'red'
        self.text.draw()
        self.win.flip()

        core.wait(2.0)  # Give time to read

        # Wait for space bar
        event.waitKeys(keyList=['space'])

        # Reset text color
        self.text.color = 'white'

    def close(self) -> None:
        """Close the window and cleanup."""
        if self.win is not None:
            self.win.close()
            logging.info("ExperimentUI closed")

    def __enter__(self) -> 'ExperimentUI':
        """Enter context manager.

        Returns:
            Self for use in with statement
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager: close window.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if exc_type is not None:
            logging.error(
                f"Exception in UI context: {exc_type.__name__}: {exc_val}"
            )
        self.close()


def create_ui_from_config(config: dict) -> ExperimentUI:
    """Create an ExperimentUI from a configuration dictionary.

    Args:
        config: Configuration dictionary containing 'display' section

    Returns:
        Configured ExperimentUI instance
    """
    display = config.get("display", {})

    return ExperimentUI(
        fullscreen=display.get("fullscreen", False),
        show_instructions=display.get("show_instructions", True)
    )