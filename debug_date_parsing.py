#!/usr/bin/env python3
"""
Debug Ava's Date Parsing Issues
Test why Ava can't understand "Monday, July 14, 2025"
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ava_intelligence_upgrade import AvaDateParser, ava_intelligence
from datetime import datetime


def test_date_parsing():
    print('🔍 Testing Ava\'s Date Parsing...')
    
    parser = AvaDateParser()
    
    test_messages = [
        "What's on the calendar for Monday?",
        "Monday, July 14, 2025",
        "Monday July 14",
        "Monday the 14th", 
        "next Monday",
        "tomorrow",
        "today",
        "What's scheduled for Monday?",
        "Who's scheduled for Monday the 14th?",
        "Any appointments on Monday?"
    ]
    
    print(f"Current date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"Target date should be: Monday, July 14, 2025")
    print("\n" + "="*60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        
        try:
            parsed_date = parser.parse_date_from_message(message)
            
            if parsed_date:
                print(f"   ✅ Parsed: {parsed_date.strftime('%A, %B %d, %Y')}")
                
                # Check if it's the expected Monday July 14
                if parsed_date.year == 2025 and parsed_date.month == 7 and parsed_date.day == 14:
                    print(f"   🎯 CORRECT! Found Monday July 14, 2025")
                else:
                    print(f"   ❌ WRONG DATE! Expected Monday July 14, 2025")
            else:
                print(f"   ❌ Failed to parse - will default to today")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    print("\n" + "="*60)
    print("🔧 Date Parser Analysis Complete")


async def test_full_schedule_question():
    print('\n🧪 Testing Full Schedule Question Flow...')
    
    test_questions = [
        "What's on the calendar for Monday?",
        "Monday, July 14, 2025",
        "Who's scheduled for Monday the 14th?"
    ]
    
    for question in test_questions:
        print(f"\n📝 Question: '{question}'")
        try:
            response = await ava_intelligence.handle_schedule_question(question)
            print(f"📋 Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == '__main__':
    test_date_parsing()
    asyncio.run(test_full_schedule_question())