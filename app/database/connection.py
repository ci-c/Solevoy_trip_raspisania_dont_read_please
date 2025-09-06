# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Asynchronous SQLite database connection.

Responsibilities:
- Manage asynchronous SQLite connections via aiosqlite
- Initialize database schema from SQL files
- Execute database migrations with state tracking
- Create database backups
- Configure optimal SQLite parameters (WAL, foreign keys)
- Provide global interface for database access
"""

import aiosqlite
import anyio
from collections.abc import AsyncGenerator
from loguru import logger
from pathlib import Path


class DatabaseError(Exception):
    """Base class for database-related exceptions."""


class SchemaNotFoundError(DatabaseError):
    """Raised when schema file cannot be found."""

    def __init__(self, schema_path: Path) -> None:
        """Initialize schema not found error.

        Args:
            schema_path: Path where schema file was expected.
        """
        self.schema_path = schema_path
        super().__init__(f"Schema file not found: {schema_path}")


class DatabaseNotFoundError(DatabaseError):
    """Raised when source database does not exist."""

    def __init__(self) -> None:
        """Initialize database not found error."""
        super().__init__("Source database does not exist")


class MigrationError(DatabaseError):
    """Raised when a database migration fails."""

    def __init__(self, migration_name: str, cause: str) -> None:
        """Initialize migration error.

        Args:
            migration_name: Name of the failed migration.
            cause: Reason for migration failure.
        """
        self.migration_name = migration_name
        self.cause = cause
        super().__init__(f"Failed to apply migration {migration_name}: {cause}")


class InitializationError(DatabaseError):
    """Raised when database initialization fails."""

    def __init__(self, cause: str) -> None:
        """Initialize initialization error.

        Args:
            cause: Reason for initialization failure.
        """
        self.cause = cause
        super().__init__(f"Failed to initialize database: {cause}")


DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "database.db"


class DatabaseConnection:
    """Database connection manager."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize database connection manager.

        Args:
            db_path: Custom database path, defaults to DATABASE_PATH.
        """
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get an asynchronous database connection.

        Yields:
            aiosqlite.Connection: Database connection with WAL mode and foreign keys
                enabled.
        """
        async with aiosqlite.connect(str(self.db_path)) as conn:
            # Enable foreign key support
            await conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better performance
            await conn.execute("PRAGMA journal_mode = WAL")
            yield conn

    async def initialize_database(self) -> None:
        """Initialize database with schema.

        This method creates the initial database structure by executing
        the SQL schema file.

        Raises:
            SchemaNotFoundError: If schema file does not exist.
            InitializationError: If there's an error executing schema SQL.
        """
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise SchemaNotFoundError(schema_path)

        async with aiosqlite.connect(str(self.db_path)) as conn:
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute("PRAGMA journal_mode = WAL")
            
            try:
                sql = await anyio.Path(schema_path).read_text(encoding="utf-8")
                await conn.executescript(sql)
                await conn.commit()
                logger.info("Database schema initialized successfully")
            except Exception as e:
                msg = f"Error executing schema SQL: {e}"
                logger.error(msg)
                raise InitializationError(str(e)) from e

    async def init_database(self) -> None:
        """Initialize database and run migrations.

        This method performs complete database initialization by executing
        the base schema and all available migrations.
        """
        # Initialize main schema
        await self.initialize_database()
        # Run migrations
        await self.run_migrations()

    async def run_migrations(self) -> None:
        """Execute database migrations.

        This method applies all available migration files in order,
        tracking which migrations have been applied.

        Raises:
            MigrationError: If a migration fails.
        """
        migrations_dir = Path(__file__).parent
        migration_files = sorted(migrations_dir.glob("migration_*.sql"))

        if not migration_files:
            logger.info("No migrations found")
            return

        async with aiosqlite.connect(str(self.db_path)) as conn:
            await conn.execute("PRAGMA foreign_keys = OFF")
            await conn.execute("PRAGMA journal_mode = WAL")
            
            try:
                # Create migration tracking table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        filename TEXT PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await conn.commit()

                for migration_file in migration_files:
                    filename = migration_file.name
                    cursor = await conn.execute(
                        "SELECT filename FROM schema_migrations WHERE filename = ?",
                        (filename,),
                    )

                    if await cursor.fetchone():
                        logger.debug(f"Migration {filename} already applied")
                        continue

                    # Create savepoint
                    await conn.execute("SAVEPOINT migration_start")

                    try:
                        # Apply migration
                        migration_sql = await anyio.Path(
                            migration_file
                        ).read_text(encoding="utf-8")
                        
                        # Execute migration statements
                        statements = migration_sql.split(";")
                        for statement in statements:
                            if statement.strip():
                                await conn.execute(statement)
                        
                        # Mark as applied
                        await conn.execute(
                            "INSERT INTO schema_migrations (filename) VALUES (?)",
                            (filename,),
                        )

                        # Release savepoint
                        await conn.execute("RELEASE migration_start")
                        logger.info(f"Applied migration: {filename}")
                    
                    except Exception as e:
                        # Rollback to savepoint on error
                        await conn.execute("ROLLBACK TO migration_start")
                        logger.error(f"Failed to apply migration {filename}: {e}")
                        msg = f"Migration failed: {e}"
                        raise MigrationError(filename, msg) from e

                await conn.commit()
                await conn.execute("PRAGMA foreign_keys = ON")
                logger.info("All migrations applied successfully")

            except Exception as e:
                msg = f"Error running migrations: {e}"
                logger.error(msg)
                raise MigrationError("migrations", str(e)) from e

    async def check_database_exists(self) -> bool:
        """Check if the database file exists.

        Returns:
            bool: True if database exists, False otherwise.
        """
        return self.db_path.exists()

    async def backup_database(self, backup_path: Path) -> None:
        """Create a backup of the database.

        Args:
            backup_path: Path where backup will be created.

        Raises:
            DatabaseNotFoundError: If source database does not exist.
            DatabaseError: If backup operation fails.
        """
        if not self.db_path.exists():
            raise DatabaseNotFoundError

        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiosqlite.connect(str(self.db_path)) as source, \
                      aiosqlite.connect(str(backup_path)) as backup:
                await source.backup(backup)

            logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            msg = f"Backup failed: {e}"
            logger.error(msg)
            raise DatabaseError(msg) from e


# Global instance for use in application
db_connection = DatabaseConnection()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get a database connection.

    A convenience function that provides a database connection with proper
    settings.

    Yields:
        aiosqlite.Connection: Database connection with WAL mode and foreign keys
            enabled.
    """
    async with db_connection.get_connection() as conn:
        yield conn


async def init_db() -> None:
    """Initialize database when application starts.

    Raises:
        InitializationError: If database initialization fails.
    """
    try:
        await db_connection.initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        msg = f"Failed to initialize database: {e}"
        logger.error(msg)
        raise InitializationError(str(e)) from e
