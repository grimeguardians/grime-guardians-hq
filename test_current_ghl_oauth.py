#!/usr/bin/env python3
"""
Test Current GoHighLevel OAuth Integration
Using the actual OAuth token from .env file
"""

import asyncio
import aiohttp
from datetime import datetime

# Current OAuth credentials from .env
OAUTH_ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoQ2xhc3MiOiJMb2NhdGlvbiIsImF1dGhDbGFzc0lkIjoiZzNnSk5kRVNOdzlTclY3TnBqSmwiLCJzb3VyY2UiOiJJTlRFR1JBVElPTiIsInNvdXJjZUlkIjoiNjg1YjQ3ZGI5OGQwMDcyMTVlMjc2MGMwLW1jYmxmYzR0IiwiY2hhbm5lbCI6Ik9BVVRIIiwicHJpbWFyeUF1dGhDbGFzc0lkIjoiZzNnSk5kRVNOdzlTclY3TnBqSmwiLCJvYXV0aE1ldGEiOnsic2NvcGVzIjpbImNvbnZlcnNhdGlvbnMvbWVzc2FnZS5yZWFkb25seSIsImNvbnZlcnNhdGlvbnMvbWVzc2FnZS53cml0ZSIsImNvbnRhY3RzLnJlYWRvbmx5IiwiY29udGFjdHMud3JpdGUiLCJjb252ZXJzYXRpb25zLnJlYWRvbmx5IiwiY29udmVyc2F0aW9ucy53cml0ZSIsImxvY2F0aW9ucy5yZWFkb25seSJdLCJjbGllbnQiOiI2ODViNDdkYjk4ZDAwNzIxNWUyNzYwYzAiLCJ2ZXJzaW9uSWQiOiI2ODViNDdkYjk4ZDAwNzIxNWUyNzYwYzAiLCJjbGllbnRLZXkiOiI2ODViNDdkYjk4ZDAwNzIxNWUyNzYwYzAtbWNibGZjNHQifSwiaWF0IjoxNzUwOTE5MjEzLjkzLCJleHAiOjE3NTEwMDU2MTMuOTN9.PexRH4iVqoZA5si7jkr3M8ABObO60gc78NMNeHRLVLnGhPW3n7aT1id8wCW80R2Sr_3K8OyGmvj0q-8nzrisdhrRRfqMMoCkH_YCGyJlSW0et5pRu45k-cRYKAyjGD53_MzxO4bvq02C3QwD89YctkxePIr5YOkbXGc0q4U_ZMVRnKVds9pKD-qNcuTLTIT7-YT6_FBEW-QjcRVO5uTsj5vBStQVbT5D6Lq1ZcTToIVndEI1DRTppuRKAutzey6qkCEWj5o_KgdKhc7T6MtmlqaYv25HsJnILK1aYw7cSWGsO7odwLXfUPppvJk_MRwWLXajziFwP4q0mGTtVFBlhiIA8liT0aSDEEeGj6WTvtDjDpXsXPAXgJOfTlvFOGs7Bhq3QwzPJtxPhcBc-l9BMwqN1wZMtWZcvRYE9m-ib4-sRvoQeoNk9-3QujzPb5h25rFHVV5_c9FIka1kxOsXuuHLhIVFh28IbgCOKUIndTEYaAw_sBOVL2lzH7XU4lFgcNyM8TOIfUFRSeUNLYIo7Yeh2e7MZ0irZsIT05U7PU49AMQ7P-oNSNG28gebpH3d-IO7WDj8hBJK_4x2TlK0iX0BBbUP_reVlPO48yY6xL1P8r0aGTcWbJkfGAAuf5IL1Vqo8EgxeOna1sEfaZVqZggKytMHyC990C0FAljt_Zk"
LOCATION_ID = "g3gJNdESNw9SrV7NpjJl"
BASE_URL = "https://services.leadconnectorhq.com"

async def test_oauth_endpoints():
    """Test GoHighLevel endpoints with current OAuth token."""
    print("🚀 Testing Current GoHighLevel OAuth Integration")
    print("=" * 60)
    
    # Check token expiry first
    token_expiry = 1751005613973 / 1000  # Convert to seconds
    current_time = datetime.now().timestamp()
    
    if current_time > token_expiry:
        print("⚠️  WARNING: OAuth token may be expired")
        print(f"   Token expires: {datetime.fromtimestamp(token_expiry)}")
        print(f"   Current time:  {datetime.fromtimestamp(current_time)}")
    else:
        time_left = (token_expiry - current_time) / 3600  # Hours
        print(f"✅ OAuth token valid for {time_left:.1f} more hours")
    
    headers = {
        "Authorization": f"Bearer {OAUTH_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }
    
    # Test endpoints that should work with current scopes
    endpoints = [
        # Contacts (should work - has contacts.readonly scope)
        (f"/contacts/?locationId={LOCATION_ID}&limit=5", "Contacts"),
        
        # Conversations (should work - has conversations.readonly scope)  
        (f"/conversations/?locationId={LOCATION_ID}&limit=5", "Conversations"),
        
        # Location info (should work - has locations.readonly scope)
        (f"/locations/{LOCATION_ID}", "Location Info"),
        
        # Calendar/Appointments (may not work - no calendar scopes visible)
        (f"/calendars/?locationId={LOCATION_ID}", "Calendars"),
        (f"/calendars/events?locationId={LOCATION_ID}", "Calendar Events"),
        
        # Opportunities (may not work - no opportunities scope)
        (f"/opportunities/?locationId={LOCATION_ID}&limit=5", "Opportunities"),
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
                                if isinstance(value, list):
                                    print(f"   📊 {key}: {len(value)} items")
                                    break
                            else:
                                keys = list(data.keys())[:3]
                                print(f"   📋 Keys: {keys}")
                        
                        working_endpoints.append(name)
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Status: {status} - FAILED")
                        if error_text:
                            print(f"   💬 Error: {error_text[:100]}...")
                        failed_endpoints.append(name)
                        
        except Exception as e:
            print(f"   💥 Exception: {e}")
            failed_endpoints.append(name)
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if working_endpoints:
        print("✅ WORKING ENDPOINTS:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
    
    if failed_endpoints:
        print("\n❌ FAILED ENDPOINTS:")
        for endpoint in failed_endpoints:
            print(f"   • {endpoint}")
    
    print(f"\n🎯 SUCCESS RATE: {len(working_endpoints)}/{len(endpoints)}")
    
    # Recommendations
    if len(working_endpoints) > 0:
        print("\n🔧 RECOMMENDATIONS:")
        print("✅ OAuth token is working for some endpoints")
        
        if "Contacts" in working_endpoints:
            print("✅ Dean can monitor contact/lead data")
        
        if "Conversations" in working_endpoints:
            print("✅ Dean can monitor conversations")
        
        if "Calendars" not in working_endpoints and "Calendar Events" not in working_endpoints:
            print("⚠️  Calendar access may need additional scopes")
            print("   Consider adding 'calendars.readonly' to OAuth scopes")
        
        if len(working_endpoints) >= 2:
            print("\n🚀 READY FOR DISCORD TESTING:")
            print("   Ask Ava: 'What's on the schedule today?'")
            print("   Ask Dean: 'Show me our lead analytics'")
    else:
        print("\n❌ OAuth token needs refresh or additional scopes")
    
    return len(working_endpoints) > 0

if __name__ == '__main__':
    success = asyncio.run(test_oauth_endpoints())
    print(f"\n{'🎉 OAUTH INTEGRATION READY' if success else '⚠️ OAUTH NEEDS ATTENTION'}")