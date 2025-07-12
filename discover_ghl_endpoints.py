#!/usr/bin/env python3
"""
Discover GoHighLevel API Endpoints
Try to find the correct appointments/bookings endpoints
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.gohighlevel_service import ghl_service


async def discover_endpoints():
    print('🔍 Discovering GoHighLevel API Endpoints...')
    print('=' * 60)
    
    # Test different base patterns that might work
    endpoint_patterns = [
        # Calendar-based appointment endpoints
        "/calendars/sb6IQR2sx5JXOQqMgtf5/appointments",
        "/calendars/sb6IQR2sx5JXOQqMgtf5/bookings", 
        "/calendars/sb6IQR2sx5JXOQqMgtf5/slots",
        
        # Location-based patterns
        f"/locations/{ghl_service.location_id}/bookings",
        f"/locations/{ghl_service.location_id}/appointments", 
        f"/locations/{ghl_service.location_id}/calendar-events",
        
        # API v2 patterns
        "/bookings",
        "/calendar-bookings",
        "/scheduled-appointments",
        "/calendar-appointments",
        
        # Alternative patterns
        "/calendars/bookings",
        "/calendars/scheduled",
        "/bookings/calendar",
        "/appointment-bookings",
        
        # With location parameter
        f"/bookings?locationId={ghl_service.location_id}",
        f"/calendar-bookings?locationId={ghl_service.location_id}",
        f"/scheduled?locationId={ghl_service.location_id}",
        
        # Different date formats
        f"/appointments?locationId={ghl_service.location_id}&date=2025-07-14",
        f"/bookings?locationId={ghl_service.location_id}&date=2025-07-14"
    ]
    
    print(f"🔑 Using PIT Token: {ghl_service.pit_token[:20]}...")
    print(f"📍 Location ID: {ghl_service.location_id}")
    print(f"📅 Primary Calendar ID: sb6IQR2sx5JXOQqMgtf5")
    
    working_endpoints = []
    
    for i, endpoint in enumerate(endpoint_patterns, 1):
        print(f"\\n{i:2d}. Testing: {endpoint}")
        
        try:
            response = await ghl_service._make_request("GET", endpoint)
            
            if "error" in response:
                status = response.get('status_code', 'unknown')
                error_msg = response['error']
                
                if status == 404:
                    print(f"    ❌ 404 Not Found")
                elif status == 403:
                    print(f"    ❌ 403 Forbidden - Check API scopes")
                elif status == 401:
                    print(f"    ❌ 401 Unauthorized - Check authentication")
                elif status == 400:
                    print(f"    ❌ 400 Bad Request: {error_msg}")
                else:
                    print(f"    ❌ {status}: {error_msg}")
            else:
                print(f"    ✅ SUCCESS! Response keys: {list(response.keys())}")
                working_endpoints.append(endpoint)
                
                # Check what data we got
                data_keys = [key for key in response.keys() if isinstance(response[key], list)]
                for key in data_keys:
                    items = response[key]
                    print(f"       📋 {key}: {len(items)} items")
                    
                    if items and len(items) > 0:
                        first_item = items[0]
                        if isinstance(first_item, dict):
                            print(f"       🔍 Sample keys: {list(first_item.keys())[:5]}")
                        
                        # Look for Destiny or any appointments
                        for item in items[:3]:
                            if isinstance(item, dict):
                                name_fields = ['contactName', 'name', 'contact', 'title']
                                for field in name_fields:
                                    value = item.get(field)
                                    if value and 'destiny' in str(value).lower():
                                        print(f"       🎯 FOUND DESTINY: {field} = {value}")
                                    elif value:
                                        print(f"       👤 {field}: {value}")
                                        break
                
        except Exception as e:
            print(f"    💥 Exception: {e}")
    
    print(f"\\n" + "="*60)
    print("📊 DISCOVERY RESULTS")
    print("="*60)
    
    if working_endpoints:
        print(f"✅ Found {len(working_endpoints)} working endpoints:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
    else:
        print("❌ No working appointment endpoints found")
        print("\\n💡 SUGGESTIONS:")
        print("1. Check if your GoHighLevel plan includes API access to appointments")
        print("2. Verify API scopes include calendar/appointment permissions")
        print("3. Try GoHighLevel API v1 instead of v2")
        print("4. Check if appointments are stored differently in your setup")
    
    print("\\n📋 NEXT STEPS:")
    print("- If no endpoints work, Destiny's appointment might be:")
    print("  • In a different calendar system")
    print("  • Stored as recurring events (not appointments)")
    print("  • In a calendar not accessible via API")
    print("  • Using a different GoHighLevel feature")


if __name__ == '__main__':
    asyncio.run(discover_endpoints())