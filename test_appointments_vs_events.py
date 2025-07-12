#!/usr/bin/env python3
"""
Test Appointments vs Events in GoHighLevel
Check the difference between /appointments and /calendars/events endpoints
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.gohighlevel_service import ghl_service
from datetime import datetime, timedelta


async def test_appointments_vs_events():
    print('🔍 Testing APPOINTMENTS vs EVENTS in GoHighLevel...')
    print('=' * 60)
    
    target_date = datetime(2025, 7, 14)  # Monday July 14th
    start_str = target_date.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_str = target_date.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    print(f"📅 Target Date: {target_date.strftime('%A, %B %d, %Y')}")
    print(f"🕐 Time Range: {start_str} to {end_str}")
    
    # Test 1: Appointments API endpoints
    print('\n1. TESTING APPOINTMENTS ENDPOINTS:')
    print('=' * 40)
    
    appointments_endpoints = [
        f"/appointments/?locationId={ghl_service.location_id}&startDate=2025-07-14&endDate=2025-07-14",
        f"/appointments?locationId={ghl_service.location_id}&from=2025-07-14&to=2025-07-14",
        f"/appointments?locationId={ghl_service.location_id}&startTime={start_str}&endTime={end_str}",
        f"/locations/{ghl_service.location_id}/appointments?startDate=2025-07-14&endDate=2025-07-14",
        f"/calendars/appointments?locationId={ghl_service.location_id}&startDate=2025-07-14&endDate=2025-07-14"
    ]
    
    for i, endpoint in enumerate(appointments_endpoints, 1):
        print(f"\\n🧪 Testing appointments endpoint {i}:")
        print(f"   {endpoint}")
        
        try:
            response = await ghl_service._make_request("GET", endpoint)
            
            if "error" in response:
                print(f"   ❌ Error: {response['error']}")
                if 'status_code' in response:
                    print(f"   📟 Status: {response['status_code']}")
            else:
                appointments = response.get("appointments", response.get("data", []))
                print(f"   ✅ Response keys: {list(response.keys())}")
                print(f"   📅 Found {len(appointments)} appointments")
                
                if appointments:
                    print(f"   📋 Appointment details:")
                    for j, apt in enumerate(appointments[:3], 1):
                        contact_name = apt.get('contact', {}).get('name', apt.get('contactName', 'Unknown'))
                        title = apt.get('title', apt.get('appointmentTitle', 'No title'))
                        start_time = apt.get('startTime', apt.get('dateTime', 'No time'))
                        print(f"      {j}. {title} - {contact_name} at {start_time}")
                        
                        # Check if this is Destiny
                        if 'destiny' in contact_name.lower():
                            print(f"      🎯 FOUND DESTINY! {contact_name}")
                else:
                    print(f"   📭 No appointments found")
                    
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    # Test 2: Compare with Events (what we were checking before)
    print('\n\\n2. TESTING EVENTS ENDPOINTS (what we were checking):')
    print('=' * 40)
    
    from src.config.settings import GOHIGHLEVEL_CALENDARS
    
    for key, config in GOHIGHLEVEL_CALENDARS.items():
        cal_id = config['id']
        cal_name = config['name']
        
        print(f"\\n📅 {cal_name} (Events):")
        endpoint = f"/calendars/events?locationId={ghl_service.location_id}&calendarId={cal_id}&startTime={start_str}&endTime={end_str}"
        
        try:
            response = await ghl_service._make_request("GET", endpoint)
            
            if "error" not in response:
                events = response.get("events", [])
                print(f"   ✅ Found {len(events)} events")
                
                for event in events:
                    contact_name = event.get('contact', {}).get('name', event.get('contactName', 'Unknown'))
                    title = event.get('title', 'No title')
                    start_time = event.get('startTime', 'No time')
                    print(f"      • {title} - {contact_name} at {start_time}")
            else:
                print(f"   ❌ Error: {response['error']}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    # Test 3: Check next 7 days for any appointments
    print('\n\\n3. CHECKING NEXT 7 DAYS FOR APPOINTMENTS:')
    print('=' * 40)
    
    for days_ahead in range(7):
        check_date = datetime.now() + timedelta(days=days_ahead)
        date_str = check_date.strftime('%Y-%m-%d')
        day_name = check_date.strftime('%A, %B %d')
        
        print(f"\\n📅 {day_name}:")
        
        # Try the most promising appointments endpoint
        endpoint = f"/appointments/?locationId={ghl_service.location_id}&startDate={date_str}&endDate={date_str}"
        
        try:
            response = await ghl_service._make_request("GET", endpoint)
            
            if "error" not in response:
                appointments = response.get("appointments", response.get("data", []))
                print(f"   ✅ {len(appointments)} appointments")
                
                for apt in appointments:
                    contact_name = apt.get('contact', {}).get('name', apt.get('contactName', 'Unknown'))
                    title = apt.get('title', apt.get('appointmentTitle', 'No title'))
                    print(f"      • {title} - {contact_name}")
                    
                    if 'destiny' in contact_name.lower():
                        print(f"      🎯 FOUND DESTINY ON {day_name}!")
            else:
                print(f"   ❌ Error: {response['error']}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    print('\\n✅ Appointments vs Events Test Complete!')


if __name__ == '__main__':
    asyncio.run(test_appointments_vs_events())