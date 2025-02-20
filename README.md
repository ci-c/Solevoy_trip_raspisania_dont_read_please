# Schedule Processor 🗓️

Проект для автоматической конвертации CSV/XLSX-файлов с расписанием занятий в удобные форматы: календарь (ICS) и таблицы Excel.

## Особенности ✨

- Конвертация CSV/XLSX в iCalendar (ICS) и Excel (XLSX)
- Поддержка разных типов занятий (лекции/семинары)
- Автоматическое определение временных интервалов
- Генерация расписания с учётом учебных недель

## Установка ⚙️

1. Клонируйте репозиторий
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

## Использование 🚀

1. Поместите исходные файлы в папку `input/`
   - Примеры имён файлов:
     - Лекции: `Л_1_МПФ_АБ.csv`
     - Семинары: `С_1_МПФ_АБ_102.csv`
   - Формат имён: `[Тип]_[Номер]_[Факультет]_[Группа].расширение`

2. Запустите скрипт:

```bash
python script.py
```

1. Результаты будут сохранены в папке `output/`:
   - `.ics` файлы для импорта в календарь
   - `.xlsx` файлы с табличным расписанием

## Структура проекта 📂

```plaintext
.
├── Drafts/            - Черновики и предыдущие версии скриптов
├── input/             - Входные файлы (CSV/XLSX)
├── output/            - Сгенерированные файлы расписаний
├── README.md          - Этот файл
└── script.py          - Основной скрипт обработки
```

## Конфигурация ⚙️

Основные настройки в коде:

```python
FIRST_DATE = datetime.date(2025, 2, 3)  # Дата начала семестра
ADD_BREAKS = False                      # Добавление перерывов в календарь
ADD_MARK = True                         # Добавление ссылки на телеграм-канал
RINGS = { ... }                         # Настройки временных интервалов
```

## Пример входных данных 📄

Файл `Л_1_МПФ_АБ.csv`:

```csv
пн,9:00,1-5,Математика
вт,13:10,2-8,Физика
```

## Зависимости 📦

- Python 3.10+
- ics==0.7.2
- openpyxl==3.1.2
- python-dateutil==2.8.2
- rich==13.7.0
- zoneinfo==2023.3

## TODO

- [ ] Расписания экзаменов (втч пересдач)
- [ ] Расписания отработок
- [ ] Расписания для 4+ курсов
- [ ] Темы занятий
- [ ] Кафедры
- [ ] Павильоны
- [ ] Предподователи
- [ ] Номера занятий
- [ ] Бассейн для фп
- [ ] Цвета в календаре

## Лицензия 📄

MIT License. Подробности в файле LICENSE.

---
Для связи: [Telegram канал](https://t.me/mechnews_1k) 📢

---
