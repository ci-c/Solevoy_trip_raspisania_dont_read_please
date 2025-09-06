"""
Модули Telegram бота.
"""

from .main import create_bot_app
from .handlers import register_handlers

__all__ = ["create_bot_app", "register_handlers"]
