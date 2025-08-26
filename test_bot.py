#!/usr/bin/env python3
"""Test script to validate bot functionality without running the full bot."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from schedule_processor.api import get_available_filters, search_schedules


async def test_api_functions():
    """Test the API functions used by the bot."""
    print("🧪 Testing bot API functions...\n")
    
    # Test 1: Get available filters
    print("1️⃣ Testing get_available_filters()...")
    try:
        filters = await get_available_filters()
        print(f"✅ Got filters: {list(filters.keys())}")
        for name, options in filters.items():
            print(f"   {name}: {len(options)} options")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: Search schedules
    print("2️⃣ Testing search_schedules()...")
    try:
        test_filters = {
            "Курс": ["2"],
            "Специальность": ["32.05.01 медико-профилактическое дело"],
            "Семестр": ["весенний"],
            "Учебный год": ["2024/2025"]
        }
        
        print(f"   Searching with filters: {test_filters}")
        results = await search_schedules(test_filters)
        print(f"✅ Found {len(results)} schedules")
        
        for i, result in enumerate(results[:3], 1):  # Show first 3 results
            print(f"   {i}. {result.get('display_name', 'Unknown')}")
            print(f"      ID: {result.get('id')}")
            
            # Check if schedule has lessons
            data = result.get('data', {})
            lessons = data.get('scheduleLessonDtoList', [])
            print(f"      Lessons: {len(lessons)}")
            
            if lessons:
                # Show subgroups
                subgroups = set()
                for lesson in lessons[:5]:  # Check first 5 lessons
                    if lesson.get('subgroup'):
                        subgroups.add(lesson.get('subgroup'))
                print(f"      Subgroups: {', '.join(sorted(subgroups)) if subgroups else 'None'}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("🔍 API functions test completed!")


if __name__ == "__main__":
    asyncio.run(test_api_functions())