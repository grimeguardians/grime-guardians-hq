"""
Social Media Agent - Content Planning & Automation
Handles content creation, scheduling, A/B testing, and engagement.
Implements Hormozi's Give-Give-Give-Ask methodology.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import openai
import logging

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ContentPost:
    """Social media content post structure."""
    post_id: str
    platform: str           # 'facebook', 'instagram', 'linkedin', 'nextdoor', 'tiktok'
    content_type: str       # 'give', 'ask', 'story', 'tips', 'social_proof'
    title: str
    content: str
    hashtags: List[str]
    scheduled_time: datetime
    status: str             # 'draft', 'scheduled', 'posted', 'failed'
    engagement_metrics: Dict[str, int] = None
    hormozi_framework: str = ""
    target_audience: str = ""


@dataclass
class ContentCalendar:
    """Social media content calendar structure."""
    week_start: datetime
    posts: List[ContentPost]
    give_give_give_ask_ratio: Dict[str, int]
    platforms_active: List[str]
    content_themes: List[str]


@dataclass
class ABTestResult:
    """A/B test results for content optimization."""
    test_id: str
    variant_a: ContentPost
    variant_b: ContentPost
    winner: str             # 'a', 'b', or 'pending'
    metrics: Dict[str, float]
    confidence_level: float
    recommendation: str


class SocialMediaAgent:
    """
    Social media management agent implementing Hormozi's Give-Give-Give-Ask methodology.

    Handles:
    - Content planning (3:1 give/ask ratio)
    - Multi-platform scheduling
    - A/B testing for optimization
    - Engagement monitoring
    - Content calendar management
    """

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.content_calendar: Optional[ContentCalendar] = None
        self.active_ab_tests: List[ABTestResult] = []
        self.ratio_tracker = {
            "give_count": 0,
            "ask_count": 0,
            "current_phase": "give",
        }

        # Platform character limits and best post times
        self.platform_specs = {
            "facebook":  {"optimal_chars": 400,  "best_times": ["9:00", "13:00", "15:00"]},
            "instagram": {"optimal_chars": 300,  "best_times": ["11:00", "13:00", "17:00"]},
            "linkedin":  {"optimal_chars": 600,  "best_times": ["8:00", "12:00", "17:00"]},
            "nextdoor":  {"optimal_chars": 300,  "best_times": ["10:00", "14:00", "19:00"]},
        }

        # Content hooks — Hormozi-aligned
        self.hooks = {
            "curiosity":  ["What most property managers don't know...",
                           "The #1 mistake I see realtors make...",
                           "Here's what happened when..."],
            "authority":  ["After 500+ cleanings, here's what I've learned...",
                           "BBB-accredited tip:",
                           "From our 70+ five-star reviews..."],
            "urgency":    ["Tenant moving out this week?",
                           "Before your listing photos...",
                           "Don't let this cost you a deposit..."],
        }

    async def create_content_calendar(self, weeks_ahead: int = 4) -> ContentCalendar:
        """
        Create a content calendar following the Give-Give-Give-Ask methodology.

        Args:
            weeks_ahead (int): Number of weeks to plan.

        Returns:
            ContentCalendar: Populated calendar with give and ask posts.
        """
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        posts: List[ContentPost] = []

        give_per_week = 10
        ask_per_week = 4

        for week in range(weeks_ahead):
            week_start = start_date + timedelta(weeks=week)
            posts.extend(await self._generate_give_content(give_per_week, week_start))
            posts.extend(await self._generate_ask_content(ask_per_week, week_start))

        self.content_calendar = ContentCalendar(
            week_start=start_date,
            posts=posts,
            give_give_give_ask_ratio={"give": give_per_week * weeks_ahead,
                                      "ask": ask_per_week * weeks_ahead},
            platforms_active=["facebook", "instagram", "linkedin", "nextdoor"],
            content_themes=[
                "property_management_tips", "cleaning_education",
                "client_success_stories", "behind_the_scenes",
                "market_insights", "community_engagement",
            ],
        )

        logger.info(f"Content calendar created: {len(posts)} posts over {weeks_ahead} weeks")
        return self.content_calendar

    async def _generate_give_content(self, count: int, week_start: datetime) -> List[ContentPost]:
        """Generate 'give' posts — value-first, education-focused."""
        categories = ["cleaning_tips", "property_management_insights",
                      "market_education", "behind_the_scenes",
                      "client_success_stories", "community_value"]
        posts = []

        for i in range(count):
            platform = ["facebook", "instagram", "linkedin"][i % 3]
            category = categories[i % len(categories)]
            content = await self._generate_ai_content("give", category, platform)

            posts.append(ContentPost(
                post_id=f"give_{week_start.strftime('%Y%m%d')}_{i:02d}",
                platform=platform,
                content_type="give",
                title=content["title"],
                content=content["content"],
                hashtags=content["hashtags"],
                scheduled_time=week_start + timedelta(days=i // 2, hours=9 + (i % 2) * 6),
                status="draft",
                hormozi_framework="give_give_give_ask",
                target_audience=content["target_audience"],
            ))

        return posts

    async def _generate_ask_content(self, count: int, week_start: datetime) -> List[ContentPost]:
        """Generate 'ask' posts — strategically placed after give content."""
        categories = ["service_promotion", "review_request", "referral_ask", "booking_request"]
        posts = []

        for i in range(count):
            platform = ["facebook", "linkedin"][i % 2]
            category = categories[i % len(categories)]
            content = await self._generate_ai_content("ask", category, platform)

            posts.append(ContentPost(
                post_id=f"ask_{week_start.strftime('%Y%m%d')}_{i:02d}",
                platform=platform,
                content_type="ask",
                title=content["title"],
                content=content["content"],
                hashtags=content["hashtags"],
                scheduled_time=week_start + timedelta(days=2 + i * 2, hours=13),
                status="draft",
                hormozi_framework="give_give_give_ask",
                target_audience=content["target_audience"],
            ))

        return posts

    async def _generate_ai_content(self, content_type: str, category: str, platform: str) -> Dict[str, Any]:
        """
        Generate AI-powered social post content.

        Args:
            content_type (str): 'give' or 'ask'
            category (str): Content category
            platform (str): Target platform

        Returns:
            dict: title, content, hashtags, target_audience
        """
        spec = self.platform_specs.get(platform, {"optimal_chars": 400})

        prompt = f"""Create {content_type} social media content for Grime Guardians cleaning service.

BUSINESS: Premium cleaning in Twin Cities, MN. Target: Property managers, realtors, investors.
TAGLINE: "We clean like it's our name on the lease"
SOCIAL PROOF: 70+ five-star Google reviews, BBB-accredited
PLATFORM: {platform} (target {spec['optimal_chars']} characters)
CONTENT TYPE: {content_type} — {category}
METHODOLOGY: Hormozi Give-Give-Give-Ask. {"Value-first, educational" if content_type == "give" else "Soft ask with clear value prop"}

Return JSON: {{"title": "...", "content": "...", "hashtags": [...], "target_audience": "..."}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.8,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return {
                "title": f"{category.replace('_', ' ').title()}",
                "content": "Professional cleaning insights for Twin Cities property professionals.",
                "hashtags": ["#GrimeGuardians", "#TwinCities", "#PropertyManagement"],
                "target_audience": "property_managers",
            }

    async def create_ab_test(self, post_concept: Dict[str, Any],
                              test_variables: List[str]) -> ABTestResult:
        """
        Create an A/B test for content optimization.

        Args:
            post_concept (dict): Base post concept (content_type, category, platform)
            test_variables (list): Variables to test (e.g., ['hook_style', 'cta'])

        Returns:
            ABTestResult: Test with both variants ready to schedule.
        """
        test_id = f"ab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        platform = post_concept.get("platform", "facebook")

        variant_a_data = await self._generate_ai_content(
            post_concept["content_type"], post_concept["category"], platform
        )
        variant_b_prompt = (
            f"Rewrite this social post testing: {test_variables[0]}\n"
            f"Original: {variant_a_data['content']}\n"
            f"Return JSON: {{title, content, hashtags, target_audience}}"
        )

        try:
            resp = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": variant_b_prompt}],
                max_tokens=500,
                temperature=0.8,
            )
            variant_b_data = json.loads(resp.choices[0].message.content)
        except Exception:
            variant_b_data = {**variant_a_data, "title": variant_a_data["title"] + " (B)"}

        base_time = datetime.now() + timedelta(hours=2)

        def _make_post(pid: str, data: Dict, sched: datetime) -> ContentPost:
            return ContentPost(
                post_id=pid, platform=platform,
                content_type=post_concept["content_type"],
                title=data["title"], content=data["content"],
                hashtags=data["hashtags"], scheduled_time=sched,
                status="test_ready", hormozi_framework="give_give_give_ask",
                target_audience=data["target_audience"],
            )

        result = ABTestResult(
            test_id=test_id,
            variant_a=_make_post(f"{test_id}_a", variant_a_data, base_time),
            variant_b=_make_post(f"{test_id}_b", variant_b_data, base_time + timedelta(hours=24)),
            winner="pending",
            metrics={},
            confidence_level=0.0,
            recommendation="Monitor for 48 hours minimum before declaring winner.",
        )

        self.active_ab_tests.append(result)
        logger.info(f"A/B test created: {test_id}")
        return result

    def get_calendar_summary(self, weeks: int = 2) -> str:
        """
        Get a summary of the upcoming content calendar.

        Args:
            weeks (int): Weeks of calendar to summarize.

        Returns:
            str: Formatted summary string.
        """
        if not self.content_calendar:
            return "No calendar created yet. Call create_content_calendar() first."

        cutoff = datetime.now() + timedelta(weeks=weeks)
        upcoming = [p for p in self.content_calendar.posts if p.scheduled_time <= cutoff]
        give_count = sum(1 for p in upcoming if p.content_type == "give")
        ask_count = sum(1 for p in upcoming if p.content_type == "ask")
        ratio_ok = give_count >= ask_count * 2

        return (
            f"Content Calendar ({weeks}wk): {len(upcoming)} posts | "
            f"Give: {give_count} | Ask: {ask_count} | "
            f"Ratio: {'OK' if ratio_ok else 'Needs more give content'}"
        )

    def get_hormozi_status(self) -> str:
        """
        Get current Give-Give-Give-Ask compliance status.

        Returns:
            str: Status string.
        """
        t = self.ratio_tracker
        needed = max(0, 3 - t["give_count"])
        if t["give_count"] >= 3:
            phase = "Ready for ask content"
        else:
            phase = f"Need {needed} more give posts before next ask"
        return f"Give/Ask Tracker — Give: {t['give_count']} | Ask: {t['ask_count']} | {phase}"


# Singleton
social_media_agent = SocialMediaAgent()
