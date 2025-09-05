"""
Модели пользователей и профилей.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import Field

from .base import BaseModel


class AccessLevel(str, Enum):
    """Уровни доступа пользователей."""
    GUEST = "guest"
    BASIC = "basic"
    TESTER = "tester"
    ADMIN = "admin"


class SubscriptionPlan(str, Enum):
    """Тарифные планы подписок."""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"


class User(BaseModel):
    """Модель пользователя Telegram."""
    
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    telegram_username: Optional[str] = Field(None, description="Username в Telegram")
    full_name: Optional[str] = Field(None, description="Полное имя пользователя")
    access_level: AccessLevel = Field(AccessLevel.GUEST, description="Уровень доступа")
    is_active: bool = Field(True, description="Активен ли пользователь")
    last_seen: Optional[datetime] = Field(None, description="Время последней активности")


class StudentProfile(BaseModel):
    """Профиль студента."""
    
    user_id: int = Field(..., description="ID пользователя")
    group_id: Optional[int] = Field(None, description="ID группы студента")
    student_id: Optional[str] = Field(None, description="Номер студенческого билета")
    preferred_format: str = Field("xlsx", description="Предпочитаемый формат файлов")


class Subscription(BaseModel):
    """Подписка пользователя."""
    
    user_id: int = Field(..., description="ID пользователя")
    plan: SubscriptionPlan = Field(..., description="Тарифный план")
    started_at: datetime = Field(default_factory=datetime.now, description="Начало подписки")
    expires_at: Optional[datetime] = Field(None, description="Окончание подписки")
    is_active: bool = Field(True, description="Активна ли подписка")
    auto_renewal: bool = Field(False, description="Автопродление")
    payment_method: Optional[str] = Field(None, description="Способ оплаты")
    subscription_id: Optional[str] = Field(None, description="ID в платежной системе")