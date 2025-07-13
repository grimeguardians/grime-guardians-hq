#!/usr/bin/env python3
"""
Test Ava's Discord response fix
Test to verify that Ava's Discord responses now show real appointment data
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append('src')
sys.path.insert(0, os.path.abspath('.'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ava_discord_fix():
    """Test Ava's fixed Discord response system."""
    
    print("🧪 Testing Ava's Discord Response Fix")
    print("=" * 45)
    
    try:
        # Import the fixed intelligence upgrade
        from ava_intelligence_upgrade import ava_intelligence
        
        print("✅ Ava intelligence upgrade imported successfully")
        print()
        
        # Test 1: Schedule question for today
        print("1. 🗓️ TESTING TODAY'S SCHEDULE QUESTION")
        print("-" * 40)
        
        test_message = "What's on the schedule for today?"
        response = await ava_intelligence.handle_schedule_question(test_message)
        
        print(f"📝 Message: '{test_message}'")
        print(f"📋 Response preview: {response[:200]}...")
        print()
        
        # Check if response contains real data indicators
        has_real_appointments = "appointments scheduled" in response.lower() or "cleaning appointments" in response.lower()
        has_contact_names = any(name in response for name in ["Madhavi", "Destiny", "Whitney", "Alex"])
        has_unknown_contacts = "Unknown Client" in response
        
        print(f"   📊 Analysis:")
        print(f"   • Contains appointments: {'✅' if has_real_appointments else '❌'}")
        print(f"   • Has real contact names: {'✅' if has_contact_names else '❌'}")
        print(f"   • Has 'Unknown Client': {'❌' if has_unknown_contacts else '✅'}")
        
        # Test 2: Monday the 14th question (Destiny's day)
        print(f"\n2. 🎯 TESTING MONDAY THE 14TH QUESTION")
        print("-" * 40)
        
        test_message_monday = "What's scheduled for Monday the 14th?"
        response_monday = await ava_intelligence.handle_schedule_question(test_message_monday)
        
        print(f"📝 Message: '{test_message_monday}'")
        print(f"📋 Response preview: {response_monday[:200]}...")
        print()
        
        # Check for Destiny specifically
        has_destiny = "Destiny" in response_monday
        has_july_14 = "July 14" in response_monday or "Monday, July 14" in response_monday
        
        print(f"   📊 Analysis:")
        print(f"   • Mentions Destiny: {'✅' if has_destiny else '❌'}")
        print(f"   • Recognizes July 14th: {'✅' if has_july_14 else '❌'}")
        
        # Test 3: Full response display
        print(f"\n3. 📄 FULL RESPONSE SAMPLE")
        print("-" * 30)
        print("Here's the full response for today:")
        print()
        print(response)
        
        # Test 4: Backend integration verification
        print(f"\n4. 🔗 BACKEND INTEGRATION VERIFICATION")
        print("-" * 40)
        
        # Test if we can get raw appointments from the backend
        from src.integrations.gohighlevel_service import ghl_service
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        backend_appointments = await ghl_service.get_appointments(today, today.replace(hour=23, minute=59))
        
        print(f"✅ Backend returned {len(backend_appointments)} appointments")
        
        if backend_appointments:
            for i, apt in enumerate(backend_appointments[:3], 1):
                print(f"   {i}. {apt.title} → {apt.contact_name}")
                print(f"      📧 {apt.contact_email or 'N/A'}")
                print(f"      📞 {apt.contact_phone or 'N/A'}")
                print(f"      🔗 Source: {getattr(apt, '_contact_source', 'unknown')}")
                print()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 45)
    print("🧪 AVA DISCORD FIX TEST COMPLETE")
    print("=" * 45)
    print("💡 Expected improvements:")
    print("   ✅ Ava should show real appointment data instead of 'No appointments'")
    print("   🎯 Destiny should be found on Monday the 14th")
    print("   📋 Contact names should be real instead of 'Unknown Client'")
    print("   🔗 Backend integration should be working properly")

if __name__ == '__main__':
    asyncio.run(test_ava_discord_fix())