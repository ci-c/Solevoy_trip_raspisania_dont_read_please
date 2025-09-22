# Система идентификации агентов

## Обзор

Каждый агент в системе SZGMU Bot имеет уникальный идентификатор для различения сообщений, задач и взаимодействий. Это обеспечивает прозрачность работы команды и позволяет отслеживать вклад каждого агента.

## Формат идентификации агентов

### Структура ID агента
```
AGENT_ID: [ROLE]_[NUMBER]_[VERSION]
```

### Примеры ID
- `PO_001_v1` - Product Owner Agent #1 версия 1
- `BE_001_v1` - Backend Agent #1 версия 1  
- `FE_001_v1` - Frontend Agent #1 версия 1
- `QA_001_v1` - QA Agent #1 версия 1
- `DO_001_v1` - DevOps Agent #1 версия 1
- `SM_001_v1` - Scrum Master Agent #1 версия 1

### Роли (ROLE)
- `PO` - Product Owner
- `BE` - Backend
- `FE` - Frontend  
- `QA` - QA
- `DO` - DevOps
- `SM` - Scrum Master

## Использование ID в сообщениях

### Формат сообщений агентов
```
[AGENT_ID] Заголовок сообщения
Содержание сообщения...
+tags @mentions
```

### Примеры сообщений
```
[BE_001_v1] Исправил ошибку в GroupService
Добавил недостающий метод get_available_faculties в GroupService
Исправлена ошибка AttributeError при выборе факультета
+bugfix +services @frontend

[FE_001_v1] Обновил UI выбора групп
Исправлены callback data для кнопок факультетов
Добавлена валидация длины callback данных
+ui +callback @backend

[QA_001_v1] Написал тесты для GroupService
Добавлены unit тесты для всех методов GroupService
Покрытие кода: 95%
+testing +pytest @backend
```

## Использование ID в todo.txt

### Формат задач с ID агента
```
(PRIORITY) YYYY-MM-DD Описание задачи +tags +agent_id:AGENT_ID @role
```

### Примеры задач
```
(A) 2025-01-24 Исправить ошибку в GroupService +critical +bugfix +agent_id:BE_001_v1 @backend
(B) 2025-01-24 Написать тесты для GroupService +testing +pytest +agent_id:QA_001_v1 @qa
(C) 2025-01-24 Обновить документацию API +docs +agent_id:QA_001_v1 @qa
```

## Регистрация агентов

### Где хранится реестр
- `ai_docs/state/agent_state.yaml` — основная информация (ID, роль, статус, последняя активность).
- `ai_docs/state/agents/<ID>/profile.yaml` — индивидуальные настройки.

### Пример записи в `agent_state.yaml`
```yaml
agents:
  - id: BE_001_v1
    role: BE
    name: Backend Developer
    created_at: "2025-09-20"
    status: active
    last_activity: "2025-09-20T01:41"
```

### Регистрация нового агента
```bash
python ai_docs/system/agent_system_cli.py agents create BE "Backend Specialist"
```

### Обновление активности
```bash
python ai_docs/system/agent_system_cli.py agents touch BE_001_v1
```

### Изменение статуса
```bash
python ai_docs/system/agent_system_cli.py agents update-status FE_001_v1 paused
```

## Команды для работы с агентами

- `python ai_docs/system/agent_system_cli.py agents list` — список активных агентов.
- `python ai_docs/system/agent_system_cli.py agents info AGENT_ID` — подробная информация и активные задачи.
- `python ai_docs/system/agent_system_cli.py agents update-status AGENT_ID paused` — смена статуса.
- `python ai_docs/system/agent_system_cli.py agents remove AGENT_ID --purge` — удалить агента и связанные данные.

Для работы с задачами используйте:

- `python ai_docs/system/agent_system_cli.py tasks add ...` — создать задачу с нужным `+agent_id`.
- `python ai_docs/system/agent_system_cli.py tasks list --agent-id AGENT_ID` — посмотреть задачи конкретного агента.
- `python ai_docs/system/agent_system_cli.py tasks complete TSK-0001` — закрыть задачу.

Все изменения автоматически отражаются в `ai_docs/state/agent_state.yaml` и `todo.txt`.

## Использование ID в коммуникации

### Формат сообщений в каналах
```
[AGENT_ID] @mention Заголовок
Описание проблемы/вопроса
+tags @related_agent
```

### Примеры коммуникации
```
[BE_001_v1] @FE_001_v1 Ошибка в callback data
В GroupSelectionHandler callback data превышает 64 байта
Нужно сократить данные или использовать другой подход
+bugfix +callback @frontend

[FE_001_v1] @BE_001_v1 Готово к тестированию
Исправил callback data в GroupSelectionHandler
Используется хэширование для длинных названий факультетов
+ready +testing @qa

[QA_001_v1] @FE_001_v1 Тесты пройдены
Все тесты для GroupSelectionHandler проходят успешно
Покрытие кода: 98%
+passed +testing @frontend
```

## Отслеживание вклада агентов

### Базовые метрики
```bash
# Сколько задач закреплено за агентом
python ai_docs/system/agent_system_cli.py tasks list --agent-id AGENT_ID | wc -l

# Сколько задач завершено агентом
python ai_docs/system/agent_system_cli.py tasks list --agent-id AGENT_ID --include-completed | grep 'completed' | wc -l

# Критические задачи агента
python ai_docs/system/agent_system_cli.py tasks list --agent-id AGENT_ID --include-completed | grep ' | A | '
```

### История активности агента
```bash
# Все задачи агента
python ai_docs/system/agent_system_cli.py tasks list --agent-id AGENT_ID --include-completed

# Активные сообщения/логи
cat ai_docs/state/agents/AGENT_ID/logs/coordination.log 2>/dev/null || echo "Лог пуст"

# Story points (sum) — извлечь из todo.txt по тегу +task_id
grep "+agent_id:AGENT_ID" todo.txt | grep -o "+[0-9]*sp" | sed 's/+//;s/sp//' | awk '{s+=$1} END {print s}'
```

## Система версий агентов

### Обновление версии агента

Версия хранится в идентификаторе (`BE_001_v1`). При необходимости изменить версию:
1. Отредактируйте поле `agent.id` и `agent.status` в `ai_docs/state/agents/<ID>/profile.yaml`.
2. Обновите запись в `ai_docs/state/agent_state.yaml`, заменив `id` на новый (`v2`).
3. Проверьте, что задачи в `todo.txt` и `tasks.yaml` используют обновлённый ID.

Для массового обновления используйте Python-скрипт, который загружает YAML, меняет ID и пересохраняет файлы.

## Интеграция с существующими процессами

### Обновление todo.txt с ID агентов
```bash
python ai_docs/system/agent_system_cli.py tasks add   "Описание" --priority B --role backend --agent-id AGENT_ID --tag custom
```

### Автоматическое добавление ID в сообщения
```bash
echo "[AGENT_ID] Сообщение" >> logs/team_communication.log
python ai_docs/system/agent_system_cli.py agents touch AGENT_ID
```

## Примеры использования

### Регистрация нового Backend агента
```bash
python ai_docs/system/agent_system_cli.py agents create BE "Backend Specialist"
# => возвращает ID, например BE_002_v1
```

### Создание задачи с ID агента
```bash
python ai_docs/system/agent_system_cli.py tasks add \
  "Исправить ошибку в GroupService" \
  --priority A --role backend --agent-id BE_002_v1 \
  --tag critical --tag bugfix
```

### Отправка сообщения
```bash
echo "[BE_002_v1] Исправил ошибку в GroupService.get_available_faculties" >> logs/backend.log
python ai_docs/system/agent_system_cli.py agents touch BE_002_v1
```

### Просмотр статистики агента
```bash
python ai_docs/system/agent_system_cli.py tasks list --agent-id BE_002_v1 --include-completed
```

## Резервное копирование реестра

### Автоматическое резервное копирование
```bash
cp ai_docs/state/agent_state.yaml backups/agent_state_$(date +%Y%m%d_%H%M%S).yaml
```

### Восстановление реестра
```bash
cp backups/agent_state_20250920_0100.yaml ai_docs/state/agent_state.yaml
```

---

**Система ID агентов** обеспечивает прозрачность и отслеживаемость работы команды, позволяя каждому агенту быть идентифицированным в системе управления задачами и коммуникации.
