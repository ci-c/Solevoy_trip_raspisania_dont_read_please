# Implementation Plan: SZGMU Schedule Bot Baseline

**Branch**: `001-szgmu-bot-baseline` | **Date**: 2025-10-10 | **Spec**: `specs/001-szgmu-bot-baseline/spec.md`
**Input**: Feature specification from `/specs/001-szgmu-bot-baseline/spec.md`

**Note**: Generated manually по обновлённому шаблону; поддерживайте актуальность при переходе между фазами.

## Summary

Реализуем минимальный набор возможностей Telegram-бота: просмотр расписания (P1), экспорт (P2) и профиль с уведомлениями (P3). Все сценарии используют единую каноническую БД и сервисы `app/services/`, чтобы соблюсти Принцип I и избежать расхождений между ботом, экспортами и уведомлениями.

## Technical Context

**Language/Version**: Python 3.10+ managed with `uv`  
**Primary Dependencies**: aiogram 3.x, SQLAlchemy 2.0, Pydantic, Loguru, async HTTP client (`httpx` предпочтительно; уточнить в FR-010)  
**Storage**: SQLite (`data/szgmu_bot.db`) через модели и сессии в `app/database/`  
**Testing**: `pytest` (asyncio-mode=auto) с маркерами `unit`, `integration`, `slow`, `database`, `external`; фикстуры в `tests/fixtures/`  
**Target Platform**: Telegram-бот, развёрнутый на Linux-контейнере/VM со службой фоновых задач  
**Project Type**: Асинхронный бот + сервисный слой  
**Performance Goals**: Ответ `/schedule` < 3 с для кэшированных групп; генерация экспорта ≤ 5 с; уведомления доставляются в заданное окно  
**Constraints**: Без блокирующего I/O в хендлерах; канонические данные только в БД; секреты — из `.env`; логирование структурированное  
**Scale/Scope**: Студенты СЗГМУ (десятки тысяч запросов в день) с сезонными пиками обновлений расписания

## Constitution Check

*GATE: пройти перед завершением фазы 0 и перепроверить перед реализацией.*

- [ ] **Принцип I — Канонические данные расписания**: Подготовить миграции/сидеры под нужные сценарии; убедиться, что все новые функции используют `app/services/schedule.py` и не читают файлы напрямую.
- [ ] **Принцип II — Асинхронная оркестрация Telegram**: Уточнить, какие новые хендлеры/планировщики появятся, и доказать, что они вызывают только асинхронные сервисы.
- [ ] **Принцип III — Ценность для студента**: Пересмотреть копирайтинг и flow, убедиться, что профили и локализация покрывают весь маршрут; зафиксировать требования в спеце/тестах.
- [ ] **Принцип IV — Тесты до кода**: Составить список тестов из спецификации, создать заглушки, добиться красного статуса перед реализацией.
- [ ] **Принцип V — Прозрачность и отказоустойчивость**: Спланировать логирование, таймауты, ретраи и алерты, включая проверку Loguru-конфигурации.

Любые отклонения — в таблицу Complexity Tracking до начала фазы 1.

## Project Structure

### Documentation (this feature)

```
specs/001-szgmu-bot-baseline/
├── spec.md
├── plan.md           # этот файл
├── research.md       # заполнить на фазе 0
├── data-model.md     # заполнить на фазе 1
├── quickstart.md     # подготовить для передачи команды
└── tasks.md          # появится после /speckit.tasks
```

### Source Code (repository root)

```
app/
├── bot/
│   ├── handlers/
│   ├── keyboards.py
│   ├── states.py
│   └── main.py
├── services/
├── schedule/
├── database/
│   ├── models.py
│   └── session.py
└── utils/

tests/
├── unit/
├── integration/
└── fixtures/

data/
└── szgmu_bot.db
```

**Structure Decision**: Работа затрагивает `app/bot/handlers/` (новые команды/меню), `app/services/` (расписание, экспорт, профиль, уведомления), `app/schedule/` (ингест и экспорт), `app/database/models.py` (возможные изменения схемы), а также соответствующие тесты (`tests/unit`, `tests/integration`). Прямой доступ к БД из хендлеров исключается — только через сервисы, что соответствует Принципам I и II.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |

Если возникнут отклонения (например, временная работа с `aiohttp` без подтверждения), зафиксировать причину и план возврата здесь и продублировать в `tasks.md`.
