"""
Enhanced Telegram bot with student profile and diary integration.
Implements full UX design with personalized academic assistant functionality.
"""

import asyncio
import hashlib
import os
import sys
from collections.abc import Coroutine
from pathlib import Path
from typing import Any

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
from schedule_processor.attestation_helper import AttestationHelper
from schedule_processor.diary import StudentDiary
from schedule_processor.disclaimer import DisclaimerManager
from schedule_processor.grade_calculator import GradeCalculator
from schedule_processor.group_search import GroupSearchService
from schedule_processor.semester_detector import SemesterDetector
from schedule_processor.student_profile import StudentProfile, StudentProfileManager
from schedule_processor.yaml_config import get_config

# --- 1. Configuration ---
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
API_TOKEN: str | None = os.getenv("BOT_API_KEY")
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
class ProfileSetup(StatesGroup):
    waiting_name = State()
    selecting_speciality = State()
    selecting_course = State()
    selecting_stream = State()
    selecting_group = State()
    confirmation = State()


class MainMenu(StatesGroup):
    home = State()
    schedule_view = State()
    diary_view = State()
    applications = State()
    reminders = State()
    settings = State()


class SearchForm(StatesGroup):
    waiting_activation = State()
    selecting_filters = State()
    selecting_options = State()
    processing_search = State()
    selecting_result = State()
    selecting_format = State()
    generating_file = State()


class DiaryStates(StatesGroup):
    main_view = State()
    adding_grade = State()
    adding_homework = State()
    adding_absence = State()
    viewing_stats = State()


class ApplicationStates(StatesGroup):
    selecting_dates = State()
    selecting_reason = State()
    generating_docs = State()


class AttestationStates(StatesGroup):
    main_view = State()
    asking_question = State()
    viewing_info = State()


class GradeStates(StatesGroup):
    main_view = State()
    selecting_subject = State()
    viewing_subject = State()
    adding_grade = State()
    adding_attendance = State()
    entering_grade_data = State()
    entering_attendance_data = State()


class GroupSearchStates(StatesGroup):
    choosing_search_type = State()
    entering_group_number = State()
    selecting_speciality = State()
    selecting_course = State()
    viewing_results = State()
    viewing_schedule = State()


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


class MenuCallback(CallbackData, prefix="menu"):
    action: str


class ProfileCallback(CallbackData, prefix="profile"):
    action: str
    value: str = ""


class DiaryCallback(CallbackData, prefix="diary"):
    action: str
    item_id: str = ""


class ApplicationCallback(CallbackData, prefix="app"):
    action: str
    data: str = ""


class AttestationCallback(CallbackData, prefix="attest"):
    action: str
    topic: str = ""


class GradeCallback(CallbackData, prefix="grade"):
    action: str
    subject: str = ""
    data: str = ""


class GroupSearchCallback(CallbackData, prefix="group"):
    action: str
    group_number: str = ""
    week: str = "current"


# --- 6. Keyboard utilities ---
def get_filters_keyboard(
    available_filters: dict[str, list[str]],
    selected_filters: dict[str, list[str]],
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in available_filters:
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
    options: list[str],
    selected_options: list[str],
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        is_selected = option in selected_options
        button_text = f"{'✅ ' if is_selected else ''}{option}"

        # Для длинных строк используем индекс вместо полного значения
        callback_value = str(i) if len(option.encode()) > 40 else option
        builder.button(
            text=button_text,
            callback_data=OptionCallback(filter_name=filter_name, value=callback_value),
        )
    builder.button(text="⬅️ Назад к фильтрам", callback_data="back_to_filters")
    builder.adjust(2)
    return builder.as_markup()


def get_main_menu_keyboard(
    user_profile: StudentProfile | None = None,
) -> types.InlineKeyboardMarkup:
    """Create main menu keyboard based on user profile status."""
    config = get_config()
    emojis = config.get("bot", {}).get("emojis", {})

    builder = InlineKeyboardBuilder()

    if user_profile:
        # Personalized menu
        builder.button(
            text=f"{emojis.get('schedule', '📅')} Мое расписание",
            callback_data=MenuCallback(action="my_schedule"),
        )
        builder.button(
            text="👥 Найти группу", callback_data=MenuCallback(action="search_group")
        )
        builder.button(
            text=f"{emojis.get('document', '📝')} Заявления",
            callback_data=MenuCallback(action="applications"),
        )
        builder.button(
            text=f"{emojis.get('grades', '📊')} Мой дневник",
            callback_data=MenuCallback(action="diary"),
        )
        builder.button(
            text="📚 Аттестация", callback_data=MenuCallback(action="attestation")
        )
        builder.button(
            text="🔢 Мои ОСБ/КНЛ/КНС", callback_data=MenuCallback(action="grades")
        )
        builder.button(
            text="🔔 Напоминания", callback_data=MenuCallback(action="reminders")
        )
        builder.button(
            text=f"{emojis.get('settings', '⚙️')} Настройки",
            callback_data=MenuCallback(action="settings"),
        )
        builder.button(
            text=f"{emojis.get('search', '🔍')} Поиск (старый)",
            callback_data=MenuCallback(action="search"),
        )
        builder.adjust(2)
    else:
        # New user menu
        builder.button(
            text="🎓 Настроить профиль",
            callback_data=MenuCallback(action="setup_profile"),
        )
        builder.button(
            text="🔍 Разовый поиск расписания",
            callback_data=MenuCallback(action="search"),
        )
        builder.adjust(1)

    return builder.as_markup()


def get_profile_setup_keyboard(
    step: str, options: list[str] | None = None
) -> types.InlineKeyboardMarkup:
    """Create keyboard for profile setup steps."""
    builder = InlineKeyboardBuilder()

    if options:
        for option in options:
            builder.button(
                text=option, callback_data=ProfileCallback(action=step, value=option)
            )
        builder.adjust(2)

    return builder.as_markup()


def get_diary_keyboard() -> types.InlineKeyboardMarkup:
    """Create diary main menu keyboard."""
    config = get_config()
    emojis = config.get("bot", {}).get("emojis", {})

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"{emojis.get('homework', '📝')} ДЗ и задания",
        callback_data=DiaryCallback(action="homework"),
    )
    builder.button(
        text=f"{emojis.get('grades', '🎯')} Оценки",
        callback_data=DiaryCallback(action="grades"),
    )
    builder.button(
        text=f"{emojis.get('absences', '❌')} Пропуски",
        callback_data=DiaryCallback(action="absences"),
    )
    builder.button(text="📊 Статистика", callback_data=DiaryCallback(action="stats"))
    builder.button(text="➕ Добавить", callback_data=DiaryCallback(action="add"))
    builder.button(
        text=f"{emojis.get('home', '🏠')} В меню",
        callback_data=MenuCallback(action="home"),
    )
    builder.adjust(2)
    return builder.as_markup()


def get_applications_keyboard() -> types.InlineKeyboardMarkup:
    """Create applications menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📅 Сегодняшние занятия", callback_data=ApplicationCallback(action="today")
    )
    builder.button(
        text="🗓 Выбрать даты вручную",
        callback_data=ApplicationCallback(action="manual_dates"),
    )
    builder.button(
        text="📋 Период (несколько дней)",
        callback_data=ApplicationCallback(action="period"),
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_attestation_keyboard() -> types.InlineKeyboardMarkup:
    """Create attestation help keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔢 КНЛ/КНС",
        callback_data=AttestationCallback(action="info", topic="knl_kns"),
    )
    builder.button(
        text="📋 Пропуски",
        callback_data=AttestationCallback(action="info", topic="absences"),
    )
    builder.button(
        text="📚 Консультации",
        callback_data=AttestationCallback(action="info", topic="consultations"),
    )
    builder.button(
        text="📅 Сроки документов",
        callback_data=AttestationCallback(action="info", topic="deadlines"),
    )
    builder.button(
        text="🎓 Аттестация",
        callback_data=AttestationCallback(action="info", topic="attestation"),
    )
    builder.button(
        text="💡 Советы", callback_data=AttestationCallback(action="info", topic="tips")
    )
    builder.button(
        text="❓ Задать вопрос", callback_data=AttestationCallback(action="ask")
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_grades_keyboard(subjects: list[str] | None = None) -> types.InlineKeyboardMarkup:
    """Create grades management keyboard."""
    builder = InlineKeyboardBuilder()

    if subjects:
        for subject in subjects:
            builder.button(
                text=f"📚 {subject}",
                callback_data=GradeCallback(action="view_subject", subject=subject),
            )

    builder.button(
        text="➕ Добавить предмет", callback_data=GradeCallback(action="add_subject")
    )
    builder.button(
        text="📊 Общая статистика", callback_data=GradeCallback(action="overall_stats")
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_subject_keyboard(subject: str) -> types.InlineKeyboardMarkup:
    """Create subject management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Добавить оценку",
        callback_data=GradeCallback(action="add_grade", subject=subject),
    )
    builder.button(
        text="✅ Отметить посещение",
        callback_data=GradeCallback(
            action="add_attendance", subject=subject, data="present"
        ),
    )
    builder.button(
        text="❌ Отметить пропуск",
        callback_data=GradeCallback(
            action="add_attendance", subject=subject, data="absent"
        ),
    )
    builder.button(text="⬅️ К предметам", callback_data=MenuCallback(action="grades"))
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_group_search_keyboard() -> types.InlineKeyboardMarkup:
    """Create group search keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔍 Быстрый поиск",
        callback_data=GroupSearchCallback(action="quick_search"),
    )
    builder.button(
        text="📊 Подробный поиск",
        callback_data=GroupSearchCallback(action="detailed_search"),
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)
    return builder.as_markup()


def get_group_result_keyboard(group_number: str) -> types.InlineKeyboardMarkup:
    """Create keyboard for group search result."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📅 Текущая неделя",
        callback_data=GroupSearchCallback(
            action="show_schedule", group_number=group_number, week="current"
        ),
    )
    builder.button(
        text="⬅️ Предыдущая",
        callback_data=GroupSearchCallback(
            action="show_schedule", group_number=group_number, week="prev"
        ),
    )
    builder.button(
        text="➡️ Следующая",
        callback_data=GroupSearchCallback(
            action="show_schedule", group_number=group_number, week="next"
        ),
    )
    builder.button(
        text="📊 Excel",
        callback_data=GroupSearchCallback(action="export", group_number=group_number),
    )
    builder.button(
        text="🔍 Новый поиск", callback_data=MenuCallback(action="search_group")
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(3, 2)
    return builder.as_markup()


async def show_loading_spinner(
    message, text_prefix: str = "⏳ Загрузка", duration: int = 10
) -> None:
    """Показать спиннер во время загрузки."""
    spinner_frames = list("🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛")
    steps = [
        "Подключение к API...",
        "Поиск в базе расписаний...",
        "Обработка данных...",
        "Объединение лекций и семинаров...",
        "Завершение...",
    ]

    frames_per_step = max(1, duration // len(steps))

    for step_idx, step_text in enumerate(steps):
        for i in range(frames_per_step):
            frame = spinner_frames[i % len(spinner_frames)]
            try:
                progress = f"{step_idx + 1}/{len(steps)}"
                await message.edit_text(
                    f"{frame} {text_prefix}\n📊 {progress} | {step_text}"
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Could not update spinner: {e}")
                break


# --- 7. File generation function ---
async def generate_schedule_file(
    search_result: dict, format_type: str, subgroup_name: str
) -> Path:
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
    schedule_data = search_result["data"]

    # Process using v3 logic (working version)
    try:
        import sys
        from pathlib import Path

        # Add legacy/v3 to path temporarily
        v3_path = Path(__file__).parent / "legacy" / "v3"
        sys.path.insert(0, str(v3_path))

        import datetime

        from config import WEEK_DAYS
        from get_raw import process_lessons
        from ical import gen_ical
        from processing import process_lessons_for_export
        from xlsx import gen_excel_file

        # Process lessons from the schedule data
        all_lessons = process_lessons(schedule_data)

        if not all_lessons:
            msg = "No lessons found in schedule data"
            raise Exception(msg)

        # Determine first schedule date (same logic as v3/main.py)
        earliest_lesson = min(
            all_lessons,
            key=lambda x: (int(x.weekNumber), WEEK_DAYS.get(x.dayName, 999)),
        )
        first_day_index = WEEK_DAYS.get(earliest_lesson.dayName, 0)

        semestr_num: int = 0 if earliest_lesson.semester == "осенний" else 1
        year: int = int(earliest_lesson.academicYear.split("/")[semestr_num])
        month: int = [9, 2][semestr_num]
        first_monday_of_semestr: datetime.date = datetime.date(year, month, 1)
        while first_monday_of_semestr.weekday() != first_day_index:
            first_monday_of_semestr += datetime.timedelta(days=1)

        # Process lessons for export using v3 logic
        processed_lessons = process_lessons_for_export(
            all_lessons, subgroup_name, first_monday_of_semestr
        )

        if not processed_lessons:
            msg = f"No lessons found for subgroup {subgroup_name}"
            raise Exception(msg)

        # Ensure output directory exists
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

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
        msg = f"Generated file {file_path} does not exist"
        raise Exception(msg)

    except Exception as e:
        logger.error(f"Error generating schedule file: {e}")

        # Fallback: create a simple text file with error info
        file_hash = hashlib.md5(
            f"{search_result['display_name']}_{subgroup_name}".encode()
        ).hexdigest()
        fallback_file = temp_dir / f"error_{file_hash}.txt"

        with open(fallback_file, "w", encoding="utf-8") as f:
            f.write(f"Error generating {format_type} file\n")
            f.write(f"Schedule: {search_result['display_name']}\n")
            f.write(f"Subgroup: {subgroup_name}\n")
            f.write(f"Error: {e!s}\n")
            f.write("Generated by Schedule Processor Bot\n")

        return fallback_file


def format_schedule_info(schedule_data: dict) -> str:
    """
    Format schedule data into readable description for bot buttons.

    Args:
        schedule_data: Raw schedule data from API

    Returns:
        Formatted string with schedule characteristics
    """
    data = schedule_data.get("data", {})

    # Extract key information
    file_name = data.get("fileName", "Unknown")

    # Try to extract info from lessons
    lessons = data.get("scheduleLessonDtoList", [])
    if lessons:
        first_lesson = lessons[0]
        speciality = first_lesson.get("speciality", "Unknown")
        course_number = first_lesson.get("courseNumber", "Unknown")
        semester = first_lesson.get("semester", "Unknown")
        academic_year = first_lesson.get("academicYear", "Unknown")
        group_stream = first_lesson.get("groupStream", "Unknown")
        lesson_type = first_lesson.get("lessonType", "Unknown")

        # Get unique subgroups
        subgroups = set()
        for lesson in lessons[:10]:  # Check first 10 lessons
            if lesson.get("subgroup"):
                subgroups.add(lesson.get("subgroup"))

        subgroups_str = ", ".join(sorted(subgroups)) if subgroups else "Unknown"

        return (
            f"{speciality}\n"
            f"Курс: {course_number}, Поток: {group_stream}\n"
            f"Семестр: {semester} {academic_year}\n"
            f"Подгруппы: {subgroups_str}\n"
            f"Тип: {lesson_type}"
        )

    return f"Файл: {file_name}"


# --- 8. Handlers ---


@dp.message(Command("start", "help"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    logger.info(f"User {message.from_user.id} started the bot.")
    await state.clear()

    # Check user agreement
    disclaimer_manager = DisclaimerManager(BASE_DIR / "user_data" / "agreements")
    user_id = str(message.from_user.id)

    if not disclaimer_manager.has_user_agreed(user_id):
        # Show disclaimer first
        agreement_text = disclaimer_manager.get_welcome_agreement()
        disclaimer_manager.record_user_agreement(user_id)  # Auto-agree for now

        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Понятно, продолжить",
            callback_data=MenuCallback(action="continue_after_agreement"),
        )

        await message.answer(agreement_text, reply_markup=builder.as_markup())
        return

    # Load user profile
    profile_manager = StudentProfileManager(BASE_DIR / "user_data" / "profiles")
    user_profile = profile_manager.load_profile(message.from_user.id)

    config = get_config()
    welcome_msg = (
        config.get("bot", {})
        .get("messages", {})
        .get("welcome", "👋 Привет! Я твой учебный помощник.")
    )

    if user_profile:
        # Returning user with profile
        await state.set_state(MainMenu.home)
        await message.answer(
            f"📚 Студент: {user_profile.full_name} | Группа: {user_profile.group}\n\n"
            f"Что тебя интересует?",
            reply_markup=get_main_menu_keyboard(user_profile),
        )
    else:
        # New user
        await state.set_state(MainMenu.home)
        setup_msg = (
            config.get("bot", {})
            .get("messages", {})
            .get("profile_setup_needed", "Для начала работы нужно выбрать твою группу:")
        )
        await message.answer(
            f"{welcome_msg}\n\n{setup_msg}", reply_markup=get_main_menu_keyboard()
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


# --- 8.1 Main Menu Handlers ---


@dp.callback_query(MenuCallback.filter())
async def handle_main_menu(
    callback: types.CallbackQuery, callback_data: MenuCallback, state: FSMContext
) -> None:
    await callback.answer()
    action = callback_data.action
    logger.info(f"User {callback.from_user.id} selected menu action: {action}")

    profile_manager = StudentProfileManager(BASE_DIR / "user_data" / "profiles")
    user_profile = profile_manager.load_profile(callback.from_user.id)

    if action == "home":
        await state.set_state(MainMenu.home)
        if user_profile:
            await callback.message.edit_text(
                f"📚 Студент: {user_profile.full_name} | Группа: {user_profile.group}\n\n"
                f"Что тебя интересует?",
                reply_markup=get_main_menu_keyboard(user_profile),
            )
        else:
            await callback.message.edit_text(
                "👋 Привет! Я твой учебный помощник.\n\n"
                "Для начала работы нужно выбрать твою группу:",
                reply_markup=get_main_menu_keyboard(),
            )

    elif action == "setup_profile":
        await state.set_state(ProfileSetup.waiting_name)
        await callback.message.edit_text(
            "Давай настроим твой профиль!\n\nКак тебя зовут? (ФИО полностью)"
        )

    elif action == "my_schedule":
        await state.set_state(MainMenu.schedule_view)
        # TODO: Implement schedule view
        await callback.message.edit_text(
            "📅 Расписание группы (функция в разработке)\n\n"
            "🗓 Сегодня: Информация о занятиях будет здесь",
            reply_markup=InlineKeyboardBuilder()
            .button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
            .as_markup(),
        )

    elif action == "diary":
        await state.set_state(DiaryStates.main_view)
        if user_profile:
            diary = StudentDiary(user_profile.user_id)
            stats = diary.get_statistics()

            stats_text = "📊 Дневник | "
            if user_profile.full_name:
                stats_text += f"{user_profile.full_name.split()[1]} {user_profile.full_name.split()[0]} | "
            stats_text += f"{user_profile.group}\n\n"

            stats_text += "📈 Текущая успеваемость:\n"
            if stats.get("subjects"):
                for subject, avg in stats["subjects"].items():
                    stats_text += f"📚 {subject}: {avg:.1f}\n"
            else:
                stats_text += "Пока нет оценок\n"

            stats_text += f"\n📝 Активных ДЗ: {stats.get('active_homework', 0)}\n"
            stats_text += f"❌ Пропусков: {stats.get('absences', 0)} дней"

            await callback.message.edit_text(
                stats_text, reply_markup=get_diary_keyboard()
            )
        else:
            await callback.message.edit_text(
                "Сначала настройте профиль", reply_markup=get_main_menu_keyboard()
            )

    elif action == "applications":
        await state.set_state(ApplicationStates.selecting_dates)
        if user_profile:
            await callback.message.edit_text(
                f"📝 Система заявлений СЗГМУ\n\n"
                f"👤 Студент: {user_profile.full_name}\n"
                f"🎓 Группа: {user_profile.group}, {user_profile.course} курс\n\n"
                f"ℹ️ Нужно 2 документа:\n"
                f"• Заявления по каждой дисциплине\n"
                f"• Объяснительная в дирекцию института\n\n"
                f"Что пропускаешь?",
                reply_markup=get_applications_keyboard(),
            )
        else:
            await callback.message.edit_text(
                "Сначала настройте профиль", reply_markup=get_main_menu_keyboard()
            )

    elif action == "attestation":
        await state.set_state(AttestationStates.main_view)
        if user_profile:
            await callback.message.edit_text(
                f"📚 Справочник по аттестации СЗГМУ\n\n"
                f"👤 {user_profile.full_name}\n"
                f"🎓 {user_profile.group}, {user_profile.course} курс\n\n"
                f"Выберите тему:",
                reply_markup=get_attestation_keyboard(),
            )
        else:
            await callback.message.edit_text(
                "Сначала настройте профиль", reply_markup=get_main_menu_keyboard()
            )

    elif action == "grades":
        await state.set_state(GradeStates.main_view)
        if user_profile:
            calculator = GradeCalculator(str(callback.from_user.id))
            subjects = calculator.get_all_subjects()
            stats = calculator.get_overall_stats()

            text = "🔢 **Академические показатели**\n\n"
            text += f"👤 {user_profile.full_name}\n"
            text += f"🎓 {user_profile.group}, {user_profile.course} курс\n\n"

            if stats["total_subjects"] > 0:
                text += "📊 **Общая статистика:**\n"
                text += f"• Средний ТСБ: {stats['average_tsb']}\n"
                text += f"• Средний КНЛ: {stats['average_knl']}\n"
                text += f"• Средний КНС: {stats['average_kns']}\n"
                text += f"• **Средний ОСБ: {stats['average_osb']}**\n\n"
                text += f"📚 Предметов: {stats['total_subjects']}\n"
                text += f"🎯 Всего оценок: {stats['total_grades']}"
            else:
                text += "📚 Предметы еще не добавлены.\n\n"
                text += "Начните с добавления предмета и ведения учета оценок и посещаемости."

            await callback.message.edit_text(
                text, reply_markup=get_grades_keyboard(subjects)
            )
        else:
            await callback.message.edit_text(
                "Сначала настройте профиль", reply_markup=get_main_menu_keyboard()
            )

    elif action == "search_group":
        await state.set_state(GroupSearchStates.choosing_search_type)
        if user_profile:
            semester_detector = SemesterDetector()
            current_semester = semester_detector.get_semester_display_text()

            await callback.message.edit_text(
                f"👥 **Поиск группы**\n\n📅 {current_semester}\n\nВыберите тип поиска:",
                reply_markup=get_group_search_keyboard(),
            )
        else:
            await callback.message.edit_text(
                "Сначала настройте профиль", reply_markup=get_main_menu_keyboard()
            )

    elif action == "continue_after_agreement":
        # После соглашения показать обычное меню
        await state.set_state(MainMenu.home)

        # Load user profile
        profile_manager = StudentProfileManager(BASE_DIR / "user_data" / "profiles")
        user_profile = profile_manager.load_profile(callback.from_user.id)

        config = get_config()
        welcome_msg = (
            config.get("bot", {})
            .get("messages", {})
            .get("welcome", "👋 Привет! Я твой учебный помощник.")
        )

        if user_profile:
            await callback.message.edit_text(
                f"📚 Студент: {user_profile.full_name} | Группа: {user_profile.group}\n\n"
                f"Что тебя интересует?",
                reply_markup=get_main_menu_keyboard(user_profile),
            )
        else:
            setup_msg = (
                config.get("bot", {})
                .get("messages", {})
                .get(
                    "profile_setup_needed",
                    "Для начала работы нужно выбрать твою группу:",
                )
            )
            await callback.message.edit_text(
                f"{welcome_msg}\n\n{setup_msg}", reply_markup=get_main_menu_keyboard()
            )

    elif action == "search":
        await state.set_state(SearchForm.waiting_activation)
        await callback.message.edit_text(
            "🔍 Поиск расписания\n\nНайдем расписание для любой группы",
            reply_markup=InlineKeyboardBuilder()
            .button(text="Начать выбор", callback_data="start_selection")
            .as_markup(),
        )


# --- 8.2 Profile Setup Handlers ---


@dp.message(StateFilter(ProfileSetup.waiting_name))
async def process_profile_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer(
            "Пожалуйста, введите полное ФИО (имя и фамилию как минимум)"
        )
        return

    await state.update_data(full_name=full_name)
    await state.set_state(ProfileSetup.selecting_speciality)

    # Load available filters to get specialities
    try:
        logger.info("Loading available filters for profile setup")
        available_filters = await get_available_filters()
        specialities = available_filters.get("Специальность", [])

        if not specialities:
            specialities = ["Лечебное дело", "Педиатрия", "Стоматология"]  # Fallback

        keyboard = get_profile_setup_keyboard(
            "speciality", specialities[:10]
        )  # Limit to first 10
        await message.answer(
            "Отлично! Теперь найдем твою группу.\n\nВыберите специальность:",
            reply_markup=keyboard,
        )
        logger.info(f"Loaded {len(specialities)} specialities for profile setup")

    except Exception as e:
        logger.error(f"Error loading specialities: {e}")
        # Fallback with basic specialities
        basic_specialities = ["Лечебное дело", "Педиатрия", "Стоматология", "Фармация"]
        keyboard = get_profile_setup_keyboard("speciality", basic_specialities)

        await message.answer(
            "Отлично! Теперь найдем твою группу.\n\n"
            "⚠️ Загрузка данных заняла много времени. Показаны основные специальности.\n\n"
            "Выберите специальность:",
            reply_markup=keyboard,
        )


@dp.callback_query(
    ProfileCallback.filter(), StateFilter(ProfileSetup.selecting_speciality)
)
async def process_profile_speciality(
    callback: types.CallbackQuery, callback_data: ProfileCallback, state: FSMContext
) -> None:
    await callback.answer()
    speciality = callback_data.value
    await state.update_data(speciality=speciality)
    await state.set_state(ProfileSetup.selecting_course)

    # Simple course selection
    courses = ["1", "2", "3", "4", "5", "6"]
    keyboard = get_profile_setup_keyboard("course", courses)
    await callback.message.edit_text("Курс:", reply_markup=keyboard)


@dp.callback_query(ProfileCallback.filter(), StateFilter(ProfileSetup.selecting_course))
async def process_profile_course(
    callback: types.CallbackQuery, callback_data: ProfileCallback, state: FSMContext
) -> None:
    await callback.answer()
    course = callback_data.value
    await state.update_data(course=course)
    await state.set_state(ProfileSetup.selecting_stream)

    # Simple stream selection
    streams = ["а", "б", "в"]
    keyboard = get_profile_setup_keyboard("stream", streams)
    await callback.message.edit_text("Поток:", reply_markup=keyboard)


@dp.callback_query(ProfileCallback.filter(), StateFilter(ProfileSetup.selecting_stream))
async def process_profile_stream(
    callback: types.CallbackQuery, callback_data: ProfileCallback, state: FSMContext
) -> None:
    await callback.answer()
    stream = callback_data.value
    await state.update_data(stream=stream)

    data = await state.get_data()
    course = data.get("course")

    # Generate group options based on course and stream
    groups = [f"{course}0{i}{stream}" for i in range(1, 6)]

    await state.set_state(ProfileSetup.selecting_group)
    keyboard = get_profile_setup_keyboard("group", groups)
    await callback.message.edit_text("Подгруппа:", reply_markup=keyboard)


@dp.callback_query(ProfileCallback.filter(), StateFilter(ProfileSetup.selecting_group))
async def process_profile_group(
    callback: types.CallbackQuery, callback_data: ProfileCallback, state: FSMContext
) -> None:
    await callback.answer()
    group = callback_data.value

    data = await state.get_data()
    full_name = data.get("full_name")
    speciality = data.get("speciality")
    course = data.get("course")

    await state.set_state(ProfileSetup.confirmation)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, сохранить", callback_data=ProfileCallback(action="confirm")
    )
    builder.button(
        text="❌ Выбрать заново", callback_data=MenuCallback(action="setup_profile")
    )

    await callback.message.edit_text(
        f"🎉 Отлично! Твоя группа: {group}\n\n"
        f"{speciality}, {course} курс\n"
        f"Студент: {full_name}\n\n"
        f"Сохранить эти данные?",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(
    ProfileCallback.filter(F.action == "confirm"),
    StateFilter(ProfileSetup.confirmation),
)
async def confirm_profile_setup(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()

    data = await state.get_data()

    # Create and save profile
    profile = StudentProfile(
        user_id=str(callback.from_user.id),
        telegram_username=callback.from_user.username or "",
        full_name=data.get("full_name"),
        speciality=data.get("speciality"),
        course=int(data.get("course")),
        stream=data.get("stream"),
        group=data.get("group"),
    )

    profile_manager = StudentProfileManager(BASE_DIR / "user_data" / "profiles")
    profile_manager.save_profile(profile)

    # Initialize diary for the user
    StudentDiary(str(callback.from_user.id))

    await state.clear()
    await state.set_state(MainMenu.home)

    welcome_back = "✅ Профиль сохранен! Добро пожаловать в систему."

    await callback.message.edit_text(
        f"📚 Студент: {profile.full_name} | Группа: {profile.group}\n\n"
        f"{welcome_back}\n\n"
        f"Что тебя интересует?",
        reply_markup=get_main_menu_keyboard(profile),
    )


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
    available_options = data["available_filters"][filter_name]

    # Если value - это индекс, получаем реальное значение
    if value.isdigit():
        option_index = int(value)
        if 0 <= option_index < len(available_options):
            actual_value = available_options[option_index]
        else:
            await callback.answer("❌ Некорректный выбор", show_alert=True)
            return
    else:
        actual_value = value

    if filter_name not in selected_filters:
        selected_filters[filter_name] = []

    if actual_value in selected_filters[filter_name]:
        selected_filters[filter_name].remove(actual_value)
    else:
        selected_filters[filter_name].append(actual_value)

    await state.update_data(selected_filters=selected_filters)

    data = await state.get_data()
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
        button_text = formatted_info.replace("\n", " | ")
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
    schedule_data = selected_result.get("data", {})
    lessons = schedule_data.get("scheduleLessonDtoList", [])
    subgroups = set()
    for lesson in lessons:
        if lesson.get("subgroup"):
            subgroups.add(lesson.get("subgroup"))

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
            text=f"📚 {subgroup}", callback_data=f"subgroup_{result_index}_{subgroup}"
        )
    builder.button(text="⬅️ Назад к результатам", callback_data="back_to_results")
    builder.adjust(2)

    await state.set_state(SearchForm.selecting_format)
    await callback.message.edit_text(
        f"📋 <b>Выбранное расписание:</b>\n{schedule_info}\n\n"
        f"Выберите подгруппу для генерации файла:",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(
    F.data.startswith("subgroup_"), StateFilter(SearchForm.selecting_format)
)
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
        callback_data=FormatCallback(result_index=result_index, format_type="xlsx"),
    )
    builder.button(
        text="📅 Календарь (.ics)",
        callback_data=FormatCallback(result_index=result_index, format_type="ics"),
    )
    builder.button(
        text="⬅️ Назад к подгруппам", callback_data=f"back_to_subgroups_{result_index}"
    )
    builder.adjust(2)

    await callback.message.edit_text(
        f"📚 <b>Подгруппа:</b> {subgroup_name}\n\nВыберите формат файла:",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(
    F.data.startswith("back_to_subgroups_"), StateFilter(SearchForm.selecting_format)
)
async def back_to_subgroups(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    result_index = int(callback.data.split("_")[-1])

    # Re-trigger result selection to show subgroup menu
    fake_callback_data = ResultCallback(index=result_index)
    await select_result(callback, fake_callback_data, state)


@dp.callback_query(
    F.data == "back_to_results", StateFilter(SearchForm.selecting_format)
)
async def back_to_results_from_subgroups(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()

    # Go back to results selection
    data = await state.get_data()
    search_results = data.get("search_results", [])

    builder = InlineKeyboardBuilder()
    for i, result in enumerate(search_results):
        formatted_info = format_schedule_info(result)
        button_text = formatted_info.replace("\n", " | ")
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
    await callback.message.edit_text(
        f"⏳ Генерирую {format_name} файл для подгруппы {subgroup_name}..."
    )

    try:
        file_path = await generate_schedule_file(
            selected_result, format_type, subgroup_name
        )

        # Проверяем, что файл существует
        if not file_path.exists():
            msg = f"Generated file does not exist: {file_path}"
            raise FileNotFoundError(msg)

        # Send file to user with disclaimer
        disclaimer_manager = DisclaimerManager(BASE_DIR / "user_data" / "agreements")
        disclaimer = disclaimer_manager.get_short_disclaimer()

        document = FSInputFile(file_path)
        file_description = f"📎 {format_name} файл для подгруппы {subgroup_name}"
        caption = f"{file_description}\n\n{disclaimer}"

        await callback.message.answer_document(document, caption=caption)

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
            f"❌ Ошибка при генерации файла: {e!s}\n\n"
            f"Попробуйте еще раз или выберите другой формат."
        )
        # Return to format selection
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📊 Excel (.xlsx)",
            callback_data=FormatCallback(result_index=result_index, format_type="xlsx"),
        )
        builder.button(
            text="📅 Календарь (.ics)",
            callback_data=FormatCallback(result_index=result_index, format_type="ics"),
        )
        builder.adjust(2)

        await callback.message.answer(
            f"Выберите формат файла для подгруппы {subgroup_name}:",
            reply_markup=builder.as_markup(),
        )


# --- 8.3 Attestation Handlers ---


@dp.callback_query(AttestationCallback.filter())
async def handle_attestation(
    callback: types.CallbackQuery, callback_data: AttestationCallback, state: FSMContext
) -> None:
    await callback.answer()
    action = callback_data.action
    topic = callback_data.topic

    attestation_helper = AttestationHelper()

    if action == "info":
        await state.set_state(AttestationStates.viewing_info)

        if topic == "knl_kns":
            text = attestation_helper.get_knl_kns_explanation()
        elif topic == "absences":
            text = attestation_helper._get_absence_detailed_info()
        elif topic == "consultations":
            text = attestation_helper.get_individual_consultations_info()
        elif topic == "deadlines":
            text = attestation_helper.get_document_deadlines()
        elif topic == "attestation":
            text = attestation_helper._get_attestation_info()
        elif topic == "tips":
            tips = attestation_helper.get_practical_tips()
            text = "💡 **Практические советы**\n\n" + "\n".join(tips)
        else:
            text = "Информация не найдена"

        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=MenuCallback(action="attestation"))
        builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))

        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    elif action == "ask":
        await state.set_state(AttestationStates.asking_question)
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Отмена", callback_data=MenuCallback(action="attestation")
        )

        await callback.message.edit_text(
            "❓ **Задайте ваш вопрос**\n\n"
            "Напишите вопрос об аттестации, пропусках, КНЛ/КНС или документах.\n"
            "Бот попытается дать релевантный ответ на основе регламентов СЗГМУ.",
            reply_markup=builder.as_markup(),
        )


@dp.message(StateFilter(AttestationStates.asking_question))
async def process_attestation_question(message: Message, state: FSMContext) -> None:
    question = message.text.strip()

    attestation_helper = AttestationHelper()
    answer = attestation_helper.analyze_question(question)

    if answer:
        response_text = f"❓ **Ваш вопрос:** {question}\n\n{answer}"
    else:
        response_text = (
            f"❓ **Ваш вопрос:** {question}\n\n"
            "❌ Не удалось найти подходящий ответ.\n\n"
            "Попробуйте:\n"
            "• Переформулировать вопрос более конкретно\n"
            "• Использовать ключевые слова: КНЛ, КНС, пропуски, консультации, сроки\n"
            "• Обратиться к разделам информации через кнопки"
        )

    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ К разделам", callback_data=MenuCallback(action="attestation")
    )
    builder.button(
        text="❓ Другой вопрос", callback_data=AttestationCallback(action="ask")
    )
    builder.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
    builder.adjust(2)

    await state.set_state(AttestationStates.viewing_info)
    await message.answer(response_text, reply_markup=builder.as_markup())


# --- 8.4 Group Search Handlers ---


@dp.callback_query(GroupSearchCallback.filter())
async def handle_group_search(
    callback: types.CallbackQuery, callback_data: GroupSearchCallback, state: FSMContext
) -> None:
    await callback.answer()
    action = callback_data.action

    if action == "quick_search":
        await state.set_state(GroupSearchStates.entering_group_number)
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Отмена", callback_data=MenuCallback(action="search_group")
        )

        await callback.message.edit_text(
            "🔍 **Быстрый поиск группы**\n\n"
            "📝 Введите номер группы:\n"
            "Примеры: `103а`, `204б`, `301в`",
            reply_markup=builder.as_markup(),
        )

    elif action == "detailed_search":
        # TODO: Реализовать подробный поиск
        await callback.message.edit_text(
            "📊 **Подробный поиск**\n\n"
            "🚧 В разработке...\n"
            "Пока используйте быстрый поиск по номеру группы.",
            reply_markup=get_group_search_keyboard(),
        )

    elif action == "show_schedule":
        week = callback_data.week

        # Получаем данные группы из состояния
        data = await state.get_data()
        group_info = data.get("current_group_info")

        if not group_info:
            await callback.message.edit_text(
                "❌ Данные группы не найдены. Попробуйте поиск заново.",
                reply_markup=get_group_search_keyboard(),
            )
            return

        await show_group_schedule(callback.message, group_info, week, state)

    elif action == "export":
        # TODO: Реализовать экспорт
        await callback.answer("🚧 Экспорт в разработке", show_alert=True)


@dp.message(StateFilter(GroupSearchStates.entering_group_number))
async def process_group_number(message: Message, state: FSMContext) -> None:
    group_number = message.text.strip()

    # Валидация ввода
    if not group_number or len(group_number) > 10:
        await message.answer(
            "❌ Неверный формат номера группы.\n\n"
            "Введите корректный номер (например: 103а, 204б):",
            reply_markup=InlineKeyboardBuilder()
            .button(text="❌ Отмена", callback_data=MenuCallback(action="search_group"))
            .as_markup(),
        )
        return

    # Показываем спиннер
    loading_msg = await message.answer("🔍 Начинаю поиск группы...")

    try:
        # Создаем задачи параллельно
        group_search_service = GroupSearchService()

        # Запускаем поиск и спиннер параллельно
        search_task = asyncio.create_task(
            group_search_service.search_group_by_number(group_number)
        )
        spinner_task = asyncio.create_task(
            show_loading_spinner(loading_msg, f"Поиск группы {group_number}", 15)
        )

        # Ждем завершения поиска с тайм-аутом
        try:
            groups = await asyncio.wait_for(search_task, timeout=30.0)
            spinner_task.cancel()  # Останавливаем спиннер

        except TimeoutError:
            spinner_task.cancel()
            await loading_msg.edit_text(
                f"⏱️ Поиск группы `{group_number}` занял слишком много времени.\n\n"
                f"Попробуйте позже или проверьте номер группы.",
                reply_markup=get_group_search_keyboard(),
            )
            await state.set_state(GroupSearchStates.choosing_search_type)
            return

        except Exception as search_error:
            spinner_task.cancel()
            logger.error(f"Search task failed: {search_error}")
            raise

        if not groups:
            await loading_msg.edit_text(
                f"❌ Группа `{group_number}` не найдена.\n\n"
                f"Возможные причины:\n"
                f"• Неверный номер группы\n"
                f"• Группа не активна в текущем семестре\n"
                f"• Временная недоступность данных\n\n"
                f"Попробуйте другой номер:",
                reply_markup=get_group_search_keyboard(),
            )
            await state.set_state(GroupSearchStates.choosing_search_type)
            return

        # Берем первую найденную группу
        group_info = groups[0]
        logger.info(
            f"Found group: {group_info.number}, speciality: {group_info.speciality}"
        )

        # Сохраняем в состояние
        await state.update_data(current_group_info=group_info)
        await state.set_state(GroupSearchStates.viewing_schedule)

        # Показываем расписание
        await show_group_schedule(loading_msg, group_info, "current", state)

    except Exception as e:
        logger.error(f"Critical error searching group {group_number}: {e}")
        try:
            await loading_msg.edit_text(
                f"❌ Критическая ошибка при поиске группы `{group_number}`.\n\n"
                f"Техническая информация: {str(e)[:100]}...\n\n"
                f"Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_group_search_keyboard(),
            )
        except Exception as edit_error:
            logger.error(f"Could not edit error message: {edit_error}")
            await message.answer(
                "❌ Произошла критическая ошибка.\n\n"
                "Попробуйте перезапустить бота командой /start"
            )

        await state.set_state(GroupSearchStates.choosing_search_type)


async def show_group_schedule(
    message, group_info, week: str, state: FSMContext
) -> None:
    """Показать расписание группы."""
    try:
        group_search_service = GroupSearchService()

        # Определяем номер недели с защитой от ошибок
        try:
            semester_info = (
                group_search_service.semester_detector.get_current_semester_info()
            )
            current_week = semester_info.current_week
        except Exception as e:
            logger.warning(f"Failed to get semester info: {e}, using default week")
            current_week = 1

        if week == "current":
            week_number = current_week
        elif week == "prev":
            week_number = max(1, current_week - 1)
        elif week == "next":
            week_number = min(20, current_week + 1)
        else:
            week_number = current_week

        logger.info(
            f"Showing schedule for group {group_info.number}, week {week_number}"
        )

        # Форматируем расписание с защитой от ошибок
        try:
            schedule_text = group_search_service.format_group_schedule(
                group_info, week_number
            )

            if not schedule_text or schedule_text.strip() == "":
                schedule_text = f"📅 **Расписание группы {group_info.number}**\n\n❌ Нет данных для отображения."

        except Exception as e:
            logger.error(f"Error formatting schedule: {e}")
            schedule_text = f"📅 **Расписание группы {group_info.number}**\n\n❌ Ошибка при обработке данных расписания.\n\nТехническая информация: {str(e)[:100]}"

        # Добавляем дисклеймер с защитой от ошибок
        try:
            disclaimer_manager = DisclaimerManager(
                BASE_DIR / "user_data" / "agreements"
            )
            disclaimer = disclaimer_manager.get_short_disclaimer()
        except Exception as e:
            logger.warning(f"Failed to get disclaimer: {e}")
            disclaimer = "\n⚠️ Информация может быть неактуальной. Уточняйте расписание в официальных источниках."

        full_text = f"{schedule_text}\n\n{disclaimer}"

        # Ограничиваем длину сообщения для Telegram
        max_length = 4000
        if len(full_text) > max_length:
            # Обрезаем текст расписания, сохраняя дисклеймер
            available_length = (
                max_length - len(disclaimer) - 50
            )  # Запас для "... (сокращено)"
            truncated_schedule = (
                schedule_text[:available_length] + "\n\n... (сокращено)"
            )
            full_text = f"{truncated_schedule}\n\n{disclaimer}"

        # Создаем клавиатуру с защитой от ошибок
        try:
            keyboard = get_group_result_keyboard(group_info.number)
        except Exception as e:
            logger.warning(f"Failed to create keyboard: {e}")
            keyboard = (
                InlineKeyboardBuilder()
                .button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
                .as_markup()
            )

        # Отправляем сообщение с защитой от ошибок
        try:
            await message.edit_text(full_text, reply_markup=keyboard)
            logger.info(
                f"Successfully displayed schedule for group {group_info.number}"
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Пробуем отправить новое сообщение
            try:
                await message.answer(full_text, reply_markup=keyboard)
            except Exception as send_error:
                logger.error(f"Failed to send new message: {send_error}")
                await message.answer(
                    "❌ Критическая ошибка при отображении расписания."
                )

    except Exception as e:
        logger.error(f"Critical error showing group schedule: {e}")
        try:
            error_text = (
                f"❌ Критическая ошибка при отображении расписания.\n\n"
                f"Группа: {getattr(group_info, 'number', 'Unknown')}\n"
                f"Ошибка: {str(e)[:200]}...\n\n"
                f"Попробуйте:\n"
                f"• Поиск другой группы\n"
                f"• Повторить попытку позже\n"
                f"• Обратиться к администратору"
            )

            keyboard = InlineKeyboardBuilder()
            keyboard.button(
                text="🔍 Новый поиск", callback_data=MenuCallback(action="search_group")
            )
            keyboard.button(text="🏠 В меню", callback_data=MenuCallback(action="home"))
            keyboard.adjust(2)

            await message.edit_text(error_text, reply_markup=keyboard.as_markup())

        except Exception as final_error:
            logger.critical(f"Could not display error message: {final_error}")
            # Последняя попытка - простое текстовое сообщение
            await message.answer(
                "❌ Произошла критическая ошибка. Перезапустите бота командой /start"
            )


# --- 9. Error handler ---
@dp.error(StateFilter("*"))
async def global_error_handler(
    event: types.ErrorEvent, state: FSMContext
) -> Coroutine[Any, Any, None]:
    exception_info = (
        f"Exception: {event.exception.__class__.__name__}: {event.exception}"
    )
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
