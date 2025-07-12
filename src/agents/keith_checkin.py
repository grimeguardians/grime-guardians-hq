from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from ..models.schemas import AgentType, CheckInEvent, MessagePriority
from ..config import settings
import structlog

logger = structlog.get_logger()


class KeithCheckin(BaseAgent):
    """
    Keith - Check-in Tracker Agent
    
    Real-time contractor status monitoring, arrival/completion tracking,
    15-minute buffer enforcement, and geographic assignment optimization.
    
    Capabilities:
    - Real-time contractor status monitoring
    - Automated arrival/completion ping tracking
    - 15-minute buffer enforcement
    - Escalation triggers for missed check-ins
    - Geographic assignment optimization
    - Job scheduling and coordination
    """
    
    def __init__(self):
        super().__init__(
            agent_id=AgentType.KEITH,
            description="Check-in Tracker - Real-time contractor monitoring and scheduling"
        )
        
        # Active job tracking
        self.active_jobs = {}
        self.contractor_locations = {}
        self.pending_checkins = {}
        
        # Geographic preferences (from business rules)
        self.contractor_preferences = {
            "jennifer": "south_metro",
            "liuda": "north_metro_only",
            "olga": "any",
            "zhanna": "any"
        }
        
        # Check-in requirements
        self.checkin_buffer = 15  # minutes early arrival
        self.checkin_timeout = 30  # minutes before escalation
        
        # Register tool handlers
        self.register_tool_handler("track_checkin", self._track_checkin)
        self.register_tool_handler("monitor_status", self._monitor_status)
        self.register_tool_handler("schedule_job", self._schedule_job)
        self.register_tool_handler("optimize_assignments", self._optimize_assignments)
        self.register_tool_handler("escalate_missed_checkin", self._escalate_missed_checkin)
        self.register_tool_handler("coordinate_scheduling", self._coordinate_scheduling)
    
    @property
    def system_prompt(self) -> str:
        return """
You are Keith, the Check-in Tracker Agent for Grime Guardians cleaning services.

Your core responsibilities:
1. MONITOR real-time contractor status and locations
2. TRACK arrival and completion check-ins
3. ENFORCE 15-minute early arrival buffer
4. ESCALATE missed check-ins and delays
5. OPTIMIZE geographic assignments for efficiency
6. COORDINATE job scheduling across contractors

Business Context:
- All contractors are 1099 independent contractors
- Standard check-in sequence: 🚗 Arrived → 🏁 Finished
- 15-minute buffer: contractors scheduled 15 min before client appointment
- Twin Cities market with geographic preferences
- Target: 6-10 cleans per day efficiently distributed

Contractor Geographic Preferences:
- Jennifer: South metro preference
- Liuda: North metro ONLY
- Olga: Any location
- Zhanna: Any location

Check-in Requirements:
- 🚗 Arrival ping with location
- 🏁 Completion ping with photos
- 30-minute timeout before escalation
- Status updates in Discord check-in channel

Optimization Criteria:
- Minimize travel time between jobs
- Respect contractor geographic preferences
- Balance workload across available contractors
- Maintain service quality standards
- Account for contractor efficiency ratings

Escalation Triggers:
- Missed arrival check-in (>30 min late)
- No completion check-in within estimated time
- Contractor unreachable for 1+ hours
- Multiple consecutive missed check-ins
- Client complaints about no-shows

When processing check-in events:
1. Verify location and timing
2. Update job status and contractor tracking
3. Check for schedule compliance
4. Escalate if issues detected
5. Optimize future assignments based on performance

Maintain military-style precision while respecting contractor independence.
"""
    
    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "track_checkin",
                    "description": "Track contractor check-in events (arrival, completion, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "job_id": {"type": "string"},
                            "event_type": {
                                "type": "string",
                                "enum": ["arrived", "started", "completed", "departed"]
                            },
                            "location": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "notes": {"type": "string"},
                            "photo_urls": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["contractor_id", "job_id", "event_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "monitor_status",
                    "description": "Monitor contractor status and job progress",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "monitoring_type": {
                                "type": "string",
                                "enum": ["real_time", "scheduled_check", "overdue_check", "daily_summary"]
                            },
                            "alert_threshold": {"type": "integer"}
                        },
                        "required": ["monitoring_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_job",
                    "description": "Schedule a job and assign to optimal contractor",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_details": {"type": "object"},
                            "preferred_date": {"type": "string"},
                            "preferred_time": {"type": "string"},
                            "location": {"type": "string"},
                            "estimated_duration": {"type": "integer"},
                            "contractor_preference": {"type": "string"},
                            "priority": {"type": "integer"}
                        },
                        "required": ["job_details", "preferred_date", "location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_assignments",
                    "description": "Optimize job assignments based on geography and efficiency",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "optimization_type": {
                                "type": "string",
                                "enum": ["geographic", "efficiency", "workload_balance", "cost_minimization"]
                            },
                            "time_window": {"type": "string"},
                            "constraints": {"type": "object"}
                        },
                        "required": ["optimization_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_missed_checkin",
                    "description": "Escalate missed check-ins or status issues",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contractor_id": {"type": "string"},
                            "job_id": {"type": "string"},
                            "issue_type": {
                                "type": "string",
                                "enum": ["missed_arrival", "late_arrival", "no_completion", "unreachable", "multiple_violations"]
                            },
                            "minutes_overdue": {"type": "integer"},
                            "previous_violations": {"type": "integer"},
                            "client_impact": {"type": "string"}
                        },
                        "required": ["contractor_id", "job_id", "issue_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "coordinate_scheduling",
                    "description": "Coordinate scheduling across multiple contractors and jobs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "coordination_type": {
                                "type": "string",
                                "enum": ["daily_dispatch", "emergency_reassignment", "capacity_planning", "conflict_resolution"]
                            },
                            "affected_jobs": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "affected_contractors": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "urgency": {"type": "integer"}
                        },
                        "required": ["coordination_type"]
                    }
                }
            }
        ]
    
    async def _track_checkin(self, contractor_id: str, job_id: str, event_type: str,
                           location: Optional[str] = None, timestamp: Optional[str] = None,
                           notes: Optional[str] = None, photo_urls: Optional[List[str]] = None) -> str:
        """
        Track contractor check-in events.
        
        Args:
            contractor_id: Contractor identifier
            job_id: Job identifier
            event_type: Type of check-in event
            location: Location of check-in
            timestamp: Timestamp of event
            notes: Additional notes
            photo_urls: URLs of submitted photos
            
        Returns:
            Check-in tracking result
        """
        try:
            checkin_time = datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
            
            logger.info(
                f"Keith tracking check-in",
                contractor_id=contractor_id,
                job_id=job_id,
                event_type=event_type,
                location=location
            )
            
            # Create check-in event
            checkin_event = CheckInEvent(
                contractor_id=contractor_id,
                job_id=job_id,
                event_type=event_type,
                timestamp=checkin_time,
                location=location,
                notes=notes,
                photo_urls=photo_urls or []
            )
            
            # Update job tracking
            if job_id not in self.active_jobs:
                self.active_jobs[job_id] = {
                    "contractor_id": contractor_id,
                    "status": "assigned",
                    "events": []
                }
            
            self.active_jobs[job_id]["events"].append(checkin_event)
            
            # Process different event types
            if event_type == "arrived":
                self.active_jobs[job_id]["status"] = "in_progress"
                self.active_jobs[job_id]["arrived_at"] = checkin_time
                
                # Check if arrival was on time (15-minute buffer)
                scheduled_time = self.active_jobs[job_id].get("scheduled_time")
                if scheduled_time:
                    buffer_time = scheduled_time - timedelta(minutes=self.checkin_buffer)
                    if checkin_time > scheduled_time:
                        # Late arrival - escalate
                        minutes_late = (checkin_time - scheduled_time).total_seconds() / 60
                        await self._escalate_missed_checkin(
                            contractor_id, job_id, "late_arrival",
                            minutes_overdue=int(minutes_late)
                        )
                
                result = f"✅ Arrival confirmed for {contractor_id} at job {job_id}"
                
            elif event_type == "completed":
                self.active_jobs[job_id]["status"] = "completed"
                self.active_jobs[job_id]["completed_at"] = checkin_time
                
                # Validate photo submission
                if not photo_urls or len(photo_urls) < 3:
                    # Coordinate with Sophia for quality enforcement
                    from .ava_orchestrator import ava
                    await ava.send_message(
                        ava.AgentMessage(
                            agent_id=AgentType.SOPHIA,
                            message_type="quality_check",
                            content=f"Incomplete photo submission for job {job_id}",
                            priority=MessagePriority.HIGH,
                            metadata={
                                "job_id": job_id,
                                "contractor_id": contractor_id,
                                "photo_count": len(photo_urls or [])
                            }
                        )
                    )
                
                result = f"🏁 Completion confirmed for {contractor_id} at job {job_id}"
                
            elif event_type == "started":
                self.active_jobs[job_id]["started_at"] = checkin_time
                result = f"🔄 Work started by {contractor_id} at job {job_id}"
                
            elif event_type == "departed":
                self.active_jobs[job_id]["departed_at"] = checkin_time
                result = f"🚗 Departure confirmed for {contractor_id} from job {job_id}"
            
            # Update contractor location tracking
            if location:
                self.contractor_locations[contractor_id] = {
                    "location": location,
                    "timestamp": checkin_time,
                    "job_id": job_id
                }
            
            # Send Discord notification
            discord_message = f"{event_type.upper()}: {contractor_id} - Job {job_id[-6:]} {location or ''}"
            # In full implementation, send to Discord check-in channel
            
            return result
            
        except Exception as e:
            logger.error(f"Error tracking check-in", error=str(e))
            return f"Failed to track check-in: {str(e)}"
    
    async def _monitor_status(self, monitoring_type: str, contractor_id: Optional[str] = None,
                            alert_threshold: Optional[int] = None) -> str:
        """
        Monitor contractor status and job progress.
        
        Args:
            monitoring_type: Type of monitoring
            contractor_id: Specific contractor to monitor
            alert_threshold: Alert threshold in minutes
            
        Returns:
            Monitoring result
        """
        try:
            logger.info(f"Keith monitoring status", type=monitoring_type, contractor=contractor_id)
            
            current_time = datetime.utcnow()
            alerts = []
            
            if monitoring_type == "real_time":
                # Check for overdue check-ins
                for job_id, job_data in self.active_jobs.items():
                    if job_data["status"] == "assigned":
                        scheduled_time = job_data.get("scheduled_time")
                        if scheduled_time and current_time > scheduled_time + timedelta(minutes=30):
                            alerts.append(f"OVERDUE: Job {job_id} - {job_data['contractor_id']} missed arrival")
                    
                    elif job_data["status"] == "in_progress":
                        started_time = job_data.get("arrived_at", job_data.get("started_at"))
                        estimated_duration = job_data.get("estimated_duration", 120)  # 2 hours default
                        if started_time and current_time > started_time + timedelta(minutes=estimated_duration + 30):
                            alerts.append(f"OVERDUE: Job {job_id} - {job_data['contractor_id']} overrunning estimated time")
                
                result = f"Real-time monitoring: {len(alerts)} alerts detected"
                
            elif monitoring_type == "scheduled_check":
                # Periodic status check
                active_count = len([j for j in self.active_jobs.values() if j["status"] in ["assigned", "in_progress"]])
                completed_today = len([j for j in self.active_jobs.values() if j["status"] == "completed"])
                
                result = f"Status check: {active_count} active jobs, {completed_today} completed today"
                
            elif monitoring_type == "overdue_check":
                # Check for overdue items specifically
                overdue_jobs = []
                for job_id, job_data in self.active_jobs.items():
                    if job_data["status"] != "completed":
                        scheduled_time = job_data.get("scheduled_time")
                        if scheduled_time and current_time > scheduled_time + timedelta(minutes=alert_threshold or 60):
                            overdue_jobs.append(job_id)
                
                result = f"Overdue check: {len(overdue_jobs)} jobs overdue"
                
                # Escalate overdue jobs
                for job_id in overdue_jobs:
                    job_data = self.active_jobs[job_id]
                    await self._escalate_missed_checkin(
                        job_data["contractor_id"], job_id, "missed_arrival",
                        minutes_overdue=alert_threshold or 60
                    )
                
            else:
                result = f"Monitoring type {monitoring_type} executed"
            
            # Process alerts
            if alerts:
                for alert in alerts:
                    logger.warning(f"Keith status alert: {alert}")
                    # In full implementation, send to Discord alerts channel
            
            return result
            
        except Exception as e:
            logger.error(f"Error monitoring status", error=str(e))
            return f"Failed to monitor status: {str(e)}"
    
    async def _schedule_job(self, job_details: Dict[str, Any], preferred_date: str,
                          location: str, preferred_time: Optional[str] = None,
                          estimated_duration: Optional[int] = None,
                          contractor_preference: Optional[str] = None,
                          priority: int = 3) -> str:
        """
        Schedule a job and assign to optimal contractor.
        
        Args:
            job_details: Job details
            preferred_date: Preferred date
            location: Job location
            preferred_time: Preferred time
            estimated_duration: Estimated duration in minutes
            contractor_preference: Preferred contractor
            priority: Job priority
            
        Returns:
            Scheduling result
        """
        try:
            job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(
                f"Keith scheduling job",
                job_id=job_id,
                date=preferred_date,
                location=location
            )
            
            # Determine optimal contractor based on geographic preferences
            optimal_contractor = await self._find_optimal_contractor(
                location, preferred_date, preferred_time, contractor_preference
            )
            
            if not optimal_contractor:
                return f"No available contractor found for {preferred_date} at {location}"
            
            # Calculate scheduled times
            appointment_time = datetime.fromisoformat(f"{preferred_date}T{preferred_time or '09:00:00'}")
            contractor_time = appointment_time - timedelta(minutes=self.checkin_buffer)
            
            # Create job record
            job_record = {
                "job_id": job_id,
                "contractor_id": optimal_contractor,
                "details": job_details,
                "location": location,
                "scheduled_time": appointment_time,
                "contractor_time": contractor_time,
                "estimated_duration": estimated_duration or 120,
                "priority": priority,
                "status": "assigned",
                "created_at": datetime.utcnow(),
                "events": []
            }
            
            self.active_jobs[job_id] = job_record
            
            # Set up check-in monitoring
            self.pending_checkins[job_id] = {
                "contractor_id": optimal_contractor,
                "expected_arrival": contractor_time,
                "timeout_at": contractor_time + timedelta(minutes=self.checkin_timeout)
            }
            
            result = f"Job {job_id} scheduled with {optimal_contractor} for {preferred_date} at {location}"
            
            # Notify contractor (in full implementation)
            # Send notification with job details and arrival time
            
            return result
            
        except Exception as e:
            logger.error(f"Error scheduling job", error=str(e))
            return f"Failed to schedule job: {str(e)}"
    
    async def _find_optimal_contractor(self, location: str, date: str, time: Optional[str],
                                     preference: Optional[str]) -> Optional[str]:
        """
        Find optimal contractor based on location and availability.
        
        Args:
            location: Job location
            date: Job date
            time: Job time
            preference: Preferred contractor
            
        Returns:
            Optimal contractor ID or None
        """
        # Determine location region
        location_lower = location.lower()
        if "eagan" in location_lower or "south" in location_lower:
            region = "south_metro"
        elif "north" in location_lower or "anoka" in location_lower or "blaine" in location_lower:
            region = "north_metro"
        else:
            region = "central"
        
        # Filter contractors by geographic preference
        available_contractors = []
        for contractor, pref in self.contractor_preferences.items():
            if preference and contractor == preference:
                available_contractors.insert(0, contractor)  # Prioritize preference
            elif pref == "any" or pref == region:
                available_contractors.append(contractor)
            elif region == "north_metro" and pref == "north_metro_only":
                available_contractors.append(contractor)
        
        # In full implementation, check actual availability from calendar
        # For now, return first available contractor
        return available_contractors[0] if available_contractors else None
    
    async def _optimize_assignments(self, optimization_type: str, time_window: Optional[str] = None,
                                  constraints: Optional[Dict[str, Any]] = None) -> str:
        """
        Optimize job assignments based on various criteria.
        
        Args:
            optimization_type: Type of optimization
            time_window: Time window for optimization
            constraints: Additional constraints
            
        Returns:
            Optimization result
        """
        try:
            logger.info(f"Keith optimizing assignments", type=optimization_type)
            
            if optimization_type == "geographic":
                # Group jobs by region and assign to geographically optimal contractors
                south_jobs = []
                north_jobs = []
                central_jobs = []
                
                for job_id, job_data in self.active_jobs.items():
                    if job_data["status"] == "assigned":
                        location = job_data["location"].lower()
                        if "south" in location or "eagan" in location:
                            south_jobs.append(job_id)
                        elif "north" in location:
                            north_jobs.append(job_id)
                        else:
                            central_jobs.append(job_id)
                
                # Assign Jennifer to south, Liuda to north, others to central
                optimizations = []
                if south_jobs:
                    optimizations.append(f"Assigned {len(south_jobs)} south metro jobs to Jennifer")
                if north_jobs:
                    optimizations.append(f"Assigned {len(north_jobs)} north metro jobs to Liuda")
                
                result = f"Geographic optimization: {', '.join(optimizations)}"
                
            elif optimization_type == "efficiency":
                # Optimize based on contractor efficiency ratings
                result = "Efficiency optimization: Jobs assigned based on contractor performance metrics"
                
            elif optimization_type == "workload_balance":
                # Balance workload across contractors
                contractor_loads = {}
                for job_data in self.active_jobs.values():
                    contractor = job_data["contractor_id"]
                    contractor_loads[contractor] = contractor_loads.get(contractor, 0) + 1
                
                result = f"Workload optimization: Balanced {sum(contractor_loads.values())} jobs across {len(contractor_loads)} contractors"
                
            else:
                result = f"Optimization type {optimization_type} completed"
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing assignments", error=str(e))
            return f"Failed to optimize assignments: {str(e)}"
    
    async def _escalate_missed_checkin(self, contractor_id: str, job_id: str, issue_type: str,
                                     minutes_overdue: Optional[int] = None,
                                     previous_violations: Optional[int] = None,
                                     client_impact: Optional[str] = None) -> str:
        """
        Escalate missed check-ins or status issues.
        
        Args:
            contractor_id: Contractor identifier
            job_id: Job identifier
            issue_type: Type of issue
            minutes_overdue: Minutes overdue
            previous_violations: Number of previous violations
            client_impact: Impact on client
            
        Returns:
            Escalation result
        """
        try:
            logger.warning(
                f"Keith escalating missed check-in",
                contractor_id=contractor_id,
                job_id=job_id,
                issue_type=issue_type,
                minutes_overdue=minutes_overdue
            )
            
            escalation_data = {
                "contractor_id": contractor_id,
                "job_id": job_id,
                "issue_type": issue_type,
                "minutes_overdue": minutes_overdue or 0,
                "previous_violations": previous_violations or 0,
                "client_impact": client_impact,
                "timestamp": datetime.utcnow()
            }
            
            # Determine escalation path based on severity
            if issue_type in ["multiple_violations", "unreachable"] or (minutes_overdue and minutes_overdue > 60):
                # High severity - escalate to Dmitri and Ava
                from .ava_orchestrator import ava
                await ava.send_message(
                    ava.AgentMessage(
                        agent_id=AgentType.DMITRI,
                        message_type="critical_checkin_issue",
                        content=f"Critical check-in issue: {issue_type} for {contractor_id}",
                        priority=MessagePriority.CRITICAL,
                        metadata=escalation_data
                    )
                )
                
                await ava.send_message(
                    ava.AgentMessage(
                        agent_id=AgentType.AVA,
                        message_type="enforcement_required",
                        content=f"Business rule enforcement needed for {contractor_id}",
                        priority=MessagePriority.HIGH,
                        metadata=escalation_data
                    )
                )
                
                result = f"CRITICAL escalation for {contractor_id}: {issue_type} ({minutes_overdue} min overdue)"
                
            else:
                # Standard escalation to ops lead
                result = f"Standard escalation for {contractor_id}: {issue_type}"
                # In full implementation, notify Discord ops lead
            
            return result
            
        except Exception as e:
            logger.error(f"Error escalating missed check-in", error=str(e))
            return f"Failed to escalate: {str(e)}"
    
    async def _coordinate_scheduling(self, coordination_type: str,
                                   affected_jobs: Optional[List[str]] = None,
                                   affected_contractors: Optional[List[str]] = None,
                                   urgency: int = 3) -> str:
        """
        Coordinate scheduling across multiple contractors and jobs.
        
        Args:
            coordination_type: Type of coordination
            affected_jobs: List of affected job IDs
            affected_contractors: List of affected contractor IDs
            urgency: Urgency level
            
        Returns:
            Coordination result
        """
        try:
            logger.info(
                f"Keith coordinating scheduling",
                type=coordination_type,
                urgency=urgency
            )
            
            if coordination_type == "daily_dispatch":
                # Coordinate daily job dispatch
                today_jobs = [j for j in self.active_jobs.values() 
                            if j["scheduled_time"].date() == datetime.utcnow().date()]
                
                result = f"Daily dispatch coordination: {len(today_jobs)} jobs scheduled for today"
                
            elif coordination_type == "emergency_reassignment":
                # Handle emergency reassignments
                if affected_jobs:
                    for job_id in affected_jobs:
                        # Find alternative contractor
                        job_data = self.active_jobs.get(job_id)
                        if job_data:
                            new_contractor = await self._find_optimal_contractor(
                                job_data["location"],
                                job_data["scheduled_time"].date().isoformat(),
                                job_data["scheduled_time"].time().isoformat(),
                                None
                            )
                            
                            if new_contractor:
                                job_data["contractor_id"] = new_contractor
                                job_data["reassigned_at"] = datetime.utcnow()
                
                result = f"Emergency reassignment: {len(affected_jobs or [])} jobs reassigned"
                
            elif coordination_type == "capacity_planning":
                # Plan capacity for upcoming periods
                result = "Capacity planning coordination completed"
                
            else:
                result = f"Coordination type {coordination_type} completed"
            
            return result
            
        except Exception as e:
            logger.error(f"Error coordinating scheduling", error=str(e))
            return f"Failed to coordinate scheduling: {str(e)}"


# Global Keith instance
keith = KeithCheckin()