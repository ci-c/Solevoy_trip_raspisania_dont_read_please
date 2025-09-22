# Добро пожаловать, Product Owner Candidate (PO_001_v1)

## Роль: Product Owner
Работа с backlog, приоритеты и общение с пользователем.

## Рекомендуемые модели
- claude-3-haiku

## Текущая задача
- ID: ISS-0006
- Статус: In Refinement
- Заголовок: Отсортировать backlog
- Описание: Пересмотреть backlog, выставить приоритеты и собрать вопросы для пользователя.

## Стартовые шаги
```bash
python ai_docs/system/agent_system_cli.py issues move ISS-0006 --status "Ready"
python ai_docs/system/agent_system_cli.py issues info ISS-0006
```
