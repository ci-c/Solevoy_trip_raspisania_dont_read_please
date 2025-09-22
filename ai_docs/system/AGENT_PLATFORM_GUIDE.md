# Платформа управления агентами

Актуальная система для LLM-агентов включает три ключевых части:

1. **Конфигурация** — `ai_docs/system/agent_policies.yaml` описывает роли, каналы связи и допустимые действия.
2. **Состояние** — `ai_docs/state/agent_state.yaml`, `ai_docs/state/tasks.yaml` и каталоги `ai_docs/state/agents/*` хранят текущие данные об агентах и задачах.
3. **Инструмент** — `python ai_docs/system/agent_system_cli.py` заменяет прежние shell-скрипты и позволяет работать с реестром и задачами.

## Быстрый старт

```bash
# Список агентов
python ai_docs/system/agent_system_cli.py agents list

# Создать нового агента (код роли можно задавать alias'ом)
python ai_docs/system/agent_system_cli.py agents create BE "Backend LLM"

# Просмотреть подробности и активные задачи
python ai_docs/system/agent_system_cli.py agents info BE_001_v1

# Добавить задачу
python ai_docs/system/agent_system_cli.py tasks add "Согласовать UX" --role frontend --agent-id FE_001_v1 --priority A --tag ui --story-points 2

# Завершить задачу
python ai_docs/system/agent_system_cli.py tasks complete TSK-0001
```

## Формат данных

- **Агенты**: `agent_state.yaml` (список записей с `id`, `role`, `status` и `last_activity`).
- **Каталоги агентов**: `ai_docs/state/agents/<ID>/profile.yaml` плюс папка `logs/` для сообщений.
- **Задачи**: `tasks.yaml` (структурированная информация о задачах) + синхронизация с `todo.txt` через тег `+task_id:<ID>`.

## Правила использования

- Все действия с агентами и задачами выполняются через Python-CLI.
- Если нужен новый тип роли — сначала добавьте её в `agent_policies.yaml`, затем используйте CLI.
- При закрытии задачи CLI автоматически помечает строку в `todo.txt` и обновляет `tasks.yaml`.
- Архивные инструкции, основанные на shell-скриптах, перенесены в `ai_docs/legacy/` и оставлены только для истории.

## Полезные команды

```bash
# Получить справку по конфигурации ролей
python ai_docs/system/agent_system_cli.py config roles

# Отфильтровать задачи по роли
python ai_docs/system/agent_system_cli.py tasks list --role qa

# Обновить статус агента
python ai_docs/system/agent_system_cli.py agents update-status FE_002_v1 paused

# Быстро обновить активность
python ai_docs/system/agent_system_cli.py agents touch BE_001_v1
```

Дальнейшее развитие платформы (уведомления, интеграции и т.д.) следует также описывать в `agent_policies.yaml`, чтобы инструменты могли опираться на единый источник правды.
