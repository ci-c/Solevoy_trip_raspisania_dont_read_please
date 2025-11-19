"""
Сервис для работы с пользователями и профилями через SQLAlchemy.
"""

from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger
from sqlalchemy import select, func

from app.database.session import get_session
from app.database.models import (
    User as UserModel,
    UserProfile as UserProfileModel,
)
from app.models.user import User, StudentProfile, Subscription, AccessLevel


class UserService:
    """Асинхронный сервис для управления пользователями через SQLAlchemy."""

    async def create_user(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Создать нового пользователя."""
        now = datetime.now(tz=timezone.utc)

        stored_now = now.replace(tzinfo=None)

        async for session in get_session():
            existing_result = await session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
            existing_user = existing_result.scalar_one_or_none()

            if existing_user:
                logger.info(
                    "User with telegram_id %s already exists, returning existing record",
                    telegram_id,
                )
                return self._to_user_model(existing_user)

            db_user = UserModel(
                telegram_id=telegram_id,
                username=telegram_username,
                first_name=full_name or "",
                last_name=None,
                access_level=AccessLevel.BASIC.value,  # New users get BASIC access
                is_active=True,
                last_seen=stored_now,
            )

            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

            user = self._to_user_model(db_user)
            logger.info("Created new user %s (telegram_id: %s)", user.id, telegram_id)
            return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        async for session in get_session():
            result = await session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
            db_user = result.scalar_one_or_none()

            if not db_user:
                return None

            return self._to_user_model(db_user)

    async def update_user_activity(self, telegram_id: int) -> None:
        """Обновить время последней активности пользователя по telegram_id."""
        now = datetime.now(tz=timezone.utc)
        async for session in get_session():
            result = await session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                logger.warning("User with telegram_id %s not found for activity update", telegram_id)
                return

            db_user.last_seen = now.astimezone(timezone.utc).replace(tzinfo=None)
            await session.commit()
            logger.debug("Updated last_seen for user telegram_id %s", telegram_id)

    async def update_user_access_level(
        self, user_id: int, access_level: AccessLevel
    ) -> bool:
        """Обновить уровень доступа пользователя."""
        async for session in get_session():
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if not db_user:
                logger.warning("User %s not found for access level update", user_id)
                return False

            db_user.access_level = access_level.value
            await session.commit()
            logger.info(
                "Updated access level for user %s to %s",
                user_id,
                access_level.value,
            )
            return True

    async def get_user_profile(self, user_id: int) -> Optional[StudentProfile]:
        """Получить профиль студента."""
        async for session in get_session():
            result = await session.execute(
                select(UserProfileModel).where(UserProfileModel.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return None

            return StudentProfile(
                id=profile.user_id,
                user_id=profile.user_id,
                group_id=profile.group_id,
                student_id=profile.student_id,
                preferred_format=profile.preferred_export_format,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )

    async def create_or_update_profile(self, profile: StudentProfile) -> StudentProfile:
        """Создать или обновить профиль студента."""
        async for session in get_session():
            result = await session.execute(
                select(UserProfileModel).where(
                    UserProfileModel.user_id == profile.user_id
                )
            )
            db_profile = result.scalar_one_or_none()

            if db_profile:
                db_profile.group_id = profile.group_id
                db_profile.student_id = profile.student_id
                db_profile.preferred_export_format = profile.preferred_format
            else:
                db_profile = UserProfileModel(
                    user_id=profile.user_id,
                    group_id=profile.group_id,
                    student_id=profile.student_id,
                    preferred_export_format=profile.preferred_format,
                )
                session.add(db_profile)

            await session.commit()
            await session.refresh(db_profile)

            logger.info("Upserted profile for user %s", profile.user_id)
            return StudentProfile(
                id=db_profile.user_id,
                user_id=db_profile.user_id,
                group_id=db_profile.group_id,
                student_id=db_profile.student_id,
                preferred_format=db_profile.preferred_export_format,
                created_at=db_profile.created_at,
                updated_at=db_profile.updated_at,
            )

    async def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Получить активную подписку пользователя."""
        # TODO: реализовать через SQLAlchemy
        return None

    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """Создать новую подписку."""
        # TODO: реализовать через SQLAlchemy
        return subscription

    async def update_user_group(self, telegram_id: int, group_id: int) -> bool:
        """Обновить группу пользователя."""
        try:
            async for session in get_session():
                result = await session.execute(
                    select(UserModel).where(UserModel.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    user.group_id = group_id
                    await session.commit()
                    logger.info(f"Updated user {telegram_id} group to {group_id}")
                    return True
                else:
                    logger.warning(f"User {telegram_id} not found for group update")
                    return False

        except Exception as e:
            logger.error(f"Error updating user group: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
        return False

    async def get_all_users(
        self, limit: int = 100, offset: int = 0
    ) -> List[User] | None:
        """Получить список всех пользователей."""
        async for session in get_session():
            result = await session.execute(
                select(UserModel).offset(offset).limit(limit)
            )
            db_users = result.scalars().all()
            return [self._to_user_model(user) for user in db_users]

    async def get_users_count(self) -> int:
        """Получить общее количество пользователей."""
        async for session in get_session():
            result = await session.execute(select(func.count(UserModel.id)))
            return result.scalar_one()

    def _to_user_model(self, db_user: UserModel) -> User:
        """Преобразовать SQLAlchemy-модель пользователя в Pydantic-модель."""
        full_name = db_user.first_name
        if db_user.last_name:
            full_name = f"{db_user.first_name} {db_user.last_name}".strip()

        try:
            level = AccessLevel(db_user.access_level)
        except ValueError:
            level = AccessLevel.GUEST

        last_seen = (
            db_user.last_seen.replace(tzinfo=timezone.utc)
            if db_user.last_seen
            else None
        )

        return User(
            id=db_user.id,
            telegram_id=db_user.telegram_id,
            telegram_username=db_user.username,
            full_name=full_name,
            access_level=level,
            is_active=db_user.is_active,
            selected_group_id=db_user.group_id,
            last_seen=last_seen,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )

    async def get_or_create_user(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Получить существующего пользователя или создать нового."""
        # Сначала пытаемся получить
        existing_user = await self.get_user_by_telegram_id(telegram_id)
        if existing_user:
            return existing_user

        # Если не найден, создаем нового
        return await self.create_user(telegram_id, telegram_username, full_name)

    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id (alias для get_user_by_telegram_id)."""
        return await self.get_user_by_telegram_id(telegram_id)

    async def set_user_group(self, telegram_id: int, group_id: int) -> bool:
        """Установить группу пользователя (alias для update_user_group)."""
        return await self.update_user_group(telegram_id, group_id)
