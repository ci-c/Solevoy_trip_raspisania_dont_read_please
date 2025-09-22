# Добро пожаловать, Unified Agent (AGENT_001_v1)

## Роли
- ARCH: Architect — Архитектурные решения и стратегия.
- BE: Backend Engineer — Сервисы, БД, API.
- FE: Frontend Engineer — Handlers, UX, клавиатуры.
- QA: QA Engineer — Тесты и качество.
- DO: DevOps Engineer — CI/CD, мониторинг.
- PO: Product Owner — Backlog и приоритеты.
- SM: Scrum Master — Координация и процессы.

## Рекомендуемые модели
- gpt-4o
- claude-3-opus
- gpt-4o-mini
- claude-3.5-sonnet
- claude-3-haiku

## Активные задачи
- ARCH → ISS-0001 (In Progress): Архитектурный обзор.
- BE → ISS-0002 (Ready): Проверить сервисы расписаний.
- FE → ISS-0003 (Ready): Аудит пользовательских сценариев.
- QA → ISS-0004 (Ready): Критические тест-кейсы.
- DO → ISS-0005 (Ready): Мониторинг и алерты.
- PO → ISS-0006 (In Refinement): Уточнить требования пользователя.
- SM → ISS-0007 (Ready): Организовать процесс.

## Первые шаги
```bash
# Просмотреть список задач
python ai_docs/system/agent_system_cli.py issues list

# Перевести задачу в работу
python ai_docs/system/agent_system_cli.py issues move ISS-0002 --status "In Progress"

# Добавить комментарий или запрос к PO
python ai_docs/system/agent_system_cli.py communications send product "Нужна дополнительная информация" --sender AGENT_001_v1 --recipient PO --create-issue
```

Следуйте workflow: `New → In Refinement → Ready → In Progress → Review/Blocked → Done → Archived`. Новые агенты будут появляться через `agents ingest`. ရ
