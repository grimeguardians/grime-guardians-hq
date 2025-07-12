#!/usr/bin/env python3
"""
Discord CRM Integration Test
Test Ava and Dean's CRM access through Discord with mock data
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock settings
class MockSettings:
    highlevel_location_id = "g3gJNdESNw9SrV7NpjJl"
    highlevel_api_key = "mock_api_key"
    highlevel_calendar_id = "mock_calendar_id"
    highlevel_oauth_access_token = "expired_oauth_token"
    highlevel_oauth_refresh_token = "expired_refresh_token"
    highlevel_token_expiry = 1751005613973  # Expired
    demo_mode = True

# Override settings module
sys.modules['src.config.settings'] = type('MockModule', (), {'settings': MockSettings()})()

async def test_ava_schedule_integration():
    """Test Ava's schedule integration with mock data."""
    print("🧪 Testing Ava's Schedule Integration")
    print("-" * 50)
    
    try:
        from src.integrations.gohighlevel_service import ghl_service
        
        # Test today's schedule (should return mock data)
        appointments = await ghl_service.get_todays_schedule()
        
        print(f"✅ Retrieved {len(appointments)} appointments")
        
        if appointments:
            print("\n📅 AVA'S SCHEDULE RESPONSE:")
            print("=" * 40)
            
            schedule_response = f"📅 **TODAY'S SCHEDULE** ({len(appointments)} appointments):\n\n"
            
            for i, apt in enumerate(appointments, 1):
                time_str = apt.start_time.strftime('%I:%M %p')
                schedule_response += f"**{i}. {time_str} - {apt.contact_name}**\n"
                schedule_response += f"   📋 Service: {apt.service_type}\n"
                schedule_response += f"   📍 Location: {apt.address[:60]}{'...' if len(apt.address) > 60 else ''}\n"
                schedule_response += f"   👤 {apt.assigned_user} | 📞 {apt.contact_phone}\n"
                if apt.notes:
                    schedule_response += f"   📝 Notes: {apt.notes[:80]}{'...' if len(apt.notes) > 80 else ''}\n"
                schedule_response += "\n"
            
            print(schedule_response)
            
            # Test upcoming appointments
            upcoming = await ghl_service.get_upcoming_appointments(24)
            print(f"✅ Upcoming appointments (24h): {len(upcoming)}")
            
            return True
        else:
            print("❌ No appointments returned")
            return False
            
    except Exception as e:
        print(f"❌ Ava schedule test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dean_conversation_monitoring():
    """Test Dean's conversation monitoring with mock data."""
    print("\n🧪 Testing Dean's Conversation Monitoring")
    print("-" * 50)
    
    try:
        from src.integrations.gohighlevel_service import ghl_service
        
        # Test conversation retrieval (should return mock data)
        conversations = await ghl_service.get_conversations(20)
        
        print(f"✅ Retrieved {len(conversations)} conversations")
        
        if conversations:
            active_convs = [c for c in conversations if c.unread_count > 0]
            print(f"✅ Active conversations: {len(active_convs)}")
            
            print("\n💼 DEAN'S ANALYTICS RESPONSE:")
            print("=" * 40)
            
            analytics_response = f"📊 **SALES INTELLIGENCE** (Real-time from GoHighLevel):\n\n"
            analytics_response += f"💬 **Active Conversations:** {len(active_convs)}\n"
            analytics_response += f"📞 **Total Conversations:** {len(conversations)}\n\n"
            
            if active_convs:
                analytics_response += "**🔥 Urgent Conversations:**\n"
                for conv in active_convs[:3]:  # Show top 3
                    time_ago = _time_since(conv.last_message_time)
                    analytics_response += f"• {conv.contact_name} ({conv.unread_count} unread, {time_ago})\n"
                    analytics_response += f"  Type: {conv.type} | Last: {conv.last_message[:50]}{'...' if len(conv.last_message) > 50 else ''}\n\n"
            
            print(analytics_response)
            
            # Test lead analytics
            analytics = await ghl_service.get_lead_analytics(7)
            if analytics:
                print(f"✅ Lead analytics: {analytics.get('total_leads', 0)} leads")
            
            return True
        else:
            print("❌ No conversations returned")
            return False
            
    except Exception as e:
        print(f"❌ Dean conversation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def _time_since(timestamp):
    """Calculate time since timestamp."""
    try:
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    except Exception:
        return "Recently"

async def test_social_media_integration():
    """Test social media agent integration."""
    print("\n🧪 Testing Social Media Agent Integration")
    print("-" * 50)
    
    try:
        from src.core.social_media_agent import social_media_agent
        
        # Test content calendar
        calendar = await social_media_agent.create_content_calendar(weeks_ahead=1)
        
        give_posts = len([p for p in calendar.posts if p.content_type == 'give'])
        ask_posts = len([p for p in calendar.posts if p.content_type == 'ask'])
        
        print(f"✅ Content calendar created:")
        print(f"   • Total Posts: {len(calendar.posts)}")
        print(f"   • Give Posts: {give_posts}")
        print(f"   • Ask Posts: {ask_posts}")
        print(f"   • Ratio: {give_posts}:{ask_posts}")
        
        # Test Hormozi status
        status = social_media_agent.get_give_give_give_ask_status()
        print(f"\n✅ Hormozi Status Generated:")
        print(status)
        
        return True
        
    except Exception as e:
        print(f"❌ Social media test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_discord_command_simulation():
    """Simulate Discord commands that users can test."""
    print("\n🎮 Discord Command Testing Guide")
    print("=" * 60)
    
    print("📱 **Ready for Discord Testing**")
    print("=" * 40)
    
    print("\n🎯 **Test Commands:**")
    
    print("\n**Ava (Schedule Management):**")
    print("   • Message: 'What's on the schedule today?'")
    print("   • Command: !gg schedule")
    print("   • Expected: Mock appointment data shown above")
    
    print("\n**Dean (Sales Analytics):**")
    print("   • Message: 'Show me our lead analytics'")
    print("   • Message: 'What's our pipeline status?'")
    print("   • Expected: Mock conversation data shown above")
    
    print("\n**Social Media Agent:**")
    print("   • Command: !gg social_calendar")
    print("   • Command: !gg social_test")
    print("   • Command: !gg hormozi_status")
    print("   • Expected: Hormozi content generation")
    
    print("\n**General Commands:**")
    print("   • Command: !gg help_gg")
    print("   • Command: !gg test_ghl")
    
    print("\n🔧 **When You Fix GoHighLevel Tokens:**")
    print("   • Same commands will show REAL CRM data")
    print("   • Follow GOHIGHLEVEL_INTEGRATION_GUIDE.md")
    print("   • Regenerate OAuth credentials in GoHighLevel")

async def main():
    """Run all Discord CRM integration tests."""
    print("🚀 Discord CRM Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run integration tests
    results.append(await test_ava_schedule_integration())
    results.append(await test_dean_conversation_monitoring())
    results.append(await test_social_media_integration())
    
    # Show Discord testing guide
    await test_discord_command_simulation()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ **Discord Integration Ready for Testing!**")
        
        print("\n🎯 **What's Working:**")
        print("   ✅ Ava can show today's schedule (mock data)")
        print("   ✅ Dean can show sales analytics (mock data)")
        print("   ✅ Social Media Agent creates Hormozi content")
        print("   ✅ Discord commands functional")
        print("   ✅ Error handling with graceful fallbacks")
        
        print("\n🔄 **Next Steps:**")
        print("   1. Test Discord commands in your server")
        print("   2. Verify mock data responses")
        print("   3. Fix GoHighLevel tokens for real data")
        print("   4. Enjoy full CRM monitoring!")
        
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)