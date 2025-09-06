"""Main Telegram bot application module."""

import asyncio
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from dotenv import load_dotenv
from loguru import logger

from app.bot.handlers import register_handlers
from app.database.session import init_db
from app.services.background_scheduler import (
    start_background_scheduler,
    stop_background_scheduler,
)
from app.utils.logger import LoggingConfig, log_bot_startup, log_bot_shutdown

__all__ = ["BotError", "create_bot", "main"]


class BotError(Exception):
    """Base class for bot-related errors."""

    def __init__(self, message: str) -> None:
        """Initialize error.
        
        Args:
            message: Error description.
        
        """
        self.message = message
        super().__init__(message)


class ConfigError(BotError):
    """Raised when bot configuration is invalid."""

    def __init__(self, parameter: str) -> None:
        """Initialize error.
        
        Args:
            parameter: Missing configuration parameter name.
        
        """
        message = f"Missing required config parameter: {parameter}"
        super().__init__(message)


class SetupError(BotError):
    """Raised when bot setup fails."""

    def __init__(self, cause: str | None = None) -> None:
        """Initialize error.
        
        Args:
            cause: Optional description of what caused the failure.
        
        """
        message = "Bot setup failed. See logs for details."
        if cause:
            message = f"{message} Cause: {cause}"
        super().__init__(message)


class NotInitializedError(BotError):
    """Raised when trying to use uninitialized bot."""

    def __init__(self) -> None:
        """Initialize error."""
        super().__init__("Bot not initialized. Call setup() first.")


class BotApplication:
    """Manage the Telegram bot application lifecycle.

    This class handles bot initialization, startup, and shutdown,
    providing a high-level interface for bot operations.
    """

    def __init__(self) -> None:
        """Initialize an empty bot application instance."""
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self._background_started: bool = False

    async def _check_token(self) -> str:
        """Validate and retrieve bot token.
        
        Returns:
            Valid bot token from environment.
        
        Raises:
            ConfigError: If BOT_TOKEN is not set.
        
        """
        token = os.environ.get("BOT_TOKEN")
        if not token:
            param = "BOT_TOKEN"
            raise ConfigError(param)
        return token

    async def _init_database(self) -> None:
        """Initialize database connection.
        
        Raises:
            SetupError: If database initialization fails.
        
        """
        try:
            await init_db()
        except Exception as e:
            cause = f"Database initialization failed: {e}"
            raise SetupError(cause) from e

    async def _init_scheduler(self) -> None:
        """Initialize background task scheduler.
        
        Sets _background_started flag if successful.
        Logs but does not raise on failure.
        
        """
        try:
            await start_background_scheduler()
            self._background_started = True
        except Exception as e:
            logger.warning(f"Background scheduler failed to start: {e}")

    async def setup(self) -> "BotApplication":
        """Set up the bot application.

        Load configuration and initialize all components.

        Returns:
            Configured bot application instance.

        Raises:
            ConfigError: If required configuration is missing.
            SetupError: If initialization of any component fails.
            BotError: Base class for all bot-related errors.

        """
        try:
            load_dotenv()
            token = await self._check_token()

            self.bot = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            self.dp = Dispatcher()
            register_handlers(self.dp)

            await self._init_database()
            await self._init_scheduler()

            return self

        except BotError:
            raise
        except Exception as e:
            err_msg = f"Failed to setup bot: {e}"
            logger.error(err_msg)
            raise SetupError(err_msg) from e

    async def start(self) -> None:
        """Start bot application.

        Raises:
            NotInitializedError: If setup() was not called
            TelegramAPIError: If connection to Telegram API fails
        """
        if not (self.bot and self.dp):
            raise NotInitializedError()

        try:
            log_bot_startup()

            # Start polling
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
            )
        except TelegramAPIError as e:
            logger.critical(f"Bot failed to start: {e}")
            raise
        except Exception as e:
            logger.critical(f"Bot failed to start: {e}")
            raise BotError(str(e)) from e
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop bot application and cleanup."""
        try:
            if self._background_started:
                await stop_background_scheduler()

            if self.bot:
                await self.bot.session.close()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")

async def create_bot() -> BotApplication:
    """Create and set up a new bot application.

    Returns:
        Configured bot application instance.

    """
    app = BotApplication()
    await app.setup()
    return app


async def main() -> None:
    """Run the bot application.

    Initialize and start the bot, handle shutdown on interrupt.
    """
    # Load environment variables
    load_dotenv()

    # Get bot token
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN not found in environment variables")
        sys.exit(1)

    # Set up logging
    base_dir = Path(__file__).resolve().parent.parent.parent
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "data").mkdir(exist_ok=True)

    LoggingConfig(base_dir).setup_logging()

    # Create and start bot
    app = None
    try:
        app = await create_bot()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except BotError as e:
        logger.critical(f"Bot error: {e}")
        sys.exit(1)
    finally:
        if app is not None:
            await app.stop()
            log_bot_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
