"""
Maya - Coaching Agent
Performance coaching and skill development specialist
Handles contractor training, performance improvement, and skill enhancement
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_agent import BaseAgent, AgentTool
from ..models.schemas import AgentResponse, BusinessContext
from ..models.types import MessageType, PerformanceLevel, TrainingStatus
from ..tools.discord_tools import DiscordTools
from ..tools.database_tools import DatabaseTools
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MayaCoachingAgent(BaseAgent):
    """
    Maya - Coaching Agent
    
    Responsibilities:
    - Performance analysis and skill development planning
    - Individualized coaching for contractor improvement
    - Training content delivery and progress tracking
    - Quality improvement initiatives and best practices
    - Recognition and motivation programs
    - Problem identification and corrective action plans
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("maya", business_context)
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        self.performance_thresholds = self._set_performance_thresholds()
        
    @property
    def system_prompt(self) -> str:
        """Maya's system prompt with coaching and development focus."""
        return f"""
        You are Maya, the Coaching Agent for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: Performance coach and skill development specialist
        
        CORE RESPONSIBILITIES:
        1. Analyze contractor performance data and identify improvement opportunities
        2. Develop personalized coaching plans for each contractor
        3. Deliver training content and track skill development progress
        4. Implement quality improvement initiatives and best practices
        5. Provide recognition and motivation to maintain high standards
        6. Address performance issues with corrective action plans
        7. Foster a culture of continuous improvement and excellence
        
        CONTRACTOR PROFILES & COACHING FOCUS:
        - Jennifer: South metro, $28/hr, most reliable - Leadership development, mentoring others
        - Olga: East metro, $25/hr, deep cleaning specialist - Efficiency optimization, technique refinement
        - Zhanna: Central metro, $25/hr, recurring expert - Client relationship skills, consistency focus
        - Liuda: North metro, $30/hr, part-time - Skill enhancement for higher rate justification
        
        PERFORMANCE METRICS TO COACH:
        - Checklist compliance: Target 90%+ (currently varies by contractor)
        - Photo submission quality: Target 90%+ submission rate with quality photos
        - On-time arrival: Target 95%+ within 15-minute buffer
        - Client satisfaction: Target 9/10+ average rating
        - Efficiency metrics: Time management and thoroughness balance
        - Communication skills: Client interaction and team coordination
        
        COACHING METHODOLOGY:
        - Strengths-based approach: Build on existing capabilities
        - Data-driven insights: Use performance metrics for targeted coaching
        - Positive reinforcement: Recognize achievements and improvements
        - Skill-building focus: Practical techniques and best practices
        - Regular check-ins: Consistent support and progress monitoring
        - Peer learning: Facilitate knowledge sharing between contractors
        
        TRAINING AREAS:
        - Quality standards and attention to detail
        - Time management and efficiency techniques
        - Client communication and professional presence
        - Photo documentation for quality validation
        - Problem-solving and issue resolution
        - Safety protocols and best practices
        - Technology usage (apps, communication tools)
        
        PERFORMANCE IMPROVEMENT PROCESS:
        1. Performance assessment and gap analysis
        2. Personalized development plan creation
        3. Skill-building activities and training delivery
        4. Progress monitoring and regular check-ins
        5. Feedback integration and plan adjustments
        6. Recognition and celebration of improvements
        
        COMMUNICATION STYLE:
        - Supportive and encouraging
        - Clear and actionable guidance
        - Professional yet approachable
        - Growth-oriented mindset
        - Solution-focused problem solving
        
        ESCALATION TO OTHER AGENTS:
        - Serious performance issues → Dmitri (Escalation Agent)
        - New contractor onboarding → Iris (Onboarding Agent)
        - Scheduling/location concerns → Keith (Check-in Tracker)
        - Recognition and bonuses → Bruno (Bonus Tracker)
        
        You excel at developing contractor potential and maintaining the high-quality standards that define Grime Guardians.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Maya's coaching and development tools."""
        return [
            AgentTool(
                name="analyze_performance",
                description="Analyze contractor performance data and identify coaching opportunities",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "time_period": {"type": "string", "enum": ["weekly", "monthly", "quarterly"]},
                        "metrics": {"type": "array", "items": {"type": "string"}},
                        "benchmarks": {"type": "object"},
                        "identify_gaps": {"type": "boolean"}
                    }
                },
                required=["contractor_id", "time_period"]
            ),
            AgentTool(
                name="create_coaching_plan",
                description="Create personalized coaching and development plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "performance_gaps": {"type": "array", "items": {"type": "string"}},
                        "development_goals": {"type": "array", "items": {"type": "object"}},
                        "coaching_activities": {"type": "array", "items": {"type": "object"}},
                        "timeline": {"type": "object"},
                        "success_metrics": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["contractor_id", "development_goals"]
            ),
            AgentTool(
                name="deliver_training",
                description="Deliver training content and track progress",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "training_topic": {"type": "string"},
                        "delivery_method": {"type": "string", "enum": ["one_on_one", "group_session", "digital_content", "shadowing"]},
                        "content": {"type": "string"},
                        "duration_minutes": {"type": "integer"},
                        "competency_check": {"type": "boolean"}
                    }
                },
                required=["contractor_id", "training_topic", "delivery_method"]
            ),
            AgentTool(
                name="provide_feedback",
                description="Provide specific feedback and recognition",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "feedback_type": {"type": "string", "enum": ["positive_reinforcement", "corrective_guidance", "skill_improvement", "recognition"]},
                        "specific_area": {"type": "string"},
                        "feedback_content": {"type": "string"},
                        "action_items": {"type": "array", "items": {"type": "string"}},
                        "follow_up_needed": {"type": "boolean"}
                    }
                },
                required=["contractor_id", "feedback_type", "feedback_content"]
            ),
            AgentTool(
                name="track_improvement",
                description="Track skill development and improvement progress",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "skill_area": {"type": "string"},
                        "baseline_score": {"type": "number"},
                        "current_score": {"type": "number"},
                        "improvement_percentage": {"type": "number"},
                        "milestone_achieved": {"type": "boolean"}
                    }
                },
                required=["contractor_id", "skill_area", "current_score"]
            ),
            AgentTool(
                name="facilitate_peer_learning",
                description="Facilitate knowledge sharing between contractors",
                parameters={
                    "type": "object",
                    "properties": {
                        "learning_topic": {"type": "string"},
                        "mentor_contractor": {"type": "string"},
                        "mentee_contractors": {"type": "array", "items": {"type": "string"}},
                        "session_format": {"type": "string"},
                        "key_takeaways": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["learning_topic", "mentor_contractor"]
            ),
            AgentTool(
                name="generate_improvement_report",
                description="Generate performance improvement and coaching reports",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["individual_progress", "team_performance", "coaching_effectiveness", "skill_gaps"]},
                        "time_period": {"type": "string"},
                        "contractors": {"type": "array", "items": {"type": "string"}},
                        "include_recommendations": {"type": "boolean"}
                    }
                },
                required=["report_type", "time_period"]
            }
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Maya handles performance feedback, coaching requests, and skill development."""
        coaching_types = {
            MessageType.PERFORMANCE_FEEDBACK,
            MessageType.COACHING_REQUEST,
            MessageType.SKILL_DEVELOPMENT,
            MessageType.QUALITY_IMPROVEMENT
        }
        return message_type in coaching_types
    
    async def _handle_message_type(
        self, 
        message_type: MessageType, 
        content: str, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Handle coaching and development messages."""
        
        if message_type == MessageType.PERFORMANCE_FEEDBACK:
            return await self._handle_performance_feedback(content, extracted_data)
        elif message_type == MessageType.COACHING_REQUEST:
            return await self._handle_coaching_request(content, extracted_data)
        elif message_type == MessageType.SKILL_DEVELOPMENT:
            return await self._handle_skill_development(content, extracted_data)
        elif message_type == MessageType.QUALITY_IMPROVEMENT:
            return await self._handle_quality_improvement(content, extracted_data)
        else:
            # Use AI for complex coaching decisions
            return await self._ai_coaching_response(content, extracted_data)
    
    async def _handle_performance_feedback(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle performance feedback and coaching opportunities."""
        contractor_id = extracted_data.get("contractor_id", "unknown")
        performance_area = extracted_data.get("performance_area", "general")
        feedback_type = extracted_data.get("feedback_type", "improvement")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Analyze performance data
            performance_analysis = await self._tool_analyze_performance(
                contractor_id=contractor_id,
                time_period="monthly",
                metrics=["checklist_compliance", "photo_quality", "on_time_percentage", "client_satisfaction"],
                identify_gaps=True
            )
            actions_taken.append("performance_analyzed")
            
            # Determine coaching approach based on performance
            if performance_analysis.get("overall_score", 85) >= 90:
                # High performer - focus on recognition and leadership development
                feedback_result = await self._tool_provide_feedback(
                    contractor_id=contractor_id,
                    feedback_type="recognition",
                    specific_area=performance_area,
                    feedback_content=f"Excellent performance in {performance_area}! You're setting a great example for the team.",
                    action_items=["Consider mentoring newer contractors", "Explore leadership opportunities"]
                )
                next_steps.append("Explore leadership development opportunities")
                
            elif performance_analysis.get("overall_score", 85) >= 75:
                # Good performer - focus on skill enhancement
                feedback_result = await self._tool_provide_feedback(
                    contractor_id=contractor_id,
                    feedback_type="skill_improvement",
                    specific_area=performance_area,
                    feedback_content=f"Good work in {performance_area}. Let's work on taking it to the next level.",
                    action_items=[f"Training session on {performance_area} optimization"],
                    follow_up_needed=True
                )
                next_steps.append("Schedule skill enhancement training")
                
            else:
                # Needs improvement - focus on corrective guidance
                feedback_result = await self._tool_provide_feedback(
                    contractor_id=contractor_id,
                    feedback_type="corrective_guidance",
                    specific_area=performance_area,
                    feedback_content=f"I've noticed some opportunities for improvement in {performance_area}. Let's work together to get you back on track.",
                    action_items=[f"Focused coaching session on {performance_area}", "Weekly check-ins for progress monitoring"],
                    follow_up_needed=True
                )
                next_steps.append("Create improvement plan with specific goals")
            
            actions_taken.append("feedback_provided")
            
            # Create coaching plan if needed
            if performance_analysis.get("overall_score", 85) < 85:
                coaching_plan = await self._tool_create_coaching_plan(
                    contractor_id=contractor_id,
                    performance_gaps=performance_analysis.get("improvement_areas", []),
                    development_goals=[{
                        "area": performance_area,
                        "target_score": 90,
                        "timeline": "30_days"
                    }]
                )
                actions_taken.append("coaching_plan_created")
                next_steps.append("Implement coaching plan with regular check-ins")
            
            response_text = f"""
            📊 PERFORMANCE COACHING for {contractor_id.title()}
            
            Current Performance: {performance_analysis.get('overall_score', 85)}%
            Focus Area: {performance_area.replace('_', ' ').title()}
            Coaching Approach: {feedback_result.get('feedback_type', '').replace('_', ' ').title()}
            
            Key Strengths: {', '.join(performance_analysis.get('strengths', ['Reliability', 'Quality work']))}
            Development Areas: {', '.join(performance_analysis.get('improvement_areas', ['None identified']))}
            
            Next Steps:
            {chr(10).join(f"• {step}" for step in next_steps)}
            """
            
            # Send encouraging message via Discord
            if self.discord_tools:
                await self.discord_tools.send_general_message(
                    f"💪 Coaching session completed for {contractor_id.title()} - focused on {performance_area}"
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="coaching_provided",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                metadata={"performance_analysis": performance_analysis, "feedback": feedback_result}
            )
            
        except Exception as e:
            logger.error(f"Maya performance feedback error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing performance feedback: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_coaching_request(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle specific coaching requests."""
        contractor_id = extracted_data.get("contractor_id", "unknown")
        coaching_topic = extracted_data.get("coaching_topic", "general_skills")
        urgency = extracted_data.get("urgency", "normal")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Determine training approach based on topic
            training_methods = {
                "photo_quality": "one_on_one",
                "time_management": "digital_content",
                "client_communication": "group_session",
                "cleaning_techniques": "shadowing",
                "checklist_compliance": "one_on_one"
            }
            
            delivery_method = training_methods.get(coaching_topic, "one_on_one")
            
            # Deliver targeted training
            training_result = await self._tool_deliver_training(
                contractor_id=contractor_id,
                training_topic=coaching_topic,
                delivery_method=delivery_method,
                content=self._get_training_content(coaching_topic),
                duration_minutes=30 if delivery_method == "one_on_one" else 60,
                competency_check=True
            )
            actions_taken.append("training_delivered")
            
            # Track improvement baseline
            improvement_tracking = await self._tool_track_improvement(
                contractor_id=contractor_id,
                skill_area=coaching_topic,
                current_score=self._get_baseline_score(contractor_id, coaching_topic),
                baseline_score=self._get_baseline_score(contractor_id, coaching_topic)
            )
            actions_taken.append("improvement_tracking_initiated")
            
            response_text = f"""
            🎯 COACHING SESSION COMPLETED for {contractor_id.title()}
            
            Topic: {coaching_topic.replace('_', ' ').title()}
            Method: {delivery_method.replace('_', ' ').title()}
            Duration: {training_result.get('duration_minutes', 30)} minutes
            
            Key Learning Points:
            {self._get_training_summary(coaching_topic)}
            
            Follow-up: Progress check scheduled in 1 week
            """
            
            next_steps.extend([
                "Monitor performance in coached area",
                "Schedule follow-up session if needed",
                "Celebrate improvements when achieved"
            ])
            
            # Handle urgent requests
            if urgency == "high":
                next_steps.append("Priority follow-up within 24 hours")
                if self.discord_tools:
                    await self.discord_tools.send_urgent_alert(
                        f"🎯 Urgent coaching completed: {contractor_id.title()} - {coaching_topic}"
                    )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="coaching_completed",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                metadata={"training": training_result, "tracking": improvement_tracking}
            )
            
        except Exception as e:
            logger.error(f"Maya coaching request error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing coaching request: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_skill_development(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle skill development initiatives."""
        development_area = extracted_data.get("development_area", "general")
        contractors_involved = extracted_data.get("contractors", ["all"])
        
        actions_taken = []
        
        try:
            # Facilitate peer learning session
            if len(contractors_involved) > 1 or "all" in contractors_involved:
                peer_learning = await self._tool_facilitate_peer_learning(
                    learning_topic=development_area,
                    mentor_contractor="jennifer",  # Most experienced contractor
                    mentee_contractors=["olga", "zhanna", "liuda"] if "all" in contractors_involved else contractors_involved
                )
                actions_taken.append("peer_learning_facilitated")
                
                response_text = f"""
                🤝 PEER LEARNING SESSION COMPLETED
                
                Topic: {development_area.replace('_', ' ').title()}
                Mentor: Jennifer (sharing expertise)
                Participants: {', '.join(peer_learning.get('mentee_contractors', []))}
                
                Key Takeaways:
                {chr(10).join(f"• {takeaway}" for takeaway in peer_learning.get('key_takeaways', ['Knowledge sharing completed']))}
                
                Team skill level improved through collaborative learning!
                """
            else:
                # Individual skill development
                contractor_id = contractors_involved[0]
                training_result = await self._tool_deliver_training(
                    contractor_id=contractor_id,
                    training_topic=development_area,
                    delivery_method="one_on_one",
                    content=self._get_training_content(development_area)
                )
                actions_taken.append("individual_training_delivered")
                
                response_text = f"Individual skill development completed for {contractor_id.title()} in {development_area}"
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="skill_development_completed",
                response=response_text,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Maya skill development error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing skill development: {str(e)}",
                requires_escalation=True
            )
    
    async def _ai_coaching_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Use AI for complex coaching decisions."""
        messages = self._build_agent_prompt(content, extracted_data)
        
        # Add coaching context
        coaching_context = f"""
        COACHING CONTEXT:
        - Performance thresholds: {self.performance_thresholds}
        - Focus on strengths-based development
        - Positive reinforcement and growth mindset
        - Data-driven coaching with specific metrics
        """
        messages.append({"role": "system", "content": coaching_context})
        
        tools = [{"type": "function", "function": tool.dict()} for tool in self.tools]
        
        try:
            ai_response = await self.call_openai(messages, tools)
            
            actions_taken = []
            if ai_response.get("tool_calls"):
                for tool_call in ai_response["tool_calls"]:
                    tool_name = tool_call.function.name
                    actions_taken.append(f"executed_{tool_name}")
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="ai_coaching_response",
                response=ai_response["content"] or "Coaching decision processed",
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Maya AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing coaching request: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementation methods
    async def _tool_analyze_performance(
        self,
        contractor_id: str,
        time_period: str,
        metrics: List[str] = None,
        benchmarks: Dict[str, float] = None,
        identify_gaps: bool = True
    ) -> Dict[str, Any]:
        """Analyze contractor performance data."""
        
        if metrics is None:
            metrics = ["checklist_compliance", "photo_quality", "on_time_percentage", "client_satisfaction"]
        
        if benchmarks is None:
            benchmarks = self.performance_thresholds
        
        # Mock performance data - in production, query actual database
        mock_performance = {
            "jennifer": {
                "checklist_compliance": 96.0,
                "photo_quality": 92.0,
                "on_time_percentage": 98.0,
                "client_satisfaction": 9.3,
                "efficiency_score": 95.0
            },
            "olga": {
                "checklist_compliance": 88.0,
                "photo_quality": 95.0,
                "on_time_percentage": 94.0,
                "client_satisfaction": 9.0,
                "efficiency_score": 87.0
            },
            "zhanna": {
                "checklist_compliance": 94.0,
                "photo_quality": 89.0,
                "on_time_percentage": 97.0,
                "client_satisfaction": 9.2,
                "efficiency_score": 91.0
            },
            "liuda": {
                "checklist_compliance": 85.0,
                "photo_quality": 87.0,
                "on_time_percentage": 92.0,
                "client_satisfaction": 8.8,
                "efficiency_score": 84.0
            }
        }
        
        contractor_scores = mock_performance.get(contractor_id, {})
        
        # Calculate overall score
        metric_scores = [contractor_scores.get(metric, 80) for metric in metrics]
        overall_score = sum(metric_scores) / len(metric_scores) if metric_scores else 80
        
        # Identify strengths and improvement areas
        strengths = []
        improvement_areas = []
        
        for metric in metrics:
            score = contractor_scores.get(metric, 80)
            threshold = benchmarks.get(metric, 85)
            
            if score >= threshold + 5:  # Above threshold
                strengths.append(metric)
            elif score < threshold:  # Below threshold
                improvement_areas.append(metric)
        
        analysis_result = {
            "contractor_id": contractor_id,
            "time_period": time_period,
            "overall_score": overall_score,
            "metric_scores": {metric: contractor_scores.get(metric, 80) for metric in metrics},
            "benchmarks": benchmarks,
            "strengths": strengths,
            "improvement_areas": improvement_areas,
            "performance_level": self._categorize_performance(overall_score),
            "analyzed_by": "maya",
            "analyzed_at": datetime.now().isoformat()
        }
        
        return analysis_result
    
    async def _tool_create_coaching_plan(
        self,
        contractor_id: str,
        performance_gaps: List[str] = None,
        development_goals: List[Dict] = None,
        coaching_activities: List[Dict] = None,
        timeline: Dict[str, Any] = None,
        success_metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Create personalized coaching plan."""
        
        if performance_gaps is None:
            performance_gaps = []
        if development_goals is None:
            development_goals = []
        if coaching_activities is None:
            coaching_activities = []
        if timeline is None:
            timeline = {"duration_weeks": 4, "check_ins": "weekly"}
        if success_metrics is None:
            success_metrics = ["improvement_percentage", "goal_achievement"]
        
        # Generate coaching activities based on gaps
        for gap in performance_gaps:
            coaching_activities.append({
                "activity": f"Focused training on {gap}",
                "method": "one_on_one",
                "duration": "30 minutes",
                "frequency": "weekly"
            })
        
        coaching_plan = {
            "plan_id": f"PLAN{datetime.now().strftime('%Y%m%d%H%M')}{contractor_id[-4:]}",
            "contractor_id": contractor_id,
            "performance_gaps": performance_gaps,
            "development_goals": development_goals,
            "coaching_activities": coaching_activities,
            "timeline": timeline,
            "success_metrics": success_metrics,
            "created_by": "maya",
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Store plan in database if available
        if self.database_tools:
            await self.database_tools.create_coaching_plan(coaching_plan)
        
        return coaching_plan
    
    async def _tool_deliver_training(
        self,
        contractor_id: str,
        training_topic: str,
        delivery_method: str,
        content: str = "",
        duration_minutes: int = 30,
        competency_check: bool = False
    ) -> Dict[str, Any]:
        """Deliver training content and track progress."""
        
        if not content:
            content = self._get_training_content(training_topic)
        
        training_record = {
            "training_id": f"TRAIN{datetime.now().strftime('%Y%m%d%H%M')}{contractor_id[-4:]}",
            "contractor_id": contractor_id,
            "training_topic": training_topic,
            "delivery_method": delivery_method,
            "content_summary": content[:200] + "..." if len(content) > 200 else content,
            "duration_minutes": duration_minutes,
            "competency_check": competency_check,
            "completion_status": "completed",
            "delivered_by": "maya",
            "delivered_at": datetime.now().isoformat()
        }
        
        # Log training completion
        logger.info(f"Training delivered: {training_topic} to {contractor_id} via {delivery_method}")
        
        return training_record
    
    async def _tool_provide_feedback(
        self,
        contractor_id: str,
        feedback_type: str,
        feedback_content: str,
        specific_area: str = "",
        action_items: List[str] = None,
        follow_up_needed: bool = False
    ) -> Dict[str, Any]:
        """Provide specific feedback and recognition."""
        
        if action_items is None:
            action_items = []
        
        feedback_record = {
            "feedback_id": f"FB{datetime.now().strftime('%Y%m%d%H%M')}{contractor_id[-4:]}",
            "contractor_id": contractor_id,
            "feedback_type": feedback_type,
            "specific_area": specific_area,
            "feedback_content": feedback_content,
            "action_items": action_items,
            "follow_up_needed": follow_up_needed,
            "follow_up_date": (datetime.now() + timedelta(weeks=1)).isoformat() if follow_up_needed else None,
            "provided_by": "maya",
            "provided_at": datetime.now().isoformat()
        }
        
        # Send positive feedback via Discord if it's recognition
        if feedback_type == "recognition" and self.discord_tools:
            await self.discord_tools.send_general_message(
                f"🌟 Shoutout to {contractor_id.title()}: {feedback_content[:100]}!"
            )
        
        return feedback_record
    
    async def _tool_track_improvement(
        self,
        contractor_id: str,
        skill_area: str,
        current_score: float,
        baseline_score: float = None,
        improvement_percentage: float = None,
        milestone_achieved: bool = False
    ) -> Dict[str, Any]:
        """Track skill development progress."""
        
        if baseline_score is None:
            baseline_score = current_score
        
        if improvement_percentage is None:
            improvement_percentage = ((current_score - baseline_score) / baseline_score * 100) if baseline_score > 0 else 0
        
        improvement_record = {
            "tracking_id": f"IMP{datetime.now().strftime('%Y%m%d%H%M')}{contractor_id[-4:]}",
            "contractor_id": contractor_id,
            "skill_area": skill_area,
            "baseline_score": baseline_score,
            "current_score": current_score,
            "improvement_percentage": improvement_percentage,
            "milestone_achieved": milestone_achieved,
            "trend": "improving" if current_score > baseline_score else "stable",
            "tracked_by": "maya",
            "tracked_at": datetime.now().isoformat()
        }
        
        return improvement_record
    
    async def _tool_facilitate_peer_learning(
        self,
        learning_topic: str,
        mentor_contractor: str,
        mentee_contractors: List[str] = None,
        session_format: str = "group_discussion",
        key_takeaways: List[str] = None
    ) -> Dict[str, Any]:
        """Facilitate knowledge sharing between contractors."""
        
        if mentee_contractors is None:
            mentee_contractors = []
        if key_takeaways is None:
            key_takeaways = [
                f"Best practices for {learning_topic}",
                "Practical tips and techniques",
                "Common challenges and solutions"
            ]
        
        peer_learning_record = {
            "session_id": f"PEER{datetime.now().strftime('%Y%m%d%H%M')}",
            "learning_topic": learning_topic,
            "mentor_contractor": mentor_contractor,
            "mentee_contractors": mentee_contractors,
            "session_format": session_format,
            "key_takeaways": key_takeaways,
            "participants_count": len(mentee_contractors) + 1,
            "facilitated_by": "maya",
            "session_date": datetime.now().isoformat()
        }
        
        return peer_learning_record
    
    def _set_performance_thresholds(self) -> Dict[str, float]:
        """Set performance threshold values for coaching."""
        return {
            "checklist_compliance": 90.0,
            "photo_quality": 90.0,
            "on_time_percentage": 95.0,
            "client_satisfaction": 9.0,
            "efficiency_score": 85.0
        }
    
    def _categorize_performance(self, overall_score: float) -> str:
        """Categorize performance level."""
        if overall_score >= 95:
            return "exceptional"
        elif overall_score >= 90:
            return "excellent"
        elif overall_score >= 85:
            return "good"
        elif overall_score >= 75:
            return "needs_improvement"
        else:
            return "requires_intervention"
    
    def _get_training_content(self, topic: str) -> str:
        """Get training content for specific topics."""
        content_library = {
            "photo_quality": "Focus on good lighting, multiple angles, clear before/after shots. Document kitchen, bathrooms, entry area, and impacted rooms.",
            "time_management": "Use the checklist efficiently, prioritize high-impact areas, maintain steady pace without rushing quality.",
            "client_communication": "Professional greeting, clear communication about process, proactive updates on timing and any issues.",
            "cleaning_techniques": "Work top to bottom, left to right, use proper products for each surface, attention to detail in corners and edges.",
            "checklist_compliance": "Follow every item systematically, document completion, ask for clarification if needed, never skip steps."
        }
        return content_library.get(topic, "Comprehensive training content will be provided during the session.")
    
    def _get_training_summary(self, topic: str) -> str:
        """Get training summary for display."""
        summaries = {
            "photo_quality": "• Proper lighting and angles\n• Multiple shots per room\n• Clear before/after documentation",
            "time_management": "• Systematic checklist approach\n• Prioritization techniques\n• Quality-speed balance",
            "client_communication": "• Professional presentation\n• Proactive updates\n• Issue resolution",
            "cleaning_techniques": "• Proper product usage\n• Systematic approach\n• Detail orientation",
            "checklist_compliance": "• Step-by-step execution\n• Documentation importance\n• Quality standards"
        }
        return summaries.get(topic, "• Key concepts covered\n• Practical application\n• Follow-up actions")
    
    def _get_baseline_score(self, contractor_id: str, skill_area: str) -> float:
        """Get baseline score for contractor in specific skill area."""
        # Mock baseline data - in production, query actual database
        baselines = {
            "jennifer": {"photo_quality": 92, "time_management": 95, "client_communication": 96},
            "olga": {"photo_quality": 95, "time_management": 87, "client_communication": 88},
            "zhanna": {"photo_quality": 89, "time_management": 91, "client_communication": 94},
            "liuda": {"photo_quality": 87, "time_management": 84, "client_communication": 86}
        }
        return baselines.get(contractor_id, {}).get(skill_area, 85.0)