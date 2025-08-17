import requests
import json
import sys

def get_valid_filters():
    """
    Получает и выводит список валидных фильтров (типов занятий, курсов и т.д.)
    с API сайта СЗГМУ.
    """
    # Словарь URL-адресов API и соответствующих им названий фильтров
    endpoints = {
        'Типы занятий': 'https://frsview.szgmu.ru/api/view/lessonType',
        'Учебные годы': 'https://frsview.szgmu.ru/api/view/academicYear',
        'Номера курсов': 'https://frsview.szgmu.ru/api/view/courseNumber',
        'Потоки групп': 'https://frsview.szgmu.ru/api/view/groupStream',
        'Специальности': 'https://frsview.szgmu.ru/api/view/speciality',
        'Семестры': 'https://frsview.szgmu.ru/api/view/semester'
    }

    print("Получение валидных фильтров с сайта СЗГМУ...\n")

    for filter_name, url in endpoints.items():
        try:
            response = requests.get(url)
            response.raise_for_status()  # Вызовет исключение для ошибок HTTP
            data = response.json()
            
            # Извлекаем значения 'name' из каждого объекта в списке
            valid_names = [item['name'] for item in data]
            
            # Выводим результат
            print(f"--- {filter_name} ---")
            for name in valid_names:
                print(f"  - {name}")
            print() # Пустая строка для читаемости

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении '{filter_name}': {e}", file=sys.stderr)
            continue
        except json.JSONDecodeError:
            print(f"Ошибка: Ответ для '{filter_name}' не является корректным JSON.", file=sys.stderr)
            continue

if __name__ == "__main__":
    get_valid_filters()
