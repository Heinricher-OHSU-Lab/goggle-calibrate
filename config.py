"""Configuration management for the goggle calibration experiment.

This module handles loading, validation, and auto-creation of experiment
configuration files. It ensures that all required directories exist and that
configuration values are within acceptable ranges.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

# Default configuration file location
DEFAULT_CONFIG_PATH = Path.home() / "Documents" / "Calibration" / "config" / "experiment_config.json"


class ConfigError(Exception):
    """Raised when there is an error in configuration loading or validation."""
    pass


def expand_path(path_str: str) -> Path:
    """Expand a path string with ~ and environment variables.

    Args:
        path_str: Path string that may contain ~ or environment variables

    Returns:
        Expanded Path object
    """
    return Path(os.path.expanduser(os.path.expandvars(path_str)))


def get_default_config() -> Dict[str, Any]:
    """Get the default configuration dictionary.

    Returns:
        Dictionary containing default configuration values
    """
    return {
        "hardware": {
            "serial_port": "/dev/tty.usbserial-0001",
            "baud_rate": 9600,
            "brightness_min": 0,
            "brightness_max": 255,
            "serial_timeout": 1.0
        },
        "staircase": {
            "start_value": 128,
            "step_sizes": [32, 16, 8, 4, 2, 1],
            "n_up": 1,
            "n_down": 3,
            "n_trials": 30,
            "step_type": "lin",
            "apply_initial_rule": False
        },
        "timing": {
            "pre_stimulus_delay": 6.0,
            "stimulus_duration": 2.0,
            "inter_trial_interval": 6.0,
            "response_timeout": 0
        },
        "paths": {
            "data_directory": "~/Documents/Calibration/data",
            "log_directory": "~/Documents/Calibration/logs",
            "config_directory": "~/Documents/Calibration/config"
        },
        "data": {
            "threshold_reversals": 6,
            "auto_save": True
        },
        "display": {
            "show_instructions": True,
            "show_trial_info": True,
            "fullscreen": False
        }
    }


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If configuration is invalid
    """
    # Check required top-level sections
    required_sections = ["hardware", "staircase", "timing", "paths"]
    for section in required_sections:
        if section not in config:
            raise ConfigError(f"Missing required configuration section: {section}")

    # Validate hardware settings
    hw = config["hardware"]
    if hw["brightness_min"] < 0 or hw["brightness_min"] > 255:
        raise ConfigError(f"brightness_min must be 0-255, got {hw['brightness_min']}")
    if hw["brightness_max"] < 0 or hw["brightness_max"] > 255:
        raise ConfigError(f"brightness_max must be 0-255, got {hw['brightness_max']}")
    if hw["brightness_min"] >= hw["brightness_max"]:
        raise ConfigError("brightness_min must be less than brightness_max")
    if hw["baud_rate"] <= 0:
        raise ConfigError(f"baud_rate must be positive, got {hw['baud_rate']}")

    # Validate staircase settings
    sc = config["staircase"]
    if sc["start_value"] < hw["brightness_min"] or sc["start_value"] > hw["brightness_max"]:
        raise ConfigError(
            f"start_value {sc['start_value']} outside brightness range "
            f"[{hw['brightness_min']}, {hw['brightness_max']}]"
        )
    if sc["n_up"] < 1:
        raise ConfigError(f"n_up must be >= 1, got {sc['n_up']}")
    if sc["n_down"] < 1:
        raise ConfigError(f"n_down must be >= 1, got {sc['n_down']}")
    if sc["n_trials"] < 1:
        raise ConfigError(f"n_trials must be >= 1, got {sc['n_trials']}")
    if not sc["step_sizes"]:
        raise ConfigError("step_sizes cannot be empty")
    if any(step < 1 for step in sc["step_sizes"]):
        raise ConfigError("All step_sizes must be >= 1")
    if sc["step_type"] not in ["lin", "log", "db"]:
        raise ConfigError(f"step_type must be 'lin', 'log', or 'db', got {sc['step_type']}")

    # Validate timing settings
    tm = config["timing"]
    if tm["pre_stimulus_delay"] < 0:
        raise ConfigError(f"pre_stimulus_delay must be >= 0, got {tm['pre_stimulus_delay']}")
    if tm["stimulus_duration"] <= 0:
        raise ConfigError(f"stimulus_duration must be > 0, got {tm['stimulus_duration']}")
    if tm["inter_trial_interval"] < 0:
        raise ConfigError(f"inter_trial_interval must be >= 0, got {tm['inter_trial_interval']}")

    # Validate data settings (if present)
    if "data" in config:
        data = config["data"]
        if data.get("threshold_reversals", 6) < 0:
            raise ConfigError(
                f"threshold_reversals must be >= 0, got {data['threshold_reversals']}"
            )


def create_default_config_file(config_path: Path) -> None:
    """Create a default configuration file.

    Args:
        config_path: Path where the configuration file should be created
    """
    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write default config
    default_config = get_default_config()
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)

    logging.info(f"Created default configuration file at {config_path}")


def ensure_directories(config: Dict[str, Any]) -> None:
    """Ensure that all configured directories exist.

    Args:
        config: Configuration dictionary containing path information
    """
    paths = config["paths"]
    for key, path_str in paths.items():
        path = expand_path(path_str)
        path.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Ensured directory exists: {path} ({key})")


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load and validate experiment configuration.

    If the configuration file does not exist, a default one will be created.
    All configured directories will be created if they don't exist.

    Args:
        config_path: Path to configuration file (default: ~/Documents/Calibration/config/experiment_config.json)

    Returns:
        Dictionary containing validated configuration

    Raises:
        ConfigError: If configuration is invalid or cannot be loaded
    """
    # Create default config if it doesn't exist
    if not config_path.exists():
        logging.warning(f"Configuration file not found at {config_path}")
        create_default_config_file(config_path)
        logging.info("Using default configuration")

    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in configuration file: {e}")
    except IOError as e:
        raise ConfigError(f"Error reading configuration file: {e}")

    # Validate configuration
    try:
        validate_config(config)
    except ConfigError as e:
        raise ConfigError(f"Invalid configuration: {e}")

    # Ensure all directories exist
    ensure_directories(config)

    logging.info(f"Loaded configuration from {config_path}")
    return config


def get_expanded_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """Get all paths from configuration as expanded Path objects.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary mapping path keys to expanded Path objects
    """
    return {
        key: expand_path(path_str)
        for key, path_str in config["paths"].items()
    }