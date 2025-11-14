"""Configuration management

This module provides configuration loading and validation.
To be implemented across phases.
"""
import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Validation will be added in Phase 1
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, False otherwise

    To be implemented in Phase 1
    """
    # Placeholder - will implement validation logic
    return True


__all__ = ["load_config", "validate_config"]
