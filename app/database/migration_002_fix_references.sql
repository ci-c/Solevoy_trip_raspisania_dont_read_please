-- Migration for fixing column references
-- Copyright (c) 2024 SZGMU Bot Project
-- See LICENSE for details.

-- Date: 2025-09-07
-- Description: Fixing faculty and speciality references

BEGIN TRANSACTION;

-- Drop foreign key constraints first
DROP TABLE IF EXISTS specialities_temp;
DROP TABLE IF EXISTS groups_temp;

-- Create new specialities table with correct references
CREATE TABLE specialities_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    faculty_id INTEGER,
    degree_type TEXT CHECK(degree_type IN ('bachelor', 'speciality', 'master')) DEFAULT 'speciality',
    study_years INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(faculty_id) REFERENCES faculties(id)
);

-- Copy data with correct faculty_id
INSERT INTO specialities_temp
SELECT id, code, name, full_name, faculty_id, degree_type, study_years, created_at, updated_at
FROM specialities;

-- Replace old table
DROP TABLE specialities;
ALTER TABLE specialities_temp RENAME TO specialities;

-- Create new groups table with correct references
CREATE TABLE groups_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    course INTEGER,
    stream TEXT,
    faculty_id INTEGER,
    speciality_id INTEGER,
    current_semester TEXT CHECK(current_semester IN ('autumn', 'spring')),
    academic_year TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(faculty_id) REFERENCES faculties(id),
    FOREIGN KEY(speciality_id) REFERENCES specialities(id),
    UNIQUE(number, academic_year)
);

-- Copy data with correct references
INSERT INTO groups_temp
SELECT id, number, course, stream, faculty_id, speciality_id, current_semester,
       academic_year, is_active, last_sync, created_at, updated_at
FROM groups;

-- Replace old table
DROP TABLE groups;
ALTER TABLE groups_temp RENAME TO groups;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_specialities_faculty ON specialities(faculty_id);
CREATE INDEX IF NOT EXISTS idx_groups_faculty ON groups(faculty_id);
CREATE INDEX IF NOT EXISTS idx_groups_speciality ON groups(speciality_id);

COMMIT;
