#!/usr/bin/env python3
"""
Simple Test for Ava's GoHighLevel Appointments
Tests the fixed milliseconds timestamp approach directly
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ava_appointments():
    """Test Ava's ability to see appointments using the fixed approach."""
    
    print("🔧 Testing Ava's Fixed GoHighLevel Appointments Access")
    print("=" * 60)
    
    # Get settings from environment
    base_url = "https://services.leadconnectorhq.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    pit_token = os.getenv('HIGHLEVEL_API_V2_TOKEN')
    api_key = os.getenv('HIGHLEVEL_API_KEY')
    
    print(f"📍 Location ID: {location_id}")
    print(f"🔑 PIT Token: {'✅ Available' if pit_token else '❌ Missing'}")
    print(f"🗝️ API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    if not location_id:
        print("❌ No HIGHLEVEL_LOCATION_ID found in environment")
        return
    
    # Setup headers with correct API version
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Grime-Guardians-Agent-System/1.0",
        "Version": "2021-04-15"  # Correct version from documentation
    }
    
    # Use PIT token if available, otherwise API key
    if pit_token:
        headers["Authorization"] = f"Bearer {pit_token}"
        auth_method = "PIT Token"
    elif api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        auth_method = "API Key"
    else:
        print("❌ No authentication token available")
        return
    
    print(f"🔐 Using: {auth_method}")
    print()
    
    # Calendar IDs from your priority configuration
    calendar_configs = [
        {"id": "sb6IQR2sx5JXOQqMgtf5", "name": "Cleaning Service", "priority": 1},
        {"id": "mhrQNqycH11jLZah5sJ6", "name": "Walkthrough", "priority": 2},
        {"id": "qXm41YUW2Cxc0stYERn8", "name": "Commercial Walkthrough", "priority": 3}
    ]
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Today's appointments
        print("1. 📅 TESTING TODAY'S APPOINTMENTS")
        print("-" * 40)
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        start_millis = int(today.timestamp() * 1000)
        end_millis = int(tomorrow.timestamp() * 1000)
        
        print(f"Date: {today.strftime('%A, %B %d, %Y')}")
        print(f"Time range: {start_millis} to {end_millis}")
        
        total_today = 0
        for config in calendar_configs:
            cal_id = config["id"]
            cal_name = config["name"]
            priority = config["priority"]
            
            endpoint = f"/calendars/events?locationId={location_id}&calendarId={cal_id}&startTime={start_millis}&endTime={end_millis}"
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get('events', [])
                        total_today += len(events)
                        
                        priority_emoji = "🔥" if priority == 1 else "⭐" if priority == 2 else "📅"
                        print(f"{priority_emoji} {cal_name}: {len(events)} appointments")
                        
                        for event in events:
                            title = event.get('title', 'No title')
                            contact = event.get('contact', {}).get('name', 'Unknown contact')
                            start_time = event.get('startTime', '')
                            
                            print(f"   • {start_time} - {contact}: {title}")
                            
                            if 'destiny' in contact.lower() or 'destiny' in title.lower():
                                print(f"     🎯 DESTINY APPOINTMENT FOUND!")
                    else:
                        print(f"❌ {cal_name}: {response.status} error")
                        
            except Exception as e:
                print(f"❌ {cal_name}: Error - {e}")
        
        print(f"\n📊 Total appointments today: {total_today}")
        
        # Test 2: Next Week's Schedule (Monday July 14th area)
        print(f"\n2. 📅 TESTING NEXT WEEK (July 14th, 2025 - Destiny's Day)")
        print("-" * 40)
        
        july_14 = datetime(2025, 7, 14, 0, 0, 0)  # Monday July 14th
        july_21 = datetime(2025, 7, 21, 0, 0, 0)  # Following Monday
        week_start_millis = int(july_14.timestamp() * 1000)
        week_end_millis = int(july_21.timestamp() * 1000)
        
        print(f"Week: {july_14.strftime('%A, %B %d')} to {july_21.strftime('%A, %B %d, %Y')}")
        print(f"Time range: {week_start_millis} to {week_end_millis}")
        
        total_week = 0
        destiny_found = False
        
        for config in calendar_configs:
            cal_id = config["id"]
            cal_name = config["name"]
            priority = config["priority"]
            
            endpoint = f"/calendars/events?locationId={location_id}&calendarId={cal_id}&startTime={week_start_millis}&endTime={week_end_millis}"
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get('events', [])
                        total_week += len(events)
                        
                        priority_emoji = "🔥" if priority == 1 else "⭐" if priority == 2 else "📅"
                        print(f"{priority_emoji} {cal_name}: {len(events)} appointments")
                        
                        for event in events:
                            title = event.get('title', 'No title')
                            contact = event.get('contact', {}).get('name', 'Unknown contact')
                            start_time_str = event.get('startTime', '')
                            
                            # Parse the date for display
                            try:
                                if start_time_str:
                                    start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                                    day_name = start_dt.strftime('%A %m/%d')
                                    time_str = start_dt.strftime('%I:%M %p')
                                else:
                                    day_name = "Unknown day"
                                    time_str = "Unknown time"
                            except:
                                day_name = "Parse error"
                                time_str = start_time_str
                            
                            print(f"   • {day_name} {time_str} - {contact}: {title}")
                            
                            if 'destiny' in contact.lower() or 'destiny' in title.lower():
                                print(f"     🎯 DESTINY'S RECURRING APPOINTMENT FOUND!")
                                print(f"        📍 Address: {event.get('address', 'No address')}")
                                print(f"        📋 Status: {event.get('appointmentStatus', 'Unknown')}")
                                print(f"        🔄 Recurring: {event.get('isRecurring', False)}")
                                destiny_found = True
                    else:
                        response_text = await response.text()
                        print(f"❌ {cal_name}: {response.status} - {response_text[:100]}")
                        
            except Exception as e:
                print(f"❌ {cal_name}: Error - {e}")
        
        print(f"\n📊 Total appointments in week: {total_week}")
        
        if destiny_found:
            print(f"🎯 SUCCESS! Ava can now see Destiny's appointment!")
        else:
            print(f"❌ Destiny's appointment not found")
            print(f"💡 Possible reasons:")
            print(f"   - Appointment is in a different time period")
            print(f"   - Contact name is different (not 'Destiny')")
            print(f"   - Appointment is in a calendar not covered by our API scopes")
            print(f"   - Recurring appointment pattern is different")
        
        # Test 3: Broader search for any appointments containing "Destiny"
        print(f"\n3. 🔍 SEARCHING BROADER DATE RANGE FOR DESTINY")
        print("-" * 40)
        
        # Search from July 1 to July 31, 2025
        july_1 = datetime(2025, 7, 1, 0, 0, 0)
        august_1 = datetime(2025, 8, 1, 0, 0, 0)
        month_start_millis = int(july_1.timestamp() * 1000)
        month_end_millis = int(august_1.timestamp() * 1000)
        
        print(f"Searching entire July 2025...")
        
        destiny_appointments = []
        
        for config in calendar_configs:
            cal_id = config["id"]
            cal_name = config["name"]
            
            endpoint = f"/calendars/events?locationId={location_id}&calendarId={cal_id}&startTime={month_start_millis}&endTime={month_end_millis}"
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get('events', [])
                        
                        for event in events:
                            title = event.get('title', '')
                            contact = event.get('contact', {}).get('name', '')
                            
                            if 'destiny' in contact.lower() or 'destiny' in title.lower():
                                destiny_appointments.append({
                                    'calendar': cal_name,
                                    'event': event,
                                    'contact': contact,
                                    'title': title
                                })
                        
            except Exception as e:
                print(f"❌ Error searching {cal_name}: {e}")
        
        if destiny_appointments:
            print(f"🎯 Found {len(destiny_appointments)} Destiny appointments in July 2025:")
            for apt in destiny_appointments:
                event = apt['event']
                start_time_str = event.get('startTime', '')
                try:
                    start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    formatted_time = start_dt.strftime('%A, %B %d at %I:%M %p')
                except:
                    formatted_time = start_time_str
                
                print(f"   📅 {formatted_time}")
                print(f"      📋 {apt['title']}")
                print(f"      👤 {apt['contact']}")
                print(f"      📍 Calendar: {apt['calendar']}")
                print()
        else:
            print(f"❌ No Destiny appointments found in July 2025")
    
    print("=" * 60)
    print("🧪 APPOINTMENTS TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_ava_appointments())