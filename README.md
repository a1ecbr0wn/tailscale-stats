# Tailscale Status Stats

A Python application that periodically collects Tailscale status statistics and
stores them in Parquet files for analysis.

## Features

- **Periodic Collection**: Configurable interval-based collection of Tailscale status
- **Parquet Storage**: Efficient columnar storage format with Apache Arrow
- **Organized File Structure**: Automatic date-based directory organization (`YYYY/MM/`)
- **Append Support**: Automatically appends records to existing daily files
- **Error Handling**: Graceful error handling and comprehensive logging
- **Configuration**: YAML-based configuration for flexibility

## Requirements

- Python 3.10 or higher
- Tailscale CLI tool installed and accessible
- pandas >= 1.5.0
- pyarrow >= 10.0.0
- pyyaml >= 6.0

## Installation

### From Source

- Clone or download the repository:

```bash
cd tailscale-stats
```

- Install in development mode:

```bash
pip install -e .
```

Or install with test dependencies:

```bash
pip install -e ".[dev]"
```

## Configuration

Create a configuration file at `~/.config/ts-status.yml` with the following structure:

```yaml
interval: 60 # Collection interval in seconds (required)
base_location: /path/to/storage # Base directory for Parquet files (required)
file_name_format: "tailscale-status-{date}.parquet" # Optional, defaults to this value
```

### Configuration Options

| Option             | Type    | Required | Default                           | Description                                                                           |
| ------------------ | ------- | -------- | --------------------------------- | ------------------------------------------------------------------------------------- |
| `interval`         | integer | Yes      | N/A                               | Collection interval in seconds (must be > 0)                                          |
| `base_location`    | string  | Yes      | N/A                               | Base directory for storing Parquet files. Will be created if it doesn't exist.        |
| `file_name_format` | string  | No       | `tailscale-status-{date}.parquet` | Format string for Parquet file names. Use `{date}` placeholder for `YYYYMMDD` format. |

### Example Configuration

```yaml
interval: 60
base_location: ~/tailscale-stats
file_name_format: "tailscale-status-{date}.parquet"
```

## Usage

### Running the Application

Start the Tailscale status collector:

```bash
python -m ts_status_stats.main
```

Or if installed as a console script:

```bash
ts-status-stats
```

### Output Structure

Statistics are stored in the following directory structure:

```
<base_location>/
├── 2024/
│   ├── 01/
│   │   ├── tailscale-status-20240101.parquet
│   │   ├── tailscale-status-20240102.parquet
│   │   └── ...
│   ├── 02/
│   │   └── ...
│   └── ...
├── 2025/
│   └── ...
```

Each Parquet file contains multiple records (rows) for that day, with one record
per collection interval.

### Data Format

Each record in the Parquet files contains flattened Tailscale status data with the
following columns:

- `_timestamp`: ISO format timestamp of when the data was collected
- `Version`: Tailscale version
- `TUN`: Boolean indicating if TUN is enabled
- `BackendState`: Current backend state
- `Self_*`: Flattened self/local node information
  - `Self_ID`: Node ID
  - `Self_HostName`: Hostname
  - `Self_RxBytes`: Received bytes
  - `Self_TxBytes`: Transmitted bytes
  - And many more...
- `Peer_*`: Flattened peer information for each peer node
- And other top-level fields from `tailscale status --json`

Nested structures are flattened using underscore separators (e.g.,
`Self_AllowedIPs_0`, `Self_AllowedIPs_1`).

## Development

### Running Tests

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests with pytest:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src/ts_status_stats tests/
```

### Project Structure

```text
tailscale-stats/
├── src/ts_status_stats/
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Entry point
│   ├── config.py           # Configuration loading
│   └── collector.py        # Status collection and storage
├── tests/
│   ├── test_main.py
│   ├── test_config.py
│   └── test_collector.py
├── example/
│   └── example_stats.json  # Example Tailscale status output
├── setup.py                # Package setup configuration
├── README.md              # This file
└── REQUIREMENTS.md        # Original requirements
```

### Code Overview

#### `config.py`

- `Config`: Dataclass for configuration management
- `load_config()`: Loads configuration from `~/.config/ts-status.yml`

#### `collector.py`

- `TailscaleCollector`: Main class for collecting and storing status data
  - `collect_status()`: Executes `tailscale status --json` command
  - `save_status()`: Stores data to Parquet file with automatic appending
  - `_flatten_dict()`: Flattens nested structures for tabular storage
  - `_prepare_record()`: Prepares records with timestamp

#### `main.py`

- `main()`: Entry point with configuration loading and collection loop

## Logging

The application outputs logs to stdout with the following format:

```text
YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE
```

Example output:

```text
2024-01-15 10:30:45 - INFO - Loading configuration...
2024-01-15 10:30:45 - INFO - Configuration loaded: interval=60s, base_location=/path/to/stats
2024-01-15 10:30:45 - INFO - Starting Tailscale status collection...
2024-01-15 10:30:46 - INFO - Status saved to /path/to/stats/2024/01/tailscale-status-20240115.parquet
```

## Error Handling

The application handles various error scenarios:

- **Configuration File Not Found**: Exits with code 1 and helpful message
- **Invalid Configuration**: Validates all required fields and types
- **Tailscale Command Not Found**: Indicates Tailscale is not installed
- **JSON Parse Errors**: Logs error if Tailscale output is malformed
- **Collection Errors**: Logs error and continues with next collection cycle
- **Keyboard Interrupt**: Gracefully shuts down on Ctrl+C

## Troubleshooting

### "Configuration file not found"

Make sure you've created `~/.config/ts-status.yml` with the required fields:

```bash
mkdir -p ~/.config
cat > ~/.config/ts-status.yml << EOF
interval: 60
base_location: ~/tailscale-stats
EOF
```

### "tailscale command not found"

Ensure Tailscale is installed and the `tailscale` command is in your PATH:

```bash
which tailscale
```

### "'tailscale status --json' requires elevated privileges"

You may need to run the application with `sudo` or configure your system to allow
the command without a password.

### No files being created

Check that:

1. The `base_location` directory is writable
2. The `interval` value is reasonable (not too small)
3. Check the logs for any error messages
4. Verify `tailscale status --json` works manually

## Performance Considerations

- **Storage Size**: Each record is typically 5-50 KB depending on the number of peers
- **Collection Overhead**: The `tailscale status --json` command typically completes in < 100ms
- **Recommended Interval**: 60-300 seconds depending on your monitoring needs

## Examples

### Analyzing Data with Python

```python
import pandas as pd

# Read a single day's data
df = pd.read_parquet('/path/to/stats/2024/01/tailscale-status-20240115.parquet')

# Get all records
print(df.head())

# Analyze RX/TX bytes over time
print(df[['_timestamp', 'Self_RxBytes', 'Self_TxBytes']])

# Find when the device was online
print(df[['_timestamp', 'Self_Online']])
```

### Combining Multiple Days

```python
import pandas as pd
from pathlib import Path

# Read all Parquet files from a month
stats_dir = Path('/path/to/stats/2024/01')
files = sorted(stats_dir.glob('*.parquet'))

dfs = [pd.read_parquet(f) for f in files]
combined_df = pd.concat(dfs, ignore_index=True)

print(combined_df.describe())
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines if applicable]
