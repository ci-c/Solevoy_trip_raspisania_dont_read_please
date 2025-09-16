"""
Сервис для работы с пользователями и профилями через SQLAlchemy.
"""

from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger
from sqlalchemy import select

from app.database.session import get_session
from app.database.models import User as UserModel
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
        
        async for session in get_session():
            # Создаем SQLAlchemy модель
            db_user = UserModel(
                telegram_id=telegram_id,
                username=telegram_username,
                first_name=full_name or "",
                last_name=None,
            )
            
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            
            # Конвертируем в Pydantic модель
            user = User(
                id=db_user.id,
                telegram_id=db_user.telegram_id,
                telegram_username=db_user.username,
                full_name=db_user.first_name,
                access_level=AccessLevel.GUEST,  # По умолчанию
                is_active=True,
                last_seen=now,
            )
            
            logger.info(f"Created new user {user.id} (telegram_id: {telegram_id})")
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
            
            return User(
                id=db_user.id,
                telegram_id=db_user.telegram_id,
                telegram_username=db_user.username,
                full_name=db_user.first_name,
                access_level=AccessLevel.GUEST,  # TODO: добавить поле в модель
                is_active=True,
                last_seen=datetime.now(tz=timezone.utc),
            )

    async def update_user_activity(self, user_id: int) -> None:
        """Обновить время последней активности пользователя."""
        # TODO: добавить поле last_seen в модель User
        pass

    async def update_user_access_level(
        self, user_id: int, access_level: AccessLevel
    ) -> bool:
        """Обновить уровень доступа пользователя."""
        # TODO: добавить поле access_level в модель User
        return True

    async def get_user_profile(self, user_id: int) -> Optional[StudentProfile]:
        """Получить профиль студента."""
        # TODO: реализовать через SQLAlchemy
        return None

    async def create_or_update_profile(self, profile: StudentProfile) -> StudentProfile:
        """Создать или обновить профиль студента."""
        # TODO: реализовать через SQLAlchemy
        return profile

    async def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Получить активную подписку пользователя."""
        # TODO: реализовать через SQLAlchemy
        return None

    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """Создать новую подписку."""
        # TODO: реализовать через SQLAlchemy
        return subscription

    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Получить список всех пользователей."""
        async for session in get_session():
            result = await session.execute(
                select(UserModel).offset(offset).limit(limit)
            )
            db_users = result.scalars().all()
            
            users = []
            for db_user in db_users:
                users.append(User(
                    id=db_user.id,
                    telegram_id=db_user.telegram_id,
                    telegram_username=db_user.username,
                    full_name=db_user.first_name,
                    access_level=AccessLevel.GUEST,
                    is_active=True,
                    last_seen=datetime.now(tz=timezone.utc),
                ))
            
            return users

    async def get_users_count(self) -> int:
        """Получить общее количество пользователей."""
        async for session in get_session():
            result = await session.execute(select(UserModel))
            return len(result.scalars().all())