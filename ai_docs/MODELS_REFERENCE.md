# Справочник моделей данных

## Pydantic модели

### User (app/models/user.py)

#### User
```python
class User(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    telegram_username: Optional[str] = Field(None, description="Username в Telegram")
    full_name: Optional[str] = Field(None, description="Полное имя пользователя")
    access_level: AccessLevel = Field(AccessLevel.GUEST, description="Уровень доступа")
    is_active: bool = Field(True, description="Активен ли пользователь")
    last_seen: Optional[datetime] = Field(None, description="Время последней активности")
```

#### StudentProfile
```python
class StudentProfile(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    group_id: Optional[int] = Field(None, description="ID группы студента")
    student_id: Optional[str] = Field(None, description="Номер студенческого билета")
    preferred_format: str = Field("xlsx", description="Предпочитаемый формат файлов")
```

#### Subscription
```python
class Subscription(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    plan: SubscriptionPlan = Field(..., description="Тарифный план")
    started_at: datetime = Field(default_factory=datetime.now, description="Начало подписки")
    expires_at: Optional[datetime] = Field(None, description="Окончание подписки")
    is_active: bool = Field(True, description="Активна ли подписка")
    auto_renewal: bool = Field(False, description="Автопродление")
    payment_method: Optional[str] = Field(None, description="Способ оплаты")
    subscription_id: Optional[str] = Field(None, description="ID в платежной системе")
```

#### AccessLevel
```python
class AccessLevel(str, Enum):
    GUEST = "guest"
    BASIC = "basic"
    TESTER = "tester"
    ADMIN = "admin"
```

#### SubscriptionPlan
```python
class SubscriptionPlan(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
```

### Education (app/models/education.py)

#### Speciality
```python
class Speciality(BaseModel):
    code: str = Field(..., description="Код специальности (31.05.01)")
    name: str = Field(..., description="Название специальности")
    full_name: Optional[str] = Field(None, description="Полное название")
    faculty: Optional[str] = Field(None, description="Факультет")
    degree_type: DegreeType = Field(DegreeType.SPECIALITY, description="Тип программы")
    study_years: int = Field(6, description="Количество лет обучения")
```

#### StudyGroup
```python
class StudyGroup(BaseModel):
    number: str = Field(..., description="Номер группы (103а)")
    course: int = Field(..., description="Курс")
    stream: str = Field(..., description="Поток (а, б, в)")
    speciality_id: int = Field(..., description="ID специальности")
    current_semester: Optional[Semester] = Field(None, description="Текущий семестр")
    academic_year: Optional[str] = Field(None, description="Учебный год (2024/2025)")
    is_active: bool = Field(True, description="Активна ли группа")
```

#### Subject
```python
class Subject(BaseModel):
    name: str = Field(..., description="Название предмета")
    code: Optional[str] = Field(None, description="Код предмета")
    speciality_id: int = Field(..., description="ID специальности")
    course: int = Field(..., description="Курс")
    semester: Semester = Field(..., description="Семестр")
    credits: Optional[int] = Field(None, description="Количество кредитов")
    hours_total: Optional[int] = Field(None, description="Всего часов")
    hours_lectures: Optional[int] = Field(None, description="Часов лекций")
    hours_seminars: Optional[int] = Field(None, description="Часов семинаров")
    hours_practice: Optional[int] = Field(None, description="Часов практики")
```

#### Teacher
```python
class Teacher(BaseModel):
    full_name: str = Field(..., description="ФИО преподавателя")
    short_name: Optional[str] = Field(None, description="Краткое имя")
    department: Optional[str] = Field(None, description="Кафедра")
    position: Optional[str] = Field(None, description="Должность")
    email: Optional[str] = Field(None, description="Email")
```

#### Room
```python
class Room(BaseModel):
    number: str = Field(..., description="Номер аудитории")
    building: Optional[str] = Field(None, description="Корпус")
    floor: Optional[int] = Field(None, description="Этаж")
    capacity: Optional[int] = Field(None, description="Вместимость")
    equipment: Optional[str] = Field(None, description="Оборудование (JSON)")
    room_type: Optional[str] = Field(None, description="Тип аудитории")
```

#### Schedule
```python
class Schedule(BaseModel):
    id: Optional[int] = Field(None, description="ID записи")
    group_id: int = Field(..., description="ID группы")
    date: datetime = Field(..., description="Дата занятия")
    week_number: int = Field(..., description="Номер недели")
    day_of_week: int = Field(..., description="День недели (1-7)")
    lesson_number: int = Field(..., description="Номер пары")
    subject_name: str = Field(..., description="Название предмета")
    lesson_type: LessonType = Field(..., description="Тип занятия")
    teacher_name: Optional[str] = Field(None, description="Преподаватель")
    room_number: Optional[str] = Field(None, description="Номер аудитории")
    building: Optional[str] = Field(None, description="Корпус")
    start_time: Optional[str] = Field(None, description="Время начала")
    end_time: Optional[str] = Field(None, description="Время окончания")
    is_cancelled: bool = Field(False, description="Отменено ли занятие")
    notes: Optional[str] = Field(None, description="Примечания")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")
```

#### Grade
```python
class Grade(BaseModel):
    id: Optional[int] = Field(None, description="ID оценки")
    student_id: int = Field(..., description="ID студента")
    subject_name: str = Field(..., description="Название предмета")
    grade_type: GradeType = Field(..., description="Тип оценки")
    grade_value: str = Field(..., description="Значение оценки")
    max_grade: Optional[str] = Field(None, description="Максимальная оценка")
    date_recorded: datetime = Field(..., description="Дата выставления")
    semester: Optional[str] = Field(None, description="Семестр")
    teacher_name: Optional[str] = Field(None, description="Преподаватель")
    notes: Optional[str] = Field(None, description="Примечания")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")
```

#### AttendanceRecord
```python
class AttendanceRecord(BaseModel):
    id: Optional[int] = Field(None, description="ID записи")
    student_id: int = Field(..., description="ID студента")
    schedule_id: int = Field(..., description="ID занятия в расписании")
    status: AttendanceStatus = Field(..., description="Статус посещаемости")
    notes: Optional[str] = Field(None, description="Примечания")
    recorded_by: Optional[int] = Field(None, description="Кто записал")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время обновления")
```

### Enums

#### DegreeType
```python
class DegreeType(str, Enum):
    BACHELOR = "bachelor"
    SPECIALITY = "speciality"
    MASTER = "master"
```

#### Semester
```python
class Semester(str, Enum):
    AUTUMN = "осенний"
    SPRING = "весенний"
```

#### LessonType
```python
class LessonType(str, Enum):
    LECTURE = "лекция"
    SEMINAR = "семинар"
    PRACTICE = "практика"
    LAB = "лабораторная"
    EXAM = "экзамен"
    OFFSET = "зачет"
```

#### GradeType
```python
class GradeType(str, Enum):
    TSB = "ТСБ"  # Тематическое собеседование
    OSB = "ОСБ"  # Оценочное собеседование
    KNL = "КНЛ"  # Контрольная лекция
    KNS = "КНС"  # Контрольная семинар
    EXAM = "экзамен"
    OFFSET = "зачет"
    HOMEWORK = "домашнее задание"
    ESSAY = "реферат"
```

#### AttendanceStatus
```python
class AttendanceStatus(str, Enum):
    PRESENT = "present"  # Присутствует
    ABSENT = "absent"  # Отсутствует
    LATE = "late"  # Опоздание
    EXCUSED = "excused"  # Уважительная причина
```

## SQLAlchemy модели

### User (app/database/models.py)
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group: Mapped["Group"] = relationship(back_populates="users")
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"), nullable=True)
```

### Group (app/database/models.py)
```python
class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    faculty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    speciality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    course: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="group")
```

### Faculty (app/database/models.py)
```python
class Faculty(Base):
    __tablename__ = "faculties"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Speciality (app/database/models.py)
```python
class Speciality(Base):
    __tablename__ = "specialities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    faculty_id: Mapped[Optional[int]] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Schedule (app/database/models.py)
```python
class Schedule(Base):
    __tablename__ = "schedules"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    faculty_id: Mapped[Optional[int]] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    speciality_id: Mapped[Optional[int]] = mapped_column(ForeignKey("specialities.id"), nullable=True)
    academic_year_id: Mapped[Optional[int]] = mapped_column(ForeignKey("academic_years.id"), nullable=True)
    semester_id: Mapped[Optional[int]] = mapped_column(ForeignKey("semesters.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Lesson (app/database/models.py)
```python
class Lesson(Base):
    __tablename__ = "lessons"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"))
    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"), nullable=True)
    classroom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    lesson_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

## Использование моделей

### Pydantic модели
Используются для:
- Валидации данных от пользователя
- Сериализации данных для API
- Структурирования данных в сервисах
- Типизации возвращаемых значений

### SQLAlchemy модели
Используются для:
- Работы с базой данных
- ORM маппинга
- Связей между таблицами
- Миграций схемы БД

### Примеры использования

#### Создание пользователя
```python
from app.models.user import User, AccessLevel

user = User(
    telegram_id=12345,
    telegram_username="test_user",
    full_name="Иван Иванов",
    access_level=AccessLevel.BASIC
)
```

#### Валидация данных
```python
from app.models.education import Speciality, DegreeType

speciality = Speciality(
    code="31.05.01",
    name="Лечебное дело",
    degree_type=DegreeType.SPECIALITY,
    study_years=6
)
```

#### Работа с БД
```python
from app.database.models import User as UserModel

# Создание записи в БД
db_user = UserModel(
    telegram_id=12345,
    username="test_user",
    first_name="Иван"
)
session.add(db_user)
await session.commit()
```
