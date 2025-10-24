#!/usr/bin/env python
"""Simple integration test with mock serial device (no UI).

This test runs the core experiment logic with the mock device,
without creating a PsychoPy window.
"""

import logging
import sys
import threading
import time
from pathlib import Path

import mock_serial_device


def test_goggles_with_mock_device():
    """Test goggles communication with mock device."""
    print("\n" + "="*60)
    print("SIMPLE INTEGRATION TEST: Goggles + Mock Device")
    print("="*60)

    import config
    import goggles

    # Create mock device
    device = mock_serial_device.MockGoggleDevice()
    port_name = device.create_virtual_port()

    print(f"\n✓ Created mock device at {port_name}")

    # Start device in background thread
    device_thread = threading.Thread(target=device.run, daemon=True)
    device_thread.start()

    time.sleep(0.2)  # Give device time to start

    try:
        # Load config and override serial port
        cfg = config.load_config()
        cfg["hardware"]["serial_port"] = port_name

        print("✓ Loaded config")

        # Create and test goggles controller
        gc = goggles.create_goggles_from_config(cfg)
        print("✓ Created goggles controller")

        # Open and run test sequence
        with gc:
            print("✓ Opened connection to mock device")
            print("\nRunning test sequence...")

            # Test sequence simulating typical trial
            test_levels = [128, 0, 160, 0, 192, 0, 224, 0, 255, 0]

            for i, level in enumerate(test_levels, 1):
                gc.set_brightness(level)
                time.sleep(0.05)
                status = "ON" if level > 0 else "OFF"
                print(f"  Step {i}/10: Set brightness to {level} [{status}]")

            print("\n✓ Test sequence completed")

        print("✓ Goggles controller closed")

        # Stop device and get summary
        device.running = False
        time.sleep(0.1)
        device_summary = device.get_summary()

        print("\n" + "-"*60)
        print("Mock Device Summary:")
        print(f"  Commands received: {device_summary['command_count']}")
        print(f"  Final brightness: {device_summary['current_brightness']}")
        print(f"  Safe shutdown: {'✓ YES' if device_summary['final_state_safe'] else '✗ NO'}")
        print("-"*60)

        # Validation
        success = True
        errors = []

        if device_summary['command_count'] == 0:
            success = False
            errors.append("Device received no commands")

        if not device_summary['final_state_safe']:
            success = False
            errors.append(f"Device not safely shut down (brightness={device_summary['current_brightness']})")

        # Should have received all commands plus initial brightness=0
        expected_commands = len(test_levels) + 1  # +1 for initial set to 0
        if device_summary['command_count'] < expected_commands:
            success = False
            errors.append(f"Expected at least {expected_commands} commands, got {device_summary['command_count']}")

        if success:
            print("\n✓ ALL TESTS PASSED")
            return True
        else:
            print("\n✗ TEST FAILURES:")
            for error in errors:
                print(f"  - {error}")
            return False

    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        logging.error(f"Integration test error: {e}", exc_info=True)
        return False

    finally:
        device.running = False


def main():
    """Main entry point."""
    print("="*60)
    print("SIMPLE INTEGRATION TEST SUITE")
    print("="*60)

    success = test_goggles_with_mock_device()

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    if success:
        print("✓ PASS: Goggles + Mock Device")
        print("\n✓ All tests passed!")
        return 0
    else:
        print("✗ FAIL: Goggles + Mock Device")
        print("\n✗ Test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())