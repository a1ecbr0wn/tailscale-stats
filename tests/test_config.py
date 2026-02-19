"""Tests for the configuration module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ts_status_stats.config import Config, load_config


class TestConfig:
    """Tests for the Config dataclass."""

    def test_config_initialization(self):
        """Test Config initialization with valid values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                interval=60,
                base_location=tmpdir,
                file_name_format="tailscale-status-{date}.parquet",
            )
            assert config.interval == 60
            assert config.base_location == Path(tmpdir)
            assert config.file_name_format == "tailscale-status-{date}.parquet"

    def test_config_default_file_name_format(self):
        """Test Config uses default file_name_format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                interval=60,
                base_location=tmpdir,
            )
            assert config.file_name_format == "tailscale-status-{date}.parquet"

    def test_config_invalid_interval(self):
        """Test Config raises error for invalid interval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="interval must be greater than 0"):
                Config(interval=0, base_location=tmpdir)

            with pytest.raises(ValueError, match="interval must be greater than 0"):
                Config(interval=-1, base_location=tmpdir)

    def test_config_creates_base_location(self):
        """Test Config creates base_location if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            assert not new_dir.exists()

            config = Config(interval=60, base_location=str(new_dir))

            assert new_dir.exists()
            assert new_dir.is_dir()


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_success(self):
        """Test successfully loading a valid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ts-status.yml"
            config_data = {
                "interval": 60,
                "base_location": tmpdir,
                "file_name_format": "custom-{date}.parquet",
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with patch("ts_status_stats.config.Path.home", return_value=Path(tmpdir)):
                config = load_config()

            assert config.interval == 60
            assert config.base_location == Path(tmpdir)
            assert config.file_name_format == "custom-{date}.parquet"

    def test_load_config_missing_file(self):
        """Test load_config raises error when config file is missing."""
        with patch(
            "ts_status_stats.config.Path.home", return_value=Path("/nonexistent")
        ):
            with pytest.raises(FileNotFoundError, match="Configuration file not found"):
                load_config()

    def test_load_config_empty_file(self):
        """Test load_config raises error for empty config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ts-status.yml"
            config_path.write_text("")

            with patch("ts_status_stats.config.Path.home", return_value=Path(tmpdir)):
                with pytest.raises(ValueError, match="Configuration file is empty"):
                    load_config()

    def test_load_config_missing_required_fields(self):
        """Test load_config raises error for missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ts-status.yml"

            # Missing base_location
            config_data = {"interval": 60}
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with patch("ts_status_stats.config.Path.home", return_value=Path(tmpdir)):
                with pytest.raises(
                    ValueError, match="Configuration is missing required fields"
                ):
                    load_config()

    def test_load_config_default_file_name_format(self):
        """Test load_config uses default file_name_format when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ts-status.yml"
            config_data = {
                "interval": 60,
                "base_location": tmpdir,
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            with patch("ts_status_stats.config.Path.home", return_value=Path(tmpdir)):
                config = load_config()

            assert config.file_name_format == "tailscale-status-{date}.parquet"
