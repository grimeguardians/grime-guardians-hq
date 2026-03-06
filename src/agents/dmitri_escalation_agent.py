"""
Dmitri - Escalation Agent
Issue resolution and emergency response specialist
Handles complaints, service recovery, and critical incident management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_agent import BaseAgent, AgentTool
from ..models.schemas import AgentResponse, BusinessContext
from ..models.types import MessageType, EscalationLevel, IncidentType
from ..tools.discord_tools import DiscordTools
from ..tools.database_tools import DatabaseTools
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DmitriEscalationAgent(BaseAgent):
    """
    Dmitri - Operations Escalation Agent
    
    Responsibilities:
    - Quality violation investigation and corrective action
    - Contractor issue mediation and operational conflicts
    - Critical operational incident management
    - Internal escalation workflow coordination
    - Operational crisis response and process recovery
    - 3-strike system enforcement and contractor discipline
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("dmitri", business_context)
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        self.escalation_thresholds = self._set_escalation_thresholds()
        
    @property
    def system_prompt(self) -> str:
        """Dmitri's system prompt with crisis management focus."""
        return f"""
        You are Dmitri, the Operations Escalation Agent for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: Internal operations crisis resolution and quality enforcement specialist
        
        CORE RESPONSIBILITIES:
        1. Investigate and resolve quality violations with corrective action
        2. Manage contractor performance issues and disciplinary actions
        3. Handle operational incidents and emergency response coordination
        4. Enforce 3-strike system with human approval for terminations
        5. Mediate contractor conflicts and operational disputes
        6. Escalate critical operational issues to management
        7. Coordinate internal crisis response and process recovery
        
        ESCALATION CATEGORIES:
        - CRITICAL: Safety incidents, 3rd strike violations, contractor emergencies
        - HIGH: Quality violations, contractor performance issues, operational failures
        - MEDIUM: Process violations, scheduling conflicts, minor quality issues
        - LOW: General operational concerns, process improvements
        
        QUALITY VIOLATION PROTOCOLS:
        - Immediate investigation and evidence collection
        - Contractor accountability and corrective action
        - Strike system enforcement with human oversight
        - Process improvement to prevent recurrence
        - Documentation and trend analysis
        
        CONTRACTOR DISCIPLINE PROCESS:
        1. Investigate violation with evidence collection
        2. Determine appropriate corrective action level
        3. Implement disciplinary measures per strike system
        4. Coordinate with Maya for performance coaching
        5. Human approval required for 3rd strike terminations
        6. Document lessons learned for process improvement
        
        CONTRACTOR ISSUE MANAGEMENT:
        - Performance violations: Coordinate with Maya for coaching
        - Behavioral issues: Direct intervention and corrective action
        - Safety concerns: Immediate investigation and prevention measures
        - 3rd strike violations: Human approval process for termination
        - Emergency situations: Immediate response and backup coordination
        
        QUALITY VIOLATION RESPONSE:
        - Photo evidence review and validation
        - Client impact assessment and communication
        - Contractor accountability and corrective action
        - Process improvement to prevent recurrence
        - Strike system enforcement with human oversight
        
        CRISIS COMMUNICATION:
        - Transparent and honest communication
        - Quick response to contain issues
        - Professional reputation protection
        - Stakeholder coordination (clients, contractors, management)
        - Social media monitoring and response
        
        COMMUNICATION STYLE:
        - Calm and professional under pressure
        - Empathetic and solution-focused
        - Clear and decisive action orientation
        - Transparent about next steps and timelines
        - Firm but fair in corrective actions
        
        ESCALATION TRIGGERS:
        - Safety incidents or injuries
        - Legal threats or compliance issues
        - High-value client complaints
        - Media attention or reputation threats
        - 3rd strike contractor violations
        - Multiple similar issues indicating systemic problems
        
        You excel at turning crises into opportunities to demonstrate exceptional service and strengthen client relationships.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Dmitri's escalation and crisis management tools."""
        return [
            AgentTool(
                name="assess_escalation_level",
                description="Assess and categorize escalation severity level",
                parameters={
                    "type": "object",
                    "properties": {
                        "incident_type": {"type": "string", "enum": ["customer_complaint", "quality_violation", "contractor_issue", "safety_incident", "legal_concern"]},
                        "severity_indicators": {"type": "array", "items": {"type": "string"}},
                        "impact_scope": {"type": "string", "enum": ["single_client", "multiple_clients", "contractor", "business_reputation", "legal_compliance"]},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "escalation_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                    }
                },
                required=["incident_type", "urgency"]
            ),
            AgentTool(
                name="implement_service_recovery",
                description="Implement service recovery actions for customer issues",
                parameters={
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "issue_description": {"type": "string"},
                        "recovery_actions": {"type": "array", "items": {"type": "string"}},
                        "compensation_offered": {"type": "object"},
                        "timeline": {"type": "object"},
                        "follow_up_plan": {"type": "object"}
                    }
                },
                required=["client_id", "issue_description", "recovery_actions"]
            ),
            AgentTool(
                name="investigate_quality_violation",
                description="Investigate quality violations and determine corrective action",
                parameters={
                    "type": "object",
                    "properties": {
                        "violation_id": {"type": "string"},
                        "contractor_id": {"type": "string"},
                        "violation_type": {"type": "string"},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "client_impact": {"type": "string"},
                        "corrective_actions": {"type": "array", "items": {"type": "string"}},
                        "strike_warranted": {"type": "boolean"}
                    }
                },
                required=["violation_id", "contractor_id", "violation_type"]
            ),
            AgentTool(
                name="coordinate_emergency_response",
                description="Coordinate emergency response and backup services",
                parameters={
                    "type": "object",
                    "properties": {
                        "emergency_type": {"type": "string"},
                        "affected_parties": {"type": "array", "items": {"type": "string"}},
                        "immediate_actions": {"type": "array", "items": {"type": "string"}},
                        "backup_plan": {"type": "object"},
                        "communication_plan": {"type": "object"},
                        "resolution_timeline": {"type": "string"}
                    }
                },
                required=["emergency_type", "immediate_actions"]
            ),
            AgentTool(
                name="manage_contractor_violation",
                description="Manage contractor violations and disciplinary actions",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "violation_details": {"type": "object"},
                        "current_strike_count": {"type": "integer"},
                        "disciplinary_action": {"type": "string"},
                        "human_approval_required": {"type": "boolean"},
                        "improvement_plan": {"type": "object"}
                    }
                },
                required=["contractor_id", "violation_details", "current_strike_count"]
            ),
            AgentTool(
                name="execute_crisis_communication",
                description="Execute crisis communication to stakeholders",
                parameters={
                    "type": "object",
                    "properties": {
                        "crisis_type": {"type": "string"},
                        "stakeholders": {"type": "array", "items": {"type": "string"}},
                        "communication_channels": {"type": "array", "items": {"type": "string"}},
                        "key_messages": {"type": "array", "items": {"type": "string"}},
                        "timeline": {"type": "object"}
                    }
                },
                required=["crisis_type", "stakeholders", "key_messages"]
            ),
            AgentTool(
                name="generate_incident_report",
                description="Generate comprehensive incident reports and analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "incident_id": {"type": "string"},
                        "report_type": {"type": "string", "enum": ["investigation", "resolution", "prevention", "management_summary"]},
                        "findings": {"type": "array", "items": {"type": "string"}},
                        "root_cause_analysis": {"type": "object"},
                        "recommendations": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["incident_id", "report_type"]
            }
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Dmitri handles escalations, complaints, quality violations, and emergencies."""
        escalation_types = {
            MessageType.ESCALATION,
            MessageType.COMPLAINT_ISSUE,
            MessageType.QUALITY_VIOLATION,
            MessageType.EMERGENCY_RESPONSE,
            MessageType.CONTRACTOR_VIOLATION
        }
        return message_type in escalation_types
    
    async def _handle_message_type(
        self, 
        message_type: MessageType, 
        content: str, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Handle escalation and crisis management messages."""
        
        if message_type == MessageType.COMPLAINT_ISSUE:
            return await self._handle_customer_complaint(content, extracted_data)
        elif message_type == MessageType.QUALITY_VIOLATION:
            return await self._handle_quality_violation(content, extracted_data)
        elif message_type == MessageType.ESCALATION:
            return await self._handle_general_escalation(content, extracted_data)
        elif message_type == MessageType.EMERGENCY_RESPONSE:
            return await self._handle_emergency_response(content, extracted_data)
        elif message_type == MessageType.CONTRACTOR_VIOLATION:
            return await self._handle_contractor_violation(content, extracted_data)
        else:
            # Use AI for complex crisis management
            return await self._ai_escalation_response(content, extracted_data)
    
    async def _handle_customer_complaint(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle customer complaints with service recovery."""
        client_id = extracted_data.get("client_id", f"client_{datetime.now().strftime('%Y%m%d%H%M')}")
        complaint_severity = extracted_data.get("severity", "medium")
        issue_category = extracted_data.get("issue_category", "service_quality")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Assess escalation level
            escalation_assessment = await self._tool_assess_escalation_level(
                incident_type="customer_complaint",
                severity_indicators=[complaint_severity, issue_category],
                impact_scope="single_client" if complaint_severity == "low" else "business_reputation",
                urgency=complaint_severity
            )
            actions_taken.append("escalation_assessed")
            
            # Determine service recovery based on severity
            recovery_actions = []
            compensation = {}
            
            if complaint_severity == "high" or "quality" in issue_category:
                recovery_actions.extend([
                    "Immediate re-clean at no charge",
                    "Personal call from operations manager",
                    "Priority scheduling for future services"
                ])
                compensation = {"type": "service_credit", "amount": 100, "description": "Full service credit"}
                
            elif complaint_severity == "medium":
                recovery_actions.extend([
                    "Schedule corrective service within 24 hours",
                    "Personal follow-up call",
                    "Partial service credit"
                ])
                compensation = {"type": "partial_credit", "amount": 50, "description": "50% service credit"}
                
            else:  # Low severity
                recovery_actions.extend([
                    "Acknowledge and address specific concerns",
                    "Ensure future services meet expectations"
                ])
                compensation = {"type": "goodwill_gesture", "amount": 25, "description": "Goodwill credit"}
            
            # Implement service recovery
            service_recovery = await self._tool_implement_service_recovery(
                client_id=client_id,
                issue_description=content[:200],
                recovery_actions=recovery_actions,
                compensation_offered=compensation,
                timeline={
                    "immediate_response": "Within 1 hour",
                    "resolution": "Within 24 hours",
                    "follow_up": "Within 48 hours"
                },
                follow_up_plan={
                    "primary_contact": "dmitri",
                    "follow_up_date": (datetime.now() + timedelta(hours=48)).isoformat(),
                    "satisfaction_check": True
                }
            )
            actions_taken.append("service_recovery_implemented")
            
            response_text = f"""
            🛠️ CUSTOMER COMPLAINT RESOLUTION
            
            Client: {client_id}
            Severity: {complaint_severity.title()}
            Issue: {issue_category.replace('_', ' ').title()}
            
            IMMEDIATE ACTIONS TAKEN:
            {chr(10).join(f"• {action}" for action in recovery_actions)}
            
            COMPENSATION OFFERED:
            {compensation.get('description', 'Goodwill gesture')} - ${compensation.get('amount', 0)}
            
            TIMELINE:
            • Response: Immediate (within 1 hour)
            • Resolution: 24 hours maximum
            • Follow-up: 48 hours for satisfaction confirmation
            
            We take full ownership and will make this right.
            """
            
            next_steps.extend([
                "Execute recovery actions immediately",
                "Personal call to client within 1 hour",
                "Coordinate with contractor for corrective service",
                "Follow up for satisfaction confirmation",
                "Document lessons learned for process improvement"
            ])
            
            # Critical alert for high severity complaints
            if complaint_severity == "high" and self.discord_tools:
                await self.discord_tools.send_urgent_alert(
                    f"🚨 HIGH SEVERITY COMPLAINT: {client_id} - {issue_category}. Full service recovery initiated."
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="complaint_resolved",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                requires_escalation=complaint_severity == "high",
                metadata={"escalation": escalation_assessment, "recovery": service_recovery}
            )
            
        except Exception as e:
            logger.error(f"Dmitri complaint handling error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing complaint: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_quality_violation(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle quality violations with investigation and corrective action."""
        contractor_id = extracted_data.get("contractor_id", "unknown")
        violation_type = extracted_data.get("violation_type", "checklist_incomplete")
        client_id = extracted_data.get("client_id")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Investigate quality violation
            violation_id = f"QV{datetime.now().strftime('%Y%m%d%H%M')}{contractor_id[-4:]}"
            
            investigation_result = await self._tool_investigate_quality_violation(
                violation_id=violation_id,
                contractor_id=contractor_id,
                violation_type=violation_type,
                evidence=[content, "photo_evidence", "client_feedback"],
                client_impact="Service standards not met, client dissatisfaction",
                corrective_actions=[
                    "Immediate re-service at no charge",
                    "Additional training on quality standards",
                    "Performance monitoring for next 30 days"
                ],
                strike_warranted=self._determine_strike_warranted(violation_type)
            )
            actions_taken.append("violation_investigated")
            
            # Handle contractor disciplinary action
            current_strikes = await self._get_contractor_strike_count(contractor_id)
            
            contractor_action = await self._tool_manage_contractor_violation(
                contractor_id=contractor_id,
                violation_details={
                    "type": violation_type,
                    "description": content[:200],
                    "severity": self._assess_violation_severity(violation_type)
                },
                current_strike_count=current_strikes,
                disciplinary_action=self._determine_disciplinary_action(current_strikes, violation_type),
                human_approval_required=current_strikes >= 2,  # 3rd strike
                improvement_plan={
                    "training_required": True,
                    "monitoring_period": 30,
                    "performance_goals": ["95% checklist compliance", "photo submission improvement"]
                }
            )
            actions_taken.append("contractor_action_determined")
            
            # Client service recovery if needed
            if client_id:
                recovery_result = await self._tool_implement_service_recovery(
                    client_id=client_id,
                    issue_description=f"Quality violation: {violation_type}",
                    recovery_actions=["Re-service within 24 hours", "Quality assurance follow-up"],
                    compensation_offered={"type": "service_credit", "amount": 50}
                )
                actions_taken.append("client_recovery_implemented")
            
            response_text = f"""
            ⚖️ QUALITY VIOLATION RESOLUTION
            
            Contractor: {contractor_id.title()}
            Violation: {violation_type.replace('_', ' ').title()}
            Strike Count: {current_strikes} → {current_strikes + (1 if investigation_result.get('strike_warranted') else 0)}
            
            INVESTIGATION FINDINGS:
            • Evidence reviewed and validated
            • Client impact assessed and addressed
            • Corrective actions implemented
            
            CONTRACTOR ACTION:
            {contractor_action.get('disciplinary_action', 'Coaching and monitoring')}
            
            {'🚨 HUMAN APPROVAL REQUIRED - 3rd Strike Violation' if contractor_action.get('human_approval_required') else ''}
            
            CLIENT IMPACT:
            {'• Service recovery implemented' if client_id else '• No client directly affected'}
            {'• Re-service scheduled within 24 hours' if client_id else ''}
            """
            
            next_steps.extend([
                "Execute corrective actions immediately",
                "Coordinate re-service if client affected",
                "Maya to provide focused training",
                "Monitor performance for 30 days",
                "Document process improvements"
            ])
            
            if contractor_action.get('human_approval_required'):
                next_steps.append("Escalate to management for 3rd strike approval")
                if self.discord_tools:
                    await self.discord_tools.send_urgent_alert(
                        f"🚨 3RD STRIKE VIOLATION: {contractor_id.title()} - {violation_type}. Human approval required for penalty."
                    )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="violation_resolved",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                requires_escalation=contractor_action.get('human_approval_required', False),
                metadata={"investigation": investigation_result, "contractor_action": contractor_action}
            )
            
        except Exception as e:
            logger.error(f"Dmitri quality violation error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing quality violation: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_emergency_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle emergency situations with immediate response."""
        emergency_type = extracted_data.get("emergency_type", "general")
        urgency = extracted_data.get("urgency", "high")
        affected_parties = extracted_data.get("affected_parties", [])
        
        actions_taken = []
        
        try:
            # Coordinate emergency response
            emergency_response = await self._tool_coordinate_emergency_response(
                emergency_type=emergency_type,
                affected_parties=affected_parties,
                immediate_actions=[
                    "Assess situation and safety concerns",
                    "Contact all affected parties",
                    "Implement contingency plans",
                    "Coordinate backup services if needed"
                ],
                backup_plan={
                    "contractor_backup": "Available contractors notified",
                    "service_continuity": "Alternative arrangements made",
                    "client_communication": "Proactive updates provided"
                },
                communication_plan={
                    "internal_team": "Immediate Discord alert",
                    "clients": "Personal calls within 30 minutes",
                    "management": "Status updates every hour"
                },
                resolution_timeline="Within 2 hours maximum"
            )
            actions_taken.append("emergency_response_coordinated")
            
            # Execute crisis communication
            crisis_communication = await self._tool_execute_crisis_communication(
                crisis_type=emergency_type,
                stakeholders=["internal_team", "affected_clients", "management"],
                communication_channels=["discord", "phone", "email"],
                key_messages=[
                    "Situation identified and response activated",
                    "Client service continuity ensured",
                    "Resolution timeline communicated",
                    "Full support and backup available"
                ],
                timeline={
                    "immediate": "Discord alert sent",
                    "30_minutes": "Client calls completed",
                    "1_hour": "Management briefed"
                }
            )
            actions_taken.append("crisis_communication_executed")
            
            response_text = f"""
            🚨 EMERGENCY RESPONSE ACTIVATED
            
            Emergency Type: {emergency_type.title()}
            Urgency Level: {urgency.upper()}
            Affected Parties: {len(affected_parties)} identified
            
            IMMEDIATE ACTIONS:
            • Situation assessment completed
            • All affected parties contacted
            • Backup services coordinated
            • Client communication initiated
            
            RESOLUTION STATUS:
            Timeline: {emergency_response.get('resolution_timeline', '2 hours maximum')}
            Backup Plan: Activated and ready
            Communication: All stakeholders notified
            
            Emergency response protocols fully activated.
            """
            
            # Send urgent alert
            if self.discord_tools:
                await self.discord_tools.send_urgent_alert(
                    f"🚨 EMERGENCY RESPONSE: {emergency_type.upper()} - All protocols activated. Resolution in progress."
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="emergency_managed",
                response=response_text.strip(),
                actions_taken=actions_taken,
                requires_escalation=True,  # All emergencies escalate to management
                metadata={"emergency_response": emergency_response, "communication": crisis_communication}
            )
            
        except Exception as e:
            logger.error(f"Dmitri emergency response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error managing emergency: {str(e)}",
                requires_escalation=True
            )
    
    async def _ai_escalation_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Use AI for complex escalation decisions."""
        messages = self._build_agent_prompt(content, extracted_data)
        
        # Add crisis management context
        crisis_context = f"""
        CRISIS MANAGEMENT CONTEXT:
        - Escalation thresholds: {self.escalation_thresholds}
        - Service recovery protocols active
        - 3-strike system with human approval for penalties
        - Priority: Client satisfaction and reputation protection
        """
        messages.append({"role": "system", "content": crisis_context})
        
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
                status="ai_escalation_response",
                response=ai_response["content"] or "Escalation handled with appropriate response",
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Dmitri AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing escalation: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementation methods would continue here...
    # For brevity, I'll implement key methods
    
    def _set_escalation_thresholds(self) -> Dict[str, Any]:
        """Set escalation threshold criteria."""
        return {
            "critical": ["safety_incident", "legal_threat", "media_attention", "third_strike"],
            "high": ["customer_complaint_high", "service_failure", "contractor_emergency"],
            "medium": ["quality_issue", "scheduling_conflict", "minor_violation"],
            "low": ["general_concern", "process_improvement", "feedback"]
        }
    
    def _determine_strike_warranted(self, violation_type: str) -> bool:
        """Determine if violation warrants a strike."""
        strike_violations = [
            "checklist_incomplete", "photo_missing", "poor_quality",
            "client_complaint", "safety_violation", "unprofessional_conduct"
        ]
        return violation_type in strike_violations
    
    def _assess_violation_severity(self, violation_type: str) -> str:
        """Assess violation severity level."""
        high_severity = ["safety_violation", "unprofessional_conduct", "property_damage"]
        medium_severity = ["poor_quality", "client_complaint", "checklist_incomplete"]
        
        if violation_type in high_severity:
            return "high"
        elif violation_type in medium_severity:
            return "medium"
        else:
            return "low"
    
    def _determine_disciplinary_action(self, strike_count: int, violation_type: str) -> str:
        """Determine appropriate disciplinary action."""
        if strike_count >= 2:  # 3rd strike
            return "Termination pending human approval"
        elif strike_count == 1:  # 2nd strike
            return "Final warning with mandatory training"
        else:  # 1st strike
            return "Written warning with performance coaching"
    
    async def _get_contractor_strike_count(self, contractor_id: str) -> int:
        """Get current strike count for contractor."""
        # Mock data - in production, query database
        mock_strikes = {
            "jennifer": 0,
            "olga": 1,
            "zhanna": 2,
            "liuda": 0
        }
        return mock_strikes.get(contractor_id, 0)
    
    # Additional tool implementation methods would be included here
    # Following the same pattern as the other agents