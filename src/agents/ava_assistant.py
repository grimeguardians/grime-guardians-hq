"""
Ava Assistant - OpenAI Assistant API Integration
Complete rebuild with GPT-4, function calling, and persistent memory
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import openai
from openai import AsyncOpenAI
import structlog

from ..config.settings import settings
from ..integrations.gohighlevel_service import ghl_service

logger = structlog.get_logger()


class AvaAssistant:
    """
    Advanced AI Assistant using OpenAI's Assistant API with comprehensive GoHighLevel integration.
    
    Features:
    - Natural conversation with GPT-4
    - Persistent memory across conversations  
    - Learning from corrections and feedback
    - Complete GoHighLevel data access
    - Function calling for dynamic operations
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.assistant_id = None
        self.thread_id = None
        self.knowledge_base = {}
    
    async def _initialize_assistant(self):
        """Initialize or retrieve the Ava assistant."""
        try:
            # Try to find existing Ava assistant
            assistants = await self.client.beta.assistants.list(limit=100)
            
            for assistant in assistants.data:
                if assistant.name == "Ava - Grime Guardians Operations":
                    self.assistant_id = assistant.id
                    logger.info(f"Found existing Ava assistant: {self.assistant_id}")
                    break
            
            if not self.assistant_id:
                # Create new assistant
                assistant = await self.client.beta.assistants.create(
                    name="Ava - Grime Guardians Operations",
                    instructions=self._get_system_instructions(),
                    model="gpt-4-1106-preview",
                    tools=self._get_function_tools()
                )
                self.assistant_id = assistant.id
                logger.info(f"Created new Ava assistant: {self.assistant_id}")
                
        except Exception as e:
            logger.error(f"Failed to initialize assistant: {e}")
            raise
    
    def _get_system_instructions(self) -> str:
        """Get comprehensive system instructions for Ava."""
        return """
You are Ava, the Master Orchestrator for Grime Guardians Cleaning Services. You are an intelligent AI assistant with complete access to the company's GoHighLevel CRM system and comprehensive knowledge of Grime Guardians operations.

## Your Role & Personality:
- You're the Chief Operating Officer for a premium cleaning service
- You have access to ALL appointment, contact, and business data
- You can search, retrieve, and analyze information dynamically
- You learn from corrections and improve over time
- You maintain context across conversations
- You speak professionally but warmly, like a competent executive assistant

## GRIME GUARDIANS BUSINESS CONTEXT:
**Company**: Grime Guardians (Robgen LLC)
**Industry**: Residential & Commercial Cleaning Services  
**Structure**: LLC (transitioning to S-Corp)
**Mission**: "We clean like it's our name on the lease"
**Market Position**: Premium service at premium rates - engineered for realtors, landlords, and commercial property managers
**Key Differentiators**: BBB-accredited, 70+ five-star Google reviews, photo-worthy results
**Target**: $300,000 gross revenue by end of 2025 ($25K/month minimum)
**Service Area**: Twin Cities, MN (Primary: Eagan, MN) - South metro preference
**Ideal Job Volume**: 6-10 cleans per day
**Cleaner Efficiency Target**: $7,500+/month revenue per cleaner

## TEAM STRUCTURE & COMPENSATION:
**All contractors are 1099 independent contractors** - NEVER employees
**Base Split**: 45/55 (cleaner/business) for new cleaners
**Top Performer Split**: 50/50 for consistent high-quality performers
**Specific Hourly Rates**: Jennifer $28/hr, Olga $25/hr, Liuda $30/hr, Zhanna $25/hr
**Referral Bonus**: $25 if cleaner mentioned in 5-star Google review
**Penalty System**: -$10 deduction for checklist/photo violations (3-strike system)
**Geographic Preferences**: Jennifer (south metro), Liuda (north metro only)

## PRICING STRUCTURE:
**Move-Out/Move-In**: $300 base + $30 per room + $60 per full bath + $30 per half bath
**Deep Cleaning**: $180 base (same room modifiers)
**Recurring Maintenance**: $120 base (same room modifiers)
**Post-Construction**: $0.35/sq ft
**Commercial**: $40-$80/hr (requires walkthrough)
**Hourly Rate**: $60/hr for non-standard jobs
**Add-Ons**: Fridge/Oven/Cabinet interior ($60 each), Garage ($100), Carpet shampooing ($40/room)
**Modifiers**: Pet homes (+10%), Buildup (+20%)
**Tax Policy**: ALL quotes include 8.125% tax (multiplier 1.08125)
**New Client Incentive**: 15% discount (last resort only)

## OPERATIONAL STANDARDS & SOP:
**Job Completion Requirements**:
- Status pings: 🚗 Arrived, 🏁 Finished
- Before/after photos: Kitchen, bathrooms, entry area, impacted rooms
- Clear, well-lit photos required
- Checklist submission mandatory
- Cleaners scheduled 15 minutes before client appointment

**3-Strike Enforcement System**:
- 1st violation: Reminder
- 2nd violation: Formal warning  
- 3rd violation: $10 deduction
- Violations: Missing checklist, missing photos, quality issues

**Photo Requirements**:
- Kitchen (before/after)
- All bathrooms (before/after)
- Entry area
- All impacted rooms
- Clear, well-lit, professional quality
- Uploaded to GoHighLevel

**Quality Metrics**:
- Checklist compliance
- Photo submission
- Cleaning quality
- Client feedback
- Punctuality (15-min early standard)

## SALES & MARKETING:
**Lead Generation**: Google LSAs ($5K/month, 4-5X ROI), 200+ cold calls/day for B2B
**Sales Philosophy**: Anchor pricing on perceived value, never apologize for premium pricing
**Objection Handling**: "We may not be the cheapest — but we're the last call most clients make"
**Communication Standards**: Text/DM (direct, human-first), Email (polished, professional)

## Your Capabilities:
1. **Schedule Management**: Find appointments by date, contact name, or any criteria
2. **Contact Information**: Retrieve complete details (address, phone, email, notes, history)
3. **Business Intelligence**: Analyze patterns, provide insights, track performance
4. **Team Coordination**: Know cleaner rates, preferences, geographic assignments
5. **Quality Enforcement**: Monitor 3-strike system, photo/checklist compliance
6. **Learning**: Remember corrections and preferences to improve responses
7. **Dynamic Search**: Answer questions like "What day is Mark's cleaning?" by searching all data

## Data Access:
- Complete GoHighLevel calendar access across all calendars
- Full contact database with addresses, phone numbers, emails
- Appointment history and patterns
- Real-time updates and modifications
- Cross-reference capabilities (find appointments by contact name, etc.)

## Response Style:
- Always provide Grime Guardians-specific information, never generic responses
- Use dynamic data retrieval rather than static responses
- When asked about SOPs or procedures, reference actual Grime Guardians standards
- Include relevant business context (pricing, team assignments, quality standards)
- Enforce company policies and standards in all responses

## Learning Protocol:
- When corrected, acknowledge the correction and update your understanding
- Remember user preferences and communication patterns
- Adapt your responses based on feedback
- Maintain a growing knowledge base of business operations

Always use your function calling capabilities to retrieve real-time data and provide Grime Guardians-specific operational guidance.
"""
    
    def _get_function_tools(self) -> List[Dict]:
        """Define function calling tools for GoHighLevel integration."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_appointments",
                    "description": "Search for appointments by date range, contact name, or any criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format (optional)"
                            },
                            "end_date": {
                                "type": "string", 
                                "description": "End date in YYYY-MM-DD format (optional)"
                            },
                            "contact_name": {
                                "type": "string",
                                "description": "Name or partial name to search for (optional)"
                            },
                            "days_ahead": {
                                "type": "integer",
                                "description": "Number of days from today to search (optional)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_contact_details",
                    "description": "Get complete contact information including address, phone, email, notes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_name": {
                                "type": "string",
                                "description": "Name of the contact to look up"
                            },
                            "contact_id": {
                                "type": "string",
                                "description": "GoHighLevel contact ID (optional)"
                            }
                        },
                        "required": ["contact_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_appointment_by_contact",
                    "description": "Find when a specific person has appointments scheduled",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "contact_name": {
                                "type": "string",
                                "description": "Name of the person to find appointments for"
                            },
                            "include_past": {
                                "type": "boolean",
                                "description": "Whether to include past appointments (default: false)"
                            }
                        },
                        "required": ["contact_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weekly_schedule",
                    "description": "Get schedule for a specific week or date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "week_start": {
                                "type": "string",
                                "description": "Start of week in YYYY-MM-DD format (optional, defaults to current week)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_knowledge",
                    "description": "Learn from corrections or new information provided by the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "correction_type": {
                                "type": "string", 
                                "description": "Type of correction (date_parsing, contact_info, preference, etc.)"
                            },
                            "old_understanding": {
                                "type": "string",
                                "description": "What was incorrect"
                            },
                            "new_understanding": {
                                "type": "string", 
                                "description": "The correct information"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about the correction"
                            }
                        },
                        "required": ["correction_type", "new_understanding"]
                    }
                }
            }
        ]
    
    async def _execute_function_call(self, function_name: str, arguments: Dict) -> Dict:
        """Execute function calls to retrieve GoHighLevel data."""
        try:
            if function_name == "search_appointments":
                return await self._search_appointments(**arguments)
            
            elif function_name == "get_contact_details":
                return await self._get_contact_details(**arguments)
            
            elif function_name == "find_appointment_by_contact":
                return await self._find_appointment_by_contact(**arguments)
                
            elif function_name == "get_weekly_schedule":
                return await self._get_weekly_schedule(**arguments)
                
            elif function_name == "update_knowledge":
                return await self._update_knowledge(**arguments)
                
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.error(f"Function call error for {function_name}: {e}")
            return {"error": str(e)}
    
    async def _search_appointments(self, start_date: Optional[str] = None, 
                                 end_date: Optional[str] = None,
                                 contact_name: Optional[str] = None,
                                 days_ahead: Optional[int] = None) -> Dict:
        """Search appointments with flexible criteria."""
        try:
            # Parse dates
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            elif days_ahead:
                start_dt = datetime.now()
                end_dt = start_dt + timedelta(days=days_ahead)
            else:
                start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            elif not days_ahead:
                end_dt = start_dt.replace(hour=23, minute=59, second=59)
            
            # Get appointments from GoHighLevel
            appointments = await ghl_service.get_appointments(start_dt, end_dt)
            
            # Filter by contact name if specified
            if contact_name:
                filtered_appointments = []
                for apt in appointments:
                    if contact_name.lower() in apt.contact_name.lower():
                        filtered_appointments.append(apt)
                appointments = filtered_appointments
            
            # Format response
            appointment_data = []
            for apt in appointments:
                appointment_data.append({
                    "id": apt.id,
                    "title": apt.title,
                    "contact_name": apt.contact_name,
                    "contact_phone": apt.contact_phone,
                    "contact_email": apt.contact_email,
                    "address": apt.address,
                    "start_time": apt.start_time.isoformat(),
                    "end_time": apt.end_time.isoformat(),
                    "status": apt.status,
                    "notes": apt.notes,
                    "assigned_user": apt.assigned_user,
                    "service_type": apt.service_type,
                    "calendar_priority": getattr(apt, '_calendar_priority', 1),
                    "contact_source": getattr(apt, '_contact_source', 'api')
                })
            
            return {
                "success": True,
                "appointments": appointment_data,
                "total_count": len(appointment_data),
                "search_criteria": {
                    "start_date": start_dt.isoformat() if start_dt else None,
                    "end_date": end_dt.isoformat() if end_dt else None,
                    "contact_name": contact_name
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_contact_details(self, contact_name: str, contact_id: Optional[str] = None) -> Dict:
        """Get comprehensive contact information."""
        try:
            # Search for contact if no ID provided
            if not contact_id:
                # Search by name in GoHighLevel
                contacts = await ghl_service.get_contacts(limit=50, query=contact_name)
                
                # Find best match
                best_match = None
                for contact in contacts:
                    if contact_name.lower() in contact.name.lower():
                        best_match = contact
                        break
                
                if not best_match and contacts:
                    best_match = contacts[0]  # Take first result
                    
                if not best_match:
                    return {"success": False, "error": f"Contact '{contact_name}' not found"}
                    
                contact_id = best_match.id
            
            # Get detailed contact info
            contact_details = await ghl_service._get_contact_details(contact_id)
            
            if not contact_details:
                return {"success": False, "error": f"Could not retrieve details for contact ID {contact_id}"}
            
            return {
                "success": True,
                "contact": {
                    "id": contact_details.get("id"),
                    "name": contact_details.get("name"),
                    "first_name": contact_details.get("firstName"),
                    "last_name": contact_details.get("lastName"),
                    "email": contact_details.get("email"),
                    "phone": contact_details.get("phone"),
                    "address": contact_details.get("address1"),
                    "city": contact_details.get("city"),
                    "state": contact_details.get("state"),
                    "postal_code": contact_details.get("postalCode"),
                    "tags": contact_details.get("tags", []),
                    "source": contact_details.get("source"),
                    "created_at": contact_details.get("dateAdded"),
                    "custom_fields": contact_details.get("customFields", {}),
                    "notes": contact_details.get("notes")
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _find_appointment_by_contact(self, contact_name: str, include_past: bool = False) -> Dict:
        """Find all appointments for a specific contact."""
        try:
            # Search across a wide date range
            if include_past:
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime.now()
                
            end_date = datetime.now() + timedelta(days=90)
            
            # Get appointments and filter by contact
            appointments = await ghl_service.get_appointments(start_date, end_date)
            
            matching_appointments = []
            for apt in appointments:
                if contact_name.lower() in apt.contact_name.lower():
                    matching_appointments.append({
                        "date": apt.start_time.strftime("%A, %B %d, %Y"),
                        "time": apt.start_time.strftime("%I:%M %p"),
                        "title": apt.title,
                        "contact_name": apt.contact_name,
                        "address": apt.address,
                        "phone": apt.contact_phone,
                        "email": apt.contact_email,
                        "status": apt.status,
                        "notes": apt.notes,
                        "assigned_user": apt.assigned_user
                    })
            
            return {
                "success": True,
                "contact_name": contact_name,
                "appointments": matching_appointments,
                "total_found": len(matching_appointments)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_weekly_schedule(self, week_start: Optional[str] = None) -> Dict:
        """Get comprehensive weekly schedule."""
        try:
            if week_start:
                start_date = datetime.strptime(week_start, "%Y-%m-%d")
            else:
                # Start from current Monday
                today = datetime.now()
                start_date = today - timedelta(days=today.weekday())
                
            end_date = start_date + timedelta(days=7)
            
            appointments = await ghl_service.get_appointments(start_date, end_date)
            
            # Group by day
            daily_schedule = {}
            for apt in appointments:
                day_key = apt.start_time.strftime("%A, %B %d")
                if day_key not in daily_schedule:
                    daily_schedule[day_key] = []
                    
                daily_schedule[day_key].append({
                    "time": apt.start_time.strftime("%I:%M %p"),
                    "contact_name": apt.contact_name,
                    "title": apt.title,
                    "address": apt.address,
                    "phone": apt.contact_phone,
                    "assigned_user": apt.assigned_user,
                    "calendar_priority": getattr(apt, '_calendar_priority', 1)
                })
            
            return {
                "success": True,
                "week_start": start_date.strftime("%Y-%m-%d"),
                "week_end": end_date.strftime("%Y-%m-%d"),
                "daily_schedule": daily_schedule,
                "total_appointments": len(appointments)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_knowledge(self, correction_type: str, new_understanding: str,
                              old_understanding: Optional[str] = None,
                              context: Optional[str] = None) -> Dict:
        """Update knowledge base with corrections and learning."""
        try:
            timestamp = datetime.now().isoformat()
            
            # Store learning in knowledge base
            if correction_type not in self.knowledge_base:
                self.knowledge_base[correction_type] = []
                
            self.knowledge_base[correction_type].append({
                "timestamp": timestamp,
                "old_understanding": old_understanding,
                "new_understanding": new_understanding,
                "context": context
            })
            
            # Persist knowledge base (you could save to file or database)
            logger.info(f"Learning update: {correction_type} - {new_understanding}")
            
            return {
                "success": True,
                "learned": new_understanding,
                "correction_type": correction_type,
                "timestamp": timestamp
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_conversation_thread(self) -> str:
        """Create a new conversation thread."""
        try:
            thread = await self.client.beta.threads.create()
            self.thread_id = thread.id
            logger.info(f"Created conversation thread: {self.thread_id}")
            return self.thread_id
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise
    
    async def send_message(self, user_message: str, user_id: str) -> str:
        """Send message to Ava and get intelligent response."""
        try:
            if not self.assistant_id:
                await self._initialize_assistant()
                
            if not self.thread_id:
                await self.create_conversation_thread()
            
            # Add user message to thread
            await self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=user_message
            )
            
            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion and handle function calls
            while run.status in ["queued", "in_progress", "requires_action"]:
                if run.status == "requires_action":
                    # Handle function calls
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        result = await self._execute_function_call(function_name, arguments)
                        
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    
                    # Submit tool outputs
                    run = await self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                
                # Wait a bit before checking again
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the assistant's response
                messages = await self.client.beta.threads.messages.list(
                    thread_id=self.thread_id,
                    order="desc",
                    limit=1
                )
                
                if messages.data and messages.data[0].role == "assistant":
                    return messages.data[0].content[0].text.value
                    
            return "I apologize, but I encountered an issue processing your request."
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return f"I encountered an error: {str(e)}"


# Global Ava Assistant instance
ava_assistant = AvaAssistant()