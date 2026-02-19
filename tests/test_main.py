"""Tests for the main entry point."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ts_status_stats.main import main


class TestMain(unittest.TestCase):
    """Test cases for main function."""

    @patch("ts_status_stats.main.load_config")
    def test_main_config_not_found(self, mock_load_config):
        """Test main when config file is not found."""
        mock_load_config.side_effect = FileNotFoundError("Config not found")

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)

    @patch("ts_status_stats.main.load_config")
    def test_main_config_invalid(self, mock_load_config):
        """Test main when config is invalid."""
        mock_load_config.side_effect = ValueError("Invalid config")

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)

    @patch("ts_status_stats.main.time.sleep")
    @patch("ts_status_stats.main.TailscaleCollector")
    @patch("ts_status_stats.main.load_config")
    def test_main_keyboard_interrupt(
        self, mock_load_config, mock_collector_class, mock_sleep
    ):
        """Test main handles keyboard interrupt gracefully."""
        # Setup config
        mock_config = MagicMock()
        mock_config.interval = 60
        mock_config.base_location = Path("/tmp")
        mock_config.file_name_format = "tailscale-status-{date}.parquet"
        mock_load_config.return_value = mock_config

        # Setup collector to raise KeyboardInterrupt on first collection
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect_status.side_effect = KeyboardInterrupt()

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
