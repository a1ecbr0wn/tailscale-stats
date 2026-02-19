# Development Guide

This document provides guidance for developers working on the Tailscale Status
Stats project.

## Project Overview

Tailscale Status Stats is a Python application that periodically collects Tailscale
network status and stores it in Parquet files for analysis. The project is organized
with a clear separation between the main application code and tests.

## Project Structure

```text
tailscale-stats/
├── src/ts_status_stats/          # Main package source code
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration loading and validation
│   └── collector.py              # Status collection and storage logic
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_main.py              # Tests for main entry point
│   ├── test_config.py            # Tests for configuration module
│   └── test_collector.py         # Tests for collector module
├── example/                      # Example files and documentation
│   ├── example_stats.json        # Sample Tailscale status output
│   └── ts-status.yml.example     # Example configuration file
├── setup.py                      # Package setup and dependencies
├── pytest.ini                    # Pytest configuration
├── README.md                     # User documentation
├── DEVELOPMENT.md                # This file
├── CHANGELOG.md                  # Version history
├── REQUIREMENTS.md               # Original requirements
└── .gitignore                    # Git ignore rules
```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- pip or pipenv

### Local Installation

- Clone the repository:

```bash
cd tailscale-stats
```

- Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

- Install in development mode with test dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run tests with verbose output

```bash
pytest -v
```

### Run tests with coverage report

```bash
pytest --cov=src/ts_status_stats tests/
```

### Run a specific test file

```bash
pytest tests/test_collector.py
```

### Run tests matching a pattern

```bash
pytest -k "test_flatten" -v
```

## Code Style

This project follows PEP 8 style guidelines.

### Format code with black

```bash
black src/ tests/
```

### Check code style with flake8

```bash
flake8 src/ tests/
```

### Type checking with mypy

```bash
mypy src/
```

## Module Documentation

### config.py

**Responsibilities:**

- Load YAML configuration from `~/.config/ts-status.yml`
- Validate configuration values
- Provide a `Config` dataclass for type-safe access

**Key Classes:**

- `Config`: Dataclass with `interval`, `base_location`, and `file_name_format`
  - `__post_init__()`: Validates interval > 0, creates base_location directory

**Key Functions:**

- `load_config()`: Loads and returns Config from YAML file

**Error Handling:**

- `FileNotFoundError`: Config file doesn't exist
- `ValueError`: Config is empty or missing required fields

### collector.py

**Responsibilities:**

- Execute `tailscale status --json` command
- Parse and flatten nested JSON data
- Store flattened data in Parquet files
- Manage date-based file organization

**Key Classes:**

- `TailscaleCollector`: Main collection and storage class
  - `collect_status()`: Calls tailscale CLI and returns parsed JSON
  - `save_status()`: Saves/appends status to daily Parquet file
  - `_flatten_dict()`: Converts nested structures to flat key-value pairs
  - `_prepare_record()`: Adds timestamp and calls flatten

**Data Flow:**

1. `collect_status()` executes the tailscale command
2. `_prepare_record()` flattens the JSON and adds timestamp
3. `save_status()` reads existing file (if any), appends new record, writes to disk

**File Organization:**

```text
<base_location>/
└── YYYY/
    └── MM/
        └── tailscale-status-YYYYMMDD.parquet
```

### main.py

**Responsibilities:**

- Parse command-line arguments (if any)
- Load configuration
- Initialize collector
- Implement main collection loop
- Handle errors and shutdown gracefully

**Key Functions:**

- `main()`: Entry point with:
  - Configuration loading
  - Collector initialization
  - Infinite collection loop with sleep intervals
  - Error handling for FileNotFoundError, ValueError, KeyboardInterrupt

## Testing Strategy

### Test Organization

Tests are organized by module:

- `test_config.py`: Configuration loading and validation
- `test_collector.py`: Status collection and file storage
- `test_main.py`: Main entry point and error handling

### Testing Patterns

**Configuration Tests:**

- Valid configuration loading
- Missing fields validation
- Invalid interval validation
- Directory creation

**Collector Tests:**

- Successful status collection
- Command execution mocking
- JSON parsing error handling
- Dictionary flattening with nested structures and lists
- File creation and appending
- Timestamp handling

**Main Tests:**

- Configuration error handling
- Keyboard interrupt handling

### Mocking Strategy

Use `unittest.mock` for:

- `subprocess.run()`: Mock Tailscale command execution
- `Path.home()`: Mock home directory for config loading
- `time.sleep()`: Skip sleep delays in tests

## Adding New Features

### Adding a new configuration option

1. Update `Config` dataclass in `config.py`
2. Add parsing in `load_config()`
3. Add validation in `Config.__post_init__()` if needed
4. Update tests in `test_config.py`
5. Update documentation in README.md

### Adding a new command-line argument

1. Consider if it should be in config file instead (preferred)
2. Add parsing logic to `main.py`
3. Pass to `TailscaleCollector` or other components
4. Add tests for argument handling

### Changing data storage format

1. Modify `_flatten_dict()` or `_prepare_record()` in `collector.py`
2. Consider backward compatibility
3. Update tests with new expected format
4. Update documentation with schema changes

## Debugging

### Enable debug logging

Set log level to DEBUG in `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
)
```

### Print intermediate values

Add logging statements in collector methods:

```python
logger.debug(f"Flattened record: {record}")
```

### Test with sample data

Use the example JSON from `example/example_stats.json`:

```python
with open("example/example_stats.json") as f:
    sample_data = json.load(f)
collector.save_status(sample_data)
```

## Common Issues and Solutions

### "Module not found" errors in tests

Ensure the package is installed in development mode:

```bash
pip install -e .
```

### Parquet file corruption

The pandas/pyarrow libraries handle file consistency. If issues occur:

1. Backup the data directory
2. Regenerate from source data
3. Check for sufficient disk space

### Configuration not found

Ensure config file exists at `~/.config/ts-status.yml`:

```bash
mkdir -p ~/.config
cat > ~/.config/ts-status.yml << EOF
interval: 60
base_location: ~/tailscale-stats
EOF
```

## Performance Considerations

### Collection Performance

- Each `tailscale status --json` call typically takes < 100ms
- Flattening and storage typically takes < 50ms
- Recommended minimum interval: 10 seconds
- Typical interval: 60-300 seconds

### Storage Performance

- Each status record is typically 5-50 KB (depends on peer count)
- Daily files typically contain 1,440-8,640 records (60-300s intervals)
- Daily file size: 5-400 MB depending on intervals and peer count
- Appending to existing files is efficient with pandas

### Memory Usage

- Single record flattening uses < 1 MB
- Parquet library buffers one file in memory during save
- Long-running instances: Monitor for memory leaks (typically not an issue)

## Release Process

### Version Numbering

Uses semantic versioning: MAJOR.MINOR.PATCH

- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Releasing a new version

1. Update version in `setup.py`
2. Update `CHANGELOG.md` with changes
3. Create git tag: `git tag v0.2.0`
4. Push to repository

## Dependencies

### Runtime Dependencies

- `pandas`: Data manipulation and Parquet I/O
- `pyarrow`: Parquet file format support
- `pyyaml`: YAML configuration parsing

### Development Dependencies

- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `black`: Code formatting
- `flake8`: Style checking
- `mypy`: Static type checking

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/description`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Format code: `black src/ tests/`
6. Check style: `flake8 src/ tests/`
7. Run type checking: `mypy src/`
8. Commit with clear messages
9. Push to your fork
10. Create a pull request with description

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Questions and Support

For questions or issues:

1. Check existing documentation
2. Search GitHub issues
3. Create a new issue with details and reproduction steps
