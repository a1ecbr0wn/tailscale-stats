"""Tests for the Tailscale collector module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ts_status_stats.collector import TailscaleCollector


@pytest.fixture
def temp_base_location():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_status_data():
    """Provide sample Tailscale status data."""
    return {
        "Version": "1.54.0",
        "BackendState": "Running",
        "TailscaleIPs": ["100.64.0.1"],
        "Self": {
            "ID": 1,
            "HostName": "test-host",
            "OS": "darwin",
            "RxBytes": 1024,
            "TxBytes": 2048,
            "Online": True,
        },
        "Peer": {
            "peer1": {
                "ID": 2,
                "HostName": "peer-host",
                "OS": "linux",
                "RxBytes": 5120,
                "TxBytes": 10240,
                "Online": True,
            }
        },
    }


def test_collector_init(temp_base_location):
    """Test collector initialization."""
    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )
    assert collector.base_location == temp_base_location
    assert collector.file_name_format == "tailscale-status-{date}.parquet"


def test_flatten_dict(temp_base_location):
    """Test dictionary flattening."""
    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    nested_dict = {
        "level1": {"level2": {"level3": "value"}, "another": "data"},
        "simple": "value",
    }

    flattened = collector._flatten_dict(nested_dict)

    assert flattened["level1_level2_level3"] == "value"
    assert flattened["level1_another"] == "data"
    assert flattened["simple"] == "value"


def test_flatten_dict_with_list(temp_base_location):
    """Test dictionary flattening with lists."""
    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    data_with_list = {"items": ["a", "b", "c"], "nested": {"list": [1, 2, 3]}}

    flattened = collector._flatten_dict(data_with_list)

    assert "items_0" in flattened
    assert "items_1" in flattened
    assert "items_2" in flattened
    assert flattened["items_0"] == "a"
    assert flattened["items_1"] == "b"
    assert flattened["items_2"] == "c"


def test_prepare_record(temp_base_location, sample_status_data):
    """Test record preparation."""
    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    record = collector._prepare_record(sample_status_data)

    assert "_timestamp" in record
    assert "Version" in record
    assert "BackendState" in record
    assert "Self_HostName" in record
    assert record["Self_HostName"] == "test-host"


@patch("ts_status_stats.collector.subprocess.run")
def test_collect_status_success(mock_run, temp_base_location, sample_status_data):
    """Test successful status collection."""
    mock_run.return_value = MagicMock(
        stdout=json.dumps(sample_status_data), returncode=0
    )

    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )
    result = collector.collect_status()

    assert result == sample_status_data
    mock_run.assert_called_once_with(
        ["tailscale", "status", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )


@patch("ts_status_stats.collector.subprocess.run")
def test_collect_status_command_failure(mock_run, temp_base_location):
    """Test status collection with command failure."""
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(
        1, "cmd", stderr="Error message"
    )

    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    with pytest.raises(RuntimeError, match="Failed to run 'tailscale status --json'"):
        collector.collect_status()


@patch("ts_status_stats.collector.subprocess.run")
def test_collect_status_json_error(mock_run, temp_base_location):
    """Test status collection with JSON parsing error."""
    mock_run.return_value = MagicMock(stdout="invalid json {", returncode=0)

    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    with pytest.raises(RuntimeError, match="Failed to parse Tailscale status JSON"):
        collector.collect_status()


@patch("ts_status_stats.collector.subprocess.run")
def test_collect_status_not_found(mock_run, temp_base_location):
    """Test status collection when tailscale command is not found."""
    mock_run.side_effect = FileNotFoundError()

    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    with pytest.raises(RuntimeError, match="'tailscale' command not found"):
        collector.collect_status()


@patch("ts_status_stats.collector.TailscaleCollector.collect_status")
def test_save_status_new_file(mock_collect, temp_base_location, sample_status_data):
    """Test saving status to a new parquet file."""
    mock_collect.return_value = sample_status_data

    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )
    file_path = collector.save_status(sample_status_data)

    # Check file structure
    assert file_path.exists()
    assert file_path.parent.parent.name in [
        "2024",
        "2025",
        "2026",
    ]  # Allow year flexibility
    assert file_path.parent.name.isdigit()  # Month
    assert "tailscale-status-" in file_path.name

    # Check file content
    df = pd.read_parquet(file_path)
    assert len(df) == 1
    assert "_timestamp" in df.columns
    assert "Version" in df.columns


@patch("ts_status_stats.collector.TailscaleCollector.collect_status")
def test_save_status_append_to_existing(
    mock_collect, temp_base_location, sample_status_data
):
    """Test appending status to an existing parquet file."""
    collector = TailscaleCollector(
        temp_base_location, "tailscale-status-{date}.parquet"
    )

    # Save first record
    file_path1 = collector.save_status(sample_status_data)

    # Save second record
    file_path2 = collector.save_status(sample_status_data)

    # Files should be the same
    assert file_path1 == file_path2

    # Check appended content
    df = pd.read_parquet(file_path1)
    assert len(df) == 2


def test_custom_file_name_format(temp_base_location, sample_status_data):
    """Test custom file name format."""
    custom_format = "ts-{date}-custom.parquet"
    collector = TailscaleCollector(temp_base_location, custom_format)

    file_path = collector.save_status(sample_status_data)

    assert "ts-" in file_path.name
    assert "custom" in file_path.name
    assert file_path.name.endswith(".parquet")
