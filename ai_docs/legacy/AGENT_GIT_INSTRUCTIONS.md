# Инструкции для агентов: Git Workflow

## 🚀 Git - идеальное решение для координации!

### ✅ Преимущества Git:
- **Автоматическая блокировка** файлов при checkout
- **Конфликт-резолюшн** при merge
- **История изменений** с трассировкой агентов
- **Ветвление** - каждый агент в своей ветке
- **Откат изменений** при ошибках

## Быстрый старт

### 1. Получить роль
```bash
./role_manager.sh assign "Ваше имя"
```

### 2. Загрузить команды
```bash
source agents/YOUR_ID/commands.sh
```

### 3. Синхронизироваться с main
```bash
sync_with_main
```

### 4. Получить задачу
```bash
my_tasks
```

### 5. Создать ветку для задачи
```bash
create_branch "add-group-service-methods"
```

### 6. Выполнить работу
```bash
# Редактируйте файлы в IDE
# Git автоматически отслеживает изменения
```

### 7. Закоммитить изменения
```bash
commit_changes "feat: add get_available_faculties method" "app/services/group_service.py"
```

### 8. Отправить ветку
```bash
push_branch
```

### 9. Создать Pull Request
```bash
create_pr "feat: add GroupService methods" "Implemented missing methods in GroupService"
```

### 10. Завершить задачу
```bash
finish_task TASK_ID
```

## Правила именования веток

### Формат: `type/AGENT_ID/description`
- `feature/BE_001_v1/add-group-methods`
- `fix/FE_001_v1/callback-data-length`
- `test/QA_001_v1/group-service-tests`
- `docs/PO_001_v1/api-documentation`
- `refactor/DO_001_v1/optimize-database`

## Правила коммитов

### Формат: `type: description`
- `feat:` - новая функциональность
- `fix:` - исправление бага
- `test:` - добавление тестов
- `docs:` - документация
- `refactor:` - рефакторинг
- `style:` - форматирование
- `perf:` - оптимизация производительности

### Обязательные поля:
```
type: краткое описание

Подробное описание изменений:
- Что было сделано
- Почему это было сделано
- Какие файлы затронуты

Agent: YOUR_AGENT_ID
Task: TASK_ID или описание задачи
```

## Workflow для разных ролей

### Backend Agent:
```bash
# 1. Получить задачу
my_tasks

# 2. Создать ветку
create_branch "add-group-service-methods"

# 3. Редактировать файлы
# app/services/group_service.py

# 4. Коммит
commit_changes "feat: add get_available_faculties method" "app/services/group_service.py"

# 5. Push
push_branch

# 6. Создать PR
create_pr "feat: add GroupService methods" "Implemented missing methods in GroupService"

# 7. Завершить задачу
finish_task TASK_ID
```

### Frontend Agent:
```bash
# 1. Получить задачу
my_tasks

# 2. Создать ветку
create_branch "fix-callback-data-length"

# 3. Редактировать файлы
# app/bot/handlers/group_handler.py
# app/bot/keyboards.py

# 4. Коммит
commit_changes "fix: reduce callback data length" "app/bot/handlers/group_handler.py app/bot/keyboards.py"

# 5. Push
push_branch

# 6. Создать PR
create_pr "fix: reduce callback data length" "Fixed callback data length issue in group handlers"

# 7. Завершить задачу
finish_task TASK_ID
```

### QA Agent:
```bash
# 1. Получить задачу
my_tasks

# 2. Создать ветку
create_branch "add-group-service-tests"

# 3. Создать тесты
# tests/test_group_service.py

# 4. Коммит
commit_changes "test: add GroupService tests" "tests/test_group_service.py"

# 5. Push
push_branch

# 6. Создать PR
create_pr "test: add GroupService tests" "Added comprehensive tests for GroupService"

# 7. Завершить задачу
finish_task TASK_ID
```

## Решение конфликтов

### Если есть конфликты при merge:
```bash
# 1. Синхронизироваться с main
sync_with_main

# 2. Переключиться на свою ветку
git checkout feature/YOUR_ID/task-description

# 3. Rebase на main
git rebase main

# 4. Решить конфликты в файлах
# Отредактируйте файлы с конфликтами

# 5. Добавить изменения
git add .

# 6. Продолжить rebase
git rebase --continue

# 7. Force push (осторожно!)
git push origin feature/YOUR_ID/task-description --force-with-lease
```

## Мониторинг и координация

### Проверить что делают другие агенты:
```bash
# Посмотреть все ветки
git branch -r

# Посмотреть коммиты за последние 24 часа
git log --since="24 hours ago" --oneline

# Посмотреть активность конкретного агента
git log --author="AGENT_ID" --oneline
```

### Синхронизация с командой:
```bash
# Регулярно синхронизироваться с main
sync_with_main

# Проверять конфликты
check_conflicts
```

## Команды Git для агентов

### Основные команды:
```bash
create_branch <description>     # Создать ветку для задачи
commit_changes <message> <files> # Закоммитить изменения
push_branch                     # Отправить ветку
create_pr <title> <body>        # Создать Pull Request
finish_task <task_id>           # Завершить задачу
sync_with_main                  # Синхронизироваться с main
check_conflicts                 # Проверить конфликты
```

### Дополнительные команды:
```bash
my_tasks                        # Мои задачи
role_tasks                      # Задачи моей роли
critical_tasks                  # Критические задачи
send_message <message> <channel> # Отправить сообщение
update_activity                 # Обновить активность
```

## Преимущества Git workflow

### ✅ Автоматическая координация:
- Файлы блокируются при checkout
- Конфликты решаются при merge
- История изменений сохраняется
- Откат изменений возможен

### ✅ Командная работа:
- Каждый агент в своей ветке
- Pull Request для code review
- Автоматические проверки
- Интеграция с CI/CD

### ✅ Мониторинг:
- Полная трассировка изменений
- Статистика по агентам
- Отчеты по задачам
- Анализ производительности

## Экстренные ситуации

### Если что-то пошло не так:
```bash
# Отменить последний коммит
git reset --soft HEAD~1

# Отменить все изменения
git checkout -- .

# Откатиться к последнему рабочему состоянию
git reset --hard HEAD

# Удалить ветку и начать заново
git checkout main
git branch -D feature/YOUR_ID/task-description
create_branch "task-description"
```

### Если нужно срочно исправить main:
```bash
# Только Архитектор может
git checkout main
# Внести исправления
git commit -m "hotfix: critical bug fix"
git push origin main
```

---

**Git - идеальное решение для координации агентов!** 🚀

**Больше никаких конфликтов файлов!** ✅
