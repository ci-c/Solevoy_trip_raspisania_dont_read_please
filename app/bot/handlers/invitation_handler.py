# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Обработчики для системы инвайтов и контроля доступа."""


from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.bot.callbacks import MenuCallback, InvitationCallback
from app.bot.keyboards import (
    get_main_menu_keyboard,
    get_invitation_keyboard,
    get_admin_invitation_keyboard,
)
from app.bot.states import InvitationStates
from app.services.invitation_service import InvitationService
from app.services.user_service import UserService
from app.models.user import AccessLevel


async def handle_invitation_main(
    callback: types.CallbackQuery, callback_data: InvitationCallback, state: FSMContext
) -> None:
    """Главное меню системы инвайтов."""
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

        InvitationService()

        # Проверяем права пользователя
        if user.access_level in [AccessLevel.ADMIN, AccessLevel.TESTER]:
            # Админ/тестер может создавать инвайты
            text = "🎫 **Система инвайтов**\n\n"
            text += f"👤 Ваш уровень доступа: {user.access_level.value}\n\n"
            text += "Вы можете создавать инвайты для других пользователей."

            await callback.message.edit_text(
                text,
                reply_markup=get_admin_invitation_keyboard(),
            )
        else:
            # Обычный пользователь может только использовать инвайты
            text = "🎫 **Система инвайтов**\n\n"
            text += f"👤 Ваш уровень доступа: {user.access_level.value}\n\n"
            text += (
                "Введите код инвайта для получения доступа к дополнительным функциям."
            )

            await state.set_state(InvitationStates.entering_code)
            await callback.message.edit_text(
                text,
                reply_markup=get_invitation_keyboard(),
            )

    except Exception as e:
        logger.error(f"Error in invitation main handler: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке системы инвайтов. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def handle_create_invitation(
    callback: types.CallbackQuery, callback_data: InvitationCallback, state: FSMContext
) -> None:
    """Создание нового инвайта."""
    await callback.answer()
    user_id = callback.from_user.id

    try:
        user_service = UserService()
        user = await user_service.get_user_by_telegram_id(user_id)

        if not user or user.access_level not in [AccessLevel.ADMIN, AccessLevel.TESTER]:
            await callback.message.edit_text(
                "❌ У вас нет прав для создания инвайтов.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        invitation_service = InvitationService()

        # Создаем инвайт
        invitation = await invitation_service.create_invitation(
            created_by=user_id,
            access_level=AccessLevel.BASIC,
            max_uses=5,
            expires_in_days=30,
            metadata=f"Created by {user.full_name or 'Unknown'}",
        )

        text = "✅ **Инвайт создан!**\n\n"
        text += f"🎫 **Код инвайта:** `{invitation.code}`\n"
        text += f"👥 **Уровень доступа:** {invitation.access_level.value}\n"
        text += (
            f"🔢 **Максимум использований:** {invitation.max_uses or 'Неограниченно'}\n"
        )
        text += f"⏰ **Действует до:** {invitation.expires_at.strftime('%d.%m.%Y %H:%M') if invitation.expires_at else 'Бессрочно'}\n\n"
        text += "Поделитесь этим кодом с пользователями для предоставления доступа."

        await callback.message.edit_text(
            text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="📋 Мои инвайты",
                            callback_data=InvitationCallback(action="list").pack(),
                        ),
                        types.InlineKeyboardButton(
                            text="➕ Создать еще",
                            callback_data=InvitationCallback(action="create").pack(),
                        ),
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="🏠 В меню",
                            callback_data=MenuCallback(action="home").pack(),
                        ),
                    ],
                ]
            ),
        )

    except Exception as e:
        logger.error(f"Error in create invitation handler: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при создании инвайта. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def handle_list_invitations(
    callback: types.CallbackQuery, callback_data: InvitationCallback, state: FSMContext
) -> None:
    """Список инвайтов пользователя."""
    await callback.answer()
    user_id = callback.from_user.id

    try:
        user_service = UserService()
        user = await user_service.get_user_by_telegram_id(user_id)

        if not user or user.access_level not in [AccessLevel.ADMIN, AccessLevel.TESTER]:
            await callback.message.edit_text(
                "❌ У вас нет прав для просмотра инвайтов.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        invitation_service = InvitationService()
        invitations = await invitation_service.get_user_invitations(user_id)

        if not invitations:
            text = "📋 **Мои инвайты**\n\n"
            text += "У вас пока нет созданных инвайтов."
        else:
            text = "📋 **Мои инвайты**\n\n"
            for i, invitation in enumerate(invitations[:10], 1):  # Показываем первые 10
                status = "✅ Активен" if invitation.is_active else "❌ Неактивен"
                uses = f"{invitation.current_uses}/{invitation.max_uses or '∞'}"
                expires = (
                    invitation.expires_at.strftime("%d.%m.%Y")
                    if invitation.expires_at
                    else "Бессрочно"
                )

                text += f"**{i}. {invitation.code}**\n"
                text += f"   • Уровень: {invitation.access_level.value}\n"
                text += f"   • Использований: {uses}\n"
                text += f"   • Истекает: {expires}\n"
                text += f"   • Статус: {status}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="➕ Создать новый",
                            callback_data=InvitationCallback(action="create").pack(),
                        ),
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data=InvitationCallback(action="main").pack(),
                        ),
                    ],
                ]
            ),
        )

    except Exception as e:
        logger.error(f"Error in list invitations handler: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке инвайтов. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def handle_use_invitation(
    callback: types.CallbackQuery, callback_data: InvitationCallback, state: FSMContext
) -> None:
    """Использование инвайта."""
    await callback.answer()

    try:
        await state.set_state(InvitationStates.entering_code)

        text = "🎫 **Использовать инвайт**\n\n"
        text += "Введите код инвайта, который вы получили:\n\n"
        text += "Пример: `ABC12345`"

        await callback.message.edit_text(
            text,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="❌ Отмена",
                            callback_data=InvitationCallback(action="main").pack(),
                        ),
                    ]
                ]
            ),
        )

    except Exception as e:
        logger.error(f"Error in use invitation handler: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при использовании инвайта. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def process_invitation_code(message: types.Message, state: FSMContext) -> None:
    """Обработка введенного кода инвайта."""
    code = message.text.strip().upper()
    user_id = message.from_user.id

    try:
        invitation_service = InvitationService()
        user_service = UserService()

        # Проверяем валидность инвайта
        invitation = await invitation_service.validate_invitation(code)

        if not invitation:
            await message.answer(
                "❌ **Неверный код инвайта**\n\n"
                "Проверьте правильность введенного кода и попробуйте снова.",
                reply_markup=get_invitation_keyboard(),
            )
            return

        # Используем инвайт
        success = await invitation_service.use_invitation(code, user_id)

        if success:
            # Обновляем уровень доступа пользователя
            user = await user_service.get_user_by_telegram_id(user_id)
            if user:
                user.access_level = invitation.access_level
                await user_service.update_user(user)

            await message.answer(
                f"✅ **Инвайт успешно использован!**\n\n"
                f"🎫 Код: `{code}`\n"
                f"👥 Уровень доступа: {invitation.access_level.value}\n\n"
                f"Теперь вам доступны дополнительные функции бота!",
                reply_markup=get_main_menu_keyboard(user),
            )
        else:
            await message.answer(
                "❌ **Ошибка при использовании инвайта**\n\n"
                "Инвайт не может быть использован. Возможные причины:\n"
                "• Инвайт уже использован максимальное количество раз\n"
                "• Инвайт истек\n"
                "• Инвайт отозван\n\n"
                "Попробуйте другой код или обратитесь к администратору.",
                reply_markup=get_invitation_keyboard(),
            )

        await state.clear()

    except Exception as e:
        logger.error(f"Error processing invitation code: {e}")
        await message.answer(
            "❌ Ошибка при обработке кода инвайта. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(),
        )


async def register_invitation_handlers(dp: Dispatcher) -> None:
    """Регистрация обработчиков инвайтов."""
    # Основные обработчики
    dp.callback_query.register(handle_invitation_main, InvitationCallback.filter())
    dp.callback_query.register(handle_create_invitation, InvitationCallback.filter())
    dp.callback_query.register(handle_list_invitations, InvitationCallback.filter())
    dp.callback_query.register(handle_use_invitation, InvitationCallback.filter())

    # Обработка ввода кода инвайта
    dp.message.register(
        process_invitation_code, StateFilter(InvitationStates.entering_code)
    )
