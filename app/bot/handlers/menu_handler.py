"""Обработчик главного меню."""

from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import MenuCallback
from app.bot.keyboards import get_group_search_keyboard, get_main_menu_keyboard
from app.bot.states import GroupSearchStates
from app.services.user_service import UserService
from app.utils.logger import log_user_action


async def handle_menu(
    callback: types.CallbackQuery, callback_data: MenuCallback, state: FSMContext,
) -> None:
    """Обработчик главного меню."""
    await callback.answer()
    action = callback_data.action

    log_user_action(
        user_id=callback.from_user.id,
        action=f"menu_{action}",
        details={"callback_data": callback_data.model_dump()},
    )

    try:
        user_service = UserService()
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)

        if action == "home":
            await callback.message.edit_text(
                f"🏠 **Главное меню**\n\n"
                f"👋 Добро пожаловать, {callback.from_user.first_name}!\n\n"
                f"Выберите действие:",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "setup_profile":
            await callback.message.edit_text(
                "🎓 **Настройка профиля**\n\n"
                "🚧 В разработке...\n"
                "Пока используйте разовый поиск расписания.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "my_schedule":
            if not user or not hasattr(user, "profile") or not user.profile:
                await callback.message.edit_text(
                    "❌ Для просмотра персонального расписания необходимо настроить профиль.\n\n"
                    'Нажмите "🎓 Настроить профиль" для продолжения.',
                    reply_markup=get_main_menu_keyboard(user),
                )
                return

            await callback.message.edit_text(
                "📅 **Мое расписание**\n\n"
                "🚧 В разработке...\n"
                "Используйте поиск группы для просмотра расписания.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "search_group":
            await state.set_state(GroupSearchStates.choosing_search_type)
            await callback.message.edit_text(
                "👥 **Поиск группы**\n\nВыберите тип поиска:",
                reply_markup=get_group_search_keyboard(),
            )

        elif action == "search":
            await callback.message.edit_text(
                "🔍 **Разовый поиск расписания**\n\n"
                "🚧 Старая система поиска в процессе миграции...\n"
                'Используйте "👥 Найти группу" для поиска расписания.',
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "applications":
            await callback.message.edit_text(
                "📝 **Заявления**\n\n"
                "🚧 В разработке...\n"
                "Функция подачи заявлений будет доступна в ближайших обновлениях.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "diary":
            await callback.message.edit_text(
                "📊 **Мой дневник**\n\n"
                "🚧 В разработке...\n"
                "Электронный дневник будет доступен после настройки профиля.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "attestation":
            await callback.message.edit_text(
                "📚 **Аттестация**\n\n"
                "🚧 В разработке...\n"
                "Информация об аттестации будет доступна в ближайших обновлениях.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "grades":
            # Перенаправляем на обработчик оценок
            from app.bot.callbacks import GradeCallback
            from app.bot.handlers.grade_handler import handle_grades_main

            grade_callback = GradeCallback(action="main")
            await handle_grades_main(callback, grade_callback, state)

        elif action == "reminders":
            await callback.message.edit_text(
                "🔔 **Напоминания**\n\n"
                "🚧 В разработке...\n"
                "Система напоминаний о парах и экзаменах будет добавлена позже.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "settings":
            await callback.message.edit_text(
                "⚙️ **Настройки**\n\n"
                "🚧 В разработке...\n"
                "Настройки уведомлений и формата экспорта будут доступны позже.",
                reply_markup=get_main_menu_keyboard(user),
            )

        elif action == "retry":
            await callback.message.edit_text(
                "🔄 **Повторная попытка**\n\nПопробуйте снова:",
                reply_markup=get_main_menu_keyboard(user),
            )

        else:
            logger.warning(f"Unknown menu action: {action}")
            await callback.message.edit_text(
                "❓ Неизвестное действие. Попробуйте еще раз.",
                reply_markup=get_main_menu_keyboard(user),
            )

    except Exception as e:
        logger.error(f"Error in menu handler: {e}")
        await callback.message.edit_text(
            "❌ Ошибка в обработке меню. Попробуйте /start для перезапуска.",
            reply_markup=get_main_menu_keyboard(None),
        )


async def register_menu_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков меню."""
    dp.callback_query.register(handle_menu, MenuCallback.filter())
