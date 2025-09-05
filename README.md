# Schedule Processor 🗓️ | Процессор Расписания

**English** | [Русский](#русская-версия)

A comprehensive system for processing university schedules with support for:
- Converting CSV/XLSX files to iCalendar (ICS) and Excel formats
- API-based schedule fetching from university systems  
- Interactive Telegram bot interface
- Multiple lesson types support (lectures/seminars)

## Features ✨

- **Multiple Input Sources**: Process local CSV/XLSX files or fetch from API
- **Format Conversion**: Generate both Excel (.xlsx) and iCalendar (.ics) files
- **Telegram Bot**: Interactive bot for easy schedule access
- **Smart Processing**: Automatic time interval detection and week calculation
- **Flexible Configuration**: Support for different universities and schedule formats

## Quick Start 🚀

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

### Installation with uv

```bash
# Clone the repository
git clone <your-repo-url>
cd schedule-processor

# Create virtual environment and install dependencies
uv sync

# For development dependencies
uv sync --dev
```

### Installation with pip

```bash
# Clone and setup
git clone <your-repo-url>
cd schedule-processor
pip install -e .

# For development
pip install -e .[dev]
```

## Usage 🔧

### Unified Runner (Recommended)

```bash
# Using uv
uv run schedule-run <mode>

# Using pip installation  
schedule-run <mode>

# Direct script execution
python run.py <mode>
```

Available modes:
- `api` - API-based schedule processing
- `bot` - Telegram bot interface  
- `legacy` - File-based processing (v1)
- `test` - Test API functions

### Individual Components

#### 1. API-based Processing

```bash
# Using uv
uv run schedule-processor

# Using pip installation  
schedule-processor

# Direct script execution
python main_api.py
```

#### 2. Telegram Bot

First, create a `.env` file:
```env
BOT_API_KEY=your_telegram_bot_token_here
```

Then run:
```bash
# Using uv
uv run schedule-bot

# Using pip installation
schedule-bot  

# Direct script execution
python bot_main.py
```

#### 3. File-based Processing (Legacy v1)

```bash
python script.py
```

#### 4. Testing

```bash
# Test API functions
python run.py test
# or
python test_bot.py
```

Place your CSV/XLSX files in the `input/` directory with naming format:
- Lectures: `Л_1_МПФ_АБ.csv` 
- Seminars: `С_1_МПФ_АБ_102.csv`

## Project Structure 📂

```
schedule-processor/
├── schedule_processor/        # Main package
│   ├── __init__.py
│   ├── api.py                # API client for external services
│   ├── config.py             # Configuration constants
│   ├── core.py               # Core processing logic
│   ├── file_processor.py     # CSV/XLSX file processing
│   ├── generator.py          # Excel/iCal generation
│   └── models.py             # Data models
├── bot_main.py               # Telegram bot entry point
├── main_api.py               # API processing entry point  
├── script.py                 # Legacy file processor
├── pyproject.toml            # Project configuration
├── README.md                 # This file
└── .env.example              # Environment variables template
```

## Configuration ⚙️

Key settings in `schedule_processor/config.py`:

```python
# Time slots for different lesson types
RINGS = {
    "л": [  # Lectures
        ((time(9, 0), time(9, 45)), (time(9, 50), time(10, 35))),
        # ...
    ],
    "с": [  # Seminars  
        ((time(9, 0), time(10, 30)), (time(10, 45), time(12, 15))),
        # ...
    ]
}

# Week days mapping
WEEK_DAYS = {"пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6}
```

## Development 🛠️

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality Tools

```bash
# Format code
uv run black .
uv run isort .

# Lint
uv run flake8
uv run mypy schedule_processor/

# Run tests  
uv run pytest
```

### uv Commands Reference

```bash
# Install dependencies
uv sync

# Add new dependency
uv add requests

# Add development dependency  
uv add --dev pytest

# Run script in virtual environment
uv run python script.py

# Run specific command
uv run schedule-processor

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Show dependency tree
uv pip list
```

## API Integration 🔗

The system integrates with university schedule APIs. Configure endpoints in `schedule_processor/api.py`:

```python
# Example API configuration
API_BASE_URL = "https://example-university.edu/api"
SCHEDULE_ENDPOINT = "/schedule/find"
```

## Dependencies 📦

### Core Dependencies
- `aiogram>=3.0.0` - Telegram bot framework
- `ics>=0.7.2` - iCalendar file generation
- `openpyxl>=3.1.2` - Excel file manipulation
- `requests>=2.31.0` - HTTP client for API calls
- `python-dateutil>=2.8.2` - Date/time utilities
- `rich>=13.7.0` - Rich console output
- `loguru>=0.7.0` - Advanced logging

### Development Dependencies
- `pytest>=8.3.4` - Testing framework
- `black>=25.1.0` - Code formatter
- `mypy>=1.14.0` - Type checker
- `pre-commit>=4.0.1` - Git hooks

## Contributing 🤝

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run quality checks: `uv run black . && uv run pytest`
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature-name`
7. Create a Pull Request

## Documentation 📚

### For Users
- **[README.md](README.md)** - Quick start guide and basic usage
- **[.env.example](.env.example)** - Environment configuration template

### For Developers  
- **[ai_docs/ARCHITECTURE.md](ai_docs/ARCHITECTURE.md)** - Detailed architecture overview and version evolution
- **[ai_docs/TECHNICAL.md](ai_docs/TECHNICAL.md)** - Deep technical documentation with code examples
- **[ai_docs/ANALYSIS.md](ai_docs/ANALYSIS.md)** - Comparative analysis of all project versions
- **[ai_docs/modular_structure.md](ai_docs/modular_structure.md)** - Current modular architecture

### Testing
- **[legacy/test_bot.py](legacy/test_bot.py)** - Legacy API function testing
- **[run.py](run.py)** - Unified runner with test mode

## License 📄

MIT License - see LICENSE file for details.

---

# Русская версия 🇷🇺

Комплексная система для обработки университетских расписаний с поддержкой:
- Конвертации CSV/XLSX файлов в iCalendar (ICS) и Excel форматы
- Получения расписаний через API университетских систем
- Интерактивного Telegram-бота
- Различных типов занятий (лекции/семинары)

## Возможности ✨

- **Множественные источники**: Обработка локальных файлов или получение через API
- **Конвертация форматов**: Генерация Excel (.xlsx) и iCalendar (.ics) файлов
- **Telegram-бот**: Интерактивный бот для удобного доступа к расписанию
- **Умная обработка**: Автоматическое определение временных интервалов и расчет недель
- **Гибкая настройка**: Поддержка разных университетов и форматов расписаний

## Быстрый старт 🚀

### Требования

- Python 3.10+
- Пакетный менеджер [uv](https://docs.astral.sh/uv/) (рекомендуется)

### Установка с uv

```bash
# Клонировать репозиторий
git clone <your-repo-url>
cd schedule-processor

# Создать виртуальное окружение и установить зависимости
uv sync

# Для зависимостей разработки
uv sync --dev
```

### Установка с pip

```bash
# Клонировать и настроить
git clone <your-repo-url>
cd schedule-processor
pip install -e .

# Для разработки
pip install -e .[dev]
```

## Использование 🔧

### Единый запуск (рекомендуется)

```bash
# Используя uv
uv run schedule-run <режим>

# Используя pip
schedule-run <режим>

# Прямой запуск скрипта
python run.py <режим>
```

Доступные режимы:
- `api` - Обработка через API
- `bot` - Telegram-бот интерфейс
- `legacy` - Обработка файлов (v1)  
- `test` - Тестирование API функций

### Отдельные компоненты

#### 1. Обработка через API

```bash
# Используя uv
uv run schedule-processor

# Используя pip
schedule-processor

# Прямой запуск скрипта
python main_api.py
```

#### 2. Telegram-бот

Сначала создайте файл `.env`:
```env
BOT_API_KEY=your_telegram_bot_token_here
```

Затем запустите:
```bash
# Используя uv
uv run schedule-bot

# Используя pip
schedule-bot  

# Прямой запуск скрипта
python bot_main.py
```

#### 3. Обработка файлов (Legacy v1)

```bash
python script.py
```

#### 4. Тестирование

```bash
# Тестирование API функций
python run.py test
# или
python test_bot.py
```

Поместите CSV/XLSX файлы в директорию `input/` с форматом именования:
- Лекции: `Л_1_МПФ_АБ.csv` 
- Семинары: `С_1_МПФ_АБ_102.csv`

## Структура проекта 📂

```
schedule-processor/
├── schedule_processor/        # Основной пакет
│   ├── __init__.py
│   ├── api.py                # API клиент для внешних сервисов
│   ├── config.py             # Константы конфигурации
│   ├── core.py               # Основная логика обработки
│   ├── file_processor.py     # Обработка CSV/XLSX файлов
│   ├── generator.py          # Генерация Excel/iCal
│   └── models.py             # Модели данных
├── bot_main.py               # Точка входа Telegram-бота
├── main_api.py               # Точка входа API обработки  
├── script.py                 # Legacy обработчик файлов
├── pyproject.toml            # Конфигурация проекта
├── README.md                 # Этот файл
└── .env.example              # Шаблон переменных окружения
```

## Справочник команд uv 🔧

```bash
# Установить зависимости
uv sync

# Добавить новую зависимость
uv add requests

# Добавить зависимость для разработки  
uv add --dev pytest

# Запустить скрипт в виртуальном окружении
uv run python script.py

# Запустить конкретную команду
uv run schedule-processor

# Активировать виртуальное окружение
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Показать дерево зависимостей
uv pip list
```

## Разработка 🛠️

### Настройка среды разработки

```bash
# Установка с зависимостями разработки
uv sync --dev

# Установка pre-commit хуков
uv run pre-commit install
```

### Инструменты качества кода

```bash
# Форматирование кода
uv run black .
uv run isort .

# Линтинг
uv run flake8
uv run mypy schedule_processor/

# Запуск тестов  
uv run pytest
```

## Документация 📚

### Для пользователей
- **[README.md](README.md)** - Руководство по быстрому старту и основное использование
- **[.env.example](.env.example)** - Шаблон конфигурации окружения

### Для разработчиков
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Подробный обзор архитектуры и эволюции версий  
- **[TECHNICAL.md](TECHNICAL.md)** - Глубокая техническая документация с примерами кода
- **[ANALYSIS.md](ANALYSIS.md)** - Сравнительный анализ всех версий проекта

### Тестирование
- **[test_bot.py](test_bot.py)** - Тестирование API функций
- **[run.py](run.py)** - Единый запускатель с режимом тестирования

## Лицензия 📄

MIT License - подробности в файле LICENSE.

---

Для связи: [Telegram канал](https://t.me/mechnews_1k) 📢
