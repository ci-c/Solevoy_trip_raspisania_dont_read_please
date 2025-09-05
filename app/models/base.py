"""
Базовая модель для всех сущностей.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    """Базовая модель с общими полями."""
    
    id: Optional[int] = Field(None, description="Уникальный идентификатор")
    created_at: Optional[datetime] = Field(None, description="Время создания записи")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")
    
    class Config:
        from_attributes = True
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def dict_for_db(self, exclude_none: bool = True) -> dict:
        """Преобразовать модель в словарь для сохранения в БД."""
        return self.model_dump(
            exclude_none=exclude_none,
            exclude={'id'} if not self.id else set()
        )