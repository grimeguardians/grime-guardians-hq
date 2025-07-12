#!/usr/bin/env python3
"""
Test the enhanced contact search using Search Contacts API
This implements the strategy from GoHighLevel API documentation
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_enhanced_contact_search():
    """Test the enhanced contact search strategy."""
    
    print("🔍 Testing Enhanced Contact Search Strategy")
    print("=" * 55)
    
    # API Configuration
    v2_base_url = "https://services.leadconnectorhq.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    pit_token = os.getenv('HIGHLEVEL_API_V2_TOKEN')
    
    print(f"📍 Location ID: {location_id}")
    print(f"🔑 PIT Token: {'✅ Available' if pit_token else '❌ Missing'}")
    
    if not location_id or not pit_token:
        print("❌ Missing required credentials")
        return
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Direct Contact Lookup (existing approach)
        print(f"\n1. 🔗 TESTING DIRECT CONTACT LOOKUP")
        print("-" * 40)
        
        # Get a sample contact ID from today's appointments
        today = datetime.now()
        start_millis = int(today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end_millis = int(today.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        
        appointments_endpoint = f"/calendars/events?locationId={location_id}&calendarId=sb6IQR2sx5JXOQqMgtf5&startTime={start_millis}&endTime={end_millis}"
        appointments_url = f"{v2_base_url}{appointments_endpoint}"
        
        # Calendar events headers (v2 API)
        calendar_headers = {
            "Authorization": f"Bearer {pit_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Version": "2021-04-15"
        }
        
        sample_contact_ids = []
        sample_titles = []
        
        try:
            async with session.get(appointments_url, headers=calendar_headers) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('events', [])
                    print(f"✅ Found {len(events)} appointments for testing")
                    
                    for event in events[:3]:  # Test first 3
                        contact_id = event.get('contactId', '')
                        title = event.get('title', 'No title')
                        if contact_id:
                            sample_contact_ids.append(contact_id)
                            sample_titles.append(title)
                            print(f"   📋 {title} (Contact ID: {contact_id})")
                else:
                    print(f"❌ Failed to get appointments: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error getting appointments: {e}")
            return
        
        # Test direct contact lookup
        contact_headers = {
            "Authorization": f"Bearer {pit_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Version": "2021-07-28"  # Contacts API version
        }
        
        print(f"\n   🧪 Testing direct contact lookup:")
        for i, contact_id in enumerate(sample_contact_ids):
            contact_url = f"{v2_base_url}/contacts/{contact_id}"
            
            try:
                async with session.get(contact_url, headers=contact_headers) as response:
                    if response.status == 200:
                        contact_data = await response.json()
                        contact = contact_data.get('contact', contact_data)
                        name = contact.get('name', 'Unknown')
                        email = contact.get('email', 'No email')
                        phone = contact.get('phone', 'No phone')
                        print(f"      ✅ {sample_titles[i]} → {name} ({email})")
                    else:
                        print(f"      ❌ {sample_titles[i]} → Failed ({response.status})")
            except Exception as e:
                print(f"      💥 {sample_titles[i]} → Error: {e}")
        
        # Test 2: Search Contacts API (NEW approach from documentation)
        print(f"\n2. 🔍 TESTING SEARCH CONTACTS API")
        print("-" * 35)
        
        # Extract names from titles for testing
        test_names = []
        for title in sample_titles:
            # Simple name extraction for testing
            if " - " in title:
                name = title.split(" - ")[0].strip()
                test_names.append(name)
            elif " " in title:
                name = title.split(" ")[0].strip()
                test_names.append(name)
        
        print(f"   📝 Extracted names for search: {test_names}")
        
        search_endpoint = f"{v2_base_url}/contacts/search"
        
        for name in test_names:
            if len(name) < 2:
                continue
                
            search_data = {
                "locationId": location_id,
                "query": name,
                "limit": 3
            }
            
            try:
                async with session.post(search_endpoint, headers=contact_headers, json=search_data) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        contacts = search_results.get('contacts', [])
                        total = search_results.get('total', 0)
                        
                        print(f"\n   🔍 Search for '{name}':")
                        print(f"      📊 Total matches: {total}")
                        
                        if contacts:
                            for j, contact in enumerate(contacts[:2], 1):
                                contact_name = contact.get('name', 'No name')
                                contact_email = contact.get('email', 'No email')
                                contact_phone = contact.get('phone', 'No phone')
                                print(f"      {j}. {contact_name} - {contact_email}")
                        else:
                            print(f"      ❌ No matches found")
                    else:
                        print(f"   ❌ Search for '{name}' failed: {response.status}")
                        response_text = await response.text()
                        print(f"      Error: {response_text[:100]}")
            except Exception as e:
                print(f"   💥 Search for '{name}' error: {e}")
        
        # Test 3: Test the enhanced hybrid strategy simulation
        print(f"\n3. 🧠 SIMULATING ENHANCED HYBRID STRATEGY")
        print("-" * 45)
        
        print("   Strategy: Direct API → Search API → Title extraction")
        
        for i, title in enumerate(sample_titles):
            print(f"\n   📋 Processing: {title}")
            
            # Step 1: Direct contact lookup
            contact_id = sample_contact_ids[i] if i < len(sample_contact_ids) else ""
            resolved_contact = None
            source = "unknown"
            
            if contact_id:
                contact_url = f"{v2_base_url}/contacts/{contact_id}"
                try:
                    async with session.get(contact_url, headers=contact_headers) as response:
                        if response.status == 200:
                            contact_data = await response.json()
                            resolved_contact = contact_data.get('contact', contact_data)
                            source = "api_direct"
                            print(f"      ✅ Direct API success")
                except:
                    pass
            
            # Step 2: Search by name if direct failed
            if not resolved_contact:
                extracted_name = title.split(" - ")[0].strip() if " - " in title else title.split(" ")[0].strip()
                if len(extracted_name) >= 2:
                    search_data = {
                        "locationId": location_id,
                        "query": extracted_name,
                        "limit": 1
                    }
                    
                    try:
                        async with session.post(search_endpoint, headers=contact_headers, json=search_data) as response:
                            if response.status == 200:
                                search_results = await response.json()
                                contacts = search_results.get('contacts', [])
                                if contacts:
                                    resolved_contact = contacts[0]
                                    source = "api_search"
                                    print(f"      ✅ Search API success")
                    except:
                        pass
            
            # Step 3: Extract from title (fallback)
            if not resolved_contact:
                extracted_name = title.split(" - ")[0].strip() if " - " in title else title.split(" ")[0].strip()
                resolved_contact = {"name": extracted_name}
                source = "extracted"
                print(f"      📝 Title extraction fallback")
            
            # Show final result
            final_name = resolved_contact.get('name', 'Unknown')
            final_email = resolved_contact.get('email', 'N/A')
            final_phone = resolved_contact.get('phone', 'N/A')
            
            print(f"      🎯 Final: {final_name} (source: {source})")
            print(f"         📧 {final_email}")
            print(f"         📞 {final_phone}")
    
    print(f"\n" + "=" * 55)
    print("🧪 ENHANCED CONTACT SEARCH TEST COMPLETE")
    print("=" * 55)
    print("💡 Expected improvements:")
    print("   ✅ Better contact resolution through Search API")
    print("   🔍 Fallback strategy: Direct → Search → Extract")
    print("   📊 More accurate name matching")
    print("   🎯 Fewer 'Unknown contact' issues")


if __name__ == '__main__':
    asyncio.run(test_enhanced_contact_search())