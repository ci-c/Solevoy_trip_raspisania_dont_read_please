# Архитектура СЗГМУ Schedule Bot

## Обзор системы

**СЗГМУ Schedule Bot** — Telegram-бот для студентов СЗГМУ с функциями поиска расписаний, управления оценками, справочником по аттестации и системой заявлений.

### Ключевые особенности

- 🔍 **Умный поиск групп** с автоопределением семестра
- 📅 **Объединенные расписания** лекций и семинаров
- 📊 **Расчет ОСБ/КНЛ/КНС** согласно регламентам СЗГМУ 2025
- 📝 **Система заявлений** с генерацией документов
- 🔐 **Контроль доступа** через инвайты и подписки

## Архитектурные модули

### 1. Основной бот (`bot_main.py`)

- **FSM состояния** для различных сценариев
- **Обработчики событий** Telegram API
- **Middleware** для проверки доступа и лимитов
- **Клавиатуры** для интерактивного UX

### 2. Поиск и обработка расписаний (`schedule_processor/`)

#### `semester_detector.py` - Автоопределение семестра

```python
class SemesterDetector:
    def get_current_semester_info() -> SemesterInfo
    def is_current_semester(semester, year) -> bool
    def get_priority_filters() -> dict
```

#### `group_search.py` - Поиск групп и объединение расписаний

```python
class GroupSearchService:
    async def search_group_by_number(group) -> List[GroupInfo]
    def merge_schedules_to_lessons(group) -> List[UnifiedLesson] 
    def format_group_schedule(group, week) -> str

@dataclass
class UnifiedLesson:
    subject: str
    type: str  # "lecture", "seminar"
    teacher: str
    room: str
    time_start: str
    day_name: str
    week_number: int
    group: str
```

#### `api.py` - Интерфейс к API расписаний

```python
async def search_schedules(filters) -> List[Dict]
async def get_available_filters() -> Dict[str, List[str]]
```

### 3. Пользовательские профили (`student_profile.py`)

```python
@dataclass 
class StudentProfile:
    user_id: str
    telegram_username: str
    full_name: str
    speciality: str
    course: int
    group: str

class StudentProfileManager:
    def load_profile(user_id) -> Optional[StudentProfile]
    def save_profile(profile) -> bool
```

### 4. Система оценок (`grade_calculator.py`)

```python
class GradeCalculator:
    def calculate_tsb(subject) -> float  # Текущий средний балл
    def calculate_knl(subject) -> float  # Коэффициент непосещ. лекций  
    def calculate_kns(subject) -> float  # Коэффициент непосещ. семинаров
    def calculate_osb(subject) -> float  # ОСБ = ТСБ + КНЛ + КНС
  
    def add_grade(subject, grade, control_point)
    def add_attendance(subject, type, is_present, is_excused)
```

### 5. Справочник аттестации (`attestation_helper.py`)

```python
class AttestationHelper:
    def analyze_question(question) -> Optional[str]
    def get_knl_kns_explanation() -> str
    def get_absence_detailed_info() -> str
    def get_practical_tips() -> List[str]
```

### 6. Дневник студента (`diary.py`)

```python
class StudentDiary:
    def add_homework(subject, description, due_date)
    def add_grade(subject, grade, date) 
    def get_statistics() -> Dict
    def get_upcoming_deadlines() -> List
```

### 7. Система инвайтов и подписок

#### Планируемая архитектура (`invitation_system_plan.md`)

```python
@dataclass
class Invitation:
    code: str
    created_by: str
    expires_at: Optional[datetime]
    subscription_level: str  # "basic", "tester", "admin"
  
class InvitationManager:
    def generate_invitation(creator_id, level) -> str
    def validate_invitation(code) -> bool
    def use_invitation(code, user_id) -> bool
```

#### Уровни доступа

- **Guest** - базовый просмотр информации
- **Basic** - полный функционал (по инвайту)
- **Tester** - экспериментальные функции + создание инвайтов
- **Admin** - управление системой

### 8. Платежная система

#### Тарифные планы (`payment_system_plan.md`)

- **Free** - лимиты на поиски и предметы
- **Standard** (149₽/мес) - безлимитные поиски, PDF экспорт
- **Premium** (249₽/мес) - Google Calendar, напоминания

```python
@dataclass
class Subscription:
    user_id: str
    plan: str
    expires_at: datetime
    is_active: bool
  
class PaymentManager:
    async def create_payment(user_id, plan) -> str
    async def activate_subscription(user_id, plan)
```

### 9. Дисклеймер и соглашения (`disclaimer.py`)

```python
class DisclaimerManager:
    def has_user_agreed(user_id, version) -> bool
    def record_user_agreement(user_id)
    def get_disclaimer_text() -> str
    def get_short_disclaimer() -> str
```

## FSM состояния

### Основные потоки

```python
class MainMenu(StatesGroup):
    home = State()
    schedule_view = State()
    diary_view = State()

class GroupSearchStates(StatesGroup):
    choosing_search_type = State()
    entering_group_number = State()
    viewing_schedule = State()

class ProfileSetup(StatesGroup):
    waiting_name = State()
    selecting_speciality = State()
    selecting_course = State()
    confirmation = State()

class GradeStates(StatesGroup):
    main_view = State()
    selecting_subject = State()
    adding_grade = State()

class AttestationStates(StatesGroup):
    main_view = State() 
    asking_question = State()
    viewing_info = State()
```

## UX Flow

### 1. Новый пользователь

```
/start → Дисклеймер → Настройка профиля → Главное меню
```

### 2. Поиск группы (новый основной flow)

```
👥 Найти группу → 🔍 Быстрый поиск → Ввод номера → 
📅 Расписание группы (лекции + семинары) → Навигация по неделям
```

### 3. Управление оценками

```
🔢 Мои ОСБ/КНЛ/КНС → Выбор предмета → Добавление оценок/посещений →
Автоматический расчет показателей → Отчеты
```

### 4. Справочник аттестации

```
📚 Аттестация → Выбор темы ИЛИ ❓ Задать вопрос → 
ИИ-анализ → Релевантный ответ → Дополнительная информация
```

## Интеграции и API

### Внешние зависимости

- **Telegram Bot API** - основной интерфейс
- **СЗГМУ API** - получение расписаний (через schedule_processor)
- **ЮMoney API** - прием платежей (планируется)
- **Google Calendar API** - синхронизация (Premium функция)

### Внутренние зависимости

```
bot_main.py
├── schedule_processor/ (поиск и обработка данных)
├── student_profile.py (профили пользователей)
├── grade_calculator.py (оценки и статистика)
├── attestation_helper.py (справочник с ИИ)
├── disclaimer.py (соглашения)
└── diary.py (дневник студента)
```

## Хранение данных

### Файловая система

```
/user_data/
├── profiles/{user_id}.json          # Профили студентов
├── grades/{user_id}/                 # Оценки и посещаемость
│   ├── grades.json
│   └── attendance.json  
├── diaries/{user_id}.json           # Дневники  
├── agreements/{user_id}.json        # Пользовательские соглашения
└── invitations/
    ├── invitations.json             # База инвайтов
    └── user_invitations.json        # Связи пользователь-инвайт
```

### Кэширование

- **Поиск групп** - кэш результатов поиска
- **Расписания** - временное кэширование на диске
- **Фильтры** - кэш доступных опций из API

## Качество кода

### Типизация

- Полная типизация всех модулей
- Dataclasses для структур данных
- Type hints для async/await функций

### Линтинг и форматирование

- **ruff** для проверки кода и автоисправлений
- Соответствие PEP 8
- Консистентные импорты и структура

### Логирование

```python
# Структурированное логирование
logger.info(f"User {user_id} searched group {group_number}")
logger.error(f"Error in group search: {error}")

# Отдельные логи для ошибок
/logs/bot_errors.log - критичные ошибки
```

## Безопасность

### Данные пользователей

- Никаких персональных данных в логах
- Хеширование чувствительных данных
- Изоляция пользовательских файлов

### Дисклеймер ответственности

- Автоматическое согласие при первом запуске
- Четкое указание источников данных
- Снятие ответственности за неактуальную информацию

### Контроль доступа

- Middleware для проверки прав
- Система инвайтов ограничивает регистрацию
- Админские функции защищены дополнительными проверками

## Производительность

### Оптимизации

- Асинхронная обработка всех I/O операций
- Кэширование частых запросов
- Ленивая загрузка данных пользователей
- Спиннер при длительных операциях

### Масштабируемость

- Модульная архитектура для легкого расширения
- Файловое хранение данных (переход на БД при росте)
- Готовность к горизонтальному масштабированию

## Планы развития

### Краткосрочные (1-2 месяца)

1. ✅ Поиск групп с объединением расписаний
2. 🔄 Админ-панель управления инвайтами
3. 🔄 Система репортов и аналитики
4. ⏳ Базовая монетизация

### Среднесрочные (3-6 месяцев)

1. Интеграция с Google Calendar
2. Push-уведомления о расписании
3. Мобильное приложение
4. API для сторонних разработчиков

### Долгосрочные (6+ месяцев)

1. Корпоративные аккаунты для деканатов
2. Интеграция с системами университета
3. Расширение на другие вузы
4. ИИ-ассистент для учебных вопросов
