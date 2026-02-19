# Quick Start Guide

## 5-Minute Setup

### 1. Install the Package

```bash
cd tailscale-stats
pip install -e .
```

### 2. Create Configuration File

```bash
mkdir -p ~/.config
cat > ~/.config/ts-status.yml << 'EOF'
interval: 60
base_location: ~/tailscale-stats-data
EOF
```

### 3. Run the Collector

```bash
ts-status-stats
```

You should see output like:

```text
2024-01-15 10:30:45 - INFO - Loading configuration...
2024-01-15 10:30:45 - INFO - Configuration loaded: interval=60s, base_location=/Users/username/tailscale-stats-data
2024-01-15 10:30:45 - INFO - Starting Tailscale status collection...
2024-01-15 10:30:46 - INFO - Status saved to /Users/username/tailscale-stats-data/2024/01/tailscale-status-20240115.parquet
```

### 4. Stop the Collector

Press `Ctrl+C` to stop gracefully.

## Accessing Your Data

### Using Python/pandas

```python
import pandas as pd
from pathlib import Path

# Read today's data
df = pd.read_parquet(Path.home() / 'tailscale-stats-data/2024/01/tailscale-status-20240115.parquet')

# View first few records
print(df.head())

# View columns
print(df.columns.tolist())

# Check network statistics
print(df[['_timestamp', 'Self_RxBytes', 'Self_TxBytes', 'Self_Online']])
```

### Using Command Line

```bash
# List stored files
ls -la ~/tailscale-stats-data/2024/01/

# Check file size
du -h ~/tailscale-stats-data/2024/01/tailscale-status-20240115.parquet

# Show file modification time
stat ~/tailscale-stats-data/2024/01/tailscale-status-20240115.parquet
```

## Configuration Options

### Faster Collection (Every 30 seconds)

```yaml
interval: 30
base_location: ~/tailscale-stats-data
```

### Slower Collection (Every 5 minutes)

```yaml
interval: 300
base_location: ~/tailscale-stats-data
```

### Custom Storage Location

```yaml
interval: 60
base_location: /var/lib/tailscale-stats
```

### Custom Filename Format

```yaml
interval: 60
base_location: ~/tailscale-stats-data
file_name_format: ts-{date}.parquet
```

## Running as a Background Service

### Using nohup

```bash
nohup ts-status-stats > ~/.ts-status.log 2>&1 &
```

### Using screen

```bash
screen -S tailscale-stats -d -m ts-status-stats
screen -ls
screen -r tailscale-stats
```

### Using tmux

```bash
tmux new-session -d -s tailscale-stats ts-status-stats
tmux list-sessions
tmux attach -t tailscale-stats
```

## Troubleshooting

### "Configuration file not found"

Make sure you created the config file:

```bash
cat ~/.config/ts-status.yml
```

### "tailscale command not found"

Install or update Tailscale:

```bash
# macOS
brew install tailscale

# Linux
# Follow https://tailscale.com/download/linux

# Check installation
tailscale version
```

### "Permission denied" errors

Ensure the base directory is writable:

```bash
mkdir -p ~/tailscale-stats-data
chmod 755 ~/tailscale-stats-data
```

### No Parquet files being created

Check the logs for errors:

```bash
# If running in background
tail -f ~/.ts-status.log

# Run in foreground to see errors
ts-status-stats
```

## Common Tasks

### View Data from Specific Day

```python
import pandas as pd
from datetime import datetime

# Read data from January 15, 2024
df = pd.read_parquet('~/tailscale-stats-data/2024/01/tailscale-status-20240115.parquet')
print(f"Records: {len(df)}")
print(f"Date range: {df['_timestamp'].min()} to {df['_timestamp'].max()}")
```

### Combine Multiple Days

```python
import pandas as pd
from pathlib import Path

# Read all files from January 2024
files = sorted(Path('~/tailscale-stats-data/2024/01').expanduser().glob('*.parquet'))
dfs = [pd.read_parquet(f) for f in files]
combined_df = pd.concat(dfs, ignore_index=True)

print(f"Total records: {len(combined_df)}")
print(combined_df.describe())
```

### Analyze Network Traffic

```python
import pandas as pd

df = pd.read_parquet('~/tailscale-stats-data/2024/01/tailscale-status-20240115.parquet')

# Get RX/TX statistics
print("Network Statistics:")
print(f"Max RxBytes: {df['Self_RxBytes'].max()}")
print(f"Max TxBytes: {df['Self_TxBytes'].max()}")
print(f"Total RxBytes: {df['Self_RxBytes'].sum()}")
print(f"Total TxBytes: {df['Self_TxBytes'].sum()}")

# Show periods when offline
offline = df[~df['Self_Online']]
if len(offline) > 0:
    print(f"\nOffline periods: {len(offline)} records")
    print(offline[['_timestamp', 'Self_Online']])
```

### Export to CSV

```python
import pandas as pd

df = pd.read_parquet('~/tailscale-stats-data/2024/01/tailscale-status-20240115.parquet')
df.to_csv('tailscale-status-2024-01-15.csv', index=False)
```

## Next Steps

1. **Read the full README**: `cat README.md`
2. **Check the development guide**: `cat DEVELOPMENT.md`
3. **Run the tests**: `pytest -v`
4. **Explore the example data**: `cat example/example_stats.json | jq`

## Getting Help

- Check the **README.md** for detailed documentation
- Check the **DEVELOPMENT.md** for architecture details
- Run tests to verify installation: `pytest`
- Check configuration syntax: `python -c "from ts_status_stats.config import
load_config; print(load_config())"`

## Stopping and Restarting

### Stop Collection

```bash
# If in foreground: Ctrl+C

# If in background (nohup)
pkill -f ts-status-stats

# If in screen
screen -X -S tailscale-stats quit

# If in tmux
tmux kill-session -t tailscale-stats
```

### Restart Collection

```bash
ts-status-stats
```

## Performance Notes

- Each collection takes ~100-200ms
- Default interval (60s) uses minimal system resources
- Storage: ~50-100 MB per month for typical setups
- Recommended intervals: 60-300 seconds

Enjoy collecting Tailscale stats! 🎉
