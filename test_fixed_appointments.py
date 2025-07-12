#!/usr/bin/env python3
"""
Test the Fixed GoHighLevel Appointments Integration
Verify that Ava can now see Destiny's Monday July 14th appointment
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.gohighlevel_service import ghl_service
from datetime import datetime


async def test_fixed_appointments():
    """Test if the fixed GoHighLevel service can now access appointments."""
    
    print("🔧 Testing FIXED GoHighLevel Appointments Integration")
    print("=" * 60)
    
    # Test 1: Connection test
    print("1. Testing API connection...")
    connection_test = await ghl_service.test_connection()
    print(f"   Status: {connection_test.get('status')}")
    print(f"   Message: {connection_test.get('message')}")
    
    # Test 2: Today's schedule
    print("\n2. Testing today's schedule...")
    try:
        today_appointments = await ghl_service.get_todays_schedule()
        print(f"   ✅ Found {len(today_appointments)} appointments today")
        
        for apt in today_appointments:
            print(f"   📅 {apt.start_time.strftime('%I:%M %p')} - {apt.contact_name}: {apt.title}")
            if 'destiny' in apt.contact_name.lower():
                print(f"      🎯 DESTINY FOUND TODAY!")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Monday July 14th, 2025 (Destiny's appointment)
    print("\n3. Testing Monday July 14th, 2025 (Destiny's recurring appointment)...")
    try:
        july_14 = datetime(2025, 7, 14, 0, 0, 0)
        july_15 = datetime(2025, 7, 15, 0, 0, 0)
        
        july_14_appointments = await ghl_service.get_appointments(july_14, july_15)
        print(f"   ✅ Found {len(july_14_appointments)} appointments on Monday July 14th")
        
        destiny_found = False
        for apt in july_14_appointments:
            print(f"   📅 {apt.start_time.strftime('%I:%M %p')} - {apt.contact_name}: {apt.title}")
            print(f"      📍 {apt.address}")
            print(f"      🏷️ Service: {apt.service_type}")
            print(f"      👤 Assigned: {apt.assigned_user}")
            
            if 'destiny' in apt.contact_name.lower():
                print(f"      🎯 DESTINY'S APPOINTMENT FOUND!")
                print(f"         📞 Phone: {apt.contact_phone}")
                print(f"         📧 Email: {apt.contact_email}")
                print(f"         📝 Notes: {apt.notes}")
                destiny_found = True
            print()
        
        if not destiny_found:
            print(f"   ❌ Destiny's appointment not found on July 14th")
            print(f"   💡 This could mean:")
            print(f"      - The appointment is in a different calendar")
            print(f"      - Different contact name spelling")
            print(f"      - Different date or recurring pattern")
            print(f"      - API scopes don't include this calendar")
                
    except Exception as e:
        print(f"   ❌ Error getting July 14th appointments: {e}")
    
    # Test 4: Check all calendars with broader date range
    print("\n4. Testing broader date range (July 10-18, 2025)...")
    try:
        july_10 = datetime(2025, 7, 10, 0, 0, 0)
        july_18 = datetime(2025, 7, 18, 23, 59, 59)
        
        week_appointments = await ghl_service.get_appointments(july_10, july_18)
        print(f"   ✅ Found {len(week_appointments)} appointments in week of July 14th")
        
        destiny_appointments = [apt for apt in week_appointments if 'destiny' in apt.contact_name.lower()]
        
        if destiny_appointments:
            print(f"   🎯 Found {len(destiny_appointments)} Destiny appointments!")
            for apt in destiny_appointments:
                print(f"      📅 {apt.start_time.strftime('%A %B %d, %Y at %I:%M %p')}")
                print(f"      📋 {apt.title}")
        else:
            print(f"   ❌ No Destiny appointments found in the week")
        
    except Exception as e:
        print(f"   ❌ Error getting week appointments: {e}")
    
    # Test 5: Test Ava's intelligent date parsing
    print("\n5. Testing Ava's intelligent response for 'Monday the 14th'...")
    try:
        from ava_intelligence_upgrade import ava_intelligence
        
        test_message = "What's on the calendar for Monday the 14th?"
        response = await ava_intelligence.handle_schedule_question(test_message)
        
        print(f"   📝 Ava's Response Preview:")
        print(f"   {response[:200]}...")
        
        if 'destiny' in response.lower():
            print(f"   🎯 Ava can see Destiny's appointment!")
        else:
            print(f"   ❌ Ava still can't see Destiny's appointment")
            
    except Exception as e:
        print(f"   ❌ Error testing Ava's response: {e}")
    
    print(f"\n" + "=" * 60)
    print("🧪 FIXED APPOINTMENTS TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_fixed_appointments())