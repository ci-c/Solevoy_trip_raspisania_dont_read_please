# Примеры использования системы ID агентов

## Регистрация агентов

### Пример 1: Регистрация Backend агента
```bash
./register_agent.sh "BE" "Backend Specialist"
```
**Результат**:
```
==================================================
Агент успешно зарегистрирован!
==================================================

ID агента: BE_001_v1
Роль: BE
Имя: Backend Specialist
Дата регистрации: 2025-01-24
```

### Пример 2: Регистрация Frontend агента
```bash
./register_agent.sh "FE" "UI/UX Developer"
```
**Результат**:
```
ID агента: FE_001_v1
Роль: FE
Имя: UI/UX Developer
```

### Пример 3: Регистрация QA агента
```bash
./register_agent.sh "QA" "Quality Assurance"
```
**Результат**:
```
ID агента: QA_001_v1
Роль: QA
Имя: Quality Assurance
```

## Создание задач с ID агентов

### Пример 1: Backend агент создает задачу
```bash
# Backend агент (BE_001_v1) создает задачу
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить ошибку в GroupService +critical +bugfix +agent_id:BE_001_v1 @backend"
```

### Пример 2: Frontend агент создает задачу
```bash
# Frontend агент (FE_001_v1) создает задачу
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить отображение кнопок групп +ui +critical +agent_id:FE_001_v1 @frontend"
```

### Пример 3: QA агент создает задачу
```bash
# QA агент (QA_001_v1) создает задачу
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Написать тесты для GroupService +testing +pytest +agent_id:QA_001_v1 @qa"
```

## Коммуникация между агентами

### Пример 1: Backend агент сообщает о проблеме
```
[BE_001_v1] @FE_001_v1 Проблема с callback data
В GroupSelectionHandler callback data превышает 64 байта
Нужно сократить данные или использовать другой подход
+bugfix +callback @frontend
```

### Пример 2: Frontend агент отвечает
```
[FE_001_v1] @BE_001_v1 Готово к тестированию
Исправил callback data в GroupSelectionHandler
Используется хэширование для длинных названий факультетов
+ready +testing @qa
```

### Пример 3: QA агент подтверждает
```
[QA_001_v1] @FE_001_v1 Тесты пройдены
Все тесты для GroupSelectionHandler проходят успешно
Покрытие кода: 98%
+passed +testing @frontend
```

## Использование персональных команд агентов

### Работа через Python-CLI

#### Backend агент (BE_001_v1)
```bash
# Посмотреть задачи агента
python ai_docs/system/agent_system_cli.py tasks list --agent-id BE_001_v1

# Создать новую задачу
python ai_docs/system/agent_system_cli.py tasks add \
  "Исправить ошибку в UserService" \
  --priority A --role backend --agent-id BE_001_v1 \
  --tag critical --tag bugfix --story-points 2

# Отметить задачу как выполненную
python ai_docs/system/agent_system_cli.py tasks complete TSK-0005

# Обновить активность агента
python ai_docs/system/agent_system_cli.py agents touch BE_001_v1

# Зафиксировать сообщение в логах
echo "[BE_001_v1] Исправил ошибку в UserService.create_user" >> \
  ai_docs/state/agents/BE_001_v1/logs/backend.log
```

#### Frontend агент (FE_001_v1)
```bash
# Посмотреть задачи роли
python ai_docs/system/agent_system_cli.py tasks list --role frontend

# Создать задачу для улучшения UX
python ai_docs/system/agent_system_cli.py tasks add \
  "Улучшить UX выбора группы" \
  --priority B --role frontend --agent-id FE_001_v1 \
  --tag ux --tag improvement --story-points 3

# Зафиксировать обновление в общем канале
echo "[FE_001_v1] Обновил интерфейс выбора групп" >> logs/team_communication.log
```

#### QA агент (QA_001_v1)
```bash
# Посмотреть задачи агента
python ai_docs/system/agent_system_cli.py tasks list --agent-id QA_001_v1

# Создать задачу для написания тестов
python ai_docs/system/agent_system_cli.py tasks add \
  "Написать интеграционные тесты" \
  --priority B --role qa --agent-id QA_001_v1 \
  --tag testing --tag integration --story-points 5

# Зафиксировать отчет о тестировании
echo "[QA_001_v1] Все тесты пройдены успешно, покрытие 95%" >> \
  logs/team_communication.log
```

## Отслеживание работы агентов

### Просмотр активных агентов
```bash
python ai_docs/system/agent_system_cli.py agents list
```
```
# SZGMU Bot - Registry of Active Agents
# Format: AGENT_ID | ROLE | NAME | CREATED_DATE | STATUS | LAST_ACTIVITY

BE_001_v1 | BE | Backend Specialist | 2025-01-24 | active | 2025-01-24 15:30
FE_001_v1 | FE | UI/UX Developer | 2025-01-24 | active | 2025-01-24 15:25
QA_001_v1 | QA | Quality Assurance | 2025-01-24 | active | 2025-01-24 15:20
SM_001_v1 | SM | Task Manager Agent | 2025-01-24 | active | 2025-01-24 15:15
```

### Статистика по агентам
```bash
# Статистика для Backend агента
./agent_stats.sh "BE_001_v1"
```
**Вывод**:
```
=== Статистика агента BE_001_v1 ===

📊 Задачи: 5
✅ Завершено: 3
🔥 Критические задачи: 2
📅 За последнюю неделю: 3
```

### История активности агента
```bash
# История для Frontend агента
./agent_history.sh "FE_001_v1"
```
**Вывод**:
```
=== История активности FE_001_v1 ===

📋 Все задачи:
(A) 2025-01-24 Исправить отображение кнопок групп +ui +critical +agent_id:FE_001_v1 @frontend
(B) 2025-01-24 Улучшить UX выбора группы +ux +improvement +agent_id:FE_001_v1 @frontend

📊 Story Points: 5
```

## Ежедневные стендапы с ID агентов

### Утренний стендап
```bash
# Backend агент (BE_001_v1)
echo "[BE_001_v1] Daily Standup"
echo "Вчера: Исправил ошибку в GroupService.get_available_faculties"
echo "Сегодня: Работаю над валидацией данных в UserService"
echo "Препятствия: Нет"
```

### Frontend агент (FE_001_v1)
```bash
echo "[FE_001_v1] Daily Standup"
echo "Вчера: Исправил callback data для кнопок факультетов"
echo "Сегодня: Работаю над улучшением UX выбора групп"
echo "Препятствия: Нужна обратная связь от Backend агента"
```

### QA агент (QA_001_v1)
```bash
echo "[QA_001_v1] Daily Standup"
echo "Вчера: Написал тесты для GroupService"
echo "Сегодня: Тестирую новый UI для выбора групп"
echo "Препятствия: Нет"
```

## Спринт планирование с ID агентов

### Планирование задач
```bash
# Scrum Master агент (SM_001_v1) планирует спринт
echo "[SM_001_v1] Sprint Planning"
echo "Backlog для следующего спринта:"

# Критические задачи
./todo.txt-cli/todo.sh ls | grep "^(A)"

# Высокоприоритетные задачи
./todo.txt-cli/todo.sh ls | grep "^(B)" | head -5
```

### Назначение задач агентам
```bash
# Scrum Master назначает задачи
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить ошибку в GroupService +critical +bugfix +agent_id:BE_001_v1 @backend +assigned:BE_001_v1"
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить отображение кнопок групп +ui +critical +agent_id:FE_001_v1 @frontend +assigned:FE_001_v1"
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Написать тесты для GroupService +testing +pytest +agent_id:QA_001_v1 @qa +assigned:QA_001_v1"
```

## Эскалация проблем с ID агентов

### Уровень 1: Самостоятельное решение
```bash
# Backend агент решает проблему самостоятельно
echo "[BE_001_v1] Решил проблему с валидацией данных"
echo "Добавил проверку на null значения в UserService.create_user"
echo "+resolved +validation"
```

### Уровень 2: Scrum Master
```bash
# Frontend агент эскалирует к Scrum Master
echo "[FE_001_v1] @SM_001_v1 Нужна координация"
echo "Backend агент изменил API без уведомления Frontend команды"
echo "Это блокирует мою работу"
echo "+escalation +blocked"
```

### Уровень 3: Product Owner
```bash
# Scrum Master эскалирует к Product Owner
echo "[SM_001_v1] @PO_001_v1 Нужно решение по приоритетам"
echo "У нас 5 критических задач и только 2 разработчика"
echo "Нужно определить приоритеты"
echo "+escalation +priorities"
```

## Автоматизация с ID агентов

### Автоматический ежедневный отчет
```bash
#!/bin/bash
# daily_agent_report.sh

AGENT_ID="BE_001_v1"
echo "=== Daily Report for $AGENT_ID - $(date +%Y-%m-%d) ==="
echo ""

echo "📋 Мои активные задачи:"
./todo.txt-cli/todo.sh ls | grep "+agent_id:$AGENT_ID" | grep -v "^x"

echo ""
echo "✅ Завершено вчера:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d 'yesterday' +%Y-%m-%d)" | grep "+agent_id:$AGENT_ID"

echo ""
echo "🔥 Критические задачи:"
./todo.txt-cli/todo.sh ls | grep "^(A)" | grep "+agent_id:$AGENT_ID"

echo ""
echo "📊 Статистика:"
echo "Всего моих задач: $(./todo.txt-cli/todo.sh ls | grep "+agent_id:$AGENT_ID" | wc -l)"
echo "Завершено за неделю: $(./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '7 days ago' +%Y-%m-%d)" | grep "+agent_id:$AGENT_ID" | wc -l)"
```

### Автоматическое обновление активности
```bash
python ai_docs/system/agent_system_cli.py agents list | awk -F'|' '{print $1}' | tr -d ' ' |
  while read agent_id; do
    python ai_docs/system/agent_system_cli.py agents touch "$agent_id"
  done
```

## Резервное копирование и восстановление

### Создание резервной копии
```bash
BACKUP_DIR="backups/agents_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp ai_docs/state/agent_state.yaml "$BACKUP_DIR/"
cp -r ai_docs/state/agents "$BACKUP_DIR/"
cp -r logs "$BACKUP_DIR/"
```

### Восстановление из резервной копии
```bash
BACKUP_DIR="$1"
cp "$BACKUP_DIR/agent_state.yaml" ai_docs/state/agent_state.yaml
rm -rf ai_docs/state/agents
cp -r "$BACKUP_DIR/agents" ai_docs/state/
cp -r "$BACKUP_DIR/logs" .
```

---

