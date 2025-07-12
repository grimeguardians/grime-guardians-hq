#!/usr/bin/env python3
"""
Test GoHighLevel v1 Appointments API to get contact information
The v1 API should return full contact details unlike v2 events
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_v1_appointments():
    """Test GoHighLevel v1 appointments API for contact information."""
    
    print("🔧 Testing GoHighLevel v1 Appointments API (with contact data)")
    print("=" * 65)
    
    # V1 API settings
    v1_base_url = "https://rest.gohighlevel.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    api_key = os.getenv('HIGHLEVEL_API_KEY')
    
    print(f"📍 Location ID: {location_id}")
    print(f"🗝️ API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    if not location_id or not api_key:
        print("❌ Missing required credentials")
        return
    
    # V1 API headers (different from v2)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"🔐 Using: v1 API Key")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Today's appointments with v1 API
        print("1. 📅 TESTING v1 APPOINTMENTS API (Today)")
        print("-" * 45)
        
        endpoint = f"/v1/appointments/"
        url = f"{v1_base_url}{endpoint}"
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    appointments = data.get('appointments', [])
                    
                    print(f"✅ v1 API Success! Found {len(appointments)} appointments")
                    print(f"📋 Response keys: {list(data.keys())}")
                    
                    for i, apt in enumerate(appointments[:3], 1):
                        print(f"\n📅 Appointment {i}:")
                        print(f"   🆔 ID: {apt.get('id')}")
                        print(f"   📋 Title: {apt.get('title', 'No title')}")
                        print(f"   🕐 Start: {apt.get('startTime', 'No time')}")
                        
                        # Check contact information
                        contact = apt.get('contact', {})
                        if contact:
                            print(f"   👤 Contact: {contact.get('name', 'Unknown')}")
                            print(f"   📧 Email: {contact.get('email', 'No email')}")
                            print(f"   📞 Phone: {contact.get('phone', 'No phone')}")
                            print(f"   🏢 Company: {contact.get('companyName', 'No company')}")
                            
                            if 'destiny' in contact.get('name', '').lower():
                                print(f"   🎯 DESTINY CONTACT FOUND WITH FULL INFO!")
                        else:
                            print(f"   ❌ No contact information")
                else:
                    response_text = await response.text()
                    print(f"❌ v1 API Error: {response.status} - {response_text[:200]}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Test 2: Try with date parameters for July 14th
        print(f"\n2. 📅 TESTING v1 APPOINTMENTS WITH DATE FILTER")
        print("-" * 50)
        
        # Try different parameter formats for v1 API
        test_endpoints = [
            "/v1/appointments/?startDate=2025-07-14&endDate=2025-07-14",
            "/v1/appointments/?start=2025-07-14&end=2025-07-14", 
            "/v1/appointments/?dateFrom=2025-07-14&dateTo=2025-07-14"
        ]
        
        for endpoint in test_endpoints:
            url = f"{v1_base_url}{endpoint}"
            print(f"\n🧪 Testing: {endpoint}")
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        appointments = data.get('appointments', [])
                        print(f"   ✅ Success! {len(appointments)} appointments")
                        
                        for apt in appointments:
                            contact = apt.get('contact', {})
                            title = apt.get('title', 'No title')
                            name = contact.get('name', 'Unknown') if contact else 'Unknown'
                            
                            print(f"   📅 {title} - {name}")
                            
                            if 'destiny' in name.lower() or 'destiny' in title.lower():
                                print(f"   🎯 DESTINY FOUND!")
                                if contact:
                                    print(f"      📧 {contact.get('email', 'No email')}")
                                    print(f"      📞 {contact.get('phone', 'No phone')}")
                    else:
                        print(f"   ❌ {response.status} error")
                        
            except Exception as e:
                print(f"   💥 Exception: {e}")
        
        # Test 3: Compare with v2 API results
        print(f"\n3. 📅 COMPARING v1 vs v2 API RESULTS")
        print("-" * 40)
        
        # V2 API test (what we're currently using)
        v2_base_url = "https://services.leadconnectorhq.com"
        pit_token = os.getenv('HIGHLEVEL_API_V2_TOKEN')
        
        if pit_token:
            v2_headers = {
                "Authorization": f"Bearer {pit_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "2021-04-15"
            }
            
            # Test today with v2 calendar events
            today = datetime.now()
            start_millis = int(today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
            end_millis = int(today.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
            
            v2_endpoint = f"/calendars/events?locationId={location_id}&calendarId=sb6IQR2sx5JXOQqMgtf5&startTime={start_millis}&endTime={end_millis}"
            v2_url = f"{v2_base_url}{v2_endpoint}"
            
            try:
                async with session.get(v2_url, headers=v2_headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get('events', [])
                        print(f"📊 v2 API: {len(events)} events")
                        print(f"📊 v1 API: Will show appointments count above")
                        print(f"💡 v1 should have contact details, v2 shows 'Unknown contact'")
                    else:
                        print(f"❌ v2 API Error: {response.status}")
            except Exception as e:
                print(f"❌ v2 Exception: {e}")
        
    print(f"\n" + "=" * 65)
    print("🧪 v1 APPOINTMENTS API TEST COMPLETE")
    print("=" * 65)
    print("💡 If v1 shows contact details, we should switch to hybrid approach!")


if __name__ == '__main__':
    asyncio.run(test_v1_appointments())