# Руководство по дебаггингу

## Настройка дебаггера в Cursor IDE

### 1. Конфигурация VS Code
Файл `.vscode/launch.json` уже настроен для дебаггинга:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app/bot/main.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "PYTHONUNBUFFERED": "1"
            },
            "justMyCode": false,
            "stopOnEntry": false
        }
    ]
}
```

### 2. Как использовать дебаггер

1. **Установите breakpoints** - кликните слева от номера строки
2. **Запустите дебаггер** - F5 или через меню Run > Start Debugging
3. **Выберите конфигурацию** - "Debug Bot"
4. **Используйте панель отладки** - Variables, Watch, Call Stack

### 3. Горячие клавиши
- `F5` - Запустить/продолжить дебаггинг
- `F10` - Step Over (следующая строка)
- `F11` - Step Into (войти в функцию)
- `Shift+F11` - Step Out (выйти из функции)
- `Ctrl+Shift+F5` - Restart debugging

## Архитектура защиты от runtime ошибок

### 1. Система валидации (`app/utils/validators.py`)

```python
from app.utils.validators import validate_group_data, safe_execute

# Валидация данных группы
result = validate_group_data(group_data)
if not result.is_valid:
    logger.error(f"Validation failed: {result.errors}")
    return None

# Безопасное выполнение функций
data = safe_execute(
    risky_function,
    arg1, arg2,
    default=None,
    error_message="Function failed"
)
```

### 2. Мониторинг ошибок (`app/utils/error_monitor.py`)

```python
from app.utils.error_monitor import async_error_handler, get_error_stats

@async_error_handler(default_return=None, error_message="Operation failed")
async def risky_operation():
    # Код функции
    pass

# Получить статистику ошибок
stats = get_error_stats()
print(f"Total errors: {stats['total_errors']}")
```

### 3. Проверка типов (`app/utils/type_guard.py`)

```python
from app.utils.type_guard import runtime_type_check, ensure_type

@runtime_type_check
def typed_function(value: str) -> int:
    return int(value)

# Гарантировать тип
safe_value = ensure_type(user_input, str, fallback="default")
```

## Предотвращение типичных ошибок

### 1. Ошибки с типами данных
- ✅ Всегда валидируйте входные данные
- ✅ Используйте `ensure_type()` для преобразования типов
- ✅ Проверяйте `None` значения перед использованием

### 2. Ошибки базы данных
- ✅ Используйте `safe_execute_async()` для DB операций
- ✅ Всегда проверяйте результат на `None`
- ✅ Используйте транзакции с rollback

### 3. Ошибки Telegram API
- ✅ Обрабатывайте `BadRequest` исключения
- ✅ Проверяйте статус сообщений перед редактированием
- ✅ Используйте retry логику для временных сбоев

## Мониторинг в реальном времени

### 1. Логи ошибок
```bash
# Следить за ошибками
tail -f logs/errors.log

# Следить за всеми логами
tail -f logs/bot.log

# Фильтровать по типу ошибки
tail -f logs/bot.log | grep -E "(ERROR|WARNING)"
```

### 2. Статистика ошибок
```python
from app.utils.error_monitor import get_error_stats

stats = get_error_stats()
print(f"Blacklisted functions: {stats['blacklisted_functions']}")
print(f"Recent errors: {stats['recent_errors_count']}")
```

## Отладка конкретных проблем

### 1. Проблема с выбором группы
```python
# В group_service.py добавьте детальное логирование
logger.debug(f"Group number: {group_number}, type: {type(group_number)}")
logger.debug(f"Database result: {result}")
logger.debug(f"Group object: {group}")
```

### 2. Проблема с callback'ами
```python
# В handlers добавьте логирование callback данных
logger.debug(f"Callback data: {callback.data}")
logger.debug(f"Callback type: {type(callback.data)}")
```

### 3. Проблема с состояниями FSM
```python
# Проверяйте текущее состояние пользователя
state = await state.get_state()
logger.debug(f"Current state: {state}")
```

## Лучшие практики

1. **Всегда используйте try-catch** для внешних вызовов
2. **Валидируйте данные** на входе в функции
3. **Логируйте ошибки** с контекстом
4. **Используйте дебаггер** вместо print statements
5. **Тестируйте edge cases** - пустые строки, None, неожиданные типы
6. **Мониторьте производительность** - медленные запросы к БД
7. **Документируйте ошибки** - что пошло не так и как исправить

## Инструменты для дебаггинга

1. **VS Code Debugger** - основной инструмент
2. **Loguru** - структурированное логирование
3. **pdb** - Python debugger в коде
4. **ipdb** - улучшенный pdb с IPython
5. **pytest** - тестирование с отладкой

## Примеры дебаггинга

### Отладка callback'а
```python
@dp.callback_query_handler(GroupCallback.filter())
async def handle_group_selection(callback: CallbackQuery, callback_data: dict):
    try:
        logger.debug(f"Callback received: {callback_data}")
        # Ваш код
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
```

### Отладка FSM состояний
```python
async def some_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    logger.debug(f"Current state: {current_state}")
    
    if current_state != "expected_state":
        logger.warning(f"Unexpected state: {current_state}")
        await state.reset_state()
```

Этот подход гарантирует, что runtime ошибки будут минимальными, а дебаггинг - эффективным!
