"""Adaptive staircase procedure for threshold estimation.

This module implements a 3-down-1-up staircase procedure to converge on
the 79.4% discomfort threshold. It wraps PsychoPy's StairHandler with
additional functionality for our specific use case.1
"""

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
from psychopy import data


class StaircaseManager:
    """Manager for adaptive staircase procedure.

    Implements a 3-down-1-up rule to find the brightness level at which
    subjects report discomfort 79.4% of the time. The staircase adjusts
    brightness levels based on responses, using progressively smaller
    step sizes as it converges on the threshold.
    """

    def __init__(
        self,
        start_value: int,
        step_sizes: List[int],
        n_up: int = 1,
        n_down: int = 3,
        n_trials: int = 30,
        step_type: str = 'lin',
        min_val: int = 0,
        max_val: int = 255,
        apply_initial_rule: bool = False
    ):
        """Initialize staircase manager.

        Args:
            start_value: Initial brightness level to test (0-255)
            step_sizes: List of step sizes, used sequentially at each reversal
                       Example: [32, 16, 8, 4, 2, 1] starts with large steps
                       and progressively uses smaller steps
            n_up: Number of "uncomfortable" responses before increasing brightness
                  (making stimulus MORE intense = harder = moving AWAY from threshold)
            n_down: Number of "comfortable" responses before decreasing brightness
                    (making stimulus LESS intense = easier = moving TOWARD threshold)
            n_trials: Minimum number of trials to conduct
            step_type: Type of steps ('lin' for linear, 'log' for logarithmic, 'db' for decibels)
            min_val: Minimum brightness value (0-255)
            max_val: Maximum brightness value (0-255)
            apply_initial_rule: If True, use 1-up/1-down until first reversal,
                               then switch to n_up/n_down rule
        """
        self.start_value = start_value
        self.step_sizes = step_sizes
        self.n_up = n_up
        self.n_down = n_down
        self.n_trials = n_trials
        self.step_type = step_type
        self.min_val = min_val
        self.max_val = max_val
        self.apply_initial_rule = apply_initial_rule

        # Create PsychoPy StairHandler
        # IMPORTANT: PsychoPy's nUp/nDown are defined as:
        # - nUp = number of INCORRECT responses before going UP (increasing intensity)
        # - nDown = number of CORRECT responses before going DOWN (decreasing intensity)
        #
        # For finding discomfort threshold with 3-down-1-up:
        # - comfortable response → we need 3 to go UP (increase brightness)
        # - uncomfortable response → we need 1 to go DOWN (decrease brightness)
        #
        # So we need to SWAP nUp and nDown, and invert the response mapping:
        # - comfortable → "incorrect" (0) → after 3, goes UP
        # - uncomfortable → "correct" (1) → after 1, goes DOWN
        self.staircase = data.StairHandler(
            startVal=start_value,
            stepSizes=step_sizes,
            nUp=n_down,  # SWAPPED: use n_down for nUp (3 comfortable → go up)
            nDown=n_up,  # SWAPPED: use n_up for nDown (1 uncomfortable → go down)
            nTrials=n_trials,
            stepType=step_type,
            minVal=min_val,
            maxVal=max_val,
            applyInitialRule=apply_initial_rule
        )

        # Track trial count manually (PsychoPy's internal counter is for iteration)
        self.trial_count = 0

        logging.info(
            f"StaircaseManager initialized: start={start_value}, "
            f"steps={step_sizes}, {n_down}-down-{n_up}-up, "
            f"range=[{min_val}, {max_val}], trials={n_trials}"
        )

    def get_next_level(self) -> Optional[int]:
        """Get the next brightness level to test.

        Returns:
            Next brightness level (0-255), or None if staircase is finished
        """
        try:
            # Get next value from staircase iterator
            next_val = next(self.staircase)
            # Round to integer (brightness must be whole number)
            level = int(round(next_val))
            # Ensure within bounds
            level = max(self.min_val, min(self.max_val, level))

            logging.debug(f"Next staircase level: {level}")
            return level
        except StopIteration:
            logging.info("Staircase complete (no more trials)")
            return None

    def add_response(self, uncomfortable: bool) -> None:
        """Add a response to the staircase.

        Args:
            uncomfortable: True if subject reported discomfort, False if comfortable

        Note:
            Because we swapped nUp/nDown in the StairHandler initialization,
            we also need to invert the response:
            - comfortable → 0 ("incorrect") → after nUp=3 (swapped), goes UP
            - uncomfortable → 1 ("correct") → after nDown=1 (swapped), goes DOWN
        """
        # Inverted: comfortable=0, uncomfortable=1
        # This works with our swapped nUp/nDown to create proper 3-down-1-up
        response = 1 if uncomfortable else 0

        self.staircase.addData(response)
        self.trial_count += 1

        logging.info(
            f"Trial {self.trial_count}: response={'uncomfortable' if uncomfortable else 'comfortable'} "
            f"(reversals: {self.get_reversal_count()})"
        )

    def get_reversal_count(self) -> int:
        """Get the number of reversals that have occurred.

        A reversal occurs when the staircase changes direction
        (e.g., from decreasing to increasing brightness).

        Returns:
            Number of reversals
        """
        return len(self.staircase.reversalIntensities)

    def get_reversal_intensities(self) -> List[float]:
        """Get the brightness levels at which reversals occurred.

        Returns:
            List of brightness levels at reversal points
        """
        return self.staircase.reversalIntensities.copy()

    def calculate_threshold(self, n_reversals: int = 6) -> Optional[float]:
        """Calculate threshold from reversal points.

        Args:
            n_reversals: Number of last reversals to average (0 = use all)
                        Default is 6 as specified in PROJECT_SPEC.md

        Returns:
            Estimated threshold (average of reversal points), or None if
            insufficient reversals have occurred
        """
        reversals = self.get_reversal_intensities()

        if not reversals:
            logging.warning("No reversals yet, cannot calculate threshold")
            return None

        if n_reversals == 0 or len(reversals) < n_reversals:
            # Use all reversals
            threshold = np.mean(reversals)
            logging.info(
                f"Threshold calculated from all {len(reversals)} reversals: {threshold:.2f}"
            )
        else:
            # Use last n reversals
            threshold = np.mean(reversals[-n_reversals:])
            logging.info(
                f"Threshold calculated from last {n_reversals} reversals: {threshold:.2f}"
            )

        return threshold

    def is_finished(self) -> bool:
        """Check if staircase has finished.

        Returns:
            True if no more trials remain, False otherwise
        """
        return self.staircase.finished

    def get_trial_count(self) -> int:
        """Get the number of trials completed.

        Returns:
            Number of completed trials
        """
        return self.trial_count

    def save(self, filepath: Path) -> None:
        """Save staircase data to file.

        Saves the PsychoPy StairHandler object as a pickle file (.psydat)
        which can be loaded later for analysis.

        Args:
            filepath: Path where staircase data should be saved
                     (should have .psydat extension)
        """
        try:
            self.staircase.saveAsPickle(str(filepath))
            logging.info(f"Staircase data saved to {filepath}")
        except Exception as e:
            logging.error(f"Failed to save staircase data: {e}")
            raise

    def get_data_summary(self) -> dict:
        """Get a summary of staircase data.

        Returns:
            Dictionary containing summary statistics
        """
        reversals = self.get_reversal_intensities()
        threshold = self.calculate_threshold()

        summary = {
            "n_trials": self.trial_count,
            "n_reversals": len(reversals),
            "reversal_intensities": reversals,
            "threshold": threshold,
            "start_value": self.start_value,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "finished": self.is_finished()
        }

        return summary


def create_staircase_from_config(config: dict) -> StaircaseManager:
    """Create a StaircaseManager from a configuration dictionary.

    Args:
        config: Configuration dictionary containing 'staircase' and 'hardware' sections

    Returns:
        Configured StaircaseManager instance
    """
    sc = config["staircase"]
    hw = config["hardware"]

    return StaircaseManager(
        start_value=sc["start_value"],
        step_sizes=sc["step_sizes"],
        n_up=sc["n_up"],
        n_down=sc["n_down"],
        n_trials=sc["n_trials"],
        step_type=sc["step_type"],
        min_val=hw["brightness_min"],
        max_val=hw["brightness_max"],
        apply_initial_rule=sc.get("apply_initial_rule", False)
    )