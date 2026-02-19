"""Configuration module for loading and validating ts-status settings."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Config:
    """Configuration for Tailscale status stats collection."""

    interval: int
    base_location: Path
    file_name_format: str = "tailscale-status-{date}.parquet"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.interval <= 0:
            raise ValueError("interval must be greater than 0")

        # Create base_location if it doesn't exist
        self.base_location = Path(self.base_location)
        self.base_location.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from the parameter passed in or default to 
    `~/.config/ts-status.yml`.

    Args:
        config_path: Path to the configuration file

    Returns:
        Config: Configuration object with settings

    Raises:
        FileNotFoundError: If config file is not found
        ValueError: If configuration is invalid
    """

    if config_path:
        config_path = Path(config_path)
    else:
        config_path = Path.home() / ".config" / "ts-status.yml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Please create it with 'interval', 'base_location', and optionally 'file_name_format'."
        )

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    if config_dict is None:
        raise ValueError("Configuration file is empty")

    # Validate required fields
    required_fields = ["interval", "base_location"]
    missing_fields = [field for field in required_fields if field not in config_dict]

    if missing_fields:
        raise ValueError(
            f"Configuration is missing required fields: {', '.join(missing_fields)}"
        )

    # Extract configuration with defaults
    interval = config_dict["interval"]
    base_location = config_dict["base_location"]
    file_name_format = config_dict.get(
        "file_name_format", "tailscale-status-{date}.parquet"
    )

    return Config(
        interval=interval,
        base_location=base_location,
        file_name_format=file_name_format,
    )
