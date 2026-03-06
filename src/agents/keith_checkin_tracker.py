"""
Keith - Check-in Tracker Agent
Contractor status monitoring and geographic optimization specialist
Handles arrival tracking, location monitoring, and route optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_agent import BaseAgent, AgentTool
from ..models.schemas import AgentResponse, BusinessContext
from ..models.types import MessageType, JobStatus, ContractorStatus
from ..tools.discord_tools import DiscordTools
from ..tools.database_tools import DatabaseTools
from ..config.settings import get_settings, CONTRACTOR_TERRITORIES

logger = logging.getLogger(__name__)
settings = get_settings()


class KeithCheckinTracker(BaseAgent):
    """
    Keith - Check-in Tracker Agent
    
    Responsibilities:
    - Real-time contractor location and status tracking
    - Arrival time monitoring with 15-minute buffer enforcement
    - Geographic route optimization and territory management
    - Check-in/check-out workflow coordination
    - Travel time calculations and schedule optimization
    - Status updates to clients and operations team
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("keith", business_context)
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        self.contractor_territories = CONTRACTOR_TERRITORIES
        self.checkin_buffer_minutes = settings.checkin_buffer_minutes
        
    @property
    def system_prompt(self) -> str:
        """Keith's system prompt with location tracking focus."""
        return f"""
        You are Keith, the Check-in Tracker for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: Real-time contractor coordination and geographic optimization specialist
        
        CORE RESPONSIBILITIES:
        1. Monitor contractor arrivals with 15-minute buffer enforcement
        2. Track real-time location and status throughout jobs
        3. Optimize routes and territory assignments for efficiency
        4. Coordinate check-in/check-out workflow with Discord integration
        5. Send arrival notifications to clients automatically
        6. Handle travel delays and schedule adjustments
        7. Monitor contractor productivity and time management
        
        CONTRACTOR TERRITORIES & PREFERENCES:
        - Jennifer: South metro preference, most reliable, $28/hr
        - Olga: East metro specialist, deep cleaning expert, $25/hr
        - Zhanna: Central metro focus, recurring service expert, $25/hr
        - Liuda: North metro ONLY, part-time availability, $30/hr
        
        TRACKING REQUIREMENTS:
        - 15-minute arrival buffer: Late if >15 min past scheduled time
        - Mandatory check-ins: Arrival, start cleaning, completion, departure
        - Client notifications: 30 minutes before arrival, on arrival, completion
        - Photo submissions: Required at completion for quality validation
        - Location accuracy: Within 100 meters of client address
        
        GEOGRAPHIC OPTIMIZATION:
        - Minimize travel time between jobs
        - Respect contractor territory preferences
        - Consider traffic patterns and peak hours
        - Optimize daily routes for maximum efficiency
        - Account for service duration variations
        
        COMMUNICATION PROTOCOLS:
        - Discord #✔️-job-check-ins for status updates
        - Automatic client SMS for arrival notifications
        - Operations alerts for delays or issues
        - Real-time status dashboard updates
        
        STATUS CATEGORIES:
        - Available: Ready for job assignment
        - En Route: Traveling to job location
        - Arrived: At client location, not started
        - Working: Actively cleaning
        - Completed: Job finished, awaiting photos
        - Departed: Left location, available for next job
        - Delayed: Running behind schedule
        - Issue: Problem requiring assistance
        
        ESCALATION TRIGGERS:
        - >15 minutes late without notification
        - No check-in after 30 minutes past scheduled start
        - Location discrepancies or GPS issues
        - Contractor requests assistance
        - Client complaints about arrival time
        
        You excel at keeping operations running smoothly through precise tracking and proactive communication.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Keith's tracking and coordination tools."""
        return [
            AgentTool(
                name="track_contractor_status",
                description="Track and update contractor location and status",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "status": {"type": "string", "enum": ["available", "en_route", "arrived", "working", "completed", "departed", "delayed", "issue"]},
                        "location": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}, "address": {"type": "string"}}},
                        "job_id": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "notes": {"type": "string"}
                    }
                },
                required=["contractor_id", "status"]
            ),
            AgentTool(
                name="send_arrival_notification",
                description="Send arrival notifications to clients and team",
                parameters={
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "contractor_id": {"type": "string"},
                        "notification_type": {"type": "string", "enum": ["30_min_warning", "arrived", "started", "completed"]},
                        "estimated_arrival": {"type": "string"},
                        "actual_arrival": {"type": "string"},
                        "message": {"type": "string"}
                    }
                },
                required=["client_id", "contractor_id", "notification_type"]
            ),
            AgentTool(
                name="optimize_route",
                description="Optimize contractor routes and territory assignments",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "job_list": {"type": "array", "items": {"type": "object"}},
                        "optimization_type": {"type": "string", "enum": ["daily_route", "territory_assignment", "emergency_reassign"]},
                        "constraints": {"type": "object"},
                        "priority_jobs": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["contractor_id", "job_list", "optimization_type"]
            ),
            AgentTool(
                name="monitor_arrival_compliance",
                description="Monitor and enforce 15-minute arrival buffer",
                parameters={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                        "scheduled_time": {"type": "string"},
                        "actual_arrival": {"type": "string"},
                        "buffer_minutes": {"type": "integer"},
                        "compliance_check": {"type": "boolean"}
                    }
                },
                required=["job_id", "scheduled_time"]
            ),
            AgentTool(
                name="handle_delay_escalation",
                description="Handle contractor delays and schedule adjustments",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "job_id": {"type": "string"},
                        "delay_reason": {"type": "string"},
                        "estimated_delay_minutes": {"type": "integer"},
                        "impact_assessment": {"type": "object"},
                        "proposed_solution": {"type": "string"}
                    }
                },
                required=["contractor_id", "job_id", "delay_reason", "estimated_delay_minutes"]
            ),
            AgentTool(
                name="generate_productivity_report",
                description="Generate contractor productivity and efficiency reports",
                parameters={
                    "type": "object",
                    "properties": {
                        "contractor_id": {"type": "string"},
                        "time_period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                        "metrics": {"type": "array", "items": {"type": "string"}},
                        "include_comparisons": {"type": "boolean"}
                    }
                },
                required=["contractor_id", "time_period"]
            ),
            AgentTool(
                name="coordinate_territory_coverage",
                description="Coordinate territory coverage and backup assignments",
                parameters={
                    "type": "object",
                    "properties": {
                        "territory": {"type": "string", "enum": ["north", "south", "east", "west", "central"]},
                        "coverage_gap": {"type": "object"},
                        "backup_contractors": {"type": "array", "items": {"type": "string"}},
                        "reassignment_needed": {"type": "boolean"}
                    }
                },
                required=["territory"]
            }
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Keith handles status updates, location tracking, and schedule coordination."""
        tracking_types = {
            MessageType.STATUS_UPDATE,
            MessageType.LOCATION_UPDATE,
            MessageType.CHECK_IN,
            MessageType.SCHEDULE_OPTIMIZATION
        }
        return message_type in tracking_types
    
    async def _handle_message_type(
        self, 
        message_type: MessageType, 
        content: str, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Handle tracking and coordination messages."""
        
        if message_type == MessageType.STATUS_UPDATE:
            return await self._handle_status_update(content, extracted_data)
        elif message_type == MessageType.LOCATION_UPDATE:
            return await self._handle_location_update(content, extracted_data)
        elif message_type == MessageType.CHECK_IN:
            return await self._handle_check_in(content, extracted_data)
        elif message_type == MessageType.SCHEDULE_OPTIMIZATION:
            return await self._handle_schedule_optimization(content, extracted_data)
        else:
            # Use AI for complex tracking decisions
            return await self._ai_tracking_response(content, extracted_data)
    
    async def _handle_status_update(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle contractor status updates."""
        contractor_id = extracted_data.get("contractor_id", "unknown")
        new_status = extracted_data.get("status", "unknown")
        job_id = extracted_data.get("job_id")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Update contractor status
            status_result = await self._tool_track_contractor_status(
                contractor_id=contractor_id,
                status=new_status,
                job_id=job_id,
                timestamp=datetime.now().isoformat(),
                notes=f"Status update from content: {content[:100]}"
            )
            actions_taken.append("status_updated")
            
            # Check for arrival compliance if status is "arrived"
            if new_status == "arrived" and job_id:
                compliance_result = await self._tool_monitor_arrival_compliance(
                    job_id=job_id,
                    scheduled_time=datetime.now().isoformat(),  # In production, get from database
                    actual_arrival=datetime.now().isoformat(),
                    buffer_minutes=self.checkin_buffer_minutes,
                    compliance_check=True
                )
                actions_taken.append("arrival_compliance_checked")
                
                # Send arrival notification
                if compliance_result.get("on_time", True):
                    await self._tool_send_arrival_notification(
                        client_id=f"client_{job_id}",  # In production, get from job record
                        contractor_id=contractor_id,
                        notification_type="arrived",
                        actual_arrival=datetime.now().isoformat()
                    )
                    actions_taken.append("arrival_notification_sent")
            
            # Discord check-in notification
            if self.discord_tools:
                await self.discord_tools.send_checkin_update(
                    f"✅ {contractor_id.title()}: {new_status.replace('_', ' ').title()}"
                    + (f" - Job {job_id}" if job_id else "")
                )
            
            response_text = f"""
            ✅ STATUS UPDATE PROCESSED
            
            Contractor: {contractor_id.title()}
            Status: {new_status.replace('_', ' ').title()}
            Job: {job_id or 'General status'}
            Time: {datetime.now().strftime('%H:%M')}
            
            {'✅ On time arrival' if new_status == 'arrived' else ''}
            """
            
            # Determine next steps based on status
            if new_status == "en_route":
                next_steps.append("Send 30-minute arrival warning to client")
            elif new_status == "arrived":
                next_steps.append("Monitor for start of work within 15 minutes")
            elif new_status == "completed":
                next_steps.append("Request photo submission for quality validation")
            elif new_status == "delayed":
                next_steps.append("Escalate delay and notify affected parties")
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="status_updated",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                metadata={"contractor_status": status_result}
            )
            
        except Exception as e:
            logger.error(f"Keith status update error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing status update: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_check_in(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle contractor check-in workflow."""
        contractor_id = extracted_data.get("contractor_id", "unknown")
        checkin_type = extracted_data.get("checkin_type", "arrival")
        job_id = extracted_data.get("job_id")
        location_data = extracted_data.get("location")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Process check-in based on type
            if checkin_type == "arrival":
                # Track arrival status
                await self._tool_track_contractor_status(
                    contractor_id=contractor_id,
                    status="arrived",
                    location=location_data,
                    job_id=job_id,
                    timestamp=datetime.now().isoformat()
                )
                
                # Send client notification
                await self._tool_send_arrival_notification(
                    client_id=f"client_{job_id}",
                    contractor_id=contractor_id,
                    notification_type="arrived",
                    actual_arrival=datetime.now().isoformat()
                )
                
                response_text = f"{contractor_id.title()} has arrived at the job site."
                next_steps.append("Monitor for work start within 15 minutes")
                
            elif checkin_type == "start_work":
                await self._tool_track_contractor_status(
                    contractor_id=contractor_id,
                    status="working",
                    job_id=job_id,
                    timestamp=datetime.now().isoformat()
                )
                
                response_text = f"{contractor_id.title()} has started cleaning."
                next_steps.append("Monitor progress and completion")
                
            elif checkin_type == "completion":
                await self._tool_track_contractor_status(
                    contractor_id=contractor_id,
                    status="completed",
                    job_id=job_id,
                    timestamp=datetime.now().isoformat()
                )
                
                response_text = f"{contractor_id.title()} has completed the job."
                next_steps.extend([
                    "Request photo submission",
                    "Send completion notification to client",
                    "Update contractor to available status"
                ])
            
            actions_taken.append(f"{checkin_type}_processed")
            
            # Discord notification
            if self.discord_tools:
                await self.discord_tools.send_checkin_update(
                    f"📍 {contractor_id.title()}: {checkin_type.replace('_', ' ').title()}"
                    + (f" - Job {job_id}" if job_id else "")
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="checkin_processed",
                response=response_text,
                actions_taken=actions_taken,
                next_steps=next_steps
            )
            
        except Exception as e:
            logger.error(f"Keith check-in error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing check-in: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_schedule_optimization(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle route optimization and territory management."""
        optimization_type = extracted_data.get("optimization_type", "daily_route")
        contractor_id = extracted_data.get("contractor_id")
        territory = extracted_data.get("territory", "central")
        
        actions_taken = []
        
        try:
            if optimization_type == "daily_route" and contractor_id:
                # Optimize daily route for contractor
                route_result = await self._tool_optimize_route(
                    contractor_id=contractor_id,
                    job_list=[],  # In production, get from database
                    optimization_type="daily_route",
                    constraints={"territory_preference": self.contractor_territories.get(contractor_id)}
                )
                actions_taken.append("route_optimized")
                
                response_text = f"""
                📍 ROUTE OPTIMIZED for {contractor_id.title()}
                
                Territory: {self.contractor_territories.get(contractor_id, 'flexible').title()}
                Optimized jobs: {route_result.get('job_count', 0)}
                Estimated travel time: {route_result.get('total_travel_time', 0)} minutes
                Efficiency improvement: {route_result.get('efficiency_gain', 0)}%
                """
                
            elif optimization_type == "territory_coverage":
                # Coordinate territory coverage
                coverage_result = await self._tool_coordinate_territory_coverage(
                    territory=territory,
                    coverage_gap={"time_slots": [], "contractor_shortage": False},
                    backup_contractors=[]
                )
                actions_taken.append("territory_coverage_coordinated")
                
                response_text = f"Territory coverage optimized for {territory} metro area."
            
            else:
                response_text = "Schedule optimization request processed."
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="optimization_completed",
                response=response_text.strip(),
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Keith optimization error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing optimization: {str(e)}",
                requires_escalation=True
            )
    
    async def _ai_tracking_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Use AI for complex tracking decisions."""
        messages = self._build_agent_prompt(content, extracted_data)
        
        # Add tracking context
        tracking_context = f"""
        CURRENT TRACKING CONTEXT:
        - 15-minute arrival buffer enforcement active
        - Contractor territories: {self.contractor_territories}
        - Real-time status monitoring enabled
        - Discord integration for team notifications
        """
        messages.append({"role": "system", "content": tracking_context})
        
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
                status="ai_tracking_response",
                response=ai_response["content"] or "Tracking decision processed",
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Keith AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing tracking request: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementation methods
    async def _tool_track_contractor_status(
        self,
        contractor_id: str,
        status: str,
        location: Dict[str, Any] = None,
        job_id: str = None,
        timestamp: str = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Track and update contractor location and status."""
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        status_update = {
            "contractor_id": contractor_id,
            "status": status,
            "location": location or {},
            "job_id": job_id,
            "timestamp": timestamp,
            "notes": notes,
            "updated_by": "keith",
            "territory": self.contractor_territories.get(contractor_id, "flexible")
        }
        
        # Store in database if available
        if self.database_tools:
            await self.database_tools.update_contractor_status(contractor_id, status_update)
        
        # Log status change
        logger.info(f"Contractor {contractor_id} status updated to {status}")
        
        return status_update
    
    async def _tool_send_arrival_notification(
        self,
        client_id: str,
        contractor_id: str,
        notification_type: str,
        estimated_arrival: str = None,
        actual_arrival: str = None,
        message: str = ""
    ) -> Dict[str, Any]:
        """Send arrival notifications to clients and team."""
        
        notification_templates = {
            "30_min_warning": f"{contractor_id.title()} is on the way! ETA: {estimated_arrival or '30 minutes'}",
            "arrived": f"{contractor_id.title()} has arrived and will begin shortly.",
            "started": f"{contractor_id.title()} has started your cleaning service.",
            "completed": f"Your cleaning is complete! {contractor_id.title()} has finished the job."
        }
        
        notification_content = message or notification_templates.get(notification_type, "Status update")
        
        notification_record = {
            "notification_id": f"NOTIF{datetime.now().strftime('%Y%m%d%H%M')}{client_id[-4:]}",
            "client_id": client_id,
            "contractor_id": contractor_id,
            "type": notification_type,
            "content": notification_content,
            "sent_by": "keith",
            "sent_at": datetime.now().isoformat(),
            "channel": "sms",  # Default to SMS for arrival notifications
            "status": "sent"
        }
        
        # In production, integrate with SMS service
        logger.info(f"Arrival notification sent: {notification_type} to {client_id}")
        
        return notification_record
    
    async def _tool_optimize_route(
        self,
        contractor_id: str,
        job_list: List[Dict],
        optimization_type: str,
        constraints: Dict[str, Any] = None,
        priority_jobs: List[str] = None
    ) -> Dict[str, Any]:
        """Optimize contractor routes and territory assignments."""
        
        if constraints is None:
            constraints = {}
        if priority_jobs is None:
            priority_jobs = []
        
        # Mock route optimization - in production, use actual mapping service
        optimization_result = {
            "contractor_id": contractor_id,
            "optimization_type": optimization_type,
            "original_job_count": len(job_list),
            "optimized_job_count": len(job_list),
            "territory_preference": self.contractor_territories.get(contractor_id, "flexible"),
            "total_travel_time": max(30, len(job_list) * 15),  # Mock travel time
            "efficiency_gain": 15.0,  # Mock efficiency improvement
            "optimized_route": [f"job_{i+1}" for i in range(len(job_list))],
            "constraints_applied": constraints,
            "priority_jobs_first": priority_jobs,
            "optimized_by": "keith",
            "optimized_at": datetime.now().isoformat()
        }
        
        return optimization_result
    
    async def _tool_monitor_arrival_compliance(
        self,
        job_id: str,
        scheduled_time: str,
        actual_arrival: str = None,
        buffer_minutes: int = None,
        compliance_check: bool = True
    ) -> Dict[str, Any]:
        """Monitor and enforce 15-minute arrival buffer."""
        
        if buffer_minutes is None:
            buffer_minutes = self.checkin_buffer_minutes
        
        if actual_arrival is None:
            actual_arrival = datetime.now().isoformat()
        
        # Parse times
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            actual_dt = datetime.fromisoformat(actual_arrival.replace('Z', '+00:00'))
            
            delay_minutes = (actual_dt - scheduled_dt).total_seconds() / 60
            on_time = delay_minutes <= buffer_minutes
            
        except Exception as e:
            logger.error(f"Time parsing error in arrival compliance: {e}")
            delay_minutes = 0
            on_time = True
        
        compliance_result = {
            "job_id": job_id,
            "scheduled_time": scheduled_time,
            "actual_arrival": actual_arrival,
            "delay_minutes": delay_minutes,
            "buffer_minutes": buffer_minutes,
            "on_time": on_time,
            "compliance_status": "compliant" if on_time else "violation",
            "checked_by": "keith",
            "checked_at": datetime.now().isoformat()
        }
        
        # Log compliance violations
        if not on_time:
            logger.warning(f"Arrival compliance violation: Job {job_id} - {delay_minutes:.1f} min late")
            
            # Escalate if significantly late
            if delay_minutes > buffer_minutes * 2:  # More than 30 minutes late
                compliance_result["escalation_required"] = True
        
        return compliance_result
    
    async def _tool_handle_delay_escalation(
        self,
        contractor_id: str,
        job_id: str,
        delay_reason: str,
        estimated_delay_minutes: int,
        impact_assessment: Dict[str, Any] = None,
        proposed_solution: str = ""
    ) -> Dict[str, Any]:
        """Handle contractor delays and schedule adjustments."""
        
        if impact_assessment is None:
            impact_assessment = {}
        
        escalation_record = {
            "escalation_id": f"ESC{datetime.now().strftime('%Y%m%d%H%M')}{contractor_id[-4:]}",
            "contractor_id": contractor_id,
            "job_id": job_id,
            "delay_reason": delay_reason,
            "estimated_delay_minutes": estimated_delay_minutes,
            "impact_assessment": impact_assessment,
            "proposed_solution": proposed_solution,
            "severity": "high" if estimated_delay_minutes > 30 else "medium",
            "escalated_by": "keith",
            "escalated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Notify via Discord if significant delay
        if self.discord_tools and estimated_delay_minutes > 15:
            await self.discord_tools.send_urgent_alert(
                f"🚨 Delay Alert: {contractor_id.title()} - {estimated_delay_minutes} min delay on Job {job_id}. Reason: {delay_reason}"
            )
        
        return escalation_record
    
    async def _tool_generate_productivity_report(
        self,
        contractor_id: str,
        time_period: str,
        metrics: List[str] = None,
        include_comparisons: bool = False
    ) -> Dict[str, Any]:
        """Generate contractor productivity and efficiency reports."""
        
        if metrics is None:
            metrics = ["on_time_percentage", "jobs_completed", "travel_efficiency", "client_satisfaction"]
        
        # Mock productivity data - in production, query actual database
        mock_data = {
            "jennifer": {"on_time_percentage": 96.5, "jobs_completed": 85, "travel_efficiency": 92.0, "client_satisfaction": 9.2},
            "olga": {"on_time_percentage": 94.2, "jobs_completed": 78, "travel_efficiency": 88.5, "client_satisfaction": 9.0},
            "zhanna": {"on_time_percentage": 97.1, "jobs_completed": 92, "travel_efficiency": 94.2, "client_satisfaction": 9.3},
            "liuda": {"on_time_percentage": 93.8, "jobs_completed": 65, "travel_efficiency": 85.0, "client_satisfaction": 8.9}
        }
        
        contractor_data = mock_data.get(contractor_id, {})
        
        productivity_report = {
            "contractor_id": contractor_id,
            "time_period": time_period,
            "metrics": {metric: contractor_data.get(metric, 0) for metric in metrics},
            "territory": self.contractor_territories.get(contractor_id, "flexible"),
            "report_generated_by": "keith",
            "report_generated_at": datetime.now().isoformat()
        }
        
        if include_comparisons:
            # Add team averages for comparison
            team_averages = {
                "on_time_percentage": 95.4,
                "jobs_completed": 80.0,
                "travel_efficiency": 89.9,
                "client_satisfaction": 9.1
            }
            productivity_report["team_comparisons"] = team_averages
        
        return productivity_report
    
    async def _tool_coordinate_territory_coverage(
        self,
        territory: str,
        coverage_gap: Dict[str, Any] = None,
        backup_contractors: List[str] = None,
        reassignment_needed: bool = False
    ) -> Dict[str, Any]:
        """Coordinate territory coverage and backup assignments."""
        
        if coverage_gap is None:
            coverage_gap = {}
        if backup_contractors is None:
            backup_contractors = []
        
        # Find primary and backup contractors for territory
        primary_contractors = {
            "north": ["liuda"],
            "south": ["jennifer"],
            "east": ["olga"],
            "central": ["zhanna"],
            "west": ["zhanna", "olga"]  # Flexible coverage
        }
        
        backup_options = {
            "north": ["zhanna"],  # Only Zhanna can backup North (Liuda is part-time)
            "south": ["zhanna", "olga"],
            "east": ["zhanna"],
            "central": ["jennifer", "olga"],
            "west": ["jennifer", "zhanna"]
        }
        
        coverage_result = {
            "territory": territory,
            "primary_contractors": primary_contractors.get(territory, []),
            "backup_contractors": backup_options.get(territory, []),
            "coverage_gap": coverage_gap,
            "reassignment_needed": reassignment_needed,
            "coverage_status": "adequate" if not reassignment_needed else "needs_backup",
            "coordinated_by": "keith",
            "coordinated_at": datetime.now().isoformat()
        }
        
        return coverage_result