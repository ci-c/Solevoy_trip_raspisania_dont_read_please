"""
Entry point for SZGMU Schedule Bot.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from app.database.session import init_db
from app.bot.main import main
from app.utils.logger import LoggingConfig, log_bot_startup, log_bot_shutdown


async def setup_app() -> None:
    """Initialize application."""
    # Load environment variables
    load_dotenv()

    # Set up directories
    base_dir = Path(__file__).parent
    logs_dir = base_dir / "logs"
    data_dir = base_dir / "data"

    logs_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    # Initialize logging
    logging_config = LoggingConfig(base_dir)
    logging_config.setup_logging()

    log_bot_startup()

    # Initialize database with SQLAlchemy
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}")
        raise


async def start_app() -> None:
    """Start the application."""
    try:
        await setup_app()
        await main()
    except Exception as e:
        logger.critical(f"Application error: {e}")
        raise
    finally:
        log_bot_shutdown()


if __name__ == "__main__":
    asyncio.run(start_app())