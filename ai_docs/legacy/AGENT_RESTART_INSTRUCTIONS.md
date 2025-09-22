# Инструкции для перезапуска агентов

## 🚨 ВАЖНО: Читайте это перед началом работы!

### Что изменилось:
1. **Система автоматического назначения ролей** - роли назначаются автоматически
2. **Система координации файлов** - файлы блокируются перед редактированием
3. **Предотвращение конфликтов** - агенты не могут редактировать одни файлы

## Быстрый старт

### 1. Запросите назначение роли
```bash
cd /home/c/Documents/Project/P-2
./role_manager.sh assign "Ваше имя"
```

### 2. Изучите правила координации
```bash
# ОБЯЗАТЕЛЬНО прочитайте
cat ai_docs/AGENT_COORDINATION_RULES.md
```

### 3. Загрузите команды
```bash
source agents/YOUR_ID/commands.sh
```

### 4. Проверьте статус системы
```bash
# Статус блокировок
./agent_coordinator.sh status

# Ваши задачи
my_tasks
```

### 5. Начните работу с блокировкой файлов
```bash
# ЗАБЛОКИРУЙТЕ файлы перед редактированием
./agent_coordinator.sh lock YOUR_AGENT_ID path/to/file.py

# Выполните работу

# РАЗБЛОКИРУЙТЕ файлы после завершения
./agent_coordinator.sh unlock YOUR_AGENT_ID path/to/file.py
```

## Критические правила

### ❌ НЕ ДЕЛАЙТЕ:
- Не редактируйте файлы без блокировки
- Не запускайте множественные процессы линтеров
- Не конфликтуйте с другими агентами
- Не выбирайте роль сами

### ✅ ДЕЛАЙТЕ:
- Всегда блокируйте файлы перед редактированием
- Следуйте назначенной роли
- Координируйтесь с другими агентами
- Сообщайте о проблемах Архитектору

## Системы управления

### 1. Назначение ролей:
```bash
./role_manager.sh assign "Имя"           # Запросить роль
./role_manager.sh status                 # Статус ролей
./role_manager.sh reassign ID ROLE       # Перераспределить роль
```

### 2. Координация файлов:
```bash
./agent_coordinator.sh lock ID FILE      # Заблокировать файл
./agent_coordinator.sh unlock ID FILE    # Разблокировать файл
./agent_coordinator.sh check FILE        # Проверить блокировку
./agent_coordinator.sh status            # Статус блокировок
```

### 3. Управление агентами:
```bash
./agent_manager.sh list                  # Список агентов
./agent_manager.sh info ID               # Информация об агенте
```

## Workflow для разных ролей

### Backend Agent:
```bash
# 1. Получить задачи
my_tasks

# 2. Заблокировать файлы сервисов
./agent_coordinator.sh lock YOUR_ID app/services/group_service.py

# 3. Редактировать файл
# 4. Запустить линтер на файле
uv run mypy app/services/group_service.py

# 5. Разблокировать файл
./agent_coordinator.sh unlock YOUR_ID app/services/group_service.py

# 6. Завершить задачу
complete_task TASK_ID
```

### Frontend Agent:
```bash
# 1. Получить задачи
my_tasks

# 2. Заблокировать файлы handlers
./agent_coordinator.sh lock YOUR_ID app/bot/handlers/group_handler.py

# 3. Редактировать файл
# 4. Запустить линтер на файле
uv run mypy app/bot/handlers/group_handler.py

# 5. Разблокировать файл
./agent_coordinator.sh unlock YOUR_ID app/bot/handlers/group_handler.py

# 6. Завершить задачу
complete_task TASK_ID
```

### QA Agent:
```bash
# 1. Получить задачи
my_tasks

# 2. Заблокировать тестовые файлы
./agent_coordinator.sh lock YOUR_ID tests/test_group_service.py

# 3. Написать тесты
# 4. Запустить тесты
uv run pytest tests/test_group_service.py

# 5. Разблокировать файл
./agent_coordinator.sh unlock YOUR_ID tests/test_group_service.py

# 6. Завершить задачу
complete_task TASK_ID
```

## Обработка конфликтов

### Если файл заблокирован:
```bash
# 1. НЕ РЕДАКТИРУЙТЕ файл
# 2. Сообщите Архитектору
send_message "КОНФЛИКТ: Файл path/to/file.py заблокирован агентом OTHER_ID. Нужна координация." "coordination"

# 3. Дождитесь решения Архитектора
```

### Если процесс завис:
```bash
# Сообщите Архитектору
send_message "ПРОБЛЕМА: Процесс линтера/теста завис. Нужно вмешательство." "coordination"
```

## Мониторинг и отчетность

### Ежедневные проверки:
```bash
# Статус блокировок
./agent_coordinator.sh status

# Ваши задачи
my_tasks

# Активность команды
./agent_manager.sh list
```

### Отчеты:
```bash
# Отправить отчет о работе
send_message "Отчет: Выполнено X задач, разблокированы файлы Y, Z" "general"

# Обновить активность
update_activity
```

## Совместимость с IDE

### Cursor:
- Используйте терминал для команд координации
- Проверяйте блокировки перед редактированием в IDE

### Claude/Codex:
- Всегда блокируйте файлы перед редактированием
- Используйте команды через терминал

## Экстренные ситуации

### Если система зависла:
```bash
# Сообщите Архитектору
send_message "ЭКСТРЕННО: Система зависла, нужна помощь Архитектора" "emergency"
```

### Если нужно принудительно разблокировать:
```bash
# Только Архитектор может
./agent_coordinator.sh force_unlock path/to/file.py
```

### Если нужно остановить все процессы:
```bash
# Только Архитектор может
./agent_coordinator.sh kill_processes
```

---

**ПОМНИТЕ**: Соблюдение правил координации критически важно для работы системы!
