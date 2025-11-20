#!/usr/bin/env python3
"""Скрипт для создания групп из занятий."""

import asyncio
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from app.services.api_sync_service import APISyncService


async def main() -> None:
    """Создать группы из занятий."""
    try:
        logger.info("Starting group creation from lessons...")

        sync_service = APISyncService()
        await sync_service._create_groups_from_lessons()

        logger.info("Group creation completed!")

    except Exception as e:
        logger.error(f"Error creating groups: {e}")
        logger.error(f"Traceback: {e.__traceback__}")


if __name__ == "__main__":
    asyncio.run(main())
