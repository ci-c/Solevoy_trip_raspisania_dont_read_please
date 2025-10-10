<!--
Sync Impact Report
Version change: N/A → v1.0.0
Modified principles:
- ∅ → Principle I. Canonical Schedule Data Discipline
- ∅ → Principle II. Async Telegram Orchestration
- ∅ → Principle III. Student Value First
- ∅ → Principle IV. Tests Before Code (Non-Negotiable)
- ∅ → Principle V. Operational Transparency & Resilience
Added sections:
- Implementation Constraints
- Development Workflow & Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md (updated for Principles I–V)
- ✅ .specify/templates/spec-template.md (updated for canonical data + test mandates)
- ✅ .specify/templates/tasks-template.md (updated for test-first execution)
Follow-up TODOs:
- None
-->

# SZGMU Schedule Bot Constitution

## Core Principles

### Principle I. Canonical Schedule Data Discipline
- All timetable information MUST be sourced through the ingestion pipeline in `app/schedule/` and persisted via SQLAlchemy models under `app/database/`. Manual edits to the production database or ad-hoc CSV/YAML reads in runtime code are forbidden.
- Every change to schedule schemas MUST provide a migration or seeding script in `data/` and document the impact inside the relevant feature plan.
- Schedule exports (ICS/Excel) MUST reflect the same canonical dataset used by bot responses; divergent serialization logic is prohibited.

*Rationale*: The bot’s only value is accurate schedules; a single authoritative dataset prevents drift between handlers, exports, and notifications.

### Principle II. Async Telegram Orchestration
- All Telegram flows MUST be implemented with aiogram 3 async handlers and leverage the shared service layer in `app/services/`. Blocking calls or direct database access from handlers are not allowed.
- Background jobs, CLI tools, and handlers MUST call the same asynchronous services to avoid duplicated business logic.
- External I/O MUST use async clients (`aiohttp`/`httpx`) with timeouts and error handling that surface actionable feedback to students.

*Rationale*: Consistent async orchestration keeps chat interactions responsive and ensures one source of truth for business rules.

### Principle III. Student Value First
- User-facing copy MUST default to Russian, align with Telegram UX expectations, and keep flows linear—collect only the data required for the immediate action.
- Profile preferences (group, exports, notifications) MUST be persisted and respected in every response path, including background notifications and ad-hoc exports.
- Error states MUST guide students back to a working path without exposing stack traces or internal identifiers.

*Rationale*: Students rely on the bot for daily coordination; preserving trust requires empathetic messaging, persisted preferences, and predictable recovery paths.

### Principle IV. Tests Before Code (Non-Negotiable)
- Every feature MUST start with failing automated tests (unit + integration) that codify the expected behavior before implementation begins.
- Tests MUST be organized under `tests/unit/`, `tests/integration/`, or top-level smoke files with appropriate markers (`unit`, `integration`, `slow`, `database`, `external`).
- Pull requests MUST run `uv run pytest`, `uv run ruff check .`, and `uv run mypy app` to green before merge; skipped checks require written justification in plan Complexity Tracking.

*Rationale*: Regression risk is unacceptable in schedule delivery—tests gate code to keep the bot reliable despite rapid iteration.

### Principle V. Operational Transparency & Resilience
- Structured logging via Loguru MUST capture command invocations, exports, and notification events with correlation IDs while redacting secrets.
- When upstream services fail, handlers MUST return localized, actionable guidance and queue retries or fallbacks without blocking the event loop.
- Observability artifacts (logs, metrics stubs, alerts) MUST live alongside runtime code so incidents can be investigated without guessing code paths.

*Rationale*: Schedules change hourly; resilient, observable operations let maintainers correct issues before students are impacted.

## Implementation Constraints

- **Language & Tooling**: Python 3.14 managed with `uv`; `black` formatting, `ruff` linting, and `mypy` typing are gate checks.
- **Frameworks**: aiogram 3 for Telegram flows, SQLAlchemy 2.0 for ORM, Pydantic for validation, Loguru for logging. Deviations require constitution amendment.
- **Data Stores**: SQLite (`data/szgmu_bot.db`) is the canonical store; alternative engines demand migration plans reviewed during planning.
- **Ingestion Sources**: ICS and Excel imports MUST route through `app/schedule/` abstractions; legacy scripts in `legacy/` may inform design but never run in production.
- **Secrets & Config**: All secrets stay in `.env`; config changes (e.g., `config.yaml`) MUST be documented in specs and communicated to operators.

## Development Workflow & Quality Gates

- Feature work MUST originate from `/specs/[id]/spec.md` (user stories) and `/specs/[id]/plan.md` (implementation plan). No coding without an approved spec-plan pair.
- Plans MUST document Constitution Check gates up front; violations require entries in Complexity Tracking with mitigations before Phase 1 begins.
- Task breakdowns generated via `/speckit.tasks` MUST keep user stories independently deliverable and include explicit test tasks when Principle IV applies.
- Code reviews MUST verify principle compliance, test coverage, and logging standards before approval. Missing evidence is grounds for rejection.
- Continuous integration MUST run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app`, and `uv run pytest` on every merge request.

## Governance

- **Supremacy**: This constitution supersedes historical practices in `legacy/` and ad-hoc contributor habits. Conflicts resolve in favor of this document.
- **Amendments**: Proposed changes require (1) updated constitution draft with version bump rationale, (2) Sync Impact Report listing downstream template updates, and (3) maintainer approval before merge.
- **Versioning Policy**: Semantic versioning applies—MAJOR for breaking principle reforms, MINOR for new principles or sections, PATCH for clarifications. Version metadata MUST stay in sync with the Sync Impact Report.
- **Compliance Reviews**: Each feature plan MUST include a Constitution Check section citing how the work satisfies or intentionally diverges from Principles I–V. Divergences require explicit TODOs and follow-up tasks.
- **Audit Cadence**: Twice per release cycle, maintainers review specs, plans, and tasks to confirm continued adherence; findings are logged as issues and linked to the next amendment if needed.

**Version**: 1.0.0 | **Ratified**: 2025-10-10 | **Last Amended**: 2025-10-10
