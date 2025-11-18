# Repository Guidelines

## Project Structure & Module Organization
The `app/` package hosts runtime code: `bot/` handles Telegram flows (`handlers/`, `keyboards.py`, `states.py`), `services/` implements domain orchestration, `schedule/` ingests ICS/Excel, `database/` wraps SQLAlchemy models and sessions, and `utils/` holds helpers. Persistent data lives in `data/` (SQLite, seeds) and runtime artifacts in `logs/`. Tests live in `tests/` with `unit/`, `integration/`, reusable `fixtures/`, plus top-level smoke files `test_bot_commands.py` and `test_telegram_commands.py`. Supporting docs reside in `ai_docs/`; archived iterations are under `legacy/`.

## Build, Test, and Development Commands
- `uv sync` / `uv sync --dev` installs production or full dev dependencies from `pyproject.toml`.
- `uv run szgmu-bot` starts the bot via the console script; `uv run python main.py` is the fallback entry point.
- `uv run pytest` executes the configured test matrix; add `-m "unit"` or `-m "integration"` to focus.
- `uv run ruff check .`, `uv run ruff format .`, and `uv run pyright` keep lint, formatting, and typing aligned with CI expectations.

## Coding Style & Naming Conventions
Use Python 3.14 with 4-space indentation, `black`-compatible line wrapping, and exhaustive type hints enforced by `pyright --strict`. Modules and files stay `snake_case`; classes use `PascalCase`; async handlers and services follow verb-based names (`fetch_schedule`, `update_group`). Run `ruff format` before commits, organize imports with `isort`, and verify `flake8`/`ruff check` is clean.

## Testing Guidelines
Place new tests under `tests/unit` for isolated logic and `tests/integration` when touching the database or Telegram clients. Name files `test_*.py` or `*_test.py` and functions `test_*` to satisfy `pytest.ini`. Use the `unit`, `integration`, `slow`, `database`, and `external` markers so CI can select suites; async tests rely on the configured `asyncio-mode=auto`.

## Commit & Pull Request Guidelines
Follow conventional commits (`feat:`, `fix:`, `refactor:`) as seen in history, keeping subjects imperative and under 72 characters. Outline key changes and rationale in the body with bullets, and append `Agent: <id>` / `Task: <ref>` when relevant. Before opening a PR, re-run `ruff`, `pytest`, and `pyright`, link the tracked issue, and attach screenshots или logs for bot interaction changes; call out database or config updates explicitly.

## Security & Configuration Tips
Never commit secrets—copy `.env.example` to `.env` locally and keep tokens out of git. Document changes to `config.yaml`, and when updating schema files (`database_schema.dbml`, `database_diagram.md`) let reviewers know if diagrams in `ai_docs/` need regeneration.
