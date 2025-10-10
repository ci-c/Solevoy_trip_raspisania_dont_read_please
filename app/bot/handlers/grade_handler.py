# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Обработчики для модуля оценок и академических показателей."""

from datetime import date
from typing import List

from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import GradeCallback, MenuCallback
from app.bot.keyboards import (
    get_main_menu_keyboard,
    get_grades_keyboard,
    get_subject_grades_keyboard,
)
from app.bot.states import GradeStates
from app.services.grade_calculator_service import GradeCalculatorService
from app.services.user_service import UserService
from app.models.academic import GradeType


async def handle_grades_main(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Главное меню оценок."""
    await callback.answer()
    user_id = callback.from_user.id

    try:
        user_service = UserService()
        user = await user_service.get_user_by_telegram_id(user_id)

        if not user:
            await callback.message.edit_text(
                "❌ Профиль не найден. Сначала настройте профиль.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        grade_service = GradeCalculatorService()

        # Получаем все предметы пользователя
        subjects = await grade_service.get_user_subjects(user_id)

        # Получаем общую статистику
        stats = await grade_service.get_user_overall_stats(user_id)

        text = f"🔢 **Академические показатели**\n\n"
        text += f"👤 {user.full_name or 'Пользователь'}\n"
        text += f"🎓 Группа: {user.group_name or 'Не указана'}\n\n"

        if stats.get("total_subjects", 0) > 0:
            text += "📊 **Общая статистика:**\n"
            text += f"• Средний ТСБ: {stats.get('average_tsb', 0):.2f}\n"
            text += f"• Средний КНЛ: {stats.get('average_knl', 0):.2f}\n"
            text += f"• Средний КНС: {stats.get('average_kns', 0):.2f}\n"
            text += f"• **Средний ОСБ: {stats.get('average_osb', 0):.2f}**\n\n"
            text += f"📚 Предметов: {stats.get('total_subjects', 0)}\n"
            text += f"🎯 Всего оценок: {stats.get('total_grades', 0)}"
        else:
            text += "📚 Предметы еще не добавлены.\n\n"
            text += (
                "Начните с добавления предмета и ведения учета оценок и посещаемости."
            )

        await state.set_state(GradeStates.main_view)
        await callback.message.edit_text(
            text,
            reply_markup=get_grades_keyboard(subjects),
        )

    except Exception as e:
        logger.error(f"Error in grades main handler: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке оценок. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def handle_subject_selection(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Выбор предмета для просмотра/редактирования."""
    await callback.answer()
    subject = callback_data.subject
    user_id = callback.from_user.id

    try:
        grade_service = GradeCalculatorService()

        # Получаем статистику по предмету
        subject_stats = await grade_service.get_subject_stats(user_id, subject)

        text = f"📚 **{subject}**\n\n"
        text += f"📊 **Показатели:**\n"
        text += f"• ТСБ: {subject_stats.tsb:.2f}\n"
        text += f"• КНЛ: {subject_stats.knl:.2f}\n"
        text += f"• КНС: {subject_stats.kns:.2f}\n"
        text += f"• **ОСБ: {subject_stats.osb:.2f}**\n\n"
        text += f"📈 **Посещаемость:**\n"
        text += f"• Всего занятий: {subject_stats.total_lessons}\n"
        text += f"• Посещено: {subject_stats.attended_lessons}\n"
        text += f"• Пропущено (ув.): {subject_stats.excused_absences}\n"
        text += f"• Пропущено (б/у): {subject_stats.unexcused_absences}"

        await state.set_state(GradeStates.viewing_subject)
        await state.update_data(selected_subject=subject)

        await callback.message.edit_text(
            text,
            reply_markup=get_subject_grades_keyboard(subject),
        )

    except Exception as e:
        logger.error(f"Error in subject selection handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при загрузке предмета '{subject}'. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def handle_add_grade(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Добавление новой оценки."""
    await callback.answer()
    subject = callback_data.subject
    user_id = callback.from_user.id

    try:
        await state.set_state(GradeStates.entering_grade_data)
        await state.update_data(selected_subject=subject)

        text = f"➕ **Добавить оценку по предмету: {subject}**\n\n"
        text += "Выберите тип оценки:"

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="📝 Контрольная",
                        callback_data=GradeCallback(
                            action="grade_type", subject=subject, data="контрольная"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="🧪 Лабораторная",
                        callback_data=GradeCallback(
                            action="grade_type", subject=subject, data="лабораторная"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="📖 Устный ответ",
                        callback_data=GradeCallback(
                            action="grade_type", subject=subject, data="устный"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="📄 Реферат",
                        callback_data=GradeCallback(
                            action="grade_type", subject=subject, data="реферат"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="📊 Зачет",
                        callback_data=GradeCallback(
                            action="grade_type", subject=subject, data="зачет"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="✍️ Свой вариант",
                        callback_data=GradeCallback(
                            action="grade_type", subject=subject, data="другое"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=GradeCallback(
                            action="view_subject", subject=subject
                        ).pack(),
                    ),
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in add grade handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при добавлении оценки. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def handle_grade_type_selection(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Выбор типа оценки."""
    await callback.answer()
    subject = callback_data.subject
    grade_type = callback_data.data
    user_id = callback.from_user.id

    try:
        await state.update_data(grade_type=grade_type)
        await state.set_state(GradeStates.entering_grade_data)

        text = f"📝 **Добавить {grade_type} по предмету: {subject}**\n\n"
        text += "Выберите оценку:"

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="5️⃣",
                        callback_data=GradeCallback(
                            action="grade_value", subject=subject, data="5"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="4️⃣",
                        callback_data=GradeCallback(
                            action="grade_value", subject=subject, data="4"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="3️⃣",
                        callback_data=GradeCallback(
                            action="grade_value", subject=subject, data="3"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="2️⃣",
                        callback_data=GradeCallback(
                            action="grade_value", subject=subject, data="2"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=GradeCallback(
                            action="add_grade", subject=subject
                        ).pack(),
                    ),
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in grade type selection handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при выборе типа оценки. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def handle_grade_value_selection(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Сохранение выбранной оценки."""
    await callback.answer()
    subject = callback_data.subject
    grade_value = int(callback_data.data)
    user_id = callback.from_user.id

    try:
        state_data = await state.get_data()
        grade_type = state_data.get("grade_type", "контрольная")

        grade_service = GradeCalculatorService()

        # Сохраняем оценку
        success = await grade_service.add_grade(
            user_id=user_id,
            subject=subject,
            grade=grade_value,
            control_point=grade_type,
            date=date.today(),
            is_excused=False,
        )

        if success:
            await callback.message.edit_text(
                f"✅ **Оценка добавлена!**\n\n"
                f"📚 Предмет: {subject}\n"
                f"📝 Тип: {grade_type}\n"
                f"🎯 Оценка: {grade_value}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n\n"
                f"Оценка учтена в расчете ОСБ.",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="📚 К предмету",
                                callback_data=GradeCallback(
                                    action="view_subject", subject=subject
                                ).pack(),
                            ),
                            types.InlineKeyboardButton(
                                text="🏠 В меню",
                                callback_data=MenuCallback(action="grades").pack(),
                            ),
                        ]
                    ]
                ),
            )
        else:
            await callback.message.edit_text(
                f"❌ Ошибка при сохранении оценки. Попробуйте позже.",
                reply_markup=get_grades_keyboard([]),
            )

        await state.clear()

    except Exception as e:
        logger.error(f"Error in grade value selection handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при сохранении оценки. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def handle_add_attendance(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Добавление записи о посещаемости."""
    await callback.answer()
    subject = callback_data.subject
    user_id = callback.from_user.id

    try:
        await state.set_state(GradeStates.entering_attendance_data)
        await state.update_data(selected_subject=subject)

        text = f"📅 **Отметить посещаемость по предмету: {subject}**\n\n"
        text += "Выберите тип занятия:"

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="📚 Лекция",
                        callback_data=GradeCallback(
                            action="attendance_type", subject=subject, data="лекция"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="🧪 Семинар",
                        callback_data=GradeCallback(
                            action="attendance_type", subject=subject, data="семинар"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=GradeCallback(
                            action="view_subject", subject=subject
                        ).pack(),
                    ),
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in add attendance handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при добавлении посещаемости. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def handle_attendance_type_selection(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Выбор типа занятия для посещаемости."""
    await callback.answer()
    subject = callback_data.subject
    lesson_type = callback_data.data
    user_id = callback.from_user.id

    try:
        await state.update_data(lesson_type=lesson_type)

        text = f"📅 **Отметить посещаемость: {lesson_type} по {subject}**\n\n"
        text += "Выберите статус:"

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✅ Присутствовал",
                        callback_data=GradeCallback(
                            action="attendance_status", subject=subject, data="present"
                        ).pack(),
                    ),
                    types.InlineKeyboardButton(
                        text="❌ Отсутствовал",
                        callback_data=GradeCallback(
                            action="attendance_status", subject=subject, data="absent"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="🏥 По уважительной причине",
                        callback_data=GradeCallback(
                            action="attendance_status", subject=subject, data="excused"
                        ).pack(),
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=GradeCallback(
                            action="add_attendance", subject=subject
                        ).pack(),
                    ),
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in attendance type selection handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при выборе типа занятия. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def handle_attendance_status_selection(
    callback: types.CallbackQuery, callback_data: GradeCallback, state: FSMContext
) -> None:
    """Сохранение статуса посещаемости."""
    await callback.answer()
    subject = callback_data.subject
    status = callback_data.data
    user_id = callback.from_user.id

    try:
        state_data = await state.get_data()
        lesson_type = state_data.get("lesson_type", "лекция")

        grade_service = GradeCalculatorService()

        # Определяем параметры для сохранения
        is_present = status == "present"
        is_excused = status == "excused"

        # Сохраняем посещаемость
        success = await grade_service.add_attendance(
            user_id=user_id,
            subject=subject,
            lesson_type=lesson_type,
            date=date.today(),
            is_present=is_present,
            is_excused=is_excused,
        )

        if success:
            status_text = {
                "present": "✅ Присутствовал",
                "absent": "❌ Отсутствовал",
                "excused": "🏥 По уважительной причине",
            }.get(status, "Неизвестно")

            await callback.message.edit_text(
                f"✅ **Посещаемость отмечена!**\n\n"
                f"📚 Предмет: {subject}\n"
                f"📅 Тип: {lesson_type}\n"
                f"👤 Статус: {status_text}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n\n"
                f"Данные учтены в расчете КНЛ/КНС.",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="📚 К предмету",
                                callback_data=GradeCallback(
                                    action="view_subject", subject=subject
                                ).pack(),
                            ),
                            types.InlineKeyboardButton(
                                text="🏠 В меню",
                                callback_data=MenuCallback(action="grades").pack(),
                            ),
                        ]
                    ]
                ),
            )
        else:
            await callback.message.edit_text(
                f"❌ Ошибка при сохранении посещаемости. Попробуйте позже.",
                reply_markup=get_grades_keyboard([]),
            )

        await state.clear()

    except Exception as e:
        logger.error(f"Error in attendance status selection handler: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при сохранении посещаемости. Попробуйте позже.",
            reply_markup=get_grades_keyboard([]),
        )


async def register_grade_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков оценок."""
    # Основные обработчики
    dp.callback_query.register(handle_grades_main, GradeCallback.filter())
    dp.callback_query.register(handle_subject_selection, GradeCallback.filter())
    dp.callback_query.register(handle_add_grade, GradeCallback.filter())
    dp.callback_query.register(handle_grade_type_selection, GradeCallback.filter())
    dp.callback_query.register(handle_grade_value_selection, GradeCallback.filter())
    dp.callback_query.register(handle_add_attendance, GradeCallback.filter())
    dp.callback_query.register(handle_attendance_type_selection, GradeCallback.filter())
    dp.callback_query.register(
        handle_attendance_status_selection, GradeCallback.filter()
    )
