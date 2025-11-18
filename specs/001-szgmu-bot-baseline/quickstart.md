# Quickstart: SZGMU Schedule Bot Baseline

**Purpose**: Быстро провести разработчика через запуск окружения, выполнение тестов и проверку основных сценариев базовой функциональности.

## 1. Установка окружения

```bash
# Клонировать репозиторий и перейти в директорию (предполагается Python 3.14 установлен)
uv python pin 3.14
uv sync --dev
cp .env.example .env
# Заполнить .env (BOT_TOKEN, DATABASE_URL, LOG_LEVEL, QUIET_HOURS_DEFAULT и т.д.)
```

## 2. Подготовка данных

```bash
# Инициализировать каноническую БД с учебными данными
uv run python init_database_data.py --seed sample
# Проверить наличие групп и расписания
uv run python create_groups_now.py --list
```

## 3. Запуск бота

```bash
uv run szgmu-bot
# или fallback
uv run python main.py
```

Проверить, что бот поднимается без ошибок, и отправить `/schedule` тестовой группе.

## 4. Тестирование

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -m "unit"
uv run pytest -m "integration"
```

При необходимости запускать smoke-тесты `uv run pytest test_bot_commands.py`.

## 5. Проверка ключевых сценариев вручную

1. `/schedule` для группы с данными — расписание отображается корректно.
2. Команда экспорта — отправляются `.xlsx` и `.ics` файлы.
3. Настройка профиля — пользователь задаёт формат экспорта и тихие часы.
4. Планировщик уведомлений (см. логи) — напоминания не отправляются в тихие часы.

## 6. Мониторинг и диагностика

- Логи: `tail -f logs/bot.log`, `tail -f logs/errors.log`
- Проверка импортов расписания: смотреть таблицу `schedule_import_jobs` и логи `ScheduleImportJob`.
- Отладка уведомлений: таблица `notification_jobs`, логи воркера.

## 7. Полезные команды

```bash
# Перегенерировать фикстуры для тестов
uv run python tests/fixtures/generate_schedule_fixture.py

# Прогнать планировщик вручную
uv run python app/schedule/manual_import.py --source official

# Экспортировать расписание в консоль (для проверки без Telegram)
uv run python app/schedule/export_cli.py --group CODE --format excel
```

## 8. Частые проблемы

- **Нет данных в БД**: убедитесь, что запускался `init_database_data.py`; пересоздайте БД.
- **Ошибки таймаута**: проверьте доступ к официальному сайту; включите резервный API; проверьте конфигурацию таймаутов `httpx`.
- **Ночные уведомления**: проверьте настройки тихих часов в `UserProfile` и таймзону пользователя.

## 9. Следующие шаги

- Заполнить `tasks.md` по спецификации и плану.
- Уточнить политику очистки данных для `ExportRequest` и `NotificationJob`.
- Реализовать мониторинг доступности официального источника расписаний.
