# Схема базы данных SZGMU Bot

## UML Диаграмма создания групп по расписаниям

```mermaid
erDiagram
    %% Справочные таблицы
    Faculty ||--o{ Speciality : "содержит"
    Faculty ||--o{ Group : "имеет"
    Speciality ||--o{ Group : "имеет"
    Speciality ||--o{ Schedule : "имеет"
    
    AcademicYear ||--o{ Semester : "содержит"
    AcademicYear ||--o{ Schedule : "имеет"
    Semester ||--o{ Schedule : "имеет"
    
    %% Основные таблицы
    Schedule ||--o{ Lesson : "содержит"
    Schedule }o--|| Speciality : "принадлежит"
    Schedule }o--|| AcademicYear : "принадлежит"
    Schedule }o--|| Semester : "принадлежит"
    
    Lesson }o--|| Subject : "имеет предмет"
    Lesson }o--|| LessonType : "имеет тип"
    Lesson }o--o| Lecturer : "ведет преподаватель"
    Lesson }o--o| Classroom : "проходит в аудитории"
    Lesson }o--o| Department : "от кафедры"
    
    %% Пользователи и группы
    User }o--o| Group : "принадлежит"
    Group }o--|| Faculty : "принадлежит факультету"
    Group }o--|| Speciality : "принадлежит специальности"
    
    %% Таблицы
    Faculty {
        int id PK
        string name "Название факультета"
        string short_name "Краткое название"
        string description "Описание"
        datetime created_at
    }
    
    Speciality {
        int id PK
        string code "Код специальности (31.05.01)"
        string name "Название специальности"
        int faculty_id FK
        datetime created_at
    }
    
    Group {
        int id PK
        string name "Номер группы (105а)"
        string faculty "Legacy поле"
        string speciality "Legacy поле"
        int course "Курс"
        int faculty_id FK
        int speciality_id FK
        datetime created_at
    }
    
    AcademicYear {
        int id PK
        string name "2024/2025"
        boolean is_current
        datetime created_at
    }
    
    Semester {
        int id PK
        string name "осенний/весенний"
        int academic_year_id FK
        date start_date
        date end_date
        boolean is_current
        datetime created_at
    }
    
    Schedule {
        int id PK
        int external_id "ID из API СЗГМУ"
        string file_name "Имя файла расписания"
        int form_type "1=лекции, 2=практики, 3=смешанные"
        string status "APPROVED/DRAFT"
        int academic_year_id FK
        int semester_id FK
        int speciality_id FK
        datetime created_at
    }
    
    Lesson {
        int id PK
        int external_id "ID из API"
        string day_name "пн, вт, ср"
        int week_number "1, 2, 3..."
        string pair_time "9:00-10:30"
        time start_time
        time end_time
        int schedule_id FK
        int subject_id FK
        int lesson_type_id FK
        int lecturer_id FK
        int classroom_id FK
        int department_id FK
        string subgroup "241б"
        string study_group "МПФ"
        datetime created_at
    }
    
    Subject {
        int id PK
        string name "Название предмета"
        string short_name "Краткое название"
        datetime created_at
    }
    
    LessonType {
        int id PK
        string name "лекционного/семинарского типа"
        datetime created_at
    }
    
    Lecturer {
        int id PK
        string name "ФИО преподавателя"
        int department_id FK
        datetime created_at
    }
    
    Classroom {
        int id PK
        string number "101, А-201"
        string building "Главный корпус"
        string address
        int capacity
        datetime created_at
    }
    
    Department {
        int id PK
        string name "Название кафедры"
        string short_name "Краткое название"
        datetime created_at
    }
    
    User {
        int id PK
        int telegram_id "ID в Telegram"
        string username "Username в Telegram"
        string first_name "Имя"
        string last_name "Фамилия"
        int group_id FK
        datetime created_at
    }
```

## Процесс создания групп по расписаниям

### 1. Синхронизация с API СЗГМУ
```
API СЗГМУ → Schedule (расписания) → Lesson (занятия)
```

### 2. Извлечение информации о группах
Из каждого `Lesson` извлекается:
- `study_group` → номер группы (например, "105а")
- `subgroup` → подгруппа (например, "241б")
- Связь с `Speciality` через `Schedule`

### 3. Создание групп
```python
# Псевдокод создания группы
for lesson in lessons:
    group_name = lesson.study_group  # "105а"
    speciality = lesson.schedule.speciality  # Специальность
    
    # Найти или создать группу
    group = find_or_create_group(
        name=group_name,
        speciality=speciality,
        faculty=speciality.faculty,
        course=extract_course_from_group_name(group_name)
    )
```

### 4. Связывание пользователей с группами
```python
# Пользователь выбирает группу
user.group_id = selected_group.id
```

## Ключевые особенности архитектуры

1. **Нормализация данных**: Справочники вынесены в отдельные таблицы
2. **Legacy поля**: В `Group` есть поля `faculty` и `speciality` для совместимости
3. **Внешние ID**: Все записи имеют `external_id` для синхронизации с API
4. **Гибкость**: Один `Schedule` может содержать занятия для разных групп
5. **Связность**: Четкие связи между всеми сущностями

## Проблемы текущей реализации

1. **Дублирование**: `Group.faculty` и `Group.speciality` дублируют данные из связанных таблиц
2. **Неполная нормализация**: Некоторые поля могут быть вынесены в справочники
3. **Отсутствие индексов**: Нужны индексы для быстрого поиска по группам
