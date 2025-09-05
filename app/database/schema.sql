-- Схема базы данных СЗГМУ Schedule Bot

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    telegram_username TEXT,
    full_name TEXT,
    access_level TEXT DEFAULT 'guest' CHECK(access_level IN ('guest', 'basic', 'tester', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP
);

-- Направления подготовки (специальности)
CREATE TABLE IF NOT EXISTS specialities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL, -- 31.05.01
    name TEXT NOT NULL, -- "лечебное дело"
    full_name TEXT, -- "31.05.01 лечебное дело"
    faculty TEXT, -- факультет
    degree_type TEXT DEFAULT 'speciality' CHECK(degree_type IN ('bachelor', 'speciality', 'master')),
    study_years INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Группы студентов
CREATE TABLE IF NOT EXISTS study_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL, -- "103а"
    course INTEGER NOT NULL,
    stream TEXT NOT NULL, -- "а", "б", "в"
    speciality_id INTEGER REFERENCES specialities(id),
    current_semester TEXT CHECK(current_semester IN ('осенний', 'весенний')),
    academic_year TEXT, -- "2024/2025"
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number, academic_year)
);

-- Профили студентов
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES study_groups(id),
    student_id TEXT, -- номер студенческого билета
    preferred_format TEXT DEFAULT 'xlsx',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Инвайты
CREATE TABLE IF NOT EXISTS invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    created_by INTEGER REFERENCES users(id),
    access_level TEXT DEFAULT 'basic' CHECK(access_level IN ('basic', 'tester', 'admin')),
    max_uses INTEGER, -- NULL = неограниченно
    current_uses INTEGER DEFAULT 0,
    expires_at TIMESTAMP, -- NULL = бессрочный
    is_active BOOLEAN DEFAULT TRUE,
    metadata TEXT, -- JSON для дополнительной информации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Использование инвайтов
CREATE TABLE IF NOT EXISTS invitation_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invitation_id INTEGER REFERENCES invitations(id),
    user_id INTEGER REFERENCES users(id),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(invitation_id, user_id)
);

-- Подписки пользователей
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan TEXT CHECK(plan IN ('free', 'standard', 'premium')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_method TEXT,
    subscription_id TEXT, -- ID в платежной системе
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Преподаватели
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    short_name TEXT,
    department TEXT,
    position TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Аудитории
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    building TEXT,
    floor INTEGER,
    capacity INTEGER,
    equipment TEXT, -- JSON список оборудования
    room_type TEXT, -- лекционная, семинарская, лабораторная
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number, building)
);

-- Предметы
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT,
    speciality_id INTEGER REFERENCES specialities(id),
    course INTEGER,
    semester TEXT CHECK(semester IN ('осенний', 'весенний')),
    credits INTEGER,
    hours_total INTEGER,
    hours_lectures INTEGER,
    hours_seminars INTEGER,
    hours_practice INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Расписания (источники данных)
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT UNIQUE, -- ID из внешнего API
    file_name TEXT,
    schedule_type TEXT CHECK(schedule_type IN ('lectures', 'seminars', 'practice', 'mixed')),
    speciality_id INTEGER REFERENCES specialities(id),
    course INTEGER,
    semester TEXT CHECK(semester IN ('осенний', 'весенний')),
    academic_year TEXT,
    raw_data TEXT, -- JSON исходных данных
    parsed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Занятия (парсированные из расписаний)
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER REFERENCES schedules(id),
    subject_id INTEGER REFERENCES subjects(id),
    teacher_id INTEGER REFERENCES teachers(id),
    room_id INTEGER REFERENCES rooms(id),
    group_id INTEGER REFERENCES study_groups(id),
    
    lesson_type TEXT CHECK(lesson_type IN ('lecture', 'seminar', 'practice', 'exam', 'consultation')),
    subgroup TEXT, -- подгруппа внутри группы
    
    week_number INTEGER NOT NULL,
    day_of_week INTEGER CHECK(day_of_week BETWEEN 1 AND 7),
    day_name TEXT,
    time_start TEXT NOT NULL,
    time_end TEXT NOT NULL,
    
    duration_minutes INTEGER,
    is_online BOOLEAN DEFAULT FALSE,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Оценки студентов
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES student_profiles(id),
    subject_id INTEGER REFERENCES subjects(id),
    grade INTEGER CHECK(grade BETWEEN 2 AND 5),
    grade_type TEXT DEFAULT 'current' CHECK(grade_type IN ('current', 'midterm', 'final', 'exam')),
    control_point TEXT,
    date_received DATE DEFAULT CURRENT_DATE,
    teacher_id INTEGER REFERENCES teachers(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Посещаемость студентов
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES student_profiles(id),
    lesson_id INTEGER REFERENCES lessons(id),
    is_present BOOLEAN NOT NULL,
    is_excused BOOLEAN DEFAULT FALSE,
    excuse_reason TEXT,
    excuse_document TEXT,
    date_marked DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, lesson_id)
);

-- Домашние задания и задачи
CREATE TABLE IF NOT EXISTS homework (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES student_profiles(id),
    subject_id INTEGER REFERENCES subjects(id),
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'overdue')),
    priority INTEGER DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Системные настройки
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи действий пользователей
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    details TEXT, -- JSON с деталями
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Кэш поисковых запросов
CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT UNIQUE NOT NULL,
    query_params TEXT, -- JSON параметров поиска
    results TEXT, -- JSON результатов
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_lessons_group_week ON lessons(group_id, week_number);
CREATE INDEX IF NOT EXISTS idx_lessons_schedule_type ON lessons(schedule_id, lesson_type);
CREATE INDEX IF NOT EXISTS idx_grades_student_subject ON grades(student_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date_marked);
CREATE INDEX IF NOT EXISTS idx_invitations_code ON invitations(code) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_activity_log_user_date ON activity_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_search_cache_expires ON search_cache(expires_at);

-- Триггеры для автоматического обновления timestamps
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
    FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_student_profiles_timestamp 
    AFTER UPDATE ON student_profiles
    FOR EACH ROW
BEGIN
    UPDATE student_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;