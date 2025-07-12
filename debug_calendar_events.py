#!/usr/bin/env python3
"""
Debug GoHighLevel Calendar Events Access
Test if we can retrieve calendar events vs just calendars
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.gohighlevel_service import ghl_service
from datetime import datetime, timedelta


async def test_calendar_events():
    print('🔍 Testing GoHighLevel calendar events access...')
    
    # Test 1: Get calendars
    print('\n1. Testing calendar list...')
    try:
        endpoint = f'/calendars/?locationId={ghl_service.location_id}'
        response = await ghl_service._make_request('GET', endpoint)
        calendars = response.get('calendars', [])
        print(f'✅ Found {len(calendars)} calendars')
        
        calendar_ids = []
        for cal in calendars:
            cal_id = cal.get('id', 'Unknown')
            cal_name = cal.get('name', 'Unnamed')
            calendar_ids.append(cal_id)
            print(f'   📅 {cal_name} (ID: {cal_id})')
            
    except Exception as e:
        print(f'❌ Calendar test failed: {e}')
        return
    
    # Test 2: Get events for Monday July 14th, 2025
    print('\n2. Testing calendar events for Monday July 14th, 2025...')
    try:
        target_date = datetime(2025, 7, 14)
        start_str = target_date.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_str = target_date.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        print(f'   🗓️  Target date: {target_date.strftime("%A, %B %d, %Y")}')
        print(f'   🕐 Start time: {start_str}')
        print(f'   🕐 End time: {end_str}')
        
        # Try different calendar event endpoints
        endpoints_to_test = [
            f'/calendars/events?locationId={ghl_service.location_id}&startTime={start_str}&endTime={end_str}',
            f'/appointments/?locationId={ghl_service.location_id}&startDate=2025-07-14&endDate=2025-07-14',
            f'/calendars/events?locationId={ghl_service.location_id}&from={start_str}&to={end_str}',
        ]
        
        # Add specific calendar tests if we have calendar IDs
        if calendar_ids:
            for cal_id in calendar_ids[:2]:  # Test first 2 calendars
                endpoints_to_test.append(
                    f'/calendars/events?locationId={ghl_service.location_id}&calendarId={cal_id}&startTime={start_str}&endTime={end_str}'
                )
        
        for i, endpoint in enumerate(endpoints_to_test, 1):
            print(f'\n   🧪 Testing endpoint {i}: {endpoint[:80]}...')
            try:
                response = await ghl_service._make_request('GET', endpoint)
                if 'error' in response:
                    print(f'   ❌ Error: {response["error"]}')
                    if 'status_code' in response:
                        print(f'   📟 Status: {response["status_code"]}')
                else:
                    events = response.get('events', response.get('appointments', []))
                    print(f'   ✅ Response keys: {list(response.keys())}')
                    print(f'   📅 Found {len(events)} events')
                    
                    if events:
                        print(f'   📋 Event details:')
                        for j, event in enumerate(events[:3], 1):  # Show first 3
                            title = event.get('title', 'No title')
                            start_time = event.get('startTime', 'No time')
                            contact = event.get('contact', {})
                            contact_name = contact.get('name', event.get('contactName', 'Unknown'))
                            print(f'      {j}. {title} - {contact_name} at {start_time}')
                    else:
                        print(f'   📭 No events found in response')
                        
            except Exception as e:
                print(f'   ❌ Endpoint {i} failed: {e}')
    
    except Exception as e:
        print(f'❌ Events test failed: {e}')
    
    # Test 3: Check for today's events
    print('\n3. Testing today\'s events...')
    try:
        today = datetime.now()
        start_str = today.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_str = today.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        endpoint = f'/calendars/events?locationId={ghl_service.location_id}&startTime={start_str}&endTime={end_str}'
        response = await ghl_service._make_request('GET', endpoint)
        
        if 'error' not in response:
            events = response.get('events', [])
            print(f'   ✅ Today ({today.strftime("%A, %B %d")}): {len(events)} events')
        else:
            print(f'   ❌ Today\'s events failed: {response["error"]}')
            
    except Exception as e:
        print(f'❌ Today test failed: {e}')
    
    # Test 4: Test real vs mock conversations
    print('\n4. Testing conversations (real vs mock)...')
    try:
        conversations = await ghl_service.get_conversations(3)
        print(f'✅ Retrieved {len(conversations)} conversations')
        
        if conversations:
            print('   📱 Conversation details:')
            for i, conv in enumerate(conversations, 1):
                print(f'   {i}. {conv.contact_name} ({conv.type})')
                print(f'      Last: {conv.last_message[:80]}...')
                print(f'      Time: {conv.last_message_time}')
                print(f'      Unread: {conv.unread_count}')
        else:
            print('   📭 No real conversations found')
            
        # Check if these are mock conversations
        mock_names = ['Jennifer Martinez', 'David Kim', 'Lisa Thompson']
        has_mock = any(conv.contact_name in mock_names for conv in conversations)
        if has_mock:
            print('   ⚠️  WARNING: Mock data detected in conversations!')
        else:
            print('   ✅ Conversations appear to be real data')
            
    except Exception as e:
        print(f'❌ Conversations test failed: {e}')


if __name__ == '__main__':
    asyncio.run(test_calendar_events())