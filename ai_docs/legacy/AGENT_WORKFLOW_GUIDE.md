# Практическое руководство по работе агентов

## Быстрый старт для нового агента

### 1. Определение роли
Выберите свою роль из списка:
- **Product Owner Agent** - управление backlog и приоритетами
- **Backend Agent** - серверная логика и база данных
- **Frontend Agent** - UI/UX и интерфейс бота
- **QA Agent** - тестирование и качество
- **DevOps Agent** - развертывание и мониторинг
- **Scrum Master Agent** - координация и процессы

### 2. Регистрация агента
```bash
# Зарегистрировать нового агента
./register_agent.sh <ROLE> "<AGENT_NAME>"

# Пример
./register_agent.sh "BE" "Backend Specialist"
# Результат: BE_001_v1 зарегистрирован
```

### 3. Настройка окружения
```bash
# Перейти в рабочую директорию
cd /home/c/Documents/Project/P-2

# Проверить доступность todo.txt CLI
./todo.txt-cli/todo.sh version

# Загрузить команды своего агента
source agents/YOUR_AGENT_ID/commands.sh

# Посмотреть свои задачи
my_tasks
```

### 4. Ежедневный workflow
```bash
# Утренний чек-ин (5 минут)
./todo.txt-cli/todo.sh ls | grep "@your_role"
./todo.txt-cli/todo.sh ls | grep "^(A)"  # Критические задачи
tail -10 logs/errors.log  # Новые ошибки

# В течение дня
./todo.txt-cli/todo.sh do <номер>  # Отметить завершенную задачу
./todo.txt-cli/todo.sh add "..."   # Добавить новую задачу

# Вечерний отчет (3 минуты)
./todo.txt-cli/todo.sh ls | grep "^x.*$(date +%Y-%m-%d)"  # Что завершено
```

## Роли и их специфические задачи

### 🤖 Product Owner Agent

#### Ежедневные задачи
```bash
# Анализ backlog
./todo.txt-cli/todo.sh ls | grep -v "^x" | sort -k2

# Приоритизация критических задач
./todo.txt-cli/todo.sh ls | grep "^(A)"

# Планирование спринта
./todo.txt-cli/todo.sh ls | grep "^(B)" | head -10
```

#### Недельные задачи
- Sprint Planning (понедельник)
- Backlog Refinement (среда)
- Sprint Review (пятница)

#### Шаблоны задач
```bash
# Новая функция
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Реализовать функцию X +feature +5sp @backend"

# Багфикс
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить баг Y +bugfix +2sp @frontend"

# Техническая задача
./todo.txt-cli/todo.sh add "(C) 2025-01-24 Оптимизировать Z +performance +3sp @backend"
```

### 👨‍💻 Backend Agent

#### Специализация
- Services (app/services/)
- Database (app/database/)
- API интеграции (app/schedule/)
- Бизнес-логика

#### Ежедневные команды
```bash
# Проверка mypy ошибок
uv run mypy app/services/ --ignore-missing-imports

# Проверка тестов
uv run pytest tests/unit/test_services.py

# Анализ логов
tail -20 logs/errors.log | grep -i "service\|database\|api"
```

#### Шаблоны задач
```bash
# Исправление сервиса
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить GroupService.get_available_faculties +services +critical +2sp @backend"

# Новая интеграция
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Добавить API интеграцию с X +api +5sp @backend"

# Оптимизация БД
./todo.txt-cli/todo.sh add "(C) 2025-01-24 Оптимизировать запросы к БД +database +performance +3sp @backend"
```

### 🎨 Frontend Agent

#### Специализация
- Handlers (app/bot/handlers/)
- Keyboards (app/bot/keyboards.py)
- States (app/bot/states.py)
- Callbacks (app/bot/callbacks.py)

#### Ежедневные команды
```bash
# Проверка UI ошибок
tail -20 logs/errors.log | grep -i "handler\|callback\|keyboard"

# Тестирование бота
uv run python -m app.bot.main

# Проверка типов
uv run mypy app/bot/ --ignore-missing-imports
```

#### Шаблоны задач
```bash
# Исправление UI
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Исправить отображение кнопок групп +ui +critical +2sp @frontend"

# Новый handler
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Добавить handler для функции X +handler +3sp @frontend"

# UX улучшение
./todo.txt-cli/todo.sh add "(C) 2025-01-24 Улучшить UX выбора группы +ux +2sp @frontend"
```

### 🧪 QA Agent

#### Специализация
- Тесты (tests/)
- Документация (ai_docs/)
- Валидация данных
- Code review

#### Ежедневные команды
```bash
# Запуск тестов
uv run pytest tests/ -v

# Проверка покрытия
uv run pytest --cov=app tests/

# Анализ качества кода
uv run ruff check app/
uv run mypy app/ --ignore-missing-imports
```

#### Шаблоны задач
```bash
# Написание тестов
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Написать тесты для GroupService +testing +pytest +3sp @qa"

# Обновление документации
./todo.txt-cli/todo.sh add "(C) 2025-01-24 Обновить API документацию +docs +2sp @qa"

# Code review
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Code review для PR #123 +review +1sp @qa"
```

### 🚀 DevOps Agent

#### Специализация
- Развертывание
- Мониторинг (logs/)
- CI/CD
- Производительность

#### Ежедневные команды
```bash
# Проверка логов
tail -50 logs/bot.log
tail -20 logs/errors.log

# Мониторинг производительности
uv run python -c "from app.utils.error_monitor import get_error_stats; print(get_error_stats())"

# Проверка системы
df -h
free -h
```

#### Шаблоны задач
```bash
# Развертывание
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Развернуть версию 2.1.0 +deployment +5sp @devops"

# Мониторинг
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Настроить алерты для ошибок +monitoring +3sp @devops"

# Оптимизация
./todo.txt-cli/todo.sh add "(C) 2025-01-24 Оптимизировать производительность +performance +4sp @devops"
```

### 📋 Scrum Master Agent

#### Специализация
- Координация между агентами
- Устранение препятствий
- Процессы и метрики
- Коммуникация

#### Ежедневные команды
```bash
# Daily standup
./todo.txt-cli/todo.sh ls | grep "@backend\|@frontend\|@qa\|@devops"

# Анализ препятствий
./todo.txt-cli/todo.sh ls | grep "+blocked\|+impediment"

# Статистика команды
./todo.txt-cli/todo.sh ls | wc -l
./todo.txt-cli/todo.sh ls | grep "^x" | wc -l
```

#### Шаблоны задач
```bash
# Координация
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Координировать интеграцию X и Y +coordination +2sp @coordination"

# Устранение препятствий
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Устранить блокер для Backend Agent +impediment +1sp @coordination"

# Процессные улучшения
./todo.txt-cli/todo.sh add "(C) 2025-01-24 Улучшить процесс code review +process +3sp @coordination"
```

## Спринт workflow

### Sprint Planning (каждые 2 недели)
```bash
# 1. Анализ backlog
./todo.txt-cli/todo.sh ls | grep -v "^x" | sort -k2

# 2. Оценка capacity
echo "Backend: $(./todo.txt-cli/todo.sh ls | grep "@backend" | wc -l) задач"
echo "Frontend: $(./todo.txt-cli/todo.sh ls | grep "@frontend" | wc -l) задач"

# 3. Формирование Sprint Backlog
./todo.txt-cli/todo.sh ls | grep "^(A)\|^(B)" | head -10
```

### Daily Standup (ежедневно)
```bash
# Что сделал вчера
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d 'yesterday' +%Y-%m-%d)"

# Что планирую сегодня
./todo.txt-cli/todo.sh ls | grep "@your_role" | grep -v "^x" | head -3

# Препятствия
./todo.txt-cli/todo.sh ls | grep "+blocked\|+impediment"
```

### Sprint Review (конец спринта)
```bash
# Демонстрация результатов
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '2 weeks ago' +%Y-%m-%d)" | head -20

# Статистика спринта
echo "Завершено задач: $(./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '2 weeks ago' +%Y-%m-%d)" | wc -l)"
```

## Автоматизация и скрипты

### Ежедневный отчет агента
```bash
#!/bin/bash
# daily_agent_report.sh

AGENT_ROLE="$1"
DATE=$(date +%Y-%m-%d)

echo "=== Daily Report for $AGENT_ROLE - $DATE ==="
echo ""

echo "📋 Мои активные задачи:"
./todo.txt-cli/todo.sh ls | grep "@$AGENT_ROLE" | grep -v "^x"

echo ""
echo "✅ Завершено вчера:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d 'yesterday' +%Y-%m-%d)" | grep "@$AGENT_ROLE"

echo ""
echo "🔥 Критические задачи:"
./todo.txt-cli/todo.sh ls | grep "^(A)" | grep "@$AGENT_ROLE"

echo ""
echo "📊 Статистика:"
echo "Всего моих задач: $(./todo.txt-cli/todo.sh ls | grep "@$AGENT_ROLE" | wc -l)"
echo "Завершено за неделю: $(./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '7 days ago' +%Y-%m-%d)" | grep "@$AGENT_ROLE" | wc -l)"
```

### Автоматическое создание задач
```bash
#!/bin/bash
# create_task.sh

PRIORITY="$1"
DESCRIPTION="$2"
TAGS="$3"
AGENT="$4"
STORY_POINTS="$5"
DATE=$(date +%Y-%m-%d)

./todo.txt-cli/todo.sh add "($PRIORITY) $DATE $DESCRIPTION $TAGS +${STORY_POINTS}sp @$AGENT"

echo "Задача создана: $DESCRIPTION"
echo "Назначена агенту: $AGENT"
echo "Приоритет: $PRIORITY"
echo "Story Points: $STORY_POINTS"
```

### Анализ препятствий
```bash
#!/bin/bash
# analyze_impediments.sh

echo "=== Анализ препятствий $(date +%Y-%m-%d) ==="
echo ""

echo "🔴 Критические блокеры:"
./todo.txt-cli/todo.sh ls | grep "^(A)" | grep "+blocked"

echo ""
echo "🟡 Задачи без назначения:"
./todo.txt-cli/todo.sh ls | grep -v "^x" | grep -v "+assigned"

echo ""
echo "📈 Статистика по агентам:"
echo "Backend: $(./todo.txt-cli/todo.sh ls | grep "@backend" | grep -v "^x" | wc -l) активных задач"
echo "Frontend: $(./todo.txt-cli/todo.sh ls | grep "@frontend" | grep -v "^x" | wc -l) активных задач"
echo "QA: $(./todo.txt-cli/todo.sh ls | grep "@qa" | grep -v "^x" | wc -l) активных задач"
echo "DevOps: $(./todo.txt-cli/todo.sh ls | grep "@devops" | grep -v "^x" | wc -l) активных задач"
```

## Эскалация проблем

### Уровень 1: Самостоятельное решение
- Технические вопросы в своей области
- Небольшие изменения в scope
- Обычные багфиксы

### Уровень 2: Scrum Master
```bash
# Создать задачу для Scrum Master
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Координировать решение проблемы X +coordination +impediment +1sp @coordination"
```

### Уровень 3: Product Owner
```bash
# Создать задачу для Product Owner
./todo.txt-cli/todo.sh add "(A) 2025-01-24 Принять решение по приоритету Y +planning +decision +1sp @planning"
```

### Уровень 4: Emergency meeting
```bash
# Создать критическую задачу
./todo.txt-cli/todo.sh add "(A) 2025-01-24 EMERGENCY: Критическая проблема Z +emergency +all_hands +1sp @coordination"
```

## Метрики и отчетность

### Личные метрики агента
```bash
#!/bin/bash
# agent_metrics.sh

AGENT_ROLE="$1"

echo "=== Метрики для $AGENT_ROLE ==="
echo ""

echo "📊 Задачи за последний месяц:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '30 days ago' +%Y-%m-%d)" | grep "@$AGENT_ROLE" | wc -l

echo ""
echo "⚡ Velocity (Story Points за месяц):"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '30 days ago' +%Y-%m-%d)" | grep "@$AGENT_ROLE" | grep -o "+[0-9]*sp" | sed 's/+//; s/sp//' | awk '{sum += $1} END {print sum}'

echo ""
echo "🎯 Completion rate:"
TOTAL=$(./todo.txt-cli/todo.sh ls | grep "@$AGENT_ROLE" | wc -l)
COMPLETED=$(./todo.txt-cli/todo.sh ls | grep "^x" | grep "@$AGENT_ROLE" | wc -l)
if [ $TOTAL -gt 0 ]; then
    echo "$((COMPLETED * 100 / TOTAL))%"
else
    echo "0%"
fi
```

### Командные метрики
```bash
#!/bin/bash
# team_metrics.sh

echo "=== Командные метрики $(date +%Y-%m-%d) ==="
echo ""

echo "📈 Общая статистика:"
echo "Всего задач: $(./todo.txt-cli/todo.sh ls | wc -l)"
echo "Завершено: $(./todo.txt-cli/todo.sh ls | grep "^x" | wc -l)"
echo "Активных: $(./todo.txt-cli/todo.sh ls | grep -v "^x" | wc -l)"

echo ""
echo "🔥 Критические задачи:"
./todo.txt-cli/todo.sh ls | grep "^(A)" | wc -l

echo ""
echo "👥 Распределение по агентам:"
echo "Backend: $(./todo.txt-cli/todo.sh ls | grep "@backend" | wc -l)"
echo "Frontend: $(./todo.txt-cli/todo.sh ls | grep "@frontend" | wc -l)"
echo "QA: $(./todo.txt-cli/todo.sh ls | grep "@qa" | wc -l)"
echo "DevOps: $(./todo.txt-cli/todo.sh ls | grep "@devops" | wc -l)"

echo ""
echo "📅 Завершено за неделю:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '7 days ago' +%Y-%m-%d)" | wc -l
```

---

**Использование**: Каждый агент должен изучить свою роль и использовать соответствующие команды и процессы.
