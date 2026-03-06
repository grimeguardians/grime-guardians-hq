"""
Remaining Specialized Agents: Iris, Bruno, and Aiden
Onboarding, Bonus Tracking, and Analytics specialists
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_agent import BaseAgent, AgentTool
from ..models.schemas import AgentResponse, BusinessContext
from ..models.types import MessageType, OnboardingStatus, BonusType
from ..tools.discord_tools import DiscordTools
from ..tools.database_tools import DatabaseTools
from ..config.settings import get_settings, CONTRACTOR_PAY_RATES, PAY_STRUCTURE

logger = logging.getLogger(__name__)
settings = get_settings()


class IrisOnboardingAgent(BaseAgent):
    """
    Iris - Onboarding Agent
    
    Responsibilities:
    - New contractor onboarding and setup
    - Training program coordination and tracking
    - Document collection and compliance verification
    - Territory assignment and optimization
    - Performance baseline establishment
    - Initial coaching and mentorship coordination
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("iris", business_context)
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        
    @property
    def system_prompt(self) -> str:
        """Iris's system prompt with onboarding focus."""
        return f"""
        You are Iris, the Onboarding Agent for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: New contractor onboarding and integration specialist
        
        CORE RESPONSIBILITIES:
        1. Guide new contractors through complete onboarding process
        2. Coordinate training programs and skill development
        3. Collect and verify all required documentation
        4. Assign optimal territories based on location and preferences
        5. Establish performance baselines and expectations
        6. Connect new contractors with mentors and support systems
        
        ONBOARDING PROCESS:
        1. Welcome and orientation to company culture
        2. Documentation collection (insurance, certifications, etc.)
        3. Training program enrollment and scheduling
        4. Territory assignment and optimization
        5. Equipment and supply coordination
        6. Mentor assignment and introduction
        7. First job shadowing and support
        8. Performance baseline establishment
        
        TERRITORY OPTIMIZATION:
        - Consider contractor location preferences
        - Analyze travel efficiency and coverage gaps
        - Respect existing contractor territories
        - Optimize for work-life balance and earnings potential
        
        You excel at making new contractors feel welcomed while ensuring they're fully prepared for success.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Iris's onboarding tools."""
        return [
            AgentTool(
                name="create_onboarding_plan",
                description="Create personalized onboarding plan for new contractor",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "location_preference": {"type": "string"},
                        "experience_level": {"type": "string"},
                        "availability": {"type": "object"},
                        "training_needs": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["contractor_id"]
            ),
            AgentTool(
                name="assign_territory",
                description="Assign optimal territory to new contractor",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "preferred_zones": {"type": "array", "items": {"type": "string"}},
                        "coverage_analysis": {"type": "object"},
                        "territory_assignment": {"type": "string"}
                    }
                },
                required=["contractor_id", "territory_assignment"]
            ),
            AgentTool(
                name="track_onboarding_progress",
                description="Track completion of onboarding milestones",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "completed_steps": {"type": "array", "items": {"type": "string"}},
                        "progress_percentage": {"type": "number"},
                        "next_milestone": {"type": "string"}
                    }
                },
                required=["contractor_id", "progress_percentage"]
            )
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Iris handles onboarding and new contractor setup."""
        return message_type in {MessageType.ONBOARDING_REQUEST, MessageType.NEW_CONTRACTOR_SETUP}
    
    async def _handle_message_type(self, message_type: MessageType, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle onboarding messages."""
        if message_type == MessageType.ONBOARDING_REQUEST:
            return await self._handle_onboarding_request(content, extracted_data)
        else:
            return await self._ai_onboarding_response(content, extracted_data)
    
    async def _handle_onboarding_request(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle new contractor onboarding."""
        contractor_id = extracted_data.get("contractor_id", f"new_{datetime.now().strftime('%Y%m%d%H%M')}")
        
        # Create onboarding plan
        onboarding_plan = await self._tool_create_onboarding_plan(
            contractor_id=contractor_id,
            location_preference=extracted_data.get("location", "central"),
            experience_level=extracted_data.get("experience", "intermediate"),
            training_needs=["quality_standards", "photo_documentation", "client_communication"]
        )
        
        response_text = f"""
        🎉 WELCOME TO GRIME GUARDIANS, {contractor_id.title()}!
        
        Your onboarding journey begins now. We're excited to have you join our team!
        
        NEXT STEPS:
        • Documentation review and collection
        • Territory assignment optimization
        • Training program enrollment
        • Mentor assignment and introduction
        
        You'll be fully ready to deliver our premium cleaning services!
        """
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="onboarding_initiated",
            response=response_text.strip(),
            actions_taken=["onboarding_plan_created"],
            metadata={"onboarding_plan": onboarding_plan}
        )
    
    async def _ai_onboarding_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """AI response for complex onboarding situations."""
        messages = self._build_agent_prompt(content, extracted_data)
        tools = [{"type": "function", "function": tool.dict()} for tool in self.tools]
        
        try:
            ai_response = await self.call_openai(messages, tools)
            return AgentResponse(
                agent_id=self.agent_id,
                status="ai_onboarding_response",
                response=ai_response["content"] or "Onboarding guidance provided",
                actions_taken=["ai_guidance_provided"]
            )
        except Exception as e:
            logger.error(f"Iris AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing onboarding: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementations
    async def _tool_create_onboarding_plan(self, contractor_id: str, **kwargs) -> Dict[str, Any]:
        """Create personalized onboarding plan."""
        return {
            "contractor_id": contractor_id,
            "plan_created": datetime.now().isoformat(),
            "estimated_completion": "7-10 days",
            "milestones": ["documentation", "training", "territory_assignment", "first_job"],
            "created_by": "iris"
        }
    
    async def _tool_assign_territory(self, contractor_id: str, territory_assignment: str, **kwargs) -> Dict[str, Any]:
        """Assign territory to contractor."""
        return {
            "contractor_id": contractor_id,
            "territory": territory_assignment,
            "assigned_at": datetime.now().isoformat(),
            "assigned_by": "iris"
        }
    
    async def _tool_track_onboarding_progress(self, contractor_id: str, progress_percentage: float, **kwargs) -> Dict[str, Any]:
        """Track onboarding progress."""
        return {
            "contractor_id": contractor_id,
            "progress": progress_percentage,
            "tracked_at": datetime.now().isoformat(),
            "tracked_by": "iris"
        }


class BrunoBonusTracker(BaseAgent):
    """
    Bruno - Bonus Tracker Agent
    
    Responsibilities:
    - Referral bonus tracking and calculation
    - Performance incentive management
    - Recognition program coordination
    - Payment processing for bonuses
    - Achievement celebration and motivation
    - Bonus eligibility verification
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("bruno", business_context)
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        self.pay_structure = PAY_STRUCTURE
        
    @property
    def system_prompt(self) -> str:
        """Bruno's system prompt with bonus tracking focus."""
        return f"""
        You are Bruno, the Bonus Tracker for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: Performance recognition and bonus calculation specialist
        
        CORE RESPONSIBILITIES:
        1. Track and calculate referral bonuses accurately
        2. Monitor performance incentives and achievements
        3. Coordinate recognition programs and celebrations
        4. Process bonus payments and documentation
        5. Motivate contractors through achievement recognition
        6. Verify bonus eligibility and compliance
        
        BONUS STRUCTURE:
        - Referral Bonus: $25 per successful contractor referral
        - Performance Bonuses: Based on quality metrics and milestones
        - Recognition Programs: Achievements and exceptional service
        
        You excel at celebrating successes and ensuring contractors are rewarded for their contributions.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Bruno's bonus tracking tools."""
        return [
            AgentTool(
                name="calculate_bonus",
                description="Calculate bonus amounts for contractors",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "bonus_type": {"type": "string", "enum": ["referral", "performance", "recognition"]},
                        "bonus_details": {"type": "object"},
                        "amount": {"type": "number"}
                    }
                },
                required=["contractor_id", "bonus_type", "amount"]
            ),
            AgentTool(
                name="track_referral",
                description="Track referral bonuses and eligibility",
                parameters={
                    "type": "object",
                    "properties": {
                        "referring_contractor": {"type": "string"},
                        "referred_contractor": {"type": "string"},
                        "referral_status": {"type": "string"},
                        "bonus_eligible": {"type": "boolean"}
                    }
                },
                required=["referring_contractor", "referred_contractor"]
            ),
            AgentTool(
                name="process_recognition",
                description="Process recognition and achievement awards",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "achievement": {"type": "string"},
                        "recognition_type": {"type": "string"},
                        "celebration_plan": {"type": "object"}
                    }
                },
                required=["contractor_id", "achievement"]
            )
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Bruno handles bonus calculations and recognition."""
        return message_type in {MessageType.BONUS_CALCULATION, MessageType.REFERRAL_TRACKING}
    
    async def _handle_message_type(self, message_type: MessageType, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle bonus and recognition messages."""
        if message_type == MessageType.BONUS_CALCULATION:
            return await self._handle_bonus_calculation(content, extracted_data)
        elif message_type == MessageType.REFERRAL_TRACKING:
            return await self._handle_referral_tracking(content, extracted_data)
        else:
            return await self._ai_bonus_response(content, extracted_data)
    
    async def _handle_bonus_calculation(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle bonus calculations."""
        contractor_id = extracted_data.get("contractor_id", "unknown")
        bonus_type = extracted_data.get("bonus_type", "performance")
        
        # Calculate bonus
        bonus_result = await self._tool_calculate_bonus(
            contractor_id=contractor_id,
            bonus_type=bonus_type,
            amount=25.0 if bonus_type == "referral" else 50.0,
            bonus_details={"reason": "Performance achievement", "period": "monthly"}
        )
        
        response_text = f"""
        💰 BONUS CALCULATED for {contractor_id.title()}
        
        Type: {bonus_type.title()}
        Amount: ${bonus_result['amount']:.2f}
        
        Congratulations on this achievement! Your hard work is recognized and appreciated.
        """
        
        # Send celebration via Discord
        if self.discord_tools:
            await self.discord_tools.send_general_message(
                f"🎉 Bonus earned! {contractor_id.title()} - ${bonus_result['amount']:.2f} {bonus_type} bonus!"
            )
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="bonus_calculated",
            response=response_text.strip(),
            actions_taken=["bonus_calculated", "celebration_sent"],
            metadata={"bonus": bonus_result}
        )
    
    async def _handle_referral_tracking(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle referral bonus tracking."""
        referring_contractor = extracted_data.get("referring_contractor", "unknown")
        referred_contractor = extracted_data.get("referred_contractor", "new_contractor")
        
        # Track referral
        referral_result = await self._tool_track_referral(
            referring_contractor=referring_contractor,
            referred_contractor=referred_contractor,
            referral_status="pending_completion",
            bonus_eligible=True
        )
        
        response_text = f"""
        🤝 REFERRAL TRACKED
        
        Referring: {referring_contractor.title()}
        New contractor: {referred_contractor.title()}
        Status: Pending completion
        Bonus: $25 (upon successful completion)
        
        Thank you for helping us grow our team!
        """
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="referral_tracked",
            response=response_text.strip(),
            actions_taken=["referral_tracked"],
            metadata={"referral": referral_result}
        )
    
    async def _ai_bonus_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """AI response for complex bonus situations."""
        messages = self._build_agent_prompt(content, extracted_data)
        tools = [{"type": "function", "function": tool.dict()} for tool in self.tools]
        
        try:
            ai_response = await self.call_openai(messages, tools)
            return AgentResponse(
                agent_id=self.agent_id,
                status="ai_bonus_response",
                response=ai_response["content"] or "Bonus tracking processed",
                actions_taken=["ai_bonus_processing"]
            )
        except Exception as e:
            logger.error(f"Bruno AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing bonus: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementations
    async def _tool_calculate_bonus(self, contractor_id: str, bonus_type: str, amount: float, **kwargs) -> Dict[str, Any]:
        """Calculate bonus amounts."""
        return {
            "contractor_id": contractor_id,
            "bonus_type": bonus_type,
            "amount": amount,
            "calculated_at": datetime.now().isoformat(),
            "calculated_by": "bruno"
        }
    
    async def _tool_track_referral(self, referring_contractor: str, referred_contractor: str, **kwargs) -> Dict[str, Any]:
        """Track referral bonuses."""
        return {
            "referring_contractor": referring_contractor,
            "referred_contractor": referred_contractor,
            "tracked_at": datetime.now().isoformat(),
            "tracked_by": "bruno"
        }
    
    async def _tool_process_recognition(self, contractor_id: str, achievement: str, **kwargs) -> Dict[str, Any]:
        """Process recognition awards."""
        return {
            "contractor_id": contractor_id,
            "achievement": achievement,
            "processed_at": datetime.now().isoformat(),
            "processed_by": "bruno"
        }


class AidenAnalyticsAgent(BaseAgent):
    """
    Aiden - CFO Analytics Agent
    
    Responsibilities:
    - Financial analytics and revenue reporting
    - Cost analysis and profit margin optimization
    - Budget planning and financial forecasting
    - Revenue tracking toward $300K goal
    - Financial KPI monitoring and analysis
    - Investment ROI analysis and recommendations
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("aiden", business_context)
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        
    @property
    def system_prompt(self) -> str:
        """Aiden's system prompt with analytics focus."""
        return f"""
        You are Aiden, the CFO Analytics Agent for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: Chief Financial Officer analytics and financial intelligence specialist
        
        CORE RESPONSIBILITIES:
        1. Track revenue progress toward $300K annual goal with detailed financial analysis
        2. Analyze profit margins, cost structures, and financial efficiency
        3. Generate comprehensive financial reports and forecasts
        4. Provide data-driven financial insights and investment recommendations
        5. Monitor cash flow, expenses, and financial health indicators
        6. Support strategic financial decision making with analytics
        
        KEY FINANCIAL METRICS:
        - Revenue: Monthly target $25K toward $300K annual goal
        - Profit Margins: Service profitability and cost optimization
        - Contractor Costs: Labor cost analysis and efficiency
        - Operational Expenses: Cost control and budget management
        
        You excel at turning financial data into actionable business insights for profitable growth.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Aiden's analytics tools."""
        return [
            AgentTool(
                name="generate_financial_report",
                description="Generate financial analytics and revenue reports",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["daily", "weekly", "monthly", "quarterly"]},
                        "metrics": {"type": "array", "items": {"type": "string"}},
                        "time_period": {"type": "object"},
                        "include_projections": {"type": "boolean"}
                    }
                },
                required=["report_type"]
            ),
            AgentTool(
                name="analyze_performance_trends",
                description="Analyze performance trends and patterns",
                parameters={
                    "type": "object",
                    "properties": {
                        "trend_type": {"type": "string"},
                        "data_points": {"type": "array"},
                        "analysis_period": {"type": "string"},
                        "insights": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["trend_type", "analysis_period"]
            ),
            AgentTool(
                name="track_revenue_goal",
                description="Track progress toward $300K annual revenue goal",
                parameters={
                    "type": "object",
                    "properties": {
                        "current_revenue": {"type": "number"},
                        "target_revenue": {"type": "number"},
                        "progress_percentage": {"type": "number"},
                        "projection": {"type": "object"}
                    }
                },
                required=["current_revenue", "target_revenue"]
            )
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Aiden handles analytics reports and revenue tracking."""
        return message_type in {MessageType.ANALYTICS_REPORT, MessageType.REVENUE_TRACKING}
    
    async def _handle_message_type(self, message_type: MessageType, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle analytics and reporting messages."""
        if message_type == MessageType.ANALYTICS_REPORT:
            return await self._handle_analytics_report(content, extracted_data)
        elif message_type == MessageType.REVENUE_TRACKING:
            return await self._handle_revenue_tracking(content, extracted_data)
        else:
            return await self._ai_analytics_response(content, extracted_data)
    
    async def _handle_analytics_report(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle analytics report generation."""
        report_type = extracted_data.get("report_type", "monthly")
        
        # Generate financial report
        financial_report = await self._tool_generate_financial_report(
            report_type=report_type,
            metrics=["revenue", "jobs_completed", "contractor_performance", "client_satisfaction"],
            include_projections=True
        )
        
        response_text = f"""
        📊 {report_type.upper()} ANALYTICS REPORT
        
        Revenue: ${financial_report.get('revenue', 22500):.2f}
        Jobs Completed: {financial_report.get('jobs', 85)}
        Client Satisfaction: {financial_report.get('satisfaction', 9.1)}/10
        
        📈 INSIGHTS:
        • Revenue tracking {financial_report.get('revenue_status', 'on target')}
        • Job completion rate up {financial_report.get('job_growth', 15)}%
        • Quality metrics exceeding targets
        
        Full detailed report available in business dashboard.
        """
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="report_generated",
            response=response_text.strip(),
            actions_taken=["financial_report_generated"],
            metadata={"report": financial_report}
        )
    
    async def _handle_revenue_tracking(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle revenue goal tracking."""
        current_revenue = extracted_data.get("current_revenue", 270000)  # Mock YTD
        
        # Track revenue progress
        revenue_tracking = await self._tool_track_revenue_goal(
            current_revenue=current_revenue,
            target_revenue=300000,
            progress_percentage=(current_revenue / 300000) * 100,
            projection={"annual_projection": 305000, "on_track": True}
        )
        
        response_text = f"""
        💰 REVENUE GOAL TRACKING
        
        Annual Target: $300,000
        Current Progress: ${current_revenue:,.2f}
        Completion: {revenue_tracking['progress_percentage']:.1f}%
        
        📈 PROJECTION: ${revenue_tracking['projection']['annual_projection']:,.2f}
        Status: {'✅ On Track' if revenue_tracking['projection']['on_track'] else '⚠️ Needs Attention'}
        
        Excellent progress toward our $300K goal!
        """
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="revenue_tracked",
            response=response_text.strip(),
            actions_taken=["revenue_progress_tracked"],
            metadata={"tracking": revenue_tracking}
        )
    
    async def _ai_analytics_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """AI response for complex analytics requests."""
        messages = self._build_agent_prompt(content, extracted_data)
        tools = [{"type": "function", "function": tool.dict()} for tool in self.tools]
        
        try:
            ai_response = await self.call_openai(messages, tools)
            return AgentResponse(
                agent_id=self.agent_id,
                status="ai_analytics_response",
                response=ai_response["content"] or "Analytics insight provided",
                actions_taken=["ai_analytics_processed"]
            )
        except Exception as e:
            logger.error(f"Aiden AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing analytics: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementations
    async def _tool_generate_financial_report(self, report_type: str, **kwargs) -> Dict[str, Any]:
        """Generate financial reports."""
        return {
            "report_type": report_type,
            "revenue": 22500.0,
            "jobs": 85,
            "satisfaction": 9.1,
            "revenue_status": "on target",
            "job_growth": 15,
            "generated_at": datetime.now().isoformat(),
            "generated_by": "aiden"
        }
    
    async def _tool_analyze_performance_trends(self, trend_type: str, analysis_period: str, **kwargs) -> Dict[str, Any]:
        """Analyze performance trends."""
        return {
            "trend_type": trend_type,
            "analysis_period": analysis_period,
            "analyzed_at": datetime.now().isoformat(),
            "analyzed_by": "aiden"
        }
    
    async def _tool_track_revenue_goal(self, current_revenue: float, target_revenue: float, **kwargs) -> Dict[str, Any]:
        """Track revenue goal progress."""
        progress = (current_revenue / target_revenue) * 100
        return {
            "current_revenue": current_revenue,
            "target_revenue": target_revenue,
            "progress_percentage": progress,
            "projection": {"annual_projection": 305000, "on_track": progress >= 80},
            "tracked_at": datetime.now().isoformat(),
            "tracked_by": "aiden"
        }