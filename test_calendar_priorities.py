#!/usr/bin/env python3
"""
Test Calendar Priority System
Test the new prioritized calendar configuration
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import GOHIGHLEVEL_CALENDARS
from src.integrations.gohighlevel_service import ghl_service
from dean_calendar_intelligence import dean_commercial_intelligence
from datetime import datetime, timedelta


async def test_calendar_priorities():
    print('🎯 Testing Calendar Priority System...')
    
    # Test 1: Show calendar configuration
    print('\n1. Calendar Configuration:')
    print('=' * 50)
    
    for key, config in GOHIGHLEVEL_CALENDARS.items():
        priority_emoji = "🔥" if config['priority'] == 1 else "⭐" if config['priority'] == 2 else "📅"
        print(f"{priority_emoji} Priority {config['priority']}: {config['name']}")
        print(f"   📋 ID: {config['id']}")
        print(f"   🤖 Agent: {config['responsible_agent']}")
        print(f"   🎯 Focus: {config['focus']}")
        print(f"   📝 {config['description']}")
        print()
    
    # Test 2: Test appointment retrieval with priorities
    print('\n2. Testing Prioritized Appointment Retrieval:')
    print('=' * 50)
    
    try:
        # Test for today
        today = datetime.now()
        appointments = await ghl_service.get_todays_schedule()
        
        print(f"📅 Testing for: {today.strftime('%A, %B %d, %Y')}")
        print(f"✅ Retrieved {len(appointments)} appointments")
        
        if appointments:
            for i, apt in enumerate(appointments, 1):
                priority = getattr(apt, '_calendar_priority', 'unknown')
                calendar_type = getattr(apt, '_calendar_type', 'unknown')
                responsible_agent = getattr(apt, '_responsible_agent', 'unknown')
                
                priority_emoji = "🔥" if priority == 1 else "⭐" if priority == 2 else "📅"
                print(f"   {priority_emoji} {i}. {apt.title} (Priority {priority})")
                print(f"      👤 Agent: {responsible_agent}")
                print(f"      🎯 Type: {calendar_type}")
                print(f"      🕐 Time: {apt.start_time.strftime('%I:%M %p')}")
                print(f"      👥 Contact: {apt.contact_name}")
        else:
            print("   📭 No appointments found for today")
    
    except Exception as e:
        print(f"   ❌ Error testing appointments: {e}")
    
    # Test 3: Test Dean's commercial intelligence
    print('\n3. Testing Dean\'s Commercial Intelligence:')
    print('=' * 50)
    
    try:
        commercial_report = await dean_commercial_intelligence.generate_commercial_report()
        print("✅ Dean's Commercial Report Generated:")
        print(commercial_report)
        
    except Exception as e:
        print(f"❌ Error generating commercial report: {e}")
    
    # Test 4: Show next week's appointments by priority
    print('\n4. Testing Next Week Schedule by Priority:')
    print('=' * 50)
    
    try:
        next_week_start = datetime.now() + timedelta(days=1)
        next_week_end = datetime.now() + timedelta(days=7)
        
        appointments = await ghl_service.get_appointments(next_week_start, next_week_end)
        
        print(f"📅 Period: {next_week_start.strftime('%B %d')} - {next_week_end.strftime('%B %d, %Y')}")
        print(f"✅ Found {len(appointments)} appointments")
        
        if appointments:
            # Group by priority
            priority_groups = {}
            for apt in appointments:
                priority = getattr(apt, '_calendar_priority', 999)
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(apt)
            
            for priority in sorted(priority_groups.keys()):
                apt_list = priority_groups[priority]
                priority_emoji = "🔥" if priority == 1 else "⭐" if priority == 2 else "📅"
                calendar_name = "CLEANING" if priority == 1 else "WALKTHROUGH" if priority == 2 else "COMMERCIAL"
                
                print(f"\\n   {priority_emoji} Priority {priority} - {calendar_name}: {len(apt_list)} appointments")
                for apt in apt_list[:3]:  # Show first 3
                    print(f"      • {apt.start_time.strftime('%m/%d %I:%M%p')} - {apt.contact_name}")
        else:
            print("   📭 No appointments scheduled for next week")
    
    except Exception as e:
        print(f"   ❌ Error testing next week schedule: {e}")
    
    print('\n✅ Calendar Priority System Test Complete!')


if __name__ == '__main__':
    asyncio.run(test_calendar_priorities())