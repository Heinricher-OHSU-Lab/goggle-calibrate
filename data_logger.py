"""Data logging system for goggle calibration experiment.

This module handles CSV logging of trial data and ensures data integrity
even in the case of errors or crashes. All data is written immediately
(flushed) after each trial to prevent data loss.
"""

import csv
import logging
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


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
        auto_flush: bool = True
    ):
        """Initialize data logger.

        Args:
            data_dir: Directory where data files will be saved
            participant_id: Participant identifier
            session_id: Session identifier
            auto_flush: Whether to flush after each write (default: True)
                       Setting this to True ensures data persists even on crashes

        Raises:
            IOError: If data directory cannot be created or accessed
        """
        self.data_dir = Path(data_dir)
        self.participant_id = participant_id
        self.session_id = session_id
        self.auto_flush = auto_flush

        # Generate timestamp for filename
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: {participant}_{session}_{timestamp}.csv
        filename = f"{participant_id}_{session_id}_{self.timestamp}.csv"
        self.csv_path = self.data_dir / filename

        # CSV file handle and writer
        self._csv_file: Optional[Any] = None
        self._csv_writer: Optional[csv.DictWriter] = None

        # Track whether file is open
        self._is_open = False

        # Column names for CSV (as specified in PROJECT_SPEC.md)
        self.fieldnames = [
            "trial_number",
            "goggle_level",
            "uncomfortable",
            "reversals_so_far",
            "timestamp",
            "participant_id",
            "session_id"
        ]

        logging.info(f"DataLogger initialized: {self.csv_path}")

    def open(self) -> None:
        """Open CSV file and write header.

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

        except IOError as e:
            raise IOError(f"Failed to open CSV file {self.csv_path}: {e}")

    def close(self) -> None:
        """Close CSV file."""
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
            "timestamp": trial_timestamp,
            "participant_id": self.participant_id,
            "session_id": self.session_id
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


def setup_logging(log_dir: Path, log_level: int = logging.INFO) -> None:
    """Configure Python logging system for the experiment.

    Creates both file and console handlers. File logs are saved with
    timestamp in the filename.

    Args:
        log_dir: Directory where log files will be saved
        log_level: Logging level (default: logging.INFO)
    """
    # Create log directory if it doesn't exist
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = log_dir / f"experiment_{timestamp}.log"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler: detailed logging
            logging.FileHandler(log_filename),
            # Console handler: experimenter feedback
            logging.StreamHandler()
        ]
    )

    logging.info(f"Logging initialized: {log_filename}")
    logging.info(f"Log level: {logging.getLevelName(log_level)}")


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