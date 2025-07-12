"""
Social Media Agent - Content Planning & Automation
Handles all social media content creation, scheduling, A/B testing, and engagement
Implements Hormozi's "Give Give Give Ask" methodology for social media success
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import openai
import structlog

from ..config import settings

logger = structlog.get_logger()


@dataclass
class ContentPost:
    """Social media content post structure."""
    post_id: str
    platform: str  # 'facebook', 'instagram', 'linkedin', 'nextdoor', 'tiktok'
    content_type: str  # 'give', 'ask', 'story', 'tips', 'social_proof'
    title: str
    content: str
    hashtags: List[str]
    scheduled_time: datetime
    status: str  # 'draft', 'scheduled', 'posted', 'failed'
    engagement_metrics: Dict[str, int] = None
    hormozi_framework: str = ""
    target_audience: str = ""


@dataclass
class ContentCalendar:
    """Social media content calendar structure."""
    week_start: datetime
    posts: List[ContentPost]
    give_give_give_ask_ratio: Dict[str, int]  # Track the ratio
    platforms_active: List[str]
    content_themes: List[str]


@dataclass
class ABTestResult:
    """A/B test results for content optimization."""
    test_id: str
    variant_a: ContentPost
    variant_b: ContentPost
    winner: str  # 'a', 'b', or 'tie'
    metrics: Dict[str, float]
    confidence_level: float
    recommendation: str


class SocialMediaAgent:
    """
    Comprehensive social media management agent implementing Hormozi's methodology.
    
    Handles:
    - Content planning with Give Give Give Ask strategy
    - Multi-platform scheduling and posting
    - A/B testing for optimization
    - Engagement monitoring and response
    - Content calendar management
    - Performance analytics and insights
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Content templates and frameworks
        self.content_frameworks = self._load_content_frameworks()
        self.hormozi_templates = self._load_hormozi_templates()
        
        # Platform specifications
        self.platform_specs = self._load_platform_specifications()
        
        # Content calendar and tracking
        self.content_calendar: Optional[ContentCalendar] = None
        self.active_ab_tests: List[ABTestResult] = []
        self.content_performance: Dict[str, Dict] = {}
        
        # Give Give Give Ask tracking
        self.content_ratio_tracker = {
            'give_count': 0,
            'ask_count': 0,
            'current_cycle': 'give',
            'last_ask_date': None
        }
    
    def _load_content_frameworks(self) -> Dict[str, Any]:
        """Load Hormozi content frameworks and strategies."""
        return {
            'give_give_give_ask': {
                'description': 'Provide 3 pieces of value before making 1 ask',
                'give_types': [
                    'educational_tips',
                    'behind_scenes',
                    'client_success_stories',
                    'industry_insights',
                    'problem_solving_content',
                    'community_value'
                ],
                'ask_types': [
                    'service_promotion',
                    'contact_generation',
                    'review_request',
                    'referral_ask',
                    'booking_request'
                ]
            },
            'value_equation_social': {
                'dream_outcome': 'Stress-free property management',
                'perceived_likelihood': 'Social proof through before/after content',
                'time_delay': 'Quick response times showcased',
                'effort_sacrifice': 'We handle everything - show the ease'
            },
            'content_hooks': {
                'curiosity': [
                    'What most property managers don\'t know...',
                    'The #1 mistake I see realtors make...',
                    'Here\'s what happened when...',
                    'You won\'t believe what we found...'
                ],
                'authority': [
                    'After 500+ cleanings, here\'s what I\'ve learned...',
                    'Property managers ask me this daily...',
                    'BBB-accredited tip:',
                    'From our 70+ five-star reviews...'
                ],
                'urgency': [
                    'Tenant moving out this week?',
                    'Last-minute cleaning emergency?',
                    'Before your listing photos...',
                    'Don\'t let this cost you a deposit...'
                ]
            }
        }
    
    def _load_hormozi_templates(self) -> Dict[str, Dict[str, str]]:
        """Load Hormozi-optimized content templates for each platform."""
        return {
            'facebook': {
                'give_tip': """🏠 PROPERTY MANAGER TIP #{tip_number}

{hook}

{valuable_tip}

Why this matters: {explanation}

Seen this issue? Drop a comment below! 👇

#PropertyManagement #CleaningTips #TwinCities #GrimeGuardians""",
                
                'give_behind_scenes': """Behind the scenes at today's move-out cleaning! 🧽

{behind_scenes_story}

This is why we document everything with photos - protects both property managers AND tenants.

What's the wildest thing you've found in a rental turnover? 👀

#BehindTheScenes #PropertyManagement #CleaningService""",
                
                'give_success_story': """CLIENT WIN: {client_type} saved {time_saved} on their last turnover! ⭐

The situation: {problem_description}

Our solution: {solution_provided}

The result: {outcome_achieved}

Stories like this make our day! 🙌

#ClientSuccess #PropertyManagement #CleaningService #TwinCities""",
                
                'ask_service': """Is your next property turnover stressing you out? 😰

We get it. Tenant moveouts can be chaotic:
❌ Unexpected damages
❌ Time pressure for new tenants  
❌ Coordinating multiple vendors
❌ Quality concerns

Here's how we solve this: {solution_overview}

Ready to make your next turnover stress-free? Comment 'TURNOVER' below! 👇

#StressFreeCleanig #PropertyManagement #TwinCities"""
            },
            
            'linkedin': {
                'give_industry_insight': """Industry Insight: {insight_title}

After working with 100+ property management companies in the Twin Cities, I've noticed a pattern:

{professional_insight}

Key takeaway for property managers:
{actionable_advice}

What's been your experience with this? Share in the comments.

#PropertyManagement #RealEstate #TwinCities #BusinessInsights""",
                
                'ask_professional': """Property Managers: What's your biggest challenge with tenant turnovers?

In my experience working with Twin Cities property management companies, the most common pain points are:

• Timeline pressure (new tenant moving in soon)
• Quality control (ensuring move-in ready condition)  
• Damage documentation (protecting security deposits)
• Vendor coordination (multiple services, multiple schedules)

We've developed systems to address each of these challenges.

Curious about our approach? Let's connect.

#PropertyManagement #B2B #Solutions #TwinCities"""
            },
            
            'instagram': {
                'give_visual_tip': """{emoji} {tip_title}

{short_valuable_tip}

Save this post for your next rental turnover! 💾

{hashtags}""",
                
                'ask_visual': """Before ➡️ After magic ✨

Swipe to see the transformation!

Is your property ready for move-in photos? 📸

DM us 'READY' to get started! 

{hashtags}"""
            }
        }
    
    def _load_platform_specifications(self) -> Dict[str, Dict[str, Any]]:
        """Load platform-specific posting requirements and best practices."""
        return {
            'facebook': {
                'max_chars': 2000,
                'optimal_chars': 400,
                'image_sizes': {'post': (1200, 630), 'story': (1080, 1920)},
                'best_times': ['9:00', '13:00', '15:00'],
                'hashtag_limit': 30,
                'content_types': ['text', 'image', 'video', 'carousel']
            },
            'instagram': {
                'max_chars': 2200,
                'optimal_chars': 300,
                'image_sizes': {'post': (1080, 1080), 'story': (1080, 1920)},
                'best_times': ['11:00', '13:00', '17:00'],
                'hashtag_limit': 30,
                'content_types': ['image', 'video', 'reel', 'story']
            },
            'linkedin': {
                'max_chars': 3000,
                'optimal_chars': 600,
                'image_sizes': {'post': (1200, 627)},
                'best_times': ['8:00', '12:00', '17:00'],
                'hashtag_limit': 5,
                'content_types': ['text', 'image', 'video', 'article']
            },
            'nextdoor': {
                'max_chars': 1000,
                'optimal_chars': 300,
                'best_times': ['10:00', '14:00', '19:00'],
                'content_types': ['text', 'image'],
                'local_focus': True
            },
            'tiktok': {
                'max_chars': 150,
                'optimal_chars': 100,
                'video_length': {'min': 15, 'max': 180, 'optimal': 60},
                'best_times': ['6:00', '10:00', '19:00'],
                'hashtag_limit': 100,
                'content_types': ['video']
            }
        }
    
    async def create_content_calendar(self, weeks_ahead: int = 4) -> ContentCalendar:
        """Create comprehensive content calendar following Give Give Give Ask methodology."""
        try:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate optimal content mix using Hormozi methodology
            total_posts_per_week = 14  # 2 posts per day across 7 days
            give_posts_per_week = 10   # 71% give content
            ask_posts_per_week = 4     # 29% ask content
            
            calendar_posts = []
            
            for week in range(weeks_ahead):
                week_start = start_date + timedelta(weeks=week)
                
                # Generate give content (3:1 ratio as per Hormozi)
                give_posts = await self._generate_give_content(give_posts_per_week, week_start)
                ask_posts = await self._generate_ask_content(ask_posts_per_week, week_start)
                
                calendar_posts.extend(give_posts + ask_posts)
            
            # Create content calendar
            calendar = ContentCalendar(
                week_start=start_date,
                posts=calendar_posts,
                give_give_give_ask_ratio={'give': give_posts_per_week * weeks_ahead, 'ask': ask_posts_per_week * weeks_ahead},
                platforms_active=['facebook', 'instagram', 'linkedin', 'nextdoor'],
                content_themes=[
                    'property_management_tips',
                    'cleaning_education', 
                    'client_success_stories',
                    'behind_the_scenes',
                    'market_insights',
                    'community_engagement'
                ]
            )
            
            self.content_calendar = calendar
            logger.info(f"Created content calendar with {len(calendar_posts)} posts over {weeks_ahead} weeks")
            
            return calendar
            
        except Exception as e:
            logger.error(f"Error creating content calendar: {e}")
            raise
    
    async def _generate_give_content(self, count: int, week_start: datetime) -> List[ContentPost]:
        """Generate 'give' content using Hormozi value-first methodology."""
        give_posts = []
        
        # Content categories for give posts
        give_categories = [
            'cleaning_tips',
            'property_management_insights', 
            'market_education',
            'behind_the_scenes',
            'client_success_stories',
            'community_value'
        ]
        
        for i in range(count):
            category = give_categories[i % len(give_categories)]
            platform = ['facebook', 'instagram', 'linkedin'][i % 3]
            
            # Generate content using AI
            content = await self._generate_ai_content(
                content_type='give',
                category=category,
                platform=platform
            )
            
            post = ContentPost(
                post_id=f"give_{week_start.strftime('%Y%m%d')}_{i:02d}",
                platform=platform,
                content_type='give',
                title=content['title'],
                content=content['content'],
                hashtags=content['hashtags'],
                scheduled_time=week_start + timedelta(days=i//2, hours=9 + (i%2)*6),
                status='draft',
                hormozi_framework='give_give_give_ask',
                target_audience=content['target_audience']
            )
            
            give_posts.append(post)
        
        return give_posts
    
    async def _generate_ask_content(self, count: int, week_start: datetime) -> List[ContentPost]:
        """Generate 'ask' content with strategic positioning."""
        ask_posts = []
        
        ask_categories = [
            'service_promotion',
            'review_request',
            'referral_ask',
            'booking_request'
        ]
        
        for i in range(count):
            category = ask_categories[i % len(ask_categories)]
            platform = ['facebook', 'linkedin'][i % 2]  # Focus asks on FB and LinkedIn
            
            content = await self._generate_ai_content(
                content_type='ask',
                category=category,
                platform=platform
            )
            
            post = ContentPost(
                post_id=f"ask_{week_start.strftime('%Y%m%d')}_{i:02d}",
                platform=platform,
                content_type='ask',
                title=content['title'],
                content=content['content'],
                hashtags=content['hashtags'],
                scheduled_time=week_start + timedelta(days=2 + i*2, hours=13),  # Strategic timing
                status='draft',
                hormozi_framework='give_give_give_ask',
                target_audience=content['target_audience']
            )
            
            ask_posts.append(post)
        
        return ask_posts
    
    async def _generate_ai_content(self, content_type: str, category: str, platform: str) -> Dict[str, Any]:
        """Generate AI-powered content using Hormozi principles."""
        try:
            frameworks = self.content_frameworks
            templates = self.hormozi_templates.get(platform, {})
            platform_spec = self.platform_specs.get(platform, {})
            
            # Build AI prompt for content generation
            prompt = f"""Create {content_type} social media content for Grime Guardians cleaning service.

BUSINESS CONTEXT:
- Premium cleaning service in Twin Cities, MN
- Target: Property managers, realtors, real estate investors
- USP: "We clean like it's our name on the lease"
- 70+ five-star reviews, BBB-accredited
- Competitive advantage: Professional documentation and premium results

CONTENT REQUIREMENTS:
- Type: {content_type} ({category})
- Platform: {platform}
- Max characters: {platform_spec.get('optimal_chars', 400)}
- Hormozi methodology: {"Value-first, education-focused" if content_type == 'give' else "Soft ask with clear value proposition"}

FRAMEWORKS TO USE:
{json.dumps(frameworks['give_give_give_ask'], indent=2)}

CONTENT HOOKS:
{json.dumps(frameworks['content_hooks'], indent=2)}

Generate content that includes:
1. Title (engaging hook)
2. Main content (valuable and actionable)
3. Call to action (appropriate for {content_type})
4. Hashtags (relevant and strategic)
5. Target audience (specific segment)

Return as JSON with: title, content, hashtags, target_audience"""
            
            response = await self.openai_client.chat.completions.create(
                model='gpt-4-turbo-preview',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            try:
                content_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                content_text = response.choices[0].message.content
                content_data = {
                    'title': f"{category.replace('_', ' ').title()} - {platform.title()}",
                    'content': content_text,
                    'hashtags': ['#GrimeGuardians', '#TwinCities', '#CleaningService'],
                    'target_audience': 'property_managers'
                }
            
            return content_data
            
        except Exception as e:
            logger.error(f"Error generating AI content: {e}")
            # Return fallback content
            return {
                'title': f"Quality Cleaning Tips for {category.replace('_', ' ').title()}",
                'content': f"Professional cleaning insights for Twin Cities property professionals. Contact Grime Guardians for premium service.",
                'hashtags': ['#GrimeGuardians', '#CleaningTips', '#PropertyManagement'],
                'target_audience': 'property_managers'
            }
    
    async def create_ab_test(self, post_concept: Dict[str, Any], 
                           test_variables: List[str]) -> ABTestResult:
        """Create A/B test for content optimization."""
        try:
            test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate variant A (control)
            variant_a_content = await self._generate_ai_content(
                content_type=post_concept['content_type'],
                category=post_concept['category'],
                platform=post_concept['platform']
            )
            
            # Generate variant B with specific modifications
            variant_b_prompt = f"""Modify this social media content for A/B testing:

Original: {variant_a_content['content']}

Test Variables: {', '.join(test_variables)}

Create a variation that tests: {test_variables[0]}

Keep the same core message but modify the approach based on the test variable.
Return as JSON with: title, content, hashtags, target_audience"""
            
            variant_b_response = await self.openai_client.chat.completions.create(
                model='gpt-4-turbo-preview',
                messages=[{'role': 'user', 'content': variant_b_prompt}],
                max_tokens=600,
                temperature=0.8
            )
            
            try:
                variant_b_content = json.loads(variant_b_response.choices[0].message.content)
            except json.JSONDecodeError:
                variant_b_content = variant_a_content.copy()
                variant_b_content['title'] = variant_b_content['title'] + " (Variant B)"
            
            # Create content posts for both variants
            base_time = datetime.now() + timedelta(hours=2)
            
            variant_a_post = ContentPost(
                post_id=f"{test_id}_variant_a",
                platform=post_concept['platform'],
                content_type=post_concept['content_type'],
                title=variant_a_content['title'],
                content=variant_a_content['content'],
                hashtags=variant_a_content['hashtags'],
                scheduled_time=base_time,
                status='test_ready',
                hormozi_framework='give_give_give_ask',
                target_audience=variant_a_content['target_audience']
            )
            
            variant_b_post = ContentPost(
                post_id=f"{test_id}_variant_b",
                platform=post_concept['platform'],
                content_type=post_concept['content_type'],
                title=variant_b_content['title'],
                content=variant_b_content['content'],
                hashtags=variant_b_content['hashtags'],
                scheduled_time=base_time + timedelta(hours=24),  # Test 24 hours apart
                status='test_ready',
                hormozi_framework='give_give_give_ask',
                target_audience=variant_b_content['target_audience']
            )
            
            ab_test = ABTestResult(
                test_id=test_id,
                variant_a=variant_a_post,
                variant_b=variant_b_post,
                winner='pending',
                metrics={},
                confidence_level=0.0,
                recommendation='Test in progress - monitor for 48 hours minimum'
            )
            
            self.active_ab_tests.append(ab_test)
            logger.info(f"Created A/B test: {test_id}")
            
            return ab_test
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise
    
    async def analyze_content_performance(self, days_back: int = 7) -> Dict[str, Any]:
        """Analyze content performance and provide optimization insights."""
        try:
            # This would integrate with actual social media APIs
            # For now, return mock analysis structure
            
            analysis = {
                'period_days': days_back,
                'total_posts': 0,
                'engagement_summary': {
                    'total_likes': 0,
                    'total_comments': 0,
                    'total_shares': 0,
                    'average_engagement_rate': 0.0
                },
                'give_vs_ask_performance': {
                    'give_posts': {'count': 0, 'avg_engagement': 0.0},
                    'ask_posts': {'count': 0, 'avg_engagement': 0.0}
                },
                'platform_performance': {},
                'content_type_performance': {},
                'hormozi_insights': [],
                'optimization_recommendations': []
            }
            
            # Add Hormozi-specific insights
            analysis['hormozi_insights'] = [
                "Give content shows higher organic reach - maintain 3:1 ratio",
                "Educational tips generate most comments - increase frequency",
                "Behind-the-scenes content builds trust - weekly recommended",
                "Ask posts perform better after 3+ give posts - timing optimal"
            ]
            
            analysis['optimization_recommendations'] = [
                "Increase educational content frequency on LinkedIn",
                "Test video format for behind-the-scenes content",
                "Schedule ask posts 2 hours after peak engagement times",
                "Add more local Twin Cities hashtags for geographic targeting"
            ]
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {e}")
            return {}
    
    def get_content_calendar_summary(self, weeks: int = 2) -> str:
        """Get summary of upcoming content calendar."""
        if not self.content_calendar:
            return "No content calendar created yet. Use create_content_calendar() first."
        
        upcoming_posts = [
            post for post in self.content_calendar.posts 
            if post.scheduled_time <= datetime.now() + timedelta(weeks=weeks)
        ]
        
        give_count = len([p for p in upcoming_posts if p.content_type == 'give'])
        ask_count = len([p for p in upcoming_posts if p.content_type == 'ask'])
        
        summary = f"📅 CONTENT CALENDAR ({weeks} weeks):\n"
        summary += f"• Total Posts: {len(upcoming_posts)}\n"
        summary += f"• Give Content: {give_count} (Value-first)\n"
        summary += f"• Ask Content: {ask_count} (Strategic asks)\n"
        summary += f"• Ratio: {give_count}:{ask_count} ({'✅ Optimal' if give_count >= ask_count * 2 else '⚠️ Needs more give content'})\n"
        summary += f"• Platforms: {', '.join(set(p.platform for p in upcoming_posts))}\n"
        
        return summary
    
    def get_give_give_give_ask_status(self) -> str:
        """Get current status of Give Give Give Ask methodology compliance."""
        tracker = self.content_ratio_tracker
        
        status = f"🎯 GIVE GIVE GIVE ASK STATUS:\n"
        status += f"• Give Posts This Cycle: {tracker['give_count']}\n"
        status += f"• Ask Posts This Cycle: {tracker['ask_count']}\n"
        status += f"• Current Phase: {tracker['current_cycle'].title()}\n"
        
        if tracker['give_count'] >= 3 and tracker['current_cycle'] == 'give':
            status += f"• ✅ Ready for strategic ask content\n"
        elif tracker['current_cycle'] == 'ask':
            status += f"• 🔄 Reset to give cycle after current ask\n"
        else:
            needed = 3 - tracker['give_count']
            status += f"• 📈 Need {needed} more give posts before next ask\n"
        
        return status


# Global Social Media Agent instance
social_media_agent = SocialMediaAgent()