# Инструкции для запуска агентов

## Как создать агента

### 1. Выберите роль
- **PO** - Product Owner (управление backlog)
- **BE** - Backend Developer (серверная логика)
- **FE** - Frontend Developer (UI/UX бота)
- **QA** - Quality Assurance (тестирование)
- **DO** - DevOps (развертывание и мониторинг)
- **SM** - Scrum Master (координация)

### 2. Зарегистрируйтесь
```bash
cd /home/c/Documents/Project/P-2
./agent_manager.sh register "ROLE" "Ваше имя"
```

### 3. Изучите промпт
```bash
# Промпт будет показан после регистрации
# Или найдите его в: ai_docs/PROMPTS/ROLE_AGENT_PROMPT.md
```

### 4. Начните работу
```bash
# Загрузите команды агента
source agents/YOUR_AGENT_ID/commands.sh

# Посмотрите свои задачи
my_tasks

# Создайте первую задачу
create_task "B" "Первая задача" "+feature +2sp" "2"
```

## Доступные команды

### Управление агентами
```bash
./agent_manager.sh register "ROLE" "NAME"  # Регистрация
./agent_manager.sh list                     # Список агентов
./agent_manager.sh status AGENT_ID          # Статус агента
./agent_manager.sh info AGENT_ID            # Информация об агенте
./agent_manager.sh update AGENT_ID          # Обновить активность
```

### Работа с задачами
```bash
./todo.txt-cli/todo.sh ls                   # Все задачи
./todo.txt-cli/todo.sh add "..."            # Добавить задачу
./todo.txt-cli/todo.sh do NUM               # Завершить задачу
./todo.txt-cli/todo.sh pri NUM A            # Установить приоритет
```

## Примеры создания агентов

### Product Owner Agent
```bash
./agent_manager.sh register "PO" "Product Owner"
# Результат: PO_001_v1
# Промпт: ai_docs/PROMPTS/PO_AGENT_PROMPT.md
```

### Backend Agent
```bash
./agent_manager.sh register "BE" "Backend Developer"
# Результат: BE_001_v1
# Промпт: ai_docs/PROMPTS/BE_AGENT_PROMPT.md
```

### Frontend Agent
```bash
./agent_manager.sh register "FE" "Frontend Developer"
# Результат: FE_001_v1
# Промпт: ai_docs/PROMPTS/FE_AGENT_PROMPT.md
```

### QA Agent
```bash
./agent_manager.sh register "QA" "Quality Assurance"
# Результат: QA_001_v1
# Промпт: ai_docs/PROMPTS/QA_AGENT_PROMPT.md
```

### DevOps Agent
```bash
./agent_manager.sh register "DO" "DevOps Engineer"
# Результат: DO_001_v1
# Промпт: ai_docs/PROMPTS/DO_AGENT_PROMPT.md
```

## Формат сообщений агентов

### В todo.txt
```
(PRIORITY) YYYY-MM-DD Описание задачи +tags +agent_id:AGENT_ID @role
```

### В коммуникации
```
[AGENT_ID] Заголовок сообщения
Описание...
+tags @mentions
```

## Критические задачи для новых агентов

### Product Owner
- Приоритизировать backlog
- Планировать спринты
- Принимать решения по scope

### Backend
- Исправить ошибки в GroupService
- Решить проблемы с mypy (426 ошибок)
- Восстановить работу базы данных

### Frontend
- Исправить UI проблемы с кнопками
- Решить проблемы с callback data
- Улучшить UX

### QA
- Написать тесты для критических компонентов
- Проверить качество кода
- Обновить документацию

### DevOps
- Настроить мониторинг
- Создать алерты для ошибок
- Оптимизировать производительность

## Полезные команды

### Анализ проекта
```bash
# Критические задачи
./todo.txt-cli/todo.sh ls | grep "^(A)"

# Задачи по ролям
./todo.txt-cli/todo.sh ls | grep "@backend"
./todo.txt-cli/todo.sh ls | grep "@frontend"
./todo.txt-cli/todo.sh ls | grep "@qa"

# Завершенные задачи
./todo.txt-cli/todo.sh ls | grep "^x"
```

### Проверка системы
```bash
# Логи ошибок
tail -20 logs/errors.log

# Статус агентов
./agent_manager.sh list

# Информация об агенте
./agent_manager.sh info YOUR_AGENT_ID
```

---

**Готово к работе!** Выберите роль, зарегистрируйтесь и начните работу согласно промпту.
