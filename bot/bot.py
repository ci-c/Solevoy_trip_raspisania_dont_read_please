"""
Основной файл для Telegram-бота с использованием aiogram 3.x.
Бот представляет собой конечный автомат (FSM) для пошагового
выбора фильтров, выполнения поиска по ним и генерации файла по результату.
"""

import asyncio
import hashlib
import os
import sys
from pathlib import Path
from typing import Any, Coroutine, Dict, List, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from loguru import logger

# --- 1. Конфигурация ---
# Загрузка переменных окружения из .env файла
load_dotenv()

# Абсолютный путь к корневой директории проекта
BASE_DIR = Path(__file__).resolve().parent

# Токен Telegram бота
API_TOKEN: Optional[str] = os.getenv("BOT_API_KEY")
if not API_TOKEN:
    logger.critical("Необходимо указать BOT_API_KEY в .env файле. Выход.")
    sys.exit(1)

# Директории для хранения файлов и логов
FILES_DIR = BASE_DIR / "files"
LOGS_DIR = BASE_DIR / "logs"

# --- 2. Настройка логирования ---
# Удаляем стандартный обработчик и настраиваем свои
logger.remove()
# Логирование в stdout с красивым форматированием для отладки
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
)
# Логирование ошибок в файл с ротацией
logger.add(
    LOGS_DIR / "bot_errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="10 MB",  # Новый файл после достижения 10 МБ
    compression="zip",  # Сжатие старых лог-файлов
)

# --- 3. Инициализация Aiogram ---
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# --- 4. Состояния FSM (Finite State Machine) ---
class SearchForm(StatesGroup):
    """
    Класс состояний для процесса поиска.
    Определяет шаги, через которые проходит пользователь.
    """

    waiting_activation = State()  # Начальное состояние после /start
    selecting_filters = State()  # Выбор категории фильтра (Курс, Группа)
    selecting_options = State()  # Выбор значений для фильтра (1, 2, А, Б)
    processing_search = State()  # Ожидание результатов поиска
    selecting_result = State()  # Выбор одного из найденных результатов
    generating_file = State()  # Ожидание генерации файла


# --- 5. CallbackData Factories ---
# Фабрики для создания и парсинга callback_data в кнопках.
# Это безопасный и типизированный способ вместо "сырых" строк.


class FilterCallback(CallbackData, prefix="filter"):
    """Callback для выбора категории фильтра."""

    name: str  # Имя фильтра, например, "Курс"


class OptionCallback(CallbackData, prefix="option"):
    """Callback для выбора конкретного значения фильтра."""

    filter_name: str
    value: str


class ResultCallback(CallbackData, prefix="result"):
    """Callback для выбора результата поиска."""

    index: int


# --- 6. Утилиты для создания клавиатур ---
def get_filters_keyboard(
    available_filters: Dict[str, List[str]],
    selected_filters: Dict[str, List[str]],
) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора категорий фильтров.
    Показывает, сколько опций выбрано в каждой категории.
    """
    builder = InlineKeyboardBuilder()
    for name in available_filters.keys():
        selected_count = len(selected_filters.get(name, []))
        button_text = f"{name} ({selected_count}) {'✅' if selected_count > 0 else '➡️'}"
        builder.button(
            text=button_text,
            callback_data=FilterCallback(name=name),
        )
    builder.button(text="✅ Начать поиск", callback_data="start_search")
    builder.adjust(1)  # Все кнопки в один столбец
    return builder.as_markup()


def get_options_keyboard(
    filter_name: str,
    options: List[str],
    selected_options: List[str],
) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора значений внутри одной категории фильтров.
    Отмечает уже выбранные опции.
    """
    builder = InlineKeyboardBuilder()
    for option in options:
        is_selected = option in selected_options
        button_text = f"{'✅ ' if is_selected else ''}{option}"
        builder.button(
            text=button_text,
            callback_data=OptionCallback(filter_name=filter_name, value=option),
        )
    builder.button(text="⬅️ Назад к фильтрам", callback_data="back_to_filters")
    builder.adjust(2)  # Кнопки в два столбца
    return builder.as_markup()


# --- 7. "Сервисный" слой (заглушки для бизнес-логики) ---
# В реальном проекте эти функции могут делать запросы к API, базе данных и т.д.


async def get_available_filters() -> Dict[str, List[str]]:
    """
    Асинхронно получает доступные фильтры и их значения.
    Имитирует сетевой запрос.
    """
    logger.info("Получение доступных фильтров...")
    await asyncio.sleep(1.5)  # Имитация долгой операции
    return {
        "Курс": ["1", "2", "3", "4"],
        "Группа": ["101", "102", "103", "104", "105"],
        "Предмет": ["Анатомия", "Гистология", "Биохимия", "Философия"],
    }


async def perform_search(selected_filters: Dict[str, List[str]]) -> List[str]:
    """
    Асинхронно выполняет поиск по заданным фильтрам.
    Имитирует долгий поиск.
    """
    logger.info(f"Выполнение поиска с фильтрами: {selected_filters}")
    await asyncio.sleep(2)
    if not any(selected_filters.values()):
        return []
    # Имитация результатов
    return [f"Результат №{i} для {selected_filters}" for i in range(1, 6)]


async def generate_file(selected_option: str) -> Path:
    """
    Асинхронно генерирует файл на основе выбранной опции.
    Имитирует долгую генерацию.
    """
    logger.info(f"Генерация файла для: {selected_option}")
    await asyncio.sleep(3)
    # Создаем имя файла на основе хеша, чтобы избежать дублирования
    # и проблем с недопустимыми символами в имени.
    file_hash = hashlib.md5(selected_option.encode()).hexdigest()
    filename = FILES_DIR / f"{file_hash}.txt"

    # Создаем файл, только если он не существует
    if not filename.exists():
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Это сгенерированный файл для опции: {selected_option}")
    return filename


# --- 8. Хэндлеры ---


# --- Команды ---
@dp.message(Command("start", "help"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Обработчик команд /start и /help.
    Сбрасывает состояние и предлагает начать работу.
    """
    logger.info(f"Пользователь {message.from_user.id} запустил бота.")
    await state.clear()
    await state.set_state(SearchForm.waiting_activation)
    keyboard = InlineKeyboardBuilder().button(
        text="Начать выбор", callback_data="start_selection"
    )
    await message.answer(
        "Привет! Я помогу тебе найти и выгрузить нужные данные.\n"
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=keyboard.as_markup(),
    )


@dp.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /cancel.
    Позволяет пользователю сбросить текущее состояние и начать заново.
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    logger.info(f"Пользователь {message.from_user.id} отменил действие.")
    await state.clear()
    await message.answer("Действие отменено. Чтобы начать заново, введите /start")


# --- Шаг 1: Начало выбора фильтров ---
@dp.callback_query(
    F.data == "start_selection", StateFilter(SearchForm.waiting_activation)
)
async def start_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает нажатие кнопки "Начать выбор".
    Загружает фильтры и показывает их пользователю.
    """
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} начал выбор.")

    await callback.message.edit_text("⏳ Загружаю доступные параметры...")
    available_filters = await get_available_filters()

    # Сохраняем фильтры и инициализируем пустой словарь для выбранных
    await state.update_data(available_filters=available_filters, selected_filters={})
    await state.set_state(SearchForm.selecting_filters)

    keyboard = get_filters_keyboard(available_filters, {})
    await callback.message.edit_text(
        "Выберите параметры для фильтрации:", reply_markup=keyboard
    )


# --- Шаг 2: Выбор категории фильтра ---
@dp.callback_query(FilterCallback.filter(), StateFilter(SearchForm.selecting_filters))
async def select_filter_category(
    callback: types.CallbackQuery, callback_data: FilterCallback, state: FSMContext
) -> None:
    """
    Обрабатывает выбор категории фильтра (e.g., "Курс").
    Показывает доступные значения для этой категории.
    """
    await callback.answer()
    filter_name = callback_data.name
    logger.info(f"Пользователь {callback.from_user.id} выбрал фильтр: {filter_name}")

    data = await state.get_data()
    available_options = data["available_filters"][filter_name]
    selected_options = data["selected_filters"].get(filter_name, [])

    keyboard = get_options_keyboard(filter_name, available_options, selected_options)
    await state.set_state(SearchForm.selecting_options)
    await callback.message.edit_text(
        f"Выберите значения для <b>{filter_name}</b>:", reply_markup=keyboard
    )


# --- Шаг 3: Выбор значения фильтра (мультивыбор) ---
@dp.callback_query(OptionCallback.filter(), StateFilter(SearchForm.selecting_options))
async def select_filter_value(
    callback: types.CallbackQuery, callback_data: OptionCallback, state: FSMContext
) -> None:
    """
    Обрабатывает выбор конкретного значения (e.g., "1 курс").
    Поддерживает множественный выбор (toggle).
    """
    await callback.answer()
    filter_name = callback_data.filter_name
    value = callback_data.value
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} выбрал значение: {filter_name}={value}")

    data = await state.get_data()
    selected_filters = data["selected_filters"]

    # Логика "тумблера": добавляем значение, если его нет, или удаляем, если есть
    if filter_name not in selected_filters:
        selected_filters[filter_name] = []

    if value in selected_filters[filter_name]:
        selected_filters[filter_name].remove(value)
    else:
        selected_filters[filter_name].append(value)

    await state.update_data(selected_filters=selected_filters)

    # Обновляем клавиатуру, чтобы показать/скрыть галочку
    data = await state.get_data()
    available_options = data["available_filters"][filter_name]
    selected_options = data["selected_filters"].get(filter_name, [])
    keyboard = get_options_keyboard(filter_name, available_options, selected_options)

    # Используем edit_reply_markup для более плавной работы без "моргания" сообщения
    await callback.message.edit_reply_markup(reply_markup=keyboard)


# --- Шаг 4: Возврат к списку фильтров ---
@dp.callback_query(
    F.data == "back_to_filters", StateFilter(SearchForm.selecting_options)
)
async def back_to_filters(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Возвращает пользователя из выбора значений к выбору категорий фильтров.
    """
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} вернулся к фильтрам.")
    await state.set_state(SearchForm.selecting_filters)

    data = await state.get_data()
    keyboard = get_filters_keyboard(data["available_filters"], data["selected_filters"])
    await callback.message.edit_text(
        "Выберите параметры для фильтрации:", reply_markup=keyboard
    )


# --- Шаг 5: Запуск поиска ---
@dp.callback_query(F.data == "start_search", StateFilter(SearchForm.selecting_filters))
async def start_search(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Запускает процесс поиска по выбранным фильтрам.
    """
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} запустил поиск.")
    await state.set_state(SearchForm.processing_search)

    data = await state.get_data()
    selected_filters = data.get("selected_filters", {})

    # Проверяем, выбран ли хотя бы один фильтр
    if not any(selected_filters.values()):
        await callback.message.edit_text(
            "⚠️ Вы не выбрали ни одного параметра. Поиск отменен."
        )
        # Возвращаем на шаг выбора фильтров
        keyboard = get_filters_keyboard(data["available_filters"], selected_filters)
        await state.set_state(SearchForm.selecting_filters)
        await callback.message.answer(
            "Выберите параметры для фильтрации:", reply_markup=keyboard
        )
        return

    await callback.message.edit_text("⏳ Выполняю поиск...")
    search_results = await perform_search(selected_filters)
    await state.update_data(search_results=search_results)

    if not search_results:
        await callback.message.edit_text(
            "❌ Ничего не найдено. Попробуйте изменить параметры."
        )
        # Возвращаем на шаг выбора фильтров
        keyboard = get_filters_keyboard(data["available_filters"], selected_filters)
        await state.set_state(SearchForm.selecting_filters)
        await callback.message.answer(
            "Выберите параметры для фильтрации:", reply_markup=keyboard
        )
        return

    builder = InlineKeyboardBuilder()
    for i, result in enumerate(search_results):
        builder.button(text=result, callback_data=ResultCallback(index=i))

    builder.adjust(1)
    await state.set_state(SearchForm.selecting_result)
    await callback.message.edit_text(
        "Найдены следующие варианты:", reply_markup=builder.as_markup()
    )


# --- Шаг 6: Выбор результата и генерация файла ---
@dp.callback_query(ResultCallback.filter(), StateFilter(SearchForm.selecting_result))
async def select_result(
    callback: types.CallbackQuery, callback_data: ResultCallback, state: FSMContext
) -> None:
    """
    Обрабатывает выбор конкретного результата поиска и запускает генерацию файла.
    """
    await callback.answer()
    result_index = callback_data.index
    logger.info(
        f"Пользователь {callback.from_user.id} выбрал результат: {result_index}"
    )
    await state.set_state(SearchForm.generating_file)

    data = await state.get_data()
    selected_option = data["search_results"][result_index]

    await callback.message.edit_text("⏳ Генерирую файл...")
    file_path = await generate_file(selected_option)

    # Отправляем файл пользователю
    document = FSInputFile(file_path)
    await callback.message.answer_document(
        document, caption=f"Ваш файл для: {selected_option}"
    )

    # Возвращаемся в начальное состояние и предлагаем новый поиск
    await state.set_state(SearchForm.waiting_activation)
    keyboard = InlineKeyboardBuilder().button(
        text="Новый поиск", callback_data="start_selection"
    )
    await callback.message.edit_text(
        "Файл успешно отправлен. Хотите начать новый поиск?",
        reply_markup=keyboard.as_markup(),
    )


# --- 9. Глобальный обработчик ошибок ---
@dp.error(StateFilter("*"))
async def global_error_handler(
    event: types.ErrorEvent, state: FSMContext
) -> Coroutine[Any, Any, None]:
    """
    Ловит все исключения, которые не были обработаны в хэндлерах.
    Логирует ошибку и сообщает пользователю.
    """
    exception_info = (
        f"Exception: {event.exception.__class__.__name__}: {event.exception}"
    )
    update_info = f"Update: {event.update.model_dump_json(indent=2, exclude_none=True)}"
    logger.error(f"Глобальная ошибка!\n{exception_info}\n{update_info}")

    # Пытаемся уведомить пользователя
    # event.update.message или event.update.callback_query может быть None
    target_chat_id = None
    if event.update.message:
        target_chat_id = event.update.message.chat.id
    elif event.update.callback_query and event.update.callback_query.message:
        target_chat_id = event.update.callback_query.message.chat.id

    if target_chat_id:
        try:
            await bot.send_message(
                chat_id=target_chat_id,
                text="❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте снова позже.\n"
                "Вы можете сбросить бота командой /start",
            )
        except Exception as e:
            logger.error(
                f"Не удалось отправить сообщение об ошибке пользователю {target_chat_id}: {e}"
            )

    # Сбрасываем состояние пользователя, чтобы он мог начать заново
    await state.clear()


# --- 10. Основная функция запуска ---
async def main() -> None:
    """
    Главная асинхронная функция для запуска бота.
    """
    # Создаем директории, если они не существуют
    FILES_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())
