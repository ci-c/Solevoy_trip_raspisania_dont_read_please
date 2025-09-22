# Добро пожаловать, Architect Agent (ARCH_001_v1)

## Роль: Architect
Архитектурные решения, стратегия и координация команды.

## Рекомендуемые модели
- gpt-4o
- claude-3-opus

## Текущая задача
- ID: ISS-0007
- Статус: In Refinement
- Заголовок: Сформировать архитектурный план
- Описание: Собрать актуальные статусы агентов и задач, определить ключевые блокеры.

## Стартовые шаги
```bash
python ai_docs/system/agent_system_cli.py issues info ISS-0007
python ai_docs/system/agent_system_cli.py scheduler status
```
