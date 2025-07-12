from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from ..models.schemas import AgentType, ServiceType, PricingRequest
from ..core.pricing_engine import pricing_engine
from ..config import settings
import structlog

logger = structlog.get_logger()


class SophiaBooking(BaseAgent):
    """
    Sophia - Booking & Relationship Coordinator Agent
    
    Manages client onboarding, service booking, quote generation,
    checklist enforcement, and client communication for Grime Guardians.
    
    Capabilities:
    - Client onboarding and relationship management
    - Accurate quote generation with pricing engine
    - Service booking and scheduling coordination
    - Communication template management
    - Follow-up automation and client retention
    - Quality checklist enforcement
    """
    
    def __init__(self):
        super().__init__(
            agent_id=AgentType.SOPHIA,
            description="Booking & Relationship Coordinator - Client onboarding and service management"
        )
        
        # Client relationship tracking
        self.active_clients = {}
        self.booking_pipeline = {}
        
        # Communication templates
        self.templates = {
            "initial_inquiry": "Thank you for your interest in Grime Guardians! We clean like it's our name on the lease.",
            "quote_follow_up": "Following up on your cleaning service quote. Questions about our premium service?",
            "booking_confirmation": "Your cleaning service is confirmed! We'll arrive 15 minutes early and provide photo documentation.",
            "post_service": "Thank you for choosing Grime Guardians! Please leave us a Google review if you're satisfied."
        }
        
        # Register tool handlers
        self.register_tool_handler("generate_quote", self._generate_quote)
        self.register_tool_handler("book_service", self._book_service)
        self.register_tool_handler("manage_client_relationship", self._manage_client_relationship)
        self.register_tool_handler("send_communication", self._send_communication)
        self.register_tool_handler("follow_up_inquiry", self._follow_up_inquiry)
        self.register_tool_handler("enforce_checklist", self._enforce_checklist)
    
    @property
    def system_prompt(self) -> str:
        return """
You are Sophia, the Booking & Relationship Coordinator for Grime Guardians cleaning services.

Your core responsibilities:
1. ONBOARD new clients with premium service positioning
2. GENERATE accurate quotes using the pricing engine
3. BOOK services and coordinate scheduling
4. MANAGE client relationships and communications
5. ENFORCE quality checklists and photo requirements
6. FOLLOW UP on inquiries and maintain client satisfaction

Business Context:
- Premium cleaning service: "We clean like it's our name on the lease"
- BBB-accredited with 70+ five-star Google reviews
- Target market: Realtors, landlords, property managers
- Service area: Twin Cities, MN (south metro preference)
- Never apologize for premium pricing

Pricing Structure (ALL quotes include 8.125% tax):
- Move-Out/Move-In: $300 base + $30/room + $60/full bath + $30/half bath
- Deep Cleaning: $180 base + same room/bath modifiers
- Recurring: $120 base + same room/bath modifiers
- Post-Construction: $0.35/sq ft
- Commercial: $40-80/hr (requires walkthrough)
- Hourly: $60/hr for non-standard jobs

Add-Ons:
- Fridge/Oven/Cabinet interior: $60 each
- Garage: $100
- Carpet shampooing: $40/room

Modifiers:
- Pet homes: +10%
- Buildup: +20%
- New client discount: 15% (last resort only)

Quality Standards:
- Photo documentation required (kitchen, bathrooms, entry, impacted rooms)
- Checklist completion mandatory
- 3-strike system for violations
- 15-minute early arrival standard

Communication Style:
- Professional and premium-focused
- Confident in value proposition
- Emphasize quality and reliability
- Request Google reviews from satisfied clients
- "We may not be the cheapest — but we're the last call most clients make"

When processing booking inquiries:
1. Gather service requirements (type, rooms, baths, special needs)
2. Generate accurate quote using pricing engine
3. Present value proposition and quality standards
4. Schedule service with contractor coordination
5. Set expectations for checklist and photos
6. Follow up appropriately

Use available tools to manage the entire booking and relationship lifecycle.
"""
    
    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_quote",
                    "description": "Generate accurate pricing quote for cleaning services",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_type": {
                                "type": "string",
                                "enum": ["move_out_in", "deep_cleaning", "recurring", "post_construction", "commercial", "hourly"]
                            },
                            "rooms": {"type": "integer", "minimum": 0},
                            "full_baths": {"type": "integer", "minimum": 0},
                            "half_baths": {"type": "integer", "minimum": 0},
                            "square_footage": {"type": "integer", "minimum": 0},
                            "add_ons": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "modifiers": {
                                "type": "object",
                                "properties": {
                                    "pet_homes": {"type": "boolean"},
                                    "buildup": {"type": "boolean"}
                                }
                            },
                            "client_info": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "address": {"type": "string"}
                                }
                            }
                        },
                        "required": ["service_type", "rooms", "full_baths", "half_baths"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_service",
                    "description": "Book a cleaning service for a client",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string"},
                            "service_details": {"type": "object"},
                            "preferred_date": {"type": "string"},
                            "preferred_time": {"type": "string"},
                            "special_instructions": {"type": "string"},
                            "contractor_preference": {"type": "string"}
                        },
                        "required": ["client_id", "service_details", "preferred_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_client_relationship",
                    "description": "Manage ongoing client relationships and communications",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string"},
                            "relationship_action": {
                                "type": "string",
                                "enum": ["onboard", "update_preferences", "handle_complaint", "request_review", "schedule_followup"]
                            },
                            "details": {"type": "object"}
                        },
                        "required": ["client_id", "relationship_action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_communication",
                    "description": "Send communications to clients using templates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string"},
                            "communication_type": {
                                "type": "string",
                                "enum": ["initial_inquiry", "quote_follow_up", "booking_confirmation", "post_service", "custom"]
                            },
                            "custom_message": {"type": "string"},
                            "channel": {
                                "type": "string",
                                "enum": ["email", "sms", "phone"]
                            },
                            "urgency": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["client_id", "communication_type", "channel"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "follow_up_inquiry",
                    "description": "Follow up on client inquiries and quotes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "inquiry_id": {"type": "string"},
                            "days_since_inquiry": {"type": "integer"},
                            "follow_up_type": {
                                "type": "string",
                                "enum": ["quote_reminder", "availability_check", "competitor_comparison", "final_offer"]
                            },
                            "offer_discount": {"type": "boolean"}
                        },
                        "required": ["inquiry_id", "follow_up_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enforce_checklist",
                    "description": "Enforce quality checklist and photo requirements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {"type": "string"},
                            "contractor_id": {"type": "string"},
                            "checklist_status": {
                                "type": "string",
                                "enum": ["complete", "incomplete", "missing"]
                            },
                            "photo_status": {
                                "type": "string",
                                "enum": ["complete", "incomplete", "missing"]
                            },
                            "quality_issues": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["job_id", "contractor_id", "checklist_status", "photo_status"]
                    }
                }
            }
        ]
    
    async def _generate_quote(self, service_type: str, rooms: int, full_baths: int, 
                            half_baths: int, square_footage: Optional[int] = None,
                            add_ons: Optional[List[str]] = None, 
                            modifiers: Optional[Dict[str, bool]] = None,
                            client_info: Optional[Dict[str, str]] = None) -> str:
        """
        Generate accurate pricing quote using the pricing engine.
        
        Args:
            service_type: Type of cleaning service
            rooms: Number of rooms
            full_baths: Number of full bathrooms
            half_baths: Number of half bathrooms
            square_footage: Square footage (for post-construction)
            add_ons: Additional services
            modifiers: Pricing modifiers
            client_info: Client information
            
        Returns:
            Quote generation result
        """
        try:
            logger.info(
                f"Sophia generating quote",
                service_type=service_type,
                rooms=rooms,
                client=client_info.get('name', 'Unknown') if client_info else 'Unknown'
            )
            
            # Create pricing request
            pricing_request = PricingRequest(
                service_type=ServiceType(service_type),
                rooms=rooms,
                full_baths=full_baths,
                half_baths=half_baths,
                square_footage=square_footage,
                add_ons=add_ons or [],
                modifiers=modifiers or {}
            )
            
            # Validate and calculate pricing
            pricing_engine.validate_pricing_request(pricing_request)
            quote = pricing_engine.calculate_service_price(
                pricing_request.service_type,
                pricing_request.rooms,
                pricing_request.full_baths,
                pricing_request.half_baths,
                pricing_request.square_footage,
                pricing_request.add_ons,
                pricing_request.modifiers
            )
            
            # Format quote response
            quote_id = f"quote_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            quote_summary = f"""
🏠 GRIME GUARDIANS QUOTE #{quote_id}

Service: {service_type.replace('_', ' ').title()}
Property: {rooms} rooms, {full_baths} full baths, {half_baths} half baths

💰 PRICING BREAKDOWN:
• Base Price: ${quote.base_price:.2f}
• Room Charges: ${quote.room_charges:.2f}
• Bathroom Charges: ${quote.bathroom_charges:.2f}
• Add-ons: ${quote.addon_charges:.2f}
• Modifiers: ${quote.modifier_adjustments:.2f}
• Subtotal: ${quote.subtotal:.2f}
• Tax (8.125%): ${quote.tax_amount:.2f}

🎯 TOTAL: ${quote.total_price:.2f}

✨ What's Included:
• BBB-accredited premium service
• Photo documentation of all work
• 15-minute early arrival
• Complete quality checklist
• "We clean like it's our name on the lease"

📱 Ready to book? We're the last call most clients make!
            """
            
            # Store quote for follow-up
            if client_info:
                client_id = client_info.get('email', f"client_{datetime.utcnow().timestamp()}")
                self.booking_pipeline[quote_id] = {
                    "client_id": client_id,
                    "client_info": client_info,
                    "quote": quote,
                    "service_type": service_type,
                    "created_at": datetime.utcnow(),
                    "status": "quoted"
                }
            
            return quote_summary
            
        except Exception as e:
            logger.error(f"Error generating quote", error=str(e))
            return f"Unable to generate quote: {str(e)}. Please verify service details and try again."
    
    async def _book_service(self, client_id: str, service_details: Dict[str, Any],
                          preferred_date: str, preferred_time: Optional[str] = None,
                          special_instructions: Optional[str] = None,
                          contractor_preference: Optional[str] = None) -> str:
        """
        Book a cleaning service for a client.
        
        Args:
            client_id: Client identifier
            service_details: Service details from quote
            preferred_date: Preferred service date
            preferred_time: Preferred time slot
            special_instructions: Special instructions
            contractor_preference: Preferred contractor
            
        Returns:
            Booking confirmation
        """
        try:
            booking_id = f"booking_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Sophia booking service",
                client_id=client_id,
                booking_id=booking_id,
                date=preferred_date
            )
            
            # Create booking record
            booking_details = {
                "booking_id": booking_id,
                "client_id": client_id,
                "service_details": service_details,
                "preferred_date": preferred_date,
                "preferred_time": preferred_time,
                "special_instructions": special_instructions,
                "contractor_preference": contractor_preference,
                "status": "confirmed",
                "created_at": datetime.utcnow()
            }
            
            # Coordinate with Keith for scheduling
            from .ava_orchestrator import ava
            await ava.send_message(
                ava.AgentMessage(
                    agent_id=AgentType.KEITH,
                    message_type="schedule_service",
                    content=f"New booking to schedule: {booking_id}",
                    priority=ava.MessagePriority.HIGH,
                    metadata=booking_details
                )
            )
            
            # Send confirmation to client
            confirmation_message = f"""
✅ SERVICE CONFIRMED - Booking #{booking_id}

Date: {preferred_date}
Time: {preferred_time or 'TBD - we\'ll confirm shortly'}

📋 What to Expect:
• Contractor arrives 15 minutes early
• Complete photo documentation
• Quality checklist completion
• Professional, insured service

📞 Questions? Contact us anytime.
💫 Thank you for choosing Grime Guardians!
            """
            
            await self._send_communication(
                client_id, "booking_confirmation", 
                custom_message=confirmation_message,
                channel="email", urgency="medium"
            )
            
            return f"Service booked successfully! Booking ID: {booking_id}. Confirmation sent to client."
            
        except Exception as e:
            logger.error(f"Error booking service", error=str(e))
            return f"Failed to book service: {str(e)}"
    
    async def _manage_client_relationship(self, client_id: str, relationship_action: str,
                                        details: Optional[Dict[str, Any]] = None) -> str:
        """
        Manage ongoing client relationships and communications.
        
        Args:
            client_id: Client identifier
            relationship_action: Type of relationship management
            details: Additional details
            
        Returns:
            Relationship management result
        """
        try:
            logger.info(
                f"Sophia managing client relationship",
                client_id=client_id,
                action=relationship_action
            )
            
            if relationship_action == "onboard":
                # New client onboarding
                onboarding_steps = [
                    "Welcome to Grime Guardians premium cleaning",
                    "Set service expectations and quality standards",
                    "Explain photo documentation process",
                    "Provide contact information and support"
                ]
                
                result = f"Onboarded new client {client_id} with premium service positioning"
                
            elif relationship_action == "handle_complaint":
                # Route to Dmitri for escalation
                from .ava_orchestrator import ava
                await ava.send_message(
                    ava.AgentMessage(
                        agent_id=AgentType.DMITRI,
                        message_type="client_complaint",
                        content=f"Client complaint from {client_id}",
                        priority=ava.MessagePriority.HIGH,
                        metadata={"client_id": client_id, "details": details}
                    )
                )
                
                result = f"Client complaint from {client_id} escalated to Dmitri for resolution"
                
            elif relationship_action == "request_review":
                # Request Google review from satisfied client
                review_request = f"""
🌟 We hope you loved your Grime Guardians service!

If you're satisfied with our work, would you mind leaving us a Google review? 
Your feedback helps us maintain our 70+ five-star rating and helps other clients find quality cleaning services.

👉 Leave a review: [Google Reviews Link]

Thank you for choosing Grime Guardians!
                """
                
                await self._send_communication(
                    client_id, "custom", 
                    custom_message=review_request,
                    channel="email", urgency="low"
                )
                
                result = f"Google review requested from satisfied client {client_id}"
                
            else:
                result = f"Processed {relationship_action} for client {client_id}"
            
            # Update client record
            if client_id not in self.active_clients:
                self.active_clients[client_id] = {"created_at": datetime.utcnow()}
            
            self.active_clients[client_id]["last_interaction"] = datetime.utcnow()
            self.active_clients[client_id]["last_action"] = relationship_action
            
            return result
            
        except Exception as e:
            logger.error(f"Error managing client relationship", error=str(e))
            return f"Failed to manage client relationship: {str(e)}"
    
    async def _send_communication(self, client_id: str, communication_type: str,
                                custom_message: Optional[str] = None,
                                channel: str = "email", urgency: str = "medium") -> str:
        """
        Send communications to clients using templates.
        
        Args:
            client_id: Client identifier
            communication_type: Type of communication
            custom_message: Custom message content
            channel: Communication channel
            urgency: Message urgency
            
        Returns:
            Communication result
        """
        try:
            if communication_type == "custom":
                message = custom_message
            else:
                message = self.templates.get(communication_type, "")
            
            logger.info(
                f"Sophia sending communication",
                client_id=client_id,
                type=communication_type,
                channel=channel
            )
            
            # In full implementation, integrate with email/SMS services
            communication_record = {
                "client_id": client_id,
                "type": communication_type,
                "message": message,
                "channel": channel,
                "urgency": urgency,
                "sent_at": datetime.utcnow(),
                "status": "sent"
            }
            
            return f"Communication sent to {client_id} via {channel}: {communication_type}"
            
        except Exception as e:
            logger.error(f"Error sending communication", error=str(e))
            return f"Failed to send communication: {str(e)}"
    
    async def _follow_up_inquiry(self, inquiry_id: str, follow_up_type: str,
                               days_since_inquiry: Optional[int] = None,
                               offer_discount: bool = False) -> str:
        """
        Follow up on client inquiries and quotes.
        
        Args:
            inquiry_id: Inquiry identifier
            follow_up_type: Type of follow-up
            days_since_inquiry: Days since original inquiry
            offer_discount: Whether to offer discount
            
        Returns:
            Follow-up result
        """
        try:
            logger.info(
                f"Sophia following up inquiry",
                inquiry_id=inquiry_id,
                type=follow_up_type,
                discount_offered=offer_discount
            )
            
            follow_up_messages = {
                "quote_reminder": "Following up on your Grime Guardians quote. Any questions about our premium service?",
                "availability_check": "Checking on your availability for scheduling. We have openings this week!",
                "competitor_comparison": "We may not be the cheapest — but we're the last call most clients make. BBB-accredited quality.",
                "final_offer": "Last chance to secure your premium cleaning service. Limited availability remaining."
            }
            
            message = follow_up_messages.get(follow_up_type, "Following up on your inquiry.")
            
            # Add discount if authorized (15% new client discount - last resort)
            if offer_discount and follow_up_type == "final_offer":
                message += "\n\n🎯 Special offer: 15% new client discount (this week only)"
            
            # Find client from booking pipeline
            client_id = None
            for quote_id, booking_data in self.booking_pipeline.items():
                if quote_id == inquiry_id:
                    client_id = booking_data["client_id"]
                    break
            
            if client_id:
                await self._send_communication(
                    client_id, "custom",
                    custom_message=message,
                    channel="email", urgency="medium"
                )
            
            return f"Follow-up sent for inquiry {inquiry_id}: {follow_up_type}"
            
        except Exception as e:
            logger.error(f"Error following up inquiry", error=str(e))
            return f"Failed to follow up inquiry: {str(e)}"
    
    async def _enforce_checklist(self, job_id: str, contractor_id: str,
                               checklist_status: str, photo_status: str,
                               quality_issues: Optional[List[str]] = None) -> str:
        """
        Enforce quality checklist and photo requirements.
        
        Args:
            job_id: Job identifier
            contractor_id: Contractor identifier
            checklist_status: Status of checklist completion
            photo_status: Status of photo submission
            quality_issues: List of quality issues found
            
        Returns:
            Enforcement result
        """
        try:
            logger.info(
                f"Sophia enforcing quality checklist",
                job_id=job_id,
                contractor_id=contractor_id,
                checklist_status=checklist_status,
                photo_status=photo_status
            )
            
            violations = []
            
            if checklist_status != "complete":
                violations.append("incomplete_checklist")
            
            if photo_status != "complete":
                violations.append("missing_photos")
            
            if quality_issues:
                violations.extend(quality_issues)
            
            if violations:
                # Coordinate with Ava for business rule enforcement
                from .ava_orchestrator import ava
                await ava.send_message(
                    ava.AgentMessage(
                        agent_id=AgentType.AVA,
                        message_type="quality_violation",
                        content=f"Quality violations detected for job {job_id}",
                        priority=ava.MessagePriority.HIGH,
                        metadata={
                            "job_id": job_id,
                            "contractor_id": contractor_id,
                            "violations": violations
                        }
                    )
                )
                
                result = f"Quality violations reported for job {job_id}: {violations}"
            else:
                result = f"Quality checklist and photos verified for job {job_id} - all requirements met"
            
            return result
            
        except Exception as e:
            logger.error(f"Error enforcing checklist", error=str(e))
            return f"Failed to enforce checklist: {str(e)}"


# Global Sophia instance
sophia = SophiaBooking()