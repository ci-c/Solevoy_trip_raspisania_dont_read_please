"""Base SQLAlchemy models for academic data."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FacultyDB(Base, TimestampMixin):
    """Faculty database model."""
    
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False, server_default="")
    code = Column(String, nullable=False, server_default="")


class SpecialityDB(Base, TimestampMixin):
    """Speciality database model."""
    
    __tablename__ = "specialities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculties.faculty_id"), nullable=False)
    degree_type = Column(String, nullable=False, server_default="speciality")
