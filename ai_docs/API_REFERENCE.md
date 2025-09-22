# API Reference

## Services API

### ScheduleService

#### `get_user_schedule(user_id: int, start_date: date | None = None, end_date: date | None = None) -> List[Dict[str, str]] | None`
Получить расписание пользователя.

**Parameters:**
- `user_id` (int): ID пользователя
- `start_date` (date, optional): Начальная дата
- `end_date` (date, optional): Конечная дата

**Returns:**
- `List[Dict[str, str]] | None`: Список занятий или None при ошибке

**Example:**
```python
schedule_service = ScheduleService()
lessons = await schedule_service.get_user_schedule(12345)
```

### GroupService

#### `get_all_groups() -> list[dict[str, str]]`
Получить все группы.

**Returns:**
- `list[dict[str, str]]`: Список всех групп

#### `get_group_by_id(group_id: int) -> dict[str, str] | None`
Получить группу по ID.

**Parameters:**
- `group_id` (int): ID группы

**Returns:**
- `dict[str, str] | None`: Данные группы или None

#### `create_group(group_data: dict[str, str]) -> dict[str, str]`
Создать новую группу.

**Parameters:**
- `group_data` (dict[str, str]): Данные группы

**Returns:**
- `dict[str, str]`: Созданные данные группы

#### `find_groups_by_number(group_number: str) -> list[dict[str, str]]`
Найти группы по номеру.

**Parameters:**
- `group_number` (str): Номер группы

**Returns:**
- `list[dict[str, str]]`: Список найденных групп

#### `get_groups_by_faculty(faculty: str) -> list[dict[str, str]]`
Получить группы по факультету.

**Parameters:**
- `faculty` (str): Название факультета

**Returns:**
- `list[dict[str, str]]`: Список групп факультета

#### `get_available_faculties() -> list[str] | None`
Получить список доступных факультетов.

**Returns:**
- `list[str] | None`: Список факультетов или None при ошибке

#### `find_or_create_group(group_number: str) -> dict[str, str] | None`
Найти или создать группу по номеру.

**Parameters:**
- `group_number` (str): Номер группы

**Returns:**
- `dict[str, str] | None`: Данные группы или None

**Example:**
```python
group_service = GroupService()
group_data = await group_service.find_or_create_group("101")
```

### UserService

#### `create_user(telegram_id: int, telegram_username: str | None = None, full_name: str | None = None) -> User`
Создать нового пользователя.

**Parameters:**
- `telegram_id` (int): Telegram ID пользователя
- `telegram_username` (str, optional): Username в Telegram
- `full_name` (str, optional): Полное имя пользователя

**Returns:**
- `User`: Pydantic модель пользователя

**Example:**
```python
user_service = UserService()
user = await user_service.create_user(12345, "username", "Иван Иванов")
```

#### `get_user_profile(user_id: int) -> dict[str, Any] | None`
Получить профиль пользователя.

**Parameters:**
- `user_id` (int): ID пользователя

**Returns:**
- `dict[str, Any] | None`: Профиль пользователя или None

### FacultyService

#### `get_faculty_names() -> list[str] | None`
Получить список названий факультетов.

**Returns:**
- `list[str] | None`: Список факультетов или None при ошибке

#### `sync_faculties() -> bool`
Синхронизировать факультеты с API.

**Returns:**
- `bool`: Успешность синхронизации

### APISyncService

#### `full_sync() -> bool`
Полная синхронизация всех данных с API.

**Returns:**
- `bool`: Успешность синхронизации

### InvitationService

#### `create_invitation(creator_id: int, access_level: str) -> dict[str, Any] | None`
Создать приглашение.

**Parameters:**
- `creator_id` (int): ID создателя
- `access_level` (str): Уровень доступа

**Returns:**
- `dict[str, Any] | None`: Данные приглашения или None

### EducationService

#### `get_education_data() -> list[dict[str, Any]]`
Получить образовательные данные.

**Returns:**
- `list[dict[str, Any]]`: Список образовательных данных

### AcademicService

#### `get_academic_data() -> dict[str, Any]`
Получить академические данные.

**Returns:**
- `dict[str, Any]`: Академические данные

## Handlers API

### Start Handler

#### `cmd_start(message: Message, state: FSMContext) -> None`
Обработчик команды /start.

**Parameters:**
- `message` (Message): Сообщение от пользователя
- `state` (FSMContext): Состояние FSM

#### `cmd_clean(message: Message, state: FSMContext) -> None`
Обработчик команды /clean - очистка диалога.

**Parameters:**
- `message` (Message): Сообщение от пользователя
- `state` (FSMContext): Состояние FSM

### Main Menu Handler

#### `handle_menu(callback: CallbackQuery, callback_data: MenuCallback, state: FSMContext) -> None`
Обработчик главного меню.

**Parameters:**
- `callback` (CallbackQuery): Callback запрос
- `callback_data` (MenuCallback): Данные callback'а
- `state` (FSMContext): Состояние FSM

### Simplified Menu Handler

#### `handle_menu_action(callback: CallbackQuery, callback_data: MenuCallback, state: FSMContext) -> None`
Обработчик действий упрощенного меню.

**Parameters:**
- `callback` (CallbackQuery): Callback запрос
- `callback_data` (MenuCallback): Данные callback'а
- `state` (FSMContext): Состояние FSM

### Group Selection Handler

#### `register_group_selection_handlers(dp: Dispatcher) -> None`
Регистрация обработчиков выбора группы.

**Parameters:**
- `dp` (Dispatcher): Диспетчер aiogram

### Group Setup Handler

#### `register_group_setup_handlers(dp: Dispatcher) -> None`
Регистрация обработчиков настройки группы.

**Parameters:**
- `dp` (Dispatcher): Диспетчер aiogram

### Profile Handler

#### `register_profile_handlers(dp: Dispatcher) -> None`
Регистрация обработчиков профиля.

**Parameters:**
- `dp` (Dispatcher): Диспетчер aiogram

### Grade Handler

#### `register_grade_handlers(dp: Dispatcher) -> None`
Регистрация обработчиков оценок.

**Parameters:**
- `dp` (Dispatcher): Диспетчер aiogram

### Invitation Handler

#### `register_invitation_handlers(dp: Dispatcher) -> None`
Регистрация обработчиков системы инвайтов.

**Parameters:**
- `dp` (Dispatcher): Диспетчер aiogram

### Error Handler

#### `register_error_handler(dp: Dispatcher) -> None`
Регистрация обработчика ошибок.

**Parameters:**
- `dp` (Dispatcher): Диспетчер aiogram

## Validators API

### BaseValidator

#### `validate(data: Any) -> ValidationResult[T]`
Базовый валидатор с generic типизацией.

**Parameters:**
- `data` (Any): Данные для валидации

**Returns:**
- `ValidationResult[T]`: Результат валидации с типизированными данными

### ValidationResult

#### `is_valid: bool`
Успешность валидации.

#### `data: T | None`
Валидированные данные или None.

#### `errors: list[str]`
Список ошибок валидации.

#### `warnings: list[str]`
Список предупреждений валидации.

### StringValidator

#### `validate(data: Any) -> ValidationResult[str]`
Валидировать строку.

**Parameters:**
- `data` (Any): Данные для валидации

**Returns:**
- `ValidationResult[str]`: Результат валидации

**Example:**
```python
validator = StringValidator(min_length=1, max_length=50, pattern=r"^\d+$")
result = validator.validate("123")
if result.is_valid:
    print(result.data)
else:
    print(result.errors)
```

### IntegerValidator

#### `validate(data: Any) -> ValidationResult[int]`
Валидировать целое число.

**Parameters:**
- `data` (Any): Данные для валидации

**Returns:**
- `ValidationResult[int]`: Результат валидации

**Example:**
```python
validator = IntegerValidator(min_value=1, max_value=100)
result = validator.validate("50")
```

### DictValidator

#### `validate(data: Any) -> ValidationResult[dict[str, Any]]`
Валидировать словарь.

**Parameters:**
- `data` (Any): Данные для валидации

**Returns:**
- `ValidationResult[dict[str, Any]]`: Результат валидации

### GroupDataValidator

#### `validate(data: Any) -> ValidationResult[dict[str, str]]`
Валидировать данные группы.

**Parameters:**
- `data` (Any): Данные для валидации

**Returns:**
- `ValidationResult[dict[str, str]]`: Результат валидации

**Example:**
```python
validator = GroupDataValidator()
result = validator.validate(group_data)
if result.is_valid:
    print(result.data)
else:
    print(result.errors)
```

### UserDataValidator

#### `validate(data: Any) -> ValidationResult[dict[str, Any]]`
Валидировать данные пользователя.

**Parameters:**
- `data` (Any): Данные для валидации

**Returns:**
- `ValidationResult[dict[str, Any]]`: Результат валидации

### ValidationLevel

#### `STRICT = "strict"`
Строгая валидация - ошибки при любых несоответствиях.

#### `NORMAL = "normal"`
Обычная валидация - предупреждения для незначительных несоответствий.

#### `LENIENT = "lenient"`
Мягкая валидация - максимальная совместимость.

## Error Handling API

### ErrorHandlerMiddleware

#### `__call__(handler: Callable, event: TelegramObject, data: Dict[str, Any]) -> Any`
Обработать событие с глобальной обработкой ошибок.

**Parameters:**
- `handler` (Callable): Обработчик события
- `event` (TelegramObject): Событие
- `data` (Dict[str, Any]): Данные

**Returns:**
- `Any`: Результат обработки

### safe_execute_async

#### `safe_execute_async(func: Callable, *args, default: T | None = None, error_message: str = "Async operation failed", context: dict[str, Any] | None = None, **kwargs) -> T | None`
Безопасное выполнение асинхронной функции.

**Parameters:**
- `func` (Callable): Функция для выполнения
- `*args`: Аргументы функции
- `default` (T, optional): Значение по умолчанию
- `error_message` (str): Сообщение об ошибке
- `context` (dict, optional): Контекст
- `**kwargs`: Ключевые аргументы

**Returns:**
- `T | None`: Результат или значение по умолчанию

**Example:**
```python
result = await safe_execute_async(
    risky_function,
    arg1, arg2,
    default=[],
    error_message="Function failed"
)
```

### async_error_handler

#### `async_error_handler(default_return: T | None = None, error_message: str = "Operation failed")`
Декоратор для безопасного выполнения асинхронных функций.

**Parameters:**
- `default_return` (T, optional): Значение по умолчанию при ошибке
- `error_message` (str): Сообщение об ошибке

**Example:**
```python
@async_error_handler(default_return=None, error_message="Failed to get data")
async def get_data() -> dict[str, Any] | None:
    # Реализация функции
    pass
```

### safe_execute

#### `safe_execute(func: Callable[..., T], *args, default: T | None = None, error_message: str = "Operation failed", **kwargs) -> T | None`
Безопасное выполнение синхронной функции.

**Parameters:**
- `func` (Callable): Функция для выполнения
- `*args`: Аргументы функции
- `default` (T, optional): Значение по умолчанию
- `error_message` (str): Сообщение об ошибке
- `**kwargs`: Ключевые аргументы

**Returns:**
- `T | None`: Результат или значение по умолчанию

## Database Models

### User (SQLAlchemy)
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group: Mapped["Group"] = relationship(back_populates="users")
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"), nullable=True)
```

### Group (SQLAlchemy)
```python
class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    faculty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    speciality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    course: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="group")
```

### Faculty (SQLAlchemy)
```python
class Faculty(Base):
    __tablename__ = "faculties"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Speciality (SQLAlchemy)
```python
class Speciality(Base):
    __tablename__ = "specialities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    faculty_id: Mapped[Optional[int]] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Schedule (SQLAlchemy)
```python
class Schedule(Base):
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    faculty_id: Mapped[Optional[int]] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    speciality_id: Mapped[Optional[int]] = mapped_column(ForeignKey("specialities.id"), nullable=True)
    academic_year_id: Mapped[Optional[int]] = mapped_column(ForeignKey("academic_years.id"), nullable=True)
    semester_id: Mapped[Optional[int]] = mapped_column(ForeignKey("semesters.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Lesson (SQLAlchemy)
```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"))
    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"), nullable=True)
    classroom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    lesson_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

## Callback Data

### FilterCallback
```python
class FilterCallback(CallbackData, prefix="filter"):
    name: str
```

### OptionCallback
```python
class OptionCallback(CallbackData, prefix="option"):
    filter_name: str
    value: str
```

### ResultCallback
```python
class ResultCallback(CallbackData, prefix="result"):
    index: int
```

### FormatCallback
```python
class FormatCallback(CallbackData, prefix="format"):
    result_index: int
    format_type: str
```

### MenuCallback
```python
class MenuCallback(CallbackData, prefix="menu"):
    action: str
```

### ProfileCallback
```python
class ProfileCallback(CallbackData, prefix="profile"):
    action: str
    value: str = ""
```

### DiaryCallback
```python
class DiaryCallback(CallbackData, prefix="diary"):
    action: str
    item_id: str = ""
```

### ApplicationCallback
```python
class ApplicationCallback(CallbackData, prefix="app"):
    action: str
    data: str = ""
```

### AttestationCallback
```python
class AttestationCallback(CallbackData, prefix="attest"):
    action: str
    topic: str = ""
```

### GradeCallback
```python
class GradeCallback(CallbackData, prefix="grade"):
    action: str
    subject: str = ""
    data: str = ""
```

### GroupSearchCallback
```python
class GroupSearchCallback(CallbackData, prefix="group_search"):
    action: str
    value: str | None = None
    group_id: str | None = None
```

### GroupSelectionCallback
```python
class GroupSelectionCallback(CallbackData, prefix="group_select"):
    action: str
    group_id: int = 0
    faculty: str = ""
```

### GroupConfirmationCallback
```python
class GroupConfirmationCallback(CallbackData, prefix="group_confirm"):
    action: str
    group_id: int = 0
```

### InvitationCallback
```python
class InvitationCallback(CallbackData, prefix="invitation"):
    action: str
    invitation_id: str = ""
```

## FSM States

### ProfileSetup
```python
class ProfileSetup(StatesGroup):
    waiting_name = State()
    selecting_speciality = State()
    selecting_course = State()
    selecting_stream = State()
    selecting_group = State()
    confirmation = State()
```

### MainMenu
```python
class MainMenu(StatesGroup):
    home = State()
    schedule_view = State()
    diary_view = State()
    applications = State()
    reminders = State()
    settings = State()
```

### SearchForm
```python
class SearchForm(StatesGroup):
    waiting_activation = State()
    selecting_filters = State()
    selecting_options = State()
    processing_search = State()
    selecting_result = State()
    selecting_format = State()
    generating_file = State()
```

### DiaryStates
```python
class DiaryStates(StatesGroup):
    main_view = State()
    adding_grade = State()
    adding_homework = State()
    adding_absence = State()
    viewing_stats = State()
```

### ApplicationStates
```python
class ApplicationStates(StatesGroup):
    selecting_dates = State()
    selecting_reason = State()
    generating_docs = State()
```

### AttestationStates
```python
class AttestationStates(StatesGroup):
    main_view = State()
    asking_question = State()
    viewing_info = State()
```

### GradeStates
```python
class GradeStates(StatesGroup):
    main_view = State()
    selecting_subject = State()
    viewing_subject = State()
    adding_grade = State()
    adding_attendance = State()
    entering_grade_data = State()
    entering_attendance_data = State()
```

### GroupSearchStates
```python
class GroupSearchStates(StatesGroup):
    choosing_search_type = State()
    entering_group_number = State()
    selecting_speciality = State()
    selecting_course = State()
    viewing_results = State()
    viewing_schedule = State()
    confirming_selection = State()
```

### GroupSetupStates
```python
class GroupSetupStates(StatesGroup):
    choosing_method = State()
    entering_group_number = State()
    selecting_faculty = State()
    confirming_selection = State()
```

### InvitationStates
```python
class InvitationStates(StatesGroup):
    main_view = State()
    entering_code = State()
    creating_invitation = State()
    viewing_invitations = State()
```

## Configuration

### Environment Variables
```bash
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///data/szgmu_bot.db
LOG_LEVEL=INFO
```

### Logging Configuration
```python
# logs/bot.log - Основные логи
# logs/errors.log - Ошибки
# logs/api_requests.log - API запросы
# logs/user_actions.log - Действия пользователей
# logs/security.log - Безопасность
```

## Examples

### Создание нового пользователя
```python
from app.services.user_service import UserService

user_service = UserService()
user = await user_service.create_user(
    telegram_id=12345,
    telegram_username="test_user",
    full_name="Иван Иванов"
)
```

### Получение расписания
```python
from app.services.schedule_service import ScheduleService

schedule_service = ScheduleService()
lessons = await schedule_service.get_user_schedule(12345)
```

### Работа с группами
```python
from app.services.group_service import GroupService

group_service = GroupService()
faculties = await group_service.get_available_faculties()
groups = await group_service.find_groups_by_number("101")
```

### Валидация данных
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
    print(f"Validated data: {group_data}")
else:
    print(f"Validation errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
```

### Обработка ошибок
```python
from app.utils.error_monitor import safe_execute_async, async_error_handler

# Использование декоратора
@async_error_handler(default_return=None, error_message="Failed to get data")
async def get_user_data(user_id: int) -> dict[str, Any] | None:
    # Реализация функции
    pass

# Использование функции
result = await safe_execute_async(
    risky_database_operation,
    user_id=12345,
    default=[],
    error_message="Failed to get user data"
)
```

### Работа с валидаторами
```python
from app.utils.validators import StringValidator, IntegerValidator, ValidationLevel

# Валидация строки
string_validator = StringValidator(
    min_length=1, 
    max_length=50, 
    pattern=r"^\d+$",
    level=ValidationLevel.STRICT
)
result = string_validator.validate("123")

# Валидация числа
int_validator = IntegerValidator(min_value=1, max_value=100)
result = int_validator.validate("50")
```
