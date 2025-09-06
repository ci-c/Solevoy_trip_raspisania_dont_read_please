# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Base repository class and interfaces."""

from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository class for database operations."""

    def __init__(self, model: type[T], session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            model: SQLAlchemy model class.
            session: Database session.
        """
        self._model = model
        self._session = session

    async def get_by_id(self, id_: int) -> T | None:
        """Get entity by ID.

        Args:
            id_: Entity ID.

        Returns:
            Entity if found, None otherwise.
        """
        stmt = select(self._model).where(self._model.id == id_)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[T]:
        """Get all entities.

        Returns:
            List of all entities.
        """
        stmt = select(self._model)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> T:
        """Create new entity.

        Args:
            **kwargs: Entity attributes.

        Returns:
            Created entity.
        """
        entity = self._model(**kwargs)
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def update(self, id_: int, **kwargs: Any) -> T | None:
        """Update entity by ID.

        Args:
            id_: Entity ID.
            **kwargs: New attribute values.

        Returns:
            Updated entity if found, None otherwise.
        """
        entity = await self.get_by_id(id_)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            await self._session.commit()
            await self._session.refresh(entity)
        return entity

    async def delete(self, id_: int) -> bool:
        """Delete entity by ID.

        Args:
            id_: Entity ID.

        Returns:
            True if entity was deleted, False otherwise.
        """
        entity = await self.get_by_id(id_)
        if entity:
            await self._session.delete(entity)
            await self._session.commit()
            return True
        return False
