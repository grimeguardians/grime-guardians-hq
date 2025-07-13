#!/usr/bin/env python3
"""
Test Ava's New Intelligent System
Comprehensive testing of OpenAI Assistant API integration with GoHighLevel
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_ava_intelligent_system():
    """Test the new Ava intelligent assistant system."""
    
    print("🧠 Testing Ava's New Intelligent Assistant System")
    print("=" * 60)
    
    try:
        from src.agents.ava_assistant import ava_assistant
        
        print("✅ Ava Assistant imported successfully")
        print()
        
        # Test 1: Initialize Assistant
        print("1. 🤖 INITIALIZING OPENAI ASSISTANT")
        print("-" * 40)
        
        await ava_assistant._initialize_assistant()
        
        if ava_assistant.assistant_id:
            print(f"✅ Assistant initialized: {ava_assistant.assistant_id}")
        else:
            print("❌ Failed to initialize assistant")
            return
        
        # Test 2: Create conversation thread
        print(f"\n2. 💬 CREATING CONVERSATION THREAD")
        print("-" * 40)
        
        thread_id = await ava_assistant.create_conversation_thread()
        print(f"✅ Thread created: {thread_id}")
        
        # Test 3: Test schedule questions
        print(f"\n3. 📅 TESTING SCHEDULE QUESTIONS")
        print("-" * 40)
        
        test_questions = [
            "Who do we have scheduled to clean tomorrow?",
            "What's scheduled for Tuesday, July 15, 2025?", 
            "What day is Mark Trudeau's cleaning?",
            "How many cleanings are scheduled for next week?",
            "What's Mark's address?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n   🧪 Test {i}: {question}")
            
            try:
                response = await ava_assistant.send_message(question, "test_user")
                print(f"   📋 Response preview: {response[:200]}{'...' if len(response) > 200 else ''}")
                
                # Check for quality indicators
                has_real_data = any(name in response for name in ["Mark", "Destiny", "Madhavi"])
                has_specific_info = any(word in response.lower() for word in ["address", "phone", "email", "tuesday", "monday"])
                has_dynamic_search = "found" in response.lower() or "search" in response.lower()
                
                print(f"   📊 Quality check:")
                print(f"      • Contains real data: {'✅' if has_real_data else '❌'}")
                print(f"      • Has specific info: {'✅' if has_specific_info else '❌'}")
                print(f"      • Shows dynamic search: {'✅' if has_dynamic_search else '❌'}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test 4: Test function calling directly
        print(f"\n4. 🔧 TESTING FUNCTION CALLS DIRECTLY")
        print("-" * 40)
        
        # Test appointment search
        print(f"\n   🔍 Testing appointment search...")
        result = await ava_assistant._search_appointments(
            start_date="2025-07-15",
            end_date="2025-07-15"
        )
        
        if result.get("success"):
            appointments = result.get("appointments", [])
            print(f"   ✅ Found {len(appointments)} appointments for July 15th")
            
            for apt in appointments:
                print(f"      • {apt['contact_name']} - {apt['title']}")
                print(f"        📍 {apt['address'] or 'No address'}")
                print(f"        📞 {apt['contact_phone'] or 'No phone'}")
        else:
            print(f"   ❌ Search failed: {result.get('error')}")
        
        # Test contact details
        print(f"\n   👤 Testing contact details lookup...")
        result = await ava_assistant._get_contact_details("Mark")
        
        if result.get("success"):
            contact = result.get("contact", {})
            print(f"   ✅ Found contact: {contact.get('name')}")
            print(f"      📧 Email: {contact.get('email', 'N/A')}")
            print(f"      📞 Phone: {contact.get('phone', 'N/A')}")
            print(f"      📍 Address: {contact.get('address', 'N/A')}")
        else:
            print(f"   ❌ Contact lookup failed: {result.get('error')}")
        
        # Test appointment finding by contact
        print(f"\n   🎯 Testing find appointment by contact...")
        result = await ava_assistant._find_appointment_by_contact("Mark")
        
        if result.get("success"):
            appointments = result.get("appointments", [])
            print(f"   ✅ Found {len(appointments)} appointments for Mark")
            
            for apt in appointments:
                print(f"      • {apt['date']} at {apt['time']}")
                print(f"        📍 {apt['address'] or 'No address'}")
        else:
            print(f"   ❌ Find by contact failed: {result.get('error')}")
        
        # Test 5: Test learning capability
        print(f"\n5. 🧠 TESTING LEARNING CAPABILITY")
        print("-" * 40)
        
        learning_result = await ava_assistant._update_knowledge(
            correction_type="user_preference",
            new_understanding="Brandon prefers detailed address information in all responses",
            context="User requested more comprehensive location details"
        )
        
        if learning_result.get("success"):
            print(f"   ✅ Learning recorded: {learning_result['learned']}")
        else:
            print(f"   ❌ Learning failed: {learning_result.get('error')}")
        
        # Test 6: Test comprehensive conversation
        print(f"\n6. 💭 TESTING COMPREHENSIVE CONVERSATION")
        print("-" * 40)
        
        complex_question = "I need to know Mark Trudeau's appointment details including his address and contact information"
        
        print(f"   🧪 Complex question: {complex_question}")
        
        response = await ava_assistant.send_message(complex_question, "test_user")
        
        print(f"\n   📋 Full Response:")
        print(f"   {'-' * 60}")
        print(f"   {response}")
        print(f"   {'-' * 60}")
        
        # Analyze response quality
        response_lower = response.lower()
        quality_checks = {
            "mentions_mark": "mark" in response_lower,
            "has_address": any(word in response_lower for word in ["address", "street", "ave", "road", "blvd"]),
            "has_phone": any(word in response_lower for word in ["phone", "contact", "call"]),
            "has_appointment_time": any(word in response_lower for word in ["tuesday", "monday", "wednesday", "am", "pm"]),
            "uses_function_calling": "found" in response_lower or "search" in response_lower or "retrieved" in response_lower
        }
        
        print(f"\n   📊 Response Quality Analysis:")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"      • {check.replace('_', ' ').title()}: {status}")
        
        quality_score = sum(quality_checks.values()) / len(quality_checks) * 100
        print(f"\n   🎯 Overall Quality Score: {quality_score:.1f}%")
        
        if quality_score >= 80:
            print(f"   🎉 EXCELLENT! Ava is working intelligently!")
        elif quality_score >= 60:
            print(f"   ✅ GOOD! Minor improvements needed")
        else:
            print(f"   ⚠️ NEEDS WORK! Major issues detected")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 60)
    print("🧠 AVA INTELLIGENT SYSTEM TEST COMPLETE")
    print("=" * 60)
    print("💡 Expected capabilities:")
    print("   ✅ Natural conversation with GPT-4")
    print("   🔍 Dynamic appointment and contact search")
    print("   📋 Complete data retrieval (addresses, phones, etc.)")
    print("   🧠 Learning from corrections")
    print("   💬 Persistent conversation memory")
    print("   🎯 Intelligent reasoning about schedule and contacts")


if __name__ == '__main__':
    asyncio.run(test_ava_intelligent_system())