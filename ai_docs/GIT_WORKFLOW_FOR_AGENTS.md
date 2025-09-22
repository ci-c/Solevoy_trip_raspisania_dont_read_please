# Git Workflow для агентов

## 🚀 Git - идеальное решение для координации агентов!

### Преимущества Git для агентов:
- ✅ **Автоматическая блокировка** - файлы блокируются при checkout
- ✅ **Конфликт-резолюшн** - Git автоматически решает конфликты
- ✅ **История изменений** - полная трассировка работы агентов
- ✅ **Ветвление** - каждый агент работает в своей ветке
- ✅ **Откат изменений** - легко отменить неправильные изменения

## Workflow для агентов

### 1. Получение задачи
```bash
# Получить свою задачу
my_tasks

# Определить какие файлы нужно редактировать
```

### 2. Создание ветки
```bash
# Создать ветку для задачи
git checkout -b feature/YOUR_AGENT_ID/task-description

# Например:
git checkout -b feature/BE_001_v1/add-group-service-methods
git checkout -b feature/FE_001_v1/fix-callback-data-length
git checkout -b feature/QA_001_v1/add-group-service-tests
```

### 3. Работа с файлами
```bash
# Теперь безопасно редактируйте файлы
# Git автоматически отслеживает изменения

# Проверить статус
git status

# Добавить изменения
git add path/to/file.py

# Коммит с описанием
git commit -m "feat: add get_available_faculties method to GroupService

- Implemented get_available_faculties method
- Added proper error handling
- Updated type hints

Agent: BE_001_v1
Task: Fix GroupService missing methods"
```

### 4. Push ветки
```bash
# Отправить ветку в удаленный репозиторий
git push origin feature/YOUR_AGENT_ID/task-description
```

### 5. Создание Pull Request
```bash
# Создать PR через GitHub CLI (если установлен)
gh pr create --title "feat: add GroupService methods" --body "Implemented missing methods in GroupService. Agent: BE_001_v1"

# Или через веб-интерфейс GitHub
```

### 6. Завершение задачи
```bash
# После merge PR
complete_task TASK_ID

# Удалить локальную ветку
git checkout main
git pull origin main
git branch -d feature/YOUR_AGENT_ID/task-description
```

## Правила именования веток

### Формат: `type/AGENT_ID/description`
- `feature/BE_001_v1/add-group-methods` - новая функциональность
- `fix/FE_001_v1/callback-data-length` - исправление бага
- `test/QA_001_v1/group-service-tests` - тесты
- `docs/PO_001_v1/api-documentation` - документация
- `refactor/DO_001_v1/optimize-database` - рефакторинг

## Правила коммитов

### Формат: `type: description`
- `feat:` - новая функциональность
- `fix:` - исправление бага
- `test:` - добавление тестов
- `docs:` - документация
- `refactor:` - рефакторинг
- `style:` - форматирование
- `perf:` - оптимизация производительности

### Обязательные поля в коммите:
```
type: краткое описание

Подробное описание изменений:
- Что было сделано
- Почему это было сделано
- Какие файлы затронуты

Agent: YOUR_AGENT_ID
Task: TASK_ID или описание задачи
```

## Координация между агентами

### 1. Проверка конфликтов
```bash
# Перед началом работы обновите main
git checkout main
git pull origin main

# Проверьте нет ли конфликтов с другими ветками
git log --oneline --graph --all
```

### 2. Решение конфликтов
```bash
# Если есть конфликты при merge
git checkout main
git pull origin main
git checkout feature/YOUR_AGENT_ID/task-description
git rebase main

# Решите конфликты в файлах
# Затем продолжите rebase
git add .
git rebase --continue
```

### 3. Синхронизация с другими агентами
```bash
# Проверить что делают другие агенты
git branch -r

# Посмотреть изменения в других ветках
git log origin/feature/OTHER_AGENT_ID/task --oneline
```

## Команды для агентов

Используйте Python-CLI `python ai_docs/system/agent_system_cli.py` для назначения задач и обновления активности.
Для Git остаются стандартные команды, перечисленные выше.
