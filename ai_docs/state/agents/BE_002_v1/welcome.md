# Добро пожаловать, Backend Developer 2 (BE_002_v1)

## Роль: Backend Engineer
Серверная логика, база данных, API интеграции.

## Рекомендуемые модели
- gpt-4o-mini

## Текущая задача
- ID: ISS-0005
- Статус: Ready
- Заголовок: Проверить сервисы расписаний
- Описание: Пройтись по app/services/*, зафиксировать основные точки расширения и открытые mypy-ошибки.

## Стартовые шаги
```bash
python ai_docs/system/agent_system_cli.py issues move ISS-0005 --status "In Progress"
python ai_docs/system/agent_system_cli.py issues info ISS-0005
```
