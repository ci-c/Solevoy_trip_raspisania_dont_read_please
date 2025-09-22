# Руководство по обработке ошибок

## Обзор

Система обработки ошибок SZGMU Bot построена на принципах:
- **Graceful degradation** - система не падает при ошибках
- **Детальное логирование** - все ошибки записываются с контекстом
- **Пользовательский опыт** - понятные сообщения об ошибках
- **Мониторинг** - отслеживание повторяющихся ошибок

## Архитектура обработки ошибок

### Уровни обработки

1. **Validation Layer** - Валидация входных данных
2. **Service Layer** - Возврат пустых значений при ошибках
3. **Handler Layer** - Middleware для обработки ошибок
4. **User Layer** - Понятные сообщения пользователю

### Принципы

- **Services НЕ падают** - возвращают `None` при ошибках
- **Handlers проверяют** `None` и обрабатывают ошибки
- **Middleware** - единственное место где глотаются ошибки
- **Логирование** - все ошибки записываются с traceback

## Компоненты системы

### 1. ErrorHandlerMiddleware

```python
from app.bot.middleware.error_handler_middleware import ErrorHandlerMiddleware

# Регистрация middleware
dp.middleware.setup(ErrorHandlerMiddleware())
```

**Функции:**
- Глобальная обработка ошибок
- Логирование всех исключений
- Отправка уведомлений пользователю
- Предотвращение падения бота

### 2. async_error_handler

```python
from app.utils.error_monitor import async_error_handler

@async_error_handler(default_return=None, error_message="Failed to get data")
async def get_user_data(user_id: int) -> dict[str, Any] | None:
    """Получить данные пользователя."""
    # Реализация функции
    pass
```

**Параметры:**
- `default_return` - значение по умолчанию при ошибке
- `error_message` - сообщение для логирования

### 3. safe_execute_async

```python
from app.utils.error_monitor import safe_execute_async

result = await safe_execute_async(
    risky_function,
    arg1, arg2,
    default=[],
    error_message="Function failed",
    context={"user_id": 12345}
)
```

**Параметры:**
- `func` - функция для выполнения
- `*args` - аргументы функции
- `default` - значение по умолчанию
- `error_message` - сообщение об ошибке
- `context` - контекст для логирования

### 4. safe_execute

```python
from app.utils.validators import safe_execute

result = safe_execute(
    risky_function,
    arg1, arg2,
    default=None,
    error_message="Operation failed"
)
```

## Использование в сервисах

### Базовый паттерн

```python
from app.utils.error_monitor import async_error_handler
from loguru import logger

class UserService:
    @async_error_handler(default_return=None, error_message="Failed to get user")
    async def get_user(self, user_id: int) -> User | None:
        """Получить пользователя."""
        try:
            # Валидация входных данных
            if not user_id or user_id <= 0:
                logger.error(f"Invalid user_id: {user_id}")
                return None
            
            # Логика получения пользователя
            user = await self._fetch_user(user_id)
            return user
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            logger.error(f"Traceback: {e.__traceback__}")
            return None
    
    async def _fetch_user(self, user_id: int) -> User | None:
        """Получить пользователя из БД."""
        # Реализация
        pass
```

### Обработка ошибок валидации

```python
from app.utils.validators import GroupDataValidator, ValidationLevel

class GroupService:
    async def create_group(self, group_data: dict) -> dict | None:
        """Создать группу."""
        try:
            # Валидация данных
            validator = GroupDataValidator(level=ValidationLevel.STRICT)
            result = validator.validate(group_data)
            
            if not result.is_valid:
                logger.error(f"Validation failed: {result.errors}")
                return None
            
            # Создание группы с валидированными данными
            group = await self._create_group_in_db(result.data)
            return group
            
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return None
```

## Использование в обработчиках

### Базовый паттерн

```python
from aiogram import types
from app.services.user_service import UserService

async def handle_get_profile(callback: types.CallbackQuery) -> None:
    """Обработчик получения профиля."""
    try:
        user_service = UserService()
        user = await user_service.get_user(callback.from_user.id)
        
        if user is None:
            await callback.message.edit_text(
                "❌ Не удалось получить данные профиля"
            )
            return
        
        # Отображение профиля
        await show_user_profile(callback.message, user)
        
    except Exception as e:
        logger.error(f"Error in handle_get_profile: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при получении профиля"
        )
```

### Обработка с проверкой результата

```python
async def handle_get_schedule(callback: types.CallbackQuery) -> None:
    """Обработчик получения расписания."""
    try:
        schedule_service = ScheduleService()
        lessons = await schedule_service.get_user_schedule(callback.from_user.id)
        
        # Проверка результата
        if lessons is None:
            await callback.message.edit_text(
                "❌ Не удалось получить расписание. Попробуйте позже."
            )
            return
        
        if not lessons:
            await callback.message.edit_text(
                "📅 Расписание пусто"
            )
            return
        
        # Отображение расписания
        await show_schedule(callback.message, lessons)
        
    except Exception as e:
        logger.error(f"Error in handle_get_schedule: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при получении расписания"
        )
```

## Мониторинг ошибок

### Получение статистики

```python
from app.utils.error_monitor import get_error_stats

# Получить статистику ошибок
stats = get_error_stats()
print(f"Total errors: {stats['total_errors']}")
print(f"Blacklisted functions: {stats['blacklisted_functions']}")
print(f"Error rate: {stats['error_rate']}")
```

### Логирование контекста

```python
from app.utils.error_handling import log_error_context

async def risky_operation(user_id: int, data: dict) -> None:
    """Рисковая операция с логированием контекста."""
    try:
        # Операция
        pass
    except Exception as e:
        log_error_context(
            func_name="risky_operation",
            user_id=user_id,
            additional_data={"data_keys": list(data.keys())}
        )
        raise
```

## Пользовательские сообщения

### Типы ошибок

```python
class ErrorMessages:
    """Сообщения об ошибках для пользователей."""
    
    # Общие ошибки
    GENERAL_ERROR = "❌ Произошла ошибка. Попробуйте позже."
    NETWORK_ERROR = "🌐 Ошибка сети. Проверьте подключение."
    VALIDATION_ERROR = "⚠️ Некорректные данные."
    
    # Специфичные ошибки
    USER_NOT_FOUND = "👤 Пользователь не найден."
    GROUP_NOT_FOUND = "👥 Группа не найдена."
    SCHEDULE_NOT_FOUND = "📅 Расписание не найдено."
    PERMISSION_DENIED = "🔒 Недостаточно прав доступа."
```

### Обработка разных типов ошибок

```python
from app.utils.error_handling import ErrorMessages

async def handle_error(error: Exception, context: dict) -> str:
    """Обработать ошибку и вернуть сообщение пользователю."""
    
    if isinstance(error, ValidationError):
        return ErrorMessages.VALIDATION_ERROR
    
    elif isinstance(error, NetworkError):
        return ErrorMessages.NETWORK_ERROR
    
    elif isinstance(error, PermissionError):
        return ErrorMessages.PERMISSION_DENIED
    
    elif "user not found" in str(error).lower():
        return ErrorMessages.USER_NOT_FOUND
    
    elif "group not found" in str(error).lower():
        return ErrorMessages.GROUP_NOT_FOUND
    
    else:
        logger.error(f"Unhandled error: {error}")
        return ErrorMessages.GENERAL_ERROR
```

## Лучшие практики

### 1. Всегда проверяйте None

```python
# ✅ Правильно
user = await user_service.get_user(user_id)
if user is None:
    await message.answer("❌ Пользователь не найден")
    return

# ❌ Неправильно
user = await user_service.get_user(user_id)
await message.answer(f"Привет, {user.name}")  # Может упасть
```

### 2. Логируйте с контекстом

```python
# ✅ Правильно
logger.error(f"Error getting user {user_id}: {e}")
logger.error(f"Context: {context}")

# ❌ Неправильно
logger.error(f"Error: {e}")
```

### 3. Используйте декораторы

```python
# ✅ Правильно
@async_error_handler(default_return=None, error_message="Failed to get data")
async def get_data() -> dict | None:
    pass

# ❌ Неправильно
async def get_data() -> dict | None:
    try:
        # код
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
```

### 4. Обрабатывайте специфичные ошибки

```python
# ✅ Правильно
try:
    result = await risky_operation()
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    return None
except NetworkError as e:
    logger.error(f"Network error: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return None
```

## Тестирование обработки ошибок

### Unit тесты

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.user_service import UserService

@pytest.mark.asyncio
async def test_get_user_handles_error():
    """Тест обработки ошибки в get_user."""
    service = UserService()
    
    # Мокаем метод, который падает
    with patch.object(service, '_fetch_user', side_effect=Exception("DB Error")):
        result = await service.get_user(123)
        assert result is None

@pytest.mark.asyncio
async def test_get_user_handles_validation_error():
    """Тест обработки ошибки валидации."""
    service = UserService()
    
    # Передаем невалидные данные
    result = await service.get_user(-1)
    assert result is None
```

### Integration тесты

```python
@pytest.mark.asyncio
async def test_handler_handles_service_error():
    """Тест обработки ошибки сервиса в handler."""
    # Мокаем сервис, который возвращает None
    with patch('app.services.user_service.UserService.get_user', return_value=None):
        # Тестируем handler
        # Проверяем, что пользователь получил сообщение об ошибке
        pass
```

## Отладка

### Включение детального логирования

```python
import logging
from loguru import logger

# Настройка уровня логирования
logger.add("logs/debug.log", level="DEBUG")

# В коде
logger.debug(f"Debug info: {debug_data}")
logger.info(f"Info: {info_data}")
logger.warning(f"Warning: {warning_data}")
logger.error(f"Error: {error_data}")
```

### Просмотр логов

```bash
# Просмотр всех логов
tail -f logs/bot.log

# Просмотр только ошибок
tail -f logs/errors.log | grep ERROR

# Поиск по пользователю
grep "user_id=12345" logs/bot.log
```
