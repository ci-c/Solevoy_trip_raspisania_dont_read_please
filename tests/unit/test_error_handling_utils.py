"""Comprehensive tests for error handling utilities."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.utils.error_handling import (
    APIError,
    BotError,
    DatabaseError,
    ErrorHandler,
    SecurityError,
    UserError,
    format_error_for_user,
    handle_api_error,
    handle_database_error,
    log_error_context,
    safe_async_execute,
)
from app.utils.validation import ValidationError


@pytest.mark.unit
class TestErrorClasses:
    """Tests for custom error classes."""

    def test_bot_error(self):
        """Test BotError base class."""
        error = BotError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_database_error(self):
        """Test DatabaseError class."""
        error = DatabaseError("DB connection failed")
        assert str(error) == "DB connection failed"
        assert isinstance(error, BotError)

    def test_api_error(self):
        """Test APIError class."""
        error = APIError("API request failed")
        assert str(error) == "API request failed"
        assert isinstance(error, BotError)

    def test_user_error(self):
        """Test UserError class."""
        error = UserError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, BotError)

    def test_security_error(self):
        """Test SecurityError class."""
        error = SecurityError("Unauthorized access")
        assert str(error) == "Unauthorized access"
        assert isinstance(error, BotError)


@pytest.mark.asyncio
@pytest.mark.unit
class TestSafeAsyncExecute:
    """Tests for safe_async_execute decorator."""

    async def test_safe_async_execute_success(self):
        """Test decorator with successful execution."""
        @safe_async_execute()
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    async def test_safe_async_execute_validation_error(self):
        """Test decorator with ValidationError."""
        @safe_async_execute()
        async def test_func():
            msg = "Invalid data"
            raise ValidationError(msg)

        with pytest.raises(UserError):
            await test_func()

    async def test_safe_async_execute_database_error(self):
        """Test decorator with DatabaseError."""
        @safe_async_execute()
        async def test_func():
            msg = "DB error"
            raise DatabaseError(msg)

        result = await test_func()
        assert result is None

    async def test_safe_async_execute_database_error_reraise(self):
        """Test decorator with DatabaseError and reraise."""
        @safe_async_execute(reraise=True)
        async def test_func():
            msg = "DB error"
            raise DatabaseError(msg)

        with pytest.raises(DatabaseError):
            await test_func()

    async def test_safe_async_execute_api_error(self):
        """Test decorator with APIError."""
        @safe_async_execute()
        async def test_func():
            msg = "API error"
            raise APIError(msg)

        result = await test_func()
        assert result is None

    async def test_safe_async_execute_api_error_reraise(self):
        """Test decorator with APIError and reraise."""
        @safe_async_execute(reraise=True)
        async def test_func():
            msg = "API error"
            raise APIError(msg)

        with pytest.raises(APIError):
            await test_func()

    async def test_safe_async_execute_security_error(self):
        """Test decorator with SecurityError."""
        @safe_async_execute()
        async def test_func():
            msg = "Security error"
            raise SecurityError(msg)

        result = await test_func()
        assert result is None

    async def test_safe_async_execute_unknown_error(self):
        """Test decorator with unknown error."""
        @safe_async_execute()
        async def test_func():
            msg = "Unknown error"
            raise Exception(msg)

        result = await test_func()
        assert result is None

    async def test_safe_async_execute_no_logging(self):
        """Test decorator with logging disabled."""
        @safe_async_execute(log_error=False)
        async def test_func():
            msg = "Error"
            raise Exception(msg)

        result = await test_func()
        assert result is None

    async def test_safe_async_execute_custom_message(self):
        """Test decorator with custom error message."""
        @safe_async_execute(error_message="Custom error")
        async def test_func():
            msg = "Error"
            raise Exception(msg)

        result = await test_func()
        assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestHandleDatabaseError:
    """Tests for handle_database_error decorator."""

    async def test_handle_database_error_success(self):
        """Test decorator with successful execution."""
        @handle_database_error
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    async def test_handle_database_error_exception(self):
        """Test decorator with exception."""
        @handle_database_error
        async def test_func():
            msg = "DB connection lost"
            raise Exception(msg)

        with pytest.raises(DatabaseError):
            await test_func()


@pytest.mark.asyncio
@pytest.mark.unit
class TestHandleAPIError:
    """Tests for handle_api_error decorator."""

    async def test_handle_api_error_success(self):
        """Test decorator with successful execution."""
        @handle_api_error
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    async def test_handle_api_error_exception(self):
        """Test decorator with exception."""
        @handle_api_error
        async def test_func():
            msg = "API timeout"
            raise Exception(msg)

        with pytest.raises(APIError):
            await test_func()


@pytest.mark.unit
class TestFormatErrorForUser:
    """Tests for format_error_for_user function."""

    def test_format_user_error(self):
        """Test formatting UserError."""
        error = UserError("Invalid input")
        result = format_error_for_user(error)
        assert result == "❌ Invalid input"

    def test_format_database_error(self):
        """Test formatting DatabaseError."""
        error = DatabaseError("DB error")
        result = format_error_for_user(error)
        assert "базы данных" in result.lower() or "database" in result.lower()

    def test_format_api_error(self):
        """Test formatting APIError."""
        error = APIError("API error")
        result = format_error_for_user(error)
        assert "сервис" in result.lower() or "api" in result.lower()

    def test_format_security_error(self):
        """Test formatting SecurityError."""
        error = SecurityError("Security error")
        result = format_error_for_user(error)
        assert "безопасност" in result.lower() or "security" in result.lower()

    def test_format_unknown_error(self):
        """Test formatting unknown error."""
        error = Exception("Unknown error")
        result = format_error_for_user(error)
        assert "❌" in result
        assert "ошибка" in result.lower() or "error" in result.lower()


@pytest.mark.unit
class TestLogErrorContext:
    """Tests for log_error_context function."""

    def test_log_error_context_minimal(self):
        """Test logging error context with minimal data."""
        # Should not raise exception
        log_error_context("test_function")

    def test_log_error_context_with_user(self):
        """Test logging error context with user ID."""
        log_error_context("test_function", user_id=12345)

    def test_log_error_context_with_additional_data(self):
        """Test logging error context with additional data."""
        log_error_context(
            "test_function",
            user_id=12345,
            additional_data={"action": "test", "param": "value"}
        )


@pytest.mark.asyncio
@pytest.mark.unit
class TestErrorHandler:
    """Tests for ErrorHandler class."""

    async def test_handle_validation_error(self):
        """Test handling ValidationError."""
        message = MagicMock()
        message.answer = AsyncMock()

        error = ValidationError("Invalid data")
        await ErrorHandler.handle_validation_error(error, message)

        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]

    async def test_handle_database_error(self):
        """Test handling DatabaseError."""
        message = MagicMock()
        message.answer = AsyncMock()

        error = DatabaseError("DB connection failed")
        await ErrorHandler.handle_database_error(error, message)

        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]
        assert "баз" in message.answer.call_args[0][0].lower() or "database" in message.answer.call_args[0][0].lower()

    async def test_handle_api_error(self):
        """Test handling APIError."""
        message = MagicMock()
        message.answer = AsyncMock()

        error = APIError("API timeout")
        await ErrorHandler.handle_api_error(error, message)

        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]

    async def test_handle_security_error(self):
        """Test handling SecurityError."""
        message = MagicMock()
        message.answer = AsyncMock()

        error = SecurityError("Unauthorized")
        await ErrorHandler.handle_security_error(error, message)

        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]

    async def test_handle_unknown_error(self):
        """Test handling unknown error."""
        message = MagicMock()
        message.answer = AsyncMock()

        error = Exception("Something went wrong")
        await ErrorHandler.handle_unknown_error(error, message)

        message.answer.assert_called_once()
        assert "❌" in message.answer.call_args[0][0]

    async def test_error_handler_all_methods(self):
        """Test all ErrorHandler methods can be called."""
        message = MagicMock()
        message.answer = AsyncMock()

        # Test all error handlers
        await ErrorHandler.handle_validation_error(ValidationError("test"), message)
        await ErrorHandler.handle_database_error(DatabaseError("test"), message)
        await ErrorHandler.handle_api_error(APIError("test"), message)
        await ErrorHandler.handle_security_error(SecurityError("test"), message)
        await ErrorHandler.handle_unknown_error(Exception("test"), message)

        # All should have been called
        assert message.answer.call_count == 5


@pytest.mark.asyncio
@pytest.mark.unit
class TestDecoratorChaining:
    """Tests for chaining decorators."""

    async def test_chained_decorators(self):
        """Test chaining multiple decorators."""
        @safe_async_execute()
        @handle_database_error
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    async def test_chained_decorators_with_error(self):
        """Test chained decorators with error."""
        @safe_async_execute()
        async def test_func():
            msg = "DB error"
            raise DatabaseError(msg)

        result = await test_func()
        assert result is None
