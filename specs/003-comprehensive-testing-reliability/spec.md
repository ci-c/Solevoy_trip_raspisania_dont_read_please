# Feature Specification: Comprehensive Testing & Reliability Guarantees

**Feature Branch**: `003-comprehensive-testing-reliability`
**Created**: 2025-11-18
**Status**: In Progress
**Input**: User description: "Comprehensive testing, reliability guarantees, and business logic documentation - achieve 80% test coverage, ensure handlers work with real Telegram messages, verify database operations, and document all critical business flows"

> This specification establishes production-grade reliability through comprehensive test coverage, architectural guarantees, and business logic documentation. Aligns with Constitution Principle IV (Tests Before Code - Non-Negotiable) and ensures system resilience.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New User Onboarding Works Reliably (Priority: P0 - Critical)

**CURRENT PROBLEM**: First user message can fail if DB empty, permissions wrong, or validation breaks.

New user sends /start to bot and successfully registers, selects group, and views schedule without any failures, even on first run with empty database.

**Why this priority**: First user interaction determines if bot works at all. Currently 0% test coverage, high risk of failure in production.

**Independent Test**: Integration test in `tests/integration/test_user_onboarding.py`:
- test_first_user_registration_empty_db
- test_user_registration_creates_profile
- test_user_activity_tracking
- test_group_selection_flow_complete
- test_schedule_view_after_group_selection
- test_error_handling_db_failure
- test_error_handling_invalid_input

**Acceptance Scenarios**:

1. **Given** empty database, **When** user sends /start, **Then** database initializes, user creates, profile creates, main menu displays
2. **Given** existing user, **When** user sends /start, **Then** last_seen updates, existing profile loads, main menu displays
3. **Given** database permission error, **When** user sends /start, **Then** clear error message shown, app doesn't crash
4. **Given** invalid telegram data, **When** message received, **Then** validation catches error, user-friendly message shown

---

### User Story 2 - Group Selection Works With Real Data (Priority: P0 - Critical)

**CURRENT PROBLEM**: Group selection depends on API sync. If faculties table empty or sync failed, user stuck.

User selects faculty, sees available groups, selects group, and assignment persists correctly in database.

**Why this priority**: Users cannot use bot without group assignment. Currently 0% test coverage for this critical path.

**Independent Test**: Integration test in `tests/integration/test_group_selection.py`:
- test_faculty_list_from_database
- test_group_list_for_faculty
- test_group_assignment_persists
- test_empty_faculty_list_handled
- test_no_groups_for_faculty_handled
- test_invalid_group_number_rejected
- test_concurrent_group_selection
- test_group_change_updates_schedule

**Acceptance Scenarios**:

1. **Given** faculties in database, **When** user requests group setup, **Then** faculty list displays with inline keyboard
2. **Given** selected faculty, **When** user selects it, **Then** groups for faculty load from database and display
3. **Given** selected group, **When** user confirms, **Then** user.group_id updates, user_profile updates, success message shows
4. **Given** empty faculties table, **When** user requests group setup, **Then** informative message about sync needed, no crash

---

### User Story 3 - Schedule Viewing Works Reliably (Priority: P0 - Critical)

**CURRENT PROBLEM**: Complex JOINs, nullable FKs, empty schedules can cause failures.

User views their schedule for today/week and sees correctly formatted lessons with all details (lecturer, room, subject).

**Why this priority**: Primary bot feature. Complex database queries with multiple JOINs = high failure risk.

**Independent Test**: Integration test in `tests/integration/test_schedule_viewing.py`:
- test_schedule_view_with_lessons
- test_schedule_view_empty_schedule
- test_schedule_view_missing_related_data
- test_schedule_date_filtering
- test_schedule_view_no_group_assigned
- test_schedule_complex_joins_work
- test_schedule_nullable_fks_handled

**Acceptance Scenarios**:

1. **Given** user with assigned group and schedule data, **When** user requests schedule, **Then** lessons display with subject, lecturer, room, time
2. **Given** user with assigned group but no schedule data, **When** user requests schedule, **Then** "no lessons" message shows, no error
3. **Given** lesson with missing lecturer FK, **When** schedule loads, **Then** lesson shows with placeholder for lecturer, no crash
4. **Given** user without assigned group, **When** user requests schedule, **Then** prompt to select group first

---

### User Story 4 - Database Operations Are Transaction-Safe (Priority: P0 - Critical)

**CURRENT PROBLEM**: No transaction management tests. Concurrent writes could corrupt data.

All database write operations complete atomically or rollback completely on errors, maintaining data consistency.

**Why this priority**: Data corruption would require manual DB fixes. Constitution Principle I requires canonical data discipline.

**Independent Test**: Unit tests in `tests/unit/test_database_operations.py`:
- test_user_creation_transactional
- test_group_assignment_rollback_on_error
- test_concurrent_writes_no_corruption
- test_schedule_sync_atomic
- test_foreign_key_constraints_enforced
- test_unique_constraints_enforced
- test_database_connection_pool

**Acceptance Scenarios**:

1. **Given** user creation partially fails, **When** transaction rolls back, **Then** no partial user record exists
2. **Given** concurrent group assignments, **When** both succeed, **Then** both users have correct group_id, no data race
3. **Given** FK constraint violation, **When** insert attempted, **Then** IntegrityError raised, database state unchanged

---

### User Story 5 - API Sync Handles Failures Gracefully (Priority: P0 - Critical)

**CURRENT PROBLEM**: Background sync with SZGMU API has no error handling tests. Partial sync could leave DB inconsistent.

Background API sync fetches data from SZGMU, validates it, and updates database with proper error handling and rollback.

**Why this priority**: Group selection depends on this data. If sync breaks silently, bot becomes useless.

**Independent Test**: Integration test in `tests/integration/test_api_sync.py`:
- test_api_sync_full_success
- test_api_sync_api_down_handled
- test_api_sync_invalid_response_handled
- test_api_sync_partial_failure_rolls_back
- test_api_sync_network_timeout_handled
- test_api_sync_rate_limiting_handled
- test_api_sync_concurrent_sync_prevented

**Acceptance Scenarios**:

1. **Given** SZGMU API online, **When** sync runs, **Then** faculties, groups, schedules update in database with APISyncLog entry
2. **Given** SZGMU API returns 500 error, **When** sync runs, **Then** error logged, database unchanged, retry scheduled
3. **Given** SZGMU API returns invalid JSON, **When** sync runs, **Then** ValidationError logged, database unchanged
4. **Given** partial sync (faculties succeed, groups fail), **When** error occurs, **Then** transaction rolls back, database consistent

---

### User Story 6 - Error Handling Prevents Bot Crashes (Priority: P0 - Critical)

**CURRENT PROBLEM**: Global error handler exists but untested. Unknown if it actually prevents crashes.

Any unhandled exception in handlers gets caught, logged with context, and user sees friendly error message without bot crashing.

**Why this priority**: Constitution Principle V requires resilient operations. Bot must stay running despite errors.

**Independent Test**: Integration test in `tests/integration/test_error_handling.py`:
- test_database_error_caught_and_logged
- test_validation_error_shows_user_message
- test_telegram_api_error_handled
- test_generic_exception_caught
- test_async_deadlock_timeout
- test_error_logging_includes_context
- test_user_gets_helpful_message

**Acceptance Scenarios**:

1. **Given** database connection lost, **When** handler executes, **Then** error caught, logged, user sees "temporary issue, try again"
2. **Given** validation error on input, **When** handler executes, **Then** user sees specific validation message, no crash
3. **Given** unexpected exception, **When** handler executes, **Then** error logged with traceback, user sees generic error, bot continues

---

### User Story 7 - Async Orchestration Works Correctly (Priority: P1 - High)

**CURRENT PROBLEM**: No tests for async patterns. Deadlocks, race conditions possible.

All async operations (handlers, services, background tasks) complete successfully without deadlocks or race conditions.

**Why this priority**: Constitution Principle II requires correct async orchestration. Deadlocks would hang bot.

**Independent Test**: Integration test in `tests/integration/test_async_operations.py`:
- test_concurrent_message_handling
- test_background_task_doesnt_block_handlers
- test_database_connection_pool_limits
- test_async_timeout_prevents_hang
- test_service_layer_async_patterns
- test_no_blocking_calls_in_handlers

**Acceptance Scenarios**:

1. **Given** multiple users send messages simultaneously, **When** handlers execute, **Then** all complete without blocking each other
2. **Given** long-running background sync, **When** user sends message, **Then** handler responds immediately, not blocked
3. **Given** database pool exhausted, **When** new request comes, **Then** waits for connection or times out gracefully

---

### User Story 8 - Services Return Correct Data (Priority: P1 - High)

**CURRENT PROBLEM**: Service layer has minimal tests. Business logic could be wrong.

All service methods (UserService, ScheduleService, GroupService) return correct data matching business rules.

**Why this priority**: Services implement business logic. Wrong logic = wrong bot behavior.

**Independent Test**: Unit tests in `tests/unit/test_services/`:
- test_user_service_all_methods.py
- test_schedule_service_all_methods.py
- test_group_service_all_methods.py
- test_faculty_service_all_methods.py
- test_grade_calculator_service.py

**Acceptance Scenarios**:

1. **Given** valid user_id, **When** UserService.get_user_by_telegram_id called, **Then** returns User object or None correctly
2. **Given** group_id and date range, **When** ScheduleService.get_group_schedule called, **Then** returns lessons filtered correctly
3. **Given** grades for subject, **When** GradeCalculatorService.calculate_tsb called, **Then** calculation matches SZGMU rules

---

### Edge Cases

- What if database file corrupted? → app detects and recreates with error log
- What if Telegram API changes message format? → validation catches, logs schema mismatch
- What if user spams bot with 1000 messages/second? → rate limiter blocks, user gets warning
- What if two users select same group simultaneously? → transactions handle, both succeed
- What if background sync runs during active user session? → connection pool handles, no blocking
- What if user enters SQL injection attempt? → parameterized queries prevent, validation rejects
- What if async handler never completes? → timeout decorator prevents hang

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST have 80%+ code coverage for app/ directory (Principle IV - Tests Before Code).
- **FR-002**: All P0 critical flows MUST have integration tests covering happy path + error scenarios (Principle IV).
- **FR-003**: Database operations MUST be tested for transaction safety and rollback on errors (Principle I - Canonical Data).
- **FR-004**: API sync MUST handle all failure scenarios (API down, invalid data, timeout) gracefully (Principle V - Resilience).
- **FR-005**: Error handling MUST be tested to prevent bot crashes and log context (Principle V - Transparency).
- **FR-006**: Async operations MUST be tested for deadlocks and race conditions (Principle II - Async Orchestration).
- **FR-007**: All service methods MUST have unit tests verifying business logic correctness.
- **FR-008**: Handler tests MUST use aiogram TestClient or mocks to simulate real Telegram messages.
- **FR-009**: Tests MUST run in CI/CD pipeline as quality gate before merge (Principle IV).
- **FR-010**: Business logic MUST be documented in service docstrings referencing SZGMU regulations.

### Key Entities

- **TestFixtures**: Reusable test data (users, groups, schedules) for consistent testing
- **MockTelegramClient**: Simulates Telegram API for handler testing
- **TestDatabase**: Isolated test database per test run
- **CoverageReport**: pytest-cov report showing 80%+ coverage

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Test coverage reaches 80%+ for app/ directory (verified by pytest-cov).
- **SC-002**: All 8 P0 critical flows have integration tests with happy path + 3+ error scenarios each (minimum 32 tests).
- **SC-003**: All database operations have transactional tests (minimum 10 tests).
- **SC-004**: API sync has failure scenario tests covering API down, invalid data, timeout (minimum 6 tests).
- **SC-005**: Error handling tests verify all error types caught and logged (minimum 7 tests).
- **SC-006**: Async operation tests verify no deadlocks under concurrent load (minimum 6 tests).
- **SC-007**: Service layer has unit tests for all public methods (minimum 50 tests).
- **SC-008**: Handler tests simulate real Telegram messages using aiogram test tools (minimum 20 tests).
- **SC-009**: CI pipeline includes pytest run that must pass before merge.
- **SC-010**: Zero P0 critical paths remain without tests.

All outcomes verified through automated test execution and coverage reports.
