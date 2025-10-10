---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`

> Organize tasks so each user story can ship independently and in compliance with the constitution. Tests for every story MUST be scheduled before implementation (Principle IV).

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Task can proceed in parallel (different files, no dependencies)
- **[Story]**: User story identifier (US1, US2, …)
- Include full file paths (`app/...`, `tests/...`, `data/...`) in descriptions
- Call out Principle references when relevant to highlight compliance

## Phase 0: Pre-Implementation Validation

- [ ] T000 Confirm Constitution Check outcomes from `plan.md` (Principles I–V) and record any follow-ups in Complexity Tracking
- [ ] T001 Prepare fixtures/seeds in `tests/fixtures/` or `data/` required to exercise canonical schedule data

---

## Phase 1: Shared Infrastructure (Blocking)

**Purpose**: Work that every user story depends on. Complete before story implementation begins.

- [ ] T010 Update/extend services in `app/services/` to expose required async operations (Principle II)
- [ ] T011 Adjust schedule ingestion or migrations if needed in `app/schedule/` and `app/database/` (Principle I)
- [ ] T012 Configure logging/observability scaffolding in `app/utils/` or `app/bot/` to capture new events (Principle V)
- [ ] T013 Update configuration (`config.yaml`, `.env.example`) if new settings are introduced, documenting changes

---

## Phase 2: User Story 1 - [Title] (Priority: P1) 🎯

**Goal**: [Describe delivered student value]

**Independent Test**: [List failing tests authored before implementation]

### Tests (MANDATORY – write & watch them fail before coding)

- [ ] T020 [P] [US1] Add unit test in `tests/unit/` covering core logic
- [ ] T021 [P] [US1] Add integration test in `tests/integration/` simulating the Telegram flow

### Implementation

- [ ] T022 [US1] Implement async handler/menu updates in `app/bot/handlers/`
- [ ] T023 [US1] Extend service layer in `app/services/`
- [ ] T024 [US1] Update schedule/data access in `app/schedule/` or `app/database/` if required
- [ ] T025 [US1] Ensure logging, error handling, and preference usage conform to Principles III & V

**Checkpoint**: US1 tests pass; bot flow deliverable independently.

---

## Phase 3: User Story 2 - [Title] (Priority: P2)

**Goal**: [Describe delivered student value]

**Independent Test**: [List failing tests]

### Tests (MANDATORY)

- [ ] T030 [P] [US2] Add/extend unit tests in `tests/unit/`
- [ ] T031 [P] [US2] Add integration test or background job test in `tests/integration/`

### Implementation

- [ ] T032 [US2] Update handlers/services/modules as needed (cite file paths)
- [ ] T033 [US2] Persist or respect profile preferences (Principle III)
- [ ] T034 [US2] Update exports/notifications/logging if impacted (Principle V)

**Checkpoint**: US1 + US2 both pass independently.

---

## Phase 4: User Story 3 - [Title] (Priority: P3)

Repeat the pattern above for additional stories, ensuring tests precede implementation and tasks remain isolated per story.

---

## Phase N: Cross-Cutting Polish

- [ ] T0N0 Update docs (`README.md`, `docs/`, specs) to reflect changes
- [ ] T0N1 Review logs/metrics dashboards or add new ones if required (Principle V)
- [ ] T0N2 Run `uv run ruff format .`, `uv run ruff check .`, `uv run mypy app`, `uv run pytest`
- [ ] T0N3 Prepare release notes or migration instructions if Principle I changes were involved

---

## Dependencies & Execution Order

- Phase 0 and Phase 1 tasks BLOCK story work.
- Each user story proceeds only after its tests are authored and failing.
- Parallel tasks marked `[P]` assume no shared file conflicts.
- When a principle is at risk, add explicit follow-up tasks referencing the mitigation.

---

## Notes

- Keep tasks small and reviewable; commit as you complete them.
- Reference the Sync Impact Report if amendments to principles are required.
- Close the loop by linking tasks to test evidence during review.
