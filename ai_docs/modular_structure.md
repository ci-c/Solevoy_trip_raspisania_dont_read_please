# Модульная структура проекта

## Обновленная архитектура (2025-01-09)

### Основные модули

#### `schedule_processor/` - Основной пакет
```
schedule_processor/
├── __init__.py                 # Инициализация пакета
├── yaml_config.py             # Загрузка YAML конфигурации ✅
├── models.py                  # Базовые модели данных (Lesson, ProcessedLesson) 
├── api.py                     # API клиент СЗГМУ
├── core.py                    # Основная логика обработки
├── generator.py               # Генераторы Excel/iCal
├── file_processor.py          # Обработка файлов (совместимость v1)
├── student_profile.py         # Профили студентов ✅
├── diary.py                   # Студенческий дневник ✅  
└── applications.py            # Генерация заявлений СЗГМУ ✅
```

#### Точки входа
```
├── cli.py                     # CLI интерфейс (click) ✅
├── bot_main.py               # Telegram бот
├── main_api.py               # API обработка  
└── run.py                    # Unified runner
```

#### Конфигурация и данные
```  
├── config.yaml               # Основная конфигурация ✅
├── pyproject.toml            # Метаданные проекта
├── requirements.txt          # Зависимости
└── uv.lock                   # Lock файл uv
```

### Устаревшие файлы (перенесены в legacy/)
```
legacy/
├── script.py                 # v1 основной скрипт
├── sw.py                     # v1 утилиты бассейна  
├── main.py                   # Старый main
├── test_bot.py              # Устаревшие тесты
└── v3/                      # Рабочая API версия (перенесена)
    ├── main.py
    ├── config.py
    ├── get_raw.py
    ├── processing.py
    ├── xlsx.py
    ├── ical.py  
    └── ...другие модули
```

**Примечание:** v2 была удалена пользователем как неактуальная.

## Новые возможности модулей

### 1. Профили студентов (`student_profile.py`)
- **Класс `StudentProfile`** - полная информация о студенте
- **Класс `StudentProfileManager`** - управление профилями
- Сохранение в JSON файлах
- Валидация заполненности профиля

### 2. Студенческий дневник (`diary.py`)
- **Класс `Grade`** - оценки с типизацией
- **Класс `Homework`** - домашние задания
- **Класс `Absence`** - пропуски с отработками
- **Класс `StudentDiary`** - основной менеджер дневника
- Статистика по предметам
- Уведомления о дедлайнах

### 3. Система заявлений (`applications.py`)
- **Класс `AbsenceRequest`** - запрос на заявление
- **Класс `ApplicationGenerator`** - генератор документов СЗГМУ
- Автоматическая генерация заявлений по дисциплинам
- Объяснительные записки в дирекцию
- Соответствие регламенту СЗГМУ

### 4. YAML конфигурация (`yaml_config.py`)
- **Класс `ConfigLoader`** - загрузчик конфигурации
- Обратная совместимость с Python константами
- Типизированные методы получения настроек
- Валидация конфигурации

### 5. CLI интерфейс (`cli.py`)
- Команды: `config-test`, `filters`, `search`, `generate`, `bot`, `info`
- Rich форматирование вывода
- Async поддержка
- Интеграция с существующим API

## Интеграция модулей

### Telegram бот → Модули
```python
# bot_main.py будет использовать:
from schedule_processor.student_profile import StudentProfileManager
from schedule_processor.diary import StudentDiary
from schedule_processor.applications import ApplicationGenerator
from schedule_processor.yaml_config import get_config
```

### CLI → Модули  
```python
# cli.py уже интегрирован с:
from schedule_processor.yaml_config import get_config
from schedule_processor.api import get_available_filters, search_schedules
```

### Конфигурация → Все модули
```python
# Везде используется:
from schedule_processor.yaml_config import get_config
config = get_config()
```

## Следующие этапы

### Приоритет A (требует пользователя)
1. Конвертация .doc документов для понимания КНЛ/КНС
2. Анализ положения о текущем контроле успеваемости

### Приоритет B (AI развитие)  
1. Интеграция новых модулей в bot_main.py
2. Реализация системы заявлений в боте
3. Добавление типизации во все модули

### Приоритет C (дополнительно)
1. Тестирование модулей  
2. Интеграция расписания экзаменов
3. SDO Moodle интеграция

Модульная структура готова к дальнейшей разработке согласно UX описанию и требованиям СЗГМУ.