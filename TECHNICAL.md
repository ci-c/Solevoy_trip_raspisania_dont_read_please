# Technical Documentation - Schedule Processor

## Core Components Deep Dive

### 1. Schedule Processing Engine

#### Data Models (`schedule_processor/models.py`)

```python
@dataclass
class Lesson:
    """Raw lesson data from API - matches exact API response"""
    academicYear: str           # "2024/2025"
    auditoryNumber: Optional[str]  # "101", "Online", etc.
    courseNumber: int           # 1, 2, 3, 4, 5, 6
    dayName: str               # "пн", "вт", "ср", etc.
    departmentName: str        # "Кафедра анатомии"
    errorList: List[Any]       # API validation errors
    fileName: str              # Original schedule file name
    groupStream: str           # "а", "б", "в", "г"
    groupTypeName: str         # Group classification
    id: int                    # Unique lesson ID
    lectorName: Optional[str]  # "Иванов И.И."
    lessonType: str           # "лекционного", "семинарского"
    locationAddress: Optional[str]  # Building/room details
    pairTime: str             # "9:00-10:30"
    scheduleId: int           # Parent schedule ID
    semester: str             # "весенний", "осенний"
    speciality: str           # "31.05.01 лечебное дело"
    studyGroup: str           # Group identifier
    subgroup: Optional[str]   # "101б", "202а", etc.
    subjectName: str          # "Анатомия человека"
    weekNumber: int           # 1-18 (week of semester)

@dataclass
class ProcessedLesson:
    """Clean lesson data ready for export"""
    week: int                 # Calculated week number
    date: date               # Specific lesson date
    time_slot: List[time]    # [start1, end1, start2, end2]
    lesson_numbers: str      # "1", "1-2", etc.
    type_: str              # "Л", "С"
    subject: str            # Subject name
    location: Optional[str]  # Venue
    lecturer: Optional[str] # Teacher name
```

#### Time Configuration (`schedule_processor/config.py`)

The system uses a complex time mapping system to handle different lesson types:

```python
RINGS = {
    "л": [  # Lectures (45 min + 5 min break)
        ((time(9, 0), time(9, 45)), (time(9, 50), time(10, 35))),   # Пара 1
        ((time(10, 55), time(11, 40)), (time(11, 45), time(12, 30))), # Пара 2  
        ((time(13, 10), time(13, 55)), (time(14, 0), time(14, 45))),  # Пара 3
        ((time(15, 0), time(15, 45)), (time(15, 50), time(16, 35))),  # Пара 4
        ((time(16, 45), time(17, 30)), (time(17, 35), time(18, 20))), # Пара 5
    ],
    "с": [  # Seminars (90 min + 15 min break + 90 min)
        ((time(9, 0), time(10, 30)), (time(10, 45), time(12, 15))),   # Пары 1-2
        ((time(13, 10), time(14, 40)), (time(14, 55), time(16, 25))), # Пары 3-4
    ],
}
```

**Ring Structure Explanation**:
- Each ring represents a time slot
- Tuple format: `((start_time, mid_break), (break_end, end_time))`
- For lectures: 45min lesson + 5min break + 45min lesson  
- For seminars: 90min lesson + 15min break + 90min lesson

### 2. API Integration (`schedule_processor/api.py`)

#### Schedule Discovery Process

```python
def find_schedule_ids(
    group_stream: List[str] | None = None,      # ["а", "б"]
    speciality: List[str] | None = None,        # ["31.05.01 лечебное дело"] 
    course_number: List[str] | None = None,     # ["1", "2"]
    academic_year: List[str] | None = None,     # ["2024/2025"]
    lesson_type: Optional[List[str]] = None,    # ["семинарского"]
    semester: Optional[List[str]] = None,       # ["весенний"]
) -> List[int]:
```

**API Endpoint**: `https://frsview.szgmu.ru/api/xlsxSchedule/findAll/0`

**Request Format**:
```json
{
    "groupStream": ["б"],
    "speciality": ["32.05.01 медико-профилактическое дело"],
    "courseNumber": ["2"],
    "academicYear": ["2024/2025"],
    "lessonType": [],
    "semester": ["весенний"]
}
```

**Response Format**:
```json
{
    "content": [
        {
            "id": 541,
            "fileName": "С_2_МПФ_б_241.xlsx",
            "speciality": "32.05.01 медико-профилактическое дело",
            // ... other metadata
        }
    ],
    "totalElements": 1
}
```

#### Data Fetching Process

```python
def get_schedule_data(schedule_id: int) -> dict | None:
```

**API Endpoint**: `https://frsview.szgmu.ru/api/xlsxSchedule/findById?xlsxScheduleId={id}`

**Response Structure**:
```json
{
    "id": 541,
    "fileName": "С_2_МПФ_б_241.xlsx", 
    "formType": "group",
    "statusId": "APPROVED",
    "scheduleLessonDtoList": [
        {
            "id": 12345,
            "academicYear": "2024/2025",
            "semester": "весенний",
            "courseNumber": 2,
            "speciality": "32.05.01 медико-профилактическое дело",
            "groupStream": "б", 
            "studyGroup": "МПФ",
            "subgroup": "241б",
            "dayName": "пн",
            "pairTime": "9:00-10:30",
            "weekNumber": 1,
            "lessonType": "семинарского",
            "subjectName": "Анатомия человека",
            "auditoryNumber": "101",
            "locationAddress": "Главный корпус",
            "lectorName": "Иванов И.И.",
            "departmentName": "Кафедра анатомии",
            // ... other fields
        }
        // ... more lessons
    ]
}
```

### 3. Data Processing Pipeline

#### Processing Logic (`schedule_processor/generator.py`)

```python
def process_lessons_for_export(
    raw_lessons: list[Lesson], 
    subgroup_name: str, 
    first_day: datetime.date
) -> list[ProcessedLesson]:
```

**Processing Steps**:

1. **Filtering**:
   ```python
   def f_filter(lesson: Lesson) -> bool:
       r: bool = lesson.subgroup == subgroup_name.upper()
       r = r or lesson.subgroup == subgroup_name.lower()
       return r
   ```

2. **Time Processing**:
   ```python
   # Parse time string "9:00-10:30" -> time(9, 0)
   pair_time = lesson.pairTime.replace(".", ":")
   start_time_str = pair_time.split("-")[0].strip()
   lesson_start_time = datetime.time(int(t[0]), int(t[1]))
   ```

3. **Lesson Number Mapping**:
   ```python
   # Map start time to lesson number using RINGS configuration
   for num, ring in enumerate(RINGS[lesson_type_key]):
       if ring[0][0] == lesson_start_time:
           lesson_number = num
           break
   ```

4. **Date Calculation**:
   ```python
   # Calculate actual lesson date from week number
   first_monday = first_day - datetime.timedelta(days=first_day.weekday())
   date = first_monday + datetime.timedelta(weeks=week_num - 1, days=day_index)
   ```

### 4. Output Generation

#### Excel Generation (`schedule_processor/generator.py`)

**Features**:
- Merged cells for dates and weeks
- Conditional formatting (lectures vs seminars)
- Custom column widths
- Professional styling with borders and colors

```python
def gen_excel_file(schedule_data: List[ProcessedLesson], subgroup_name: str) -> None:
    # Create workbook with styling
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    
    # Apply styles
    lecture_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    seminar_fill = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
    
    # Merge cells for better readability
    worksheet.merge_cells(f"A{merge_start_row}:A{current_row - 1}")  # Week numbers
    worksheet.merge_cells(f"B{merge_start_row}:B{current_row - 1}")  # Dates
```

#### iCalendar Generation (`schedule_processor/generator.py`)

**Features**:
- RFC 5545 compliant
- Timezone support (Europe/Moscow)
- Rich metadata inclusion
- Cross-platform compatibility

```python
def gen_ical(schedule_data: List[ProcessedLesson], subgroup_name: str) -> None:
    calendar = ics.Calendar()
    moscow_tz = ZoneInfo('Europe/Moscow')
    
    for lesson in schedule_data:
        event = ics.Event()
        event.begin = datetime.datetime.combine(lesson.date, start_time, tzinfo=moscow_tz)
        event.end = datetime.datetime.combine(lesson.date, end_time, tzinfo=moscow_tz)
        event.name = f"№{lesson.lesson_numbers} {lesson.type_} {lesson.subject}"
        event.location = lesson.location or ""
        event.categories = [{"Л": "Lecture", "С": "Seminar"}.get(lesson.type_, "Class")]
        calendar.events.add(event)
```

### 5. Telegram Bot Architecture

#### State Management (`bot_main.py`)

The bot uses Finite State Machine (FSM) for complex user interactions:

```python
class SearchForm(StatesGroup):
    waiting_activation = State()    # Initial state after /start
    selecting_filters = State()     # Choose filter category (Course, Specialty)
    selecting_options = State()     # Choose filter values (1, 2, А, Б)  
    processing_search = State()     # Waiting for search results
    selecting_result = State()      # Choose from found schedules
    selecting_format = State()      # Choose output format (Excel/iCal)
    generating_file = State()       # File generation in progress
```

#### Advanced Keyboard Generation

```python
def get_filters_keyboard(
    available_filters: Dict[str, List[str]],
    selected_filters: Dict[str, List[str]],
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in available_filters.keys():
        selected_count = len(selected_filters.get(name, []))
        # Dynamic button text showing selection count
        button_text = f"{name} ({selected_count}) {'✅' if selected_count > 0 else '➡️'}"
        builder.button(text=button_text, callback_data=FilterCallback(name=name))
    return builder.as_markup()
```

#### Smart Schedule Information Display

```python
def format_schedule_info(schedule_data: Dict) -> str:
    """Extract and format key information for user-friendly display"""
    lessons = schedule_data.get('data', {}).get('scheduleLessonDtoList', [])
    if lessons:
        first_lesson = lessons[0]
        speciality = first_lesson.get('speciality', 'Unknown')
        course_number = first_lesson.get('courseNumber', 'Unknown') 
        semester = first_lesson.get('semester', 'Unknown')
        academic_year = first_lesson.get('academicYear', 'Unknown')
        
        # Extract unique subgroups
        subgroups = {lesson.get('subgroup') for lesson in lessons[:10] if lesson.get('subgroup')}
        
        return (f"{speciality}\n"
                f"Курс: {course_number}, Поток: {group_stream}\n" 
                f"Семестр: {semester} {academic_year}\n"
                f"Подгруппы: {', '.join(sorted(subgroups))}")
```

### 6. Error Handling Strategy

#### Network Resilience

```python
try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    logger.error(f"HTTP request error occurred: {e}")
    return []
except json.JSONDecodeError:
    logger.error("JSON decoding error: The response is not valid JSON.")
    return []
```

#### Graceful Bot Degradation

```python
try:
    file_path = await generate_schedule_file(selected_result, format_type, subgroup_name)
    # Send successful result
except Exception as e:
    logger.error(f"Error in file generation: {e}")
    # Show user-friendly error message
    await callback.message.edit_text(
        f"❌ Ошибка при генерации файла: {str(e)}\n\n"
        f"Попробуйте еще раз или выберите другой формат."
    )
    # Provide recovery options
```

### 7. Configuration Management

#### Environment Variables (`.env`)

```env
# Required
BOT_API_KEY=your_telegram_bot_token_here

# Optional  
API_BASE_URL=https://frsview.szgmu.ru/api
API_TIMEOUT=30
LOG_LEVEL=INFO
TIMEZONE=Europe/Moscow
```

#### Dynamic Configuration Loading

```python
load_dotenv()
API_TOKEN: Optional[str] = os.getenv("BOT_API_KEY")
if not API_TOKEN:
    logger.critical("Need to specify BOT_API_KEY in .env file. Exiting.")
    sys.exit(1)
```

### 8. Testing Strategy

#### API Function Testing (`test_bot.py`)

```python
async def test_api_functions():
    """Test core API functions without full bot deployment"""
    # Test filter retrieval
    filters = await get_available_filters()
    
    # Test search functionality
    test_filters = {
        "Курс": ["2"],
        "Специальность": ["32.05.01 медико-профилактическое дело"]
    }
    results = await search_schedules(test_filters)
    
    # Validate results
    for result in results:
        assert 'id' in result
        assert 'display_name' in result
        assert 'data' in result
```

### 9. Performance Optimizations

#### Caching Strategy

- API responses cached for 15 minutes
- Generated files reused when possible
- Expensive operations (date calculations) memoized

#### Memory Management

```python
# Process lessons in batches to avoid memory issues
def process_lessons_for_export(raw_lessons, subgroup_name, first_day):
    processed_lessons = {}  # Use dict for O(1) deduplication
    
    # Clear references after processing
    for lesson in filtered_lessons:
        # Process...
        del lesson  # Explicit cleanup for large datasets
```

#### Network Optimization

```python
# Parallel API calls for better performance
schedule_data = await asyncio.gather(*[
    get_schedule_data(schedule_id) 
    for schedule_id in schedule_ids[:10]
])
```

This technical documentation provides the foundation for understanding, maintaining, and extending the Schedule Processor system. Each component is designed for reliability, maintainability, and user experience.