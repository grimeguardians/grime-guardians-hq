#!/usr/bin/env python3
"""
Fix GoHighLevel Integration Issues
1. Fix calendar events API - requires calendarId
2. Fix conversations API endpoint
3. Remove all mock data
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.gohighlevel_service import ghl_service
from datetime import datetime, timedelta


async def test_fixed_integration():
    print('🔧 Testing FIXED GoHighLevel integration...')
    
    # Step 1: Get calendar IDs
    print('\n1. Getting calendar IDs...')
    try:
        endpoint = f'/calendars/?locationId={ghl_service.location_id}'
        response = await ghl_service._make_request('GET', endpoint)
        calendars = response.get('calendars', [])
        
        if not calendars:
            print('❌ No calendars found!')
            return
            
        print(f'✅ Found {len(calendars)} calendars:')
        calendar_ids = []
        for cal in calendars:
            cal_id = cal.get('id')
            cal_name = cal.get('name', 'Unnamed')
            calendar_ids.append(cal_id)
            print(f'   📅 {cal_name} (ID: {cal_id})')
            
    except Exception as e:
        print(f'❌ Failed to get calendars: {e}')
        return
    
    # Step 2: Test calendar events with correct endpoint
    print('\n2. Testing calendar events with calendarId...')
    try:
        # Test Monday July 14th, 2025
        target_date = datetime(2025, 7, 14)
        start_str = target_date.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_str = target_date.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        total_events = 0
        all_events = []
        
        for i, cal_id in enumerate(calendar_ids, 1):
            cal_name = calendars[i-1].get('name', 'Unknown')
            print(f'\\n   📅 Checking calendar {i}: {cal_name}')
            
            endpoint = f'/calendars/events?locationId={ghl_service.location_id}&calendarId={cal_id}&startTime={start_str}&endTime={end_str}'
            response = await ghl_service._make_request('GET', endpoint)
            
            if 'error' in response:
                print(f'   ❌ Error: {response["error"]}')
            else:
                events = response.get('events', [])
                print(f'   ✅ Found {len(events)} events')
                total_events += len(events)
                
                for j, event in enumerate(events, 1):
                    title = event.get('title', 'No title')
                    start_time = event.get('startTime', 'No time')
                    contact = event.get('contact', {})
                    contact_name = contact.get('name', event.get('contactName', 'Unknown'))
                    all_events.append(event)
                    print(f'      {j}. {title} - {contact_name} at {start_time}')
        
        print(f'\\n📊 TOTAL EVENTS FOR MONDAY JULY 14TH: {total_events}')
        if total_events > 0:
            print('✅ Calendar events are accessible!')
        else:
            print('📭 No events scheduled for that date')
            
    except Exception as e:
        print(f'❌ Calendar events test failed: {e}')
    
    # Step 3: Test conversations with correct endpoints
    print('\\n3. Testing conversations endpoints...')
    try:
        # Try different conversation endpoints
        conversation_endpoints = [
            f'/conversations?locationId={ghl_service.location_id}&limit=5',
            f'/conversations/?locationId={ghl_service.location_id}&limit=5',
            f'/locations/{ghl_service.location_id}/conversations?limit=5'
        ]
        
        for i, endpoint in enumerate(conversation_endpoints, 1):
            print(f'\\n   🧪 Testing conversations endpoint {i}:')
            print(f'   {endpoint}')
            
            response = await ghl_service._make_request('GET', endpoint)
            
            if 'error' in response:
                print(f'   ❌ Error: {response["error"]}')
                if 'status_code' in response:
                    print(f'   📟 Status: {response["status_code"]}')
            else:
                conversations = response.get('conversations', [])
                print(f'   ✅ Found {len(conversations)} conversations')
                
                if conversations:
                    print('   📱 Real conversation data:')
                    for j, conv in enumerate(conversations[:3], 1):
                        contact_name = conv.get('contact', {}).get('name', conv.get('contactName', 'Unknown'))
                        conv_type = conv.get('type', 'Unknown')
                        last_msg = conv.get('lastMessage', {}).get('body', conv.get('lastMessage', ''))
                        print(f'      {j}. {contact_name} ({conv_type})')
                        if last_msg:
                            print(f'         Last: {last_msg[:60]}...')
                    break  # Found working endpoint
                else:
                    print('   📭 No conversations in response')
                    
    except Exception as e:
        print(f'❌ Conversations test failed: {e}')
    
    print('\\n✅ Integration test complete!')


if __name__ == '__main__':
    asyncio.run(test_fixed_integration())