#!/usr/bin/env python3
"""
Test GoHighLevel v1 Appointments API with required parameters
The v1 API requires calendarId/userId/teamId parameter
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_v1_appointments_fixed():
    """Test GoHighLevel v1 appointments API with proper parameters."""
    
    print("🔧 Testing GoHighLevel v1 Appointments API (FIXED - with required params)")
    print("=" * 75)
    
    # V1 API settings
    v1_base_url = "https://rest.gohighlevel.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    api_key = os.getenv('HIGHLEVEL_API_KEY')
    
    # Calendar IDs from your setup
    calendar_ids = [
        "sb6IQR2sx5JXOQqMgtf5",  # Cleaning Service
        "mhrQNqycH11jLZah5sJ6",  # Walkthrough  
        "qXm41YUW2Cxc0stYERn8"   # Commercial
    ]
    
    print(f"📍 Location ID: {location_id}")
    print(f"🗝️ API Key: {'✅ Available' if api_key else '❌ Missing'}")
    print(f"📅 Testing {len(calendar_ids)} calendars")
    
    if not location_id or not api_key:
        print("❌ Missing required credentials")
        return
    
    # V1 API headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"🔐 Using: v1 API Key")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Today's appointments by calendar
        print("1. 📅 TESTING v1 APPOINTMENTS BY CALENDAR (Today)")
        print("-" * 55)
        
        total_appointments = 0
        
        for i, cal_id in enumerate(calendar_ids, 1):
            cal_name = ["🔥 Cleaning Service", "⭐ Walkthrough", "📅 Commercial"][i-1]
            print(f"\n{cal_name} (ID: {cal_id}):")
            
            # Try different v1 endpoint patterns with calendarId
            test_endpoints = [
                f"/v1/appointments/?calendarId={cal_id}",
                f"/v1/appointments?calendarId={cal_id}",
                f"/v1/contacts/{location_id}/appointments/?calendarId={cal_id}"  # Alternative pattern
            ]
            
            for endpoint in test_endpoints:
                url = f"{v1_base_url}{endpoint}"
                
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            appointments = data.get('appointments', [])
                            total_appointments += len(appointments)
                            
                            print(f"   ✅ Success! {len(appointments)} appointments")
                            
                            for apt in appointments[:2]:  # Show first 2
                                print(f"\n   📅 Appointment:")
                                print(f"      🆔 ID: {apt.get('id')}")
                                print(f"      📋 Title: {apt.get('title', 'No title')}")
                                print(f"      🕐 Start: {apt.get('startTime', 'No time')}")
                                
                                # Check contact information (this is what we need!)
                                contact = apt.get('contact', {})
                                if contact and isinstance(contact, dict):
                                    print(f"      👤 Contact: {contact.get('name', 'Unknown')}")
                                    print(f"      📧 Email: {contact.get('email', 'No email')}")
                                    print(f"      📞 Phone: {contact.get('phone', 'No phone')}")
                                    print(f"      🏢 Company: {contact.get('companyName', 'No company')}")
                                    
                                    if 'destiny' in contact.get('name', '').lower():
                                        print(f"      🎯 DESTINY CONTACT FOUND WITH FULL INFO!")
                                        print(f"         📧 Email: {contact.get('email')}")
                                        print(f"         📞 Phone: {contact.get('phone')}")
                                else:
                                    print(f"      ❌ No contact information in response")
                                    print(f"      🔍 Contact field type: {type(apt.get('contact'))}")
                                    print(f"      🔍 Contact value: {apt.get('contact')}")
                            
                            break  # Found working endpoint
                            
                        elif response.status == 422:
                            response_text = await response.text()
                            print(f"   ❌ 422 - Missing parameters: {response_text[:100]}")
                        else:
                            print(f"   ❌ {response.status} error")
                            
                except Exception as e:
                    print(f"   💥 Exception: {e}")
        
        print(f"\n📊 Total appointments found across all calendars: {total_appointments}")
        
        # Test 2: July 14th appointments with calendar IDs
        print(f"\n2. 📅 TESTING JULY 14TH WITH CALENDAR IDS")
        print("-" * 45)
        
        destiny_found = False
        
        for cal_id in calendar_ids:
            endpoint = f"/v1/appointments/?calendarId={cal_id}&startDate=2025-07-14&endDate=2025-07-14"
            url = f"{v1_base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        appointments = data.get('appointments', [])
                        
                        print(f"📅 Calendar {cal_id}: {len(appointments)} appointments")
                        
                        for apt in appointments:
                            contact = apt.get('contact', {})
                            title = apt.get('title', 'No title')
                            
                            if contact and isinstance(contact, dict):
                                name = contact.get('name', 'Unknown')
                                print(f"   📋 {title} - {name}")
                                
                                if 'destiny' in name.lower():
                                    print(f"   🎯 DESTINY FOUND!")
                                    print(f"      📧 Email: {contact.get('email', 'No email')}")
                                    print(f"      📞 Phone: {contact.get('phone', 'No phone')}")
                                    print(f"      🏢 Company: {contact.get('companyName', 'No company')}")
                                    destiny_found = True
                            else:
                                print(f"   📋 {title} - No contact data")
                    else:
                        print(f"❌ Calendar {cal_id}: {response.status} error")
                        
            except Exception as e:
                print(f"❌ Calendar {cal_id}: Exception - {e}")
        
        if destiny_found:
            print(f"\n🎯 SUCCESS! Found Destiny with contact information!")
        else:
            print(f"\n❌ Destiny not found or no contact information available")
        
        # Test 3: Try contact-specific appointments endpoint
        print(f"\n3. 📅 TESTING CONTACT-SPECIFIC ENDPOINTS")
        print("-" * 45)
        
        # Alternative approach - get contacts first, then their appointments
        contacts_endpoint = f"/v1/contacts/?locationId={location_id}"
        contacts_url = f"{v1_base_url}{contacts_endpoint}"
        
        try:
            async with session.get(contacts_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    contacts = data.get('contacts', [])
                    print(f"✅ Found {len(contacts)} contacts")
                    
                    # Look for Destiny in contacts
                    for contact in contacts[:5]:  # Check first 5
                        name = contact.get('name', '')
                        if 'destiny' in name.lower():
                            contact_id = contact.get('id')
                            print(f"🎯 Found Destiny contact: {name} (ID: {contact_id})")
                            print(f"   📧 Email: {contact.get('email', 'No email')}")
                            print(f"   📞 Phone: {contact.get('phone', 'No phone')}")
                            
                            # Now get this contact's appointments
                            apt_endpoint = f"/v1/contacts/{contact_id}/appointments/"
                            apt_url = f"{v1_base_url}{apt_endpoint}"
                            
                            async with session.get(apt_url, headers=headers) as apt_response:
                                if apt_response.status == 200:
                                    apt_data = await apt_response.json()
                                    appointments = apt_data.get('appointments', [])
                                    print(f"   📅 Destiny has {len(appointments)} appointments")
                                    
                                    for apt in appointments:
                                        start_time = apt.get('startTime', 'No time')
                                        title = apt.get('title', 'No title')
                                        print(f"      📋 {start_time} - {title}")
                else:
                    print(f"❌ Contacts endpoint: {response.status}")
        except Exception as e:
            print(f"❌ Contacts test: {e}")
    
    print(f"\n" + "=" * 75)
    print("🧪 v1 APPOINTMENTS API TEST COMPLETE")
    print("=" * 75)
    print("💡 Key findings:")
    print("   - v1 API requires calendarId parameter")
    print("   - Should return contact: {name, email, phone, companyName}")
    print("   - If contact data exists, we can fix the 'Unknown contact' issue!")


if __name__ == '__main__':
    asyncio.run(test_v1_appointments_fixed())