-- Add faculties table
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

-- Add faculty_id to groups table if not exists
ALTER TABLE study_groups ADD COLUMN faculty_id INTEGER REFERENCES faculties(id);

-- Create trigger for updating timestamps
CREATE TRIGGER IF NOT EXISTS update_faculties_timestamp 
    AFTER UPDATE ON faculties
    FOR EACH ROW
BEGIN
    UPDATE faculties SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Add default faculties
INSERT INTO faculties (name, is_active) VALUES 
    ('Медико-профилактический факультет', 1),
    ('Лечебный факультет', 1),
    ('Стоматологический факультет', 1),
    ('Медико-биологический факультет', 1),
    ('Факультет постдипломного образования', 1)
ON CONFLICT(name) DO NOTHING;
