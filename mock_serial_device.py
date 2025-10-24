#!/usr/bin/env python
"""Mock serial device simulator for goggle hardware.

This creates a virtual serial port that simulates the light goggle's hardware.
It receives brightness commands (0-255) and validates the protocol.

Usage:
    # Terminal 1: Start the simulator
    python mock_serial_device.py

    # Terminal 2: Run the experiment (or tests)
    python calibrate.py
"""

import logging
import os
import pty
import select
import sys
import time
from pathlib import Path


class MockGoggleDevice:
    """Simulates light goggles hardware via virtual serial port.

    Receives LF-delimited numeric strings (0-255) and validates protocol.
    Logs all commands for verification.
    """

    def __init__(self, log_file: Path = None):
        """Initialize mock device.

        Args:
            log_file: Path to log file for command history (optional)
        """
        self.current_brightness = 0
        self.command_count = 0
        self.log_file = log_file
        self.running = False
        self.master_fd = None
        self.slave_name = None

        # Command history
        self.command_history = []

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - MOCK DEVICE - %(message)s'
        )

    def create_virtual_port(self) -> str:
        """Create a virtual serial port using pty.

        Returns:
            Path to the slave end of the pty (what the experiment connects to)
        """
        # Create pseudo-terminal pair
        self.master_fd, slave_fd = pty.openpty()
        self.slave_name = os.ttyname(slave_fd)

        logging.info(f"Created virtual serial port: {self.slave_name}")
        logging.info(f"Configure experiment to use: {self.slave_name}")

        return self.slave_name

    def process_command(self, data: bytes) -> None:
        """Process received command from experiment.

        Args:
            data: Raw bytes received from serial port
        """
        try:
            # Decode and strip whitespace
            command_str = data.decode('ascii').strip()

            if not command_str:
                return

            # Parse brightness value
            try:
                brightness = int(command_str)
            except ValueError:
                logging.error(f"Invalid command (not a number): '{command_str}'")
                return

            # Validate range
            if brightness < 0 or brightness > 255:
                logging.error(f"Invalid brightness value: {brightness} (must be 0-255)")
                return

            # Update state
            old_brightness = self.current_brightness
            self.current_brightness = brightness
            self.command_count += 1

            # Log command with timestamp
            timestamp = time.time()
            self.command_history.append({
                'timestamp': timestamp,
                'command': brightness,
                'previous': old_brightness
            })

            # Display status
            status = "ON" if brightness > 0 else "OFF"
            change = brightness - old_brightness
            change_str = f"({change:+d})" if old_brightness != brightness else ""

            logging.info(
                f"Command #{self.command_count}: Brightness {old_brightness} → {brightness} {change_str} [{status}]"
            )

            # Log to file if configured
            if self.log_file:
                with open(self.log_file, 'a') as f:
                    f.write(f"{timestamp},{self.command_count},{brightness},{old_brightness}\n")

            # Simulate hardware delay (small delay to be realistic)
            time.sleep(0.001)

        except Exception as e:
            logging.error(f"Error processing command: {e}")

    def run(self) -> None:
        """Run the mock device, reading from virtual serial port."""
        if self.master_fd is None:
            raise RuntimeError("Virtual port not created. Call create_virtual_port() first.")

        self.running = True
        logging.info("Mock device running. Press Ctrl+C to stop.")
        logging.info(f"Current brightness: {self.current_brightness}")

        buffer = b''

        try:
            while self.running:
                # Check if data available (timeout 0.1s)
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)

                if ready:
                    # Read data
                    try:
                        chunk = os.read(self.master_fd, 1024)
                        if not chunk:
                            logging.warning("Serial port closed by experiment")
                            break

                        buffer += chunk

                        # Process line-delimited commands
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            self.process_command(line)

                    except OSError as e:
                        if e.errno == 5:  # EIO - Input/output error (normal on disconnect)
                            logging.info("Experiment disconnected")
                            break
                        else:
                            raise

        except KeyboardInterrupt:
            logging.info("\nStopping mock device...")

        finally:
            self.running = False
            if self.master_fd is not None:
                os.close(self.master_fd)

            # Final summary
            logging.info("="*60)
            logging.info("MOCK DEVICE SUMMARY")
            logging.info("="*60)
            logging.info(f"Total commands received: {self.command_count}")
            logging.info(f"Final brightness: {self.current_brightness}")

            if self.current_brightness == 0:
                logging.info("✓ Goggles properly turned OFF")
            else:
                logging.warning(f"✗ WARNING: Goggles left ON at brightness {self.current_brightness}!")

            # Show command statistics
            if self.command_history:
                brightness_values = [cmd['command'] for cmd in self.command_history]
                logging.info(f"Brightness range: {min(brightness_values)} - {max(brightness_values)}")
                logging.info(f"Commands to turn OFF: {brightness_values.count(0)}")
                logging.info(f"Commands to turn ON: {sum(1 for b in brightness_values if b > 0)}")

    def get_summary(self) -> dict:
        """Get summary of device activity.

        Returns:
            Dictionary with summary statistics
        """
        return {
            'command_count': self.command_count,
            'current_brightness': self.current_brightness,
            'command_history': self.command_history.copy(),
            'final_state_safe': self.current_brightness == 0
        }


def create_symlink(actual_port: str, friendly_name: str = "/tmp/mock_goggles") -> None:
    """Create a symlink with a friendly name to the virtual port.

    Args:
        actual_port: Actual pty device path (e.g., /dev/ttys001)
        friendly_name: Friendly symlink name (default: /tmp/mock_goggles)
    """
    try:
        # Remove old symlink if exists
        if os.path.exists(friendly_name):
            os.remove(friendly_name)

        # Create new symlink
        os.symlink(actual_port, friendly_name)
        logging.info(f"Created symlink: {friendly_name} -> {actual_port}")
        logging.info(f"You can use either path in your config")
    except Exception as e:
        logging.warning(f"Could not create symlink: {e}")


def main():
    """Main entry point for mock device simulator."""
    print("="*60)
    print("MOCK GOGGLES SERIAL DEVICE SIMULATOR")
    print("="*60)
    print()

    # Create log file in calibration-test-data
    log_dir = Path("calibration-test-data")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"mock_device_{int(time.time())}.log"

    # Create mock device
    device = MockGoggleDevice(log_file=log_file)

    # Create virtual port
    port_name = device.create_virtual_port()

    # Try to create friendly symlink
    create_symlink(port_name, "/tmp/mock_goggles")

    print()
    print("SETUP INSTRUCTIONS:")
    print("-" * 60)
    print(f"1. Edit your config file:")
    print(f"   ~/Documents/Calibration/config/experiment_config.json")
    print()
    print(f"2. Set 'serial_port' to one of these:")
    print(f"   \"{port_name}\"")
    print(f"   OR")
    print(f"   \"/tmp/mock_goggles\"")
    print()
    print(f"3. In another terminal, run your experiment:")
    print(f"   python calibrate.py")
    print()
    print(f"Command log: {log_file}")
    print("-" * 60)
    print()

    # Run device
    try:
        device.run()
    except Exception as e:
        logging.error(f"Device error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())