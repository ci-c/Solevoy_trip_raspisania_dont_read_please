# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Create initial tables for faculties and specialities."""

from loguru import logger

try:
    import sqlalchemy
    from sqlalchemy.schema import CreateTable
except ImportError as e:
    error_msg = "Failed to import SQLAlchemy"
    raise ImportError(error_msg) from e

from app.models.academic_db import FacultyDB, SpecialityDB

# Create engine and metadata
engine = sqlalchemy.create_engine("sqlite:///data/szgmu_bot.db", future=True)
metadata = sqlalchemy.MetaData()


def create_tables() -> None:
    """Create faculty and speciality tables."""
    # Get table objects
    faculty_table = FacultyDB.__table__
    speciality_table = SpecialityDB.__table__

    # Generate SQL
    with engine.connect() as conn:
        # Create faculties table
        create_faculty = CreateTable(faculty_table).compile(conn)
        logger.info("Creating faculties table:")
        logger.debug(str(create_faculty).strip())
        conn.execute(create_faculty)

        # Create specialities table
        create_speciality = CreateTable(speciality_table).compile(conn)
        logger.info("Creating specialities table:")
        logger.debug(str(create_speciality).strip())
        conn.execute(create_speciality)

        conn.commit()
        logger.success("Database schema created successfully")


if __name__ == "__main__":
    create_tables()
