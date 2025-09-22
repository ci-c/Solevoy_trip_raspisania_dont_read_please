# Система взаимодействия агентов на основе Agile

## Обзор системы

Система управления проектом SZGMU Bot построена на принципах Agile методологии с распределением ролей между специализированными агентами. Каждый агент отвечает за свою область экспертизы и взаимодействует с другими через четко определенные процессы.

## Роли агентов

### 🤖 Product Owner Agent (PO Agent)
**Ответственность**: Управление backlog, приоритизация, планирование спринтов
- Анализирует требования пользователей
- Приоритизирует задачи в todo.txt
- Планирует спринты и релизы
- Принимает решения о scope и направлении развития

### 👨‍💻 Backend Agent (BE Agent)
**Ответственность**: Серверная логика, база данных, API, сервисы
- Исправление ошибок в services/
- Работа с базой данных
- API интеграции
- Бизнес-логика

### 🎨 Frontend Agent (FE Agent)
**Ответственность**: UI/UX, обработчики, клавиатуры, состояния
- Telegram bot интерфейс
- Handlers и callbacks
- Клавиатуры и навигация
- UX оптимизация

### 🧪 QA Agent (QA Agent)
**Ответственность**: Тестирование, валидация, документация, качество
- Написание тестов
- Валидация данных
- Документация
- Code review

### 🚀 DevOps Agent (DevOps Agent)
**Ответственность**: Развертывание, мониторинг, инфраструктура
- CI/CD процессы
- Мониторинг и логи
- Развертывание
- Производительность

### 📋 Scrum Master Agent (SM Agent)
**Ответственность**: Координация, процессы, препятствия, коммуникация
- Организация daily standups
- Устранение препятствий
- Координация между агентами
- Отслеживание прогресса

## Agile процессы

### Sprint Planning (Планирование спринта)
**Частота**: Каждые 2 недели
**Участники**: Все агенты
**Процесс**:
1. PO Agent представляет backlog с приоритетами
2. Агенты оценивают сложность задач (Story Points)
3. Формируется Sprint Backlog
4. Определяются Sprint Goals

### Daily Standup (Ежедневные стендапы)
**Частота**: Ежедневно в 9:00
**Участники**: Все агенты
**Формат**:
- Что сделал вчера?
- Что планирую сегодня?
- Какие препятствия?

### Sprint Review (Обзор спринта)
**Частота**: В конце каждого спринта
**Участники**: Все агенты + Stakeholder
**Процесс**:
1. Демонстрация выполненных задач
2. Обсуждение результатов
3. Обратная связь
4. Планирование следующего спринта

### Sprint Retrospective (Ретроспектива)
**Частота**: В конце каждого спринта
**Участники**: Все агенты
**Формат**:
- Что прошло хорошо?
- Что можно улучшить?
- Action items на следующий спринт

## Управление задачами

### Формат задач в todo.txt
```
(PRIORITY) YYYY-MM-DD Описание задачи +tags @agent +story_points
```

### Приоритеты
- `(A)` - Critical (блокирует работу)
- `(B)` - High (важно для функциональности)
- `(C)` - Medium (улучшения)
- `(D)` - Low (nice to have)

### Story Points (оценка сложности)
- `+1sp` - Очень просто (1-2 часа)
- `+2sp` - Просто (полдня)
- `+3sp` - Средне (1 день)
- `+5sp` - Сложно (2-3 дня)
- `+8sp` - Очень сложно (неделя)
- `+13sp` - Epic (нужно разбить)

### Теги по агентам
- `@backend` - Backend Agent
- `@frontend` - Frontend Agent
- `@qa` - QA Agent
- `@devops` - DevOps Agent
- `@planning` - Product Owner Agent
- `@coordination` - Scrum Master Agent

## Workflow процессов

### 1. Создание задачи
```bash
# PO Agent создает задачу
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Реализовать новую функцию +feature +3sp @backend"
```

### 2. Назначение задачи
```bash
# SM Agent назначает задачу
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Реализовать новую функцию +feature +3sp @backend +assigned:be_agent"
```

### 3. Начало работы
```bash
# Backend Agent берет в работу
./todo.txt-cli/todo.sh add "(B) 2025-01-24 Реализовать новую функцию +feature +3sp @backend +assigned:be_agent +status:in_progress"
```

### 4. Завершение
```bash
# Backend Agent завершает
./todo.txt-cli/todo.sh do <номер_задачи>
```

### 5. Code Review
```bash
# QA Agent проверяет
./todo.txt-cli/todo.sh add "x 2025-01-24 Реализовать новую функцию +feature +3sp @backend +reviewed:qa_agent"
```

## Коммуникация между агентами

### Slack-подобные каналы
- `#general` - Общие вопросы
- `#backend` - Backend Agent
- `#frontend` - Frontend Agent
- `#qa` - QA Agent
- `#devops` - DevOps Agent
- `#planning` - Product Owner Agent
- `#scrum` - Scrum Master Agent

### Формат сообщений
```
[AGENT] @mention Заголовок
Описание проблемы/вопроса
+tags @related_agent
```

### Эскалация проблем
1. **Level 1**: Обсуждение в канале агента
2. **Level 2**: Привлечение SM Agent
3. **Level 3**: Привлечение PO Agent
4. **Level 4**: Emergency meeting всех агентов

## Метрики и KPI

### Velocity (Скорость команды)
- Story Points за спринт
- Тренд по спринтам
- Прогнозирование capacity

### Burndown Chart
- Оставшиеся Story Points
- Прогресс по дням спринта
- Выявление проблем

### Quality Metrics
- Количество багов в production
- Code coverage
- Mypy ошибки
- Performance metrics

### Lead Time
- От создания задачи до завершения
- Time to market для новых функций

## Инструменты и автоматизация

### Автоматические отчеты
```bash
#!/bin/bash
# daily_report.sh - запускается каждый день в 8:00

echo "=== Daily Report $(date +%Y-%m-%d) ==="
echo ""

echo "🔥 Критические задачи:"
./todo.txt-cli/todo.sh ls | grep "^(A)"

echo ""
echo "📊 Статистика по агентам:"
echo "Backend: $(./todo.txt-cli/todo.sh ls | grep "@backend" | wc -l)"
echo "Frontend: $(./todo.txt-cli/todo.sh ls | grep "@frontend" | wc -l)"
echo "QA: $(./todo.txt-cli/todo.sh ls | grep "@qa" | wc -l)"

echo ""
echo "✅ Завершено вчера:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d 'yesterday' +%Y-%m-%d)"
```

### Sprint Planning автоматизация
```bash
#!/bin/bash
# sprint_planning.sh

echo "=== Sprint Planning $(date +%Y-%m-%d) ==="
echo ""

echo "📋 Backlog с приоритетами:"
./todo.txt-cli/todo.sh ls | grep -v "^x" | sort -k2

echo ""
echo "🎯 Предлагаемый Sprint Backlog:"
./todo.txt-cli/todo.sh ls | grep "^(A)\|^(B)" | head -10
```

### Burndown tracking
```bash
#!/bin/bash
# burndown.sh

TOTAL_SP=$(./todo.txt-cli/todo.sh ls | grep -o "+[0-9]*sp" | sed 's/+//; s/sp//' | awk '{sum += $1} END {print sum}')
COMPLETED_SP=$(./todo.txt-cli/todo.sh ls | grep "^x" | grep -o "+[0-9]*sp" | sed 's/+//; s/sp//' | awk '{sum += $1} END {print sum}')
REMAINING_SP=$((TOTAL_SP - COMPLETED_SP))

echo "Total Story Points: $TOTAL_SP"
echo "Completed: $COMPLETED_SP"
echo "Remaining: $REMAINING_SP"
echo "Progress: $((COMPLETED_SP * 100 / TOTAL_SP))%"
```

## Роли и ответственность

### Product Owner Agent
- **Входные данные**: Требования пользователей, бизнес-цели
- **Выходные данные**: Приоритизированный backlog, acceptance criteria
- **Инструменты**: todo.txt, user stories, acceptance tests

### Backend Agent
- **Входные данные**: Technical requirements, API specs
- **Выходные данные**: Working code, database schemas, API endpoints
- **Инструменты**: Python, SQLAlchemy, API clients

### Frontend Agent
- **Входные данные**: UI/UX designs, user flows
- **Выходные данные**: Telegram bot interface, handlers, keyboards
- **Инструменты**: aiogram, FSM, keyboards

### QA Agent
- **Входные данные**: Code, requirements, test cases
- **Выходные данные**: Test reports, documentation, quality metrics
- **Инструменты**: pytest, mypy, documentation tools

### DevOps Agent
- **Входные данные**: Deployment requirements, monitoring needs
- **Выходные данные**: CI/CD pipelines, monitoring dashboards, infrastructure
- **Инструменты**: Docker, CI/CD tools, monitoring systems

### Scrum Master Agent
- **Входные данные**: Team impediments, process issues
- **Выходные данные**: Resolved blockers, improved processes
- **Инструменты**: todo.txt, communication tools, metrics

## Критерии готовности (Definition of Ready)

Задача готова к работе, если:
- [ ] Описание четкое и понятное
- [ ] Acceptance criteria определены
- [ ] Story Points оценены
- [ ] Назначен ответственный агент
- [ ] Зависимости выявлены
- [ ] Технические требования ясны

## Критерии завершения (Definition of Done)

Задача завершена, если:
- [ ] Код написан и протестирован
- [ ] Code review пройден
- [ ] Тесты написаны и проходят
- [ ] Документация обновлена
- [ ] Логирование добавлено
- [ ] Performance проверен
- [ ] Security review пройден

## Эскалация и разрешение конфликтов

### Уровень 1: Агент решает самостоятельно
- Технические вопросы в своей области
- Небольшие изменения в scope

### Уровень 2: Scrum Master координирует
- Межкомандные конфликты
- Процессные вопросы

### Уровень 3: Product Owner принимает решение
- Изменения в приоритетах
- Scope изменения

### Уровень 4: Emergency meeting
- Критические проблемы
- Блокеры всего проекта

## Continuous Improvement

### Ретроспективы
- Что прошло хорошо?
- Что можно улучшить?
- Action items

### Метрики для анализа
- Velocity trends
- Bug rates
- Lead times
- Team satisfaction

### Эксперименты
- Новые процессы
- Инструменты
- Методологии

---

**Система обновлена**: 2025-01-24  
**Версия**: 1.0  
**Статус**: Активная
