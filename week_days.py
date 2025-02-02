### Not worked!!!



rom enum import Enum

class WeekDay(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    _VARIATIONS = {
        0: ["mon", "monday", "пн", "понедельник"],
        1: ["tue", "tuesday", "вт", "вторник"],
        2: ["wed", "wednesday", "ср", "среда"],
        3: ["thu", "thursday", "чт", "четверг"],
        4: ["fri", "friday", "пт", "пятница"],
        5: ["sat", "saturday", "сб", "суббота"],
        6: ["sun", "sunday", "вс", "воскресенье"],
    }

    @property
    def variations(self) -> list[str]:
        return WeekDay._VARIATIONS[self.value]  # Обращаемся к _VARIATIONS через класс

    @classmethod
    def from_string(cls, s: str) -> "WeekDay | None":
        s = s.lower().strip().replace(".", "").replace("-", "").replace("\n", "")
        for day in cls:
            if s in WeekDay._VARIATIONS[day.value]:  # Используем day.value
                return day
        return None

# **Примеры использования**:
print(WeekDay.from_string("пн"))  # WeekDay.MONDAY
print(WeekDay.from_string("Чт.")) # WeekDay.THURSDAY
print(WeekDay.from_string("неизвестно"))  # None
