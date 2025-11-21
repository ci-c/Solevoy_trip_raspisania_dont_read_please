import json

import requests


def get_valid_filters() -> None:
    """
    Получает и выводит список валидных фильтров (типов занятий, курсов и т.д.)
    с API сайта СЗГМУ.
    """
    # Словарь URL-адресов API и соответствующих им названий фильтров
    endpoints = {
        "Типы занятий": "https://frsview.szgmu.ru/api/view/lessonType",
        "Учебные годы": "https://frsview.szgmu.ru/api/view/academicYear",
        "Номера курсов": "https://frsview.szgmu.ru/api/view/courseNumber",
        "Потоки групп": "https://frsview.szgmu.ru/api/view/groupStream",
        "Специальности": "https://frsview.szgmu.ru/api/view/speciality",
        "Семестры": "https://frsview.szgmu.ru/api/view/semester",
    }


    for url in endpoints.values():
        try:
            response = requests.get(url)
            response.raise_for_status()  # Вызовет исключение для ошибок HTTP
            data = response.json()

            # Извлекаем значения 'name' из каждого объекта в списке
            valid_names = [item["name"] for item in data]

            # Выводим результат
            for _name in valid_names:
                pass

        except requests.exceptions.RequestException:
            continue
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    get_valid_filters()
