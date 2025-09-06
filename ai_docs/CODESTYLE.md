# Кодстайл проекта СЗГМУ Bot

## Общие принципы

### 1. Структура и организация
- **Модульность**: Каждый компонент в отдельном модуле
- **Единая ответственность**: Один класс/функция = одна задача
- **Явные импорты**: Никаких `import *`
- **Логическая группировка**: Связанный код держать вместе

### 2. Именование
- **Переменные/функции**: `snake_case`
- **Классы**: `PascalCase` 
- **Константы**: `UPPER_SNAKE_CASE`
- **Приватные методы**: `_private_method`
- **Файлы/модули**: `snake_case.py`

### 3. Импорты
- **Только абсолютные импорты**: `from app.services.user_service import UserService`
- **Запрещены относительные импорты**: ~~`from .service import UserService`~~
- **Группировка импортов**: stdlib → third-party → local
- **Сортировка**: алфавитная внутри групп

```python
# ✅ Правильно - абсолютные импорты
import asyncio
from datetime import date
from typing import List, Optional

from aiogram import types
from loguru import logger

from app.services.user_service import UserService
from app.models.user import User

# ❌ Неправильно - относительные импорты  
from .services.user_service import UserService
from ..models.user import User
```

### 3. Типизация (строго обязательно)
```python
# ✅ Правильно - полная типизация
from typing import List, Dict, Optional, Union
from datetime import date

async def get_user_schedule(
    user_id: int, 
    start_date: date, 
    end_date: date
) -> List[Schedule]:
    """Получить расписание пользователя."""
    pass

# ❌ Неправильно - без типов
async def get_user_schedule(user_id, start_date, end_date):
    pass
```

### 4. Документация
- **Docstrings**: Для всех классов, методов и функций
- **Формат**: Google Style
- **Язык**: Русский для описания, английский для технических терминов

```python
def process_schedule_data(raw_data: Dict[str, Any]) -> Schedule:
    """
    Обработка сырых данных расписания.
    
    Args:
        raw_data: Словарь с данными от API СЗГМУ
        
    Returns:
        Объект Schedule с нормализованными данными
        
    Raises:
        ValidationError: При некорректных входных данных
        APIError: При ошибках API
    """
    pass
```

## Архитектурные паттерны

### 1. Сервисная архитектура
```python
# Каждый сервис отвечает за свою доменную область
class UserService:
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    async def create_user(self, user_data: UserCreateData) -> User:
        """Создание пользователя."""
        pass

class ScheduleService:
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    async def get_schedule(self, group_id: int) -> List[Schedule]:
        """Получение расписания."""
        pass
```

### 2. Dependency Injection
```python
# ✅ Инъекция зависимостей через конструктор
class BotHandler:
    def __init__(self, user_service: UserService, schedule_service: ScheduleService):
        self.user_service = user_service
        self.schedule_service = schedule_service

# ❌ Создание зависимостей внутри класса
class BadHandler:
    def __init__(self):
        self.user_service = UserService()  # Плохо
```

### 3. Обработка ошибок
```python
# ✅ Специфичные исключения с контекстом
class ScheduleNotFoundError(Exception):
    """Расписание не найдено."""
    def __init__(self, group_id: int):
        self.group_id = group_id
        super().__init__(f"Schedule not found for group {group_id}")

# ✅ Обработка с логированием
try:
    schedule = await schedule_service.get_schedule(group_id)
except ScheduleNotFoundError as e:
    logger.warning(f"Schedule not found: {e}")
    await message.answer("Расписание не найдено")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    await message.answer("Системная ошибка")
```

## Специфика для Telegram ботов

### 1. Обработчики (Handlers)
```python
async def handle_start_command(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.
    
    Args:
        message: Сообщение от пользователя
        state: Состояние FSM
    """
    user_id = message.from_user.id
    
    try:
        # Бизнес-логика в сервисах
        user_service = UserService()
        user = await user_service.get_or_create_user(user_id)
        
        # Простая логика отображения
        if user.has_profile:
            keyboard = get_main_menu_keyboard(user)
            text = f"Добро пожаловать, {user.name}!"
        else:
            keyboard = get_profile_setup_keyboard()
            text = "Настройте профиль для начала работы"
            
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer("Ошибка. Попробуйте позже.")
```

### 2. Клавиатуры
```python
# ✅ Генерация через builders с типизацией
def get_group_selection_keyboard(faculties: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора факультета."""
    builder = InlineKeyboardBuilder()
    
    for faculty in faculties:
        builder.button(
            text=f"🏛️ {faculty}", 
            callback_data=GroupCallback(action="select_faculty", value=faculty)
        )
    
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()
```

### 3. Callback Data
```python
# ✅ Структурированные callback с валидацией
class MenuCallback(CallbackData, prefix="menu"):
    action: str
    value: Optional[str] = None

class GroupCallback(CallbackData, prefix="group"):
    action: str
    group_id: Optional[int] = None
    faculty: Optional[str] = None
```

## База данных

### 1. Модели данных
```python
# ✅ Pydantic модели с валидацией
from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    id: int
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    name: Optional[str] = None
    group_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2. Сервисы БД
```python
class UserService:
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            )
            row = await cursor.fetchone()
            return User(**dict(row)) if row else None
```

## Логирование

### 1. Структура логов
```python
from loguru import logger

# ✅ Контекстные логи с метаданными
logger.info(
    "User schedule requested",
    extra={
        "user_id": user_id,
        "group_id": group_id,
        "week": week_number
    }
)

# ✅ Ошибки с трейсом
try:
    result = await api_call()
except APIError as e:
    logger.error(
        "API call failed",
        extra={
            "endpoint": e.endpoint,
            "status_code": e.status_code,
            "response": e.response
        }
    )
```

## Тестирование

### 1. Структура тестов
```python
# tests/services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, Mock

from app.services.user_service import UserService
from app.models.user import User, UserCreateData

class TestUserService:
    @pytest.fixture
    async def user_service(self):
        mock_db = AsyncMock()
        return UserService(db=mock_db)
    
    async def test_create_user_success(self, user_service):
        # Arrange
        user_data = UserCreateData(telegram_id=123, name="Test User")
        
        # Act
        user = await user_service.create_user(user_data)
        
        # Assert
        assert user.telegram_id == 123
        assert user.name == "Test User"
```

## Конфигурация

### 1. Настройки через Pydantic
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    database_url: str = Field(..., env="DATABASE_URL")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Форматирование и проверки

### 1. Обязательные инструменты
```bash
# Форматирование кода
ruff format .

# Проверка кода
ruff check .

# Типы
mypy .

# Тесты
pytest
```

### 2. Pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

## Производительность

### 1. Асинхронность
```python
# ✅ Параллельные запросы
async def get_full_user_data(user_id: int) -> UserFullData:
    """Получение полных данных пользователя."""
    user_task = user_service.get_user(user_id)
    schedule_task = schedule_service.get_user_schedule(user_id)
    grades_task = grade_service.get_user_grades(user_id)
    
    user, schedule, grades = await asyncio.gather(
        user_task, schedule_task, grades_task
    )
    
    return UserFullData(user=user, schedule=schedule, grades=grades)
```

### 2. Кэширование
```python
from functools import lru_cache
from typing import Dict, Any

class CachedScheduleService:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    @lru_cache(maxsize=128)
    async def get_semester_info(self) -> SemesterInfo:
        """Кэшированная информация о семестре."""
        pass
```

## Безопасность

### 1. Валидация входных данных
```python
from pydantic import BaseModel, Field, validator

class GroupSearchRequest(BaseModel):
    group_number: str = Field(..., min_length=1, max_length=10)
    
    @validator('group_number')
    def validate_group_number(cls, v):
        if not v.replace('а', '').replace('б', '').replace('в', '').isdigit():
            raise ValueError('Некорректный номер группы')
        return v.lower()
```

### 2. Ограничение доступа
```python
async def require_profile(user_id: int) -> User:
    """Проверка наличия профиля пользователя."""
    user = await user_service.get_user(user_id)
    if not user or not user.has_profile:
        raise AccessDeniedError("Профиль не настроен")
    return user
```

---

**Принципы кода:**
- 🎯 **Простота**: Код должен быть понятен
- 🔒 **Типобезопасность**: Строгая типизация везде
- ⚡ **Производительность**: Асинхронность и кэширование
- 🛡️ **Надежность**: Обработка всех ошибок
- 📝 **Документированность**: Каждая функция описана
- 🧪 **Тестируемость**: Легко писать тесты