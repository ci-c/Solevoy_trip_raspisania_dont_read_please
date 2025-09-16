"""
Система rate limiting для защиты от спама.
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class RateLimitConfig:
    """Конфигурация rate limiting."""
    max_requests: int
    time_window: int  # в секундах
    block_duration: int  # в секундах


class RateLimiter:
    """Rate limiter для защиты от спама."""
    
    # Конфигурации для разных типов действий
    CONFIGS = {
        "message": RateLimitConfig(max_requests=10, time_window=60, block_duration=300),
        "search": RateLimitConfig(max_requests=5, time_window=60, block_duration=300),
        "callback": RateLimitConfig(max_requests=20, time_window=60, block_duration=300),
        "start": RateLimitConfig(max_requests=3, time_window=60, block_duration=300),
    }
    
    def __init__(self):
        # user_id -> {action_type -> [timestamps]}
        self._requests: Dict[int, Dict[str, list]] = {}
        # user_id -> {action_type -> block_until}
        self._blocks: Dict[int, Dict[str, float]] = {}
    
    def _cleanup_old_requests(self, user_id: int, action_type: str) -> None:
        """Очистка старых запросов."""
        if user_id not in self._requests:
            return
        
        if action_type not in self._requests[user_id]:
            return
        
        config = self.CONFIGS.get(action_type)
        if not config:
            return
        
        current_time = time.time()
        cutoff_time = current_time - config.time_window
        
        # Удаляем старые запросы
        self._requests[user_id][action_type] = [
            timestamp for timestamp in self._requests[user_id][action_type]
            if timestamp > cutoff_time
        ]
    
    def _is_blocked(self, user_id: int, action_type: str) -> bool:
        """Проверка, заблокирован ли пользователь."""
        if user_id not in self._blocks:
            return False
        
        if action_type not in self._blocks[user_id]:
            return False
        
        current_time = time.time()
        block_until = self._blocks[user_id][action_type]
        
        if current_time < block_until:
            return True
        
        # Блокировка истекла, удаляем
        del self._blocks[user_id][action_type]
        if not self._blocks[user_id]:
            del self._blocks[user_id]
        
        return False
    
    def _block_user(self, user_id: int, action_type: str) -> None:
        """Блокировка пользователя."""
        config = self.CONFIGS.get(action_type)
        if not config:
            return
        
        current_time = time.time()
        block_until = current_time + config.block_duration
        
        if user_id not in self._blocks:
            self._blocks[user_id] = {}
        
        self._blocks[user_id][action_type] = block_until
        
        logger.warning(f"User {user_id} blocked for {action_type} until {block_until}")
    
    def check_rate_limit(self, user_id: int, action_type: str) -> Tuple[bool, Optional[str]]:
        """
        Проверка rate limit.
        
        Args:
            user_id: ID пользователя
            action_type: Тип действия
            
        Returns:
            (is_allowed, error_message)
        """
        config = self.CONFIGS.get(action_type)
        if not config:
            return True, None
        
        # Проверяем блокировку
        if self._is_blocked(user_id, action_type):
            remaining_time = int(self._blocks[user_id][action_type] - time.time())
            return False, f"Вы заблокированы на {remaining_time} секунд"
        
        # Очищаем старые запросы
        self._cleanup_old_requests(user_id, action_type)
        
        # Инициализируем структуры данных
        if user_id not in self._requests:
            self._requests[user_id] = {}
        if action_type not in self._requests[user_id]:
            self._requests[user_id][action_type] = []
        
        # Проверяем лимит
        current_requests = len(self._requests[user_id][action_type])
        if current_requests >= config.max_requests:
            # Блокируем пользователя
            self._block_user(user_id, action_type)
            return False, f"Превышен лимит запросов. Блокировка на {config.block_duration} секунд"
        
        # Добавляем текущий запрос
        self._requests[user_id][action_type].append(time.time())
        
        return True, None
    
    def get_remaining_requests(self, user_id: int, action_type: str) -> int:
        """Получить количество оставшихся запросов."""
        config = self.CONFIGS.get(action_type)
        if not config:
            return float('inf')
        
        self._cleanup_old_requests(user_id, action_type)
        
        if user_id not in self._requests or action_type not in self._requests[user_id]:
            return config.max_requests
        
        current_requests = len(self._requests[user_id][action_type])
        return max(0, config.max_requests - current_requests)
    
    def reset_user_limits(self, user_id: int) -> None:
        """Сброс лимитов для пользователя."""
        if user_id in self._requests:
            del self._requests[user_id]
        if user_id in self._blocks:
            del self._blocks[user_id]
        
        logger.info(f"Rate limits reset for user {user_id}")


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()


def rate_limit(action_type: str):
    """
    Декоратор для rate limiting.
    
    Args:
        action_type: Тип действия для rate limiting
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем user_id из аргументов
            user_id = None
            for arg in args:
                if hasattr(arg, 'from_user') and arg.from_user:
                    user_id = arg.from_user.id
                    break
                elif hasattr(arg, 'user_id'):
                    user_id = arg.user_id
                    break
            
            if user_id is None:
                logger.warning(f"Could not extract user_id for rate limiting in {func.__name__}")
                return await func(*args, **kwargs)
            
            # Проверяем rate limit
            is_allowed, error_message = rate_limiter.check_rate_limit(user_id, action_type)
            
            if not is_allowed:
                # Отправляем сообщение об ошибке
                for arg in args:
                    if hasattr(arg, 'answer'):
                        await arg.answer(f"⏱️ {error_message}")
                        return
                    elif hasattr(arg, 'edit_text'):
                        await arg.edit_text(f"⏱️ {error_message}")
                        return
                
                logger.warning(f"Rate limit exceeded for user {user_id}, action {action_type}")
                return
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_rate_limit_manual(user_id: int, action_type: str) -> Tuple[bool, Optional[str]]:
    """
    Ручная проверка rate limit.
    
    Args:
        user_id: ID пользователя
        action_type: Тип действия
        
    Returns:
        (is_allowed, error_message)
    """
    return rate_limiter.check_rate_limit(user_id, action_type)
