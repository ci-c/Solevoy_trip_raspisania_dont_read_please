# Правила координации агентов

## 🚨 КРИТИЧЕСКИ ВАЖНО: НЕ РЕДАКТИРУЙТЕ ФАЙЛЫ БЕЗ БЛОКИРОВКИ!

### Проблема
Агенты конфликтуют друг с другом:
- Редактируют одни файлы одновременно
- Запускают множественные процессы линтеров
- Перегружают систему

### Решение
**ВСЕГДА блокируйте файлы перед редактированием!**

## Правила работы с файлами

### 1. Перед редактированием файла:
```bash
# ОБЯЗАТЕЛЬНО заблокируйте файл
./agent_coordinator.sh lock YOUR_AGENT_ID path/to/file.py
```

### 2. Проверьте блокировку:
```bash
# Проверьте, не заблокирован ли файл
./agent_coordinator.sh check path/to/file.py
```

### 3. После редактирования:
```bash
# ОБЯЗАТЕЛЬНО разблокируйте файл
./agent_coordinator.sh unlock YOUR_AGENT_ID path/to/file.py
```

### 4. Если файл заблокирован другим агентом:
```bash
# НЕ РЕДАКТИРУЙТЕ! Сообщите Архитектору
send_message "Файл path/to/file.py заблокирован другим агентом" "coordination"
```

## Команды координации

### Основные команды:
```bash
# Заблокировать файл
./agent_coordinator.sh lock AGENT_ID FILE_PATH

# Разблокировать файл  
./agent_coordinator.sh unlock AGENT_ID FILE_PATH

# Проверить блокировку
./agent_coordinator.sh check FILE_PATH

# Статус всех блокировок
./agent_coordinator.sh status

# Принудительно разблокировать (только Архитектор)
./agent_coordinator.sh force_unlock FILE_PATH

# Очистить устаревшие блокировки
./agent_coordinator.sh cleanup

# Остановить все процессы агентов (только Архитектор)
./agent_coordinator.sh kill_processes
```

## Workflow для агентов

### 1. Получение задачи
```bash
# Получите свою задачу
my_tasks

# Определите какие файлы нужно редактировать
```

### 2. Блокировка файлов
```bash
# Заблокируйте ВСЕ файлы которые будете редактировать
./agent_coordinator.sh lock YOUR_AGENT_ID app/services/group_service.py
./agent_coordinator.sh lock YOUR_AGENT_ID app/bot/handlers/group_handler.py
```

### 3. Выполнение работы
```bash
# Теперь безопасно редактируйте файлы
# Запускайте линтеры/тесты только на заблокированных файлах
```

### 4. Разблокировка
```bash
# Разблокируйте ВСЕ файлы после завершения
./agent_coordinator.sh unlock YOUR_AGENT_ID app/services/group_service.py
./agent_coordinator.sh unlock YOUR_AGENT_ID app/bot/handlers/group_handler.py
```

### 5. Уведомление о завершении
```bash
# Сообщите о завершении
send_message "Задача выполнена, файлы разблокированы" "general"
complete_task TASK_ID
```

## Автоматическая разблокировка

- Блокировки автоматически истекают через 30 минут
- Устаревшие блокировки удаляются при проверке
- Используйте `./agent_coordinator.sh cleanup` для очистки

## Эскалация конфликтов

### Если файл заблокирован:
1. **НЕ РЕДАКТИРУЙТЕ** файл
2. Сообщите Архитектору:
```bash
send_message "КОНФЛИКТ: Файл path/to/file.py заблокирован агентом OTHER_AGENT_ID. Нужна координация." "coordination"
```
3. Дождитесь решения Архитектора

### Если процесс завис:
```bash
# Сообщите Архитектору
send_message "ПРОБЛЕМА: Процесс линтера/теста завис. Нужно вмешательство." "coordination"
```

## Правила для разных ролей

### Backend Agent:
- Блокируйте: `app/services/*.py`, `app/database/*.py`
- Не редактируйте: `app/bot/handlers/*.py`, `app/bot/keyboards.py`

### Frontend Agent:
- Блокируйте: `app/bot/handlers/*.py`, `app/bot/keyboards.py`, `app/bot/states.py`
- Не редактируйте: `app/services/*.py`, `app/database/*.py`

### QA Agent:
- Блокируйте: `tests/*.py`, `*.md` файлы
- Можете читать все файлы для тестирования

### DevOps Agent:
- Блокируйте: конфигурационные файлы, скрипты развертывания
- Можете читать все файлы для мониторинга

## Мониторинг Архитектора

### Архитектор должен:
```bash
# Регулярно проверять статус
./agent_coordinator.sh status

# Очищать устаревшие блокировки
./agent_coordinator.sh cleanup

# Останавливать конфликтующие процессы
./agent_coordinator.sh kill_processes
```

## Совместимость с IDE

### Cursor:
- Используйте команды координации в терминале
- Проверяйте блокировки перед редактированием

### Claude:
- Всегда блокируйте файлы перед редактированием
- Используйте команды через терминал

### Codex:
- Следуйте тем же правилам блокировки
- Координируйтесь через систему сообщений

## Примеры использования

### Backend Agent редактирует GroupService:
```bash
# 1. Заблокировать
./agent_coordinator.sh lock BE_001_v1 app/services/group_service.py

# 2. Проверить
./agent_coordinator.sh check app/services/group_service.py

# 3. Редактировать файл (в IDE)

# 4. Запустить линтер только на этом файле
uv run mypy app/services/group_service.py

# 5. Разблокировать
./agent_coordinator.sh unlock BE_001_v1 app/services/group_service.py
```

### Конфликт между агентами:
```bash
# Frontend Agent пытается заблокировать
./agent_coordinator.sh lock FE_001_v1 app/bot/handlers/group_handler.py
# Ошибка: файл уже заблокирован BE_001_v1

# Сообщить Архитектору
send_message "КОНФЛИКТ: group_handler.py заблокирован BE_001_v1. Нужна координация." "coordination"
```

---

**ПОМНИТЕ**: Нарушение правил координации приводит к конфликтам и сбоям системы!
