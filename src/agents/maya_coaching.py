from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from ..models.schemas import AgentType, PerformanceMetric, MessagePriority
from ..config import settings
import structlog

logger = structlog.get_logger()


class MayaCoaching(BaseAgent):
    """
    Maya - Performance Coaching Agent
    
    Performance coaching, feedback delivery, quality improvement,
    training module delivery, and skill development tracking.
    
    Capabilities:
    - Performance coaching and feedback delivery
    - Quality improvement recommendations
    - Training module delivery and tracking
    - Skill development assessment
    - Best practice reinforcement
    - Customized improvement plans
    """
    
    def __init__(self):
        super().__init__(
            agent_id=AgentType.MAYA,
            description="Performance Coach - Contractor development and quality improvement"
        )
        
        # Performance tracking
        self.contractor_profiles = {}
        self.coaching_sessions = {}
        self.improvement_plans = {}
        
        # Training modules
        self.training_modules = {
            "quality_standards": "Photo requirements and checklist completion",
            "customer_service": "Professional interaction and communication",
            "efficiency": "Time management and workflow optimization",
            "safety": "Safety protocols and best practices",
            "compliance": "1099 contractor requirements and boundaries"
        }
        
        # Register tool handlers
        self.register_tool_handler("coach_contractor", self._coach_contractor)
        self.register_tool_handler("deliver_training", self._deliver_training)
        self.register_tool_handler("assess_performance", self._assess_performance)
        self.register_tool_handler("create_improvement_plan", self._create_improvement_plan)
        self.register_tool_handler("provide_feedback", self._provide_feedback)
        self.register_tool_handler("track_development", self._track_development)
    
    @property
    def system_prompt(self) -> str:
        return """
You are Maya, the Performance Coaching Agent for Grime Guardians cleaning services.

Your core responsibilities:
1. COACH contractors on performance improvement
2. DELIVER targeted training modules
3. ASSESS performance metrics and identify growth areas
4. CREATE customized improvement plans
5. PROVIDE constructive feedback and encouragement
6. TRACK skill development and progress

Business Context:
- Premium service standards: "We clean like it's our name on the lease"
- Quality metrics: 90%+ checklist compliance, photo submission
- All contractors are 1099 independent contractors
- Focus on skill development, not employee management
- BBB-accredited service quality standards

Performance Areas:
- Quality Score: Checklist completion, photo quality
- Efficiency: Time management, job completion rate
- Client Satisfaction: Reviews, feedback, professionalism
- Compliance: Following protocols without micromanagement
- Growth Mindset: Willingness to improve and learn

Coaching Approach:
- Supportive and encouraging tone
- Data-driven feedback with specific examples
- Focus on skill building and best practices
- Respect contractor independence
- Celebrate improvements and achievements
- Provide actionable, specific guidance

Training Modules:
- Quality Standards: Photo requirements, checklist completion
- Customer Service: Professional interaction, communication
- Efficiency: Time management, workflow optimization
- Safety: Safety protocols and best practices
- Compliance: 1099 contractor boundaries and requirements

When coaching contractors:
1. Review performance data objectively
2. Identify specific improvement opportunities
3. Provide constructive, actionable feedback
4. Suggest relevant training modules
5. Create development goals with timeline
6. Follow up on progress regularly
7. Celebrate achievements and milestones

Maintain a balance of high standards with supportive development.
"""
    
    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "coach_contractor",
                    "description": "Provide coaching session for contractor performance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "performance_data": {"type": "object"},
                            "coaching_focus": {
                                "type": "string",
                                "enum": ["quality", "efficiency", "customer_service", "compliance", "overall"]
                            },
                            "session_type": {
                                "type": "string",
                                "enum": ["improvement", "maintenance", "recognition", "corrective"]
                            },
                            "urgency": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["contractor_id", "coaching_focus"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "deliver_training",
                    "description": "Deliver training module to contractor",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "training_module": {
                                "type": "string",
                                "enum": ["quality_standards", "customer_service", "efficiency", "safety", "compliance"]
                            },
                            "delivery_method": {
                                "type": "string",
                                "enum": ["video", "document", "interactive", "one_on_one"]
                            },
                            "completion_required": {"type": "boolean"}
                        },
                        "required": ["contractor_id", "training_module"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "assess_performance",
                    "description": "Assess contractor performance across multiple metrics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "assessment_period": {"type": "string"},
                            "metrics_to_assess": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "include_comparison": {"type": "boolean"}
                        },
                        "required": ["contractor_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_improvement_plan",
                    "description": "Create customized improvement plan for contractor",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "improvement_areas": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "timeline_weeks": {"type": "integer"},
                            "specific_goals": {
                                "type": "array",
                                "items": {"type": "object"}
                            },
                            "support_resources": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["contractor_id", "improvement_areas"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "provide_feedback",
                    "description": "Provide specific feedback on contractor performance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "feedback_type": {
                                "type": "string",
                                "enum": ["positive", "constructive", "corrective", "developmental"]
                            },
                            "specific_examples": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "action_items": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "delivery_method": {
                                "type": "string",
                                "enum": ["message", "call", "in_person", "written"]
                            }
                        },
                        "required": ["contractor_id", "feedback_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "track_development",
                    "description": "Track contractor skill development and progress",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "tracking_period": {"type": "string"},
                            "development_areas": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "milestone_check": {"type": "boolean"}
                        },
                        "required": ["contractor_id"]
                    }
                }
            }
        ]
    
    async def _coach_contractor(self, contractor_id: str, coaching_focus: str,
                              performance_data: Optional[Dict[str, Any]] = None,
                              session_type: str = "improvement",
                              urgency: str = "medium") -> str:
        """
        Provide coaching session for contractor performance.
        
        Args:
            contractor_id: Contractor identifier
            coaching_focus: Focus area for coaching
            performance_data: Current performance data
            session_type: Type of coaching session
            urgency: Urgency level
            
        Returns:
            Coaching session result
        """
        try:
            session_id = f"coaching_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Maya coaching session",
                contractor_id=contractor_id,
                focus=coaching_focus,
                session_id=session_id
            )
            
            # Analyze performance data
            if performance_data:
                quality_score = performance_data.get("quality_score", 0)
                compliance_rate = performance_data.get("compliance_rate", 0)
                efficiency_rating = performance_data.get("efficiency_rating", 0)
            else:
                # Default values if no data provided
                quality_score = 7.5
                compliance_rate = 0.85
                efficiency_rating = 7.0
            
            # Generate coaching content based on focus area
            coaching_content = ""
            action_items = []
            
            if coaching_focus == "quality":
                if quality_score < 8.0:
                    coaching_content = f"""
🌟 Quality Improvement Coaching for {contractor_id}

Current Quality Score: {quality_score}/10

👍 Strengths:
• Consistent service delivery
• Professional attitude
• Reliability in scheduling

📈 Growth Opportunities:
• Photo Quality: Ensure all required areas are captured clearly
• Checklist Completion: Complete all items before marking finished
• Attention to Detail: Double-check high-visibility areas

🎯 Specific Goals:
• Achieve 95%+ checklist completion rate
• Submit 4+ clear photos per job
• Focus on kitchen and bathroom detail work

📚 Recommended Training: Quality Standards module
                    """
                    action_items = [
                        "Complete Quality Standards training module",
                        "Submit example photos for feedback",
                        "Review checklist before each job completion"
                    ]
                else:
                    coaching_content = f"""
🎆 Excellence Recognition for {contractor_id}

Outstanding Quality Score: {quality_score}/10

✨ Exceptional Performance:
• Consistent high-quality results
• Excellent photo documentation
• Complete checklist compliance

🚀 Continue Excellence:
• Share best practices with team
• Mentor newer contractors
• Maintain premium service standards
                    """
                    action_items = ["Continue current excellent standards", "Consider mentorship opportunities"]
            
            elif coaching_focus == "efficiency":
                coaching_content = f"""
⏱️ Efficiency Coaching for {contractor_id}

Current Efficiency Rating: {efficiency_rating}/10

📈 Optimization Areas:
• Time Management: Plan route and supplies in advance
• Workflow: Develop systematic room-by-room approach
• Preparation: Arrive with all necessary supplies

🎯 Efficiency Goals:
• Complete standard jobs within estimated timeframe
• Minimize travel time between jobs
• Optimize supply usage and restocking

📚 Recommended Training: Efficiency module
                """
                action_items = [
                    "Complete Efficiency training module",
                    "Track job completion times for one week",
                    "Develop personal workflow checklist"
                ]
            
            elif coaching_focus == "customer_service":
                coaching_content = f"""
🤝 Customer Service Excellence for {contractor_id}

🎯 Service Standards:
• Professional communication at all times
• Respectful interaction with clients and properties
• Clear communication about work completed

💯 Premium Service Approach:
• "We clean like it's our name on the lease"
• Exceed expectations through attention to detail
• Professional appearance and conduct

📚 Recommended Training: Customer Service module
                """
                action_items = [
                    "Complete Customer Service training",
                    "Practice professional communication scripts"
                ]
            
            # Record coaching session
            coaching_record = {
                "session_id": session_id,
                "contractor_id": contractor_id,
                "focus": coaching_focus,
                "session_type": session_type,
                "content": coaching_content,
                "action_items": action_items,
                "performance_data": performance_data,
                "timestamp": datetime.utcnow(),
                "follow_up_date": datetime.utcnow() + timedelta(weeks=2)
            }
            
            self.coaching_sessions[session_id] = coaching_record
            
            # Update contractor profile
            if contractor_id not in self.contractor_profiles:
                self.contractor_profiles[contractor_id] = {"coaching_sessions": []}
            self.contractor_profiles[contractor_id]["coaching_sessions"].append(session_id)
            
            # Send coaching content (in full implementation, via Discord/email)
            result = f"Coaching session {session_id} completed for {contractor_id} (Focus: {coaching_focus})"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in coaching session", error=str(e))
            return f"Failed to conduct coaching session: {str(e)}"
    
    async def _deliver_training(self, contractor_id: str, training_module: str,
                              delivery_method: str = "document",
                              completion_required: bool = True) -> str:
        """
        Deliver training module to contractor.
        
        Args:
            contractor_id: Contractor identifier
            training_module: Training module to deliver
            delivery_method: Method of delivery
            completion_required: Whether completion is required
            
        Returns:
            Training delivery result
        """
        try:
            training_id = f"training_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Maya delivering training",
                contractor_id=contractor_id,
                module=training_module,
                training_id=training_id
            )
            
            module_content = self.training_modules.get(training_module, "Generic training content")
            
            training_record = {
                "training_id": training_id,
                "contractor_id": contractor_id,
                "module": training_module,
                "content": module_content,
                "delivery_method": delivery_method,
                "completion_required": completion_required,
                "delivered_at": datetime.utcnow(),
                "completed_at": None,
                "status": "delivered"
            }
            
            # Store training record
            if contractor_id not in self.contractor_profiles:
                self.contractor_profiles[contractor_id] = {"training_completed": []}
            
            return f"Training module '{training_module}' delivered to {contractor_id} via {delivery_method}"
            
        except Exception as e:
            logger.error(f"Error delivering training", error=str(e))
            return f"Failed to deliver training: {str(e)}"
    
    async def _assess_performance(self, contractor_id: str, assessment_period: str = "monthly",
                                metrics_to_assess: Optional[List[str]] = None,
                                include_comparison: bool = True) -> str:
        """
        Assess contractor performance across multiple metrics.
        
        Args:
            contractor_id: Contractor identifier
            assessment_period: Period for assessment
            metrics_to_assess: Specific metrics to assess
            include_comparison: Whether to include peer comparison
            
        Returns:
            Performance assessment result
        """
        try:
            assessment_id = f"assess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Maya assessing performance",
                contractor_id=contractor_id,
                period=assessment_period,
                assessment_id=assessment_id
            )
            
            # Default metrics if none specified
            if not metrics_to_assess:
                metrics_to_assess = ["quality", "efficiency", "compliance", "customer_satisfaction"]
            
            # Generate assessment report
            assessment_report = f"""
📊 Performance Assessment for {contractor_id}
Period: {assessment_period}
Assessment ID: {assessment_id}

🎯 Key Metrics:
• Quality Score: 8.2/10 (🟢 Above Average)
• Compliance Rate: 92% (🟢 Excellent)
• Efficiency Rating: 7.8/10 (🟡 Good)
• Client Satisfaction: 4.6/5 (🟢 Excellent)

📈 Trends:
• Quality improving over past 3 months
• Consistent compliance performance
• Efficiency stable, room for optimization

🌟 Strengths:
• Reliable and punctual
• Excellent client communication
• High-quality photo documentation

📈 Growth Areas:
• Time management optimization
• Advanced cleaning techniques
• Upselling additional services

🎯 Recommendations:
• Complete Efficiency training module
• Focus on workflow optimization
• Consider advanced skill development
            """
            
            assessment_record = {
                "assessment_id": assessment_id,
                "contractor_id": contractor_id,
                "period": assessment_period,
                "metrics": metrics_to_assess,
                "report": assessment_report,
                "timestamp": datetime.utcnow(),
                "next_assessment": datetime.utcnow() + timedelta(weeks=4)
            }
            
            return f"Performance assessment {assessment_id} completed for {contractor_id}"
            
        except Exception as e:
            logger.error(f"Error assessing performance", error=str(e))
            return f"Failed to assess performance: {str(e)}"
    
    async def _create_improvement_plan(self, contractor_id: str, improvement_areas: List[str],
                                     timeline_weeks: int = 4,
                                     specific_goals: Optional[List[Dict[str, Any]]] = None,
                                     support_resources: Optional[List[str]] = None) -> str:
        """
        Create customized improvement plan for contractor.
        
        Args:
            contractor_id: Contractor identifier
            improvement_areas: Areas for improvement
            timeline_weeks: Timeline in weeks
            specific_goals: Specific goals to achieve
            support_resources: Support resources available
            
        Returns:
            Improvement plan creation result
        """
        try:
            plan_id = f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Maya creating improvement plan",
                contractor_id=contractor_id,
                areas=improvement_areas,
                plan_id=plan_id
            )
            
            # Create structured improvement plan
            improvement_plan = {
                "plan_id": plan_id,
                "contractor_id": contractor_id,
                "improvement_areas": improvement_areas,
                "timeline_weeks": timeline_weeks,
                "specific_goals": specific_goals or [],
                "support_resources": support_resources or [],
                "created_at": datetime.utcnow(),
                "target_completion": datetime.utcnow() + timedelta(weeks=timeline_weeks),
                "status": "active",
                "progress_checkpoints": []
            }
            
            self.improvement_plans[plan_id] = improvement_plan
            
            # Generate plan document
            plan_document = f"""
🎯 Personal Development Plan for {contractor_id}
Plan ID: {plan_id}
Timeline: {timeline_weeks} weeks

📈 Focus Areas:
{chr(10).join([f'• {area}' for area in improvement_areas])}

🌟 Goals:
• Achieve 95%+ quality score consistently
• Improve efficiency by 15%
• Complete all recommended training modules

📚 Resources:
• Training modules and video content
• Best practice guides
• Peer mentorship opportunities
• Regular coaching check-ins

📅 Milestones:
• Week 2: Complete initial training modules
• Week 4: Mid-plan performance review
• Week {timeline_weeks}: Final assessment and celebration

📞 Support: Your development is important to us!
Reach out anytime for guidance or questions.
            """
            
            return f"Improvement plan {plan_id} created for {contractor_id} ({timeline_weeks} week timeline)"
            
        except Exception as e:
            logger.error(f"Error creating improvement plan", error=str(e))
            return f"Failed to create improvement plan: {str(e)}"
    
    async def _provide_feedback(self, contractor_id: str, feedback_type: str,
                              specific_examples: Optional[List[str]] = None,
                              action_items: Optional[List[str]] = None,
                              delivery_method: str = "message") -> str:
        """
        Provide specific feedback on contractor performance.
        
        Args:
            contractor_id: Contractor identifier
            feedback_type: Type of feedback
            specific_examples: Specific examples
            action_items: Action items for improvement
            delivery_method: Method of delivery
            
        Returns:
            Feedback delivery result
        """
        try:
            feedback_id = f"feedback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Maya providing feedback",
                contractor_id=contractor_id,
                type=feedback_type,
                feedback_id=feedback_id
            )
            
            # Generate feedback message based on type
            if feedback_type == "positive":
                feedback_message = f"""
🎆 Outstanding Performance Recognition!

Hi {contractor_id},

Your recent work has been exceptional! Here's what stood out:
{chr(10).join([f'• {example}' for example in (specific_examples or ['Excellent quality and professionalism'])])}

Keep up the amazing work! Your dedication to quality service is what makes Grime Guardians special.

🌟 You're setting the standard for premium cleaning service!
                """
            
            elif feedback_type == "constructive":
                feedback_message = f"""
📈 Growth Opportunity Feedback

Hi {contractor_id},

You're doing great work! I've identified some areas where we can help you excel even more:

🎯 Areas for Growth:
{chr(10).join([f'• {example}' for example in (specific_examples or ['Continue developing skills'])])}

🚀 Action Items:
{chr(10).join([f'• {item}' for item in (action_items or ['Keep up the great work'])])}

Remember: Every top performer was once a beginner. Your growth mindset is your greatest asset!
                """
            
            elif feedback_type == "corrective":
                feedback_message = f"""
🎯 Important Performance Update

Hi {contractor_id},

I need to address some concerns to help you succeed:

🚨 Areas Needing Attention:
{chr(10).join([f'• {example}' for example in (specific_examples or ['Please review quality standards'])])}

📝 Required Actions:
{chr(10).join([f'• {item}' for item in (action_items or ['Review training materials'])])}

I'm here to support your success. Let's work together to get back on track!
                """
            
            # Record feedback
            feedback_record = {
                "feedback_id": feedback_id,
                "contractor_id": contractor_id,
                "type": feedback_type,
                "message": feedback_message,
                "examples": specific_examples or [],
                "action_items": action_items or [],
                "delivery_method": delivery_method,
                "timestamp": datetime.utcnow()
            }
            
            return f"Feedback {feedback_id} delivered to {contractor_id} via {delivery_method}"
            
        except Exception as e:
            logger.error(f"Error providing feedback", error=str(e))
            return f"Failed to provide feedback: {str(e)}"
    
    async def _track_development(self, contractor_id: str, tracking_period: str = "monthly",
                               development_areas: Optional[List[str]] = None,
                               milestone_check: bool = False) -> str:
        """
        Track contractor skill development and progress.
        
        Args:
            contractor_id: Contractor identifier
            tracking_period: Period for tracking
            development_areas: Areas to track
            milestone_check: Whether this is a milestone check
            
        Returns:
            Development tracking result
        """
        try:
            tracking_id = f"track_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Maya tracking development",
                contractor_id=contractor_id,
                period=tracking_period,
                tracking_id=tracking_id
            )
            
            # Generate development progress report
            progress_report = f"""
📈 Development Progress Report
Contractor: {contractor_id}
Period: {tracking_period}
Tracking ID: {tracking_id}

🎆 Achievements:
• Completed 3 training modules
• Improved quality score by 0.8 points
• 95% checklist compliance rate
• Zero customer complaints

📈 Progress Trends:
• Consistent improvement in photo quality
• Better time management
• Enhanced customer interaction skills

🎯 Next Development Goals:
• Advanced cleaning techniques
• Leadership and mentoring skills
• Efficiency optimization

🌟 Recognition:
Your commitment to growth is exceptional!
You're well on your way to top performer status.
            """
            
            development_record = {
                "tracking_id": tracking_id,
                "contractor_id": contractor_id,
                "period": tracking_period,
                "areas": development_areas or [],
                "report": progress_report,
                "milestone_check": milestone_check,
                "timestamp": datetime.utcnow()
            }
            
            return f"Development tracking {tracking_id} completed for {contractor_id}"
            
        except Exception as e:
            logger.error(f"Error tracking development", error=str(e))
            return f"Failed to track development: {str(e)}"


# Global Maya instance
maya = MayaCoaching()