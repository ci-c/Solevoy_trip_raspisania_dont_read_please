# Добро пожаловать, QA Specialist (QA_001_v1)

## Роль: QA Engineer
Тесты, документация и контроль качества.

## Рекомендуемые модели
- gpt-4o-mini

## Текущая задача
- ID: ISS-0001
- Статус: In Progress
- Заголовок: Проверить критические тест-кейсы
- Описание: Запустить ключевые тесты, оценить покрытие и зафиксировать пробелы.

## Стартовые шаги
```bash
uv run pytest tests/ -v
python ai_docs/system/agent_system_cli.py issues info ISS-0001
```
