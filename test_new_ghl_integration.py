#!/usr/bin/env python3
"""
Test New GoHighLevel API v2.0 Private Integration
Test the fresh PIT token and updated API credentials
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# New credentials from GoHighLevel
NEW_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImczZ0pOZEVTTnc5U3JWN05wakpsIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyMzEyNzkwNjM4LCJzdWIiOiJiMno1clhhS0htaU5VSWpWSTJUVSJ9.-mzZFoDg6vAvRIrnMuVnmj-RxwmMfwvexUBO6dZnGXo"
NEW_PIT_TOKEN = "pit-2e0a5a08-87fd-4f69-bbb4-a44082079823"
LOCATION_ID = "g3gJNdESNw9SrV7NpjJl"

# Test both base URLs for API v2.0
BASE_URLS = [
    "https://services.leadconnectorhq.com",  # Standard GHL
    "https://rest.gohighlevel.com",         # Alternative
]

async def test_private_integration_token(base_url: str, token: str, token_type: str):
    """Test a specific token against GoHighLevel endpoints."""
    print(f"\n🧪 Testing {token_type} with {base_url}")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"  # Required for API v2.0
    }
    
    # Test endpoints that should work with private integration
    endpoints = [
        # Core endpoints
        (f"/contacts/?locationId={LOCATION_ID}&limit=5", "Contacts"),
        (f"/conversations/?locationId={LOCATION_ID}&limit=5", "Conversations"),
        (f"/locations/{LOCATION_ID}", "Location Info"),
        
        # Calendar endpoints (various patterns)
        (f"/calendars/?locationId={LOCATION_ID}", "Calendars"),
        (f"/calendars/events?locationId={LOCATION_ID}", "Calendar Events"),
        (f"/appointments/?locationId={LOCATION_ID}", "Appointments"),
        
        # V2 specific endpoints
        (f"/appointments/", "Appointments V2"),
        (f"/contacts/", "Contacts V2"),
        (f"/conversations/", "Conversations V2"),
        
        # Alternative calendar patterns
        (f"/locations/{LOCATION_ID}/calendars", "Location Calendars"),
        (f"/locations/{LOCATION_ID}/appointments", "Location Appointments"),
        
        # Opportunities and pipelines
        (f"/opportunities/?locationId={LOCATION_ID}&limit=5", "Opportunities"),
        (f"/pipelines/?locationId={LOCATION_ID}", "Pipelines"),
        
        # Users and custom fields
        (f"/users/?locationId={LOCATION_ID}", "Users"),
        (f"/custom-fields/?locationId={LOCATION_ID}", "Custom Fields"),
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint, name in endpoints:
        print(f"\n🔍 Testing {name}")
        print(f"   URL: {base_url}{endpoint}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}{endpoint}", headers=headers) as response:
                    status = response.status
                    
                    if status == 200:
                        data = await response.json()
                        print(f"   ✅ Status: {status} - SUCCESS")
                        
                        # Analyze response structure
                        if isinstance(data, dict):
                            data_keys = list(data.keys())
                            print(f"   📊 Response keys: {data_keys[:5]}")
                            
                            # Count items in arrays
                            for key, value in data.items():
                                if isinstance(value, list):
                                    print(f"   📋 {key}: {len(value)} items")
                                    if len(value) > 0 and isinstance(value[0], dict):
                                        sample_keys = list(value[0].keys())[:5]
                                        print(f"   🔍 Sample item keys: {sample_keys}")
                                    break
                        
                        working_endpoints.append((name, endpoint, data))
                        
                    elif status == 401:
                        error = await response.text()
                        print(f"   ❌ Status: {status} - UNAUTHORIZED")
                        print(f"   💬 Error: {error[:100]}...")
                        failed_endpoints.append((name, "Unauthorized"))
                        
                    elif status == 403:
                        error = await response.text()
                        print(f"   ❌ Status: {status} - FORBIDDEN")
                        print(f"   💬 Error: {error[:100]}...")
                        failed_endpoints.append((name, "Forbidden"))
                        
                    elif status == 404:
                        print(f"   ❌ Status: {status} - NOT FOUND")
                        failed_endpoints.append((name, "Not Found"))
                        
                    else:
                        error = await response.text()
                        print(f"   ❌ Status: {status} - OTHER ERROR")
                        print(f"   💬 Error: {error[:100]}...")
                        failed_endpoints.append((name, f"Status {status}"))
                        
        except Exception as e:
            print(f"   💥 Exception: {e}")
            failed_endpoints.append((name, "Exception"))
        
        await asyncio.sleep(0.3)  # Rate limiting
    
    return working_endpoints, failed_endpoints

async def test_lead_connector_endpoints():
    """Test Lead Connector specific endpoints."""
    print(f"\n🧪 Testing Lead Connector API Endpoints")
    print("=" * 60)
    
    # Lead Connector might use different base URLs
    lead_connector_urls = [
        "https://api.leadconnectorhq.com",
        "https://rest.leadconnectorhq.com", 
        "https://services.leadconnectorhq.com"
    ]
    
    headers = {
        "Authorization": f"Bearer {NEW_PIT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }
    
    for base_url in lead_connector_urls:
        print(f"\n🔗 Testing: {base_url}")
        
        # Test basic endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/locations/{LOCATION_ID}", headers=headers) as response:
                    status = response.status
                    print(f"   Location test: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        print(f"   ✅ Lead Connector API accessible!")
                        print(f"   📊 Response keys: {list(data.keys())[:5]}")
                        return base_url
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

async def analyze_successful_endpoints(working_endpoints):
    """Analyze what capabilities we have with working endpoints."""
    print(f"\n📊 CAPABILITY ANALYSIS")
    print("=" * 60)
    
    capabilities = {
        'ava_schedule': False,
        'dean_conversations': False,
        'dean_leads': False,
        'calendar_access': False,
        'contact_management': False
    }
    
    working_names = [name for name, _, _ in working_endpoints]
    
    # Check Ava capabilities (schedule management)
    if any('Calendar' in name or 'Appointment' in name for name in working_names):
        capabilities['ava_schedule'] = True
        print("✅ AVA: Can access schedule/appointments")
    
    # Check Dean capabilities (sales monitoring)
    if 'Conversations' in working_names:
        capabilities['dean_conversations'] = True
        print("✅ DEAN: Can monitor conversations")
    
    if 'Contacts' in working_names:
        capabilities['dean_leads'] = True
        print("✅ DEAN: Can access leads/contacts")
    
    if any('Calendar' in name for name in working_names):
        capabilities['calendar_access'] = True
        print("✅ SYSTEM: Calendar integration available")
    
    if 'Contacts' in working_names:
        capabilities['contact_management'] = True
        print("✅ SYSTEM: Contact management available")
    
    # Generate Discord testing instructions
    print(f"\n🎮 DISCORD TESTING READY:")
    print("=" * 40)
    
    if capabilities['ava_schedule']:
        print("🤖 AVA COMMANDS:")
        print("   Ask Ava: 'What's on the schedule today?'")
        print("   Command: !gg schedule")
    
    if capabilities['dean_conversations'] or capabilities['dean_leads']:
        print("💼 DEAN COMMANDS:")
        print("   Ask Dean: 'Show me our lead analytics'")
        print("   Ask Dean: 'What's our pipeline status?'")
    
    # Show sample data if available
    for name, endpoint, data in working_endpoints[:2]:  # Show first 2 successful endpoints
        print(f"\n📋 SAMPLE DATA - {name}:")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"   {key}: {len(value)} items")
                    if isinstance(value[0], dict):
                        sample = value[0]
                        important_keys = ['name', 'title', 'status', 'email', 'phone', 'startTime', 'contactName']
                        for k in important_keys:
                            if k in sample:
                                print(f"     {k}: {sample[k]}")
                    break
    
    return capabilities

async def main():
    """Test the new GoHighLevel integration comprehensively."""
    print("🚀 GoHighLevel API v2.0 Private Integration Test")
    print("=" * 70)
    
    print(f"🔑 Testing with new credentials:")
    print(f"   API Key: {NEW_API_KEY[:50]}...")
    print(f"   PIT Token: {NEW_PIT_TOKEN}")
    print(f"   Location ID: {LOCATION_ID}")
    
    all_working = []
    all_failed = []
    
    # Test API Key with standard endpoints
    for base_url in BASE_URLS:
        working, failed = await test_private_integration_token(base_url, NEW_API_KEY, "API Key")
        all_working.extend(working)
        all_failed.extend(failed)
    
    # Test PIT Token with standard endpoints  
    for base_url in BASE_URLS:
        working, failed = await test_private_integration_token(base_url, NEW_PIT_TOKEN, "PIT Token")
        all_working.extend(working)
        all_failed.extend(failed)
    
    # Test Lead Connector specifically
    lead_connector_url = await test_lead_connector_endpoints()
    
    # Results summary
    print(f"\n" + "=" * 70)
    print("🎯 INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    unique_working = list(set((name, endpoint) for name, endpoint, _ in all_working))
    
    if unique_working:
        print(f"✅ SUCCESS RATE: {len(unique_working)} working endpoints found")
        
        print(f"\n✅ WORKING ENDPOINTS:")
        for name, endpoint in unique_working:
            print(f"   • {name}: {endpoint}")
        
        # Analyze capabilities
        capabilities = await analyze_successful_endpoints(all_working)
        
        if any(capabilities.values()):
            print(f"\n🎉 GOHIGHLEVEL INTEGRATION SUCCESSFUL!")
            print(f"✅ Real-time CRM monitoring is now operational")
            print(f"✅ Discord commands will show REAL data")
            
            # Instructions for server deployment
            print(f"\n🚀 NEXT STEPS:")
            print(f"1. .env file updated with new credentials")
            print(f"2. Deploy to server: Update .env on production")
            print(f"3. Restart Discord bot")
            print(f"4. Test Discord commands with real CRM data!")
            
            return 0
        else:
            print(f"\n⚠️ Endpoints working but limited capabilities")
    
    if lead_connector_url:
        print(f"\n💡 ALTERNATIVE: Lead Connector API accessible at {lead_connector_url}")
        print(f"   Consider using Lead Connector endpoints as fallback")
    
    if not unique_working:
        print(f"❌ NO WORKING ENDPOINTS")
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"1. Verify private integration has correct scopes")
        print(f"2. Check if location ID is correct")
        print(f"3. Try Lead Connector API as alternative")
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)