#!/usr/bin/env python3
"""
Test GoHighLevel Appointments vs Events API
Determine the correct endpoint for accessing Destiny's appointment
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import settings
import aiohttp
import json
from datetime import datetime


async def test_ghl_appointments():
    """Test different GoHighLevel appointment endpoints."""
    
    base_url = "https://services.leadconnectorhq.com"
    location_id = settings.highlevel_location_id
    pit_token = getattr(settings, 'highlevel_api_v2_token', None)
    api_key = settings.highlevel_api_key
    
    print("🔍 Testing GoHighLevel Appointments API Access")
    print("=" * 60)
    print(f"📍 Location ID: {location_id}")
    print(f"🔑 PIT Token: {'✅ Available' if pit_token else '❌ Missing'}")
    print(f"🗝️ API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    # Authentication headers (using correct API version from documentation)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Grime-Guardians-Agent-System/1.0",
        "Version": "2021-04-15"  # Correct version from GHL docs
    }
    
    # Use PIT token if available, otherwise API key
    if pit_token:
        headers["Authorization"] = f"Bearer {pit_token}"
        auth_method = "PIT Token"
    else:
        headers["Authorization"] = f"Bearer {api_key}"
        auth_method = "API Key"
    
    print(f"🔐 Using: {auth_method}")
    print("\n" + "=" * 60)
    
    # Convert July 14, 2025 to milliseconds (midnight to end of day)
    from datetime import datetime
    july_14_start = datetime(2025, 7, 14, 0, 0, 0)
    july_14_end = datetime(2025, 7, 14, 23, 59, 59)
    start_millis = int(july_14_start.timestamp() * 1000)
    end_millis = int(july_14_end.timestamp() * 1000)
    
    print(f"📅 July 14, 2025 in milliseconds:")
    print(f"   Start: {start_millis} ({july_14_start})")
    print(f"   End: {end_millis} ({july_14_end})")
    
    # Test the CORRECT GoHighLevel calendar events endpoint (from documentation)
    endpoints_to_test = [
        # CORRECT: Calendar Events endpoint (this is what appointments are called in GHL API)
        f"/calendars/events?locationId={location_id}&calendarId=sb6IQR2sx5JXOQqMgtf5&startTime={start_millis}&endTime={end_millis}",
        f"/calendars/events?locationId={location_id}&startTime={start_millis}&endTime={end_millis}",
        
        # Test individual calendar IDs from your priority list
        f"/calendars/events?locationId={location_id}&calendarId=mhrQNqycH11jLZah5sJ6&startTime={start_millis}&endTime={end_millis}",  # Walkthrough
        f"/calendars/events?locationId={location_id}&calendarId=qXm41YUW2Cxc0stYERn8&startTime={start_millis}&endTime={end_millis}",  # Commercial
        
        # Test broader date ranges to find any appointments
        f"/calendars/events?locationId={location_id}&calendarId=sb6IQR2sx5JXOQqMgtf5&startTime={start_millis - 86400000}&endTime={end_millis + 86400000}",  # ±1 day
        
        # Test without calendar ID (all calendars)
        f"/calendars/events?locationId={location_id}&startTime={start_millis}&endTime={end_millis}",
        
        # Legacy patterns (probably won't work but worth testing)
        f"/appointments/?locationId={location_id}&startDate=2025-07-14&endDate=2025-07-14",
        f"/appointments?locationId={location_id}&from=2025-07-14&to=2025-07-14",
        f"/calendars/appointments?locationId={location_id}",
    ]
    
    working_endpoints = []
    
    async with aiohttp.ClientSession() as session:
        for i, endpoint in enumerate(endpoints_to_test, 1):
            print(f"\n{i:2d}. Testing: {endpoint}")
            
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            print(f"    ✅ SUCCESS! Status: {response.status}")
                            print(f"    📋 Response keys: {list(data.keys())}")
                            
                            # Look for appointment data (GHL calls them "events")
                            events = data.get('events', data.get('appointments', data.get('data', data.get('bookings', []))))
                            if isinstance(events, list):
                                print(f"    📅 Found {len(events)} events/appointments")
                                
                                # Check for Destiny specifically
                                for event in events[:5]:  # Check first 5
                                    if isinstance(event, dict):
                                        # Check contact info
                                        contact_info = event.get('contactId') or event.get('contact', {})
                                        title = event.get('title', '')
                                        contact_name = ''
                                        
                                        if isinstance(contact_info, dict):
                                            contact_name = contact_info.get('name', '')
                                        
                                        # Look for Destiny in title or contact
                                        if 'destiny' in title.lower() or 'destiny' in contact_name.lower():
                                            print(f"    🎯 FOUND DESTINY! Title: {title}, Contact: {contact_name}")
                                            print(f"        📅 Start: {event.get('startTime')}")
                                            print(f"        🆔 Event ID: {event.get('id')}")
                                        elif title or contact_name:
                                            print(f"    👤 Event: {title} - Contact: {contact_name}")
                                            if event.get('startTime'):
                                                print(f"       📅 {event.get('startTime')}")
                            
                            working_endpoints.append(endpoint)
                            
                        except json.JSONDecodeError:
                            print(f"    ⚠️ Non-JSON response (Status {response.status})")
                            
                    elif response.status == 404:
                        print(f"    ❌ 404 Not Found")
                    elif response.status == 403:
                        print(f"    ❌ 403 Forbidden - Check API scopes")
                    elif response.status == 401:
                        print(f"    ❌ 401 Unauthorized - Check authentication")
                    else:
                        print(f"    ❌ {response.status}: {response_text[:100]}")
                        
            except Exception as e:
                print(f"    💥 Exception: {e}")
    
    print(f"\n" + "=" * 60)
    print("📊 DISCOVERY RESULTS")
    print("=" * 60)
    
    if working_endpoints:
        print(f"✅ Found {len(working_endpoints)} working endpoints:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
    else:
        print("❌ No working appointment endpoints found")
        print("\n💡 POSSIBLE CAUSES:")
        print("1. API scopes don't include appointment access")
        print("2. Appointments are stored differently in your GoHighLevel setup")
        print("3. Different API version needed")
        print("4. Location/calendar configuration issue")
    
    return working_endpoints


if __name__ == '__main__':
    asyncio.run(test_ghl_appointments())