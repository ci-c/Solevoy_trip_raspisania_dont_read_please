import asyncio
import hashlib
import os
import sys

import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

# Настройки
API_TOKEN = os.getenv("BOT_API_KEY")
DB_NAME = 'db.db'

# Настройка логирования
logger.remove()  # Убираем стандартный обработчик
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/bot_errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="10 MB"
)

# Инициализация
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния FSM
class Form(StatesGroup):
    waiting_activation = State()
    selecting_filters = State()
    selecting_options = State()
    processing_search = State()
    selecting_result = State()
    generating_file = State()

# Декоратор для обработки ошибок в хэндлерах
def error_handler(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            # Пытаемся отправить сообщение об ошибке пользователю
            try:
                if len(args) > 0:
                    if hasattr(args[0], 'message'):
                        await args[0].message.answer("❌ Произошла ошибка. Попробуйте позже.")
                    elif hasattr(args[0], 'answer'):
                        await args[0].answer("❌ Произошла ошибка. Попробуйте позже.")
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
    return wrapper

# Заглушки для данных (замени на реальные запросы)
async def get_available_filters():
    """Получить доступные фильтры (замени на реальный запрос)"""
    try:
        logger.info("Getting available filters...")
        await asyncio.sleep(2)  # Имитация долгого запроса
        return {
            "Курс": ["1", "2", "3", "4"],
            "Группа": ["А", "Б", "В", "Г"],
            "Предмет": ["Математика", "Физика", "Программирование"]
        }
    except Exception as e:
        logger.error(f"Error in get_available_filters: {e}")
        raise

async def perform_search(selected_filters):
    """Выполнить поиск (замени на реальный запрос)"""
    try:
        logger.info(f"Performing search with filters: {selected_filters}")
        await asyncio.sleep(3)  # Имитация долгого поиска
        # Здесь должна быть реальная логика поиска
        results = []
        for i in range(1, 6):
            results.append(f"Вариант {i}: {selected_filters}")
        return results
    except Exception as e:
        logger.error(f"Error in perform_search: {e}")
        raise

async def generate_file(selected_option):
    """Сгенерировать файл (замени на реальную логику)"""
    try:
        logger.info(f"Generating file for: {selected_option}")
        await asyncio.sleep(5)  # Имитация долгой генерации
        filename = f"files/{hashlib.md5(selected_option.encode()).hexdigest()}.txt"
        os.makedirs("files", exist_ok=True)
        
        # Если файл уже существует, не пересоздаем
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Данные для: {selected_option}")
        
        return filename
    except Exception as e:
        logger.error(f"Error in generate_file: {e}")
        raise

@dp.message(Command("start"))
@error_handler
async def cmd_start(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started bot")
    await state.set_state(Form.waiting_activation)
    await message.answer(
        "Бот активирован. Нажмите кнопку ниже чтобы начать выбор.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать выбор", callback_data="start_selection")]
        ])
    )

@dp.callback_query(F.data == "start_selection")
@error_handler
async def start_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    logger.info(f"User {callback.from_user.id} started selection")
    await state.set_state(Form.selecting_filters)
    
    try:
        # Получаем доступные фильтры (долгая операция)
        await callback.message.edit_text("⏳ Загружаю доступные параметры...")
        available_filters = await get_available_filters()
        
        # Сохраняем фильтры в состоянии
        await state.update_data(available_filters=available_filters, selected_filters={})
        
        # Показываем фильтры для выбора
        builder = InlineKeyboardBuilder()
        for filter_name in available_filters.keys():
            builder.add(InlineKeyboardButton(
                text=f"{filter_name} ➡️", 
                callback_data=f"select_filter:{filter_name}"
            ))
        
        builder.add(InlineKeyboardButton(text="✅ Поиск", callback_data="start_search"))
        builder.adjust(1)
        
        await callback.message.edit_text(
            "Выберите параметры для фильтрации:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in start_selection: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки параметров. Попробуйте позже.")
        await state.set_state(Form.waiting_activation)

@dp.callback_query(F.data.startswith("select_filter:"))
@error_handler
async def select_filter(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    filter_name = callback.data.split(":")[1]
    logger.info(f"User {callback.from_user.id} selected filter: {filter_name}")
    
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        available_filters = data["available_filters"]
        
        # Создаем клавиатуру для выбора значений фильтра
        builder = InlineKeyboardBuilder()
        for value in available_filters[filter_name]:
            builder.add(InlineKeyboardButton(
                text=value, 
                callback_data=f"filter_value:{filter_name}:{value}"
            ))
        
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_filters"))
        builder.adjust(2)
        
        await state.set_state(Form.selecting_options)
        await callback.message.edit_text(
            f"Выберите значения для {filter_name}:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in select_filter: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки значений фильтра. Попробуйте позже.")
        await state.set_state(Form.selecting_filters)

@dp.callback_query(F.data.startswith("filter_value:"))
@error_handler
async def select_filter_value(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    _, filter_name, value = callback.data.split(":", 2)
    logger.info(f"User {callback.from_user.id} selected value: {filter_name}={value}")
    
    try:
        # Обновляем выбранные фильтры
        data = await state.get_data()
        selected_filters = data.get("selected_filters", {})
        
        if filter_name not in selected_filters:
            selected_filters[filter_name] = []
        
        if value in selected_filters[filter_name]:
            selected_filters[filter_name].remove(value)
        else:
            selected_filters[filter_name].append(value)
        
        await state.update_data(selected_filters=selected_filters)
        
        # Обновляем сообщение
        available_filters = data["available_filters"]
        builder = InlineKeyboardBuilder()
        
        for val in available_filters[filter_name]:
            is_selected = val in selected_filters.get(filter_name, [])
            builder.add(InlineKeyboardButton(
                text=f"{'✅ ' if is_selected else ''}{val}", 
                callback_data=f"filter_value:{filter_name}:{val}"
            ))
        
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_filters"))
        builder.adjust(2)
        
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f"Error in select_filter_value: {e}")
        await callback.message.edit_text("❌ Ошибка обновления фильтра. Попробуйте позже.")

@dp.callback_query(F.data == "back_to_filters")
@error_handler
async def back_to_filters(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    logger.info(f"User {callback.from_user.id} went back to filters")
    
    try:
        await state.set_state(Form.selecting_filters)
        
        data = await state.get_data()
        available_filters = data["available_filters"]
        selected_filters = data.get("selected_filters", {})
        
        # Показываем фильтры для выбора
        builder = InlineKeyboardBuilder()
        for filter_name in available_filters.keys():
            selected_count = len(selected_filters.get(filter_name, []))
            builder.add(InlineKeyboardButton(
                text=f"{filter_name} {'✅' if selected_count > 0 else ''} ({selected_count})", 
                callback_data=f"select_filter:{filter_name}"
            ))
        
        builder.add(InlineKeyboardButton(text="✅ Поиск", callback_data="start_search"))
        builder.adjust(1)
        
        await callback.message.edit_text(
            "Выберите параметры для фильтрации:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in back_to_filters: {e}")
        await callback.message.edit_text("❌ Ошибка возврата к фильтрам. Попробуйте позже.")
        await state.set_state(Form.waiting_activation)

@dp.callback_query(F.data == "start_search")
@error_handler
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    logger.info(f"User {callback.from_user.id} started search")
    
    try:
        await state.set_state(Form.processing_search)
        
        # Получаем выбранные фильтры
        data = await state.get_data()
        selected_filters = data.get("selected_filters", {})
        
        # Выполняем поиск (долгая операция)
        await callback.message.edit_text("⏳ Выполняю поиск...")
        search_results = await perform_search(selected_filters)
        
        # Сохраняем результаты в состоянии
        await state.update_data(search_results=search_results)
        
        # Показываем результаты поиска
        if not search_results:
            await callback.message.edit_text("❌ Ничего не найдено. Попробуйте другие параметры.")
            await state.set_state(Form.waiting_activation)
            return
        
        builder = InlineKeyboardBuilder()
        for i, result in enumerate(search_results):
            builder.add(InlineKeyboardButton(
                text=result, 
                callback_data=f"select_result:{i}"
            ))
        
        builder.adjust(1)
        
        await state.set_state(Form.selecting_result)
        await callback.message.edit_text(
            "Найдены следующие варианты:",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in start_search: {e}")
        await callback.message.edit_text("❌ Ошибка поиска. Попробуйте позже.")
        await state.set_state(Form.waiting_activation)

@dp.callback_query(F.data.startswith("select_result:"))
@error_handler
async def select_result(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    result_index = int(callback.data.split(":")[1])
    logger.info(f"User {callback.from_user.id} selected result: {result_index}")
    
    try:
        await state.set_state(Form.generating_file)
        
        # Получаем выбранный результат
        data = await state.get_data()
        search_results = data["search_results"]
        selected_option = search_results[result_index]
        
        # Генерируем файл (долгая операция)
        await callback.message.edit_text("⏳ Генерирую файл...")
        filename = await generate_file(selected_option)
        
        # Отправляем файл
        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"Ваш файл для: {selected_option}"
        )
        
        # Возвращаемся в состояние ожидания
        await state.set_state(Form.waiting_activation)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Новый поиск", callback_data="start_selection")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in select_result: {e}")
        await callback.message.edit_text("❌ Ошибка генерации файла. Попробуйте позже.")
        await state.set_state(Form.waiting_activation)

# Обработчик всех ошибок
@dp.error()
async def error_handler(event, exception):
    logger.error(f"Global error handler caught: {exception}")

async def main():
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    # Создаем папки для логов и файлов
    os.makedirs("logs", exist_ok=True)
    os.makedirs("files", exist_ok=True)
    
    # Запускаем бота
    asyncio.run(main())