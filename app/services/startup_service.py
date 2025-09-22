"""
Сервис для инициализации системы при запуске.
"""

from typing import Optional
from loguru import logger

from app.services.api_sync_service import APISyncService
from app.services.schedule_service import ScheduleService
from app.services.faculty_service import FacultyService


class StartupService:
    """Сервис для инициализации системы."""

    def __init__(self):
        self.api_sync_service = APISyncService()
        self.schedule_service = ScheduleService()
        self.faculty_service = FacultyService()

    async def initialize_system(self) -> dict[str, object] | None:
        """
        Инициализация системы при запуске.
        
        Returns:
            Словарь с результатами инициализации
        """
        logger.info("Starting system initialization...")
        
        results = {
            "faculties_loaded": False,
            "schedules_synced": False,
            "database_ready": False,
            "errors": []
        }
        
        try:
            # 1. Проверяем наличие факультетов
            faculties = await self.schedule_service.get_available_faculties()
            if not faculties:
                logger.info("No faculties found, starting background sync...")
                
                # Запускаем синхронизацию в фоне
                import asyncio
                asyncio.create_task(self._background_sync())
                results["schedules_synced"] = False  # В процессе
                logger.info("Background sync started")
            else:
                results["faculties_loaded"] = True
                logger.info(f"Found {len(faculties)} faculties in database")
            
            # 2. Проверяем готовность базы данных
            stats = await self.schedule_service.get_schedule_statistics()
            if stats:
                results["database_ready"] = True
                logger.info(f"Database ready: {stats}")
            else:
                results["errors"].append("Database not ready")
                logger.error("Database not ready")
            
            # 2.1. Проверяем наличие групп и создаем если нужно
            from app.services.group_service import GroupService
            group_service = GroupService()
            groups_count = await group_service.get_groups_count()
            if groups_count == 0:
                logger.info("No groups found, creating from lessons...")
                await self.api_sync_service._create_groups_from_lessons()
                logger.info("Groups created from lessons")
            else:
                logger.info(f"Found {groups_count} groups in database")
            
            # 3. Проверяем текущий семестр
            current_semester = await self.schedule_service.get_current_semester()
            if current_semester:
                logger.info(f"Current semester: {current_semester['name']}")
            else:
                logger.warning("No current semester set")
            
            # 4. Проверяем текущий учебный год
            current_year = await self.schedule_service.get_current_academic_year()
            if current_year:
                logger.info(f"Current academic year: {current_year['name']}")
            else:
                logger.warning("No current academic year set")
            
            if results["errors"]:
                logger.warning(f"Initialization completed with errors: {results['errors']}")
            else:
                logger.info("System initialization completed successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during system initialization: {e}")
            results["errors"].append(str(e))
            return results

    async def _background_sync(self) -> None:
        """Фоновая синхронизация данных."""
        try:
            logger.info("Starting background sync...")
            sync_success = await self.api_sync_service.full_sync()
            if sync_success:
                logger.info("Background sync completed successfully")
            else:
                logger.error("Background sync failed")
        except Exception as e:
            logger.error(f"Background sync error: {e}")
            logger.error(f"Traceback: {e.__traceback__}")

    async def check_system_health(self) -> dict[str, object] | None:
        """
        Проверка состояния системы.
        
        Returns:
            Словарь с информацией о состоянии системы
        """
        health = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        try:
            # Проверяем базу данных
            stats = await self.schedule_service.get_schedule_statistics()
            health["components"]["database"] = {
                "status": "healthy" if stats else "unhealthy",
                "stats": stats
            }
            
            if not stats:
                health["issues"].append("Database not accessible")
                health["status"] = "unhealthy"
            
            # Проверяем факультеты
            faculties = await self.schedule_service.get_available_faculties()
            health["components"]["faculties"] = {
                "status": "healthy" if faculties else "unhealthy",
                "count": len(faculties) if faculties else 0
            }
            
            if not faculties:
                health["issues"].append("No faculties available")
                health["status"] = "unhealthy"
            
            # Проверяем специальности
            specialities = await self.schedule_service.get_available_specialities()
            health["components"]["specialities"] = {
                "status": "healthy" if specialities else "unhealthy",
                "count": len(specialities) if specialities else 0
            }
            
            if not specialities:
                health["issues"].append("No specialities available")
                health["status"] = "unhealthy"
            
            # Проверяем текущий семестр
            current_semester = await self.schedule_service.get_current_semester()
            health["components"]["current_semester"] = {
                "status": "healthy" if current_semester else "warning",
                "semester": current_semester
            }
            
            if not current_semester:
                health["issues"].append("No current semester set")
                if health["status"] == "healthy":
                    health["status"] = "warning"
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            health["status"] = "unhealthy"
            health["issues"].append(f"Health check failed: {e}")
            return health

    async def warm_up_cache(self) -> None:
        """Прогрев кэша при запуске."""
        try:
            logger.info("Warming up cache...")
            
            # Загружаем часто используемые данные
            await self.schedule_service.get_available_faculties()
            await self.schedule_service.get_available_specialities()
            await self.schedule_service.get_current_semester()
            await self.schedule_service.get_current_academic_year()
            
            logger.info("Cache warmed up successfully")
            
        except Exception as e:
            logger.error(f"Error warming up cache: {e}")

    async def run_startup_checks(self) -> bool:
        """
        Запуск проверок при старте системы.
        
        Returns:
            True если все проверки прошли успешно
        """
        try:
            logger.info("Running startup checks...")
            
            # Инициализируем систему
            init_results = await self.initialize_system()
            
            # Проверяем состояние системы
            health = await self.check_system_health()
            
            # Прогреваем кэш
            await self.warm_up_cache()
            
            # Логируем результаты
            if init_results["errors"]:
                logger.warning(f"Initialization completed with errors: {init_results['errors']}")
            
            if health["status"] != "healthy":
                logger.warning(f"System health check failed: {health['issues']}")
                return False
            
            logger.info("All startup checks passed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during startup checks: {e}")
            return False
