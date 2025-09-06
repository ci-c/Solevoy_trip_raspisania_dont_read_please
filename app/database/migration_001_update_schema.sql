-- Migration for updating schema structure
-- Date: 2025-09-07
-- Description: Adding initial settings
-- Note: Faculties and specialities are populated through the API by the application code

-- Default system settings
INSERT INTO settings (key, value, description) VALUES 
('bot_version', '2.0.0', 'Bot version'),
('schedule_sync_enabled', 'true', 'Enable automatic schedule synchronization'),
('schedule_sync_interval_hours', '6', 'Schedule sync interval in hours'),
('max_schedule_cache_days', '30', 'Maximum days to keep schedule cache'),
('maintenance_mode', 'false', 'Maintenance mode'),
('current_semester', 'autumn', 'Current semester'),
('current_academic_year', '2024/2025', 'Current academic year')
ON CONFLICT(key) DO UPDATE SET 
    value = excluded.value,
    description = excluded.description;