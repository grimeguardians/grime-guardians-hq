#!/usr/bin/env python3
"""
Simple GoHighLevel API v2.0 Test Script
Tests the new API endpoints directly with the updated token
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# API Configuration
HIGHLEVEL_API_V2_TOKEN = "pit-49860622-40e2-46b1-ab02-db524aed510a"
HIGHLEVEL_LOCATION_ID = "JaBwKR9RJfvITmGZGuvO"

BASE_URL = "https://services.leadconnectorhq.com"

async def test_api_endpoint(endpoint: str, description: str):
    """Test a specific API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {HIGHLEVEL_API_V2_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"  # Required for GHL API v2.0
    }
    
    print(f"\n🧪 Testing {description}")
    print(f"   URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    print(f"   ✅ Status: {status} - SUCCESS")
                    
                    # Show sample data structure
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]  # First 5 keys
                        print(f"   📊 Data keys: {keys}")
                        
                        # Count items if it's a list
                        for key, value in data.items():
                            if isinstance(value, list):
                                print(f"   📋 {key}: {len(value)} items")
                                break
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ Status: {status} - FAILED")
                    print(f"   💬 Response: {error_text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return False

async def main():
    """Test all GoHighLevel API endpoints."""
    print("🚀 GoHighLevel API v2.0 Direct Test")
    print("=" * 50)
    
    # Test various endpoint patterns for v2.0 API
    endpoints_to_test = [
        # Contacts (known working)
        (f"/contacts/?locationId={HIGHLEVEL_LOCATION_ID}&limit=5", "Contacts API"),
        
        # Calendar/Appointments (various patterns)
        (f"/calendars/events?locationId={HIGHLEVEL_LOCATION_ID}", "Calendar Events"),
        (f"/calendars/appointments?locationId={HIGHLEVEL_LOCATION_ID}", "Calendar Appointments"),
        (f"/appointments?locationId={HIGHLEVEL_LOCATION_ID}", "Appointments Direct"),
        (f"/appointments/?locationId={HIGHLEVEL_LOCATION_ID}", "Appointments with Slash"),
        
        # Conversations
        (f"/conversations?locationId={HIGHLEVEL_LOCATION_ID}&limit=5", "Conversations Direct"),
        (f"/conversations/?locationId={HIGHLEVEL_LOCATION_ID}&limit=5", "Conversations with Slash"),
        
        # Locations
        (f"/locations/{HIGHLEVEL_LOCATION_ID}", "Location Info"),
        
        # Users  
        (f"/users?locationId={HIGHLEVEL_LOCATION_ID}", "Users"),
        
        # Pipelines
        (f"/opportunities/pipelines?locationId={HIGHLEVEL_LOCATION_ID}", "Pipelines"),
        
        # Companies (might show available endpoints)
        (f"/companies", "Companies"),
    ]
    
    results = []
    
    for endpoint, description in endpoints_to_test:
        result = await test_api_endpoint(endpoint, description)
        results.append((description, result))
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    working_endpoints = []
    failed_endpoints = []
    
    for description, result in results:
        if result:
            working_endpoints.append(description)
            print(f"✅ {description}")
        else:
            failed_endpoints.append(description)
            print(f"❌ {description}")
    
    print(f"\n🎯 SUCCESS RATE: {len(working_endpoints)}/{len(results)}")
    
    if working_endpoints:
        print(f"\n✅ WORKING ENDPOINTS:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
    
    if failed_endpoints:
        print(f"\n❌ FAILED ENDPOINTS:")
        for endpoint in failed_endpoints:
            print(f"   • {endpoint}")
    
    return len(working_endpoints) > 0

if __name__ == '__main__':
    success = asyncio.run(main())
    print(f"\n{'🎉 API ACCESS CONFIRMED' if success else '⚠️ API ACCESS ISSUES'}")