# Tailscale Status Stats Requirements

- Python 3.10 or higher
- pandas

## Get ts status stats

- Every x seconds interval time, default to 60
- Call `tailscale status --json` to get stats in JSON format
  - See example output for the format: `example_stats.json`
- Store the output in Parquet files
  - Use a configured base location
  - under folder structure `<base>/yyyy/mm`
  - file name `tailscale-status-yyyymmdd.parquet`

## Configuration

- Look for a YAML configuration file in `<user-home>/.config/ts-status.yml`
- Config should contain:
  - interval time in seconds
  - base location for storing Parquet files
  - override for file name format
