"""Safety-critical goggles controller for light stimulation.

This module provides a context-managed interface to light goggles via serial port.
Safety is paramount: the goggles MUST return to brightness 0 on ANY exit path
(normal exit, exceptions, keyboard interrupt, crashes).
"""

import atexit
import logging
import signal
import sys
from typing import Optional

import serial


class GoggleError(Exception):
    """Raised when there is an error controlling the goggles."""
    pass


class GoggleController:
    """Context-managed controller for light goggles via serial port.

    This class ensures that goggles are always turned off (brightness = 0)
    when the program exits, even in the case of crashes or interruptions.

    The goggles are controlled by sending LF-delimited numeric strings
    (0-255) via serial port.

    Example:
        >>> config = load_config()
        >>> with GoggleController(config) as goggles:
        ...     goggles.set_brightness(128)  # Set to half brightness
        ...     # Goggles automatically turn off when exiting context
    """

    # Class variable to track the active instance for emergency shutdown
    _active_instance: Optional['GoggleController'] = None

    def __init__(
        self,
        port: str,
        baud_rate: int = 9600,
        brightness_min: int = 0,
        brightness_max: int = 255,
        timeout: float = 1.0
    ):
        """Initialize goggles controller.

        Args:
            port: Serial port path (e.g., '/dev/tty.usbserial-0001' on Mac,
                'COM3' on Windows)
            baud_rate: Serial port baud rate (default: 9600)
            brightness_min: Minimum allowed brightness level (0-255)
            brightness_max: Maximum allowed brightness level (0-255)
            timeout: Serial port timeout in seconds (default: 1.0)

        Raises:
            GoggleError: If port cannot be opened or parameters are invalid
        """
        # Validate parameters
        if brightness_min < 0 or brightness_min > 255:
            raise GoggleError(f"brightness_min must be 0-255, got {brightness_min}")
        if brightness_max < 0 or brightness_max > 255:
            raise GoggleError(f"brightness_max must be 0-255, got {brightness_max}")
        if brightness_min >= brightness_max:
            raise GoggleError("brightness_min must be less than brightness_max")

        self.port_name = port
        self.baud_rate = baud_rate
        self.brightness_min = brightness_min
        self.brightness_max = brightness_max
        self.timeout = timeout

        self._serial: Optional[serial.Serial] = None
        self._current_brightness: int = 0
        self._is_open: bool = False

        # Register emergency shutdown handlers
        self._register_shutdown_handlers()

        logging.info(
            f"Initializing GoggleController on {port} at {baud_rate} baud "
            f"(range: {brightness_min}-{brightness_max})"
        )

    def _register_shutdown_handlers(self) -> None:
        """Register handlers to ensure goggles turn off on any exit."""
        # Register this instance for emergency shutdown
        GoggleController._active_instance = self

        # Register atexit handler
        atexit.register(self._emergency_shutdown)

        # Register signal handlers for clean shutdown
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle interrupt signals by turning off goggles and exiting.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logging.warning(f"Received {signal_name}, shutting down goggles...")
        self._emergency_shutdown()
        sys.exit(1)

    @classmethod
    def _emergency_shutdown(cls) -> None:
        """Emergency shutdown: turn off goggles immediately.

        This is called by atexit and signal handlers to ensure goggles
        are turned off even if the program crashes.
        """
        if cls._active_instance is not None:
            try:
                cls._active_instance._force_brightness_zero()
            except Exception as e:
                # In emergency shutdown, log but don't raise
                logging.error(f"Error during emergency shutdown: {e}")

    def open(self) -> None:
        """Open serial port connection to goggles.

        Raises:
            GoggleError: If port cannot be opened
        """
        if self._is_open:
            logging.warning("Serial port already open")
            return

        try:
            self._serial = serial.Serial(
                port=self.port_name,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            self._is_open = True
            logging.info(f"Opened serial port {self.port_name}")

            # Ensure goggles start at brightness 0
            self.set_brightness(0)

        except serial.SerialException as e:
            raise GoggleError(f"Failed to open serial port {self.port_name}: {e}")

    def close(self) -> None:
        """Close serial port connection, ensuring goggles are off."""
        if not self._is_open:
            return

        try:
            # CRITICAL: Turn off goggles before closing
            self._force_brightness_zero()

            if self._serial is not None:
                self._serial.close()
                logging.info(f"Closed serial port {self.port_name}")
        except Exception as e:
            logging.error(f"Error closing serial port: {e}")
        finally:
            self._is_open = False
            self._serial = None

    def _force_brightness_zero(self) -> None:
        """Force goggles to brightness 0 without validation checks.

        This is used during shutdown to ensure goggles turn off
        even if other errors occur.
        """
        if self._serial is not None and self._serial.is_open:
            try:
                self._write_brightness(0)
                self._current_brightness = 0
                logging.info("Goggles set to brightness 0 (off)")
            except Exception as e:
                logging.error(f"Failed to turn off goggles: {e}")

    def _write_brightness(self, level: int) -> None:
        """Write brightness level to serial port.

        Sends LF-delimited numeric string to goggles controller.

        Args:
            level: Brightness level (0-255)

        Raises:
            GoggleError: If write fails
        """
        if self._serial is None or not self._serial.is_open:
            raise GoggleError("Serial port not open")

        try:
            # Protocol: send numeric value as string followed by LF
            message = f"{level}\n"
            self._serial.write(message.encode('ascii'))
            self._serial.flush()  # Ensure data is sent immediately
            logging.debug(f"Sent brightness command: {level}")
        except serial.SerialException as e:
            raise GoggleError(f"Failed to write to serial port: {e}")

    def set_brightness(self, level: int) -> None:
        """Set goggles to specified brightness level.

        Args:
            level: Brightness level (0-255, constrained by min/max settings)

        Raises:
            GoggleError: If level is invalid or write fails
        """
        if not self._is_open:
            raise GoggleError("Cannot set brightness: serial port not open")

        # Validate level
        if level < 0 or level > 255:
            raise GoggleError(f"Brightness level must be 0-255, got {level}")

        # Constrain to configured range
        if level < self.brightness_min:
            logging.warning(
                f"Requested brightness {level} below minimum {self.brightness_min}, "
                f"clamping to minimum"
            )
            level = self.brightness_min
        if level > self.brightness_max:
            logging.warning(
                f"Requested brightness {level} above maximum {self.brightness_max}, "
                f"clamping to maximum"
            )
            level = self.brightness_max

        # Send command
        self._write_brightness(level)
        self._current_brightness = level
        logging.info(f"Goggles brightness set to {level}")

    def get_brightness(self) -> int:
        """Get current brightness level.

        Returns:
            Current brightness level (0-255)
        """
        return self._current_brightness

    def is_open(self) -> bool:
        """Check if serial port is open.

        Returns:
            True if serial port is open, False otherwise
        """
        return self._is_open

    def __enter__(self) -> 'GoggleController':
        """Enter context manager: open serial port.

        Returns:
            Self for use in with statement
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager: ensure goggles are off and close port.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        if exc_type is not None:
            logging.error(
                f"Exception in goggles context: {exc_type.__name__}: {exc_val}"
            )

        # Always close (which turns off goggles)
        self.close()


def create_goggles_from_config(config: dict) -> GoggleController:
    """Create a GoggleController from a configuration dictionary.

    Args:
        config: Configuration dictionary containing 'hardware' section

    Returns:
        Configured GoggleController instance

    Raises:
        GoggleError: If configuration is invalid
    """
    hw = config.get("hardware", {})

    return GoggleController(
        port=hw["serial_port"],
        baud_rate=hw["baud_rate"],
        brightness_min=hw["brightness_min"],
        brightness_max=hw["brightness_max"],
        timeout=hw.get("serial_timeout", 1.0)
    )