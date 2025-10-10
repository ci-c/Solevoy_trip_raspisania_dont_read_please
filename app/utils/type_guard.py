# Copyright (c) 2024 SZGMU Bot Project

"""Система проверки типов во время выполнения для предотвращения runtime ошибок."""

from typing import Any, TypeVar, Type, Union, get_origin, get_args, Callable
import inspect
from functools import wraps

T = TypeVar("T")


def type_check(value: Any, expected_type: Type[T]) -> bool:
    """Проверить тип значения во время выполнения."""
    if expected_type is Any:
        return True

    # Обработка Union типов
    origin = get_origin(expected_type)
    if origin is Union:
        args = get_args(expected_type)
        return any(type_check(value, arg) for arg in args)

    # Обработка встроенных типов
    if expected_type in (int, str, float, bool, list, dict, tuple, set):
        return isinstance(value, expected_type)

    # Обработка generic типов (list[str], dict[str, int], etc.)
    if origin is not None:
        if not isinstance(value, origin):
            return False

        args = get_args(expected_type)
        if not args:
            return True

        # Для list[Type] проверяем элементы
        if origin is list and len(args) == 1:
            return all(type_check(item, args[0]) for item in value)

        # Для dict[KeyType, ValueType] проверяем ключи и значения
        if origin is dict and len(args) == 2:
            key_type, value_type = args
            return all(
                type_check(key, key_type) and type_check(val, value_type)
                for key, val in value.items()
            )

    # Обработка пользовательских типов
    return isinstance(value, expected_type)


def runtime_type_check(func: Callable) -> Callable:
    """Декоратор для проверки типов во время выполнения."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Получаем аннотации типов
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Проверяем типы аргументов
        for param_name, value in bound_args.arguments.items():
            if param_name in sig.parameters:
                param = sig.parameters[param_name]
                if param.annotation != inspect.Parameter.empty:
                    if not type_check(value, param.annotation):
                        raise TypeError(
                            f"Parameter '{param_name}' expected {param.annotation}, "
                            f"got {type(value).__name__}"
                        )

        # Выполняем функцию
        result = func(*args, **kwargs)

        # Проверяем тип возвращаемого значения
        if sig.return_annotation != inspect.Parameter.empty:
            if not type_check(result, sig.return_annotation):
                raise TypeError(
                    f"Return value expected {sig.return_annotation}, "
                    f"got {type(result).__name__}"
                )

        return result

    return wrapper


def safe_type_convert(
    value: Any, target_type: Type[T], default: T | None = None
) -> T | None:
    """Безопасное преобразование типа с fallback значением."""
    try:
        if target_type is str:
            return str(value)  # type: ignore
        elif target_type is int:
            return int(value)  # type: ignore
        elif target_type is float:
            return float(value)  # type: ignore
        elif target_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")  # type: ignore
            return bool(value)  # type: ignore
        elif target_type is list:
            if isinstance(value, (list, tuple, set)):
                return list(value)  # type: ignore
            return [value]  # type: ignore
        elif target_type is dict:
            if isinstance(value, dict):
                return value  # type: ignore
            return {}  # type: ignore
        else:
            return value  # type: ignore
    except (ValueError, TypeError):
        return default


def validate_dict_structure(
    data: dict[str, Any], expected_structure: dict[str, Type]
) -> bool:
    """Проверить структуру словаря."""
    for key, expected_type in expected_structure.items():
        if key not in data:
            return False
        if not type_check(data[key], expected_type):
            return False
    return True


def ensure_type(value: Any, expected_type: Type[T], fallback: T | None = None) -> T:
    """Гарантировать правильный тип значения."""
    if type_check(value, expected_type):
        return value

    if fallback is not None:
        return fallback

    # Пытаемся преобразовать тип
    converted = safe_type_convert(value, expected_type)
    if converted is not None:
        return converted

    raise TypeError(
        f"Cannot convert {type(value).__name__} to {expected_type.__name__}"
    )


# Примеры использования для основных типов данных бота
def validate_group_data_types(data: dict[str, Any]) -> bool:
    """Проверить типы данных группы."""
    expected_structure = {
        "id": str,
        "name": str,
        "faculty": str,
        "speciality": str,
        "course": str,
    }
    return validate_dict_structure(data, expected_structure)


def validate_user_data_types(data: dict[str, Any]) -> bool:
    """Проверить типы данных пользователя."""
    expected_structure = {"telegram_id": int, "group_id": int, "subscription_type": str}
    return validate_dict_structure(data, expected_structure)
