# Tasks: SZGMU Schedule Bot Baseline

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`
**Prerequisites**: Constitution Check выполнен; тестовые артефакты подготовлены

> Требования: задачи сгруппированы по user stories, тесты пишутся и падают до реализации. Все пути указываются явно.

## Phase 0: Pre-Implementation Validation

- [ ] T000 Проверить чек-лист конституции в `plan.md`, зафиксировать результаты
- [ ] T001 Подготовить фикстуры расписаний/профилей в `tests/fixtures/`
- [ ] T002 Спайк-парсер PDF → таблицы, выбрать библиотеку (например, camelot) и оформить вывод

---

## Phase 1: Shared Infrastructure

- [ ] T010 Обновить модели SQLAlchemy (`app/database/models.py`) согласно `data-model.md` (UserProfile, ScheduleLesson с FK на Lecturer/Room, Lecturer, Room, NotificationJob, ExportRequest)
- [ ] T011 Написать миграции/сидеры в `data/` для AcademicGroup, ScheduleLesson, Lecturer, Room
- [ ] T012 Настроить `app/utils/logging.py` для correlation IDs, таймаутов httpx, ретраев
- [ ] T013 Проверить совместимость зависимостей с Python 3.14, обновить `uv.lock`
- [ ] T014 Обновить пайплайн импорта в `app/schedule/ingest/` для создания/обновления сущностей Lecturer/Room и маркировки источников
- [ ] T015 Реализовать очистку завершённых `ExportRequest`/`NotificationJob` (удаление записей + логирование результата)

---

## Phase 2: User Story 1 — Просмотр расписания (P1)

### Tests (write first, ensure red)
- [ ] T020 [P] Добавить unit-тест `tests/unit/services/test_schedule_service.py::test_fetch_day_schedule_returns_canonical_data`
- [ ] T021 [P] Добавить integration-тест `tests/integration/bot/test_schedule_commands.py::test_schedule_today_flow`

### Implementation
- [ ] T022 Обновить `app/services/schedule.py` для чтения только из БД, учитывая параметры профиля
- [ ] T023 Добавить/рефакторить хендлеры `/schedule` в `app/bot/handlers/schedule.py`
- [ ] T024 Обеспечить локализацию и обработку ошибок (Принцип III) в хендлерах
- [ ] T025 Актуализировать документацию `docs/group_search_and_reports_plan.md` при необходимости

**Checkpoint**: Тесты T020–T021 зелёные, сценарий `/schedule` работает.

---

## Phase 3: User Story 2 — Экспорт расписания (P2)

### Tests
- [ ] T030 [P] Добавить unit-тест `tests/unit/services/test_export_service.py::test_generate_week_excel_matches_canonical_dataset`
- [ ] T031 [P] Добавить integration-тест `tests/integration/bot/test_export_commands.py::test_export_week_command_sends_files`

### Implementation
- [ ] T032 Реализовать/обновить `app/services/export.py` с использованием ScheduleService
- [ ] T033 Добавить команды/клавиатуры для экспорта в `app/bot/handlers/export.py`
- [ ] T034 Обновить `app/schedule/exporters` (Excel/ICS) под новые данные
- [ ] T035 Добавить логирование экспортов с correlation ID (Принцип V)
- [ ] T036 Убедиться, что по завершении экспорта запись удаляется и событие логируется (соответствие FR-012)

**Checkpoint**: Тесты T030–T031 зелёные, файлы `.xlsx`/`.ics` корректны.

---

## Phase 4: User Story 3 — Профиль и уведомления (P3)

### Tests
- [ ] T040 [P] Добавить unit-тест `tests/unit/services/test_profile_service.py::test_update_preferences_persists_state`
- [ ] T041 [P] Добавить integration-тест `tests/integration/notifications/test_schedule_notifications.py::test_daily_notification_honors_preferences`

### Implementation
- [ ] T042 Реализовать `app/services/profile.py` с поддержкой тихих часов и форматов
- [ ] T043 Добавить диалоги/клавиатуры в `app/bot/handlers/profile.py`
- [ ] T044 Настроить планировщик уведомлений (например, APScheduler) в `app/schedule/notifications.py`
- [ ] T045 Обновить фоновые воркеры для уважения тихих часов и таймзон
- [ ] T046 Удалять записи `NotificationJob` после успешной отправки, избегая повторов

**Checkpoint**: Тесты T040–T041 зелёные, уведомления работают с настройками профиля.

---

## Phase N: Cross-Cutting Polish

- [ ] T100 Актуализировать README, quickstart, docs по новым настройкам
- [ ] T101 Настроить мониторинг импортов и уведомлений (алерты)
- [ ] T102 Провести проход `uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, `uv run pytest`
- [ ] T103 Подготовить релизные заметки и миграционные инструкции

---

## Notes

- Маркер [P] означает возможность параллельного выполнения (разные файлы/области).
- Каждый блок завершать после прохождения тестов и ревью на соответствие конституции.
- Все отклонения фиксировать в Complexity Tracking и задачах, прежде чем переходить к следующей фазе.
