# Feature Specification: Fix Critical Blockers and Make Application Runnable

**Feature Branch**: `002-fix-critical-blockers`
**Created**: 2025-11-18
**Status**: Draft
**Input**: User description: "Fix critical blockers and make application runnable - create missing secrets module, fix undefined names, create env example, and auto-fix linting issues"

> This specification addresses critical blockers preventing application startup and establishes baseline code quality. All changes preserve canonical schedule data flow (Principle I), maintain async orchestration (Principle II), and prepare for comprehensive test coverage (Principle IV).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application Startup (Priority: P0 - Critical)

Developer clones the repository, configures environment variables, and successfully starts the bot without import errors or crashes.

**Why this priority**: Application currently cannot start due to missing `app/utils/secrets.py` module. This is a complete blocker for all development and testing.

**Independent Test**: Integration test in `tests/integration/test_app_startup.py` that:
- Validates environment setup
- Imports all required modules successfully
- Initializes bot application without errors
- Verifies all dependencies are properly configured

**Acceptance Scenarios**:

1. **Given** fresh repository clone with `.env` configured, **When** developer runs `uv run szgmu-bot`, **Then** application starts without ImportError
2. **Given** missing BOT_TOKEN in environment, **When** application starts, **Then** validation fails with clear error message
3. **Given** valid environment, **When** secrets module validates configuration, **Then** all required variables are confirmed present

---

### User Story 2 - Code Quality Baseline (Priority: P0 - Critical)

Developer runs linting and type checking commands and sees clean output or minimal, documented exceptions, enabling consistent code quality across the team.

**Why this priority**: Currently 79 ruff errors and 1,429 type errors prevent automated quality gates. This blocks CI/CD and makes code reviews difficult.

**Independent Test**: CI smoke test in `tests/test_code_quality.py` that:
- Runs `ruff check .` and expects 0 errors (excluding legacy/)
- Verifies critical imports resolve
- Confirms no undefined names in active codebase

**Acceptance Scenarios**:

1. **Given** current codebase, **When** running `uv run ruff check . --fix`, **Then** auto-fixable errors (45) are corrected
2. **Given** fixed codebase, **When** running `uv run ruff check .`, **Then** only legacy files show errors, app/ is clean
3. **Given** fixed imports, **When** running Python import checks, **Then** no undefined names exist in handlers

---

### User Story 3 - Environment Configuration Template (Priority: P1 - High)

New developer finds `.env.example` in repository, copies it to `.env`, fills in their bot token, and understands all required configuration.

**Why this priority**: Without `.env.example`, onboarding is confusing and error-prone. Developers don't know what variables are required.

**Independent Test**: Documentation test in `tests/test_environment.py` that:
- Verifies `.env.example` exists
- Confirms all required variables are documented
- Validates example format matches actual requirements

**Acceptance Scenarios**:

1. **Given** `.env.example` file, **When** developer reads it, **Then** all required variables (BOT_TOKEN, DATABASE_URL, LOG_LEVEL) are listed with examples
2. **Given** copied `.env.example` to `.env`, **When** developer adds BOT_TOKEN, **Then** application validates and starts successfully
3. **Given** missing optional variable, **When** application starts, **Then** default value is used and logged

---

### Edge Cases

- What happens when `BOT_TOKEN` is present but invalid (wrong format)?
  - Validation should catch format errors early with clear message
- How does the system respond when `.env` file is missing entirely?
  - Should fall back to environment variables, document this behavior
- What if DATABASE_URL points to invalid path or permissions issue?
  - Should fail fast with actionable error message
- How are secrets redacted in logs to prevent accidental exposure?
  - Secrets module must implement redaction patterns for all log output

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide `app/utils/secrets.py` module with functions: `validate_environment()`, `secrets_manager` object, and `get_api_base_url()` (Principle V - operational transparency).
- **FR-002**: Secrets module MUST validate required environment variables (BOT_TOKEN) before application starts and fail fast with clear errors (Principle III - student value through operational reliability).
- **FR-003**: System MUST provide `.env.example` template documenting all environment variables with examples and descriptions.
- **FR-004**: All undefined names (GroupSearchCallback, etc.) MUST be resolved through proper imports or definitions (Principle II - maintain async orchestration integrity).
- **FR-005**: Auto-fixable linting errors (45 of 79) MUST be corrected using `ruff --fix` while preserving functionality (Principle IV - code quality for testability).
- **FR-006**: Secrets MUST be redacted in all log output using configurable patterns to prevent exposure (Principle V - operational security).
- **FR-007**: API URLs and configuration MUST be centralized and environment-configurable rather than hardcoded (Principle I - canonical configuration).

### Key Entities

- **SecretsManager**: Manages environment variables, validates configuration, provides access to secrets with automatic redaction
- **Environment Configuration**: Set of required and optional variables with validation rules and defaults
- **ValidationResult**: Result object indicating success/failure of environment validation with specific error messages

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application starts successfully when running `uv run szgmu-bot` with valid `.env` configuration (0 import errors).
- **SC-002**: Ruff linting shows 0 errors in `app/` directory (legacy/ excluded) after auto-fix application.
- **SC-003**: All undefined names (9 instances of GroupSearchCallback) are resolved with 0 `F821` errors.
- **SC-004**: Environment validation catches missing BOT_TOKEN and fails with error message within 2 seconds.
- **SC-005**: New developers can onboard using `.env.example` in under 5 minutes without asking questions.
- **SC-006**: Secrets redaction prevents BOT_TOKEN from appearing in any log file when tested with sample runs.
- **SC-007**: Integration test `test_app_startup.py` passes, confirming complete initialization flow works.

All outcomes verified through automated tests and manual startup verification.
