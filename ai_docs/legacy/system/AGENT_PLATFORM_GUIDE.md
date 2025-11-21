# Платформа управления агентами

Актуальная система для LLM-агентов включает три ключевых части:

1. **Конфигурация** — `ai_docs/system/agent_policies.yaml` (роли, приоритеты, планировщик) и `ai_docs/system/initial_tasks.yaml` (стартовые задачи).
2. **Состояние** — `ai_docs/state/agents.yaml`, `ai_docs/state/issues.yaml`, `ai_docs/state/events.yaml`, `ai_docs/state/communications.yaml` и каталоги `ai_docs/state/agents/*` с профилями и логами.
3. **Инструмент** — `python ai_docs/system/agent_system_cli.py` заменяет shell-скрипты и управляет онбордингом, задачами и планировщиком.

## Быстрый старт

```bash
# Список агентов
python ai_docs/system/agent_system_cli.py agents list

# Автоматический онбординг (роль, промпт и задача выдаются системой)
python ai_docs/system/agent_system_cli.py agents ingest "Новый участник" "Помогаю команде"

# Просмотреть подробности и активные задачи
python ai_docs/system/agent_system_cli.py agents info BE_001_v1

# Добавить задачу вручную
python ai_docs/system/agent_system_cli.py tasks add "Согласовать UX" --role frontend --agent-id FE_001_v1 --priority A --tag ui --story-points 2

# Завершить задачу
python ai_docs/system/agent_system_cli.py tasks complete TSK-0001

# Принудительно запустить распределение
python ai_docs/system/agent_system_cli.py scheduler run

# Отправить запрос Product Owner через систему коммуникаций
python ai_docs/system/agent_system_cli.py communications send product "Нужны уточнения по платежам" --sender user --recipient PO --create-issue
```

## Онбординг и первая задача

Команда `agents ingest` (alias `agents onboard`) выполняет за один шаг:

1. Подбор роли по приоритетам, минимумам и флагам `auto_fill_capacity` из `agent_policies.yaml`.
2. Запись агента в `agents.yaml` (один агент может держать несколько ролей — поле `roles`).
3. Формирование профиля `ai_docs/state/agents/<ID>/profile.yaml` и пакета `welcome.md` с промптом (из `ai_docs/prompts/roles/<ROLE>_AGENT_PROMPT.md`).
4. Генерацию стартовой задачи на основе `ai_docs/system/initial_tasks.yaml` — запись попадает в `issues.yaml` и экспортируется в `todo.txt` с тегами `+issue_id`, `+assignee`, `+status`.

Если роль подобрать нельзя (например, все квоты заняты и авто-перераспределение запрещено), агент помещается в `pending_agents`, а ближайший `scheduler run` обработает очередь.

## Планировщик

Планировщик реализует псевдомногозадачность: поддерживает минимальный состав ролей, запускает стартовые задачи и при дефиците может перераспределять агентов.

```bash
# Статус распределения
python ai_docs/system/agent_system_cli.py scheduler status

# Выполнить один проход (очередь + авто-перераспределение)
python ai_docs/system/agent_system_cli.py scheduler run

# Обновить активность конкретного агента
python ai_docs/system/agent_system_cli.py agents touch QA_001_v1
```

Авто-перераспределение срабатывает только для ролей, у которых не выполнен минимум (`minimum`) либо включён `auto_fill_capacity`. Донором не станет роль, у которой остался единственный активный агент.

## Формат данных

- **Агенты**: `agents.yaml` содержит инфраструктурные данные (id, роль, статус, компетенции, временные отметки).
- **Каталоги агентов**: `ai_docs/state/agents/<ID>/profile.yaml` и `welcome.md` хранят настройки, промпт и ссылки на стартовые задачи.
- **Задачи**: `issues.yaml` — структурированное хранилище (`type`, `status`, `dependencies`, `story_points`). Каждая активная задача экспортируется в `todo.txt` с тегами `+issue_id`, `+assignee`, `+status`.
- **Коммуникации**: `communications.yaml` фиксирует диалоги пользователя и агентов.
- **Журнал**: `events.yaml` отслеживает ключевые действия (назначения ролей, создание задач, перемещения по workflow).

## Полезные команды

```bash
# Конфигурация ролей
python ai_docs/system/agent_system_cli.py config roles

# Фильтрация задач по роли
python ai_docs/system/agent_system_cli.py tasks list --role qa

# Смена статуса агента
python ai_docs/system/agent_system_cli.py agents update-status QA_001_v1 paused

# Быстрое Heartbeat агента
python ai_docs/system/agent_system_cli.py agents touch BE_001_v1
```

Дальнейшее развитие платформы (уведомления, интеграции и т.п.) фиксируйте в `agent_policies.yaml`, чтобы инструмент оставался единым источником правды.
