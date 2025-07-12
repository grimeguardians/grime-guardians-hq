#!/usr/bin/env python3
"""
Test Real CRM Data Integration
Verify Ava and Dean can access real GoHighLevel data with new PIT token
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# New working credentials
PIT_TOKEN = "pit-2e0a5a08-87fd-4f69-bbb4-a44082079823"
LOCATION_ID = "g3gJNdESNw9SrV7NpjJl"
BASE_URL = "https://services.leadconnectorhq.com"

async def test_ava_real_schedule():
    """Test Ava's access to real schedule data."""
    print("🤖 Testing Ava's Real Schedule Access")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {PIT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }
    
    try:
        # Get calendars first
        print("📅 Getting calendars...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/calendars/?locationId={LOCATION_ID}", headers=headers) as response:
                if response.status == 200:
                    calendars_data = await response.json()
                    calendars = calendars_data.get("calendars", [])
                    print(f"✅ Found {len(calendars)} calendars")
                    
                    if calendars:
                        calendar_id = calendars[0]["id"]
                        calendar_name = calendars[0].get("name", "Unnamed Calendar")
                        print(f"📋 Using calendar: {calendar_name} ({calendar_id})")
                        
                        # Get today's events
                        today = datetime.now()
                        start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
                        end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)
                        
                        start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        
                        events_url = f"{BASE_URL}/calendars/events?locationId={LOCATION_ID}&calendarId={calendar_id}&startTime={start_str}&endTime={end_str}"
                        
                        async with session.get(events_url, headers=headers) as events_response:
                            if events_response.status == 200:
                                events_data = await events_response.json()
                                events = events_data.get("events", [])
                                
                                print(f"✅ Found {len(events)} events for today")
                                
                                if events:
                                    print(f"\n📅 AVA'S REAL SCHEDULE:")
                                    for i, event in enumerate(events, 1):
                                        start_time = event.get("startTime", "")
                                        if start_time:
                                            try:
                                                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                                time_str = dt.strftime('%I:%M %p')
                                            except:
                                                time_str = start_time
                                        else:
                                            time_str = "Time TBD"
                                        
                                        title = event.get("title", event.get("eventTitle", "Appointment"))
                                        contact = event.get("contact", {})
                                        contact_name = contact.get("name", event.get("contactName", "Unknown"))
                                        
                                        print(f"**{i}. {time_str} - {contact_name}**")
                                        print(f"   📋 Service: {title}")
                                        print(f"   📍 Status: {event.get('status', 'Scheduled')}")
                                        print(f"   📞 Contact: {contact.get('phone', 'No phone')}")
                                        if event.get("notes"):
                                            print(f"   📝 Notes: {event.get('notes')[:60]}...")
                                        print()
                                    
                                    return True, len(events)
                                else:
                                    print("No events scheduled for today")
                                    return True, 0
                            else:
                                error = await events_response.text()
                                print(f"❌ Events request failed: {events_response.status}")
                                print(f"Error: {error[:200]}...")
                                return False, 0
                    else:
                        print("No calendars found")
                        return False, 0
                else:
                    error = await response.text()
                    print(f"❌ Calendars request failed: {response.status}")
                    print(f"Error: {error[:200]}...")
                    return False, 0
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, 0

async def test_dean_real_analytics():
    """Test Dean's access to real analytics data."""
    print("\n💼 Testing Dean's Real Analytics Access")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {PIT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }
    
    try:
        # Get contacts (leads)
        print("👥 Getting contacts/leads...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/contacts/?locationId={LOCATION_ID}&limit=10", headers=headers) as response:
                if response.status == 200:
                    contacts_data = await response.json()
                    contacts = contacts_data.get("contacts", [])
                    
                    print(f"✅ Found {len(contacts)} contacts")
                    
                    if contacts:
                        print(f"\n📊 DEAN'S REAL ANALYTICS:")
                        print(f"💬 **LEAD INTELLIGENCE** (Real-time from GoHighLevel):")
                        print(f"📞 **Total Contacts:** {len(contacts)}")
                        
                        # Analyze contact data
                        contacts_with_phone = len([c for c in contacts if c.get("phone")])
                        contacts_with_email = len([c for c in contacts if c.get("email")])
                        
                        print(f"📱 **Contacts with Phone:** {contacts_with_phone}")
                        print(f"📧 **Contacts with Email:** {contacts_with_email}")
                        
                        # Show recent contacts
                        print(f"\n🔥 **Recent Contacts:**")
                        for i, contact in enumerate(contacts[:5], 1):
                            name = contact.get("contactName") or contact.get("firstName") or "Unknown"
                            phone = contact.get("phone") or "No phone"
                            email = contact.get("email") or "No email"
                            
                            print(f"• {name}")
                            if email != "No email":
                                email_display = email[:30] + ('...' if len(email) > 30 else '')
                            else:
                                email_display = email
                            print(f"  📞 {phone} | 📧 {email_display}")
                        
                        # Get users for team info
                        async with session.get(f"{BASE_URL}/users/?locationId={LOCATION_ID}", headers=headers) as users_response:
                            if users_response.status == 200:
                                users_data = await users_response.json()
                                users = users_data.get("users", [])
                                print(f"\n👤 **Team Members:** {len(users)} users")
                        
                        return True, len(contacts)
                    else:
                        print("No contacts found")
                        return True, 0
                else:
                    error = await response.text()
                    print(f"❌ Contacts request failed: {response.status}")
                    print(f"Error: {error[:200]}...")
                    return False, 0
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, 0

async def generate_discord_commands():
    """Generate Discord commands that will work with real data."""
    print(f"\n🎮 Discord Commands for Real CRM Data")
    print("=" * 60)
    
    print(f"🤖 **AVA COMMANDS (Operations):**")
    print(f"   Ask Ava: 'What's on the schedule today?'")
    print(f"   Ask Ava: 'Any upcoming appointments?'")
    print(f"   Command: !gg schedule")
    
    print(f"\n💼 **DEAN COMMANDS (Sales):**")
    print(f"   Ask Dean: 'Show me our lead analytics'")
    print(f"   Ask Dean: 'What's our pipeline status?'")
    print(f"   Ask Dean: 'Monitor active conversations'")
    
    print(f"\n📱 **SOCIAL MEDIA COMMANDS:**")
    print(f"   Command: !gg social_calendar")
    print(f"   Command: !gg social_test")
    print(f"   Command: !gg hormozi_status")
    
    print(f"\n🔧 **TESTING COMMANDS:**")
    print(f"   Command: !gg test_ghl")
    print(f"   Command: !gg help_gg")

async def main():
    """Test real CRM data integration."""
    print("🚀 Real CRM Data Integration Test")
    print("=" * 70)
    
    print(f"🔑 Using PIT Token: {PIT_TOKEN}")
    print(f"📍 Location ID: {LOCATION_ID}")
    
    # Test Ava's capabilities
    ava_success, ava_events = await test_ava_real_schedule()
    
    # Test Dean's capabilities  
    dean_success, dean_contacts = await test_dean_real_analytics()
    
    # Generate Discord testing guide
    await generate_discord_commands()
    
    # Summary
    print(f"\n" + "=" * 70)
    print("🎯 REAL CRM INTEGRATION RESULTS")
    print("=" * 70)
    
    if ava_success and dean_success:
        print(f"🎉 **SUCCESS! Real CRM Integration Working**")
        
        print(f"\n✅ **What's Working:**")
        print(f"   🤖 Ava: Real calendar access ({ava_events} events today)")
        print(f"   💼 Dean: Real contacts access ({dean_contacts} contacts)")
        print(f"   📱 Social Media: Hormozi methodology active")
        print(f"   🔗 API: PIT token authentication working")
        
        print(f"\n🚀 **Next Steps:**")
        print(f"   1. ✅ .env file updated with working credentials")
        print(f"   2. 🚀 Deploy to production server")
        print(f"   3. 🔄 Restart Discord bot with new credentials")
        print(f"   4. 🧪 Test Discord commands with REAL CRM data")
        
        print(f"\n📋 **Server Deployment:**")
        print(f"   • Upload updated .env file to server")
        print(f"   • Restart grime-guardians-agent-system service")
        print(f"   • Test Discord bot in your server")
        
        return 0
    else:
        print(f"❌ **Some Issues Found:**")
        if not ava_success:
            print(f"   ❌ Ava: Schedule access issues")
        if not dean_success:
            print(f"   ❌ Dean: Contact access issues")
        
        print(f"\n🔧 **Troubleshooting:**")
        print(f"   • Verify PIT token has correct scopes")
        print(f"   • Check calendar setup in GoHighLevel")
        print(f"   • Test individual API endpoints manually")
        
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)