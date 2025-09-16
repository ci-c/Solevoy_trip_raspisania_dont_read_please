# Copyright (c) 2024 SZGMU Bot Project
# See LICENSE for details.

"""Bot FSM states."""

from aiogram.fsm.state import State, StatesGroup


class ProfileSetup(StatesGroup):
    """Состояния настройки профиля."""

    waiting_name = State()
    selecting_speciality = State()
    selecting_course = State()
    selecting_stream = State()
    selecting_group = State()
    confirmation = State()


class MainMenu(StatesGroup):
    """Главное меню."""

    home = State()
    schedule_view = State()
    diary_view = State()
    applications = State()
    reminders = State()
    settings = State()


class SearchForm(StatesGroup):
    """Состояния поиска расписания."""

    waiting_activation = State()
    selecting_filters = State()
    selecting_options = State()
    processing_search = State()
    selecting_result = State()
    selecting_format = State()
    generating_file = State()


class DiaryStates(StatesGroup):
    """Состояния дневника."""

    main_view = State()
    adding_grade = State()
    adding_homework = State()
    adding_absence = State()
    viewing_stats = State()


class ApplicationStates(StatesGroup):
    """Состояния заявлений."""

    selecting_dates = State()
    selecting_reason = State()
    generating_docs = State()


class AttestationStates(StatesGroup):
    """Состояния справочника аттестации."""

    main_view = State()
    asking_question = State()
    viewing_info = State()


class GradeStates(StatesGroup):
    """Состояния управления оценками."""

    main_view = State()
    selecting_subject = State()
    viewing_subject = State()
    adding_grade = State()
    adding_attendance = State()
    entering_grade_data = State()
    entering_attendance_data = State()


class GroupSearchStates(StatesGroup):
    """Состояния поиска групп."""

    choosing_search_type = State()
    entering_group_number = State()
    selecting_speciality = State()
    selecting_course = State()
    viewing_results = State()
    viewing_schedule = State()
    confirming_selection = State()


class GroupSetupStates(StatesGroup):
    """Состояния настройки группы."""

    choosing_method = State()
    entering_group_number = State()
    selecting_faculty = State()
    confirming_selection = State()
