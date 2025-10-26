#!/usr/bin/env python
"""Goggle Calibration Experiment - Main Script

This script runs a light discomfort threshold experiment using adaptive
staircase methodology (1-up-1-down) to find the brightness level at which
subjects report discomfort approximately 50% of the time.

Safety: Goggles are automatically turned off on ANY exit path (normal,
exception, or keyboard interrupt).
"""

import os

# Performance optimizations: Set environment variables BEFORE importing PsychoPy
# This experiment only needs ~0.1s timing precision, not microsecond accuracy
os.environ['PSYCHOPY_TIMING_MODE'] = 'simple'

import logging
import sys

from psychopy import prefs

# Disable unnecessary PsychoPy features for faster startup
prefs.general['startUpPlugins'] = []  # No plugins needed
prefs.hardware['audioLib'] = []  # No audio used in this experiment
prefs.general['allowGUI'] = True  # Allow GUI for window creation

import config
import data_logger
import experiment_ui
import goggles
import staircase


def run_trial(
    trial_number: int,
    level: int,
    ui: experiment_ui.ExperimentUI,
    goggles_controller: goggles.GoggleController,
    logger: data_logger.DataLogger,
    staircase_mgr: staircase.StaircaseManager,
    timing_config: dict
) -> bool:
    """Run a single trial.

    Args:
        trial_number: Current trial number (1-indexed)
        level: Brightness level to test (0-255)
        ui: ExperimentUI instance
        goggles_controller: GoggleController instance
        logger: DataLogger instance
        staircase_mgr: StaircaseManager instance
        timing_config: Timing configuration dictionary

    Returns:
        True if uncomfortable response, False if comfortable

    Raises:
        KeyboardInterrupt: If ESC is pressed
    """
    # Get timing parameters
    pre_delay = timing_config["pre_stimulus_delay"]
    stim_duration = timing_config["stimulus_duration"]
    iti = timing_config["inter_trial_interval"]

    # Show trial info
    ui.show_trial_info(
        trial_number=trial_number,
        total_trials=staircase_mgr.n_trials,
        current_level=level,
        reversals=staircase_mgr.get_reversal_count()
    )

    # Pre-stimulus delay
    ui.show_countdown(pre_delay, "Stimulus in")

    # Present stimulus
    logging.info(f"Trial {trial_number}: Setting goggles to brightness {level}")
    goggles_controller.set_brightness(level)

    ui.show_stimulus_active(level, stim_duration)

    # Turn off goggles
    logging.info(f"Trial {trial_number}: Turning off goggles")
    goggles_controller.set_brightness(0)

    # Get response (uses inter-trial interval as timeout)
    uncomfortable = ui.get_response(trial_number, iti)

    # Log trial data BEFORE updating staircase
    # This ensures data is saved even if something fails
    logger.log_trial(
        trial_number=trial_number,
        goggle_level=level,
        uncomfortable=uncomfortable,
        reversals_so_far=staircase_mgr.get_reversal_count()
    )

    # Update staircase
    staircase_mgr.add_response(uncomfortable)

    return uncomfortable


def get_participant_info_console() -> tuple[str, str, int]:
    """Get participant ID, session ID, and starting intensity from console input.

    Returns:
        Tuple of (participant_id, session_id, starting_intensity)

    Raises:
        ValueError: If IDs are invalid
    """
    print("\n" + "="*60)
    print("GOGGLE CALIBRATION EXPERIMENT")
    print("="*60)
    print()

    while True:
        participant_id = input("Enter Participant ID: ").strip()
        if not data_logger.validate_participant_id(participant_id):
            print("ERROR: Invalid Participant ID. Use only letters, numbers, underscores, and hyphens.")
            print()
            continue
        break

    while True:
        session_id = input("Enter Session ID: ").strip()
        if not data_logger.validate_session_id(session_id):
            print("ERROR: Invalid Session ID. Use only letters, numbers, underscores, and hyphens.")
            print()
            continue
        break

    while True:
        intensity_input = input("Enter Starting Intensity (1-255): ").strip()
        starting_intensity = data_logger.validate_starting_intensity(intensity_input)
        if starting_intensity is None:
            print("ERROR: Invalid Starting Intensity. Must be an integer between 1 and 255.")
            print()
            continue
        break

    print()
    return participant_id, session_id, starting_intensity


def run_experiment(cfg: dict) -> None:
    """Run the complete experiment.

    Args:
        cfg: Configuration dictionary

    Raises:
        KeyboardInterrupt: If ESC is pressed
        Exception: For other errors
    """
    # Get participant info from console BEFORE creating UI
    # This avoids Qt initialization issues
    participant_id, session_id, starting_intensity = get_participant_info_console()
    logging.info(
        f"Starting experiment: participant={participant_id}, "
        f"session={session_id}, starting_intensity={starting_intensity}"
    )

    # Create UI
    with experiment_ui.create_ui_from_config(cfg) as ui:
        # Initialize logger variable outside try block so it's accessible in except
        logger = None

        try:

            # Show instructions
            ui.show_instructions(participant_id, session_id)

            # Get paths
            paths = config.get_expanded_paths(cfg)
            data_dir = paths["data_directory"]

            # Create data logger
            logger = data_logger.DataLogger(
                data_dir=data_dir,
                participant_id=participant_id,
                session_id=session_id,
                starting_intensity=starting_intensity,
                auto_flush=cfg["data"]["auto_save"]
            )

            # Create staircase with user-specified starting intensity
            staircase_mgr = staircase.create_staircase_from_config(cfg, starting_intensity)

            # Create goggles controller
            goggles_controller = goggles.create_goggles_from_config(cfg)

            # Open connections
            logger.open()
            goggles_controller.open()

            try:
                # Run trials
                trial_number = 0
                while not staircase_mgr.is_finished():
                    trial_number += 1

                    # Get next level
                    level = staircase_mgr.get_next_level()
                    if level is None:
                        break

                    # Run trial
                    run_trial(
                        trial_number=trial_number,
                        level=level,
                        ui=ui,
                        goggles_controller=goggles_controller,
                        logger=logger,
                        staircase_mgr=staircase_mgr,
                        timing_config=cfg["timing"]
                    )

                # Experiment completed normally
                logging.info("Experiment completed successfully")

                # Calculate threshold
                threshold_reversals = cfg["data"].get("threshold_reversals", 6)
                threshold = staircase_mgr.calculate_threshold(threshold_reversals)

                # Write final results to metadata
                logger.write_final_results(
                    final_threshold=threshold,
                    total_trials=staircase_mgr.get_trial_count(),
                    total_reversals=staircase_mgr.get_reversal_count()
                )

                # Save staircase data
                staircase_file = data_logger.generate_staircase_filename(
                    data_dir=data_dir,
                    participant_id=participant_id,
                    session_id=session_id,
                    timestamp=logger.timestamp
                )
                staircase_mgr.save(staircase_file)

                # Show completion
                ui.show_completion(
                    n_trials=staircase_mgr.get_trial_count(),
                    n_reversals=staircase_mgr.get_reversal_count(),
                    threshold=threshold
                )

                # Log summary
                summary = staircase_mgr.get_data_summary()
                logging.info(f"Experiment summary: {summary}")

            finally:
                # CRITICAL: Always close goggles and logger
                goggles_controller.close()
                if logger is not None:
                    logger.close()

        except KeyboardInterrupt:
            logging.warning("Experiment aborted by experimenter (ESC pressed)")
            # Mark experiment as aborted in metadata
            if logger is not None:
                logger.mark_aborted()
            ui.show_abort_message("Experiment Aborted")
            raise

        except Exception as e:
            logging.error(f"Experiment error: {e}", exc_info=True)
            ui.show_error(f"Error: {str(e)}")
            raise


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Load configuration
        cfg = config.load_config()

        # Setup logging
        paths = config.get_expanded_paths(cfg)
        data_logger.setup_logging(
            log_dir=paths["log_directory"],
            log_level=logging.INFO
        )

        logging.info("="*60)
        logging.info("GOGGLE CALIBRATION EXPERIMENT STARTING")
        logging.info("="*60)

        # Run experiment
        run_experiment(cfg)

        logging.info("Experiment completed successfully")
        return 0

    except KeyboardInterrupt:
        logging.warning("Experiment aborted by user")
        return 1

    except config.ConfigError as e:
        logging.error(f"Configuration error: {e}")
        print(f"\nCONFIGURATION ERROR: {e}", file=sys.stderr)
        print("\nPlease check your configuration file.", file=sys.stderr)
        return 1

    except goggles.GoggleError as e:
        logging.error(f"Goggles error: {e}")
        print(f"\nGOGGLES ERROR: {e}", file=sys.stderr)
        print("\nPlease check serial port connection and configuration.", file=sys.stderr)
        return 1

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        print("\nPlease check the log file for details.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())