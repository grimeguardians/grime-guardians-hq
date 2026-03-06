"""
Sophia - Booking Coordinator Agent
Client onboarding and relationship management specialist
Handles new prospects, quotes, scheduling, and client communication
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_agent import BaseAgent, AgentTool
from ..models.schemas import AgentResponse, BusinessContext
from ..models.types import MessageType, JobStatus, ServiceType
from ..core.pricing_engine import PricingEngine
from ..tools.discord_tools import DiscordTools
from ..tools.database_tools import DatabaseTools
from ..config.settings import get_settings, PRICING_STRUCTURE, ADD_ONS

logger = logging.getLogger(__name__)
settings = get_settings()


class SophiaBookingCoordinator(BaseAgent):
    """
    Sophia - Operations Scheduling Coordinator
    
    Responsibilities:
    - Appointment scheduling and logistics coordination
    - Contractor-client scheduling optimization
    - Service delivery coordination and timing
    - Appointment confirmation and scheduling changes
    - Operational workflow management between contractors and clients
    - Schedule optimization for maximum efficiency
    """
    
    def __init__(self, business_context: Optional[BusinessContext] = None):
        super().__init__("sophia", business_context)
        self.pricing_engine = PricingEngine()
        self.discord_tools = DiscordTools() if settings.enable_discord_integration else None
        self.database_tools = DatabaseTools() if settings.enable_database_operations else None
        
    @property
    def system_prompt(self) -> str:
        """Sophia's system prompt with client relationship focus."""
        return f"""
        You are Sophia, the Operations Scheduling Coordinator for Grime Guardians cleaning service.
        
        MISSION: "We clean like it's our name on the lease"
        YOUR ROLE: Operations scheduling and logistics coordination specialist
        
        CORE RESPONSIBILITIES:
        1. Coordinate appointment scheduling between clients and contractors
        2. Optimize contractor assignments based on location and availability
        3. Manage scheduling changes, cancellations, and rescheduling requests
        4. Ensure efficient service delivery timing and logistics
        5. Coordinate operational workflow for maximum efficiency
        6. Handle appointment confirmations and scheduling communications
        
        SCHEDULING PRIORITIES:
        - Contractor territory optimization (Jennifer: South, Olga: East, Zhanna: Central, Liuda: North only)
        - Service type duration planning (Move out: 4-6 hrs, Deep: 3-4 hrs, Recurring: 2-3 hrs)
        - Travel time optimization between appointments
        - Client timing preferences and availability windows
        - Emergency scheduling and same-day service coordination
        
        OPERATIONAL FOCUS:
        - Schedule confirmed services (quotes already provided by Dean's sales team)
        - Optimize contractor assignments for efficiency and client satisfaction
        - Coordinate timing for maximum operational efficiency
        - Handle scheduling logistics, not sales conversations
        - Ensure proper service delivery timing and coordination
        
        CONTRACTOR COORDINATION:
        - Jennifer: South metro preference, $28/hr, most reliable
        - Olga: East metro, $25/hr, deep cleaning specialist
        - Zhanna: Central metro, $25/hr, recurring client expert
        - Liuda: North metro only, $30/hr, part-time availability
        
        COMMUNICATION STYLE:
        - Efficient and organized
        - Clear about scheduling and logistics
        - Solution-oriented for timing conflicts
        - Detail-focused for appointment accuracy
        - Operationally focused, not sales-focused
        
        SCHEDULING COORDINATION:
        - Work with already-sold services from Dean's sales team
        - Focus on "when and who" not "what and how much"
        - Optimize contractor-client matching for efficiency
        - Ensure smooth operational flow from booking to completion
        - Coordinate timing for maximum satisfaction and efficiency
        
        OPERATIONAL PRIORITIES:
        1. Efficient contractor assignment based on location and specialization
        2. Optimal scheduling for travel time and service delivery
        3. Clear appointment confirmation and timing communication
        4. Proactive scheduling conflict resolution
        5. Smooth handoff to Keith for execution tracking
        6. Scheduling optimization for operational efficiency
        
        You excel at coordinating efficient service delivery through optimal scheduling and contractor assignment.
        """
    
    def _register_tools(self) -> List[AgentTool]:
        """Register Sophia's scheduling and coordination tools."""
        return [
            AgentTool(
                name="schedule_appointment",
                description="Schedule cleaning appointment with optimal contractor matching",
                parameters={
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "service_type": {"type": "string"},
                        "preferred_date": {"type": "string"},
                        "preferred_time": {"type": "string"},
                        "location_zone": {"type": "string", "enum": ["north", "south", "east", "west", "central"]},
                        "duration_hours": {"type": "number"},
                        "special_instructions": {"type": "string"},
                        "contractor_preference": {"type": "string"}
                    }
                },
                required=["client_id", "service_type", "preferred_date"]
            ),
            AgentTool(
                name="manage_client_profile",
                description="Create or update client profile with preferences and history",
                parameters={
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "action": {"type": "string", "enum": ["create", "update", "view"]},
                        "contact_info": {"type": "object"},
                        "service_preferences": {"type": "object"},
                        "cleaning_history": {"type": "array"},
                        "satisfaction_score": {"type": "number", "minimum": 1, "maximum": 10},
                        "notes": {"type": "string"}
                    }
                },
                required=["client_id", "action"]
            ),
            AgentTool(
                name="check_contractor_availability",
                description="Check contractor availability for scheduling optimization",
                parameters={
                    "type": "object",
                    "properties": {
                        "date_range": {"type": "object"},
                        "location_zone": {"type": "string"},
                        "service_duration": {"type": "number"},
                        "contractor_preferences": {"type": "array", "items": {"type": "string"}},
                        "skill_requirements": {"type": "array", "items": {"type": "string"}}
                    }
                },
                required=["date_range"]
            ),
            AgentTool(
                name="send_client_communication",
                description="Send personalized communication to clients",
                parameters={
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "communication_type": {"type": "string", "enum": ["quote", "confirmation", "reminder", "follow_up", "satisfaction"]},
                        "message_content": {"type": "string"},
                        "channel": {"type": "string", "enum": ["email", "sms", "phone"]},
                        "priority": {"type": "string", "enum": ["low", "normal", "high"]}
                    }
                },
                required=["client_id", "communication_type", "message_content"]
            ),
            AgentTool(
                name="track_conversion_metrics",
                description="Track prospect conversion and client satisfaction metrics",
                parameters={
                    "type": "object",
                    "properties": {
                        "metric_type": {"type": "string", "enum": ["conversion_rate", "quote_acceptance", "client_retention", "satisfaction_score"]},
                        "time_period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                        "client_segment": {"type": "string"},
                        "value": {"type": "number"}
                    }
                },
                required=["metric_type", "time_period"]
            )
        ]
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Sophia handles prospect inquiries, booking, and client management."""
        booking_types = {
            MessageType.JOB_ASSIGNMENT,
            MessageType.NEW_PROSPECT_INQUIRY,
            MessageType.SCHEDULE_CHANGE_REQUEST,
            MessageType.BOOKING_REQUEST
        }
        return message_type in booking_types
    
    async def _handle_message_type(
        self, 
        message_type: MessageType, 
        content: str, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Handle client-related messages."""
        
        if message_type == MessageType.NEW_PROSPECT_INQUIRY:
            return await self._handle_prospect_inquiry(content, extracted_data)
        elif message_type == MessageType.JOB_ASSIGNMENT:
            return await self._handle_job_assignment(content, extracted_data)
        elif message_type == MessageType.SCHEDULE_CHANGE_REQUEST:
            return await self._handle_schedule_change(content, extracted_data)
        elif message_type == MessageType.BOOKING_REQUEST:
            return await self._handle_booking_request(content, extracted_data)
        else:
            # Use AI for complex client interactions
            return await self._ai_client_response(content, extracted_data)
    
    async def _handle_prospect_inquiry(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle new prospect inquiries with quote generation."""
        service_type = extracted_data.get("service_type", "one_time")
        bedrooms = extracted_data.get("bedrooms", 3)  # Default assumption
        location = extracted_data.get("location", "central")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Generate quote using pricing engine
            quote_params = {
                "service_type": service_type,
                "bedrooms": bedrooms,
                "full_bathrooms": 2,  # Default assumption
                "half_bathrooms": 1,
                "add_ons": [],
                "modifiers": []
            }
            
            quote_result = await self._tool_generate_quote(**quote_params)
            actions_taken.append("quote_generated")
            
            # Check contractor availability for location
            availability_result = await self._tool_check_contractor_availability({
                "date_range": {"start": datetime.now().isoformat(), "days": 7},
                "location_zone": location,
                "service_duration": 3.0
            })
            actions_taken.append("availability_checked")
            
            # Prepare response with value positioning
            response_text = f"""
            Thank you for your interest in Grime Guardians! We clean like it's our name on the lease.
            
            QUOTE DETAILS:
            Service: {service_type.replace('_', ' ').title()}
            Bedrooms: {bedrooms}
            Price: ${quote_result['total_price']:.2f} (includes 8.125% tax)
            
            NEXT STEPS:
            1. Available dates in {location} metro: {availability_result['available_slots'][:3]}
            2. Preferred contractor recommendations provided
            3. Service can be scheduled within 24-48 hours
            
            Our premium service includes thorough cleaning with meticulous attention to detail. 
            We're fully insured and bonded for your peace of mind.
            """
            
            next_steps.extend([
                "Send formal quote via email",
                "Schedule follow-up call within 2 hours",
                "Create client profile for preference tracking"
            ])
            
            # Send quote via Discord notification
            if self.discord_tools:
                await self.discord_tools.send_job_notification(
                    f"📋 New prospect quote generated: {service_type} - ${quote_result['total_price']:.2f}"
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="prospect_quoted",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                metadata={"quote": quote_result, "availability": availability_result}
            )
            
        except Exception as e:
            logger.error(f"Sophia prospect inquiry error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing prospect inquiry: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_booking_request(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle booking requests with scheduling optimization."""
        client_id = extracted_data.get("client_id", f"client_{datetime.now().strftime('%Y%m%d_%H%M')}")
        service_type = extracted_data.get("service_type", "one_time")
        preferred_date = extracted_data.get("preferred_date")
        location_zone = extracted_data.get("location_zone", "central")
        
        actions_taken = []
        next_steps = []
        
        try:
            # Schedule appointment with contractor optimization
            scheduling_params = {
                "client_id": client_id,
                "service_type": service_type,
                "preferred_date": preferred_date or (datetime.now() + timedelta(days=2)).isoformat(),
                "location_zone": location_zone,
                "duration_hours": 3.0
            }
            
            scheduling_result = await self._tool_schedule_appointment(**scheduling_params)
            actions_taken.append("appointment_scheduled")
            
            # Update client profile
            if self.database_tools:
                profile_result = await self._tool_manage_client_profile(
                    client_id=client_id,
                    action="update",
                    service_preferences={"service_type": service_type, "location": location_zone}
                )
                actions_taken.append("client_profile_updated")
            
            # Send confirmation
            confirmation_params = {
                "client_id": client_id,
                "communication_type": "confirmation",
                "message_content": f"Appointment confirmed for {scheduling_result['scheduled_date']} with {scheduling_result['assigned_contractor']}",
                "channel": "email"
            }
            
            await self._tool_send_client_communication(**confirmation_params)
            actions_taken.append("confirmation_sent")
            
            response_text = f"""
            ✅ APPOINTMENT CONFIRMED
            
            Date: {scheduling_result['scheduled_date']}
            Time: {scheduling_result['scheduled_time']}
            Service: {service_type.replace('_', ' ').title()}
            Contractor: {scheduling_result['assigned_contractor']}
            Location: {location_zone.title()} metro
            
            Your contractor will arrive within a 2-hour window and text 30 minutes before arrival.
            We guarantee our work and will return if anything isn't perfect.
            """
            
            next_steps.extend([
                "Send appointment reminder 24 hours before",
                "Coordinate with Keith for check-in tracking",
                "Schedule satisfaction follow-up"
            ])
            
            # Notify team via Discord
            if self.discord_tools:
                await self.discord_tools.send_job_notification(
                    f"📅 Appointment scheduled: {client_id} - {service_type} on {scheduling_result['scheduled_date']}"
                )
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="appointment_scheduled",
                response=response_text.strip(),
                actions_taken=actions_taken,
                next_steps=next_steps,
                metadata={"appointment": scheduling_result}
            )
            
        except Exception as e:
            logger.error(f"Sophia booking error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing booking request: {str(e)}",
                requires_escalation=True
            )
    
    async def _handle_schedule_change(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Handle schedule changes with minimal disruption."""
        action_type = extracted_data.get("action_type", "reschedule")
        urgency = extracted_data.get("urgency", "medium")
        client_id = extracted_data.get("client_id")
        
        actions_taken = []
        next_steps = []
        
        if action_type == "cancel":
            response_text = "We understand cancellations happen. Your appointment has been cancelled with no penalty."
            actions_taken.append("appointment_cancelled")
            next_steps.append("Offer rescheduling options")
            
        elif action_type == "reschedule":
            # Check new availability
            availability_result = await self._tool_check_contractor_availability({
                "date_range": {"start": datetime.now().isoformat(), "days": 14},
                "location_zone": "central"  # Default
            })
            
            response_text = f"""
            No problem! We can reschedule your appointment.
            
            Available options:
            {chr(10).join(availability_result['available_slots'][:5])}
            
            Which date and time works best for you?
            """
            actions_taken.extend(["reschedule_options_provided", "availability_checked"])
            next_steps.append("Confirm new appointment once client selects")
        
        # Handle urgency
        if urgency == "high":
            next_steps.append("Priority handling - respond within 1 hour")
            if self.discord_tools:
                await self.discord_tools.send_urgent_alert(
                    f"🚨 Urgent schedule change: {action_type} for client {client_id}"
                )
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="schedule_change_handled",
            response=response_text,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
    
    async def _ai_client_response(self, content: str, extracted_data: Dict[str, Any]) -> AgentResponse:
        """Use AI for complex client interactions."""
        messages = self._build_agent_prompt(content, extracted_data)
        
        # Add client relationship context
        client_context = f"""
        CURRENT CLIENT CONTEXT:
        - Premium service positioning: Quality justifies pricing
        - Response time target: Within 2 hours during business hours
        - Always apply 8.125% tax to all quotes
        - Focus on value: thoroughness, reliability, peace of mind
        - Coordinate with contractors based on location preferences
        """
        messages.append({"role": "system", "content": client_context})
        
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
                status="ai_client_response",
                response=ai_response["content"] or "Client interaction processed professionally",
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Sophia AI response error: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing client interaction: {str(e)}",
                requires_escalation=True
            )
    
    # Tool implementation methods
    async def _tool_generate_quote(
        self, 
        service_type: str, 
        bedrooms: int = 3, 
        full_bathrooms: int = 2, 
        half_bathrooms: int = 1,
        square_feet: int = 0,
        add_ons: List[str] = None,
        modifiers: List[str] = None,
        client_id: str = None
    ) -> Dict[str, Any]:
        """Generate accurate pricing quote using the pricing engine."""
        
        if add_ons is None:
            add_ons = []
        if modifiers is None:
            modifiers = []
        
        # Use the pricing engine for accurate calculations
        quote_result = await self.pricing_engine.calculate_job_pricing(
            service_type=service_type,
            bedrooms=bedrooms,
            full_bathrooms=full_bathrooms,
            half_bathrooms=half_bathrooms,
            square_feet=square_feet,
            add_ons=add_ons,
            modifiers=modifiers
        )
        
        # Add Sophia-specific enhancements
        quote_result.update({
            "generated_by": "sophia",
            "generated_at": datetime.now().isoformat(),
            "client_id": client_id,
            "quote_id": f"GG{datetime.now().strftime('%Y%m%d%H%M')}{bedrooms}",
            "valid_until": (datetime.now() + timedelta(days=7)).isoformat(),
            "service_positioning": "Premium residential cleaning with meticulous attention to detail"
        })
        
        return quote_result
    
    async def _tool_schedule_appointment(
        self,
        client_id: str,
        service_type: str,
        preferred_date: str,
        preferred_time: str = "09:00",
        location_zone: str = "central",
        duration_hours: float = 3.0,
        special_instructions: str = "",
        contractor_preference: str = ""
    ) -> Dict[str, Any]:
        """Schedule appointment with optimal contractor matching."""
        
        # Contractor optimization based on location and specialization
        contractor_map = {
            "south": "jennifer",  # South metro preference, most reliable
            "east": "olga",       # East metro, deep cleaning specialist
            "central": "zhanna",  # Central metro, recurring expert
            "north": "liuda",     # North metro only, part-time
            "west": "zhanna"      # Default to central for west
        }
        
        # Select optimal contractor
        assigned_contractor = contractor_preference or contractor_map.get(location_zone, "zhanna")
        
        # Parse preferred date
        try:
            scheduled_date = datetime.fromisoformat(preferred_date.replace('Z', '+00:00'))
        except:
            scheduled_date = datetime.now() + timedelta(days=2)
        
        scheduling_result = {
            "appointment_id": f"APP{datetime.now().strftime('%Y%m%d%H%M')}{client_id[-4:]}",
            "client_id": client_id,
            "service_type": service_type,
            "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
            "scheduled_time": preferred_time,
            "assigned_contractor": assigned_contractor,
            "location_zone": location_zone,
            "duration_hours": duration_hours,
            "special_instructions": special_instructions,
            "status": "confirmed",
            "created_by": "sophia",
            "created_at": datetime.now().isoformat()
        }
        
        # Store in database if available
        if self.database_tools:
            await self.database_tools.create_job(scheduling_result)
        
        return scheduling_result
    
    async def _tool_manage_client_profile(
        self,
        client_id: str,
        action: str,
        contact_info: Dict[str, Any] = None,
        service_preferences: Dict[str, Any] = None,
        cleaning_history: List[Dict] = None,
        satisfaction_score: float = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Manage client profiles and preferences."""
        
        if action == "create":
            profile_data = {
                "client_id": client_id,
                "created_by": "sophia",
                "created_at": datetime.now().isoformat(),
                "contact_info": contact_info or {},
                "service_preferences": service_preferences or {},
                "cleaning_history": cleaning_history or [],
                "satisfaction_score": satisfaction_score,
                "notes": notes,
                "status": "active"
            }
            
            if self.database_tools:
                await self.database_tools.create_client(profile_data)
            
            return {"action": "created", "client_id": client_id, "profile": profile_data}
        
        elif action == "update":
            update_data = {
                "updated_by": "sophia",
                "updated_at": datetime.now().isoformat()
            }
            
            if service_preferences:
                update_data["service_preferences"] = service_preferences
            if satisfaction_score:
                update_data["satisfaction_score"] = satisfaction_score
            if notes:
                update_data["notes"] = notes
            
            if self.database_tools:
                await self.database_tools.update_client(client_id, update_data)
            
            return {"action": "updated", "client_id": client_id, "updates": update_data}
        
        elif action == "view":
            if self.database_tools:
                profile = await self.database_tools.get_client(client_id)
                return {"action": "retrieved", "client_id": client_id, "profile": profile}
            
            return {"action": "view", "client_id": client_id, "profile": "Database not available"}
    
    async def _tool_check_contractor_availability(
        self,
        date_range: Dict[str, Any],
        location_zone: str = "central",
        service_duration: float = 3.0,
        contractor_preferences: List[str] = None,
        skill_requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Check contractor availability for optimal scheduling."""
        
        # Mock availability data - in production, this would query actual schedules
        base_date = datetime.now()
        available_slots = []
        
        for i in range(1, 8):  # Next 7 days
            check_date = base_date + timedelta(days=i)
            if check_date.weekday() < 5:  # Monday-Friday
                available_slots.extend([
                    f"{check_date.strftime('%Y-%m-%d')} 09:00-12:00",
                    f"{check_date.strftime('%Y-%m-%d')} 13:00-16:00"
                ])
        
        # Optimal contractor recommendations based on location
        contractor_recommendations = {
            "south": ["jennifer"],
            "east": ["olga"],
            "central": ["zhanna", "olga"],
            "north": ["liuda"],
            "west": ["zhanna"]
        }
        
        return {
            "location_zone": location_zone,
            "available_slots": available_slots[:10],  # Top 10 slots
            "recommended_contractors": contractor_recommendations.get(location_zone, ["zhanna"]),
            "service_duration": service_duration,
            "checked_at": datetime.now().isoformat()
        }
    
    async def _tool_send_client_communication(
        self,
        client_id: str,
        communication_type: str,
        message_content: str,
        channel: str = "email",
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send personalized communication to clients."""
        
        communication_record = {
            "communication_id": f"COMM{datetime.now().strftime('%Y%m%d%H%M')}{client_id[-4:]}",
            "client_id": client_id,
            "type": communication_type,
            "channel": channel,
            "content": message_content,
            "priority": priority,
            "sent_by": "sophia",
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        # Log communication for tracking
        logger.info(f"Client communication sent: {communication_type} to {client_id} via {channel}")
        
        # In production, integrate with email/SMS services
        return communication_record
    
    async def _tool_track_conversion_metrics(
        self,
        metric_type: str,
        time_period: str,
        client_segment: str = "all",
        value: float = None
    ) -> Dict[str, Any]:
        """Track prospect conversion and client satisfaction metrics."""
        
        # Mock metrics data - in production, query actual database
        mock_metrics = {
            "conversion_rate": {"daily": 15.5, "weekly": 18.2, "monthly": 21.0},
            "quote_acceptance": {"daily": 65.0, "weekly": 62.5, "monthly": 68.0},
            "client_retention": {"daily": 95.0, "weekly": 92.0, "monthly": 89.0},
            "satisfaction_score": {"daily": 9.2, "weekly": 9.1, "monthly": 9.0}
        }
        
        current_value = mock_metrics.get(metric_type, {}).get(time_period, 0.0)
        
        metric_result = {
            "metric_type": metric_type,
            "time_period": time_period,
            "client_segment": client_segment,
            "current_value": current_value,
            "target_value": self._get_metric_target(metric_type),
            "performance_status": "on_track" if current_value >= self._get_metric_target(metric_type) else "needs_attention",
            "tracked_by": "sophia",
            "tracked_at": datetime.now().isoformat()
        }
        
        return metric_result
    
    def _get_metric_target(self, metric_type: str) -> float:
        """Get target values for tracking metrics."""
        targets = {
            "conversion_rate": 20.0,  # 20% prospect conversion
            "quote_acceptance": 60.0,  # 60% quote acceptance
            "client_retention": 90.0,  # 90% client retention
            "satisfaction_score": 9.0   # 9/10 satisfaction
        }
        return targets.get(metric_type, 0.0)