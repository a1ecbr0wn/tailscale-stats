"""Main entry point for Tailscale status stats collection."""

import logging
import sys
import time

from .collector import TailscaleCollector
from .config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info(
            f"Configuration loaded: interval={config.interval}s, "
            f"base_location={config.base_location}"
        )

        # Initialize collector
        collector = TailscaleCollector(
            config.base_location,
            config.file_name_format,
        )

        logger.info("Starting Tailscale status collection...")

        # Main collection loop
        while True:
            try:
                logger.debug("Collecting Tailscale status...")
                status_data = collector.collect_status()

                file_path = collector.save_status(status_data)
                logger.info(f"Status saved to {file_path}")

            except Exception as e:
                logger.error(f"Error during collection: {e}", exc_info=True)

            # Wait before next collection
            time.sleep(config.interval)

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
