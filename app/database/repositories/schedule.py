# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Schedule repository implementation."""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Schedule, Group
from app.database.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    """Schedule repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: Database session.

        """
        super().__init__(Schedule, session)

    async def get_by_group(self, group: Group) -> Sequence[Schedule]:
        """Get schedule entries by group.

        Args:
            group: Group to get schedule for.

        Returns:
            List of schedule entries.

        """
        stmt = select(Schedule).where(Schedule.group_id == group.id)
        result = await self._session.execute(stmt)
        return result.scalars().all()
