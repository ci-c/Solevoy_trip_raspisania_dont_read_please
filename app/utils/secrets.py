"""
Secrets and Environment Management Module

Provides secure access to environment variables, validation,
and secret redaction for logging.

Aligned with Constitution Principle V: Operational Transparency & Resilience
"""

import os
import re
from typing import Any, Dict, List, Optional

from loguru import logger


class SecretsManager:
    """Manages environment variables and secrets with validation and redaction."""

    # Patterns for detecting secrets in logs
    SECRET_PATTERNS = [
        (re.compile(r'(BOT_TOKEN=)([^\s]+)'), r'\1***REDACTED***'),
        (re.compile(r'(token["\']?\s*[:=]\s*["\']?)([^"\'\\s]+)', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(\d{10}:[A-Za-z0-9_-]{35})'), r'***REDACTED_BOT_TOKEN***'),  # Telegram bot token pattern
    ]

    def __init__(self) -> None:
        """Initialize secrets manager."""
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """
        Get environment variable with optional caching.

        Args:
            key: Environment variable name
            default: Default value if not found
            required: If True, raises error when variable is missing

        Returns:
            Environment variable value or default

        Raises:
            ValueError: If required variable is missing
        """
        if key in self._cache:
            return self._cache[key]

        value = os.getenv(key, default)

        if required and value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")

        if value is not None:
            self._cache[key] = value

        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')

    def get_int(self, key: str, default: int = 0) -> int:
        """Get environment variable as integer."""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}, using default {default}")
            return default

    def redact(self, text: str) -> str:
        """
        Redact secrets from text for safe logging.

        Args:
            text: Text potentially containing secrets

        Returns:
            Text with secrets redacted
        """
        result = text
        for pattern, replacement in self.SECRET_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def get_all_required(self) -> Dict[str, str]:
        """Get all required environment variables."""
        return {
            'BOT_TOKEN': self.get('BOT_TOKEN', required=True),
            'DATABASE_URL': self.get('DATABASE_URL', default='sqlite+aiosqlite:///./data/szgmu_bot.db'),
            'LOG_LEVEL': self.get('LOG_LEVEL', default='INFO'),
        }


# Global secrets manager instance
secrets_manager = SecretsManager()


def validate_environment() -> bool:
    """
    Validate required environment variables are present.

    Returns:
        True if all required variables are valid, False otherwise
    """
    try:
        # Check BOT_TOKEN
        bot_token = secrets_manager.get('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN environment variable is required")
            return False

        # Validate BOT_TOKEN format (Telegram bot token pattern)
        # Format: <bot_id>:<secret> where bot_id is ~10 digits and secret is ~35 characters
        token_pattern = re.compile(r'^\d{8,11}:[A-Za-z0-9_-]{35}$')
        if not token_pattern.match(bot_token):
            logger.error(
                "BOT_TOKEN format is invalid. Expected format: <bot_id>:<secret>"
            )
            logger.error(
                "Example: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
            )
            return False

        # Check optional but important variables
        database_url = secrets_manager.get(
            'DATABASE_URL',
            default='sqlite+aiosqlite:///./data/szgmu_bot.db'
        )
        log_level = secrets_manager.get('LOG_LEVEL', default='INFO')

        logger.info(f"Environment validation successful")
        logger.info(f"Database URL: {database_url}")
        logger.info(f"Log level: {log_level}")
        logger.info(f"BOT_TOKEN: {'*' * 10}[REDACTED]")

        return True

    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during environment validation: {e}")
        return False


def get_api_base_url() -> str:
    """
    Get API base URL from environment or config.

    Returns:
        API base URL

    Note:
        Defaults to SZGMU API URL if not specified in environment.
        This supports Constitution Principle I: Canonical Schedule Data Discipline
    """
    return secrets_manager.get(
        'API_BASE_URL',
        default='https://frsview.szgmu.ru/api'
    )


def get_database_url() -> str:
    """
    Get database URL from environment.

    Returns:
        Database connection URL
    """
    return secrets_manager.get(
        'DATABASE_URL',
        default='sqlite+aiosqlite:///./data/szgmu_bot.db'
    )


def get_log_level() -> str:
    """
    Get logging level from environment.

    Returns:
        Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = secrets_manager.get('LOG_LEVEL', default='INFO').upper()
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    if level not in valid_levels:
        logger.warning(
            f"Invalid LOG_LEVEL '{level}', using default 'INFO'. "
            f"Valid levels: {', '.join(valid_levels)}"
        )
        return 'INFO'

    return level


def get_required_env_vars() -> List[str]:
    """
    Get list of required environment variables.

    Returns:
        List of required variable names
    """
    return ['BOT_TOKEN']


def get_optional_env_vars() -> Dict[str, str]:
    """
    Get dictionary of optional environment variables with defaults.

    Returns:
        Dictionary mapping variable names to default values
    """
    return {
        'DATABASE_URL': 'sqlite+aiosqlite:///./data/szgmu_bot.db',
        'LOG_LEVEL': 'INFO',
        'API_BASE_URL': 'https://frsview.szgmu.ru/api',
    }
