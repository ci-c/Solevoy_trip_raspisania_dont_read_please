"""Системные модели."""

from datetime import datetime

from pydantic import Field

from .base import BaseModel


class Setting(BaseModel):
    """Системная настройка."""

    key: str = Field(..., description="Ключ настройки")
    value: str | None = Field(None, description="Значение")
    description: str | None = Field(None, description="Описание настройки")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Время обновления",
    )


class ActivityLog(BaseModel):
    """Лог активности пользователя."""

    user_id: int | None = Field(None, description="ID пользователя")
    action: str = Field(..., description="Выполненное действие")
    details: str | None = Field(None, description="Детали в JSON")
    ip_address: str | None = Field(None, description="IP адрес")
    user_agent: str | None = Field(None, description="User Agent")


class SearchCache(BaseModel):
    """Кэш поисковых запросов."""

    query_hash: str = Field(..., description="Хеш запроса")
    query_params: str | None = Field(None, description="Параметры запроса в JSON")
    results: str | None = Field(None, description="Результаты в JSON")
    expires_at: datetime = Field(..., description="Время истечения кэша")
