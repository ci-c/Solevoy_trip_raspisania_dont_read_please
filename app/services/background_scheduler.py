"""
Фоновый планировщик для автоматического обновления расписаний.
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Optional
from loguru import logger

from app.services.schedule_updater_service import ScheduleUpdaterService


class BackgroundScheduler:
    """Планировщик фоновых задач."""

    def __init__(self):
        self.schedule_updater = ScheduleUpdaterService()
        self.is_running = False
        self.tasks: set = set()

    async def start(self) -> None:
        """Запустить планировщик."""
        if self.is_running:
            logger.warning("Background scheduler already running")
            return

        self.is_running = True
        logger.info("Starting background scheduler")

        # Запускаем основные задачи
        self._create_task(self._daily_schedule_update())
        self._create_task(self._hourly_health_check())

        logger.info("Background scheduler started successfully")

    async def stop(self) -> None:
        """Остановить планировщик."""
        if not self.is_running:
            return

        logger.info("Stopping background scheduler...")
        self.is_running = False

        # Отменяем все задачи
        for task in self.tasks.copy():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.tasks.clear()
        logger.info("Background scheduler stopped")

    def _create_task(self, coro) -> asyncio.Task:
        """Создать и отслеживать задачу."""
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def _daily_schedule_update(self) -> None:
        """Ежедневное обновление расписаний."""
        while self.is_running:
            try:
                # Запускаем в 03:00 каждый день
                target_time = time(3, 0)
                await self._wait_until_time(target_time)

                if not self.is_running:
                    break

                logger.info("Starting daily schedule update")
                stats = await self.schedule_updater.update_all_schedules()

                logger.info(f"Daily schedule update completed: {stats}")

                # Если много ошибок, делаем дополнительную попытку через 2 часа
                if stats["failed_groups"] > stats["updated_groups"] * 0.3:
                    logger.warning("High failure rate, retry in 2 hours")
                    await asyncio.sleep(2 * 3600)  # 2 часа

                    if self.is_running:
                        logger.info("Starting retry schedule update")
                        retry_stats = await self.schedule_updater.update_all_schedules()
                        logger.info(f"Retry update completed: {retry_stats}")

            except Exception as e:
                logger.error(f"Error in daily schedule update: {e}")
                # При ошибке ждем час перед следующей попыткой
                await asyncio.sleep(3600)

    async def _hourly_health_check(self) -> None:
        """Ежечасная проверка состояния системы."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Каждый час

                if not self.is_running:
                    break

                # Получаем статистику синхронизации
                stats = await self.schedule_updater.get_sync_statistics()

                # Проверяем критические проблемы
                issues = []

                # Давно не было синхронизации
                if stats["last_sync"]:
                    last_sync = datetime.fromisoformat(stats["last_sync"])
                    if datetime.now() - last_sync > timedelta(days=2):
                        issues.append("No sync for 2+ days")

                # Мало синхронизированных групп
                if stats["total_groups"] > 0:
                    sync_rate = stats["synced_groups"] / stats["total_groups"]
                    if sync_rate < 0.5:
                        issues.append(f"Low sync rate: {sync_rate:.1%}")

                if issues:
                    logger.warning(f"Health check issues: {', '.join(issues)}")
                else:
                    logger.debug(f"Health check OK: {stats}")

            except Exception as e:
                logger.error(f"Error in health check: {e}")

    async def _wait_until_time(self, target_time: time) -> None:
        """Ждать до определенного времени."""
        now = datetime.now()
        target_dt = datetime.combine(now.date(), target_time)

        # Если время уже прошло сегодня, ждем до завтра
        if target_dt <= now:
            target_dt += timedelta(days=1)

        sleep_seconds = (target_dt - now).total_seconds()
        await asyncio.sleep(sleep_seconds)

    async def trigger_immediate_update(self, force: bool = False) -> dict:
        """Запустить немедленное обновление расписаний."""
        logger.info("Triggering immediate schedule update")

        try:
            stats = await self.schedule_updater.update_all_schedules(force=force)
            logger.info(f"Immediate update completed: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error in immediate update: {e}")
            raise

    async def update_single_group(self, group_id: int) -> dict:
        """Обновить расписание одной группы."""
        logger.info(f"Updating single group: {group_id}")

        try:
            result = await self.schedule_updater.update_group_schedule(group_id)
            logger.info(f"Group {group_id} updated: {result}")
            return result
        except Exception as e:
            logger.error(f"Error updating group {group_id}: {e}")
            raise


# Глобальный экземпляр планировщика
_scheduler_instance: Optional[BackgroundScheduler] = None


async def get_scheduler() -> BackgroundScheduler:
    """Получить экземпляр планировщика."""
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = BackgroundScheduler()

    return _scheduler_instance


async def start_background_scheduler() -> None:
    """Запустить фоновый планировщик."""
    scheduler = await get_scheduler()
    await scheduler.start()


async def stop_background_scheduler() -> None:
    """Остановить фоновый планировщик."""
    global _scheduler_instance

    if _scheduler_instance:
        await _scheduler_instance.stop()
        _scheduler_instance = None
