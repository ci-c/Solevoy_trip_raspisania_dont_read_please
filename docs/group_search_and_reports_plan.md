# План улучшений поиска и системы репортов

## 1. Поиск группы вместо расписания

### Текущая проблема
Пользователь выбирает фильтры и получает множество расписаний, не понимая что выбрать.

### Новый UX
```
🔍 **Поиск группы**

1️⃣ **Быстрый поиск**
   📝 Введите номер группы: [103а]
   🎓 Введите специальность: [Лечебное дело]

2️⃣ **Подробный поиск** 
   📊 Курс: [1] [2] [3] [4] [5] [6]
   📚 Специальность: [Выбрать из списка]
   🔤 Поток: [а] [б] [в]

[🔍 Найти группу] [📅 Мое расписание]
```

### Архитектура

```python
class GroupSearchService:
    def __init__(self):
        self.current_semester = self.detect_current_semester()
        self.groups_cache = {}
    
    def detect_current_semester(self) -> Tuple[str, str]:
        """Определить текущий семестр и учебный год"""
        now = datetime.now()
        if 9 <= now.month <= 12:  # Осенний семестр
            return "осенний", f"{now.year}/{now.year + 1}"
        else:  # Весенний семестр  
            return "весенний", f"{now.year - 1}/{now.year}"
    
    async def search_group_by_number(self, group_number: str) -> List[GroupInfo]:
        """Поиск группы по номеру (103а, 204б, etc)"""
        
    async def search_groups_by_filters(self, filters: Dict) -> List[GroupInfo]:
        """Поиск групп по фильтрам"""
        
    def merge_lecture_seminar_schedules(self, group: GroupInfo) -> UnifiedSchedule:
        """Объединить лекции и семинары в единое расписание"""

@dataclass
class GroupInfo:
    number: str  # "103а"  
    speciality: str
    course: int
    stream: str
    semester: str
    year: str
    lecture_schedule_id: Optional[str]
    seminar_schedule_id: Optional[str]
    unified_schedule: Optional[UnifiedSchedule] = None

@dataclass  
class UnifiedSchedule:
    group: str
    week_schedule: Dict[str, List[Lesson]]  # день недели -> уроки
    metadata: Dict[str, Any]
```

## 2. Автоопределение даты и семестра

### Логика определения
```python
class SemesterDetector:
    def get_current_semester_info(self) -> SemesterInfo:
        now = datetime.now()
        
        # Осенний семестр: сентябрь-декабрь
        if 9 <= now.month <= 12:
            return SemesterInfo(
                name="осенний",
                year=f"{now.year}/{now.year + 1}",
                start_date=self.get_semester_start(now.year, "autumn"),
                end_date=self.get_semester_end(now.year, "autumn")
            )
        
        # Весенний семестр: февраль-май  
        elif 2 <= now.month <= 5:
            return SemesterInfo(
                name="весенний", 
                year=f"{now.year - 1}/{now.year}",
                start_date=self.get_semester_start(now.year, "spring"),
                end_date=self.get_semester_end(now.year, "spring")
            )
        
        # Каникулы: показывать ближайший семестр
        else:
            return self.get_next_semester(now)
    
    def get_semester_start(self, year: int, season: str) -> date:
        """Первый понедельник сентября/февраля"""
        
    def get_current_week_number(self) -> int:
        """Номер учебной недели"""
```

## 3. Объединение лекций и семинаров

### Проблема
Сейчас лекции и семинары в разных расписаниях, пользователю нужно скачивать 2 файла.

### Решение
```python
class ScheduleMerger:
    def merge_schedules(self, lecture_data: Dict, seminar_data: Dict, group: str) -> UnifiedSchedule:
        """Объединить два расписания в одно"""
        merged_lessons = []
        
        # Парсим лекции
        lecture_lessons = self.parse_lessons(lecture_data, "lecture")
        seminar_lessons = self.parse_lessons(seminar_data, "seminar")
        
        # Фильтруем по группе
        filtered_lectures = [l for l in lecture_lessons if self.lesson_matches_group(l, group)]
        filtered_seminars = [l for l in seminar_lessons if self.lesson_matches_group(l, group)]
        
        # Объединяем и сортируем по времени
        all_lessons = filtered_lectures + filtered_seminars
        all_lessons.sort(key=lambda x: (x.week_number, x.day_of_week, x.time_start))
        
        return self.build_unified_schedule(all_lessons, group)
    
    def build_week_view(self, lessons: List[Lesson]) -> Dict[str, List[Lesson]]:
        """Сгруппировать по дням недели"""
        week_view = defaultdict(list)
        for lesson in lessons:
            week_view[lesson.day_name].append(lesson)
        return dict(week_view)

@dataclass
class Lesson:
    subject: str
    type: str  # "lecture", "seminar", "practice"
    teacher: str
    room: str
    time_start: str
    time_end: str
    day_name: str
    day_of_week: int
    week_number: int
    group: str
    subgroup: Optional[str] = None
```

### UX для объединенного расписания
```
📅 **Расписание группы 103а**
🗓 Неделя 12 | Весенний семестр 2024/2025

**Понедельник, 24 января**
🕘 09:00-10:30 | 📚 Анатомия (лекция)
     👨‍🏫 Иванов И.И. | 🏢 Ауд. 101

🕐 11:00-12:30 | 📝 Анатомия (семинар)  
     👨‍🏫 Петров П.П. | 🏢 Ауд. 205 | Подгр. А

**Вторник, 25 января**
🕘 09:00-10:30 | 📚 Физиология (лекция)
     👨‍🏫 Сидоров С.С. | 🏢 Ауд. 301

[📊 Экспорт] [🔔 Уведомления] [⚙️ Настройки]
```

## 4. Админская панель

### Доступ
Только пользователи с уровнем `admin` могут попасть в админ-панель.

### UX админ-панели
```
🛠 **Админ-панель**

👥 **Управление пользователями**
• Активных: 1,247
• Новых за неделю: 89  
• Заблокированных: 3
[Просмотр пользователей] [Статистика]

🔑 **Управление инвайтами**  
• Всего создано: 156
• Активных: 23
• Использованных: 133
[Создать инвайт] [Список инвайтов]

📊 **Аналитика**
• Поисков расписаний: 2,341 за неделю
• Популярные группы: 103а, 204б, 301в
• Активность по часам: [График]
[Подробная аналитика] [Экспорт данных]

⚙️ **Настройки системы**
• Лимиты для бесплатных: 10 поисков/день  
• Стоимость подписок: 149₽/249₽
• Техническое обслуживание
[Изменить настройки] [Логи системы]
```

### Архитектура админки
```python
class AdminPanel:
    def __init__(self, user_manager, invitation_manager, analytics):
        self.user_manager = user_manager
        self.invitation_manager = invitation_manager  
        self.analytics = analytics
    
    async def get_users_stats(self) -> Dict:
        """Статистика пользователей"""
        
    async def create_invitation(self, admin_id: str, level: str, expires_in: int) -> str:
        """Создать инвайт"""
        
    async def ban_user(self, admin_id: str, user_id: str, reason: str):
        """Заблокировать пользователя"""
        
    async def get_system_analytics(self) -> Dict:
        """Системная аналитика"""

# Декоратор для админских функций
def require_admin_access():
    def decorator(handler):
        async def wrapper(callback, state, user_access_level):
            if user_access_level != "admin":
                await callback.answer("🚫 Доступ только для администраторов", show_alert=True)
                return
            return await handler(callback, state)
        return wrapper
    return decorator
```

## 5. Система репортов

### Типы репортов

#### Для пользователей
1. **Персональная статистика**
   - Использование функций за месяц
   - Успеваемость по предметам (если ведется)
   - Посещаемость и КНЛ/КНС

2. **Отчет по группе** (для старост)
   - Общая статистика группы
   - Популярные предметы
   - Активность использования бота

#### Для администраторов
1. **Отчет по пользователям**
   - Регистрации по дням/неделям
   - Конверсия в платные тарифы
   - Активные/неактивные пользователи

2. **Финансовый отчет**
   - Доходы по тарифам
   - Популярность подписок
   - Churn rate (отток пользователей)

3. **Технический отчет**
   - Ошибки и падения
   - Производительность
   - Использование ресурсов

### Архитектура репортов
```python
@dataclass
class ReportRequest:
    report_type: str
    user_id: str
    parameters: Dict[str, Any]
    format: str  # "pdf", "excel", "json"
    
class ReportGenerator:
    def __init__(self):
        self.pdf_generator = PDFReportGenerator()
        self.excel_generator = ExcelReportGenerator()
        
    async def generate_report(self, request: ReportRequest) -> Path:
        data = await self.collect_report_data(request)
        
        if request.format == "pdf":
            return await self.pdf_generator.generate(data, request.report_type)
        elif request.format == "excel":
            return await self.excel_generator.generate(data, request.report_type)
        
    async def collect_report_data(self, request: ReportRequest) -> Dict:
        """Собрать данные для отчета"""

# Планировщик автоматических отчетов
class ReportScheduler:
    def __init__(self):
        self.scheduled_reports = []
        
    def schedule_daily_reports(self):
        """Ежедневные отчеты для админов"""
        
    def schedule_weekly_reports(self):
        """Еженедельные отчеты"""
        
    def schedule_monthly_reports(self):
        """Месячные отчеты для бизнес-аналитики"""
```

### UX для репортов
```
📊 **Мои отчеты**

📈 **Персональная статистика за месяц**
• Поисков расписаний: 47
• Оценок добавлено: 23
• Средний ОСБ: 4.2
• Посещаемость: 87%
[📄 Скачать PDF] [📊 Подробнее]

👥 **Отчет по группе 103а** (староста)
• Активных пользователей: 18/25
• Популярные предметы: Анатомия, Физиология
• Средняя успеваемость: 4.1
[📄 Скачать отчет]

🤖 **Помощь в учебе**
• Вопросов по аттестации: 12
• Документов сгенерировано: 5
• Сэкономлено времени: ~3 часа
[💝 Поддержать проект]
```

## 6. Интеграция в бот

### Новые состояния FSM
```python
class GroupSearchStates(StatesGroup):
    choosing_search_type = State()  # быстрый или подробный
    entering_group_number = State()
    selecting_speciality = State()
    selecting_course = State()
    viewing_results = State()
    
class AdminStates(StatesGroup):
    main_panel = State()
    managing_users = State()
    managing_invites = State()
    viewing_analytics = State()
    creating_invite = State()
    
class ReportsStates(StatesGroup):
    selecting_report_type = State()
    configuring_report = State()
    generating_report = State()
```

### Обновленное главное меню
```python
def get_main_menu_keyboard(user_profile: Optional[StudentProfile] = None) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if user_profile:
        builder.button(text="👥 Найти группу", callback_data=MenuCallback(action="search_group"))
        builder.button(text="📅 Мое расписание", callback_data=MenuCallback(action="my_schedule"))  
        builder.button(text="📊 Мои отчеты", callback_data=MenuCallback(action="reports"))
        # ... остальные кнопки
        
        # Админская кнопка только для админов
        if user_access_level == "admin":
            builder.button(text="🛠 Админ-панель", callback_data=MenuCallback(action="admin_panel"))
```

## 7. Этапы реализации

### Этап 1: Поиск группы (1 неделя)
1. Реализовать GroupSearchService
2. Добавить UX поиска по номеру группы
3. Интегрировать автоопределение семестра
4. Тестирование поиска

### Этап 2: Объединение расписаний (1 неделя) 
1. Создать ScheduleMerger
2. Обновить генерацию файлов
3. Новый UX для объединенного расписания
4. Тестирование слияния данных

### Этап 3: Админ-панель (2 недели)
1. Реализовать AdminPanel  
2. Добавить управление инвайтами
3. Статистика и аналитика
4. Система прав доступа

### Этап 4: Репорты (1-2 недели)
1. Базовые персональные отчеты
2. PDF/Excel генерация
3. Планировщик автоматических отчетов
4. Интеграция в UI

Приоритет: **Поиск группы → Объединение расписаний → Админ-панель → Репорты**