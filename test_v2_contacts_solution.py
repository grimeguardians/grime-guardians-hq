#!/usr/bin/env python3
"""
V2 API Hybrid Solution for Contact Information
Uses PIT token to get appointments + contact details separately
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_v2_contact_solution():
    """Test v2 API hybrid approach: appointments + contact details."""
    
    print("🔧 Testing v2 API Hybrid Solution (Appointments + Contacts)")
    print("=" * 65)
    
    # V2 API settings
    v2_base_url = "https://services.leadconnectorhq.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    pit_token = os.getenv('HIGHLEVEL_API_V2_TOKEN')
    
    print(f"📍 Location ID: {location_id}")
    print(f"🔑 PIT Token: {'✅ Available' if pit_token else '❌ Missing'}")
    
    if not location_id or not pit_token:
        print("❌ Missing required credentials")
        return
    
    # V2 API headers
    headers = {
        "Authorization": f"Bearer {pit_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-04-15"
    }
    
    print(f"🔐 Using: PIT Token")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Get appointments (already working)
        print("1. 📅 GETTING APPOINTMENTS (Known Working)")
        print("-" * 45)
        
        today = datetime.now()
        start_millis = int(today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end_millis = int(today.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        
        appointments_endpoint = f"/calendars/events?locationId={location_id}&calendarId=sb6IQR2sx5JXOQqMgtf5&startTime={start_millis}&endTime={end_millis}"
        appointments_url = f"{v2_base_url}{appointments_endpoint}"
        
        appointments_with_contacts = []
        
        try:
            async with session.get(appointments_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('events', [])
                    print(f"✅ Found {len(events)} appointments")
                    
                    for event in events:
                        title = event.get('title', 'No title')
                        contact_id = event.get('contactId', '')
                        start_time = event.get('startTime', '')
                        
                        print(f"\n📅 Appointment: {title}")
                        print(f"   🕐 Start: {start_time}")
                        print(f"   🆔 Contact ID: {contact_id}")
                        
                        appointment_data = {
                            'appointment': event,
                            'contact_id': contact_id,
                            'contact_details': None
                        }
                        appointments_with_contacts.append(appointment_data)
                        
                else:
                    print(f"❌ Appointments API error: {response.status}")
                    return
                    
        except Exception as e:
            print(f"❌ Error getting appointments: {e}")
            return
        
        # Step 2: Test different v2 contact endpoints
        print(f"\n2. 👤 TESTING V2 CONTACT ENDPOINTS")
        print("-" * 40)
        
        # Try different v2 contact endpoint patterns
        contact_endpoints = [
            f"/contacts?locationId={location_id}",
            f"/contacts/?locationId={location_id}",
            f"/locations/{location_id}/contacts",
            f"/contacts"
        ]
        
        working_contact_endpoint = None
        
        for endpoint in contact_endpoints:
            url = f"{v2_base_url}{endpoint}"
            print(f"\n🧪 Testing: {endpoint}")
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        contacts = data.get('contacts', data.get('data', []))
                        
                        if isinstance(contacts, list) and len(contacts) > 0:
                            print(f"   ✅ Success! Found {len(contacts)} contacts")
                            working_contact_endpoint = endpoint
                            
                            # Show first few contacts
                            for i, contact in enumerate(contacts[:3], 1):
                                name = contact.get('name', 'No name')
                                email = contact.get('email', 'No email')
                                contact_id = contact.get('id', 'No ID')
                                print(f"      {i}. {name} - {email} (ID: {contact_id})")
                                
                                if 'destiny' in name.lower():
                                    print(f"         🎯 DESTINY FOUND!")
                            break
                        else:
                            print(f"   ⚠️ Success but no contacts in response")
                    else:
                        print(f"   ❌ {response.status} error")
                        
            except Exception as e:
                print(f"   💥 Exception: {e}")
        
        # Step 3: Fetch individual contact details
        if working_contact_endpoint and appointments_with_contacts:
            print(f"\n3. 🔍 FETCHING INDIVIDUAL CONTACT DETAILS")
            print("-" * 45)
            
            for i, apt_data in enumerate(appointments_with_contacts, 1):
                contact_id = apt_data['contact_id']
                apt_title = apt_data['appointment'].get('title', 'No title')
                
                print(f"\n📋 Appointment {i}: {apt_title}")
                
                if contact_id:
                    # Try different patterns for individual contact lookup
                    individual_endpoints = [
                        f"/contacts/{contact_id}?locationId={location_id}",
                        f"/contacts/{contact_id}",
                        f"/locations/{location_id}/contacts/{contact_id}"
                    ]
                    
                    for endpoint in individual_endpoints:
                        url = f"{v2_base_url}{endpoint}"
                        
                        try:
                            async with session.get(url, headers=headers) as response:
                                if response.status == 200:
                                    contact_data = await response.json()
                                    contact = contact_data.get('contact', contact_data)
                                    
                                    if isinstance(contact, dict):
                                        name = contact.get('name', 'Unknown')
                                        email = contact.get('email', 'No email')
                                        phone = contact.get('phone', 'No phone')
                                        
                                        print(f"   ✅ Contact: {name}")
                                        print(f"      📧 Email: {email}")
                                        print(f"      📞 Phone: {phone}")
                                        
                                        apt_data['contact_details'] = contact
                                        
                                        if 'destiny' in name.lower():
                                            print(f"      🎯 DESTINY CONTACT DETAILS FOUND!")
                                        
                                        break
                                else:
                                    print(f"   ❌ Contact lookup failed: {response.status}")
                                    
                        except Exception as e:
                            print(f"   💥 Contact lookup error: {e}")
                else:
                    print(f"   ❌ No contact ID available")
        
        # Step 4: Show combined results
        print(f"\n4. 📊 COMBINED APPOINTMENT + CONTACT DATA")
        print("-" * 45)
        
        for i, apt_data in enumerate(appointments_with_contacts, 1):
            apt = apt_data['appointment']
            contact = apt_data['contact_details']
            
            title = apt.get('title', 'No title')
            start_time = apt.get('startTime', 'No time')
            
            print(f"\n📅 {i}. {title}")
            print(f"   🕐 {start_time}")
            
            if contact:
                name = contact.get('name', 'Unknown')
                email = contact.get('email', 'No email')
                phone = contact.get('phone', 'No phone')
                
                print(f"   👤 Contact: {name}")
                print(f"   📧 Email: {email}")
                print(f"   📞 Phone: {phone}")
                
                if 'destiny' in name.lower():
                    print(f"   🎯 DESTINY WITH FULL CONTACT INFO!")
            else:
                print(f"   ❌ Contact: Unknown (no contact details fetched)")
        
        # Step 5: Test solution for July 14th (Destiny's day)
        print(f"\n5. 🎯 TESTING JULY 14TH (DESTINY'S DAY)")
        print("-" * 40)
        
        july_14 = datetime(2025, 7, 14, 0, 0, 0)
        july_15 = datetime(2025, 7, 15, 0, 0, 0)
        july_start_millis = int(july_14.timestamp() * 1000)
        july_end_millis = int(july_15.timestamp() * 1000)
        
        july_endpoint = f"/calendars/events?locationId={location_id}&calendarId=sb6IQR2sx5JXOQqMgtf5&startTime={july_start_millis}&endTime={july_end_millis}"
        july_url = f"{v2_base_url}{july_endpoint}"
        
        try:
            async with session.get(july_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('events', [])
                    print(f"📅 July 14th: {len(events)} appointments")
                    
                    for event in events:
                        title = event.get('title', 'No title')
                        contact_id = event.get('contactId', '')
                        
                        print(f"   📋 {title} (Contact ID: {contact_id})")
                        
                        if 'destiny' in title.lower() and contact_id and working_contact_endpoint:
                            print(f"   🎯 DESTINY FOUND - Getting contact details...")
                            
                            contact_url = f"{v2_base_url}/contacts/{contact_id}"
                            
                            async with session.get(contact_url, headers=headers) as contact_response:
                                if contact_response.status == 200:
                                    contact_data = await contact_response.json()
                                    contact = contact_data.get('contact', contact_data)
                                    
                                    name = contact.get('name', 'Unknown')
                                    email = contact.get('email', 'No email')
                                    phone = contact.get('phone', 'No phone')
                                    
                                    print(f"      👤 Full Name: {name}")
                                    print(f"      📧 Email: {email}")
                                    print(f"      📞 Phone: {phone}")
                                    print(f"      🎉 SUCCESS! No more 'Unknown contact'!")
                else:
                    print(f"❌ July 14th lookup error: {response.status}")
        except Exception as e:
            print(f"❌ July 14th test error: {e}")
    
    print(f"\n" + "=" * 65)
    print("🧪 V2 HYBRID SOLUTION TEST COMPLETE")
    print("=" * 65)
    print("💡 Key findings:")
    print("   - If contact details fetched successfully → Update GoHighLevel service")
    print("   - If contact lookup failed → May need additional scopes in PIT")
    print("   - If working → Ava will show real contact info instead of 'Unknown'")


if __name__ == '__main__':
    asyncio.run(test_v2_contact_solution())