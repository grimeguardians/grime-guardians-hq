"""
Ava - Master Orchestrator Agent
Chief Operations Officer for Grime Guardians
Coordinates all agent activities and enforces business rules
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_agent import BaseAgent, AgentTool
from ..models.schemas import AgentResponse, BusinessContext, KPISnapshot
from ..models.types import MessageType, JobStatus, ContractorStatus, ViolationType
from ..core.pricing_engine import PricingEngine
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AvaOrchestrator(BaseAgent):
    """
    Ava - Master Orchestrator Agent
    
    Responsibilities:
    - Central coordination of all agent activities
    - Business rule enforcement and decision making
    - KPI monitoring and performance analytics
    - Revenue tracking toward $300K annual goal
    - Escalation management and workflow coordination
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("ava", business_context)
        self.pricing_engine = PricingEngine()
        self.kpi_thresholds = self._set_kpi_thresholds()
        
    @property
    def system_prompt(self) -> str:
        """Ava's system prompt with business context."""
        return f"""
        You are Ava, the Master Orchestrator and COO for Grime Guardians cleaning service.

        MISSION: "We clean like it's our name on the lease"
        BUSINESS GOAL: $500,000 gross revenue by EOY 2026 (~$42K/month, ~$9,615/week)

        CORE RESPONSIBILITIES:
        1. Coordinate all agent activities (Dean, Emma, Sophia, Keith, Maya, Iris, Dmitri, Bruno, Aiden)
        2. Enforce business rules and maintain premium service standards
        3. Monitor KPIs and ensure 90%+ compliance rates
        4. Track revenue progress toward $500K goal
        5. Manage escalations and workflow coordination
        6. Maintain contractor independence (1099 status)

        BUSINESS RULES TO ENFORCE:
        - All pricing includes 8.125% tax (multiplier 1.08125)
        - 3-strike system for quality violations (HUMAN APPROVAL required for penalties)
        - Contractor independence must be preserved at all times
        - Photo requirements: kitchen, bathrooms, entry area, impacted rooms
        - 15-minute arrival buffer — cleaners scheduled 15 min before client appointment
        - Premium service positioning — never apologize for pricing
        - Late arrival without prior communication = auto-flag and log to #strikes channel

        ACTIVE CONTRACTOR TEAMS:
        - Katy + Crew (sub): Anywhere except north. Best for high-volume, move-outs, large scope.
        - Anna + Oksana (duo): Anywhere. Best for move-outs, deep cleans, post-con.
        - Kateryna (solo): North/Eagan/Minnetonka/Eden Prairie/Edina. Will NOT do Mpls/St. Paul or Woodbury+.
        - Liuda (solo): North only. Recurring northern routes.

        DISPATCH PRIORITY: Territory match → Job type match → Consistency → Quality risk

        PRICING FRAMEWORK (pre-tax):
        - Elite Reset: $299-$549 by sqft tier (50% to cleaner — CAC job)
        - Elite Listing Polish: $549/$749/$999+ (30% to cleaner)
        - Move-Out Deep Reset: $849/$1,149/$1,499+ (30% to cleaner)
        - Continuity Essentials: $299-$499/visit (40% to cleaner)
        - Continuity Prestige: $449-$649/visit (40% to cleaner)
        - Continuity VIP Elite: $799-$999/visit (40% to cleaner)
        - B2B Turnover: $399-$699/unit (30% to cleaner)
        - Hourly: $100/hr (non-standard only)

        KPI TARGETS:
        - Checklist compliance: 90%+
        - Photo submission: 90%+
        - On-time arrival: 95%+
        - Customer satisfaction: 9/10+
        - Jobs per day: 6-10
        - Monthly revenue: $42,000

        COMMUNICATION STYLE:
        - Direct and decisive
        - Business-focused, solution-oriented
        - Maintains premium positioning

        ESCALATION PROTOCOLS:
        - Pricing/quotes → Dean (CMO)
        - Customer complaints/feedback → Emma (CXO)
        - Quality violations → Dmitri for resolution
        - Contractor coaching → Maya
        - New contractor issues → Iris
        - Scheduling/check-ins → Keith
        - Bonus calculations → Bruno
        - Performance analytics → Aiden

        You make executive decisions while maintaining contractor independence and business compliance.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Ava's coordination and oversight tools."""
        return [
            AgentTool(
                name="coordinate_agents",
                description="Coordinate activities between specialist agents",
                parameters={
                    "type": "object",
                    "properties": {
                        "target_agents": {"type": "array", "items": {"type": "string"}},
                        "coordination_type": {"type": "string", "enum": ["assign", "escalate", "collaborate"]},
                        "message": {"type": "string"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5}
                    }
                },
                required=["target_agents", "coordination_type", "message"]
            ),
            AgentTool(
                name="enforce_business_rules",
                description="Enforce Grime Guardians business rules and compliance",
                parameters={
                    "type": "object",
                    "properties": {
                        "rule_type": {"type": "string", "enum": ["pricing", "quality", "contractor_independence", "compliance"]},
                        "entity_id": {"type": "string"},
                        "action": {"type": "string"},
                        "justification": {"type": "string"}
                    }
                },
                required=["rule_type", "action", "justification"]
            ),
            AgentTool(
                name="monitor_kpis",
                description="Monitor and analyze key performance indicators",
                parameters={
                    "type": "object",
                    "properties": {
                        "kpi_type": {"type": "string", "enum": ["compliance", "revenue", "quality", "efficiency"]},
                        "time_period": {"type": "string", "enum": ["today", "week", "month"]},
                        "alert_threshold": {"type": "boolean"}
                    }
                },
                required=["kpi_type"]
            ),
            AgentTool(
                name="escalate_issue",
                description="Escalate issues requiring immediate attention",
                parameters={
                    "type": "object",
                    "properties": {
                        "issue_type": {"type": "string", "enum": ["quality", "contractor", "customer", "system"]},
                        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "description": {"type": "string"},
                        "involved_parties": {"type": "array", "items": {"type": "string"}},
                        "recommended_action": {"type": "string"}
                    }
                },
                required=["issue_type", "severity", "description", "recommended_action"]
            ),
            AgentTool(
                name="track_revenue_progress",
                description="Track progress toward $300K annual revenue goal",
                parameters={
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "enum": ["daily", "monthly", "annual"]},
                        "current_amount": {"type": "number"},
                        "target_amount": {"type": "number"},
                        "projection_needed": {"type": "boolean"}
                    }
                },
                required=["period", "current_amount"]
            ),
            AgentTool(
                name="validate_contractor_compliance",
                description="Validate contractor 1099 independence compliance",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "action_type": {"type": "string"},
                        "compliance_check": {"type": "array", "items": {"type": "string"}},
                        "independence_maintained": {"type": "boolean"}
                    }
                },
                required=["contractor_id", "action_type", "independence_maintained"]
            }
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Ava handles coordination, compliance, and escalation messages."""
        coordination_types = {
            MessageType.ESCALATION,
            MessageType.COMPLIANCE_CHECK,
            MessageType.ANALYTICS_REPORT
        }
        return message_type in coordination_types
    
    async def _handle_message_type(
        self, 
        message_type: MessageType, 
        content: str, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Handle messages that require Ava's coordination."""
        
        if message_type == MessageType.ESCALATION:
            return await self._handle_escalation(content, extracted_data)
        elif message_type == MessageType.COMPLIANCE_CHECK:
            return await self._handle_compliance_check(content, extracted_data)
        elif message_type == MessageType.ANALYTICS_REPORT:
            return await self._handle_analytics_report(content, extracted_data)
        else:
            # Use AI to determine best response
            return await self._ai_response(content, extracted_data)
    
    async def _handle_escalation(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle escalated issues requiring immediate attention."""
        issue_type = extracted_data.get("issue_type", "general")
        severity = extracted_data.get("severity", "medium")
        contractor_id = extracted_data.get("contractor_id")
        
        # Determine escalation response based on business rules
        actions_taken = []
        next_steps = []
        requires_escalation = False
        
        if issue_type == "quality" and contractor_id:
            # Quality issue escalation
            violation_count = await self._get_contractor_violation_count(contractor_id)
            
            if violation_count >= 2:  # 3rd strike
                actions_taken.append(f"3rd_strike_penalty_request_{contractor_id}")
                next_steps.append("Request human approval for contractor penalty")
                requires_escalation = True
            else:
                actions_taken.append(f"route_to_dmitri_quality_resolution")
                next_steps.append("Dmitri to handle quality issue resolution")
        
        elif issue_type == "customer":
            # Customer complaint escalation
            actions_taken.append("route_to_dmitri_customer_recovery")
            next_steps.append("Dmitri to implement service recovery protocol")
            
        elif issue_type == "contractor":
            # Contractor performance escalation
            actions_taken.append("route_to_maya_coaching")
            next_steps.append("Maya to provide performance coaching")
        
        response_text = f"Escalation handled: {issue_type} issue (severity: {severity}). "
        if contractor_id:
            response_text += f"Contractor {contractor_id} involved. "
        response_text += f"Actions: {', '.join(actions_taken)}"
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="escalation_handled",
            response=response_text,
            actions_taken=actions_taken,
            requires_escalation=requires_escalation,
            next_steps=next_steps
        )
    
    async def _handle_compliance_check(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle contractor compliance validation."""
        contractor_id = extracted_data.get("contractor_id")
        action_type = extracted_data.get("action_type", "general")
        
        # Validate contractor independence
        compliance_issues = []
        
        # Check for employee-like control
        control_indicators = [
            "mandate_schedule", "require_specific_hours", "control_work_method",
            "direct_supervision", "exclusive_work_requirement"
        ]
        
        if any(indicator in content.lower() for indicator in control_indicators):
            compliance_issues.append("potential_employee_control_detected")
        
        # Check for proper 1099 treatment
        if "w2" in content.lower() or "employee" in content.lower():
            compliance_issues.append("employee_classification_risk")
        
        independence_maintained = len(compliance_issues) == 0
        
        if compliance_issues:
            response = f"COMPLIANCE ALERT: Issues detected for contractor {contractor_id}: {', '.join(compliance_issues)}"
            actions_taken = ["compliance_violation_flagged", "require_policy_review"]
            requires_escalation = True
        else:
            response = f"Compliance check passed for contractor {contractor_id}. 1099 independence maintained."
            actions_taken = ["compliance_validated"]
            requires_escalation = False
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="compliance_checked",
            response=response,
            actions_taken=actions_taken,
            requires_escalation=requires_escalation
        )
    
    async def _handle_analytics_report(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle analytics and KPI reporting."""
        kpi_data = await self._get_current_kpis()
        
        # Analyze KPI performance
        alerts = []
        recommendations = []
        
        # Check compliance rates
        if kpi_data["checklist_compliance"] < 90:
            alerts.append(f"Checklist compliance below target: {kpi_data['checklist_compliance']:.1f}%")
            recommendations.append("Increase checklist enforcement training")
        
        if kpi_data["photo_submission"] < 90:
            alerts.append(f"Photo submission below target: {kpi_data['photo_submission']:.1f}%")
            recommendations.append("Route to Maya for photo submission coaching")
        
        # Check revenue progress
        monthly_target = 42_000  # $42K/month target (Operating Manual 2026)
        if kpi_data["revenue_month"] < monthly_target * 0.8:  # 80% of target
            alerts.append(f"Revenue tracking behind target: ${kpi_data['revenue_month']:,.2f}")
            recommendations.append("Increase job volume or evaluate pricing strategy")
        
        # Generate response
        if alerts:
            response = f"KPI ALERTS: {len(alerts)} issues detected. " + "; ".join(alerts[:2])
            actions_taken = ["kpi_alerts_generated", "recommendations_provided"]
            requires_escalation = True
        else:
            response = f"KPI Status: All metrics on target. Revenue: ${kpi_data['revenue_month']:,.2f}"
            actions_taken = ["kpi_report_generated"]
            requires_escalation = False
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="analytics_processed",
            response=response,
            actions_taken=actions_taken,
            requires_escalation=requires_escalation,
            next_steps=recommendations
        )
    
    async def _ai_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Use AI for complex coordination decisions."""
        messages = self._build_agent_prompt(content, extracted_data)
        
        # Add tools for AI decision making
        tools = [
            {
                "type": "function",
                "function": tool.dict()
            } for tool in self.tools
        ]
        
        try:
            ai_response = await self.call_openai(messages, tools)
            
            actions_taken = []
            next_steps = []
            requires_escalation = False
            
            # Process tool calls if any
            if ai_response.get("tool_calls"):
                for tool_call in ai_response["tool_calls"]:
                    tool_name = tool_call.function.name
                    tool_params = tool_call.function.arguments
                    
                    # Execute tool and track actions
                    tool_result = await self.execute_tool(tool_name, tool_params)
                    actions_taken.append(f"executed_{tool_name}")
                    
                    if "escalate" in tool_name:
                        requires_escalation = True
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="ai_processed",
                response=ai_response["content"] or "Coordination decision processed",
                actions_taken=actions_taken,
                requires_escalation=requires_escalation,
                next_steps=next_steps
            )
            
        except Exception as e:
            logger.error(f"Ava AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing coordination request: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementation methods
    async def _tool_coordinate_agents(
        self, 
        target_agents: List[str], 
        coordination_type: str, 
        message: str, 
        priority: int = 3
    ) -> Dict[str, Any]:
        """Coordinate activities between specialist agents."""
        coordination_results = []
        
        for agent_id in target_agents:
            if agent_id in ["sophia", "keith", "maya", "iris", "dmitri", "bruno", "aiden"]:
                # In production, this would route to actual agents
                coordination_results.append({
                    "agent_id": agent_id,
                    "coordination_type": coordination_type,
                    "status": "coordinated",
                    "message": message
                })
        
        return {
            "coordinated_agents": len(coordination_results),
            "results": coordination_results,
            "priority": priority
        }
    
    async def _tool_enforce_business_rules(
        self, 
        rule_type: str, 
        action: str, 
        justification: str, 
        entity_id: str = None
    ) -> Dict[str, Any]:
        """Enforce business rules and compliance."""
        enforcement_result = {
            "rule_type": rule_type,
            "action": action,
            "entity_id": entity_id,
            "justification": justification,
            "compliant": True,
            "enforcement_actions": []
        }
        
        if rule_type == "contractor_independence":
            # Validate contractor independence
            if any(keyword in action.lower() for keyword in ["mandate", "require", "control"]):
                enforcement_result["compliant"] = False
                enforcement_result["enforcement_actions"].append("independence_violation_flagged")
        
        elif rule_type == "pricing":
            # Validate pricing rules
            if "tax" not in action.lower():
                enforcement_result["enforcement_actions"].append("ensure_tax_application")
        
        elif rule_type == "quality":
            # Validate quality enforcement
            if "strike" in action.lower() and "approval" not in action.lower():
                enforcement_result["enforcement_actions"].append("require_human_approval")
        
        return enforcement_result
    
    async def _tool_monitor_kpis(
        self, 
        kpi_type: str, 
        time_period: str = "today", 
        alert_threshold: bool = False
    ) -> Dict[str, Any]:
        """Monitor and analyze KPIs."""
        kpi_data = await self._get_current_kpis()
        
        monitoring_result = {
            "kpi_type": kpi_type,
            "time_period": time_period,
            "current_values": kpi_data,
            "alerts": [],
            "recommendations": []
        }
        
        # Apply threshold alerts if requested
        if alert_threshold:
            if kpi_type == "compliance":
                if kpi_data.get("checklist_compliance", 0) < 90:
                    monitoring_result["alerts"].append("Checklist compliance below 90%")
                if kpi_data.get("photo_submission", 0) < 90:
                    monitoring_result["alerts"].append("Photo submission below 90%")
            
            elif kpi_type == "revenue":
                monthly_target = 25000
                if kpi_data.get("revenue_month", 0) < monthly_target * 0.8:
                    monitoring_result["alerts"].append("Revenue below 80% of monthly target")
        
        return monitoring_result
    
    async def _tool_track_revenue_progress(
        self, 
        period: str, 
        current_amount: float, 
        target_amount: float = None, 
        projection_needed: bool = False
    ) -> Dict[str, Any]:
        """Track revenue progress toward goals."""
        
        # Set default targets (Operating Manual 2026)
        targets = {
            "daily": 1_400.00,   # $42K/month ÷ 30 days
            "weekly": 9_615,
            "monthly": 42_000,
            "annual": 500_000
        }
        
        if target_amount is None:
            target_amount = targets.get(period, 25000)
        
        progress_percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
        
        tracking_result = {
            "period": period,
            "current_amount": current_amount,
            "target_amount": target_amount,
            "progress_percentage": progress_percentage,
            "on_track": progress_percentage >= 80,  # 80% threshold
            "projection": None
        }
        
        if projection_needed and period == "monthly":
            # Simple projection based on current progress
            days_in_month = 30
            current_day = datetime.now().day
            daily_average = current_amount / current_day if current_day > 0 else 0
            projected_monthly = daily_average * days_in_month
            
            tracking_result["projection"] = {
                "projected_monthly": projected_monthly,
                "projected_vs_target": (projected_monthly / target_amount * 100) if target_amount > 0 else 0
            }
        
        return tracking_result
    
    def _set_kpi_thresholds(self) -> Dict[str, float]:
        """Set KPI threshold values for monitoring."""
        return {
            "checklist_compliance_min": 90.0,
            "photo_submission_min": 90.0,
            "on_time_percentage_min": 95.0,
            "customer_satisfaction_min": 9.0,
            "jobs_per_day_min": 6,
            "jobs_per_day_max": 10,
            "weekly_revenue_min": 9_615,
            "monthly_revenue_min": 42_000,
            "annual_revenue_target": 500_000,
        }
    
    async def _get_contractor_violation_count(self, contractor_id: str) -> int:
        """Get current violation count for contractor."""
        # In production, this would query the database
        # Violation history starts fresh — no import from legacy system
        mock_violations: Dict[str, int] = {
            "katy_crew":   0,
            "anna_oksana": 0,
            "kateryna":    0,
            "liuda":       0,
        }
        return mock_violations.get(contractor_id, 0)
    
    async def _get_current_kpis(self) -> Dict[str, float]:
        """Get current KPI values."""
        # In production, this would aggregate from Notion/database
        return {
            "checklist_compliance": 92.5,
            "photo_submission": 88.3,   # Below 90% threshold — triggers alert
            "on_time_percentage": 96.2,
            "customer_satisfaction": 9.1,
            "jobs_today": 7,
            "revenue_today": 1_850.00,
            "revenue_week": 9_200.00,
            "revenue_month": 34_500.00,
            "active_teams": 4,           # katy_crew, anna_oksana, kateryna, liuda
            "violations_today": 1,
            "annual_target": 500_000,
        }