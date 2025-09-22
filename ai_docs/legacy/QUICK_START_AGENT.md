# Быстрый старт агента-менеджера задач

## Первые шаги (5 минут)

### 1. Проверить текущий статус
```bash
cd /home/c/Documents/Project/P-2

# Посмотреть активные задачи
./todo.txt-cli/todo.sh ls | grep -v "^x"

# Проверить критические задачи
./todo.txt-cli/todo.sh ls | grep "^(A)"
```

### 2. Анализ проблем
```bash
# Проверить ошибки mypy
uv run mypy app/ --ignore-missing-imports | head -10

# Посмотреть последние ошибки в логах
tail -20 logs/errors.log

# Проверить git статус
git status --porcelain | wc -l
```

### 3. Определить приоритеты
```bash
# Критические задачи (A) - требуют немедленного внимания
./todo.txt-cli/todo.sh ls | grep "^(A)"

# Высокоприоритетные (B) - важны для функциональности
./todo.txt-cli/todo.sh ls | grep "^(B)"
```

## Критические проблемы (требуют немедленного внимания)

### 1. Ошибки типизации
- **426 ошибок mypy** по всему проекту
- Конфликт модулей в start_handler
- **Действие**: Назначить Backend агенту

### 2. Проблемы с группами
- Группы не создаются автоматически
- Пользователи не привязываются к группам
- **Действие**: Назначить Backend агенту

### 3. UI проблемы
- Кнопки не отображаются
- Callback data слишком длинные
- **Действие**: Назначить Frontend агенту

## Распределение задач по агентам

### Backend агент
- Исправление mypy ошибок
- Проблемы с GroupService
- Database интеграция
- API синхронизация

### Frontend агент
- UI/UX проблемы
- Callback handlers
- Keyboard генерация
- Обработка состояний

### QA агент
- Написание тестов
- Валидация данных
- Проверка безопасности
- Документация

## Ежедневный workflow

### Утром (10 минут)
```bash
# 1. Проверить новые задачи
./todo.txt-cli/todo.sh ls | grep "$(date +%Y-%m-%d)"

# 2. Проверить критические задачи
./todo.txt-cli/todo.sh ls | grep "^(A)"

# 3. Посмотреть новые ошибки
tail -10 logs/errors.log
```

### В течение дня
- Отслеживать прогресс агентов
- Уточнять детали задач
- Корректировать приоритеты

### Вечером (5 минут)
```bash
# 1. Обновить статус выполненных задач
./todo.txt-cli/todo.sh do <номер_задачи>

# 2. Добавить новые задачи (если появились)
./todo.txt-cli/todo.sh add "Описание +теги @проект"

# 3. Проверить статистику
./todo.txt-cli/todo.sh ls | wc -l
```

## Команды для быстрого доступа

### Просмотр задач
```bash
alias tasks='./todo.txt-cli/todo.sh ls'
alias critical='./todo.txt-cli/todo.sh ls | grep "^(A)"'
alias active='./todo.txt-cli/todo.sh ls | grep -v "^x"'
```

### Управление
```bash
alias add-task='./todo.txt-cli/todo.sh add'
alias done='./todo.txt-cli/todo.sh do'
alias priority='./todo.txt-cli/todo.sh pri'
```

### Анализ
```bash
alias errors='tail -20 logs/errors.log'
alias mypy-check='uv run mypy app/ --ignore-missing-imports | head -10'
alias git-status='git status --porcelain'
```

## Шаблоны задач

### Критическая ошибка
```
(A) 2025-01-24 Исправить ошибку в <компонент> +critical +bugfix @technical
```

### Новый функционал
```
(B) 2025-01-24 Добавить <функция> +ui +feature @features
```

### Техническое улучшение
```
(C) 2025-01-24 Оптимизировать <компонент> +performance @technical
```

### Документация
```
(B) 2025-01-24 Обновить документацию по <модуль> +docs @planning
```

## Контакты и ресурсы

### Ключевые файлы
- `todo.txt` - основной список задач
- `logs/errors.log` - ошибки системы
- `ai_docs/ARCHITECTURE.md` - архитектура
- `ai_docs/CODESTYLE.md` - стандарты кода

### Полезные команды
```bash
# Быстрый запуск бота для тестирования
uv run python -m app.bot.main

# Проверка здоровья системы
uv run python -c "from app.utils.error_monitor import get_error_stats; print(get_error_stats())"

# Создание backup БД
cp data/szgmu_bot.db data/szgmu_bot.db.backup.$(date +%Y%m%d)
```

## Аварийные процедуры

### Если много ошибок
1. Остановить бота
2. Проверить критические ошибки
3. Исправить блокеры
4. Постепенно запускать компоненты

### Если БД проблемы
1. Создать backup
2. Проверить миграции
3. Восстановить из backup при необходимости

---

**Время на изучение**: 5 минут  
**Время на ежедневную работу**: 15-20 минут  
**Критические задачи**: Требуют немедленного внимания
