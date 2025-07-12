#!/usr/bin/env python3
"""
Test GoHighLevel API Key Access
Test what endpoints work with the current API key vs OAuth
"""

import asyncio
import aiohttp
from datetime import datetime

# Current API key from .env
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImczZ0pOZEVTTnc5U3JWN05wakpsIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUwODAzNjY1OTQ4LCJzdWIiOiJiMno1clhhS0htaU5VSWpWSTJUVSJ9.ny1dUhY-qqt4np11n5uG-WmdVRWprF0clMhDWfluxdI"
LOCATION_ID = "g3gJNdESNw9SrV7NpjJl"
BASE_URL = "https://services.leadconnectorhq.com"

async def test_api_key_endpoints():
    """Test GoHighLevel endpoints with API key authentication."""
    print("🚀 Testing GoHighLevel API Key Access")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }
    
    # Test various endpoint patterns
    endpoints = [
        # Contacts 
        (f"/contacts/?locationId={LOCATION_ID}&limit=5", "Contacts"),
        
        # Conversations
        (f"/conversations/?locationId={LOCATION_ID}&limit=5", "Conversations"),
        
        # Location info
        (f"/locations/{LOCATION_ID}", "Location Info"),
        
        # Calendar/Appointments
        (f"/calendars/?locationId={LOCATION_ID}", "Calendars"),
        (f"/calendars/events?locationId={LOCATION_ID}", "Calendar Events"),
        (f"/appointments/?locationId={LOCATION_ID}", "Appointments"),
        
        # Alternative appointment endpoints
        (f"/appointments/", "Appointments (no location)"),
        (f"/locations/{LOCATION_ID}/appointments", "Location Appointments"),
        
        # Opportunities/Pipeline
        (f"/opportunities/?locationId={LOCATION_ID}&limit=5", "Opportunities"),
        
        # Other potential endpoints
        (f"/users/?locationId={LOCATION_ID}", "Users"),
        (f"/pipelines/?locationId={LOCATION_ID}", "Pipelines"),
        (f"/custom-values/?locationId={LOCATION_ID}", "Custom Values"),
    ]
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint, name in endpoints:
        print(f"\n🧪 Testing {name}")
        print(f"   URL: {BASE_URL}{endpoint}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                    status = response.status
                    
                    if status == 200:
                        data = await response.json()
                        print(f"   ✅ Status: {status} - SUCCESS")
                        
                        # Show data structure
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"   📊 {key}: {len(value)} items")
                                    # Show sample item structure
                                    if len(value) > 0 and isinstance(value[0], dict):
                                        sample_keys = list(value[0].keys())[:5]
                                        print(f"   🔍 Sample keys: {sample_keys}")
                                    break
                            else:
                                keys = list(data.keys())[:5]
                                print(f"   📋 Response keys: {keys}")
                        
                        working_endpoints.append((name, endpoint))
                        
                    elif status == 404:
                        print(f"   ❌ Status: {status} - NOT FOUND")
                        failed_endpoints.append((name, "Not Found"))
                        
                    elif status == 401:
                        error_text = await response.text()
                        print(f"   ❌ Status: {status} - UNAUTHORIZED")
                        print(f"   💬 Error: {error_text[:100]}...")
                        failed_endpoints.append((name, "Unauthorized"))
                        
                    elif status == 403:
                        error_text = await response.text()
                        print(f"   ❌ Status: {status} - FORBIDDEN")
                        print(f"   💬 Error: {error_text[:100]}...")
                        failed_endpoints.append((name, "Forbidden"))
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Status: {status} - OTHER ERROR")
                        print(f"   💬 Error: {error_text[:100]}...")
                        failed_endpoints.append((name, f"Status {status}"))
                        
        except Exception as e:
            print(f"   💥 Exception: {e}")
            failed_endpoints.append((name, "Exception"))
        
        await asyncio.sleep(0.3)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 API KEY ACCESS RESULTS")
    print("=" * 60)
    
    if working_endpoints:
        print("✅ WORKING ENDPOINTS:")
        for name, endpoint in working_endpoints:
            print(f"   • {name}: {endpoint}")
        
        print(f"\n🎯 SUCCESS RATE: {len(working_endpoints)}/{len(endpoints)}")
        
        # Determine what we can do
        working_names = [name for name, _ in working_endpoints]
        
        capabilities = []
        if "Contacts" in working_names:
            capabilities.append("✅ Dean can monitor leads and contacts")
        if "Conversations" in working_names:
            capabilities.append("✅ Dean can monitor conversations")
        if any("Calendar" in name or "Appointment" in name for name in working_names):
            capabilities.append("✅ Ava can access calendar/appointments")
        if "Location Info" in working_names:
            capabilities.append("✅ Basic location information available")
        
        if capabilities:
            print("\n🚀 AVAILABLE CAPABILITIES:")
            for capability in capabilities:
                print(f"   {capability}")
        
        print("\n💬 DISCORD TESTING READY:")
        if "Contacts" in working_names or "Conversations" in working_names:
            print("   Ask Dean: 'Show me our lead analytics'")
        if any("Calendar" in name or "Appointment" in name for name in working_names):
            print("   Ask Ava: 'What's on the schedule today?'")
        
    else:
        print("❌ NO WORKING ENDPOINTS")
        print("   API key may be invalid or expired")
    
    if failed_endpoints:
        print(f"\n❌ FAILED ENDPOINTS ({len(failed_endpoints)}):")
        for name, reason in failed_endpoints:
            print(f"   • {name}: {reason}")
    
    return len(working_endpoints) > 0

async def main():
    """Run the API key test."""
    success = await test_api_key_endpoints()
    
    if success:
        print("\n🎉 API KEY INTEGRATION WORKING!")
        print("\n📋 Next Steps:")
        print("1. Test Discord commands with working endpoints")
        print("2. Ava and Dean will use real CRM data where available")
        print("3. Fallback to mock data for unavailable endpoints")
        
        print("\n🔧 To get full access:")
        print("1. Regenerate OAuth credentials in GoHighLevel")
        print("2. Add calendar and opportunities scopes")
        print("3. Update .env file with new tokens")
    else:
        print("\n❌ API KEY ACCESS FAILED")
        print("API key may need regeneration in GoHighLevel dashboard")
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)