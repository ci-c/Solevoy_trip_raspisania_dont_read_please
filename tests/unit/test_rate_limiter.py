"""Tests for rate limiter."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    check_rate_limit_manual,
    rate_limit,
    rate_limiter,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_config_creation(self):
        """Test creating a rate limit config."""
        config = RateLimitConfig(
            max_requests=10, time_window=60, block_duration=300
        )

        assert config.max_requests == 10
        assert config.time_window == 60
        assert config.block_duration == 300


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()

        assert limiter._requests == {}
        assert limiter._blocks == {}

    def test_configs_exist(self):
        """Test that default configs exist."""
        configs = RateLimiter.CONFIGS

        assert "message" in configs
        assert "search" in configs
        assert "callback" in configs
        assert "start" in configs

    def test_check_rate_limit_first_request(self):
        """Test checking rate limit for first request."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        is_allowed, error_msg = limiter.check_rate_limit(user_id, action_type)

        assert is_allowed is True
        assert error_msg is None
        assert user_id in limiter._requests
        assert action_type in limiter._requests[user_id]
        assert len(limiter._requests[user_id][action_type]) == 1

    def test_check_rate_limit_within_limit(self):
        """Test checking rate limit within allowed requests."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        # Make 5 requests (well under the limit of 10)
        for _ in range(5):
            is_allowed, error_msg = limiter.check_rate_limit(user_id, action_type)
            assert is_allowed is True
            assert error_msg is None

    def test_check_rate_limit_exceeds_limit(self):
        """Test checking rate limit when exceeding max requests."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"
        config = limiter.CONFIGS["message"]

        # Make max_requests + 1 requests
        for i in range(config.max_requests):
            is_allowed, _ = limiter.check_rate_limit(user_id, action_type)
            if i < config.max_requests:
                assert is_allowed is True

        # This should exceed the limit
        is_allowed, error_msg = limiter.check_rate_limit(user_id, action_type)
        assert is_allowed is False
        assert error_msg is not None
        assert "Превышен лимит" in error_msg or "Блокировка" in error_msg

    def test_check_rate_limit_blocked_user(self):
        """Test checking rate limit for blocked user."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        # Block the user
        limiter._block_user(user_id, action_type)

        # Try to make a request
        is_allowed, error_msg = limiter.check_rate_limit(user_id, action_type)

        assert is_allowed is False
        assert error_msg is not None
        assert "заблокирован" in error_msg.lower()

    def test_check_rate_limit_unknown_action(self):
        """Test checking rate limit for unknown action type."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "unknown_action"

        is_allowed, error_msg = limiter.check_rate_limit(user_id, action_type)

        # Should allow unknown action types
        assert is_allowed is True
        assert error_msg is None

    def test_cleanup_old_requests(self):
        """Test cleanup of old requests."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"
        config = limiter.CONFIGS["message"]

        # Add old timestamp
        old_time = time.time() - config.time_window - 10
        limiter._requests[user_id] = {action_type: [old_time]}

        # Cleanup should remove old requests
        limiter._cleanup_old_requests(user_id, action_type)

        assert len(limiter._requests[user_id][action_type]) == 0

    def test_is_blocked_expired(self):
        """Test checking if block has expired."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        # Set expired block time
        limiter._blocks[user_id] = {action_type: time.time() - 10}

        is_blocked = limiter._is_blocked(user_id, action_type)

        # Block should have expired
        assert is_blocked is False
        assert user_id not in limiter._blocks

    def test_is_blocked_active(self):
        """Test checking if block is still active."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        # Set future block time
        limiter._blocks[user_id] = {action_type: time.time() + 100}

        is_blocked = limiter._is_blocked(user_id, action_type)

        # Block should still be active
        assert is_blocked is True
        assert user_id in limiter._blocks

    def test_block_user(self):
        """Test blocking a user."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        limiter._block_user(user_id, action_type)

        assert user_id in limiter._blocks
        assert action_type in limiter._blocks[user_id]
        assert limiter._blocks[user_id][action_type] > time.time()

    def test_get_remaining_requests_new_user(self):
        """Test getting remaining requests for new user."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"
        config = limiter.CONFIGS["message"]

        remaining = limiter.get_remaining_requests(user_id, action_type)

        assert remaining == config.max_requests

    def test_get_remaining_requests_after_some_requests(self):
        """Test getting remaining requests after making some requests."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"
        config = limiter.CONFIGS["message"]

        # Make 3 requests
        for _ in range(3):
            limiter.check_rate_limit(user_id, action_type)

        remaining = limiter.get_remaining_requests(user_id, action_type)

        assert remaining == config.max_requests - 3

    def test_get_remaining_requests_unknown_action(self):
        """Test getting remaining requests for unknown action."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "unknown"

        remaining = limiter.get_remaining_requests(user_id, action_type)

        # Should return large number for unknown action
        assert remaining == 999999

    def test_reset_user_limits(self):
        """Test resetting user limits."""
        limiter = RateLimiter()
        user_id = 12345
        action_type = "message"

        # Make some requests and block the user
        limiter.check_rate_limit(user_id, action_type)
        limiter._block_user(user_id, action_type)

        # Reset
        limiter.reset_user_limits(user_id)

        assert user_id not in limiter._requests
        assert user_id not in limiter._blocks

    def test_multiple_action_types(self):
        """Test handling multiple action types for same user."""
        limiter = RateLimiter()
        user_id = 12345

        # Make requests for different action types
        limiter.check_rate_limit(user_id, "message")
        limiter.check_rate_limit(user_id, "search")
        limiter.check_rate_limit(user_id, "callback")

        assert "message" in limiter._requests[user_id]
        assert "search" in limiter._requests[user_id]
        assert "callback" in limiter._requests[user_id]

    def test_multiple_users(self):
        """Test handling multiple users independently."""
        limiter = RateLimiter()
        user1 = 12345
        user2 = 67890
        action_type = "message"

        limiter.check_rate_limit(user1, action_type)
        limiter.check_rate_limit(user2, action_type)

        assert user1 in limiter._requests
        assert user2 in limiter._requests
        assert len(limiter._requests[user1][action_type]) == 1
        assert len(limiter._requests[user2][action_type]) == 1


def test_check_rate_limit_manual():
    """Test manual rate limit checking function."""
    # Reset global rate limiter
    rate_limiter._requests.clear()
    rate_limiter._blocks.clear()

    user_id = 99999
    action_type = "test"

    is_allowed, error_msg = check_rate_limit_manual(user_id, action_type)

    # Unknown action type should be allowed
    assert is_allowed is True
    assert error_msg is None


@pytest.mark.asyncio
class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""

    async def test_decorator_allows_request(self):
        """Test decorator allows request within limits."""

        @rate_limit("message")
        async def test_handler(message):
            return "success"

        mock_message = MagicMock()
        mock_message.from_user = MagicMock()
        mock_message.from_user.id = 11111

        # Reset rate limiter
        rate_limiter.reset_user_limits(11111)

        result = await test_handler(mock_message)

        assert result == "success"

    async def test_decorator_blocks_request(self):
        """Test decorator blocks request when limit exceeded."""

        @rate_limit("message")
        async def test_handler(message):
            return "success"

        mock_message = AsyncMock()
        mock_message.from_user = MagicMock()
        mock_message.from_user.id = 22222
        mock_message.answer = AsyncMock()

        # Reset and exhaust the limit
        rate_limiter.reset_user_limits(22222)
        config = rate_limiter.CONFIGS["message"]

        for _ in range(config.max_requests + 1):
            await test_handler(mock_message)

        # Should have called answer with error message
        assert mock_message.answer.called

    async def test_decorator_no_user_id(self):
        """Test decorator handles missing user_id gracefully."""

        @rate_limit("message")
        async def test_handler(obj):
            return "success"

        # Object without from_user attribute
        mock_obj = MagicMock()
        delattr(mock_obj, "from_user")

        result = await test_handler(mock_obj)

        # Should still execute the function
        assert result == "success"

    async def test_decorator_with_callback(self):
        """Test decorator with callback query."""

        @rate_limit("callback")
        async def test_handler(callback):
            return "success"

        mock_callback = AsyncMock()
        mock_callback.from_user = MagicMock()
        mock_callback.from_user.id = 33333
        mock_callback.answer = AsyncMock()

        # Reset rate limiter
        rate_limiter.reset_user_limits(33333)

        result = await test_handler(mock_callback)

        assert result == "success"

    async def test_decorator_extracts_user_id_from_attr(self):
        """Test decorator extracts user_id from user_id attribute."""

        @rate_limit("message")
        async def test_handler(obj):
            return "success"

        mock_obj = MagicMock()
        mock_obj.user_id = 44444

        # Reset rate limiter
        rate_limiter.reset_user_limits(44444)

        result = await test_handler(mock_obj)

        assert result == "success"
