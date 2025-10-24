#!/usr/bin/env python
"""Test script for goggle calibration experiment.

This script tests the experiment components without requiring actual
hardware. It uses mock objects for the serial port connection.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def test_config():
    """Test configuration loading and validation."""
    print("\n=== Testing Configuration System ===")

    import config

    try:
        # Load config (will create default if missing)
        cfg = config.load_config()
        print("✓ Configuration loaded successfully")

        # Validate structure
        assert "hardware" in cfg
        assert "staircase" in cfg
        assert "timing" in cfg
        assert "paths" in cfg
        print("✓ Configuration has all required sections")

        # Check paths expansion
        paths = config.get_expanded_paths(cfg)
        assert all(isinstance(p, Path) for p in paths.values())
        print("✓ Path expansion works correctly")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_data_logger():
    """Test data logging system."""
    print("\n=== Testing Data Logger ===")

    import data_logger

    try:
        # Create test data directory
        test_dir = Path("calibration-test-data")
        test_dir.mkdir(exist_ok=True)

        # Create logger
        logger = data_logger.DataLogger(
            data_dir=test_dir,
            participant_id="TEST001",
            session_id="S01",
            auto_flush=True
        )
        print("✓ DataLogger created")

        # Open and write test data
        with logger:
            logger.log_trial(
                trial_number=1,
                goggle_level=128,
                uncomfortable=True,
                reversals_so_far=0
            )
            logger.log_trial(
                trial_number=2,
                goggle_level=96,
                uncomfortable=False,
                reversals_so_far=1
            )
        print("✓ Trial data logged successfully")

        # Verify file exists
        assert logger.get_filepath().exists()
        print(f"✓ CSV file created: {logger.get_filepath()}")

        return True

    except Exception as e:
        print(f"✗ Data logger test failed: {e}")
        return False


def test_staircase():
    """Test staircase procedure."""
    print("\n=== Testing Staircase ===")

    import staircase

    try:
        # Create staircase
        sc = staircase.StaircaseManager(
            start_value=128,
            step_sizes=[32, 16, 8, 4, 2, 1],
            n_up=1,
            n_down=3,
            n_trials=10,
            min_val=0,
            max_val=255
        )
        print("✓ Staircase created")

        # Run a few trials
        for i in range(5):
            level = sc.get_next_level()
            assert level is not None
            assert 0 <= level <= 255
            # Alternate responses
            sc.add_response(uncomfortable=(i % 2 == 0))

        print(f"✓ Ran 5 trials, {sc.get_reversal_count()} reversals")

        # Test threshold calculation
        if sc.get_reversal_count() > 0:
            threshold = sc.calculate_threshold()
            print(f"✓ Threshold calculation works: {threshold:.1f}")

        return True

    except Exception as e:
        print(f"✗ Staircase test failed: {e}")
        return False


def test_goggles_mock():
    """Test goggles controller with mocked serial port."""
    print("\n=== Testing Goggles Controller (Mocked) ===")

    import goggles

    try:
        # Mock serial.Serial
        with patch('serial.Serial') as mock_serial:
            # Setup mock
            mock_port = MagicMock()
            mock_serial.return_value = mock_port
            mock_port.is_open = True

            # Create goggles controller
            gc = goggles.GoggleController(
                port="/dev/tty.test",
                baud_rate=9600,
                brightness_min=0,
                brightness_max=255
            )
            print("✓ GoggleController created")

            # Open and test
            with gc:
                gc.set_brightness(128)
                assert gc.get_brightness() == 128
                print("✓ Set brightness to 128")

                gc.set_brightness(0)
                assert gc.get_brightness() == 0
                print("✓ Set brightness to 0")

            print("✓ Context manager cleanup works")

        return True

    except Exception as e:
        print(f"✗ Goggles controller test failed: {e}")
        return False


def test_validation():
    """Test ID validation functions."""
    print("\n=== Testing Validation ===")

    import data_logger

    try:
        # Valid IDs
        assert data_logger.validate_participant_id("P001")
        assert data_logger.validate_participant_id("TEST-123_A")
        print("✓ Valid participant IDs accepted")

        # Invalid IDs
        assert not data_logger.validate_participant_id("")
        assert not data_logger.validate_participant_id("P 001")  # space
        assert not data_logger.validate_participant_id("P/001")  # slash
        print("✓ Invalid participant IDs rejected")

        # Valid session IDs
        assert data_logger.validate_session_id("S01")
        assert data_logger.validate_session_id("Session_1-A")
        print("✓ Valid session IDs accepted")

        # Invalid session IDs
        assert not data_logger.validate_session_id("")
        assert not data_logger.validate_session_id("S 01")  # space
        print("✓ Invalid session IDs rejected")

        return True

    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("GOGGLE CALIBRATION EXPERIMENT - TEST SUITE")
    print("="*60)

    tests = [
        ("Configuration", test_config),
        ("Data Logger", test_data_logger),
        ("Staircase", test_staircase),
        ("Goggles (Mocked)", test_goggles_mock),
        ("Validation", test_validation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
