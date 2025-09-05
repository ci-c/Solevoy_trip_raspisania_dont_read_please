# Schedule Processor Architecture Documentation

## Project Evolution Overview

This document provides detailed analysis of the Schedule Processor project evolution through different versions, from v1 to the latest modular architecture.

## Version Comparison Table

| Feature | v1 (Root) | v2 (Incomplete) | v3 (API-Based) | Latest (Modular) |
|---------|-----------|-----------------|----------------|------------------|
| **Status** | ✅ Working | ❌ Incomplete | ✅ Working | ✅ Working |
| **Input Source** | Local CSV/XLSX files | Local files | API requests | Both API + Files |
| **Architecture** | Monolithic script | Class-based | Modular functions | Package-based |
| **API Integration** | ❌ None | ❌ None | ✅ Full | ✅ Full |
| **Telegram Bot** | ❌ None | ❌ None | ❌ None | ✅ Full FSM |
| **Output Formats** | Excel + iCal | Not implemented | Excel + iCal | Excel + iCal |
| **Error Handling** | Basic | Not implemented | Good | Excellent |
| **Logging** | Print statements | Not implemented | Structured | Advanced (loguru) |
| **Testing** | None | None | None | Test utilities |
| **Configuration** | Hardcoded | Constants | Config file | Modular config |
| **Documentation** | Minimal | None | Comments | Comprehensive |

## Detailed Version Analysis

### v1 (Root Directory) - The Foundation ✅

**Status**: Working, production-ready for file-based processing

**Files**:
- `script.py` - Main processing script
- `sw.py` - Swimming pool schedule utilities

**Architecture**:
```
┌─────────────────────────────────────────┐
│                script.py                │
│  ┌─────────────────────────────────────┐ │
│  │        File Processing              │ │
│  │  • CSV/XLSX reading                 │ │
│  │  • Data parsing & validation        │ │
│  │  └─────────────────────────────────────┤
│  │        Schedule Generation          │ │
│  │  • Time slot mapping               │ │
│  │  • Date calculations               │ │
│  │  └─────────────────────────────────────┤
│  │        Output Generation            │ │
│  │  • Excel file creation             │ │
│  │  • iCalendar file creation         │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Key Features**:
- **File Processing**: Robust CSV/XLSX parsing with error handling
- **Smart Merging**: Combines lecture and seminar schedules by group ID
- **Time Slot Mapping**: Complex RINGS configuration for different lesson types
- **Excel Generation**: Rich formatting with merged cells, colors, and styling
- **iCalendar Generation**: Full RFC compliance with timezone support
- **Swimming Pool Integration**: Special handling for physical education classes

**Strengths**:
- Proven stability and reliability
- Comprehensive output formatting
- Good error handling for file operations
- Well-tested time calculation logic

**Limitations**:
- Monolithic design (single 460+ line file)
- Hardcoded configuration
- No API integration
- Limited extensibility

### v2 (Incomplete Refactoring) ❌

**Status**: Abandoned, incomplete implementation

**Files**:
- `script_v2.py` - Partial class-based rewrite

**Architecture**:
```
┌─────────────────────────────────────────┐
│           script_v2.py                  │
│  ┌─────────────────────────────────────┐ │
│  │     LessonType (Enum)               │ │
│  │  • LECTURE = 0                      │ │
│  │  • SEMINAR = 1                      │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │     Lesson (Dataclass)              │ │
│  │  • 15+ fields including metadata   │ │
│  │  • Type safety improvements        │ │
│  └─────────────────────────────────────┘ │
│  ┌─────────────────────────────────────┐ │
│  │     ScheduleTable (Class)           │ │
│  │  • File processing methods         │ │
│  │  • Partial implementation          │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Analysis**:
This version attempted to modernize v1 with object-oriented design but was never completed. The approach shows good architectural thinking:
- Type safety with enums and dataclasses
- Separation of concerns with dedicated classes
- Better data modeling

**Why it failed**:
- Incomplete implementation (only 102 lines vs v1's 460+)
- Missing core functionality (no file generation)
- No clear migration path from v1

### v3 (API Integration) ✅

**Status**: Working, API-focused implementation

**Files**:
- `main.py` - Entry point and orchestration
- `config.py` - Configuration constants
- `lesson.py` - Data models matching API response
- `post_lesson.py` - Processed lesson model
- `get_id.py` - Schedule ID discovery
- `get_raw.py` - API data fetching
- `get_filters.py` - Dynamic filter discovery
- `processing.py` - Data transformation logic
- `xlsx.py` - Excel file generation
- `ical.py` - iCalendar file generation

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                      v3 Architecture                   │
└─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │   main.py   │      │ get_id.py   │      │get_raw.py   │
    │ • Entry pt  │ ───▶ │ • Find IDs  │ ───▶ │ • Fetch API │
    │ • Orchestr. │      │ • Filtering │      │ • Parse JSON│
    └─────────────┘      └─────────────┘      └─────────────┘
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │processing.py│      │ lesson.py   │      │config.py    │
    │ • Transform │      │ • Raw model │      │ • Constants │
    │ • Filter    │      │ • API match │      │ • Time maps │
    │ • Sort      │      └─────────────┘      └─────────────┘
    └─────────────┘              │
           │                     ▼
           ▼              ┌─────────────┐
    ┌─────────────┐      │post_lesson  │
    │   Output    │      │ • Clean mdl │
    │  ┌────────┐ │      │ • Export    │
    │  │xlsx.py │ │      └─────────────┘
    │  └────────┘ │
    │  ┌────────┐ │
    │  │ical.py│ │
    │  └────────┘ │
    └─────────────┘
```

**Key Innovations**:

1. **API-First Design**: 
   - Direct integration with SZGMU university API
   - Dynamic filter discovery (`get_filters.py`)
   - Robust error handling for network requests

2. **Modular Architecture**:
   - Single responsibility principle
   - Clear separation between data fetching, processing, and output
   - Easy to test and maintain individual components

3. **Data Models**:
   ```python
   # lesson.py - Matches API response exactly
   @dataclass
   class Lesson:
       academicYear: str
       auditoryNumber: Optional[str]
       courseNumber: int
       dayName: str
       # ... 20+ fields matching API
   
   # post_lesson.py - Clean model for export
   @dataclass  
   class PostLesson:
       date: date
       lesson_number: int
       lesson_type: str
       subject_name: str
       lesson_seq: int
       metadata: dict[str, str]
   ```

4. **Advanced Processing Logic**:
   ```python
   # processing.py - Sophisticated filtering and transformation
   def process_lessons_for_export(raw_lessons, subgroup_name, first_day):
       # 1. Filter by subgroup with case-insensitive matching
       # 2. Handle time parsing with multiple formats  
       # 3. Map lesson types to internal format
       # 4. Calculate dates based on week numbers
       # 5. Deduplicate and sort chronologically
   ```

5. **Enhanced Output Generation**:
   - `xlsx.py`: Advanced Excel formatting with merged cells, conditional colors
   - `ical.py`: RFC-compliant iCalendar with timezone support
   - Both support metadata injection

**Strengths**:
- Clean, modular design
- API integration with real data
- Good error handling and logging  
- Type hints and documentation
- Extensible architecture

**Limitations**:
- No bot integration
- Limited backward compatibility with v1 file processing
- Missing some v1 features (swimming pool integration)

### Latest Version (Modular Package) ✅

**Status**: Working, comprehensive solution

**Architecture**:
```
schedule-processor/
├── schedule_processor/          # Core package
│   ├── __init__.py
│   ├── api.py                  # API client + bot integration  
│   ├── config.py               # Unified configuration
│   ├── core.py                 # High-level processing logic
│   ├── file_processor.py       # v1 file processing (compat)
│   ├── generator.py            # Unified output generation
│   └── models.py               # Data models
├── bot_main.py                 # Telegram bot (FSM-based)
├── main_api.py                 # API processing entry point
├── run.py                      # Unified runner script
├── test_bot.py                 # Testing utilities
└── v1-v3/                      # Legacy versions preserved
```

**Key Architectural Improvements**:

1. **Package-Based Design**:
   - Proper Python package structure
   - Clear module boundaries
   - Import management and dependencies

2. **Unified Configuration**:
   ```python
   # config.py - Single source of truth
   RINGS = {
       "с": [  # Seminars
           ((time(9, 0), time(10, 30)), (time(10, 45), time(12, 15))),
       ],
       "л": [  # Lectures  
           ((time(9, 0), time(9, 45)), (time(9, 50), time(10, 35))),
       ]
   }
   
   # Legacy compatibility
   RINGS_V1 = {...}  # For backward compatibility
   ```

3. **Advanced Telegram Bot**:
   ```python
   # FSM-based state management
   class SearchForm(StatesGroup):
       waiting_activation = State()
       selecting_filters = State() 
       selecting_options = State()
       processing_search = State()
       selecting_result = State()
       selecting_format = State()  # Excel vs iCalendar choice
       generating_file = State()
   ```

4. **Multi-Source Data Processing**:
   ```python
   # core.py - Unified processing interface
   def process_api_schedule(...)  -> bool:
       # API-based processing using v3 logic
   
   def process_file_schedule(...) -> bool:  
       # File-based processing using v1 logic
   ```

5. **Comprehensive Error Handling**:
   - Structured logging with `loguru`
   - Graceful degradation for network issues
   - User-friendly error messages in bot
   - Fallback mechanisms

6. **Testing Infrastructure**:
   ```python
   # test_bot.py - Automated testing
   async def test_api_functions():
       # Validate bot functions without full deployment
   ```

7. **Modern Development Practices**:
   - `uv` for dependency management
   - `ruff` for linting and formatting
   - Type hints throughout
   - Comprehensive documentation

## Data Flow Analysis

### v1 Data Flow (File-Based)
```
CSV/XLSX Files → Parse → Validate → Transform → Generate Excel/iCal
     ↓              ↓         ↓          ↓            ↓
  [Fixed Input] [Hardcoded] [Simple] [Monolithic] [Direct Output]
```

### v3 Data Flow (API-Based)  
```
API Request → Find IDs → Fetch Data → Process → Filter → Export
     ↓           ↓          ↓          ↓         ↓       ↓
 [Dynamic]  [Smart Search] [JSON]  [Transform] [Smart] [Formatted]
```

### Latest Data Flow (Hybrid)
```
User Input (Bot/CLI) → Route → [API Path] OR [File Path] → Process → Export
       ↓                ↓           ↓            ↓           ↓        ↓
   [Interactive]   [Smart Route] [v3 Logic] [v1 Logic] [Unified] [Multi-format]
```

## Configuration Evolution

### v1 Configuration
```python
# Hardcoded in script.py
RINGS = {
    "s": {
        "9:00": [time(9, 0), time(10, 30), time(10, 45), time(12, 15), '1,2'],
        # ...
    }
}
```

### v3 Configuration  
```python
# config.py - More structured
RINGS: dict[str, list[tuple[tuple[time, time], tuple[time, time]]]] = {
    "с": [
        ((time(9, 0), time(10, 30)), (time(10, 45), time(12, 15))),
    ],
}
```

### Latest Configuration
```python
# Unified config with backward compatibility
RINGS = {...}           # Modern format
RINGS_V1 = {...}       # Legacy compatibility  
WEEK_DAYS = {...}      # Shared constants
WIDTH_COLUMNS = [...]  # Excel formatting
```

## Performance Characteristics

| Aspect | v1 | v3 | Latest |
|--------|----|----|--------|
| **Startup Time** | Fast (local files) | Medium (API calls) | Medium |
| **Memory Usage** | Low | Medium | Medium |
| **Network Deps** | None | High | Medium |
| **Scalability** | Limited | Good | Excellent |
| **Maintainability** | Poor | Good | Excellent |

## Security Considerations

### v1 Security
- ✅ No network exposure
- ❌ No input validation
- ❌ File system vulnerabilities

### v3 Security  
- ✅ Input validation
- ✅ Network error handling
- ❌ No authentication
- ❌ Potential API abuse

### Latest Security
- ✅ Input validation & sanitization
- ✅ Rate limiting considerations
- ✅ Environment variable management
- ✅ Bot token protection
- ✅ File system sandboxing

## Conclusion

The evolution from v1 to the latest version demonstrates a clear progression:
- **v1**: Solid foundation with file processing
- **v2**: Failed attempt at modernization  
- **v3**: Successful API integration with modular design
- **Latest**: Comprehensive solution combining the best of all versions

The latest architecture successfully:
- Preserves v1's reliability for file processing
- Incorporates v3's API capabilities and modular design
- Adds modern features (Telegram bot, testing, proper packaging)
- Maintains backward compatibility
- Provides excellent developer experience

This evolution showcases how software architecture can improve while maintaining core functionality and reliability.