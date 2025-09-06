"""Service for managing faculties and specialities."""

from datetime import datetime, timezone

import asyncio
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import Faculty, Speciality
from app.models.academic_db import FacultyDB, SpecialityDB
from app.schedule.faculty_api_client import FacultyAPIClient


class FacultyService:
    """Service for managing faculties and specialities."""
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service.
        
        Args:
            session: SQLAlchemy async database session.
            
        """
        self.session = session
        self.api_client = FacultyAPIClient()
        
    async def sync_faculties(self) -> None:
        """Sync faculties from API to database."""
        try:
            faculties = await asyncio.get_event_loop().run_in_executor(
                None, self.api_client.get_faculties,
            )
            logger.info(f"Syncing {len(faculties)} faculties")
            
            for faculty_data in faculties:
                faculty_model = Faculty(
                    faculty_id=faculty_data["id"],
                    name=faculty_data["name"],
                    short_name=faculty_data.get("shortName", ""),
                    code=faculty_data.get("code", ""),
                )
                
                # Check if faculty exists
                stmt = select(FacultyDB).where(
                    FacultyDB.faculty_id == faculty_data["id"],
                )
                result = await self.session.execute(stmt)
                faculty_db = result.scalar_one_or_none()
                
                if faculty_db:
                    # Update existing faculty
                    faculty_db.name = faculty_model.name
                    faculty_db.short_name = faculty_model.short_name
                    faculty_db.code = faculty_model.code
                    faculty_db.updated_at = datetime.now(tz=timezone.utc)
                else:
                    # Create new faculty
                    faculty_db = FacultyDB(
                        faculty_id=faculty_model.faculty_id,
                        name=faculty_model.name,
                        short_name=faculty_model.short_name,
                        code=faculty_model.code,
                    )
                    self.session.add(faculty_db)
                
                try:
                    await self.session.commit()
                    # Sync specialities for this faculty
                    await self.sync_specialities(faculty_model.faculty_id)
                except IntegrityError as e:
                    await self.session.rollback()
                    logger.error(f"Error saving faculty {faculty_model.name}: {e}")
                
        except Exception as e:
            logger.error(f"Error syncing faculties: {e}")
            raise

    async def sync_specialities(self, faculty_id: int | None = None) -> None:
        """Sync specialities from API to database.
        
        Args:
            faculty_id: Optional ID of faculty to sync specialities for.
                If None, syncs all specialities.
                
        """
        try:
            specialities = await asyncio.get_event_loop().run_in_executor(
                None, self.api_client.get_specialities, faculty_id,
            )
            logger.info(f"Syncing {len(specialities)} specialities")
            
            for spec_data in specialities:
                spec_model = Speciality(
                    code=spec_data["code"],
                    name=spec_data["name"],
                    full_name=spec_data["fullName"],
                    faculty_id=spec_data["facultyId"],
                    degree_type=spec_data.get("degreeType", "speciality"),
                )
                
                # Check if speciality exists
                stmt = select(SpecialityDB).where(
                    SpecialityDB.code == spec_data["code"],
                )
                result = await self.session.execute(stmt)
                spec_db = result.scalar_one_or_none()
                
                if spec_db:
                    # Update existing speciality
                    spec_db.name = spec_model.name
                    spec_db.full_name = spec_model.full_name
                    spec_db.faculty_id = spec_model.faculty_id
                    spec_db.degree_type = spec_model.degree_type
                    spec_db.updated_at = datetime.now(tz=timezone.utc)
                else:
                    # Create new speciality
                    spec_db = SpecialityDB(
                        code=spec_model.code,
                        name=spec_model.name,
                        full_name=spec_model.full_name,
                        faculty_id=spec_model.faculty_id,
                        degree_type=spec_model.degree_type,
                    )
                    self.session.add(spec_db)
                
                try:
                    await self.session.commit()
                except IntegrityError as e:
                    await self.session.rollback()
                    logger.error(f"Error saving speciality {spec_model.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error syncing specialities: {e}")
            raise
            
    def close(self) -> None:
        """Close the API client connection."""
        self.api_client.close()
