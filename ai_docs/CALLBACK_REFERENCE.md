# Справочник Callback Data

## Обзор

Callback Data - это система для передачи данных через кнопки Telegram бота. Все callback'и наследуются от `CallbackData` и имеют уникальный префикс.

## Базовые Callback'и

### FilterCallback
```python
class FilterCallback(CallbackData, prefix="filter"):
    name: str
```
**Использование**: Фильтры поиска
**Пример**: `filter:name=course`

### OptionCallback
```python
class OptionCallback(CallbackData, prefix="option"):
    filter_name: str
    value: str
```
**Использование**: Опции фильтров
**Пример**: `option:filter_name=course&value=1`

### ResultCallback
```python
class ResultCallback(CallbackData, prefix="result"):
    index: int
```
**Использование**: Результаты поиска
**Пример**: `result:index=0`

### FormatCallback
```python
class FormatCallback(CallbackData, prefix="format"):
    result_index: int
    format_type: str
```
**Использование**: Форматы файлов
**Пример**: `format:result_index=0&format_type=xlsx`

## Меню и навигация

### MenuCallback
```python
class MenuCallback(CallbackData, prefix="menu"):
    action: str
```
**Использование**: Главное меню
**Примеры**:
- `menu:action=home`
- `menu:action=schedule`
- `menu:action=settings`

### ProfileCallback
```python
class ProfileCallback(CallbackData, prefix="profile"):
    action: str
    value: str = ""
```
**Использование**: Настройка профиля
**Примеры**:
- `profile:action=edit`
- `profile:action=change_group&value=123`

## Образовательные функции

### DiaryCallback
```python
class DiaryCallback(CallbackData, prefix="diary"):
    action: str
    item_id: str = ""
```
**Использование**: Дневник студента
**Примеры**:
- `diary:action=view`
- `diary:action=add_grade&item_id=123`

### ApplicationCallback
```python
class ApplicationCallback(CallbackData, prefix="app"):
    action: str
    data: str = ""
```
**Использование**: Заявления
**Примеры**:
- `app:action=create`
- `app:action=view&data=123`

### AttestationCallback
```python
class AttestationCallback(CallbackData, prefix="attest"):
    action: str
    topic: str = ""
```
**Использование**: Справочник аттестации
**Примеры**:
- `attest:action=search`
- `attest:action=view&topic=anatomy`

### GradeCallback
```python
class GradeCallback(CallbackData, prefix="grade"):
    action: str
    subject: str = ""
    data: str = ""
```
**Использование**: Управление оценками
**Примеры**:
- `grade:action=view`
- `grade:action=add&subject=anatomy`
- `grade:action=edit&subject=anatomy&data=123`

## Работа с группами

### GroupSearchCallback
```python
class GroupSearchCallback(CallbackData, prefix="group_search"):
    action: str
    value: str | None = None
    group_id: str | None = None
```
**Использование**: Поиск групп
**Примеры**:
- `group_search:action=search`
- `group_search:action=select&group_id=123`
- `group_search:action=filter&value=faculty`

### GroupSelectionCallback
```python
class GroupSelectionCallback(CallbackData, prefix="group_select"):
    action: str
    group_id: int = 0
    faculty: str = ""
```
**Использование**: Выбор группы
**Примеры**:
- `group_select:action=select&group_id=123&faculty=Лечебный`
- `group_select:action=back`

### GroupConfirmationCallback
```python
class GroupConfirmationCallback(CallbackData, prefix="group_confirm"):
    action: str
    group_id: int = 0
```
**Использование**: Подтверждение выбора группы
**Примеры**:
- `group_confirm:action=confirm&group_id=123`
- `group_confirm:action=cancel`

## Система инвайтов

### InvitationCallback
```python
class InvitationCallback(CallbackData, prefix="invitation"):
    action: str
    invitation_id: str = ""
```
**Использование**: Система инвайтов
**Примеры**:
- `invitation:action=create`
- `invitation:action=use&invitation_id=abc123`
- `invitation:action=view`

## Использование в коде

### Регистрация обработчиков

```python
from aiogram import Dispatcher
from app.bot.callbacks import MenuCallback, GroupSelectionCallback

async def register_handlers(dp: Dispatcher):
    # Обработчик меню
    dp.callback_query.register(
        handle_menu,
        MenuCallback.filter()
    )
    
    # Обработчик выбора группы
    dp.callback_query.register(
        handle_group_selection,
        GroupSelectionCallback.filter()
    )
```

### Обработка callback'ов

```python
from aiogram import types
from app.bot.callbacks import MenuCallback

async def handle_menu(
    callback: types.CallbackQuery, 
    callback_data: MenuCallback
) -> None:
    """Обработчик меню."""
    await callback.answer()
    
    action = callback_data.action
    
    if action == "home":
        await show_main_menu(callback.message)
    elif action == "schedule":
        await show_schedule(callback.message)
    elif action == "settings":
        await show_settings(callback.message)
```

### Создание кнопок

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.bot.callbacks import MenuCallback, GroupSelectionCallback

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру главного меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главная",
                    callback_data=MenuCallback(action="home").pack()
                ),
                InlineKeyboardButton(
                    text="📅 Расписание",
                    callback_data=MenuCallback(action="schedule").pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data=MenuCallback(action="settings").pack()
                )
            ]
        ]
    )

def get_group_selection_keyboard(groups: list[dict]) -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора группы."""
    buttons = []
    
    for group in groups:
        buttons.append([
            InlineKeyboardButton(
                text=f"Группа {group['name']}",
                callback_data=GroupSelectionCallback(
                    action="select",
                    group_id=group['id'],
                    faculty=group['faculty']
                ).pack()
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

## Лучшие практики

### 1. Именование действий
```python
# ✅ Хорошо - понятные действия
MenuCallback(action="home")
MenuCallback(action="schedule")
MenuCallback(action="settings")

# ❌ Плохо - неясные действия
MenuCallback(action="a")
MenuCallback(action="btn1")
MenuCallback(action="click")
```

### 2. Обработка данных
```python
async def handle_callback(callback: types.CallbackQuery, callback_data: MenuCallback):
    """Обработчик callback'а."""
    await callback.answer()
    
    # Валидация данных
    if not callback_data.action:
        logger.error("Empty action in callback")
        return
    
    # Обработка действия
    try:
        if callback_data.action == "home":
            await show_home(callback.message)
        elif callback_data.action == "schedule":
            await show_schedule(callback.message)
        else:
            logger.warning(f"Unknown action: {callback_data.action}")
            await callback.message.edit_text("❌ Неизвестное действие")
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await callback.message.edit_text("❌ Произошла ошибка")
```

### 3. Безопасность
```python
# Валидация callback данных
def validate_callback_data(callback_data: CallbackData) -> bool:
    """Валидировать данные callback'а."""
    if not callback_data.action:
        return False
    
    # Проверка на подозрительные символы
    suspicious_chars = ['<', '>', '"', "'", '&', ';']
    for char in suspicious_chars:
        if char in callback_data.action:
            return False
    
    return True
```

### 4. Логирование
```python
from app.utils.logger import log_user_action

async def handle_menu(callback: types.CallbackQuery, callback_data: MenuCallback):
    """Обработчик меню с логированием."""
    user_id = callback.from_user.id
    
    # Логирование действия
    log_user_action(
        user_id=user_id,
        action=f"menu_{callback_data.action}",
        details={"callback_data": callback_data.model_dump()}
    )
    
    # Обработка действия
    # ...
```

## Отладка

### Просмотр callback данных
```python
async def debug_callback(callback: types.CallbackQuery):
    """Отладочная функция для просмотра callback данных."""
    logger.info(f"Callback data: {callback.data}")
    logger.info(f"User: {callback.from_user.id}")
    logger.info(f"Message: {callback.message.message_id}")
```

### Тестирование callback'ов
```python
import pytest
from app.bot.callbacks import MenuCallback

def test_menu_callback():
    """Тест создания callback'а меню."""
    callback = MenuCallback(action="home")
    assert callback.action == "home"
    assert callback.pack() == "menu:action=home"

def test_group_selection_callback():
    """Тест создания callback'а выбора группы."""
    callback = GroupSelectionCallback(
        action="select",
        group_id=123,
        faculty="Лечебный"
    )
    assert callback.action == "select"
    assert callback.group_id == 123
    assert callback.faculty == "Лечебный"
```
