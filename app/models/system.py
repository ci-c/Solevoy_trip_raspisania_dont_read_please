"""
Системные модели.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from .base import BaseModel


class Setting(BaseModel):
    """Системная настройка."""

    key: str = Field(..., description="Ключ настройки")
    value: Optional[str] = Field(None, description="Значение")
    description: Optional[str] = Field(None, description="Описание настройки")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Время обновления"
    )


class ActivityLog(BaseModel):
    """Лог активности пользователя."""

    user_id: Optional[int] = Field(None, description="ID пользователя")
    action: str = Field(..., description="Выполненное действие")
    details: Optional[str] = Field(None, description="Детали в JSON")
    ip_address: Optional[str] = Field(None, description="IP адрес")
    user_agent: Optional[str] = Field(None, description="User Agent")


class SearchCache(BaseModel):
    """Кэш поисковых запросов."""

    query_hash: str = Field(..., description="Хеш запроса")
    query_params: Optional[str] = Field(None, description="Параметры запроса в JSON")
    results: Optional[str] = Field(None, description="Результаты в JSON")
    expires_at: datetime = Field(..., description="Время истечения кэша")
