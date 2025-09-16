#!/usr/bin/env python3
"""
SZGMU Schedule Bot - Main Entry Point
Telegram bot for SZGMU university schedule management.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from app.bot.main import main as bot_main
from app.utils.logger import LoggingConfig, log_bot_shutdown
from app.utils.secrets import validate_environment, secrets_manager


async def setup_app() -> None:
    """Initialize application."""
    # Load environment variables
    load_dotenv()

    # Validate environment and secrets
    if not validate_environment():
        logger.error("Environment validation failed. Please check your .env file.")
        sys.exit(1)

    # Set up directories
    base_dir = Path(__file__).parent
    logs_dir = base_dir / "logs"
    data_dir = base_dir / "data"

    logs_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    # Initialize logging
    logging_config = LoggingConfig(base_dir)
    logging_config.setup_logging()

    # Log secrets status (masked)
    secrets_manager.log_secrets_status()


async def start_app() -> None:
    """Start the application."""
    await setup_app()
    await bot_main()


def main():
    """Main entry point for the application."""
    try:
        asyncio.run(start_app())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.critical(f"Application error: {e}")
        sys.exit(1)
    finally:
        log_bot_shutdown()


if __name__ == "__main__":
    main()
