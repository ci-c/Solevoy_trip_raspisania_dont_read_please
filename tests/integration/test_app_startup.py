"""
Integration tests for application startup and initialization.

Tests aligned with Constitution Principle IV: Tests Before Code
"""

import os

import pytest


class TestApplicationStartup:
    """Test application startup and environment validation."""

    def test_secrets_module_imports(self):
        """Test that secrets module can be imported without errors."""
        from app.utils.secrets import (
            get_api_base_url,
            secrets_manager,
            validate_environment,
        )

        assert validate_environment is not None
        assert secrets_manager is not None
        assert get_api_base_url is not None

    def test_main_module_imports(self):
        """Test that main module can be imported without errors."""
        import main

        assert main is not None
        assert hasattr(main, "main")
        assert hasattr(main, "setup_app")

    def test_environment_validation_with_valid_token(self, monkeypatch):
        """Test environment validation succeeds with valid BOT_TOKEN."""
        from app.utils.secrets import secrets_manager, validate_environment

        # Clear secrets cache to ensure fresh read
        secrets_manager._cache.clear()

        # Set valid test token (secret must be exactly 35 characters)
        monkeypatch.setenv("BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789")

        result = validate_environment()
        assert result is True

    def test_environment_validation_with_invalid_token_format(self, monkeypatch):
        """Test environment validation fails with invalid token format."""
        from app.utils.secrets import secrets_manager, validate_environment

        # Clear secrets cache to ensure fresh read
        secrets_manager._cache.clear()

        # Set invalid token format
        monkeypatch.setenv("BOT_TOKEN", "invalid_token_format")

        result = validate_environment()
        assert result is False

    def test_environment_validation_without_token(self, monkeypatch):
        """Test environment validation fails without BOT_TOKEN."""
        from app.utils.secrets import secrets_manager, validate_environment

        # Clear secrets cache to ensure fresh read
        secrets_manager._cache.clear()

        # Remove token from environment
        monkeypatch.delenv("BOT_TOKEN", raising=False)

        result = validate_environment()
        assert result is False

    def test_secrets_manager_get_with_default(self):
        """Test secrets manager returns default for missing variable."""
        from app.utils.secrets import secrets_manager

        result = secrets_manager.get("NONEXISTENT_VAR", default="default_value")
        assert result == "default_value"

    def test_secrets_manager_redaction(self):
        """Test that secrets are properly redacted in logs."""
        from app.utils.secrets import secrets_manager

        # Test BOT_TOKEN redaction
        text_with_token = "BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345"
        redacted = secrets_manager.redact(text_with_token)

        assert "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz12345" not in redacted
        assert "REDACTED" in redacted

    def test_get_api_base_url_default(self):
        """Test API base URL returns correct default."""
        from app.utils.secrets import get_api_base_url

        # Clear any existing env var
        if "API_BASE_URL" in os.environ:
            del os.environ["API_BASE_URL"]

        url = get_api_base_url()
        assert url == "https://frsview.szgmu.ru/api"

    def test_get_database_url_default(self):
        """Test database URL returns correct default."""
        from app.utils.secrets import get_database_url

        # Clear any existing env var
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        url = get_database_url()
        assert url == "sqlite+aiosqlite:///./data/szgmu_bot.db"

    def test_get_log_level_default(self):
        """Test log level returns correct default."""
        from app.utils.secrets import get_log_level

        # Clear any existing env var
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]

        level = get_log_level()
        assert level == "INFO"

    def test_get_log_level_invalid_value(self):
        """Test log level returns default for invalid value."""
        from app.utils.secrets import get_log_level

        os.environ["LOG_LEVEL"] = "INVALID_LEVEL"

        level = get_log_level()
        assert level == "INFO"  # Should return default

    def test_all_handler_modules_import(self):
        """Test that all handler modules can be imported."""
        # Import all handler modules to ensure no undefined names
        from app.bot.handlers import (
            grade_handler,
            group_setup_handler,
            main_menu_handler,
            profile_handler,
            start_handler,
        )

        assert start_handler is not None
        assert main_menu_handler is not None
        assert group_setup_handler is not None
        assert profile_handler is not None
        assert grade_handler is not None

    def test_group_search_callback_defined(self):
        """Test that GroupSearchCallback is properly defined and importable."""
        from app.bot.callbacks import GroupSearchCallback

        assert GroupSearchCallback is not None

        # Test that it can be instantiated
        callback = GroupSearchCallback(action="test")
        assert callback.action == "test"

    def test_all_services_import(self):
        """Test that all service modules can be imported."""
        from app.services import (
            faculty_service,
            group_service,
            schedule_service,
            user_service,
        )

        assert user_service is not None
        assert schedule_service is not None
        assert group_service is not None
        assert faculty_service is not None


@pytest.mark.integration
class TestEnvironmentConfiguration:
    """Test environment configuration and .env.example."""

    def test_env_example_exists(self):
        """Test that .env.example file exists."""
        import os.path

        assert os.path.exists(".env.example")

    def test_env_example_contains_bot_token(self):
        """Test that .env.example documents BOT_TOKEN."""
        with open(".env.example") as f:
            content = f.read()

        assert "BOT_TOKEN" in content

    def test_env_example_contains_database_url(self):
        """Test that .env.example documents DATABASE_URL."""
        with open(".env.example") as f:
            content = f.read()

        assert "DATABASE_URL" in content

    def test_env_example_contains_log_level(self):
        """Test that .env.example documents LOG_LEVEL."""
        with open(".env.example") as f:
            content = f.read()

        assert "LOG_LEVEL" in content
