"""
Сервис для работы с системой инвайтов.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger

from app.database.connection import DatabaseConnection
from app.models.invitation import Invitation
from app.models.user import AccessLevel


class InvitationService:
    """Асинхронный сервис для управления инвайтами."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        self.db = db_connection or DatabaseConnection()

    def generate_invite_code(self, length: int = 8) -> str:
        """Сгенерировать уникальный код инвайта."""
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_invitation(
        self,
        created_by: int,
        access_level: AccessLevel = AccessLevel.BASIC,
        max_uses: Optional[int] = None,
        expires_in_days: Optional[int] = None,
        metadata: Optional[str] = None,
    ) -> Invitation:
        """Создать новый инвайт."""

        # Генерируем уникальный код
        code = self.generate_invite_code()

        # Проверяем уникальность кода
        async for conn in self.db.get_connection():
            while True:
                cursor = await conn.execute(
                    "SELECT id FROM invitations WHERE code = ?", (code,)
                )
                if not await cursor.fetchone():
                    break
                code = self.generate_invite_code()

        # Рассчитываем время истечения
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        invitation = Invitation(
            code=code,
            created_by=created_by,
            access_level=access_level,
            max_uses=max_uses,
            expires_at=expires_at,
            metadata=metadata,
        )

        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                INSERT INTO invitations 
                (code, created_by, access_level, max_uses, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    invitation.code,
                    invitation.created_by,
                    invitation.access_level.value,
                    invitation.max_uses,
                    invitation.expires_at,
                    invitation.metadata,
                ),
            )

            invitation.id = cursor.lastrowid
            await conn.commit()

        logger.info(f"Created invitation {invitation.code} by user {created_by}")
        return invitation

    async def get_invitation_by_code(self, code: str) -> Optional[Invitation]:
        """Получить инвайт по коду."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM invitations WHERE code = ?
            """,
                (code,),
            )

            row = await cursor.fetchone()
            if not row:
                return None

            invitation_dict = {
                "id": row[0],
                "code": row[1],
                "created_by": row[2],
                "access_level": row[3],
                "max_uses": row[4],
                "current_uses": row[5],
                "expires_at": row[6],
                "is_active": bool(row[7]),
                "metadata": row[8],
                "created_at": row[9],
            }

            return Invitation(**invitation_dict)

    async def validate_invitation(self, code: str) -> tuple[bool, str]:
        """Проверить валидность инвайта.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        invitation = await self.get_invitation_by_code(code)

        if not invitation:
            return False, "Инвайт не найден"

        if not invitation.is_active:
            return False, "Инвайт деактивирован"

        if invitation.expires_at and invitation.expires_at < datetime.now():
            return False, "Срок действия инвайта истек"

        if invitation.max_uses and invitation.current_uses >= invitation.max_uses:
            return False, "Инвайт исчерпал лимит использований"

        return True, ""

    async def use_invitation(
        self, code: str, user_id: int
    ) -> tuple[bool, str, Optional[AccessLevel]]:
        """Использовать инвайт.

        Returns:
            tuple[bool, str, AccessLevel]: (success, message, access_level)
        """
        # Проверяем валидность
        is_valid, error_msg = await self.validate_invitation(code)
        if not is_valid:
            return False, error_msg, None

        invitation = await self.get_invitation_by_code(code)
        if not invitation:
            return False, "Ошибка получения инвайта", None

        async for conn in self.db.get_connection():
            # Проверяем, не использовал ли уже этот пользователь этот инвайт
            cursor = await conn.execute(
                """
                SELECT id FROM invitation_usage 
                WHERE invitation_id = ? AND user_id = ?
            """,
                (invitation.id, user_id),
            )

            if await cursor.fetchone():
                return False, "Вы уже использовали этот инвайт", None

            # Записываем использование
            await conn.execute(
                """
                INSERT INTO invitation_usage (invitation_id, user_id)
                VALUES (?, ?)
            """,
                (invitation.id, user_id),
            )

            # Увеличиваем счетчик использований
            await conn.execute(
                """
                UPDATE invitations 
                SET current_uses = current_uses + 1
                WHERE id = ?
            """,
                (invitation.id,),
            )

            await conn.commit()

        logger.info(f"User {user_id} used invitation {code}")
        return True, "Инвайт успешно использован", invitation.access_level

    async def get_user_invitations(self, created_by: int) -> List[Invitation]:
        """Получить список инвайтов, созданных пользователем."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT * FROM invitations 
                WHERE created_by = ?
                ORDER BY created_at DESC
            """,
                (created_by,),
            )

            rows = await cursor.fetchall()
            invitations = []

            for row in rows:
                invitation_dict = {
                    "id": row[0],
                    "code": row[1],
                    "created_by": row[2],
                    "access_level": row[3],
                    "max_uses": row[4],
                    "current_uses": row[5],
                    "expires_at": row[6],
                    "is_active": bool(row[7]),
                    "metadata": row[8],
                    "created_at": row[9],
                }
                invitations.append(Invitation(**invitation_dict))

            return invitations

    async def deactivate_invitation(
        self, code: str, user_id: Optional[int] = None
    ) -> bool:
        """Деактивировать инвайт."""
        async for conn in self.db.get_connection():
            # Если указан user_id, проверяем права
            if user_id:
                cursor = await conn.execute(
                    """
                    SELECT created_by FROM invitations WHERE code = ?
                """,
                    (code,),
                )

                row = await cursor.fetchone()
                if not row or row[0] != user_id:
                    return False  # Нет прав на деактивацию

            cursor = await conn.execute(
                """
                UPDATE invitations 
                SET is_active = 0
                WHERE code = ?
            """,
                (code,),
            )

            await conn.commit()
            return cursor.rowcount > 0

    async def get_invitation_usage_stats(self, invitation_id: int) -> dict:
        """Получить статистику использования инвайта."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as total_uses,
                       MIN(used_at) as first_use,
                       MAX(used_at) as last_use
                FROM invitation_usage 
                WHERE invitation_id = ?
            """,
                (invitation_id,),
            )

            row = await cursor.fetchone()
            if not row:
                return {"total_uses": 0, "first_use": None, "last_use": None}

            return {"total_uses": row[0], "first_use": row[1], "last_use": row[2]}

    async def cleanup_expired_invitations(self) -> int:
        """Очистить истекшие инвайты."""
        async for conn in self.db.get_connection():
            cursor = await conn.execute(
                """
                UPDATE invitations 
                SET is_active = 0
                WHERE expires_at < ? AND is_active = 1
            """,
                (datetime.now(),),
            )

            await conn.commit()
            cleaned_count = cursor.rowcount

        if cleaned_count > 0:
            logger.info(f"Deactivated {cleaned_count} expired invitations")

        return cleaned_count
