#!/usr/bin/env python3
"""
Test the name extraction logic without importing full modules
Simple isolated test of the intelligent name extraction patterns
"""

import re

def extract_name_from_title(title: str) -> str:
    """Extract contact name from appointment title using smart patterns."""
    try:
        if not title or title.lower() in ['appointment', 'cleaning', 'service']:
            return "Unknown"
        
        # Common patterns in cleaning appointment titles:
        patterns = [
            # "Destiny - Recurring Cleaning" -> "Destiny"
            r'^([A-Za-z]+)\s*[-–—]\s*\w+',
            # "Cleaning for Sarah Johnson" -> "Sarah Johnson"
            r'(?:cleaning|service)\s+for\s+([A-Za-z\s]+?)(?:\s*[-–—]|$)',
            # "Johnson, Mike - Deep Clean" -> "Johnson, Mike"
            r'^([A-Za-z]+,\s*[A-Za-z]+)\s*[-–—]',
            # "Mike Peterson (Property Manager)" -> "Mike Peterson"
            r'^([A-Za-z\s]+?)\s*\(',
            # "Smith Residence Cleaning" -> "Smith"
            r'^([A-Za-z]+)\s+(?:residence|house|home|property)',
            # First word that looks like a name
            r'^([A-Z][a-z]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'[^A-Za-z\s,.]', '', name).strip()
                if len(name) > 1 and name.lower() not in ['cleaning', 'service', 'appointment', 'recurring']:
                    return name.title()
        
        # If no pattern matches, return the first word if it looks like a name
        first_word = title.split()[0] if title.split() else ""
        if first_word and first_word[0].isupper() and len(first_word) > 1:
            return first_word.title()
            
        return "Unknown"
        
    except Exception as e:
        print(f"Error extracting name from title '{title}': {e}")
        return "Unknown"

def test_name_extraction():
    """Test name extraction patterns with various appointment title formats."""
    
    print("🧪 Testing Name Extraction Patterns")
    print("=" * 40)
    
    test_cases = [
        # Expected successful extractions
        ("Destiny - Recurring Cleaning", "Destiny"),
        ("Cleaning for Sarah Johnson", "Sarah Johnson"),
        ("Mike Peterson (Property Manager)", "Mike Peterson"),
        ("Smith Residence Cleaning", "Smith"),
        ("Johnson, Mike - Deep Clean", "Johnson, Mike"),
        ("Martinez House - Move Out", "Martinez"),
        ("Diana - Weekly Service", "Diana"),
        ("Madhavi Apartment Cleaning", "Madhavi"),
        ("Larry - Deep Cleaning Service", "Larry"),
        ("Sandra Move-Out Clean", "Sandra"),
        ("Elizabeth - Maintenance", "Elizabeth"),
        
        # Edge cases
        ("Commercial Walkthrough - ABC Corp", "Commercial"),
        ("Regular Maintenance Service", "Regular"),
        ("Appointment", "Unknown"),
        ("Cleaning", "Unknown"),
        ("Service", "Unknown"),
        ("", "Unknown"),
        ("123 Main St Cleaning", "Unknown"),  # No proper name
        ("cleaning for john", "John"),  # Lowercase handling
        ("DESTINY - RECURRING", "Destiny"),  # Uppercase handling
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    print("📝 Testing extraction patterns:")
    print()
    
    for title, expected in test_cases:
        result = extract_name_from_title(title)
        success = result == expected
        status = "✅" if success else "❌"
        
        print(f"{status} '{title}' → '{result}' (expected: '{expected}')")
        
        if success:
            success_count += 1
        else:
            print(f"   ⚠️ Mismatch detected")
    
    print()
    print("=" * 40)
    print(f"📊 Results: {success_count}/{total_count} tests passed")
    print(f"📈 Success rate: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 All tests passed! Name extraction is working correctly.")
    else:
        print("⚠️ Some tests failed. Consider refining the patterns.")
    
    print()
    print("💡 Key capabilities demonstrated:")
    print("   • Extracts names from 'Name - Service' format")
    print("   • Handles 'Cleaning for Name' format")
    print("   • Recognizes 'Name (Title)' format")
    print("   • Processes 'Name Residence/House' format")
    print("   • Manages case sensitivity properly")
    print("   • Returns 'Unknown' for ambiguous cases")


if __name__ == '__main__':
    test_name_extraction()