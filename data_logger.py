"""Data logging system for goggle calibration experiment.

This module handles CSV logging of trial data and ensures data integrity
even in the case of errors or crashes. All data is written immediately
(flushed) after each trial to prevent data loss.
"""

import csv
import logging
import os
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Cache Python and PsychoPy versions at module load time
# (PsychoPy is already imported before this module in normal workflow)
_PYTHON_VERSION = sys.version.split()[0]
try:
    import psychopy
    _PSYCHOPY_VERSION = psychopy.__version__
except (ImportError, AttributeError):
    _PSYCHOPY_VERSION = "unknown"


class DataLogger:
    """Logger for trial-by-trial experimental data.

    Writes CSV files with immediate flushing to ensure data persists
    even if the experiment crashes mid-trial.

    File naming format: {participant}_{session}_{timestamp}.csv
    This ensures sorting by participant → session → date.
    """

    def __init__(
        self,
        data_dir: Path,
        participant_id: str,
        session_id: str,
        starting_intensity: Optional[int] = None,
        auto_flush: bool = True,
        timestamp: Optional[str] = None
    ):
        """Initialize data logger.

        Args:
            data_dir: Directory where data files will be saved
            participant_id: Participant identifier
            session_id: Session identifier
            starting_intensity: Starting brightness intensity (1-255), if provided
            auto_flush: Whether to flush after each write (default: True)
                       Setting this to True ensures data persists even on crashes
            timestamp: Timestamp string (YYYYMMDD_HHMMSS format). If not provided,
                      current time will be used. Providing this allows log files
                      and data files to have matching timestamps.

        Raises:
            IOError: If data directory cannot be created or accessed
        """
        self.data_dir = Path(data_dir)
        self.participant_id = participant_id
        self.session_id = session_id
        self.starting_intensity = starting_intensity
        self.auto_flush = auto_flush

        # Use provided timestamp or generate one
        self.timestamp = timestamp if timestamp else datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: {participant}_{session}_{timestamp}.csv
        filename = f"{participant_id}_{session_id}_{self.timestamp}.csv"
        self.csv_path = self.data_dir / filename

        # Generate metadata filename: {participant}_{session}_{timestamp}.meta
        meta_filename = f"{participant_id}_{session_id}_{self.timestamp}.meta"
        self.meta_path = self.data_dir / meta_filename

        # CSV file handle and writer
        self._csv_file: Optional[Any] = None
        self._csv_writer: Optional[csv.DictWriter] = None

        # Track whether file is open
        self._is_open = False

        # Column names for CSV
        # Note: participant_id and session_id removed - stored in .meta file and filename
        self.fieldnames = [
            "trial_number",
            "goggle_level",
            "uncomfortable",
            "reversals_so_far",
            "timestamp"
        ]

        # Metadata tracking
        self._metadata: dict[str, str] = {}
        self._experiment_start_time: Optional[str] = None
        self._experiment_aborted: bool = False

        # Final results (set by write_final_results())
        self._final_threshold: Optional[float] = None
        self._total_trials: Optional[int] = None
        self._total_reversals: Optional[int] = None

        logging.info(f"DataLogger initialized: {self.csv_path}, {self.meta_path}")

    def open(self) -> None:
        """Open CSV file and write header. Also writes initial metadata.

        Raises:
            IOError: If file cannot be opened
        """
        if self._is_open:
            logging.warning("CSV file already open")
            return

        try:
            self._csv_file = open(self.csv_path, 'w', newline='')
            self._csv_writer = csv.DictWriter(
                self._csv_file,
                fieldnames=self.fieldnames
            )
            self._csv_writer.writeheader()

            if self.auto_flush:
                self._csv_file.flush()

            self._is_open = True
            logging.info(f"Opened CSV file: {self.csv_path}")

            # Record experiment start time and write initial metadata
            self._experiment_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._write_metadata()

        except IOError as e:
            raise IOError(f"Failed to open CSV file {self.csv_path}: {e}")

    def close(self) -> None:
        """Close CSV file and update final metadata."""
        if not self._is_open:
            return

        try:
            if self._csv_file is not None:
                self._csv_file.close()
                logging.info(f"Closed CSV file: {self.csv_path}")
        except Exception as e:
            logging.error(f"Error closing CSV file: {e}")
        finally:
            self._is_open = False
            self._csv_file = None
            self._csv_writer = None

            # Write final metadata with end time
            self._write_metadata()

    def log_trial(
        self,
        trial_number: int,
        goggle_level: int,
        uncomfortable: bool,
        reversals_so_far: int
    ) -> None:
        """Log a single trial's data.

        Data is written immediately and flushed if auto_flush is True.

        Args:
            trial_number: Sequential trial number (1-indexed)
            goggle_level: Brightness level tested (0-255)
            uncomfortable: True if response was "uncomfortable", False otherwise
            reversals_so_far: Cumulative number of reversals

        Raises:
            IOError: If file is not open or write fails
        """
        if not self._is_open:
            raise IOError("Cannot log trial: CSV file not open")

        # Convert boolean to integer (1 = uncomfortable, 0 = comfortable)
        uncomfortable_int = 1 if uncomfortable else 0

        # Generate timestamp for this trial
        trial_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        row = {
            "trial_number": trial_number,
            "goggle_level": goggle_level,
            "uncomfortable": uncomfortable_int,
            "reversals_so_far": reversals_so_far,
            "timestamp": trial_timestamp
        }

        try:
            self._csv_writer.writerow(row)

            # Critical: Flush immediately to ensure data persists
            if self.auto_flush:
                self._csv_file.flush()

            logging.debug(
                f"Logged trial {trial_number}: level={goggle_level}, "
                f"uncomfortable={uncomfortable}, reversals={reversals_so_far}"
            )

        except IOError as e:
            logging.error(f"Failed to write trial data: {e}")
            raise

    def _write_metadata(self) -> None:
        """Write metadata to .meta file.

        Writes all currently available metadata fields to the .meta file.
        Uses INI-style key=value format. Auto-flushes if auto_flush is True.

        The file is completely rewritten each time to ensure consistency.
        """
        try:
            # Build metadata dictionary with session information (always available)
            metadata = {
                'participant_id': self.participant_id,
                'session_id': self.session_id,
                'timestamp': self.timestamp
            }

            if self._experiment_start_time:
                metadata['experiment_start_time'] = self._experiment_start_time

            # Add end time if experiment is done
            if not self._is_open or self._experiment_aborted or self._final_threshold is not None:
                metadata['experiment_end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Experiment parameters
            if self.starting_intensity is not None:
                metadata['starting_intensity'] = str(self.starting_intensity)

            # Try to get config file path (DEFAULT_CONFIG_PATH is a module constant)
            try:
                import config
                metadata['config_file_path'] = str(config.DEFAULT_CONFIG_PATH)
            except (ImportError, AttributeError):
                pass  # Config path not critical

            # System information (from cached module-level variables)
            metadata['python_version'] = _PYTHON_VERSION
            metadata['psychopy_version'] = _PSYCHOPY_VERSION

            # Results (if available)
            if hasattr(self, '_final_threshold') and self._final_threshold is not None:
                metadata['final_threshold'] = f"{self._final_threshold:.2f}"

            if hasattr(self, '_total_trials'):
                metadata['total_trials'] = str(self._total_trials)

            if hasattr(self, '_total_reversals'):
                metadata['total_reversals'] = str(self._total_reversals)

            # Completion status
            if hasattr(self, '_final_threshold') and self._final_threshold is not None:
                metadata['experiment_completed'] = 'true'
            else:
                metadata['experiment_completed'] = 'false'

            if self._experiment_aborted:
                metadata['experiment_aborted'] = 'true'

            # Write to file
            with open(self.meta_path, 'w') as f:
                for key, value in metadata.items():
                    f.write(f"{key}={value}\n")

                # Flush if auto_flush enabled
                if self.auto_flush:
                    f.flush()

            logging.debug(f"Metadata written to {self.meta_path}")

        except Exception as e:
            logging.error(f"Failed to write metadata: {e}")
            # Don't raise - metadata write failure shouldn't stop experiment

    def write_final_results(
        self,
        final_threshold: float,
        total_trials: int,
        total_reversals: int
    ) -> None:
        """Write final experiment results to metadata file.

        Args:
            final_threshold: Calculated threshold value
            total_trials: Total number of trials completed
            total_reversals: Total number of reversals observed
        """
        self._final_threshold = final_threshold
        self._total_trials = total_trials
        self._total_reversals = total_reversals

        # Rewrite metadata file with results
        self._write_metadata()

        logging.info(
            f"Final results written: threshold={final_threshold:.2f}, "
            f"trials={total_trials}, reversals={total_reversals}"
        )

    def mark_aborted(self) -> None:
        """Mark experiment as aborted (ESC pressed).

        Sets the aborted flag and updates the metadata file.
        """
        self._experiment_aborted = True
        self._write_metadata()
        logging.info("Experiment marked as aborted in metadata")

    def get_filepath(self) -> Path:
        """Get the path to the CSV file.

        Returns:
            Path to the CSV file
        """
        return self.csv_path

    def is_open(self) -> bool:
        """Check if CSV file is open.

        Returns:
            True if file is open, False otherwise
        """
        return self._is_open

    def __enter__(self) -> 'DataLogger':
        """Enter context manager: open CSV file.

        Returns:
            Self for use in with statement
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager: close CSV file.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if exc_type is not None:
            logging.error(
                f"Exception in data logger context: {exc_type.__name__}: {exc_val}"
            )
        self.close()


def setup_logging(
    log_dir: Path,
    log_level: int = logging.INFO,
    timestamp: Optional[str] = None
) -> str:
    """Configure Python logging system for the experiment.

    Creates file handler for all runs. Console handler is only added in
    development mode (controlled by GOGGLE_DEV_MODE environment variable).

    Args:
        log_dir: Directory where log files will be saved
        log_level: Logging level for file logging (default: logging.INFO)
        timestamp: Timestamp string (YYYYMMDD_HHMMSS format). If not provided,
                  current time will be used. Providing this allows log files
                  and data files to have matching timestamps.

    Returns:
        The timestamp string used for the log filename (either provided or generated)

    Environment Variables:
        GOGGLE_DEV_MODE: Set to a log level name to enable console logging at that level.
                        Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
                        If not set, console logging is disabled.
    """
    # Create log directory if it doesn't exist
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Use provided timestamp or generate one
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = log_dir / f"{timestamp}.log"

    # Check for development mode first to determine console level
    dev_mode_level = os.environ.get('GOGGLE_DEV_MODE', '').upper()
    console_level = None
    if dev_mode_level:
        # Map string level to logging constant
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        console_level = level_map.get(dev_mode_level, logging.INFO)

    # Configure root logger directly (basicConfig won't work if logging already initialized)
    root_logger = logging.getLogger()
    # Set root logger to minimum level needed (so both file and console handlers work)
    if console_level is not None:
        root_logger.setLevel(min(log_level, console_level))
    else:
        root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler: always enabled for detailed logging
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler: only enabled in development mode
    if console_level is not None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        logging.info(f"Development mode: console logging enabled at {dev_mode_level} level")

    logging.info(f"Logging initialized: {log_filename}")
    logging.info(f"File log level: {logging.getLevelName(log_level)}")

    return timestamp


def validate_participant_id(participant_id: str) -> bool:
    """Validate participant ID format.

    Ensures ID contains only alphanumeric characters, underscores, and hyphens
    to prevent filesystem issues.

    Args:
        participant_id: Participant identifier to validate

    Returns:
        True if valid, False otherwise
    """
    if not participant_id:
        return False

    # Allow alphanumeric, underscore, and hyphen
    allowed_chars = set(string.ascii_letters + string.digits + "_-")
    return all(c in allowed_chars for c in participant_id)


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format.

    Ensures ID contains only alphanumeric characters, underscores, and hyphens
    to prevent filesystem issues.

    Args:
        session_id: Session identifier to validate

    Returns:
        True if valid, False otherwise
    """
    if not session_id:
        return False

    # Allow alphanumeric, underscore, and hyphen
    allowed_chars = set(string.ascii_letters + string.digits + "_-")
    return all(c in allowed_chars for c in session_id)


def validate_starting_intensity(value: str) -> Optional[int]:
    """Validate starting intensity input.

    Ensures value is an integer between 1 and 255 (inclusive).
    0 is reserved for goggle shutdown only.

    Args:
        value: String input to validate

    Returns:
        Integer value if valid, None if invalid
    """
    try:
        intensity = int(value)
        if 1 <= intensity <= 255:
            return intensity
        return None
    except ValueError:
        return None


def read_metadata(meta_path: Path) -> dict[str, str]:
    """Read metadata from .meta file.

    Args:
        meta_path: Path to .meta file

    Returns:
        Dictionary of metadata key-value pairs

    Raises:
        IOError: If file cannot be read
        FileNotFoundError: If file does not exist
    """
    metadata = {}

    with open(meta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                metadata[key.strip()] = value.strip()

    return metadata


def generate_staircase_filename(
    data_dir: Path,
    participant_id: str,
    session_id: str,
    timestamp: str
) -> Path:
    """Generate filename for staircase .psydat file.

    Args:
        data_dir: Directory where data files will be saved
        participant_id: Participant identifier
        session_id: Session identifier
        timestamp: Timestamp string (format: YYYYMMDD_HHMMSS)

    Returns:
        Path to staircase file
    """
    filename = f"{participant_id}_{session_id}_{timestamp}_staircase.psydat"
    return Path(data_dir) / filename