"""Module for collecting Tailscale status statistics."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd


class TailscaleCollector:
    """Collects Tailscale status statistics and stores them in Parquet files."""

    def __init__(self, base_location: Path, file_name_format: str):
        """
        Initialize the collector.

        Args:
            base_location: Base directory for storing Parquet files
            file_name_format: Format string for file names (e.g., "tailscale-status-{date}.parquet")
        """
        self.base_location = Path(base_location)
        self.file_name_format = file_name_format

    def collect_status(self) -> Dict[str, Any]:
        """
        Collect current Tailscale status by calling 'tailscale status --json'.

        Returns:
            Dict containing the JSON status output

        Raises:
            RuntimeError: If tailscale command fails
        """
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run 'tailscale status --json': {e.stderr}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Tailscale status JSON: {e}")
        except FileNotFoundError:
            raise RuntimeError("'tailscale' command not found. Is Tailscale installed?")

    def _flatten_dict(
        self, obj: Any, parent_key: str = "", sep: str = "_"
    ) -> Dict[str, Any]:
        """
        Flatten nested dictionaries and lists into a single level.

        Args:
            obj: Object to flatten
            parent_key: Parent key prefix
            sep: Separator for nested keys

        Returns:
            Flattened dictionary
        """
        items = {}

        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    items.update(self._flatten_dict(v, new_key, sep=sep))
                else:
                    items[new_key] = v
        elif isinstance(obj, list):
            # For lists, convert to JSON string representation
            for i, item in enumerate(obj):
                new_key = f"{parent_key}_{i}" if parent_key else str(i)
                if isinstance(item, (dict, list)):
                    items.update(self._flatten_dict(item, new_key, sep=sep))
                else:
                    items[new_key] = item
        else:
            items[parent_key] = obj

        return items

    def _prepare_record(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a status record for storage.

        Args:
            status_data: Raw Tailscale status data

        Returns:
            Prepared record with flattened structure and timestamp
        """
        record = self._flatten_dict(status_data)
        record["_timestamp"] = datetime.now().isoformat()
        return record

    def save_status(self, status_data: Dict[str, Any]) -> Path:
        """
        Save status data to a Parquet file.

        The file is stored in <base_location>/yyyy/mm/tailscale-status-yyyymmdd.parquet

        Args:
            status_data: Tailscale status data to save

        Returns:
            Path to the saved Parquet file
        """
        now = datetime.now()
        year_month_path = self.base_location / str(now.year) / f"{now.month:02d}"
        year_month_path.mkdir(parents=True, exist_ok=True)

        # Format the filename using the configured format
        date_str = now.strftime("%Y%m%d")
        filename = self.file_name_format.format(date=date_str)
        file_path = year_month_path / filename

        # Prepare the record
        record = self._prepare_record(status_data)

        # Create or append to DataFrame
        df = pd.DataFrame([record])

        # If file exists, append to it
        if file_path.exists():
            existing_df = pd.read_parquet(file_path)
            df = pd.concat([existing_df, df], ignore_index=True)

        # Save to Parquet
        df.to_parquet(file_path, index=False)

        return file_path
