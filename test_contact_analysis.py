#!/usr/bin/env python3
"""
Analyze GoHighLevel contact data and determine best approach for contact information
Focus on finding Destiny and understanding contact structure
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def analyze_contacts():
    """Analyze GoHighLevel contacts to understand Destiny's data structure."""
    
    print("🔍 Analyzing GoHighLevel Contact Data Structure")
    print("=" * 55)
    
    # V1 API settings
    v1_base_url = "https://rest.gohighlevel.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    api_key = os.getenv('HIGHLEVEL_API_KEY')
    
    print(f"📍 Location ID: {location_id}")
    print(f"🗝️ API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    if not location_id or not api_key:
        print("❌ Missing required credentials")
        return
    
    # V1 API headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Analyze all contacts to find Destiny
        print("\n1. 📋 ANALYZING CONTACTS TO FIND DESTINY")
        print("-" * 45)
        
        contacts_endpoint = f"/v1/contacts/"
        contacts_url = f"{v1_base_url}{contacts_endpoint}"
        
        destiny_contact = None
        
        try:
            async with session.get(contacts_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    contacts = data.get('contacts', [])
                    print(f"✅ Found {len(contacts)} total contacts")
                    
                    print(f"\n🔍 Searching for Destiny in contacts...")
                    
                    for i, contact in enumerate(contacts, 1):
                        name = contact.get('name', 'No name')
                        email = contact.get('email', 'No email')
                        phone = contact.get('phone', 'No phone')
                        contact_id = contact.get('id', 'No ID')
                        
                        # Show all contacts to help identify patterns
                        print(f"   {i:2d}. {name} - {email} - {phone}")
                        
                        # Look for Destiny (broad search)
                        if any(keyword in name.lower() for keyword in ['destiny', 'dest']):
                            print(f"       🎯 POTENTIAL DESTINY MATCH!")
                            destiny_contact = contact
                            
                        # Also check if any contact matches appointment names we saw
                        if any(keyword in name.lower() for keyword in ['madhavi', 'mark', 'larry', 'sandra', 'david', 'diana', 'elizabeth']):
                            print(f"       📅 MATCHES APPOINTMENT: {name}")
                            
                else:
                    print(f"❌ Contacts API error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error getting contacts: {e}")
        
        # Test 2: If we found Destiny, get her appointments
        if destiny_contact:
            print(f"\n2. 📅 GETTING DESTINY'S APPOINTMENTS")
            print("-" * 35)
            
            destiny_id = destiny_contact.get('id')
            destiny_name = destiny_contact.get('name')
            
            print(f"🎯 Found Destiny: {destiny_name} (ID: {destiny_id})")
            print(f"   📧 Email: {destiny_contact.get('email', 'No email')}")
            print(f"   📞 Phone: {destiny_contact.get('phone', 'No phone')}")
            print(f"   🏢 Company: {destiny_contact.get('companyName', 'No company')}")
            
            # Get Destiny's appointments
            apt_endpoint = f"/v1/contacts/{destiny_id}/appointments/"
            apt_url = f"{v1_base_url}{apt_endpoint}"
            
            try:
                async with session.get(apt_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        appointments = data.get('appointments', [])
                        print(f"\n   📅 Destiny has {len(appointments)} appointments:")
                        
                        for apt in appointments:
                            apt_id = apt.get('id', 'No ID')
                            title = apt.get('title', 'No title')
                            start_time = apt.get('startTime', 'No time')
                            calendar_id = apt.get('calendarId', 'No calendar')
                            
                            print(f"      📋 {start_time} - {title}")
                            print(f"         🆔 ID: {apt_id}")
                            print(f"         📅 Calendar: {calendar_id}")
                            
                            # Check if this matches our Monday appointment
                            if 'monday' in start_time.lower() or '2025-07-14' in start_time:
                                print(f"         🎯 THIS IS THE MONDAY APPOINTMENT!")
                    else:
                        print(f"   ❌ Appointments API error: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error getting Destiny's appointments: {e}")
        
        # Test 3: Alternative approach - lookup contact by name
        print(f"\n3. 🔍 CONTACT LOOKUP BY NAME")
        print("-" * 30)
        
        # Try the lookup endpoint mentioned in documentation
        search_terms = ['destiny', 'Destiny', 'DESTINY']
        
        for term in search_terms:
            lookup_endpoint = f"/v1/contacts/lookup?email={term}"
            lookup_url = f"{v1_base_url}{lookup_endpoint}"
            
            try:
                async with session.get(lookup_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Lookup '{term}' found: {data}")
                    else:
                        print(f"❌ Lookup '{term}': {response.status}")
            except Exception as e:
                print(f"❌ Lookup '{term}': {e}")
        
        # Test 4: Check v2 API contact information in appointments
        print(f"\n4. 📊 COMPARING V2 APPOINTMENT CONTACT DATA")
        print("-" * 45)
        
        v2_base_url = "https://services.leadconnectorhq.com"
        pit_token = os.getenv('HIGHLEVEL_API_V2_TOKEN')
        
        if pit_token:
            v2_headers = {
                "Authorization": f"Bearer {pit_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "2021-04-15"
            }
            
            # Get today's appointments from v2 to see contact structure
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
                        print(f"📊 v2 API returned {len(events)} events")
                        
                        for event in events[:2]:
                            print(f"\n📅 Event: {event.get('title', 'No title')}")
                            print(f"   🆔 Contact ID: {event.get('contactId', 'No contact ID')}")
                            
                            contact_info = event.get('contact', {})
                            if contact_info:
                                print(f"   👤 Contact object: {contact_info}")
                            else:
                                print(f"   ❌ No contact object in v2 response")
                    else:
                        print(f"❌ v2 API error: {response.status}")
            except Exception as e:
                print(f"❌ v2 API error: {e}")
    
    print(f"\n" + "=" * 55)
    print("🧪 CONTACT ANALYSIS COMPLETE")
    print("=" * 55)
    print("💡 Next steps based on findings:")
    print("   1. If Destiny found in contacts → Use contact data")
    print("   2. If v2 has contactId → Fetch contact details separately") 
    print("   3. If neither works → Extract from appointment titles")


if __name__ == '__main__':
    asyncio.run(analyze_contacts())