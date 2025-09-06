"""
Асинхронное подключение к базе данных SQLite.

Зона ответственности:
- Управление асинхронными подключениями к SQLite через aiosqlite
- Инициализация схемы базы данных из SQL-файлов
- Выполнение миграций базы данных с отслеживанием состояния
- Создание резервных копий базы данных
- Настройка оптимальных параметров SQLite (WAL, foreign keys)
- Предоставление глобального интерфейса для доступа к БД
"""

import aiosqlite
from pathlib import Path
from typing import AsyncGenerator, Optional
from loguru import logger

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "szgmu_bot.db"


class DatabaseConnection:
    """Управление подключениями к базе данных."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Получить асинхронное подключение к БД."""
        async with aiosqlite.connect(str(self.db_path)) as conn:
            # Включаем поддержку foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")
            # Включаем WAL режим для лучшей производительности
            await conn.execute("PRAGMA journal_mode = WAL")
            yield conn

    async def initialize_database(self) -> None:
        """Инициализация базы данных со схемой."""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        async with aiosqlite.connect(str(self.db_path)) as conn:
            # Включаем поддержку foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")
            # Включаем WAL режим для лучшей производительности
            await conn.execute("PRAGMA journal_mode = WAL")
            
            try:
                with open(schema_path, "r", encoding="utf-8") as schema_file:
                    schema_sql = schema_file.read()

                # Выполняем создание базовой схемы
                await conn.executescript(schema_sql)
                await conn.commit()

                logger.info("Database schema initialized successfully")

            except Exception as e:
                logger.error(f"Error initializing database schema: {e}")
                raise

    async def init_database(self) -> None:
        """Полная инициализация базы данных с миграциями."""
        # Инициализируем основную схему
        await self.initialize_database()

        # Выполняем миграции
        await self.run_migrations()

    async def run_migrations(self) -> None:
        """Выполнение миграций базы данных."""
        migrations_dir = Path(__file__).parent
        migration_files = sorted(migrations_dir.glob("migration_*.sql"))

        if not migration_files:
            logger.info("No migrations found")
            return

        async with aiosqlite.connect(str(self.db_path)) as conn:
            # Включаем поддержку foreign keys
            await conn.execute("PRAGMA foreign_keys = ON")
            # Включаем WAL режим для лучшей производительности
            await conn.execute("PRAGMA journal_mode = WAL")
            try:
                # Создаем таблицу для отслеживания миграций
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        filename TEXT PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                for migration_file in migration_files:
                    filename = migration_file.name

                    # Проверяем не применялась ли уже эта миграция
                    cursor = await conn.execute(
                        "SELECT filename FROM schema_migrations WHERE filename = ?",
                        (filename,),
                    )

                    if await cursor.fetchone():
                        logger.debug(f"Migration {filename} already applied")
                        continue

                    # Применяем миграцию
                    with open(migration_file, "r", encoding="utf-8") as f:
                        migration_sql = f.read()

                    await conn.executescript(migration_sql)

                    # Отмечаем как примененную
                    await conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (?)",
                        (filename,),
                    )

                    logger.info(f"Applied migration: {filename}")

                await conn.commit()
                logger.info("All migrations applied successfully")

            except Exception as e:
                logger.error(f"Error running migrations: {e}")
                raise

    async def check_database_exists(self) -> bool:
        """Проверить существует ли база данных."""
        return self.db_path.exists()

    async def backup_database(self, backup_path: Path) -> None:
        """Создать резервную копию базы данных."""
        if not self.db_path.exists():
            raise FileNotFoundError("Source database does not exist")

        backup_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(str(self.db_path)) as source:
            async with aiosqlite.connect(str(backup_path)) as backup:
                await source.backup(backup)

        logger.info(f"Database backed up to {backup_path}")


# Глобальный экземпляр для использования в приложении
db_connection = DatabaseConnection()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Удобная функция для получения подключения к БД."""
    async with db_connection.get_connection() as conn:
        yield conn


async def init_db() -> None:
    """Инициализация базы данных при запуске приложения."""
    try:
        await db_connection.initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
