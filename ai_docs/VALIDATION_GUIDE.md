# Руководство по системе валидации

## Обзор

Система валидации SZGMU Bot построена на принципах:
- **Generic типизация** - строгая типизация с поддержкой generic типов
- **Уровни валидации** - гибкая настройка строгости проверок
- **Детальная отчетность** - подробные ошибки и предупреждения
- **Безопасность** - защита от runtime ошибок

## Базовые компоненты

### ValidationLevel

```python
class ValidationLevel(Enum):
    STRICT = "strict"      # Строгая валидация
    NORMAL = "normal"      # Обычная валидация  
    LENIENT = "lenient"    # Мягкая валидация
```

### ValidationResult

```python
@dataclass
class ValidationResult(Generic[T]):
    is_valid: bool         # Успешность валидации
    data: T | None         # Валидированные данные
    errors: list[str]      # Список ошибок
    warnings: list[str]    # Список предупреждений
```

### BaseValidator

```python
class BaseValidator(Generic[T]):
    def validate(self, data: Any) -> ValidationResult[T]
```

## Валидаторы

### StringValidator

Валидатор строк с поддержкой:
- Минимальной/максимальной длины
- Регулярных выражений
- Пустых значений
- Разных уровней валидации

```python
from app.utils.validators import StringValidator, ValidationLevel

# Строгая валидация
validator = StringValidator(
    min_length=1,
    max_length=50,
    pattern=r"^\d+$",
    allow_empty=False,
    level=ValidationLevel.STRICT
)

result = validator.validate("123")
if result.is_valid:
    print(f"Valid data: {result.data}")
else:
    print(f"Errors: {result.errors}")
```

### IntegerValidator

Валидатор целых чисел с поддержкой:
- Диапазонов значений
- Автоматического преобразования типов
- Разных уровней валидации

```python
from app.utils.validators import IntegerValidator, ValidationLevel

validator = IntegerValidator(
    min_value=1,
    max_value=100,
    level=ValidationLevel.NORMAL
)

result = validator.validate("50")
if result.is_valid:
    print(f"Valid number: {result.data}")
```

### DictValidator

Валидатор словарей с поддержкой:
- Обязательных и опциональных ключей
- Валидации значений по ключам
- Вложенной валидации

```python
from app.utils.validators import DictValidator, StringValidator, IntegerValidator

validator = DictValidator(
    required_keys={"id", "name", "age"},
    optional_keys={"email", "phone"},
    key_validators={
        "id": IntegerValidator(min_value=1),
        "name": StringValidator(min_length=1, max_length=100),
        "age": IntegerValidator(min_value=0, max_value=120),
        "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    }
)

result = validator.validate({
    "id": 1,
    "name": "Иван",
    "age": 25,
    "email": "ivan@example.com"
})
```

## Специализированные валидаторы

### GroupDataValidator

Валидатор данных группы студентов:

```python
from app.utils.validators import GroupDataValidator, ValidationLevel

validator = GroupDataValidator(level=ValidationLevel.STRICT)
result = validator.validate({
    "id": "1",
    "name": "101",
    "faculty": "Лечебный",
    "speciality": "Лечебное дело",
    "course": "1"
})

if result.is_valid:
    group_data = result.data
    print(f"Valid group: {group_data}")
else:
    print(f"Validation errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
```

### UserDataValidator

Валидатор данных пользователя:

```python
from app.utils.validators import UserDataValidator, ValidationLevel

validator = UserDataValidator(level=ValidationLevel.NORMAL)
result = validator.validate({
    "telegram_id": 12345,
    "group_id": 1,
    "subscription_type": "free"
})
```

## Утилиты валидации

### safe_execute

Безопасное выполнение функций с обработкой ошибок:

```python
from app.utils.validators import safe_execute

def risky_function(x: int, y: int) -> int:
    return x / y

result = safe_execute(
    risky_function,
    10, 0,
    default=0,
    error_message="Division by zero"
)
print(f"Result: {result}")  # 0
```

### validate_group_data

Быстрая валидация данных группы:

```python
from app.utils.validators import validate_group_data

result = validate_group_data({
    "id": "1",
    "name": "101",
    "faculty": "Лечебный",
    "speciality": "Лечебное дело",
    "course": "1"
})

if result.is_valid:
    group_data = result.data
else:
    print(f"Errors: {result.errors}")
```

### validate_user_data

Быстрая валидация данных пользователя:

```python
from app.utils.validators import validate_user_data

result = validate_user_data({
    "telegram_id": 12345,
    "group_id": 1
})
```

## Уровни валидации

### STRICT (Строгий)

- Ошибки при любых несоответствиях
- Нет автоматических преобразований
- Максимальная безопасность

```python
validator = StringValidator(
    min_length=5,
    max_length=10,
    level=ValidationLevel.STRICT
)

# Ошибка - строка слишком короткая
result = validator.validate("123")
# result.is_valid = False
# result.errors = ["String too short: 3 < 5"]
```

### NORMAL (Обычный)

- Предупреждения для незначительных несоответствий
- Ограниченные автоматические преобразования
- Баланс между гибкостью и безопасностью

```python
validator = StringValidator(
    min_length=5,
    max_length=10,
    level=ValidationLevel.NORMAL
)

# Предупреждение - строка обрезана
result = validator.validate("123456789012345")
# result.is_valid = True
# result.data = "1234567890"
# result.warnings = ["String truncated to 10 characters"]
```

### LENIENT (Мягкий)

- Максимальная совместимость
- Автоматические преобразования
- Минимум ошибок

```python
validator = IntegerValidator(level=ValidationLevel.LENIENT)

# Автоматическое преобразование
result = validator.validate("123.45")
# result.is_valid = True
# result.data = 123
# result.warnings = ["Converted float to integer"]
```

## Лучшие практики

### 1. Выбор уровня валидации

```python
# Для пользовательского ввода - строгий
user_input_validator = StringValidator(level=ValidationLevel.STRICT)

# Для API данных - обычный
api_data_validator = DictValidator(level=ValidationLevel.NORMAL)

# Для внутренних данных - мягкий
internal_data_validator = IntegerValidator(level=ValidationLevel.LENIENT)
```

### 2. Обработка результатов

```python
def process_user_data(data: dict) -> dict | None:
    validator = UserDataValidator(level=ValidationLevel.STRICT)
    result = validator.validate(data)
    
    if not result.is_valid:
        logger.error(f"Validation failed: {result.errors}")
        return None
    
    if result.warnings:
        logger.warning(f"Validation warnings: {result.warnings}")
    
    return result.data
```

### 3. Кастомные валидаторы

```python
class EmailValidator(BaseValidator[str]):
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        super().__init__(level)
        self.pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
    
    def _validate_impl(self, data: Any) -> str:
        if not isinstance(data, str):
            if self.level == ValidationLevel.STRICT:
                raise ValidationError(f"Expected string, got {type(data).__name__}")
            data = str(data)
            self.warnings.append(f"Converted {type(data).__name__} to string")
        
        if not self.pattern.match(data):
            raise ValidationError("Invalid email format")
        
        return data.lower()
```

### 4. Валидация в сервисах

```python
class UserService:
    async def create_user(self, user_data: dict) -> User | None:
        # Валидация входных данных
        validator = UserDataValidator(level=ValidationLevel.STRICT)
        result = validator.validate(user_data)
        
        if not result.is_valid:
            logger.error(f"Invalid user data: {result.errors}")
            return None
        
        # Создание пользователя с валидированными данными
        user = User(**result.data)
        # ... сохранение в БД
        
        return user
```

## Отладка валидации

### Логирование

```python
import logging
from app.utils.validators import GroupDataValidator

logger = logging.getLogger(__name__)

validator = GroupDataValidator(level=ValidationLevel.STRICT)
result = validator.validate(data)

if not result.is_valid:
    logger.error(f"Validation failed for data: {data}")
    logger.error(f"Errors: {result.errors}")
    
if result.warnings:
    logger.warning(f"Validation warnings: {result.warnings}")
```

### Тестирование

```python
import pytest
from app.utils.validators import StringValidator, ValidationLevel

def test_string_validator():
    validator = StringValidator(min_length=1, max_length=10)
    
    # Валидные данные
    result = validator.validate("test")
    assert result.is_valid
    assert result.data == "test"
    
    # Невалидные данные
    result = validator.validate("")
    assert not result.is_valid
    assert "Empty string not allowed" in result.errors
```

## Производительность

### Кэширование валидаторов

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_group_validator(level: ValidationLevel) -> GroupDataValidator:
    return GroupDataValidator(level=level)

# Использование
validator = get_group_validator(ValidationLevel.STRICT)
```

### Батчевая валидация

```python
def validate_multiple_groups(groups_data: list[dict]) -> list[dict]:
    validator = GroupDataValidator(level=ValidationLevel.NORMAL)
    valid_groups = []
    
    for group_data in groups_data:
        result = validator.validate(group_data)
        if result.is_valid:
            valid_groups.append(result.data)
        else:
            logger.warning(f"Invalid group data: {result.errors}")
    
    return valid_groups
```
