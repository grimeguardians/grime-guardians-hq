#!/usr/bin/env python3
"""
Test the Search Contacts API with correct parameters
Quick test to verify the API works with proper filters
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_search_api():
    """Test Search Contacts API with correct parameters."""
    
    print("🔍 Testing Search Contacts API Parameters")
    print("=" * 45)
    
    # API Configuration
    v2_base_url = "https://services.leadconnectorhq.com"
    location_id = os.getenv('HIGHLEVEL_LOCATION_ID')
    pit_token = os.getenv('HIGHLEVEL_API_V2_TOKEN')
    
    print(f"📍 Location ID: {location_id}")
    print(f"🔑 PIT Token: {'✅ Available' if pit_token else '❌ Missing'}")
    
    if not location_id or not pit_token:
        print("❌ Missing required credentials")
        return
    
    # Contact headers with proper version
    headers = {
        "Authorization": f"Bearer {pit_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"  # Contacts API version
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Simple search with correct parameters
        print(f"\n1. 🧪 TESTING SEARCH WITH FILTERS")
        print("-" * 35)
        
        search_endpoint = f"{v2_base_url}/contacts/search"
        test_names = ["Madhavi", "Whitney", "Alex", "Destiny"]
        
        for name in test_names:
            print(f"\n   🔍 Searching for: {name}")
            
            # Use the correct Search API format from documentation
            search_data = {
                "locationId": location_id,
                "filters": [
                    {
                        "field": "name",
                        "operator": "contains",
                        "value": name
                    }
                ],
                "pageLimit": 5
            }
            
            try:
                async with session.post(search_endpoint, headers=headers, json=search_data) as response:
                    print(f"      📊 Status: {response.status}")
                    
                    if response.status == 200:
                        search_results = await response.json()
                        contacts = search_results.get('contacts', [])
                        total = search_results.get('total', 0)
                        
                        print(f"      ✅ Found {len(contacts)} contacts (total: {total})")
                        
                        for i, contact in enumerate(contacts[:2], 1):
                            contact_name = contact.get('name', 'No name')
                            contact_email = contact.get('email', 'No email')
                            contact_phone = contact.get('phone', 'No phone')
                            print(f"         {i}. {contact_name}")
                            print(f"            📧 {contact_email}")
                            print(f"            📞 {contact_phone}")
                    else:
                        response_text = await response.text()
                        print(f"      ❌ Error: {response_text[:200]}")
                        
            except Exception as e:
                print(f"      💥 Exception: {e}")
        
        # Test 2: Simple search without filters (broader search)
        print(f"\n2. 🧪 TESTING SIMPLE SEARCH (NO FILTERS)")
        print("-" * 40)
        
        # Try simple search without complex filters
        simple_search_data = {
            "locationId": location_id,
            "pageLimit": 10
        }
        
        try:
            async with session.post(search_endpoint, headers=headers, json=simple_search_data) as response:
                print(f"   📊 Status: {response.status}")
                
                if response.status == 200:
                    search_results = await response.json()
                    contacts = search_results.get('contacts', [])
                    total = search_results.get('total', 0)
                    
                    print(f"   ✅ Found {len(contacts)} contacts (total: {total})")
                    print(f"   📋 Sample contacts:")
                    
                    for i, contact in enumerate(contacts[:3], 1):
                        contact_name = contact.get('name', 'No name')
                        contact_email = contact.get('email', 'No email')
                        print(f"      {i}. {contact_name} - {contact_email}")
                        
                        # Check if any contain our target names
                        if any(target in contact_name.lower() for target in ['madhavi', 'whitney', 'alex', 'destiny']):
                            print(f"         🎯 TARGET FOUND!")
                else:
                    response_text = await response.text()
                    print(f"   ❌ Error: {response_text[:200]}")
                    
        except Exception as e:
            print(f"   💥 Exception: {e}")
        
        # Test 3: Alternative search methods
        print(f"\n3. 🧪 TESTING ALTERNATIVE CONTACT ACCESS")
        print("-" * 40)
        
        # Try the deprecated but simpler GET contacts endpoint
        get_contacts_endpoint = f"/contacts/?locationId={location_id}&limit=10"
        get_contacts_url = f"{v2_base_url}{get_contacts_endpoint}"
        
        try:
            async with session.get(get_contacts_url, headers=headers) as response:
                print(f"   📊 GET /contacts Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    contacts = data.get('contacts', [])
                    
                    print(f"   ✅ GET method found {len(contacts)} contacts")
                    
                    for i, contact in enumerate(contacts[:3], 1):
                        contact_name = contact.get('name', 'No name')
                        contact_email = contact.get('email', 'No email')
                        print(f"      {i}. {contact_name} - {contact_email}")
                else:
                    response_text = await response.text()
                    print(f"   ❌ GET method error: {response_text[:200]}")
                    
        except Exception as e:
            print(f"   💥 GET method exception: {e}")
    
    print(f"\n" + "=" * 45)
    print("🧪 SEARCH API TEST COMPLETE")
    print("=" * 45)
    print("💡 Next steps:")
    print("   • If Search API works → Use it for contact resolution")
    print("   • If Search API fails → Check PIT token scopes")
    print("   • Update hybrid strategy based on results")


if __name__ == '__main__':
    asyncio.run(test_search_api())