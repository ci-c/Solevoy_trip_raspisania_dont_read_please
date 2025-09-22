# Архитектура SZGMU Bot

## Обзор системы

SZGMU Bot - это Telegram бот для получения расписания занятий СЗГМУ. Система построена на модульной архитектуре с четким разделением ответственности.

## Основные компоненты

### 1. Bot Layer (`app/bot/`)
- **main.py** - Главный файл запуска бота
- **handlers/** - Обработчики команд и callback'ов
- **middleware/** - Middleware для обработки ошибок
- **keyboards.py** - Генерация клавиатур
- **states.py** - FSM состояния
- **callbacks.py** - Callback data factories

### 2. Services Layer (`app/services/`)
- **schedule_service.py** - Работа с расписанием
- **group_service.py** - Управление группами
- **user_service.py** - Управление пользователями
- **faculty_service.py** - Работа с факультетами
- **api_sync_service.py** - Синхронизация с внешним API
- **background_scheduler.py** - Фоновые задачи
- **invitation_service.py** - Система инвайтов
- **education_service.py** - Образовательные данные
- **academic_service.py** - Академические данные
- **grade_calculator_service.py** - Расчет оценок
- **real_schedule_service.py** - Реальное расписание
- **schedule_updater_service.py** - Обновление расписания
- **startup_service.py** - Инициализация системы
- **data_initialization_service.py** - Инициализация данных

### 3. Database Layer (`app/database/`)
- **models.py** - SQLAlchemy модели
- **session.py** - Управление сессиями БД
- **repositories/** - Репозитории для работы с данными

### 4. Models Layer (`app/models/`)
- **user.py** - Pydantic модели пользователей
- **education.py** - Pydantic модели образования
- **academic.py** - Pydantic модели академических данных
- **base.py** - Базовые модели
- **invitation.py** - Модели системы инвайтов
- **schedule.py** - Модели расписания
- **system.py** - Системные модели

### 5. Schedule Layer (`app/schedule/`)
- **api_client.py** - Клиент для внешнего API
- **api.py** - API интерфейс
- **faculty_api_client.py** - Клиент API факультетов
- **group_search.py** - Поиск групп
- **semester_detector.py** - Определение семестра
- **models.py** - Модели расписания

### 6. Utils Layer (`app/utils/`)
- **logger.py** - Настройка логирования
- **validators.py** - Система валидации данных
- **validation.py** - Валидация пользовательского ввода
- **error_monitor.py** - Мониторинг ошибок
- **error_handling.py** - Обработка ошибок
- **type_guard.py** - Проверка типов
- **rate_limiter.py** - Ограничение частоты запросов
- **disclaimer.py** - Управление дисклеймерами
- **secrets_manager.py** - Управление секретами
- **secrets.py** - Секреты

## Принципы архитектуры

### 1. Разделение ответственности
- Каждый модуль отвечает за свою область
- Services не знают о bot layer
- Database layer изолирован от business logic

### 2. Обработка ошибок
- **Services** возвращают `None` при ошибках (не падают, но сигнализируют об ошибке)
- **Handlers** проверяют `None` и обрабатывают ошибки через middleware
- **Middleware** - единственное место где глотаются ошибки
- **async_error_handler** - декоратор для безопасного выполнения асинхронных функций
- **safe_execute_async** - функция для безопасного выполнения с обработкой ошибок

### 3. Типизация
- Строгая типизация всех функций
- Runtime проверка типов в критических местах
- Валидация входных данных
- Generic типизация в валидаторах
- Pydantic модели для структурированных данных
- SQLAlchemy модели с современным синтаксисом (Mapped)

### 4. Логирование
- Структурированное логирование через loguru
- Детальные traceback для всех ошибок
- Разные уровни логирования

## Потоки данных

### 1. Получение расписания
```
User -> Handler -> Service -> Database -> API
                <- Response <- Data <- Schedule
```

### 2. Выбор группы
```
User -> Handler -> GroupService -> Database
                <- GroupData <- Validation
```

### 3. Синхронизация данных
```
Scheduler -> APISyncService -> External API
          <- Processed Data <- Raw Data
```

## Обработка ошибок

### Уровни обработки
1. **Validation Layer** - Валидация входных данных
2. **Service Layer** - Возврат пустых значений при ошибках
3. **Handler Layer** - Middleware для обработки ошибок
4. **User Layer** - Понятные сообщения пользователю

### Мониторинг ошибок
- Отслеживание повторяющихся ошибок
- Черный список проблемных функций
- Детальная статистика

## Конфигурация

### Environment Variables
- `BOT_TOKEN` - Токен Telegram бота
- `DATABASE_URL` - URL базы данных
- `LOG_LEVEL` - Уровень логирования

### Database
- SQLite для разработки
- PostgreSQL для продакшена
- SQLAlchemy ORM

## Тестирование

### Unit Tests
- Тесты для каждого service
- Моки для внешних зависимостей
- Покрытие критических путей

### Integration Tests
- Тесты взаимодействия компонентов
- Тесты с реальной БД
- Тесты API интеграции

## Развертывание

### Development
```bash
uv run python -m app.bot.main
```

### Production
```bash
uv run python -m app.bot.main --env production
```

## Мониторинг

### Логи
- `logs/bot.log` - Основные логи
- `logs/errors.log` - Ошибки
- `logs/api_requests.log` - API запросы

### Метрики
- Количество пользователей
- Количество запросов
- Время отклика API
- Ошибки по типам

## Безопасность

### Секреты
- Все секреты в .env файле
- Никогда не логируются секреты
- Валидация токенов

### Валидация
- Проверка всех входных данных
- Санитизация пользовательского ввода
- Защита от SQL инъекций

## Расширение

### Добавление новых команд
1. Создать handler в `app/bot/handlers/`
2. Зарегистрировать в `register_handlers()`
3. Добавить клавиатуру в `keyboards.py`

### Добавление новых services
1. Создать service в `app/services/`
2. Добавить валидацию данных
3. Написать тесты

### Добавление новых API
1. Создать client в `app/schedule/`
2. Добавить в `api_sync_service.py`
3. Обновить модели данных
