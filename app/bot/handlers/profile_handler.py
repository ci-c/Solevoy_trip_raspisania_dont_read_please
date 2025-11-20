"""Обработчик настройки профиля."""

from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import ProfileCallback
from app.bot.keyboards import get_main_menu_keyboard, get_profile_setup_keyboard
from app.bot.states import ProfileSetup
from app.services.user_service import UserService

# from ...services.education_service import EducationService  # Пока не используется


async def handle_profile_setup(
    callback: types.CallbackQuery, callback_data: ProfileCallback, state: FSMContext,
) -> None:
    """Обработчик настройки профиля."""
    await callback.answer()

    if callback_data.action == "confirm":
        await confirm_profile_setup(callback, state)
    else:
        # Остальные действия профиля
        await state.update_data(**{callback_data.action: callback_data.value})

        # Переход к следующему шагу
        if callback_data.action == "speciality":
            await state.set_state(ProfileSetup.selecting_course)
            courses = ["1", "2", "3", "4", "5", "6"]
            keyboard = get_profile_setup_keyboard("course", courses)
            await callback.message.edit_text("Выберите курс:", reply_markup=keyboard)


async def confirm_profile_setup(
    callback: types.CallbackQuery, state: FSMContext,
) -> None:
    """Подтверждение настройки профиля."""
    try:
        data = await state.get_data()

        user_service = UserService()

        # Получаем пользователя
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.message.edit_text("❌ Ошибка: пользователь не найден")
            return

        # Создаем профиль студента
        from app.models.user import StudentProfile

        profile = StudentProfile(
            user_id=user.id,
            group_id=None,  # TODO: связать с group_id из БД
            student_id=None,
            preferred_format="xlsx",
        )

        # Сохраняем профиль
        await user_service.create_or_update_profile(profile)

        # Получаем обновленного пользователя с профилем
        updated_user = await user_service.get_user_by_telegram_id(callback.from_user.id)

        await state.clear()
        await state.set_state(ProfileSetup.confirmation)

        await callback.message.edit_text(
            f"✅ Профиль сохранен!\n\n"
            f"👤 {callback.from_user.full_name}\n"
            f"🎓 {data.get('speciality', 'Не указана')}\n"
            f"📚 {data.get('course', 'Не указан')} курс\n\n"
            f"Теперь вы можете пользоваться всеми функциями бота!",
            reply_markup=get_main_menu_keyboard(updated_user),
        )

    except Exception as e:
        logger.error(f"Error confirming profile setup: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при сохранении профиля. Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard(None),
        )


async def register_profile_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков профиля."""
    dp.callback_query.register(handle_profile_setup, ProfileCallback.filter())
