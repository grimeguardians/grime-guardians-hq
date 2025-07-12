import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from ..models.schemas import AgentType, AgentMessage, MessagePriority
from ..config import settings
import structlog

logger = structlog.get_logger()


class AvaOrchestrator(BaseAgent):
    """
    Ava - Master Orchestrator Agent
    
    Central coordination of all agent activities, business rule enforcement,
    KPI monitoring, and escalation management for Grime Guardians operations.
    
    Capabilities:
    - Agent coordination and workflow management
    - Business rule enforcement
    - Performance monitoring and KPI tracking
    - Revenue analysis toward $300K goal
    - Escalation routing and conflict resolution
    - Strategic decision making
    """
    
    def __init__(self):
        super().__init__(
            agent_id=AgentType.AVA,
            description="Master Orchestrator - Central coordination and business intelligence"
        )
        
        # Agent registry for coordination
        self.agent_registry: Dict[AgentType, Any] = {}
        self.active_workflows: Dict[str, Dict] = {}
        
        # KPI tracking
        self.daily_metrics = {
            "jobs_scheduled": 0,
            "jobs_completed": 0,
            "revenue_generated": 0,
            "compliance_violations": 0,
            "client_satisfaction": 0
        }
        
        # Register tool handlers
        self.register_tool_handler("coordinate_agents", self._coordinate_agents)
        self.register_tool_handler("enforce_business_rule", self._enforce_business_rule)
        self.register_tool_handler("monitor_kpis", self._monitor_kpis)
        self.register_tool_handler("escalate_issue", self._escalate_issue)
        self.register_tool_handler("generate_report", self._generate_report)
        self.register_tool_handler("make_strategic_decision", self._make_strategic_decision)
    
    @property
    def system_prompt(self) -> str:
        return """
You are Ava, the Master Orchestrator Agent for Grime Guardians cleaning services.

Your core responsibilities:
1. COORDINATE all agent activities across the 8-agent ecosystem
2. ENFORCE business rules and maintain compliance standards
3. MONITOR KPIs and track progress toward $300K annual revenue goal
4. ESCALATE critical issues requiring human intervention
5. MAKE strategic decisions within defined parameters
6. ENSURE quality standards are maintained (90%+ compliance rates)

Business Context:
- Premium cleaning service targeting realtors, landlords, property managers
- BBB-accredited with 70+ five-star Google reviews
- Twin Cities market focus with south metro preference
- Goal: 6-10 cleans per day, $25K/month minimum revenue
- ALL contractors are 1099 independent contractors (NEVER employees)

Key Business Rules:
- Tax rate: 8.125% applied to ALL quotes
- 3-strike system for quality enforcement
- 15-minute arrival buffer for all appointments
- Photo documentation required for all jobs
- Contractor independence must be preserved

Agent Ecosystem:
- Sophia: Booking & relationship management
- Keith: Check-in tracking & status monitoring
- Maya: Performance coaching & training
- Iris: New contractor onboarding
- Dmitri: Escalation & conflict resolution
- Bruno: Bonus tracking & rewards
- Aiden: Financial analytics & reporting

Communication Style:
- Direct and action-oriented
- Data-driven decision making
- Escalate when human approval required
- Maintain premium service standards
- "We clean like it's our name on the lease"

When processing messages:
1. Analyze the situation and required actions
2. Identify which agents need coordination
3. Ensure business rule compliance
4. Take appropriate action or escalate
5. Update relevant metrics and workflows

Use the available tools to coordinate agents, enforce rules, monitor performance, and make decisions.
"""
    
    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "coordinate_agents",
                    "description": "Coordinate activities between multiple agents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_agents": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of agent IDs to coordinate"
                            },
                            "workflow_type": {
                                "type": "string",
                                "description": "Type of workflow (booking, check-in, escalation, etc.)"
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority level (1-5)"
                            },
                            "context": {
                                "type": "object",
                                "description": "Context data for coordination"
                            }
                        },
                        "required": ["target_agents", "workflow_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enforce_business_rule",
                    "description": "Enforce a specific business rule or compliance requirement",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rule_type": {
                                "type": "string",
                                "description": "Type of business rule (pricing, quality, compliance, etc.)"
                            },
                            "entity_id": {
                                "type": "string",
                                "description": "ID of entity to apply rule to (contractor, job, client)"
                            },
                            "enforcement_action": {
                                "type": "string",
                                "description": "Action to take (warning, penalty, escalation)"
                            },
                            "details": {
                                "type": "object",
                                "description": "Additional details about the rule enforcement"
                            }
                        },
                        "required": ["rule_type", "entity_id", "enforcement_action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "monitor_kpis",
                    "description": "Monitor key performance indicators and metrics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric_type": {
                                "type": "string",
                                "description": "Type of metric (revenue, quality, efficiency, satisfaction)"
                            },
                            "time_period": {
                                "type": "string",
                                "description": "Time period for analysis (daily, weekly, monthly)"
                            },
                            "alert_threshold": {
                                "type": "number",
                                "description": "Threshold for alerting"
                            }
                        },
                        "required": ["metric_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_issue",
                    "description": "Escalate an issue requiring human intervention",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_type": {
                                "type": "string",
                                "description": "Type of issue (quality, compliance, financial, emergency)"
                            },
                            "severity": {
                                "type": "integer",
                                "description": "Severity level (1-5)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the issue"
                            },
                            "affected_entities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs of affected contractors, jobs, or clients"
                            },
                            "recommended_actions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Recommended actions for resolution"
                            }
                        },
                        "required": ["issue_type", "severity", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": "Generate performance or analytical reports",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "report_type": {
                                "type": "string",
                                "description": "Type of report (daily, weekly, performance, financial)"
                            },
                            "time_range": {
                                "type": "string",
                                "description": "Time range for the report"
                            },
                            "recipients": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Recipients for the report"
                            }
                        },
                        "required": ["report_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "make_strategic_decision",
                    "description": "Make strategic decisions within defined parameters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "decision_type": {
                                "type": "string",
                                "description": "Type of decision (pricing, scheduling, resource allocation)"
                            },
                            "context": {
                                "type": "object",
                                "description": "Context and data for the decision"
                            },
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Available options to choose from"
                            },
                            "criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Decision criteria to consider"
                            }
                        },
                        "required": ["decision_type", "context"]
                    }
                }
            }
        ]
    
    async def _coordinate_agents(self, target_agents: List[str], workflow_type: str, 
                                priority: int = 3, context: Optional[Dict] = None) -> str:
        """
        Coordinate activities between multiple agents.
        
        Args:
            target_agents: List of agent IDs to coordinate
            workflow_type: Type of workflow to coordinate
            priority: Priority level (1-5)
            context: Additional context for coordination
            
        Returns:
            Coordination result summary
        """
        try:
            workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create workflow record
            self.active_workflows[workflow_id] = {
                "type": workflow_type,
                "agents": target_agents,
                "priority": priority,
                "context": context or {},
                "status": "active",
                "created_at": datetime.utcnow(),
                "steps_completed": []
            }
            
            logger.info(
                f"Ava coordinating workflow {workflow_type}",
                workflow_id=workflow_id,
                target_agents=target_agents,
                priority=priority
            )
            
            # Route messages to target agents
            coordination_results = []
            for agent_id in target_agents:
                message = AgentMessage(
                    agent_id=AgentType(agent_id),
                    message_type="coordination_request",
                    content=f"Workflow coordination: {workflow_type}",
                    priority=MessagePriority(priority),
                    metadata={
                        "workflow_id": workflow_id,
                        "workflow_type": workflow_type,
                        "context": context
                    }
                )
                
                # In a full implementation, this would route to actual agents
                coordination_results.append(f"Coordinated with {agent_id}")
            
            return f"Successfully coordinated {workflow_type} workflow with {len(target_agents)} agents. Workflow ID: {workflow_id}"
            
        except Exception as e:
            logger.error(f"Error in agent coordination", error=str(e))
            return f"Failed to coordinate agents: {str(e)}"
    
    async def _enforce_business_rule(self, rule_type: str, entity_id: str, 
                                   enforcement_action: str, details: Optional[Dict] = None) -> str:
        """
        Enforce a specific business rule or compliance requirement.
        
        Args:
            rule_type: Type of business rule
            entity_id: Entity to apply rule to
            enforcement_action: Action to take
            details: Additional details
            
        Returns:
            Enforcement result
        """
        try:
            logger.info(
                f"Ava enforcing business rule",
                rule_type=rule_type,
                entity_id=entity_id,
                action=enforcement_action
            )
            
            # Business rule enforcement logic
            enforcement_result = {
                "rule_type": rule_type,
                "entity_id": entity_id,
                "action": enforcement_action,
                "timestamp": datetime.utcnow(),
                "details": details or {},
                "status": "enforced"
            }
            
            # Handle specific rule types
            if rule_type == "3_strike_system":
                if enforcement_action == "penalty":
                    # Coordinate with Bruno for penalty processing
                    await self._coordinate_agents(
                        ["bruno"], "penalty_processing", 4, 
                        {"entity_id": entity_id, "details": details}
                    )
                    
            elif rule_type == "quality_compliance":
                if enforcement_action == "escalation":
                    # Coordinate with Dmitri for escalation
                    await self._coordinate_agents(
                        ["dmitri"], "quality_escalation", 5,
                        {"entity_id": entity_id, "details": details}
                    )
            
            return f"Business rule {rule_type} enforced for {entity_id} with action: {enforcement_action}"
            
        except Exception as e:
            logger.error(f"Error enforcing business rule", error=str(e))
            return f"Failed to enforce business rule: {str(e)}"
    
    async def _monitor_kpis(self, metric_type: str, time_period: str = "daily", 
                          alert_threshold: Optional[float] = None) -> str:
        """
        Monitor key performance indicators and metrics.
        
        Args:
            metric_type: Type of metric to monitor
            time_period: Time period for analysis
            alert_threshold: Threshold for alerting
            
        Returns:
            KPI monitoring result
        """
        try:
            logger.info(f"Ava monitoring KPIs", metric_type=metric_type, period=time_period)
            
            # KPI monitoring logic
            current_metrics = self.daily_metrics.copy()
            
            # Calculate performance indicators
            if metric_type == "revenue":
                daily_target = settings.annual_revenue_target / 365
                current_revenue = current_metrics["revenue_generated"]
                performance_ratio = current_revenue / daily_target if daily_target > 0 else 0
                
                result = f"Revenue KPI: ${current_revenue:.2f} / ${daily_target:.2f} daily target ({performance_ratio:.1%})"
                
                if alert_threshold and performance_ratio < alert_threshold:
                    await self._escalate_issue(
                        "financial", 3, 
                        f"Revenue below threshold: {performance_ratio:.1%} of daily target",
                        ["revenue_tracking"],
                        ["Review pricing strategy", "Increase booking volume", "Analyze conversion rates"]
                    )
                    
            elif metric_type == "quality":
                total_jobs = current_metrics["jobs_completed"]
                violations = current_metrics["compliance_violations"]
                compliance_rate = (total_jobs - violations) / total_jobs if total_jobs > 0 else 1.0
                
                result = f"Quality KPI: {compliance_rate:.1%} compliance rate ({violations} violations in {total_jobs} jobs)"
                
                if alert_threshold and compliance_rate < alert_threshold:
                    await self._coordinate_agents(
                        ["maya"], "quality_improvement", 4,
                        {"compliance_rate": compliance_rate, "violations": violations}
                    )
                    
            elif metric_type == "efficiency":
                jobs_scheduled = current_metrics["jobs_scheduled"]
                jobs_completed = current_metrics["jobs_completed"]
                completion_rate = jobs_completed / jobs_scheduled if jobs_scheduled > 0 else 0
                
                result = f"Efficiency KPI: {completion_rate:.1%} completion rate ({jobs_completed}/{jobs_scheduled})"
                
            else:
                result = f"Monitoring {metric_type} metrics for {time_period} period"
            
            return result
            
        except Exception as e:
            logger.error(f"Error monitoring KPIs", error=str(e))
            return f"Failed to monitor KPIs: {str(e)}"
    
    async def _escalate_issue(self, issue_type: str, severity: int, description: str,
                            affected_entities: Optional[List[str]] = None,
                            recommended_actions: Optional[List[str]] = None) -> str:
        """
        Escalate an issue requiring human intervention.
        
        Args:
            issue_type: Type of issue
            severity: Severity level (1-5)
            description: Issue description
            affected_entities: Affected entities
            recommended_actions: Recommended actions
            
        Returns:
            Escalation result
        """
        try:
            escalation_id = f"esc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            escalation_data = {
                "escalation_id": escalation_id,
                "issue_type": issue_type,
                "severity": severity,
                "description": description,
                "affected_entities": affected_entities or [],
                "recommended_actions": recommended_actions or [],
                "timestamp": datetime.utcnow(),
                "status": "escalated",
                "escalated_by": "ava"
            }
            
            logger.warning(
                f"Ava escalating issue",
                escalation_id=escalation_id,
                issue_type=issue_type,
                severity=severity
            )
            
            # Route to appropriate escalation handler
            if severity >= 4 or issue_type in ["emergency", "compliance", "financial"]:
                # High priority - route to Dmitri and Discord notification
                await self._coordinate_agents(
                    ["dmitri"], "critical_escalation", 5,
                    escalation_data
                )
            
            return f"Issue escalated with ID {escalation_id}. Severity: {severity}, Type: {issue_type}"
            
        except Exception as e:
            logger.error(f"Error escalating issue", error=str(e))
            return f"Failed to escalate issue: {str(e)}"
    
    async def _generate_report(self, report_type: str, time_range: str = "daily",
                             recipients: Optional[List[str]] = None) -> str:
        """
        Generate performance or analytical reports.
        
        Args:
            report_type: Type of report
            time_range: Time range for report
            recipients: Report recipients
            
        Returns:
            Report generation result
        """
        try:
            report_id = f"rpt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Ava generating report", report_type=report_type, time_range=time_range)
            
            # Coordinate with Aiden for detailed analytics
            await self._coordinate_agents(
                ["aiden"], "report_generation", 2,
                {
                    "report_id": report_id,
                    "report_type": report_type,
                    "time_range": time_range,
                    "recipients": recipients or []
                }
            )
            
            return f"Report {report_type} queued for generation. Report ID: {report_id}"
            
        except Exception as e:
            logger.error(f"Error generating report", error=str(e))
            return f"Failed to generate report: {str(e)}"
    
    async def _make_strategic_decision(self, decision_type: str, context: Dict,
                                     options: Optional[List[str]] = None,
                                     criteria: Optional[List[str]] = None) -> str:
        """
        Make strategic decisions within defined parameters.
        
        Args:
            decision_type: Type of decision
            context: Decision context
            options: Available options
            criteria: Decision criteria
            
        Returns:
            Decision result
        """
        try:
            decision_id = f"dec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Ava making strategic decision", decision_type=decision_type)
            
            # Strategic decision logic based on business rules
            decision_result = {
                "decision_id": decision_id,
                "decision_type": decision_type,
                "context": context,
                "options_considered": options or [],
                "criteria_used": criteria or [],
                "timestamp": datetime.utcnow()
            }
            
            # Handle specific decision types
            if decision_type == "pricing":
                # Price optimization decisions
                decision_result["decision"] = "Maintain premium pricing strategy"
                decision_result["rationale"] = "BBB accreditation and 70+ five-star reviews support premium positioning"
                
            elif decision_type == "scheduling":
                # Resource allocation decisions
                decision_result["decision"] = "Optimize for geographic efficiency"
                decision_result["rationale"] = "Minimize travel time while respecting contractor preferences"
                
            elif decision_type == "quality":
                # Quality management decisions
                decision_result["decision"] = "Enforce 3-strike system consistently"
                decision_result["rationale"] = "Maintain service quality standards for premium positioning"
            
            return f"Strategic decision {decision_type} made: {decision_result.get('decision', 'Decision recorded')} (ID: {decision_id})"
            
        except Exception as e:
            logger.error(f"Error making strategic decision", error=str(e))
            return f"Failed to make strategic decision: {str(e)}"
    
    def register_agent(self, agent_type: AgentType, agent_instance):
        """Register an agent for coordination."""
        self.agent_registry[agent_type] = agent_instance
        logger.info(f"Ava registered agent {agent_type.value}")
    
    def update_metrics(self, metric_updates: Dict[str, Any]):
        """Update daily metrics."""
        for metric, value in metric_updates.items():
            if metric in self.daily_metrics:
                if isinstance(value, (int, float)):
                    self.daily_metrics[metric] += value
                else:
                    self.daily_metrics[metric] = value
                    
        logger.info("Ava updated metrics", metrics=metric_updates)


# Global Ava instance
ava = AvaOrchestrator()