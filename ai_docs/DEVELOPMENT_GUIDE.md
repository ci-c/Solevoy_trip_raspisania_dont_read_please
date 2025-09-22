# Руководство по разработке

## Настройка окружения

### 1. Установка зависимостей
```bash
# Установка uv (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установка зависимостей проекта
uv sync
```

### 2. Настройка переменных окружения
```bash
# Создать .env файл
cp .env.example .env

# Отредактировать .env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///data/szgmu_bot.db
LOG_LEVEL=INFO
```

### 3. Инициализация базы данных
```bash
# Создать директории
mkdir -p data logs

# Запустить бота (БД создастся автоматически)
uv run python -m app.bot.main
```

## Структура проекта

```
app/
├── bot/                    # Telegram Bot
│   ├── handlers/          # Обработчики команд
│   ├── middleware/        # Middleware
│   ├── keyboards.py       # Клавиатуры
│   ├── states.py          # FSM состояния
│   ├── callbacks.py       # Callback data factories
│   └── main.py           # Главный файл
├── database/              # База данных
│   ├── models.py         # SQLAlchemy модели
│   ├── session.py        # Сессии БД
│   └── repositories/     # Репозитории
├── models/                # Pydantic модели
│   ├── user.py           # Модели пользователей
│   ├── education.py      # Образовательные модели
│   ├── academic.py       # Академические модели
│   ├── base.py           # Базовые модели
│   ├── invitation.py     # Модели инвайтов
│   ├── schedule.py       # Модели расписания
│   └── system.py         # Системные модели
├── services/              # Бизнес-логика
│   ├── schedule_service.py
│   ├── group_service.py
│   ├── user_service.py
│   ├── faculty_service.py
│   ├── api_sync_service.py
│   ├── invitation_service.py
│   ├── education_service.py
│   ├── academic_service.py
│   └── grade_calculator_service.py
├── schedule/              # Работа с расписанием
│   ├── api_client.py     # Внешний API
│   ├── api.py            # API интерфейс
│   ├── faculty_api_client.py
│   ├── group_search.py   # Поиск групп
│   ├── semester_detector.py
│   └── models.py         # Модели расписания
└── utils/                 # Утилиты
    ├── logger.py         # Логирование
    ├── validators.py     # Система валидации
    ├── validation.py     # Валидация ввода
    ├── error_monitor.py  # Мониторинг ошибок
    ├── error_handling.py # Обработка ошибок
    ├── rate_limiter.py   # Ограничение запросов
    ├── disclaimer.py     # Дисклеймеры
    └── type_guard.py     # Проверка типов
```

## Принципы разработки

### 1. Код стиль
- Следуйте `CODESTYLE.md`
- Используйте встроенные типы Python 3.9+
- НЕ используйте `Any` - это запрещено
- Документируйте все функции
- Используйте современный SQLAlchemy синтаксис (Mapped)

### 2. Обработка ошибок
- Services возвращают `None` при ошибках (не падают)
- Handlers используют middleware для обработки ошибок
- Используйте `async_error_handler` декоратор
- Используйте `safe_execute_async` для безопасного выполнения
- Всегда логируйте ошибки с traceback

### 3. Типизация
- Строгая типизация всех функций
- Generic типизация в валидаторах
- Pydantic модели для структурированных данных
- SQLAlchemy модели с современным синтаксисом
- Runtime проверка в критических местах

### 4. Валидация
- Используйте систему валидации из `app/utils/validators.py`
- Выбирайте подходящий уровень валидации (STRICT/NORMAL/LENIENT)
- Обрабатывайте ValidationResult с ошибками и предупреждениями
- Валидируйте все пользовательские данные

### 5. Тестирование
- Unit тесты для каждого service
- Integration тесты для взаимодействий
- Тесты валидации с разными уровнями
- Покрытие критических путей

## Добавление новых функций

### 1. Добавление новой команды

#### Создать handler
```python
# app/bot/handlers/new_command_handler.py
from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

async def handle_new_command(message: types.Message, state: FSMContext) -> None:
    """Обработчик новой команды."""
    try:
        # Логика команды
        await message.answer("Новая команда!")
    except Exception as e:
        logger.error(f"Error in new command: {e}")
        # Ошибка обрабатывается в middleware
```

#### Зарегистрировать handler
```python
# app/bot/handlers/__init__.py
from .new_command_handler import handle_new_command

def register_handlers(dp: Dispatcher) -> None:
    # ... существующие handlers
    dp.message.register(handle_new_command, commands=["new_command"])
```

### 2. Добавление нового service

#### Создать service
```python
# app/services/new_service.py
from typing import List, Dict, Any
from loguru import logger
from app.utils.validators import StringValidator, ValidationLevel, async_error_handler
from app.utils.error_monitor import safe_execute_async

class NewService:
    """Новый сервис."""
    
    @async_error_handler(default_return=[], error_message="Failed to get data")
    async def get_data(self, param: str) -> List[Dict[str, Any]]:
        """Получить данные."""
        # Валидация входных данных
        validator = StringValidator(min_length=1, max_length=100, level=ValidationLevel.STRICT)
        result = validator.validate(param)
        
        if not result.is_valid:
            logger.error(f"Invalid param: {result.errors}")
            return []
        
        # Логика получения данных
        data = await self._fetch_data(result.data)
        
        # Валидация результата
        validated_data = []
        for item in data:
            # Используем валидацию для каждого элемента
            if self._is_valid_item(item):
                validated_data.append(item)
            else:
                logger.warning(f"Invalid data item: {item}")
        
        return validated_data
    
    def _is_valid_item(self, item: Dict[str, Any]) -> bool:
        """Проверить валидность элемента данных."""
        return isinstance(item, dict) and "id" in item and "name" in item
    
    async def _fetch_data(self, param: str) -> List[Dict[str, Any]]:
        """Получить данные из источника."""
        # Реализация получения данных
        return []
```

### 3. Добавление новой модели БД

#### Создать SQLAlchemy модель
```python
# app/database/models.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class NewModel(Base):
    """Новая модель."""
    __tablename__ = "new_models"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped[Optional["User"]] = relationship(back_populates="new_models")
```

#### Создать Pydantic модель
```python
# app/models/new_model.py
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import BaseModel

class NewModel(BaseModel):
    """Pydantic модель для новой сущности."""
    
    id: Optional[int] = Field(None, description="ID записи")
    name: str = Field(..., description="Название")
    description: Optional[str] = Field(None, description="Описание")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    user_id: Optional[int] = Field(None, description="ID пользователя")
```

#### Обновить связи
```python
# В модели User (SQLAlchemy)
new_models: Mapped[list["NewModel"]] = relationship(back_populates="user")
```

## Отладка

### 1. Использование дебаггера
```bash
# Запуск с дебаггером
uv run python -m app.bot.main
```

В VS Code:
1. Установите breakpoints
2. Нажмите F5
3. Выберите "Debug Bot"

### 2. Логирование
```python
from loguru import logger

# Разные уровни логирования
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### 3. Мониторинг ошибок
```python
from app.utils.error_monitor import get_error_stats

# Получить статистику ошибок
stats = get_error_stats()
print(f"Total errors: {stats['total_errors']}")
print(f"Blacklisted functions: {stats['blacklisted_functions']}")
```

### 4. Валидация данных
```python
from app.utils.validators import GroupDataValidator, ValidationLevel

# Строгая валидация
validator = GroupDataValidator(level=ValidationLevel.STRICT)
result = validator.validate({
    "id": "1",
    "name": "101",
    "faculty": "Лечебный",
    "speciality": "Лечебное дело",
    "course": "1"
})

if result.is_valid:
    print(f"Valid data: {result.data}")
else:
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
```

## Тестирование

### 1. Unit тесты
```python
# tests/unit/test_new_service.py
import pytest
from app.services.new_service import NewService
from app.utils.validators import ValidationLevel

@pytest.mark.asyncio
async def test_get_data():
    """Тест получения данных."""
    service = NewService()
    result = await service.get_data("test")
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_data_invalid_param():
    """Тест с невалидным параметром."""
    service = NewService()
    result = await service.get_data("")
    assert result == []

@pytest.mark.asyncio
async def test_validation():
    """Тест валидации данных."""
    from app.utils.validators import GroupDataValidator, ValidationLevel
    
    validator = GroupDataValidator(level=ValidationLevel.STRICT)
    result = validator.validate({
        "id": "1",
        "name": "101",
        "faculty": "Лечебный",
        "speciality": "Лечебное дело",
        "course": "1"
    })
    
    assert result.is_valid
    assert result.data is not None
```

### 2. Integration тесты
```python
# tests/integration/test_bot_flow.py
import pytest
from app.bot.main import create_bot_app

@pytest.mark.asyncio
async def test_bot_startup():
    """Тест запуска бота."""
    app = await create_bot_app()
    assert app is not None
```

### 3. Запуск тестов
```bash
# Запуск всех тестов
uv run pytest

# Запуск с покрытием
uv run pytest --cov=app

# Запуск конкретного теста
uv run pytest tests/unit/test_new_service.py
```

## Производительность

### 1. Оптимизация запросов к БД
```python
# Плохо - N+1 запросов
for user in users:
    group = await get_group(user.group_id)

# Хорошо - один запрос с JOIN
users_with_groups = await get_users_with_groups()
```

### 2. Кэширование
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param: str) -> str:
    """Дорогая операция с кэшированием."""
    return f"result_{param}"
```

### 3. Асинхронность
```python
# Плохо - последовательные запросы
result1 = await api_call_1()
result2 = await api_call_2()

# Хорошо - параллельные запросы
result1, result2 = await asyncio.gather(
    api_call_1(),
    api_call_2()
)
```

## Безопасность

### 1. Валидация входных данных
```python
from app.utils.validators import StringValidator, ValidationLevel

validator = StringValidator(
    min_length=1, 
    max_length=100, 
    level=ValidationLevel.STRICT
)
result = validator.validate(user_input)
if not result.is_valid:
    logger.warning(f"Invalid input: {result.errors}")
    return

# Используем валидированные данные
validated_input = result.data
```

### 2. Санитизация данных
```python
import html

def sanitize_html(text: str) -> str:
    """Очистить HTML теги."""
    return html.escape(text)
```

### 3. Защита секретов
```python
# НЕ ДЕЛАЙТЕ ТАК
logger.info(f"Token: {BOT_TOKEN}")

# ДЕЛАЙТЕ ТАК
logger.info("Token loaded successfully")
```

## Развертывание

### 1. Development
```bash
# Локальная разработка
uv run python -m app.bot.main
```

### 2. Production
```bash
# Продакшен с systemd
sudo systemctl start szgmu-bot
sudo systemctl enable szgmu-bot
```

### 3. Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync

CMD ["uv", "run", "python", "-m", "app.bot.main"]
```

## Мониторинг

### 1. Логи
```bash
# Просмотр логов
tail -f logs/bot.log

# Фильтрация ошибок
tail -f logs/errors.log | grep ERROR
```

### 2. Метрики
```python
# Добавление метрик
from app.utils.metrics import increment_counter

increment_counter("user_commands", {"command": "start"})
```

### 3. Алерты
```python
# Настройка алертов
if error_count > threshold:
    send_alert(f"High error rate: {error_count}")
```

## Troubleshooting

### 1. Бот не запускается
- Проверьте BOT_TOKEN в .env
- Проверьте логи в logs/bot.log
- Убедитесь что БД доступна

### 2. Ошибки в логах
- Проверьте logs/errors.log
- Используйте дебаггер
- Проверьте конфигурацию

### 3. Медленная работа
- Проверьте запросы к БД
- Используйте профилировщик
- Оптимизируйте алгоритмы

## Полезные команды

```bash
# Проверка кода
uv run ruff check app/
uv run mypy app/

# Форматирование
uv run ruff format app/

# Тесты
uv run pytest tests/

# Запуск бота
uv run python -m app.bot.main

# Просмотр логов
tail -f logs/bot.log
```
