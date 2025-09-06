"""
Главный файл Telegram бота с улучшенной архитектурой.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from app.database.connection import DatabaseConnection
from app.bot.handlers import register_handlers
from app.services.background_scheduler import (
    start_background_scheduler,
    stop_background_scheduler,
)


class BotApplication:
    """Основное приложение бота."""

    def __init__(self, token: str):
        self.token = token
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None

    async def create_bot(self) -> Bot:
        """Создать экземпляр бота."""
        if not self.bot:
            self.bot = Bot(
                token=self.token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
        return self.bot

    async def create_dispatcher(self) -> Dispatcher:
        """Создать диспетчер."""
        if not self.dp:
            self.dp = Dispatcher()

            # Регистрируем обработчики
            await register_handlers(self.dp)

        return self.dp

    async def setup(self):
        """Настройка приложения."""
        logger.info("Setting up bot application...")

        # Инициализация базы данных
        try:
            db_connection = DatabaseConnection()
            await db_connection.init_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        # Создаем бота и диспетчер
        self.bot = await self.create_bot()
        self.dp = await self.create_dispatcher()

        # Запускаем фоновый планировщик
        try:
            await start_background_scheduler()
            logger.info("Background scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start background scheduler: {e}")
            # Не критичная ошибка, продолжаем без планировщика

        logger.info("Bot application setup completed")

    async def start(self):
        """Запуск бота."""
        logger.info("Starting bot...")

        if not self.bot or not self.dp:
            await self.setup()

        try:
            # Очищаем webhook если есть
            await self.bot.delete_webhook(drop_pending_updates=True)

            # Запускаем polling
            await self.dp.start_polling(self.bot)

        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            if self.bot:
                await self.bot.session.close()

    async def stop(self):
        """Остановка бота."""
        logger.info("Stopping bot...")

        # Останавливаем фоновый планировщик
        try:
            await stop_background_scheduler()
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping background scheduler: {e}")

        if self.dp:
            await self.dp.stop_polling()

        if self.bot:
            await self.bot.session.close()

        logger.info("Bot stopped")


def create_bot_app(token: str) -> BotApplication:
    """Создать приложение бота."""
    return BotApplication(token)


async def main():
    """Главная функция для запуска бота."""
    from dotenv import load_dotenv
    import os

    # Загрузка переменных окружения
    load_dotenv()

    token = os.getenv("BOT_API_KEY")
    if not token:
        logger.critical("BOT_API_KEY not found in environment variables")
        sys.exit(1)

    # Настройка логирования
    from ..utils.logger import LoggingConfig, log_bot_startup, log_bot_shutdown

    base_dir = Path(__file__).resolve().parent.parent.parent
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "data").mkdir(exist_ok=True)

    # Инициализируем систему логирования
    logging_config = LoggingConfig(base_dir)
    logging_config.setup_logging()

    log_bot_startup()

    # Создание и запуск приложения
    app = create_bot_app(token)

    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.critical(f"Critical error: {e}")
    finally:
        log_bot_shutdown()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
