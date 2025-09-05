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

from ..database.connection import init_db
from .handlers import register_handlers


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
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
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
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        
        # Создаем бота и диспетчер
        self.bot = await self.create_bot()
        self.dp = await self.create_dispatcher()
        
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
    logger.remove()
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO"
    )
    
    # Создание директорий
    base_dir = Path(__file__).resolve().parent.parent.parent
    (base_dir / "logs").mkdir(exist_ok=True)
    (base_dir / "data").mkdir(exist_ok=True)
    
    logger.add(
        base_dir / "logs" / "bot_errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        compression="zip"
    )
    
    # Создание и запуск приложения
    app = create_bot_app(token)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.critical(f"Critical error: {e}")
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())