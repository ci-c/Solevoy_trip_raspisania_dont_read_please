import json
import csv

# Загрузка данных из JSON файла (предположим, что файл называется 'schedule.json')
with open('sch.json', 'r', encoding='utf-8') as file:
    schedule_data = json.load(file)

# Функция для создания CSV файла для каждой группы
def create_csv_for_group(group_name, group_schedule):
    filename = f'С_1_МПФ_АБ_{group_name}.csv'
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['дн', 'время', 'Предмет', 'Недели'])

        for day, time_slots in group_schedule.items():
            for slot in time_slots:
                subject = slot['subject']
                weeks = slot['weeks']
                time = slot['time'] if 'time' in slot else ''
                time = time[:5]

                # Если предмет состоит из нескольких строк, разбиваем его на части
                subjects_list = subject.split('\n')
                weeks_list = weeks.split('\n')

                for i, subj in enumerate(subjects_list):
                    subj = subj.strip()
                    wk = weeks_list[i].strip() if i < len(weeks_list) else ''
                    writer.writerow([day, time, subj, wk])

# Проход по всем группам и создание CSV файлов
for group, group_schedule in schedule_data['schedule'].items():
    create_csv_for_group(group, group_schedule)

print("CSV files have been created successfully.")
