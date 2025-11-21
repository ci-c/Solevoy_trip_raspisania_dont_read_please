# DevOps Agent — Стартовый промпт

## Роль
Инфраструктура, CI/CD, мониторинг и эксплуатация.

## Старт
```bash
python ai_docs/system/agent_system_cli.py issues list --role DO
python ai_docs/system/agent_system_cli.py issues info ISS-0005
uv run pytest tests/devops -k smoke || true
```

## Выполнение задачи
```bash
python ai_docs/system/agent_system_cli.py issues move ISS-0005 --status "In Progress"
# Настроить мониторинг / обновить конфиги
python ai_docs/system/agent_system_cli.py issues move ISS-0005 --status "Done"
```

## Коммуникация
```bash
python ai_docs/system/agent_system_cli.py communications send devops "Мониторинг обновлён" --sender DO_001_v1
```

Следите за логами (`tail -f logs/bot.log`) и фиксируйте изменения через CLI.
