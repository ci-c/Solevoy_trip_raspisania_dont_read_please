# Исправленная структура БД SZGMU Bot

## Основные изменения:

1. **Группы создаются из расписаний** - добавлена связь `groups.source_schedule_id`
2. **Убраны legacy поля** - только нормализованные связи
3. **Правильная иерархия** - Schedule → Lessons → Groups
4. **Добавлены индексы** для производительности

## Диаграмма структуры:

```mermaid
erDiagram
    %% Справочные таблицы
    Faculty ||--o{ Speciality : "содержит"
    Faculty ||--o{ Department : "имеет"
    Department ||--o{ Lecturer : "содержит"
    Speciality ||--o{ Subject : "имеет предметы"
    
    AcademicYear ||--o{ Semester : "содержит"
    AcademicYear ||--o{ Schedule : "имеет расписания"
    Semester ||--o{ Schedule : "имеет расписания"
    Speciality ||--o{ Schedule : "имеет расписания"
    
    %% Основной поток: API → Schedule → Lessons → Groups
    Schedule ||--o{ Lesson : "содержит занятия"
    Schedule ||--o{ Group : "создает группы"
    Lesson }o--|| Group : "принадлежит группе"
    
    %% Связи занятий со справочниками
    Lesson }o--|| Subject : "имеет предмет"
    Lesson }o--|| LessonType : "имеет тип"
    Lesson }o--o| Lecturer : "ведет преподаватель"
    Lesson }o--o| Classroom : "проходит в аудитории"
    Lesson }o--o| Department : "от кафедры"
    
    %% Пользователи и профили
    User ||--o| StudentProfile : "имеет профиль"
    StudentProfile }o--|| Group : "принадлежит группе"
    
    %% Оценки и посещаемость
    StudentProfile ||--o{ Grade : "имеет оценки"
    StudentProfile ||--o{ Attendance : "имеет посещаемость"
    Grade }o--|| Lesson : "за конкретное занятие"
    Attendance }o--|| Lesson : "за конкретное занятие"
    
    %% Таблицы
    Faculty {
        int id PK
        string name "Название факультета"
        string code "Код факультета"
        boolean is_active
    }
    
    Speciality {
        int id PK
        string code "31.05.01"
        string name "Лечебное дело"
        int faculty_id FK
        boolean is_active
    }
    
    AcademicYear {
        int id PK
        string name "2024/2025"
        boolean is_current
    }
    
    Semester {
        int id PK
        string name "осенний"
        int academic_year_id FK
        boolean is_current
    }
    
    Schedule {
        int id PK
        int external_id "ID из API"
        string file_name "Имя файла"
        int form_type "1=лекции, 2=практики"
        string status "APPROVED/DRAFT"
        int academic_year_id FK
        int semester_id FK
        int speciality_id FK
    }
    
    Group {
        int id PK
        string name "105а"
        int course "Курс"
        string stream "А, Б, В"
        string subgroup "а, б, в"
        int faculty_id FK
        int speciality_id FK
        int source_schedule_id FK "Откуда создана"
        boolean is_active
    }
    
    Lesson {
        int id PK
        int external_id "ID из API"
        string day_name "пн, вт, ср"
        int week_number "1, 2, 3..."
        string pair_time "9:00-10:30"
        int schedule_id FK
        int group_id FK "Группа занятия"
        int subject_id FK
        int lesson_type_id FK
        int lecturer_id FK
        int classroom_id FK
        string subgroup "241б из API"
        string study_group "МПФ из API"
    }
    
    Subject {
        int id PK
        string name "Анатомия"
        string code "АНАТ.01"
        int speciality_id FK
        int course "Курс предмета"
    }
    
    Lecturer {
        int id PK
        string name "Иванов И.И."
        int department_id FK
        string position "доцент"
    }
    
    Classroom {
        int id PK
        string number "101"
        string building "Главный корпус"
        int capacity "Количество мест"
    }
    
    User {
        int id PK
        int telegram_id "ID в Telegram"
        string username "Username"
        string first_name "Имя"
        string access_level "guest/basic/admin"
    }
    
    StudentProfile {
        int id PK
        int user_id FK
        int group_id FK
        string student_id "Номер студбилета"
        boolean notifications_enabled
    }
    
    Grade {
        int id PK
        int student_id FK
        int subject_id FK
        int lesson_id FK
        string grade_type "TSB, OSB, exam"
        string grade_value "5, 4, 3, 2"
        datetime date_recorded
    }
    
    Attendance {
        int id PK
        int student_id FK
        int lesson_id FK
        string status "present/absent/late"
        boolean is_excused
        string reason "Причина отсутствия"
    }
```

## Процесс создания групп:

### 1. Синхронизация с API
```
API СЗГМУ → Schedule (расписания) → Lessons (занятия)
```

### 2. Извлечение групп из занятий
```python
# Псевдокод
for lesson in lessons:
    group_name = lesson.study_group  # "105а"
    subgroup = lesson.subgroup       # "241б"
    
    # Создать группу если не существует
    group = find_or_create_group(
        name=group_name,
        course=extract_course(group_name),
        stream=extract_stream(group_name),
        subgroup=subgroup,
        faculty_id=lesson.schedule.speciality.faculty_id,
        speciality_id=lesson.schedule.speciality_id,
        source_schedule_id=lesson.schedule_id
    )
    
    # Привязать занятие к группе
    lesson.group_id = group.id
```

### 3. Связывание пользователей
```python
# Пользователь выбирает группу
user_profile.group_id = selected_group.id
```

## Ключевые улучшения:

1. **Группы создаются автоматически** из расписаний
2. **Нет дублирования данных** - только нормализованные связи
3. **Правильная иерархия** - Schedule → Lessons → Groups
4. **Отслеживание источника** - `source_schedule_id` показывает откуда создана группа
5. **Гибкость** - один Schedule может создавать несколько групп
6. **Производительность** - добавлены индексы для быстрого поиска
