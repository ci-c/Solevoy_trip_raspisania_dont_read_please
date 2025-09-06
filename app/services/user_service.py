"""
Сервис для работы с пользователями и профилями.
"""

from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger

from app.database.connection import DatabaseConnection
from app.models.user import User, StudentProfile, Subscription, AccessLevel


class UserService:
    """Асинхронный сервис для управления пользователями."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        self.db = db_connection or DatabaseConnection()

    async def create_user(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Создать нового пользователя."""
        now = datetime.now(tz=timezone.utc)
        user = User(
            id=None,  # Will be set after DB insert
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            full_name=full_name,
            access_level=AccessLevel.GUEST,
            created_at=now,
            updated_at=now,
            is_active=True,
            last_seen=now,
        )

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                INSERT INTO users (telegram_id, telegramaccess_level_username, full_name, access_level, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user.telegram_id,
                    user.telegram_username,
                    user.full_name,
                    user.access_level,
                    user.last_seen,
                ),
            )

            user.id = cursor.lastrowid
            await conn.commit()

        logger.info(f"Created new user {user.id} (telegram_id: {telegram_id})")
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM users WHERE telegram_id = ?
            """,
                (telegram_id,),
            )

            row = await cursor.fetchone()
            if not row:
                return None

            # Конвертируем row в словарь
            user_dict = {
                "id": row[0],
                "telegram_id": row[1],
                "telegram_username": row[2],
                "full_name": row[3],
                "access_level": AccessLevel(row[4]) if row[4] else AccessLevel.GUEST,
                "created_at": row[5],
                "updated_at": row[6],
                "is_active": bool(row[7]),
                "last_seen": row[8],
            }

            return User(**user_dict)

    async def update_user_activity(self, user_id: int) -> None:
        """Обновить время последней активности пользователя."""
        async for conn in self.db.get_connection():
            await conn.execute(
                """
                UPDATE users SET last_seen = ? WHERE id = ?
            """,
                (datetime.now(), user_id),
            )
            await conn.commit()

    async def update_user_access_level(
        self, user_id: int, access_level: AccessLevel
    ) -> bool:
        """Обновить уровень доступа пользователя."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                UPDATE users SET access_level = ? WHERE id = ?
            """,
                (access_level.value, user_id),
            )
            await conn.commit()

            return cursor.rowcount > 0

    async def get_user_profile(self, user_id: int) -> Optional[StudentProfile]:
        """Получить профиль студента."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM student_profiles WHERE user_id = ?
            """,
                (user_id,),
            )

            row = await cursor.fetchone()
            if not row:
                return None

            profile_dict = {
                "id": row[0],
                "user_id": row[1],
                "group_id": row[2],
                "student_id": row[3],
                "preferred_format": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }

            return StudentProfile(**profile_dict)

    async def create_or_update_profile(self, profile: StudentProfile) -> StudentProfile:
        """Создать или обновить профиль студента."""
        async for conn in self.db.get_connection():
            # Проверяем существует ли профиль
            cursor = await conn.execute(
                """
                SELECT id FROM student_profiles WHERE user_id = ?
            """,
                (profile.user_id,),
            )

            existing = await cursor.fetchone()

            if existing:
                # Обновляем существующий
                await conn.execute(
                    """
                    UPDATE student_profiles 
                    SET group_id = ?, student_id = ?, preferred_format = ?, updated_at = ?
                    WHERE user_id = ?
                """,
                    (
                        profile.group_id,
                        profile.student_id,
                        profile.preferred_format,
                        datetime.now(),
                        profile.user_id,
                    ),
                )
                profile.id = existing[0]
            else:
                # Создаем новый
                cursor = await conn.execute(
                    """
                    INSERT INTO student_profiles (user_id, group_id, student_id, preferred_format)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        profile.user_id,
                        profile.group_id,
                        profile.student_id,
                        profile.preferred_format,
                    ),
                )
                profile.id = cursor.lastrowid

            await conn.commit()

        logger.info(f"Created/updated profile for user {profile.user_id}")
        return profile

    async def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Получить активную подписку пользователя."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC LIMIT 1
            """,
                (user_id,),
            )

            row = await cursor.fetchone()
            if not row:
                return None

            subscription_dict = {
                "id": row[0],
                "user_id": row[1],
                "plan": row[2],
                "started_at": row[3],
                "expires_at": row[4],
                "is_active": bool(row[5]),
                "auto_renewal": bool(row[6]),
                "payment_method": row[7],
                "subscription_id": row[8],
                "created_at": row[9],
            }

            return Subscription(**subscription_dict)

    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """Создать новую подписку."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                INSERT INTO subscriptions 
                (user_id, plan, started_at, expires_at, is_active, auto_renewal, payment_method, subscription_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    subscription.user_id,
                    subscription.plan.value,
                    subscription.started_at,
                    subscription.expires_at,
                    subscription.is_active,
                    subscription.auto_renewal,
                    subscription.payment_method,
                    subscription.subscription_id,
                ),
            )

            subscription.id = cursor.lastrowid
            await conn.commit()

        logger.info(
            f"Created subscription {subscription.id} for user {subscription.user_id}"
        )
        return subscription

    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Получить список всех пользователей."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM users 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            rows = await cursor.fetchall()
            users = []

            for row in rows:
                user_dict = {
                    "id": row[0],
                    "telegram_id": row[1],
                    "telegram_username": row[2],
                    "full_name": row[3],
                    "access_level": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "is_active": bool(row[7]),
                    "last_seen": row[8],
                }
                users.append(User(**user_dict))

            return users

    async def get_users_count(self) -> int:
        """Получить общее количество пользователей."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
            return result[0] if result else 0
