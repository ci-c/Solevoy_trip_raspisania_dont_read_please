# Data Model Sketch: SZGMU Schedule Bot Baseline

**Date**: 2025-10-10  
**Owner**: Lead Engineer

## Scope

Описание доменных сущностей и связей, необходимых для реализации спецификации baseline: расписание, профили, экспорты, уведомления. Используем Python 3.14, SQLAlchemy 2.0, SQLite в качестве основной БД.

## Entities

### User
- **Fields**: `id`, `telegram_id`, `full_name`, `created_at`, `updated_at`
- **Relationships**: One-to-one с `UserProfile`
- **Notes**: Сущность уже присутствует; нужно проверить наличие индексов по `telegram_id`.

### UserProfile
- **Fields**: `user_id`, `group_id`, `preferred_export_format`, `notifications_enabled`, `quiet_hours_start`, `quiet_hours_end`, `timezone`
- **Rules**:
  - `preferred_export_format` ∈ {`excel`, `ics`}; default `excel`.
  - `notifications_enabled` bool; default `False`.
  - `quiet_hours_start`, `quiet_hours_end` nullable. Если оба null — тихие часы выключены.
  - `timezone` default `Europe/Moscow`, но хранится строкой для будущей персонализации.

### AcademicGroup
- **Fields**: `id`, `code`, `name`, `faculty`, `course`, `created_at`, `updated_at`
- **Notes**: Код должен совпадать с идентификаторами из официальных таблиц; требуется уникальный индекс.

### ScheduleLesson
- **Fields**: `id`, `group_id`, `date`, `start_time`, `end_time`, `subject`, `lesson_type`, `lecturer`, `room`, `source`, `imported_at`
- **Rules**:
  - `source` ∈ {`official_pdf`, `legacy_csv`, `external_api`}; хранить для аудита.
  - Уникальный индекс по (`group_id`, `date`, `start_time`, `subject`, `room`) для предотвращения дублей.
  - `imported_at` хранит timestamp последнего обновления записи.

### ScheduleImportJob
- **Fields**: `id`, `source`, `status`, `started_at`, `finished_at`, `error_message`
- **Purpose**: Логирование попыток загрузки расписания (PDF → БД, API → БД).
- **Status Enum**: `pending`, `running`, `succeeded`, `failed`.

### ExportRequest
- **Fields**: `id`, `user_id`, `group_id`, `from_date`, `to_date`, `format`, `status`, `created_at`, `completed_at`
- **Notes**: Служит для аудита экспортов и отладки. `status`: `queued`, `processing`, `done`, `failed`.

### NotificationJob
- **Fields**: `id`, `user_id`, `lesson_id`, `scheduled_for`, `status`, `attempts`, `last_error`
- **Notes**: Планируем отправку уведомлений; учитываем `quiet_hours` перед постановкой в очередь.

## Relationships Diagram (textual)

```
User 1 — 1 UserProfile
User 1 — * ExportRequest
User 1 — * NotificationJob
AcademicGroup 1 — * UserProfile
AcademicGroup 1 — * ScheduleLesson
ScheduleLesson 1 — * NotificationJob
ScheduleImportJob (no direct FK)
```

## Constraints & Indexes

- `User.telegram_id` UNIQUE
- `AcademicGroup.code` UNIQUE
- Composite index on `ScheduleLesson (group_id, date, start_time)`
- Index on `ScheduleLesson (lecturer)`, `ScheduleLesson (room)` для будущих поисков
- Index on `NotificationJob (scheduled_for, status)` для фоновых воркеров

## Data Flow Overview

1. **Ingestion**
   - Планировщик запускает `ScheduleImportJob` для официальных PDF. Парсер сохраняет данные в `ScheduleLesson` с `source=official_pdf`.
   - При недоступности официальных данных запускается импорт из неофициального API (`source=external_api`). После успешной загрузки ретеншн: помечаем источник и записываем `imported_at`.

2. **Schedule Query**
   - aiogram-хэндлеры вызывают сервис `ScheduleService`, который читает из `ScheduleLesson` (по `group_id`, `date`).
   - Сервис гарантирует возвращение данных только из БД и учитывает `UserProfile` настройки.

3. **Exports**
   - `ExportService` формирует временные файлы на основе запросов `ExportRequest`. Метаданные сохраняются для трассировки.
   - По завершении экспорт удаляется или архивируется в зависимости от политики хранения (обсудить отдельно).

4. **Notifications**
   - Фоновый воркер планирует `NotificationJob` для будущих занятий. При постановке учитываются `quiet_hours_start/end` и `timezone`. Если уведомление попадает в тихие часы, оно переносится.

## Open Questions

- Нужно ли хранить историю тихих часов или достаточно текущих значений?
- Как долго хранить записи `ExportRequest` и `NotificationJob`? Нужна политика очистки.
- Требуются ли отдельные сущности для преподавателей/аудиторий (связи 1:N) или достаточно строки?

## Next Steps

- Провести ревью модели с командой, согласовать индексы и возможные миграции.
- Подготовить миграции (создание/обновление таблиц) и сидеры для AcademicGroup и ScheduleLesson.
- Определить схемы сериализации для экспорта (Pydantic-модели) и уведомлений.
