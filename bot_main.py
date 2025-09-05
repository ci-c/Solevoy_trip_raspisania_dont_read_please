"""
Enhanced Telegram bot with real schedule processing integration.
Uses the schedule_processor package for actual data processing.
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

from schedule_processor.api import get_available_filters, search_schedules

# --- 1. Configuration ---
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
API_TOKEN: Optional[str] = os.getenv("BOT_API_KEY")
if not API_TOKEN:
    logger.critical("Need to specify BOT_API_KEY in .env file. Exiting.")
    sys.exit(1)

FILES_DIR = BASE_DIR / "files"
LOGS_DIR = BASE_DIR / "logs"

# --- 2. Logging setup ---
logger.remove()
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
logger.add(
    LOGS_DIR / "bot_errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="10 MB",
    compression="zip",
)

# --- 3. Aiogram initialization ---
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# --- 4. FSM States ---
class SearchForm(StatesGroup):
    waiting_activation = State()
    selecting_filters = State()
    selecting_options = State()
    processing_search = State()
    selecting_result = State()
    selecting_format = State()
    generating_file = State()


# --- 5. CallbackData Factories ---
class FilterCallback(CallbackData, prefix="filter"):
    name: str


class OptionCallback(CallbackData, prefix="option"):
    filter_name: str
    value: str


class ResultCallback(CallbackData, prefix="result"):
    index: int


class FormatCallback(CallbackData, prefix="format"):
    result_index: int
    format_type: str  # "xlsx" or "ics"


# --- 6. Keyboard utilities ---
def get_filters_keyboard(
    available_filters: Dict[str, List[str]],
    selected_filters: Dict[str, List[str]],
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in available_filters.keys():
        selected_count = len(selected_filters.get(name, []))
        button_text = f"{name} ({selected_count}) {'✅' if selected_count > 0 else '➡️'}"
        builder.button(
            text=button_text,
            callback_data=FilterCallback(name=name),
        )
    builder.button(text="✅ Начать поиск", callback_data="start_search")
    builder.adjust(1)
    return builder.as_markup()


def get_options_keyboard(
    filter_name: str,
    options: List[str],
    selected_options: List[str],
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in options:
        is_selected = option in selected_options
        button_text = f"{'✅ ' if is_selected else ''}{option}"
        builder.button(
            text=button_text,
            callback_data=OptionCallback(filter_name=filter_name, value=option),
        )
    builder.button(text="⬅️ Назад к фильтрам", callback_data="back_to_filters")
    builder.adjust(2)
    return builder.as_markup()


# --- 7. File generation function ---
async def generate_schedule_file(search_result: Dict, format_type: str, subgroup_name: str) -> Path:
    """
    Generate schedule file using the real schedule processor.
    
    Args:
        search_result: Selected search result with schedule data
        format_type: "xlsx" or "ics"
        subgroup_name: Name of the subgroup to filter lessons
        
    Returns:
        Path to generated file
    """
    logger.info(f"Generating {format_type} file for subgroup: {subgroup_name}")
    
    # Create temporary output directory
    temp_dir = FILES_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract schedule info for processing
    schedule_data = search_result['data']
    
    # Process using v3 logic (working version)
    try:
        import sys
        from pathlib import Path
        
        # Add legacy/v3 to path temporarily
        v3_path = Path(__file__).parent / "legacy" / "v3"
        sys.path.insert(0, str(v3_path))
        
        from get_raw import process_lessons
        from processing import process_lessons_for_export
        from xlsx import gen_excel_file
        from ical import gen_ical
        from config import WEEK_DAYS
        import datetime
        
        # Process lessons from the schedule data
        all_lessons = process_lessons(schedule_data)
        
        if not all_lessons:
            raise Exception("No lessons found in schedule data")
        
        # Determine first schedule date (same logic as v3/main.py)
        earliest_lesson = min(all_lessons, key=lambda x: (int(x.weekNumber), WEEK_DAYS.get(x.dayName, 999)))
        first_day_index = WEEK_DAYS.get(earliest_lesson.dayName, 0)
        
        semestr_num: int = 0 if earliest_lesson.semester == "осенний" else 1
        year: int = int(earliest_lesson.academicYear.split("/")[semestr_num])
        month: int = [9, 2][semestr_num]
        first_monday_of_semestr: datetime.date = datetime.date(year, month, 1)
        while first_monday_of_semestr.weekday() != first_day_index:
            first_monday_of_semestr += datetime.timedelta(days=1)

        
        # Process lessons for export using v3 logic
        processed_lessons = process_lessons_for_export(all_lessons, subgroup_name, first_monday_of_semestr)
        
        if not processed_lessons:
            raise Exception(f"No lessons found for subgroup {subgroup_name}")
        
        # Ensure output directory exists
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate requested file format using v3 generators
        if format_type == "xlsx":
            gen_excel_file(processed_lessons, subgroup_name)
            file_path = output_dir / f"{subgroup_name}.xlsx"
        else:  # ics
            gen_ical(processed_lessons, subgroup_name)
            file_path = output_dir / f"{subgroup_name}.ics"
        
        # Remove v3 from path
        sys.path.remove(str(v3_path))
        
        if file_path.exists():
            logger.info(f"Successfully generated {format_type} file: {file_path}")
            return file_path
        else:
            raise Exception(f"Generated file {file_path} does not exist")
            
    except Exception as e:
        logger.error(f"Error generating schedule file: {e}")
        
        # Fallback: create a simple text file with error info
        file_hash = hashlib.md5(f"{search_result['display_name']}_{subgroup_name}".encode()).hexdigest()
        fallback_file = temp_dir / f"error_{file_hash}.txt"
        
        with open(fallback_file, "w", encoding="utf-8") as f:
            f.write(f"Error generating {format_type} file\n")
            f.write(f"Schedule: {search_result['display_name']}\n")
            f.write(f"Subgroup: {subgroup_name}\n")
            f.write(f"Error: {str(e)}\n")
            f.write("Generated by Schedule Processor Bot\n")
        
        return fallback_file


def format_schedule_info(schedule_data: Dict) -> str:
    """
    Format schedule data into readable description for bot buttons.
    
    Args:
        schedule_data: Raw schedule data from API
        
    Returns:
        Formatted string with schedule characteristics
    """
    data = schedule_data.get('data', {})
    
    # Extract key information
    file_name = data.get('fileName', 'Unknown')
    
    # Try to extract info from lessons
    lessons = data.get('scheduleLessonDtoList', [])
    if lessons:
        first_lesson = lessons[0]
        speciality = first_lesson.get('speciality', 'Unknown')
        course_number = first_lesson.get('courseNumber', 'Unknown') 
        semester = first_lesson.get('semester', 'Unknown')
        academic_year = first_lesson.get('academicYear', 'Unknown')
        group_stream = first_lesson.get('groupStream', 'Unknown')
        lesson_type = first_lesson.get('lessonType', 'Unknown')
        
        # Get unique subgroups
        subgroups = set()
        for lesson in lessons[:10]:  # Check first 10 lessons
            if lesson.get('subgroup'):
                subgroups.add(lesson.get('subgroup'))
        
        subgroups_str = ", ".join(sorted(subgroups)) if subgroups else "Unknown"
        
        return (f"{speciality}\n"
                f"Курс: {course_number}, Поток: {group_stream}\n" 
                f"Семестр: {semester} {academic_year}\n"
                f"Подгруппы: {subgroups_str}\n"
                f"Тип: {lesson_type}")
    
    return f"Файл: {file_name}"


# --- 8. Handlers ---

@dp.message(Command("start", "help"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    logger.info(f"User {message.from_user.id} started the bot.")
    await state.clear()
    await state.set_state(SearchForm.waiting_activation)
    keyboard = InlineKeyboardBuilder().button(
        text="Начать выбор", callback_data="start_selection"
    )
    await message.answer(
        "Привет! Я помогу тебе найти и выгрузить расписание занятий.\n"
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=keyboard.as_markup(),
    )


@dp.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    logger.info(f"User {message.from_user.id} cancelled action.")
    await state.clear()
    await message.answer("Действие отменено. Чтобы начать заново, введите /start")


@dp.callback_query(
    F.data == "start_selection", StateFilter(SearchForm.waiting_activation)
)
async def start_selection(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    logger.info(f"User {callback.from_user.id} started selection.")

    await callback.message.edit_text("⏳ Загружаю доступные параметры...")
    available_filters = await get_available_filters()

    await state.update_data(available_filters=available_filters, selected_filters={})
    await state.set_state(SearchForm.selecting_filters)

    keyboard = get_filters_keyboard(available_filters, {})
    await callback.message.edit_text(
        "Выберите параметры для фильтрации:", reply_markup=keyboard
    )


@dp.callback_query(FilterCallback.filter(), StateFilter(SearchForm.selecting_filters))
async def select_filter_category(
    callback: types.CallbackQuery, callback_data: FilterCallback, state: FSMContext
) -> None:
    await callback.answer()
    filter_name = callback_data.name
    logger.info(f"User {callback.from_user.id} selected filter: {filter_name}")

    data = await state.get_data()
    available_options = data["available_filters"][filter_name]
    selected_options = data["selected_filters"].get(filter_name, [])

    keyboard = get_options_keyboard(filter_name, available_options, selected_options)
    await state.set_state(SearchForm.selecting_options)
    await callback.message.edit_text(
        f"Выберите значения для <b>{filter_name}</b>:", reply_markup=keyboard
    )


@dp.callback_query(OptionCallback.filter(), StateFilter(SearchForm.selecting_options))
async def select_filter_value(
    callback: types.CallbackQuery, callback_data: OptionCallback, state: FSMContext
) -> None:
    await callback.answer()
    filter_name = callback_data.filter_name
    value = callback_data.value
    user_id = callback.from_user.id
    logger.info(f"User {user_id} selected value: {filter_name}={value}")

    data = await state.get_data()
    selected_filters = data["selected_filters"]

    if filter_name not in selected_filters:
        selected_filters[filter_name] = []

    if value in selected_filters[filter_name]:
        selected_filters[filter_name].remove(value)
    else:
        selected_filters[filter_name].append(value)

    await state.update_data(selected_filters=selected_filters)

    data = await state.get_data()
    available_options = data["available_filters"][filter_name]
    selected_options = data["selected_filters"].get(filter_name, [])
    keyboard = get_options_keyboard(filter_name, available_options, selected_options)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(
    F.data == "back_to_filters", StateFilter(SearchForm.selecting_options)
)
async def back_to_filters(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    logger.info(f"User {callback.from_user.id} returned to filters.")
    await state.set_state(SearchForm.selecting_filters)

    data = await state.get_data()
    keyboard = get_filters_keyboard(data["available_filters"], data["selected_filters"])
    await callback.message.edit_text(
        "Выберите параметры для фильтрации:", reply_markup=keyboard
    )


@dp.callback_query(F.data == "start_search", StateFilter(SearchForm.selecting_filters))
async def start_search(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    logger.info(f"User {callback.from_user.id} started search.")
    await state.set_state(SearchForm.processing_search)

    data = await state.get_data()
    selected_filters = data.get("selected_filters", {})

    if not any(selected_filters.values()):
        await callback.message.edit_text(
            "⚠️ Вы не выбрали ни одного параметра. Поиск отменен."
        )
        keyboard = get_filters_keyboard(data["available_filters"], selected_filters)
        await state.set_state(SearchForm.selecting_filters)
        await callback.message.answer(
            "Выберите параметры для фильтрации:", reply_markup=keyboard
        )
        return

    await callback.message.edit_text("⏳ Выполняю поиск...")
    search_results = await search_schedules(selected_filters)
    await state.update_data(search_results=search_results)

    if not search_results:
        await callback.message.edit_text(
            "❌ Ничего не найдено. Попробуйте изменить параметры."
        )
        keyboard = get_filters_keyboard(data["available_filters"], selected_filters)
        await state.set_state(SearchForm.selecting_filters)
        await callback.message.answer(
            "Выберите параметры для фильтрации:", reply_markup=keyboard
        )
        return

    builder = InlineKeyboardBuilder()
    for i, result in enumerate(search_results):
        # Use formatted info instead of filename
        formatted_info = format_schedule_info(result)
        # Truncate if too long for button
        button_text = formatted_info.replace('\n', ' | ')
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."
        builder.button(text=button_text, callback_data=ResultCallback(index=i))

    builder.adjust(1)
    await state.set_state(SearchForm.selecting_result)
    await callback.message.edit_text(
        "Найдены следующие варианты расписаний:", reply_markup=builder.as_markup()
    )


@dp.callback_query(ResultCallback.filter(), StateFilter(SearchForm.selecting_result))
async def select_result(
    callback: types.CallbackQuery, callback_data: ResultCallback, state: FSMContext
) -> None:
    await callback.answer()
    result_index = callback_data.index
    logger.info(f"User {callback.from_user.id} selected result: {result_index}")
    
    data = await state.get_data()
    selected_result = data["search_results"][result_index]
    
    # Store selected result for later use
    await state.update_data(selected_result_index=result_index)
    
    # Show detailed info and ask for subgroup + format
    schedule_info = format_schedule_info(selected_result)
    
    # Extract available subgroups from the schedule
    schedule_data = selected_result.get('data', {})
    lessons = schedule_data.get('scheduleLessonDtoList', [])
    subgroups = set()
    for lesson in lessons:
        if lesson.get('subgroup'):
            subgroups.add(lesson.get('subgroup'))
    
    subgroups_list = sorted(subgroups)
    
    if not subgroups_list:
        await callback.message.edit_text(
            f"❌ В выбранном расписании не найдено подгрупп.\n\n"
            f"Информация о расписании:\n{schedule_info}"
        )
        return
    
    # Create subgroup selection keyboard
    builder = InlineKeyboardBuilder()
    for subgroup in subgroups_list:
        builder.button(
            text=f"📚 {subgroup}", 
            callback_data=f"subgroup_{result_index}_{subgroup}"
        )
    builder.button(text="⬅️ Назад к результатам", callback_data="back_to_results")
    builder.adjust(2)
    
    await state.set_state(SearchForm.selecting_format)
    await callback.message.edit_text(
        f"📋 <b>Выбранное расписание:</b>\n{schedule_info}\n\n"
        f"Выберите подгруппу для генерации файла:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("subgroup_"), StateFilter(SearchForm.selecting_format))
async def select_subgroup(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    # Parse callback data: "subgroup_{result_index}_{subgroup_name}"
    _, result_index_str, subgroup_name = callback.data.split("_", 2)
    result_index = int(result_index_str)
    
    logger.info(f"User {callback.from_user.id} selected subgroup: {subgroup_name}")
    
    # Store subgroup selection
    await state.update_data(selected_subgroup=subgroup_name)
    
    # Show format selection
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📊 Excel (.xlsx)", 
        callback_data=FormatCallback(result_index=result_index, format_type="xlsx")
    )
    builder.button(
        text="📅 Календарь (.ics)", 
        callback_data=FormatCallback(result_index=result_index, format_type="ics")
    )
    builder.button(text="⬅️ Назад к подгруппам", callback_data=f"back_to_subgroups_{result_index}")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"📚 <b>Подгруппа:</b> {subgroup_name}\n\n"
        f"Выберите формат файла:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("back_to_subgroups_"), StateFilter(SearchForm.selecting_format))
async def back_to_subgroups(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    result_index = int(callback.data.split("_")[-1])
    
    # Re-trigger result selection to show subgroup menu
    fake_callback_data = ResultCallback(index=result_index)
    await select_result(callback, fake_callback_data, state)


@dp.callback_query(F.data == "back_to_results", StateFilter(SearchForm.selecting_format))
async def back_to_results_from_subgroups(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    # Go back to results selection
    data = await state.get_data()
    search_results = data.get("search_results", [])
    
    builder = InlineKeyboardBuilder()
    for i, result in enumerate(search_results):
        formatted_info = format_schedule_info(result)
        button_text = formatted_info.replace('\n', ' | ')
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."
        builder.button(text=button_text, callback_data=ResultCallback(index=i))

    builder.adjust(1)
    await state.set_state(SearchForm.selecting_result)
    await callback.message.edit_text(
        "Найдены следующие варианты расписаний:", reply_markup=builder.as_markup()
    )


@dp.callback_query(FormatCallback.filter(), StateFilter(SearchForm.selecting_format))
async def select_format(
    callback: types.CallbackQuery, callback_data: FormatCallback, state: FSMContext
) -> None:
    await callback.answer()
    result_index = callback_data.result_index
    format_type = callback_data.format_type
    
    logger.info(f"User {callback.from_user.id} selected format: {format_type}")
    
    await state.set_state(SearchForm.generating_file)

    data = await state.get_data()
    selected_result = data["search_results"][result_index]
    subgroup_name = data["selected_subgroup"]

    format_name = "Excel" if format_type == "xlsx" else "Календарь"
    await callback.message.edit_text(f"⏳ Генерирую {format_name} файл для подгруппы {subgroup_name}...")
    
    try:
        file_path = await generate_schedule_file(selected_result, format_type, subgroup_name)

        # Send file to user
        document = FSInputFile(file_path)
        file_description = f"{format_name} файл для подгруппы {subgroup_name}"
        await callback.message.answer_document(
            document, caption=f"📎 {file_description}"
        )

        # Return to initial state
        await state.set_state(SearchForm.waiting_activation)
        keyboard = InlineKeyboardBuilder().button(
            text="🔍 Новый поиск", callback_data="start_selection"
        )
        await callback.message.answer(
            "✅ Файл успешно отправлен! Хотите начать новый поиск?",
            reply_markup=keyboard.as_markup(),
        )
    except Exception as e:
        logger.error(f"Error in file generation: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при генерации файла: {str(e)}\n\n"
            f"Попробуйте еще раз или выберите другой формат."
        )
        # Return to format selection
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📊 Excel (.xlsx)", 
            callback_data=FormatCallback(result_index=result_index, format_type="xlsx")
        )
        builder.button(
            text="📅 Календарь (.ics)", 
            callback_data=FormatCallback(result_index=result_index, format_type="ics")
        )
        builder.adjust(2)
        
        await callback.message.answer(
            f"Выберите формат файла для подгруппы {subgroup_name}:",
            reply_markup=builder.as_markup()
        )


# --- 9. Error handler ---
@dp.error(StateFilter("*"))
async def global_error_handler(
    event: types.ErrorEvent, state: FSMContext
) -> Coroutine[Any, Any, None]:
    exception_info = f"Exception: {event.exception.__class__.__name__}: {event.exception}"
    logger.error(f"Global error!\n{exception_info}")

    target_chat_id = None
    if event.update.message:
        target_chat_id = event.update.message.chat.id
    elif event.update.callback_query and event.update.callback_query.message:
        target_chat_id = event.update.callback_query.message.chat.id

    if target_chat_id:
        try:
            await bot.send_message(
                chat_id=target_chat_id,
                text="❌ Произошла непредвиденная ошибка. Попробуйте снова.\n"
                "Вы можете перезапустить бота командой /start",
            )
        except Exception as e:
            logger.error(f"Could not send error message to user {target_chat_id}: {e}")

    await state.clear()


# --- 10. Main function ---
async def main() -> None:
    """Main async function for bot startup."""
    FILES_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical error starting bot: {e}")
    finally:
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())