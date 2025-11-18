# Управление задачами через todo.txt CLI

## Настройка окружения

### Рабочая директория
```bash
cd /home/c/Documents/Project/P-2
```

### Проверка доступности CLI
```bash
./todo.txt-cli/todo.sh version
```

## Основные команды

### Просмотр задач
```bash
# Все задачи
./todo.txt-cli/todo.sh ls

# Только активные (не завершенные)
./todo.txt-cli/todo.sh ls | grep -v "^x"

# По приоритету
./todo.txt-cli/todo.sh ls | grep "^(A)"
./todo.txt-cli/todo.sh ls | grep "^(B)"
./todo.txt-cli/todo.sh ls | grep "^(C)"

# По проекту
./todo.txt-cli/todo.sh ls | grep "@planning"
./todo.txt-cli/todo.sh ls | grep "@features"
./todo.txt-cli/todo.sh ls | grep "@technical"
```

### Управление задачами
```bash
# Добавить новую задачу
./todo.txt-cli/todo.sh add "Описание задачи +tag @project"

# Отметить как выполненную
./todo.txt-cli/todo.sh do 1

# Установить приоритет
./todo.txt-cli/todo.sh pri 1 A    # Высокий
./todo.txt-cli/todo.sh pri 1 B    # Средний
./todo.txt-cli/todo.sh pri 1 C    # Низкий

# Удалить задачу
./todo.txt-cli/todo.sh rm 1
```

### Анализ и статистика
```bash
# Показать проекты
./todo.txt-cli/todo.sh proj

# Показать контексты
./todo.txt-cli/todo.sh context

# Статистика по датам
./todo.txt-cli/todo.sh ls | grep -E "^x.*$(date +%Y-%m-%d)"

# Поиск по тегам
./todo.txt-cli/todo.sh ls | grep "+critical"
./todo.txt-cli/todo.sh ls | grep "+ui"
./todo.txt-cli/todo.sh ls | grep "+backend"
```

## Форматы записей

### Новая задача
```
(A) 2025-01-24 Описание задачи +tag1 +tag2 @project
```

### Завершенная задача
```
x 2025-01-24 Описание задачи +tag1 +tag2 @project
```

### Приоритеты
- `(A)` - Критический (блокирует работу)
- `(B)` - Высокий (важно для функциональности)
- `(C)` - Средний (желательно)

## Теги (tags)

### Функциональные
- `+ui` - Пользовательский интерфейс
- `+ux` - Пользовательский опыт
- `+backend` - Серверная логика
- `+frontend` - Клиентская часть
- `+api` - API интеграция
- `+database` - Работа с БД

### Технические
- `+critical` - Критические ошибки
- `+bugfix` - Исправление ошибок
- `+testing` - Тестирование
- `+docs` - Документация
- `+security` - Безопасность
- `+performance` - Производительность

### Статусные
- `+completed` - Выполнено
- `+in_progress` - В работе
- `+blocked` - Заблокировано
- `+waiting` - Ожидает

## Проекты (@)

### Основные
- `@planning` - Планирование и архитектура
- `@features` - Новый функционал
- `@technical` - Техническая работа
- `@ux_redesign` - Переработка UX
- `@code_quality` - Качество кода

### Специализированные
- `@bot` - Telegram бот
- `@api` - API интеграции
- `@database` - База данных
- `@testing` - Тестирование
- `@deployment` - Развертывание

## Рабочие процессы

### Ежедневный обзор
```bash
#!/bin/bash
# daily_review.sh

echo "=== Ежедневный обзор задач ==="
echo "Дата: $(date +%Y-%m-%d)"
echo ""

echo "Критические задачи (A):"
./todo.txt-cli/todo.sh ls | grep "^(A)"

echo ""
echo "Высокоприоритетные задачи (B):"
./todo.txt-cli/todo.sh ls | grep "^(B)"

echo ""
echo "Завершенные за сегодня:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date +%Y-%m-%d)"

echo ""
echo "Статистика по проектам:"
./todo.txt-cli/todo.sh proj
```

### Недельный отчет
```bash
#!/bin/bash
# weekly_report.sh

echo "=== Недельный отчет ==="
echo "Период: $(date -d '7 days ago' +%Y-%m-%d) - $(date +%Y-%m-%d)"
echo ""

echo "Завершенные задачи:"
./todo.txt-cli/todo.sh ls | grep "^x.*$(date -d '7 days ago' +%Y-%m-%d)" | head -20

echo ""
echo "Активные задачи по приоритетам:"
echo "Критические (A):"
./todo.txt-cli/todo.sh ls | grep "^(A)" | wc -l

echo "Высокие (B):"
./todo.txt-cli/todo.sh ls | grep "^(B)" | wc -l

echo "Средние (C):"
./todo.txt-cli/todo.sh ls | grep "^(C)" | wc -l

echo ""
echo "Распределение по проектам:"
./todo.txt-cli/todo.sh proj
```

## Интеграция с Git

### Автоматическое добавление задач из коммитов
```bash
#!/bin/bash
# git_hook.sh

# Добавить задачу из commit message
COMMIT_MSG="$1"
if [[ $COMMIT_MSG == *"[TODO]"* ]]; then
    TASK=$(echo "$COMMIT_MSG" | sed 's/.*\[TODO\]\s*//')
    ./todo.txt-cli/todo.sh add "$TASK"
fi
```

### Отслеживание прогресса
```bash
#!/bin/bash
# track_progress.sh

# Найти задачи, связанные с последними коммитами
git log --oneline -10 | while read commit; do
    echo "Коммит: $commit"
    # Извлечь номер задачи из commit message (если есть)
    TASK_ID=$(echo "$commit" | grep -o "#[0-9]*" | sed 's/#//')
    if [ ! -z "$TASK_ID" ]; then
        echo "  Связанная задача: $TASK_ID"
    fi
done
```

## Мониторинг и алерты

### Проверка просроченных задач
```bash
#!/bin/bash
# check_overdue.sh

TODAY=$(date +%Y-%m-%d)
OVERDUE_COUNT=$(./todo.txt-cli/todo.sh ls | grep -v "^x" | awk '{print $2}' | grep -v "^$TODAY" | wc -l)

if [ $OVERDUE_COUNT -gt 5 ]; then
    echo "⚠️  ВНИМАНИЕ: $OVERDUE_COUNT просроченных задач!"
    ./todo.txt-cli/todo.sh ls | grep -v "^x" | awk '{print $2}' | grep -v "^$TODAY"
fi
```

### Уведомления о критических задачах
```bash
#!/bin/bash
# critical_alert.sh

CRITICAL_COUNT=$(./todo.txt-cli/todo.sh ls | grep "^(A)" | wc -l)

if [ $CRITICAL_COUNT -gt 0 ]; then
    echo "🚨 КРИТИЧЕСКИЕ ЗАДАЧИ: $CRITICAL_COUNT"
    ./todo.txt-cli/todo.sh ls | grep "^(A)"
fi
```

## Примеры использования

### Добавление задач по категориям
```bash
# Критическая ошибка
./todo.txt-cli/todo.sh add "(A) Исправить ошибку в GroupService +critical +backend +bugfix @technical"

# Новый функционал
./todo.txt-cli/todo.sh add "(B) Добавить уведомления о расписании +ui +notifications @features"

# Техническое улучшение
./todo.txt-cli/todo.sh add "(C) Оптимизировать запросы к БД +performance +database @technical"

# Документация
./todo.txt-cli/todo.sh add "(B) Обновить API документацию +docs @planning"
```

### Массовые операции
```bash
# Установить высокий приоритет всем задачам с тегом +critical
./todo.txt-cli/todo.sh ls | grep "+critical" | awk '{print $1}' | sed 's/^.*(//; s/).*$//' | while read num; do
    ./todo.txt-cli/todo.sh pri $num A
done

# Отметить как завершенные все задачи с тегом +completed
./todo.txt-cli/todo.sh ls | grep "+completed" | awk '{print $1}' | sed 's/^.*(//; s/).*$//' | while read num; do
    ./todo.txt-cli/todo.sh do $num
done
```

## Интеграция с другими инструментами

### Экспорт в CSV
```bash
./todo.txt-cli/todo.sh ls > tasks.csv
```

### Синхронизация с внешними системами
```bash
# Экспорт для Jira/GitHub Issues
./todo.txt-cli/todo.sh ls | grep "^(A)" | while read line; do
    echo "CRITICAL: $line"
done
```

---

**Примечание**: Все скрипты должны быть исполняемыми (`chmod +x script.sh`) и находиться в PATH или вызываться с полным путем.
