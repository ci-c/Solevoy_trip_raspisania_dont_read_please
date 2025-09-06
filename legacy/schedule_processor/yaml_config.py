"""YAML configuration loader with type conversion and validation."""

import yaml
from datetime import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Union
from dataclasses import dataclass


@dataclass
class ConfigError(Exception):
    """Configuration loading error."""
    message: str


class ConfigLoader:
    """Loads and processes YAML configuration with Python type conversion."""
    
    def __init__(self, config_path: Union[str, Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML config: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_rings(self) -> Dict[str, List[Tuple[Tuple[time, time], Tuple[time, time]]]]:
        """Convert YAML schedule rings to Python time objects."""
        rings = {}
        
        # Семинары
        seminars_data = self.get('schedule_rings.seminars', [])
        seminar_rings = []
        for item in seminars_data:
            time_slots = item.get('time_slots', [])
            if len(time_slots) >= 2:
                slot1 = time_slots[0]
                slot2 = time_slots[1]
                ring = (
                    (self._parse_time(slot1['start']), self._parse_time(slot1['end'])),
                    (self._parse_time(slot2['start']), self._parse_time(slot2['end']))
                )
                seminar_rings.append(ring)
        rings['с'] = seminar_rings
        
        # Лекции
        lectures_data = self.get('schedule_rings.lectures', [])
        lecture_rings = []
        for item in lectures_data:
            time_slots = item.get('time_slots', [])
            if len(time_slots) >= 2:
                slot1 = time_slots[0]
                slot2 = time_slots[1] 
                ring = (
                    (self._parse_time(slot1['start']), self._parse_time(slot1['end'])),
                    (self._parse_time(slot2['start']), self._parse_time(slot2['end']))
                )
                lecture_rings.append(ring)
        rings['л'] = lecture_rings
        
        return rings
    
    def get_rings_v1(self) -> Dict[str, Dict[str, List]]:
        """Convert YAML schedule rings to v1 legacy format."""
        rings_v1 = {"s": {}, "l": {}}
        
        # Семинары  
        seminars_data = self.get('schedule_rings.seminars', [])
        for item in seminars_data:
            time_slots = item.get('time_slots', [])
            pair_numbers = item.get('pair_number', [])
            if time_slots and pair_numbers:
                start_time = time_slots[0]['start']
                pair_str = ','.join(map(str, pair_numbers))
                
                rings_v1['s'][start_time] = [
                    self._parse_time(time_slots[0]['start']),
                    self._parse_time(time_slots[0]['end']),
                    self._parse_time(time_slots[1]['start']),
                    self._parse_time(time_slots[1]['end']),
                    pair_str
                ]
        
        # Лекции
        lectures_data = self.get('schedule_rings.lectures', [])
        for item in lectures_data:
            time_slots = item.get('time_slots', [])
            pair_number = item.get('pair_number')
            if time_slots and pair_number:
                start_time = time_slots[0]['start']
                
                rings_v1['l'][start_time] = [
                    self._parse_time(time_slots[0]['start']),
                    self._parse_time(time_slots[0]['end']),
                    self._parse_time(time_slots[1]['start']),
                    self._parse_time(time_slots[1]['end']),
                    str(pair_number)
                ]
        
        return rings_v1
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except Exception as e:
            raise ConfigError(f"Invalid time format '{time_str}': {e}")
    
    def get_week_days(self) -> Dict[str, int]:
        """Get week days mapping."""
        return self.get('week_days', {})
    
    def get_week_days_inverted(self) -> Dict[int, str]:
        """Get inverted week days mapping."""
        inverted = self.get('week_days_inverted', {})
        # Convert string keys to int
        return {int(k): v for k, v in inverted.items()}
    
    def get_excel_config(self) -> Dict[str, Any]:
        """Get Excel configuration."""
        return self.get('excel', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.get('api', {})
    
    def get_bot_config(self) -> Dict[str, Any]:
        """Get bot configuration."""
        return self.get('bot', {})
    
    def get_applications_config(self) -> Dict[str, Any]:
        """Get applications configuration."""
        return self.get('applications', {})
    
    def get_academic_config(self) -> Dict[str, Any]:
        """Get academic configuration."""
        return self.get('academic', {})
    
    def get_reminders_config(self) -> Dict[str, Any]:
        """Get reminders configuration."""
        return self.get('reminders', {})
    
    def get_paths_config(self) -> Dict[str, str]:
        """Get paths configuration."""
        return self.get('paths', {})


# Глобальный экземпляр загрузчика конфигурации
_config_loader = None

def get_config() -> ConfigLoader:
    """Get global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def reload_config(config_path: Union[str, Path] = None) -> ConfigLoader:
    """Reload configuration from file."""
    global _config_loader
    _config_loader = ConfigLoader(config_path)
    return _config_loader


# Для обратной совместимости со старым config.py
def get_rings():
    """Get schedule rings in new format."""
    return get_config().get_rings()


def get_rings_v1():
    """Get schedule rings in v1 legacy format.""" 
    return get_config().get_rings_v1()


def get_week_days():
    """Get week days mapping."""
    return get_config().get_week_days()


def get_week_days_inverted():
    """Get inverted week days mapping."""
    return get_config().get_week_days_inverted()


def get_width_columns():
    """Get Excel column widths."""
    return get_config().get('excel.column_widths', [8, 13, 4, 4, 16, 4, 20])


# Константы для обратной совместимости
RINGS = get_rings()
RINGS_V1 = get_rings_v1()
WEEK_DAYS = get_week_days()
WEEK_DAYS_INVERTED = get_week_days_inverted()
WIDTH_COLUMNS = get_width_columns()
SWP_NAME = get_config().get('defaults.swimming_pool_name', 'ФП')
ADD_BREAKS = get_config().get('defaults.add_breaks', False)
ADD_MARK = get_config().get('defaults.add_mark', True)