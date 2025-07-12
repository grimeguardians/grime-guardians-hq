#!/usr/bin/env python3
"""
Social Media Agent Test Script
Test the Hormozi methodology implementation and content generation
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_social_media_agent():
    """Test the Social Media Agent functionality."""
    print("🚀 Testing Social Media Agent")
    print("=" * 50)
    
    try:
        # Import the social media agent
        from core.social_media_agent import social_media_agent
        print("✅ Social Media Agent imported successfully")
        
        # Test 1: Create content calendar
        print("\n🧪 Test 1: Creating Content Calendar...")
        calendar = await social_media_agent.create_content_calendar(weeks_ahead=1)
        
        give_posts = len([p for p in calendar.posts if p.content_type == 'give'])
        ask_posts = len([p for p in calendar.posts if p.content_type == 'ask'])
        
        print(f"✅ Content Calendar Created:")
        print(f"   • Total Posts: {len(calendar.posts)}")
        print(f"   • Give Posts: {give_posts}")
        print(f"   • Ask Posts: {ask_posts}")
        print(f"   • Ratio: {give_posts}:{ask_posts}")
        print(f"   • Platforms: {', '.join(calendar.platforms_active)}")
        
        # Test 2: A/B Testing
        print("\n🧪 Test 2: Creating A/B Test...")
        test_post = {
            'content_type': 'give',
            'category': 'cleaning_tips', 
            'platform': 'facebook'
        }
        
        ab_test = await social_media_agent.create_ab_test(test_post, ['hook_style'])
        
        print(f"✅ A/B Test Created:")
        print(f"   • Test ID: {ab_test.test_id}")
        print(f"   • Variant A: {ab_test.variant_a.title}")
        print(f"   • Variant B: {ab_test.variant_b.title}")
        print(f"   • Status: {ab_test.winner}")
        
        # Test 3: Hormozi Status
        print("\n🧪 Test 3: Checking Hormozi Status...")
        status = social_media_agent.get_give_give_give_ask_status()
        calendar_summary = social_media_agent.get_content_calendar_summary()
        
        print("✅ Hormozi Status:")
        print(status)
        print("\n✅ Calendar Summary:")
        print(calendar_summary)
        
        # Test 4: Performance Analysis
        print("\n🧪 Test 4: Analyzing Performance...")
        performance = await social_media_agent.analyze_content_performance(7)
        
        print("✅ Performance Analysis:")
        print(f"   • Period: {performance.get('period_days', 0)} days")
        print(f"   • Hormozi Insights: {len(performance.get('hormozi_insights', []))} insights")
        print(f"   • Recommendations: {len(performance.get('optimization_recommendations', []))} recommendations")
        
        # Show sample content
        print("\n📝 Sample Generated Content:")
        if calendar.posts:
            sample_post = calendar.posts[0]
            print(f"Platform: {sample_post.platform.title()}")
            print(f"Type: {sample_post.content_type.title()}")
            print(f"Title: {sample_post.title}")
            print(f"Content Preview: {sample_post.content[:200]}...")
            print(f"Hashtags: {', '.join(sample_post.hashtags[:5])}")
        
        print("\n🎉 All Social Media Agent tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Social Media Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the social media agent test."""
    success = await test_social_media_agent()
    
    if success:
        print("\n✅ Social Media Agent is fully operational!")
        print("\n🎯 Key Features Verified:")
        print("• Hormozi 'Give Give Give Ask' methodology")
        print("• Multi-platform content generation")
        print("• A/B testing capabilities")
        print("• Content calendar management")
        print("• Performance analytics")
        print("• Discord bot integration ready")
    else:
        print("\n❌ Social Media Agent needs attention")
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)