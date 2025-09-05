"""
Модели системы инвайтов.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from .base import BaseModel
from .user import AccessLevel


class Invitation(BaseModel):
    """Модель инвайта."""
    
    code: str = Field(..., description="Код инвайта")
    created_by: int = Field(..., description="ID создателя инвайта")
    access_level: AccessLevel = Field(AccessLevel.BASIC, description="Уровень доступа по инвайту")
    max_uses: Optional[int] = Field(None, description="Максимальное количество использований")
    current_uses: int = Field(0, description="Текущее количество использований")
    expires_at: Optional[datetime] = Field(None, description="Время истечения инвайта")
    is_active: bool = Field(True, description="Активен ли инвайт")
    metadata: Optional[str] = Field(None, description="Дополнительная информация в JSON")


class InvitationUsage(BaseModel):
    """Использование инвайта пользователем."""
    
    invitation_id: int = Field(..., description="ID инвайта")
    user_id: int = Field(..., description="ID пользователя")
    used_at: datetime = Field(default_factory=datetime.now, description="Время использования")