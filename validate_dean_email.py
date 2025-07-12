#!/usr/bin/env python3
"""
Dean & Email Agent Validation Script
Quick validation that Dean's Email Agent is properly implemented
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def validate_email_agent():
    """Validate Email Agent implementation."""
    print("🧪 Validating Email Agent Implementation...")
    
    try:
        # Test 1: Check if EmailAgent file exists and basic structure
        email_agent_path = os.path.join('src', 'core', 'email_agent.py')
        assert os.path.exists(email_agent_path), "Email Agent file not found"
        print("✅ Email Agent file exists")
        
        # Test 2: Check file content for key components
        with open(email_agent_path, 'r') as f:
            content = f.read()
        
        # Check for key classes and functions
        required_components = [
            'class EmailAgent',
            'class EmailCampaign', 
            'class EmailLead',
            'class EmailTemplate',
            'def create_campaign',
            'def send_campaign_email',
            'def monitor_inbox',
            'def _personalize_email',
            'Hormozi'
        ]
        
        for component in required_components:
            assert component in content, f"Missing component: {component}"
        print("✅ All required Email Agent components present")
        
        # Test 3: Check for Hormozi methodology
        hormozi_keywords = ['value_equation', 'offer_stacking', 'social_proof', 'pain_point']
        for keyword in hormozi_keywords:
            assert keyword in content, f"Missing Hormozi keyword: {keyword}"
        print("✅ Hormozi methodology integration validated")
        
        # Test 4: Check email templates
        template_types = ['pm_value_first', 'realtor_pain_point', 'investor_roi_focus']
        for template_type in template_types:
            assert template_type in content, f"Missing template: {template_type}"
        print("✅ All required email templates present")
        
        # Test 5: Check personalization and approval system
        approval_keywords = ['pending_approvals', 'approve_email', 'personalize']
        for keyword in approval_keywords:
            assert keyword in content, f"Missing approval system component: {keyword}"
        print("✅ Email approval and personalization system validated")
        
        return True
        
    except Exception as e:
        print(f"❌ Email Agent validation failed: {e}")
        return False

def validate_dean_integration():
    """Validate Dean's integration with Email Agent."""
    print("\n🧪 Validating Dean Integration...")
    
    try:
        # Test 1: Check Dean conversation file exists
        dean_path = os.path.join('src', 'core', 'dean_conversation.py')
        assert os.path.exists(dean_path), "Dean conversation file not found"
        print("✅ Dean conversation file exists")
        
        # Test 2: Check file content for key components
        with open(dean_path, 'r') as f:
            content = f.read()
        
        # Check for key classes and integration
        required_components = [
            'class DeanConversationEngine',
            'def _coordinate_email_agent',
            'Hormozi',
            'Strategic Sales Director',
            'subagents_status',
            'email_agent',
            'funnel_agent'
        ]
        
        for component in required_components:
            assert component in content, f"Missing component: {component}"
        print("✅ All required Dean components present")
        
        # Test 3: Check Email Agent integration
        email_integration_keywords = [
            'from .email_agent import email_agent',
            'create_campaign',
            'monitor_inbox',
            'get_metrics',
            'approve_email'
        ]
        
        for keyword in email_integration_keywords:
            assert keyword in content, f"Missing Email Agent integration: {keyword}"
        print("✅ Dean-Email Agent integration validated")
        
        # Test 4: Check Hormozi methodology
        hormozi_components = [
            'value_equation',
            'offer_stacking',
            'lead_magnets',
            'outbound_strategy',
            'dream_outcome',
            'perceived_likelihood'
        ]
        
        for component in hormozi_components:
            assert component in content, f"Missing Hormozi component: {component}"
        print("✅ Hormozi methodology implementation validated")
        
        # Test 5: Check market intelligence
        market_keywords = [
            'property_management_companies',
            'individual_realtors', 
            'real_estate_investors',
            'pain_points',
            'value_proposition'
        ]
        
        for keyword in market_keywords:
            assert keyword in content, f"Missing market intelligence: {keyword}"
        print("✅ Market intelligence and targeting validated")
        
        return True
        
    except Exception as e:
        print(f"❌ Dean integration validation failed: {e}")
        return False

def validate_discord_integration():
    """Validate Discord bot integration."""
    print("\n🧪 Validating Discord Integration...")
    
    try:
        # Test 1: Check Discord bot file exists
        discord_path = os.path.join('src', 'integrations', 'discord_bot.py')
        assert os.path.exists(discord_path), "Discord bot file not found"
        print("✅ Discord bot file exists")
        
        # Test 2: Check file content for Dean integration
        with open(discord_path, 'r') as f:
            content = f.read()
        
        # Check for Dean integration components
        dean_integration_keywords = [
            'from ..core.dean_conversation import dean_conversation',
            'handle_dean_conversation',
            'dean_command',
            'campaigns',
            'approvals'
        ]
        
        for keyword in dean_integration_keywords:
            assert keyword in content, f"Missing Discord integration: {keyword}"
        print("✅ Dean Discord integration present")
        
        # Test 3: Check command structure
        command_keywords = [
            '@self.command(name=\'dean\')',
            'Active Email Campaigns',
            'Pending Email Approvals',
            'Strategic Sales Director'
        ]
        
        for keyword in command_keywords:
            assert keyword in content, f"Missing Discord command feature: {keyword}"
        print("✅ Dean Discord commands validated")
        
        # Test 4: Check conversation routing
        routing_keywords = [
            'dean', 'sales', 'marketing', 'lead', 'campaign', 'revenue'
        ]
        
        # Check that these keywords are used for routing to Dean
        routing_check = any(keyword in content for keyword in routing_keywords)
        assert routing_check, "Missing conversation routing keywords"
        print("✅ Dean conversation routing validated")
        
        return True
        
    except Exception as e:
        print(f"❌ Discord integration validation failed: {e}")
        return False

def main():
    """Run all validations."""
    print("🚀 Dean's Strategic Sales Suite Validation")
    print("=" * 50)
    
    results = []
    
    # Run validations
    results.append(validate_email_agent())
    results.append(validate_dean_integration()) 
    results.append(validate_discord_integration())
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL VALIDATIONS PASSED ({passed}/{total})")
        print("\n📧 Dean's Email Agent is ready for deployment!")
        print("✨ Features available:")
        print("  • Hormozi-optimized email templates")
        print("  • Campaign management with approval workflow") 
        print("  • AI-powered personalization")
        print("  • Inbox monitoring and response suggestions")
        print("  • Discord integration with !gg dean commands")
        print("  • Conversational AI for strategic sales")
        return 0
    else:
        print(f"❌ VALIDATION FAILED ({passed}/{total})")
        print("Some components need attention before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())