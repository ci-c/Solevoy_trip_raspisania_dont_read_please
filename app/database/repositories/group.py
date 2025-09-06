# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Group repository implementation."""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Group, Schedule
from app.database.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """Group repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: Database session.

        """
        super().__init__(Group, session)

    async def get_by_name(self, name: str) -> Group | None:
        """Get group by name.

        Args:
            name: Group name.

        Returns:
            Group if found, None otherwise.

        """
        stmt = select(Group).where(Group.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_schedules(self) -> Sequence[Group]:
        """Get all groups with their schedules.

        Returns:
            List of groups with schedules.

        """
        stmt = select(Group).options(selectinload(Group.schedules))
        result = await self._session.execute(stmt)
        return result.scalars().all()
