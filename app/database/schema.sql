-- Database schema for SZGMU Schedule Bot

-- Users and Authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    telegram_username TEXT,
    full_name TEXT,
    access_level TEXT CHECK(access_level IN ('guest', 'basic', 'tester', 'admin')) DEFAULT 'guest',
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Academic Structure
CREATE TABLE IF NOT EXISTS faculties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    short_name TEXT,
    code TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS specialities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT,
    faculty_id INTEGER REFERENCES faculties(id),
    degree_type TEXT CHECK(degree_type IN ('bachelor', 'speciality', 'master')) DEFAULT 'speciality',
    study_years INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    course INTEGER,
    stream TEXT,
    faculty_id INTEGER REFERENCES faculties(id),
    speciality_id INTEGER REFERENCES specialities(id),
    current_semester TEXT CHECK(current_semester IN ('autumn', 'spring')),
    academic_year TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number, academic_year)
);

-- Student Profiles
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id),
    student_id TEXT,
    preferred_format TEXT DEFAULT 'xlsx',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teachers and Rooms
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    short_name TEXT,
    department TEXT,
    position TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    building TEXT,
    floor INTEGER,
    capacity INTEGER,
    equipment TEXT,  -- JSON array of equipment
    room_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(number, building)
);

-- Subjects and Schedule
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT,
    speciality_id INTEGER REFERENCES specialities(id),
    course INTEGER,
    semester TEXT CHECK(semester IN ('autumn', 'spring')),
    credits INTEGER,
    hours_total INTEGER,
    hours_lectures INTEGER,
    hours_seminars INTEGER,
    hours_practice INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER REFERENCES groups(id),
    subject_id INTEGER REFERENCES subjects(id),
    teacher_id INTEGER REFERENCES teachers(id),
    room_id INTEGER REFERENCES rooms(id),
    lesson_type TEXT CHECK(lesson_type IN ('lecture', 'seminar', 'practice', 'lab', 'exam', 'offset')),
    date TIMESTAMP NOT NULL,
    week_number INTEGER NOT NULL,
    day_of_week INTEGER CHECK(day_of_week BETWEEN 1 AND 7),
    lesson_number INTEGER,
    start_time TEXT,
    end_time TEXT,
    is_cancelled BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grades and Attendance
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES student_profiles(id),
    subject_id INTEGER REFERENCES subjects(id),
    grade_type TEXT CHECK(grade_type IN ('TSB', 'OSB', 'KNL', 'KNS', 'exam', 'offset', 'homework', 'essay')),
    grade_value TEXT NOT NULL,
    max_grade TEXT,
    date_recorded TIMESTAMP NOT NULL,
    semester TEXT CHECK(semester IN ('autumn', 'spring')),
    teacher_id INTEGER REFERENCES teachers(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES student_profiles(id),
    schedule_id INTEGER REFERENCES schedules(id),
    status TEXT CHECK(status IN ('present', 'absent', 'late', 'excused')) NOT NULL,
    notes TEXT,
    recorded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    plan TEXT CHECK(plan IN ('free', 'standard', 'premium')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_method TEXT,
    subscription_id TEXT,  -- ID in payment system
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initial Data: Faculties
INSERT INTO faculties (name, is_active) VALUES 
('Faculty of Medicine', 1),
('Faculty of Preventive Medicine', 1),
('Faculty of Dentistry', 1),
('Faculty of Medical and Biological', 1),
('Faculty of Postgraduate Education', 1)
ON CONFLICT(name) DO NOTHING;

-- Triggers for auto-updating timestamps
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users FOR EACH ROW
    BEGIN UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_faculties_timestamp 
    AFTER UPDATE ON faculties FOR EACH ROW
    BEGIN UPDATE faculties SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_specialities_timestamp 
    AFTER UPDATE ON specialities FOR EACH ROW
    BEGIN UPDATE specialities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_groups_timestamp 
    AFTER UPDATE ON groups FOR EACH ROW
    BEGIN UPDATE groups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_student_profiles_timestamp 
    AFTER UPDATE ON student_profiles FOR EACH ROW
    BEGIN UPDATE student_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_teachers_timestamp 
    AFTER UPDATE ON teachers FOR EACH ROW
    BEGIN UPDATE teachers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_subjects_timestamp 
    AFTER UPDATE ON subjects FOR EACH ROW
    BEGIN UPDATE subjects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_schedules_timestamp 
    AFTER UPDATE ON schedules FOR EACH ROW
    BEGIN UPDATE schedules SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_grades_timestamp 
    AFTER UPDATE ON grades FOR EACH ROW
    BEGIN UPDATE grades SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

CREATE TRIGGER IF NOT EXISTS update_subscriptions_timestamp 
    AFTER UPDATE ON subscriptions FOR EACH ROW
    BEGIN UPDATE subscriptions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id; END;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_groups_faculty ON groups(faculty_id);
CREATE INDEX IF NOT EXISTS idx_groups_speciality ON groups(speciality_id);
CREATE INDEX IF NOT EXISTS idx_schedules_group ON schedules(group_id);
CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(date);
CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_schedule ON attendance(schedule_id);
