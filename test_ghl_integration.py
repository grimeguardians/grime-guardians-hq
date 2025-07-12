#!/usr/bin/env python3
"""
GoHighLevel Integration Test Script
Comprehensive testing of GHL integration for both Ava and Dean suites
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_setup():
    """Test basic imports and setup."""
    print("🧪 Testing Basic Setup...")
    
    try:
        from config import settings
        print(f"✅ Settings loaded - Location ID: {settings.highlevel_location_id[:10]}...")
        
        from integrations.gohighlevel_service import ghl_service, GoHighLevelService
        print("✅ GoHighLevel service imported successfully")
        
        from core.ava_conversation import ava_conversation
        print("✅ Ava conversation engine loaded")
        
        from core.dean_conversation import dean_conversation
        print("✅ Dean conversation engine loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic setup failed: {e}")
        return False

async def test_ghl_connection():
    """Test GoHighLevel API connection."""
    print("\n🧪 Testing GoHighLevel Connection...")
    
    try:
        from integrations.gohighlevel_service import ghl_service
        
        # Test connection
        result = await ghl_service.test_connection()
        
        if result['status'] == 'success':
            print("✅ GoHighLevel API connection successful")
            print(f"✅ OAuth Working: {result.get('oauth_working', False)}")
            print(f"✅ Calendar Accessible: {result.get('calendar_accessible', False)}")
            print(f"✅ Conversations Accessible: {result.get('conversations_accessible', False)}")
            print(f"✅ Contacts Accessible: {result.get('contacts_accessible', False)}")
            return True
        else:
            print(f"❌ GoHighLevel connection failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

async def test_calendar_integration():
    """Test calendar integration for Ava."""
    print("\n🧪 Testing Calendar Integration (Ava)...")
    
    try:
        from integrations.gohighlevel_service import ghl_service
        
        # Test today's schedule
        appointments = await ghl_service.get_todays_schedule()
        print(f"✅ Retrieved {len(appointments)} appointments for today")
        
        if appointments:
            first_apt = appointments[0]
            print(f"   Sample: {first_apt.contact_name} at {first_apt.start_time.strftime('%I:%M %p')}")
        
        # Test upcoming appointments
        upcoming = await ghl_service.get_upcoming_appointments(24)
        print(f"✅ Retrieved {len(upcoming)} upcoming appointments (24h)")
        
        # Test Ava's schedule functions
        from core.ava_conversation import ava_conversation
        schedule_summary = await ava_conversation.get_todays_schedule()
        print(f"✅ Ava's schedule summary generated: {len(schedule_summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar integration error: {e}")
        return False

async def test_conversation_monitoring():
    """Test conversation monitoring for Dean."""
    print("\n🧪 Testing Conversation Monitoring (Dean)...")
    
    try:
        from integrations.gohighlevel_service import ghl_service
        
        # Test conversation retrieval
        conversations = await ghl_service.get_conversations(20)
        print(f"✅ Retrieved {len(conversations)} conversations")
        
        if conversations:
            active_count = len([c for c in conversations if c.unread_count > 0])
            print(f"   Active conversations: {active_count}")
        
        # Test Dean's conversation monitoring
        from core.dean_conversation import dean_conversation
        monitoring_report = await dean_conversation.monitor_conversations(10)
        print(f"✅ Dean's conversation monitoring: {len(monitoring_report)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation monitoring error: {e}")
        return False

async def test_lead_analytics():
    """Test lead analytics for Dean."""
    print("\n🧪 Testing Lead Analytics (Dean)...")
    
    try:
        from integrations.gohighlevel_service import ghl_service
        
        # Test analytics retrieval
        analytics = await ghl_service.get_lead_analytics(7)
        print(f"✅ Retrieved lead analytics: {len(analytics)} metrics")
        
        if analytics:
            print(f"   Total leads (7d): {analytics.get('total_leads', 0)}")
            print(f"   Active conversations: {analytics.get('active_conversations', 0)}")
            print(f"   Scheduled appointments: {analytics.get('scheduled_appointments', 0)}")
        
        # Test Dean's analytics functions
        from core.dean_conversation import dean_conversation
        analytics_report = await dean_conversation.get_lead_analytics(7)
        print(f"✅ Dean's analytics report generated: {len(analytics_report)} characters")
        
        pipeline_status = await dean_conversation.get_pipeline_status()
        print(f"✅ Dean's pipeline status: {len(pipeline_status)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Lead analytics error: {e}")
        return False

async def test_contact_management():
    """Test contact management functionality."""
    print("\n🧪 Testing Contact Management...")
    
    try:
        from integrations.gohighlevel_service import ghl_service
        
        # Test contact retrieval
        contacts = await ghl_service.get_contacts(10)
        print(f"✅ Retrieved {len(contacts)} contacts")
        
        if contacts:
            recent_count = len([c for c in contacts if (datetime.now() - c.created_at).days <= 7])
            print(f"   Recent contacts (7d): {recent_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Contact management error: {e}")
        return False

async def test_conversation_integration():
    """Test conversational AI integration with GHL data."""
    print("\n🧪 Testing Conversational AI Integration...")
    
    try:
        from core.conversation_engine import ConversationMessage, ConversationContext
        from datetime import datetime
        
        # Test Ava with schedule context
        print("Testing Ava's schedule integration...")
        ava_context = ConversationContext(
            user_id="test_user",
            conversation_id="test_ava_schedule",
            messages=[
                ConversationMessage(
                    role="user",
                    content="What's on the schedule today?",
                    timestamp=datetime.utcnow()
                )
            ],
            persona_type="Ava",
            last_activity=datetime.utcnow(),
            context_data={}
        )
        
        from core.ava_conversation import ava_conversation
        ava_context_text = ava_conversation.get_business_context(ava_context)
        print(f"✅ Ava context includes schedule: {'schedule' in ava_context_text.lower()}")
        
        # Test Dean with sales intelligence context
        print("Testing Dean's sales integration...")
        dean_context = ConversationContext(
            user_id="test_user",
            conversation_id="test_dean_analytics",
            messages=[
                ConversationMessage(
                    role="user",
                    content="Show me our lead analytics",
                    timestamp=datetime.utcnow()
                )
            ],
            persona_type="Dean",
            last_activity=datetime.utcnow(),
            context_data={}
        )
        
        from core.dean_conversation import dean_conversation
        dean_context_text = dean_conversation.get_business_context(dean_context)
        print(f"✅ Dean context includes intelligence: {'intelligence' in dean_context_text.lower()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation integration error: {e}")
        return False

def display_integration_summary():
    """Display integration capabilities summary."""
    print("\n" + "="*60)
    print("🎯 GOHIGHLEVEL INTEGRATION CAPABILITIES")
    print("="*60)
    
    print("\n📅 AVA (OPERATIONS) INTEGRATION:")
    print("  • Real-time calendar viewing")
    print("  • Today's schedule summary")
    print("  • Upcoming appointment alerts")
    print("  • Contractor assignment tracking")
    print("  • Appointment status monitoring")
    
    print("\n💼 DEAN (SALES) INTEGRATION:")
    print("  • Live conversation monitoring")
    print("  • Lead generation analytics")
    print("  • Sales pipeline tracking")
    print("  • Response time monitoring")
    print("  • Lead source analysis")
    print("  • Conversion rate tracking")
    
    print("\n🔧 SHARED CAPABILITIES:")
    print("  • Contact management")
    print("  • Real-time CRM data access")
    print("  • Automated reporting")
    print("  • API connection health monitoring")
    
    print("\n🧪 TESTING COMMANDS:")
    print("  Ava: 'What's on the schedule today?'")
    print("  Ava: 'Any upcoming appointments?'")
    print("  Dean: 'Show me our lead analytics'")
    print("  Dean: 'What's our pipeline status?'")
    print("  Dean: 'Monitor active conversations'")

async def main():
    """Run all integration tests."""
    print("🚀 GoHighLevel Integration Test Suite")
    print("="*50)
    
    results = []
    
    # Run all tests
    results.append(test_basic_setup())
    results.append(await test_ghl_connection())
    results.append(await test_calendar_integration())
    results.append(await test_conversation_monitoring())
    results.append(await test_lead_analytics())
    results.append(await test_contact_management())
    results.append(await test_conversation_integration())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*50)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ GoHighLevel integration is fully operational!")
        display_integration_summary()
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("\nSome integration components need attention.")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())