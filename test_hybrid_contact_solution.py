#!/usr/bin/env python3
"""
Test the new hybrid contact resolution system
Tests both API contact lookup and name extraction from appointment titles
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append('src')

# Load environment variables
load_dotenv()

async def test_hybrid_contact_solution():
    """Test the enhanced GoHighLevel service with hybrid contact resolution."""
    
    print("🧪 Testing Hybrid Contact Resolution System")
    print("=" * 55)
    
    try:
        # Import the enhanced service
        from integrations.gohighlevel_service import ghl_service
        
        print("✅ Service imported successfully")
        print(f"📍 Location ID: {ghl_service.location_id}")
        print(f"🔑 PIT Token: {'✅ Available' if ghl_service.pit_token else '❌ Missing'}")
        print()
        
        # Test 1: Today's appointments with hybrid contact resolution
        print("1. 📅 TESTING TODAY'S APPOINTMENTS (Hybrid Contact Resolution)")
        print("-" * 60)
        
        appointments = await ghl_service.get_todays_schedule()
        
        if appointments:
            print(f"✅ Found {len(appointments)} appointments")
            
            for i, apt in enumerate(appointments, 1):
                print(f"\n📅 Appointment {i}:")
                print(f"   📋 Title: {apt.title}")
                print(f"   🕐 Time: {apt.start_time.strftime('%H:%M')}")
                print(f"   👤 Contact: {apt.contact_name}")
                print(f"   📧 Email: {apt.contact_email or 'N/A'}")
                print(f"   📞 Phone: {apt.contact_phone or 'N/A'}")
                print(f"   🆔 Contact ID: {apt.contact_id or 'N/A'}")
                
                # Check metadata
                if hasattr(apt, '_contact_source'):
                    source_icon = "🔗" if apt._contact_source == "api" else "📝"
                    print(f"   {source_icon} Source: {apt._contact_source}")
                
                # Success indicator
                if apt.contact_name and apt.contact_name != "Unknown":
                    if 'destiny' in apt.contact_name.lower():
                        print(f"   🎯 DESTINY FOUND WITH FULL INFO!")
                    else:
                        print(f"   ✅ Contact resolved successfully!")
                else:
                    print(f"   ⚠️ Contact name still unknown")
        else:
            print("❌ No appointments found for today")
        
        # Test 2: July 14th appointments (Destiny's day)
        print(f"\n2. 🎯 TESTING JULY 14TH (DESTINY'S DAY)")
        print("-" * 40)
        
        july_14 = datetime(2025, 7, 14, 0, 0, 0)
        july_15 = datetime(2025, 7, 15, 0, 0, 0)
        july_appointments = await ghl_service.get_appointments(july_14, july_15)
        
        if july_appointments:
            print(f"📅 July 14th: {len(july_appointments)} appointments")
            
            destiny_found = False
            for apt in july_appointments:
                print(f"\n   📋 {apt.title}")
                print(f"   👤 Contact: {apt.contact_name}")
                print(f"   📧 Email: {apt.contact_email or 'N/A'}")
                print(f"   📞 Phone: {apt.contact_phone or 'N/A'}")
                
                if hasattr(apt, '_contact_source'):
                    source_icon = "🔗" if apt._contact_source == "api" else "📝"
                    print(f"   {source_icon} Source: {apt._contact_source}")
                
                if 'destiny' in apt.contact_name.lower() or 'destiny' in apt.title.lower():
                    print(f"   🎯 DESTINY FOUND!")
                    print(f"   🎉 No more 'Unknown contact' issue!")
                    destiny_found = True
            
            if not destiny_found:
                print(f"   ⚠️ Destiny not found on July 14th")
        else:
            print("❌ No appointments found on July 14th")
        
        # Test 3: Name extraction function directly
        print(f"\n3. 🧪 TESTING NAME EXTRACTION PATTERNS")
        print("-" * 40)
        
        test_titles = [
            "Destiny - Recurring Cleaning",
            "Cleaning for Sarah Johnson",
            "Mike Peterson (Property Manager)",
            "Smith Residence Cleaning",
            "Johnson, Mike - Deep Clean",
            "Regular Maintenance Service",
            "Martinez House - Move Out",
            "Commercial Walkthrough - ABC Corp"
        ]
        
        for title in test_titles:
            extracted_name = ghl_service._extract_name_from_title(title)
            print(f"   📝 '{title}' → '{extracted_name}'")
        
        # Test 4: API contact lookup test
        print(f"\n4. 🔗 TESTING API CONTACT LOOKUP")
        print("-" * 35)
        
        # Test with known contact IDs from appointments
        if appointments:
            for apt in appointments[:2]:  # Test first 2
                if apt.contact_id:
                    print(f"\n   🧪 Testing contact ID: {apt.contact_id}")
                    contact_details = await ghl_service._get_contact_details(apt.contact_id)
                    
                    if contact_details:
                        name = contact_details.get('name', 'Unknown')
                        email = contact_details.get('email', 'N/A')
                        phone = contact_details.get('phone', 'N/A')
                        print(f"   ✅ API Success: {name} - {email} - {phone}")
                    else:
                        print(f"   ❌ API contact lookup failed")
                else:
                    print(f"   ⚠️ No contact ID available for '{apt.title}'")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 55)
    print("🧪 HYBRID CONTACT RESOLUTION TEST COMPLETE")
    print("=" * 55)
    print("💡 Expected results:")
    print("   ✅ Contact names should show real names instead of 'Unknown'")
    print("   🔗 API contacts should have email/phone data")
    print("   📝 Extracted contacts should have names from titles")
    print("   🎯 Destiny should be found with contact information")


if __name__ == '__main__':
    asyncio.run(test_hybrid_contact_solution())