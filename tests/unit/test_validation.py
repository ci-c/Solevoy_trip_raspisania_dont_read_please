"""Comprehensive tests for validation utilities."""

import pytest

from app.utils.validation import (
    InputValidator,
    ValidationError,
    validate_message,
    validate_user_input,
)


@pytest.mark.unit
class TestInputValidator:
    """Tests for InputValidator class."""

    def test_validate_telegram_username_valid(self):
        """Test valid Telegram usernames."""
        assert InputValidator.validate_telegram_username("username")
        assert InputValidator.validate_telegram_username("user_name123")
        assert InputValidator.validate_telegram_username("@username")
        assert InputValidator.validate_telegram_username("User123_NAME")

    def test_validate_telegram_username_invalid(self):
        """Test invalid Telegram usernames."""
        assert not InputValidator.validate_telegram_username("")
        assert not InputValidator.validate_telegram_username("usr")  # Too short
        assert not InputValidator.validate_telegram_username("u" * 40)  # Too long
        assert not InputValidator.validate_telegram_username("user-name")  # Invalid char
        assert not InputValidator.validate_telegram_username("user name")  # Space

    def test_validate_group_number_valid(self):
        """Test valid group numbers."""
        assert InputValidator.validate_group_number("101")
        assert InputValidator.validate_group_number("101а")
        assert InputValidator.validate_group_number("205Б")
        assert InputValidator.validate_group_number("1")
        assert InputValidator.validate_group_number("999в")

    def test_validate_group_number_invalid(self):
        """Test invalid group numbers."""
        assert not InputValidator.validate_group_number("")
        assert not InputValidator.validate_group_number("1000")  # Too long
        assert not InputValidator.validate_group_number("abc")
        assert not InputValidator.validate_group_number("101-а")

    def test_validate_student_id_valid(self):
        """Test valid student IDs."""
        assert InputValidator.validate_student_id("123456")
        assert InputValidator.validate_student_id("12345678")
        assert InputValidator.validate_student_id("2024001")

    def test_validate_student_id_invalid(self):
        """Test invalid student IDs."""
        assert not InputValidator.validate_student_id("")
        assert not InputValidator.validate_student_id("12345")  # Too short
        assert not InputValidator.validate_student_id("123456789")  # Too long
        assert not InputValidator.validate_student_id("abc123")
        assert not InputValidator.validate_student_id("12-3456")

    def test_validate_phone_valid(self):
        """Test valid phone numbers."""
        assert InputValidator.validate_phone("+79991234567")
        assert InputValidator.validate_phone("79991234567")
        assert InputValidator.validate_phone("+18001234567")
        assert InputValidator.validate_phone("12345678901")

    def test_validate_phone_invalid(self):
        """Test invalid phone numbers."""
        assert not InputValidator.validate_phone("")
        assert not InputValidator.validate_phone("1234")  # Too short
        assert not InputValidator.validate_phone("+7 (999) 123-45-67")  # Spaces
        assert not InputValidator.validate_phone("abc")

    def test_validate_message_length_valid(self):
        """Test valid message lengths."""
        assert InputValidator.validate_message_length("Short message")
        assert InputValidator.validate_message_length("A" * 4096)

    def test_validate_message_length_invalid(self):
        """Test invalid message lengths."""
        assert not InputValidator.validate_message_length("A" * 4097)
        assert not InputValidator.validate_message_length("A" * 10000)

    def test_validate_name_valid(self):
        """Test valid names."""
        assert InputValidator.validate_name("John Doe")
        assert InputValidator.validate_name("Иван Иванов")
        assert InputValidator.validate_name("A" * 100)

    def test_validate_name_invalid(self):
        """Test invalid names."""
        assert not InputValidator.validate_name("")
        assert not InputValidator.validate_name("   ")
        assert not InputValidator.validate_name("A" * 101)

    def test_sanitize_input_valid(self):
        """Test input sanitization."""
        assert InputValidator.sanitize_input("Hello World") == "Hello World"
        assert InputValidator.sanitize_input("  Test  ") == "Test"
        assert InputValidator.sanitize_input("Normal text 123") == "Normal text 123"

    def test_sanitize_input_removes_dangerous_chars(self):
        """Test sanitization removes dangerous characters."""
        assert InputValidator.sanitize_input('<script>alert("xss")</script>') == "scriptalert(xss)/script"
        assert InputValidator.sanitize_input('Test "quotes"') == "Test quotes"
        assert InputValidator.sanitize_input("Test 'quotes'") == "Test quotes"

    def test_sanitize_input_limits_length(self):
        """Test sanitization limits length."""
        long_text = "A" * 5000
        sanitized = InputValidator.sanitize_input(long_text)
        assert len(sanitized) == InputValidator.MAX_MESSAGE_LENGTH

    def test_sanitize_input_empty(self):
        """Test sanitization of empty input."""
        assert InputValidator.sanitize_input("") == ""
        assert InputValidator.sanitize_input(None) == ""

    def test_validate_search_query_valid(self):
        """Test valid search queries."""
        assert InputValidator.validate_search_query("group 101")
        assert InputValidator.validate_search_query("Иванов")
        assert InputValidator.validate_search_query("AB")

    def test_validate_search_query_invalid(self):
        """Test invalid search queries."""
        assert not InputValidator.validate_search_query("")
        assert not InputValidator.validate_search_query("A")  # Too short
        assert not InputValidator.validate_search_query("<script>")
        assert not InputValidator.validate_search_query("javascript:alert()")
        assert not InputValidator.validate_search_query("data:text/html")
        assert not InputValidator.validate_search_query("vbscript:msgbox()")
        assert not InputValidator.validate_search_query("onload=alert()")

    def test_validate_filters_valid(self):
        """Test valid filter dictionaries."""
        assert InputValidator.validate_filters({})
        assert InputValidator.validate_filters({"course": "1"})
        assert InputValidator.validate_filters({"course": "1", "speciality": "Лечебное дело"})
        assert InputValidator.validate_filters({"teacher": "Иванов", "subject": "Анатомия"})

    def test_validate_filters_invalid(self):
        """Test invalid filter dictionaries."""
        assert not InputValidator.validate_filters("not a dict")
        assert not InputValidator.validate_filters(["list"])
        assert not InputValidator.validate_filters({"unknown_key": "value"})
        assert not InputValidator.validate_filters({"course": "1", "invalid": "key"})


@pytest.mark.unit
class TestValidateUserInput:
    """Tests for validate_user_input function."""

    def test_validate_username_valid(self):
        """Test username validation."""
        result = validate_user_input("username", "test_user", required=True)
        assert result == "test_user"

    def test_validate_username_invalid(self):
        """Test username validation with invalid input."""
        with pytest.raises(ValidationError):
            validate_user_input("username", "usr", required=True)

    def test_validate_group_number_valid(self):
        """Test group number validation."""
        result = validate_user_input("group_number", "101а", required=True)
        assert result == "101а"

    def test_validate_group_number_invalid(self):
        """Test group number validation with invalid input."""
        with pytest.raises(ValidationError):
            validate_user_input("group_number", "invalid", required=True)

    def test_validate_student_id_valid(self):
        """Test student ID validation."""
        result = validate_user_input("student_id", "123456", required=True)
        assert result == "123456"

    def test_validate_student_id_invalid(self):
        """Test student ID validation with invalid input."""
        with pytest.raises(ValidationError):
            validate_user_input("student_id", "12", required=True)

    def test_validate_phone_valid(self):
        """Test phone validation."""
        result = validate_user_input("phone", "+79991234567", required=True)
        assert result == "+79991234567"

    def test_validate_phone_invalid(self):
        """Test phone validation with invalid input."""
        with pytest.raises(ValidationError):
            validate_user_input("phone", "123", required=True)

    def test_validate_name_valid(self):
        """Test name validation."""
        result = validate_user_input("name", "John Doe", required=True)
        assert result == "John Doe"

    def test_validate_name_invalid(self):
        """Test name validation with invalid input."""
        with pytest.raises(ValidationError):
            validate_user_input("name", "", required=True)

    def test_validate_search_query_valid(self):
        """Test search query validation."""
        result = validate_user_input("search_query", "test query", required=True)
        assert result == "test query"

    def test_validate_search_query_invalid(self):
        """Test search query validation with invalid input."""
        with pytest.raises(ValidationError):
            validate_user_input("search_query", "<script>", required=True)

    def test_validate_required_field_empty(self):
        """Test validation of required empty field."""
        with pytest.raises(ValidationError):
            validate_user_input("username", "", required=True)

    def test_validate_optional_field_empty(self):
        """Test validation of optional empty field."""
        result = validate_user_input("username", "", required=False)
        assert result == ""

        result = validate_user_input("name", None, required=False)
        assert result == ""

    def test_sanitization_during_validation(self):
        """Test that input is sanitized during validation."""
        result = validate_user_input("name", "  John Doe  ", required=True)
        assert result == "John Doe"

    def test_unknown_input_type(self):
        """Test validation with unknown input type."""
        # Should return sanitized value without specific validation
        result = validate_user_input("unknown_type", "test value", required=True)
        assert result == "test value"


@pytest.mark.unit
class TestValidateMessage:
    """Tests for validate_message function."""

    def test_validate_message_valid(self):
        """Test valid message validation."""
        result = validate_message("Hello, World!")
        assert result == "Hello, World!"

    def test_validate_message_empty(self):
        """Test empty message validation."""
        with pytest.raises(ValidationError):
            validate_message("")

    def test_validate_message_too_long(self):
        """Test message that's too long."""
        long_message = "A" * 5000
        with pytest.raises(ValidationError):
            validate_message(long_message)

    def test_validate_message_with_sanitization(self):
        """Test message validation with sanitization."""
        result = validate_message('Hello <script>alert("xss")</script>')
        assert "<script>" not in result
        assert "Hello scriptalert" in result

    def test_validate_message_whitespace(self):
        """Test message with whitespace."""
        result = validate_message("  Test Message  ")
        assert result == "Test Message"
