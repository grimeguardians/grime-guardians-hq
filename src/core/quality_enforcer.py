"""
Quality Enforcement System
3-strike system with Discord integration and AI photo validation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import base64
import io
from PIL import Image
import cv2
import numpy as np

from openai import AsyncOpenAI
from pydantic import BaseModel

from ..models.schemas import (
    ComplianceResult, QualityViolationSchema, HumanApprovalRequest,
    PerformanceMetrics, JobSchema, ContractorSchema
)
from ..models.types import ViolationType, JobStatus, ContractorStatus
from ..config.settings import get_settings, QUALITY_REQUIREMENTS

logger = logging.getLogger(__name__)
settings = get_settings()


class PhotoValidationResult(BaseModel):
    """Result of AI photo validation."""
    is_valid: bool
    quality_score: float  # 0-10
    issues: List[str] = []
    required_rooms_covered: List[str] = []
    missing_rooms: List[str] = []
    technical_issues: List[str] = []  # blur, lighting, etc.


class StrikeRecord(BaseModel):
    """Individual strike record."""
    contractor_id: str
    strike_number: int  # 1, 2, or 3
    violation_type: ViolationType
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    job_id: Optional[str] = None
    requires_approval: bool = False
    approved_by: Optional[str] = None
    penalty_amount: Optional[Decimal] = None


class QualityEnforcer:
    """
    Quality enforcement system with 3-strike tracking and AI photo validation.
    Integrates with Discord for notifications and approval workflows.
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.strike_records: Dict[str, List[StrikeRecord]] = {}  # contractor_id -> strikes
        self.photo_validation_cache: Dict[str, PhotoValidationResult] = {}
        
        # Discord channel mapping
        self.discord_channels = {
            "strikes": "❌-strikes",
            "alerts": "🚨-alerts", 
            "job_checkins": "✔️-job-check-ins",
            "photo_submissions": "📸-photo-submissions",
            "job_board": "🪧-job-board"
        }
        
        # Required photos per service type
        self.required_photos = QUALITY_REQUIREMENTS["photos"]
        
    async def check_job_compliance(
        self, 
        job: JobSchema, 
        contractor: ContractorSchema,
        photos: List[Dict[str, Any]] = None,
        checklist_data: Dict[str, Any] = None
    ) -> ComplianceResult:
        """
        Comprehensive job compliance check.
        Validates photos, checklist, timing, and quality standards.
        """
        violations = []
        recommendations = []
        
        try:
            # Check photo compliance
            photo_result = await self._validate_photos(job.id, photos or [])
            if not photo_result.is_valid:
                violations.extend([ViolationType.MISSING_PHOTOS, ViolationType.POOR_PHOTO_QUALITY])
                recommendations.extend([
                    "Submit all required photos (kitchen, bathrooms, entry area, impacted rooms)",
                    "Ensure photos are well-lit and clear",
                    "Retake any blurry or dark photos"
                ])
            
            # Check checklist compliance
            if not self._validate_checklist(job.service_type, checklist_data or {}):
                violations.append(ViolationType.INCOMPLETE_CHECKLIST)
                recommendations.append(f"Complete all {job.service_type} checklist items")
            
            # Check timing compliance (15-minute buffer)
            timing_violation = await self._check_timing_compliance(job, contractor)
            if timing_violation:
                violations.append(timing_violation)
                if timing_violation == ViolationType.LATE_ARRIVAL:
                    recommendations.append("Communicate delays in advance via Discord")
                elif timing_violation == ViolationType.NO_SHOW:
                    recommendations.append("Immediate communication required for no-shows")
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(violations, photo_result.quality_score)
            
            # Determine if human review needed
            requires_human_review = (
                len(violations) >= 2 or
                ViolationType.NO_SHOW in violations or
                compliance_score < 70
            )
            
            # Get current strike count
            current_strikes = len(self.strike_records.get(contractor.id, []))
            
            result = ComplianceResult(
                job_id=job.id,
                contractor_id=contractor.id,
                violations=violations,
                strike_count=current_strikes,
                photos_valid=photo_result.is_valid,
                checklist_complete=len(violations) == 0 or ViolationType.INCOMPLETE_CHECKLIST not in violations,
                compliance_score=compliance_score,
                recommendations=recommendations,
                requires_human_review=requires_human_review
            )
            
            # Record violations if any
            if violations:
                await self._record_violations(job, contractor, violations, photo_result)
            
            logger.info(f"Compliance check completed for {contractor.id}: {compliance_score:.1f}% score")
            return result
            
        except Exception as e:
            logger.error(f"Compliance check error for job {job.id}: {e}")
            return ComplianceResult(
                job_id=job.id,
                contractor_id=contractor.id,
                violations=[],
                strike_count=0,
                photos_valid=False,
                checklist_complete=False,
                compliance_score=0,
                requires_human_review=True
            )
    
    async def _validate_photos(
        self, 
        job_id: str, 
        photos: List[Dict[str, Any]]
    ) -> PhotoValidationResult:
        """
        AI-powered photo validation for quality and coverage.
        """
        try:
            # Check cache first
            cache_key = f"{job_id}_{len(photos)}"
            if cache_key in self.photo_validation_cache:
                return self.photo_validation_cache[cache_key]
            
            issues = []
            required_rooms_covered = []
            missing_rooms = []
            technical_issues = []
            quality_scores = []
            
            # Check if basic photos submitted
            if len(photos) == 0:
                issues.append("No photos submitted")
                missing_rooms = self.required_photos.copy()
                result = PhotoValidationResult(
                    is_valid=False,
                    quality_score=0.0,
                    issues=issues,
                    missing_rooms=missing_rooms
                )
                self.photo_validation_cache[cache_key] = result
                return result
            
            # Analyze each photo
            for i, photo in enumerate(photos):
                photo_analysis = await self._analyze_single_photo(photo)
                quality_scores.append(photo_analysis["quality_score"])
                
                # Track room coverage
                if photo_analysis["room_identified"]:
                    required_rooms_covered.append(photo_analysis["room_type"])
                
                # Track technical issues
                if photo_analysis["technical_issues"]:
                    technical_issues.extend(photo_analysis["technical_issues"])
            
            # Check for missing required rooms
            for required_room in self.required_photos:
                if not any(required_room.lower() in covered.lower() for covered in required_rooms_covered):
                    missing_rooms.append(required_room)
            
            # Calculate overall quality score
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            coverage_penalty = len(missing_rooms) * 2  # 2 points per missing room
            technical_penalty = len(technical_issues) * 1  # 1 point per technical issue
            
            final_quality_score = max(0, avg_quality - coverage_penalty - technical_penalty)
            
            # Determine if valid
            is_valid = (
                len(missing_rooms) == 0 and
                len(technical_issues) <= 2 and  # Allow minor technical issues
                final_quality_score >= 6.0
            )
            
            # Compile issues
            if missing_rooms:
                issues.append(f"Missing required photos: {', '.join(missing_rooms)}")
            if technical_issues:
                issues.append(f"Technical issues: {', '.join(set(technical_issues))}")
            if final_quality_score < 6.0:
                issues.append(f"Overall photo quality below standard: {final_quality_score:.1f}/10")
            
            result = PhotoValidationResult(
                is_valid=is_valid,
                quality_score=final_quality_score,
                issues=issues,
                required_rooms_covered=required_rooms_covered,
                missing_rooms=missing_rooms,
                technical_issues=list(set(technical_issues))
            )
            
            # Cache result
            self.photo_validation_cache[cache_key] = result
            
            logger.info(f"Photo validation completed for job {job_id}: {final_quality_score:.1f}/10, valid={is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Photo validation error for job {job_id}: {e}")
            return PhotoValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=[f"Photo validation error: {str(e)}"],
                missing_rooms=self.required_photos.copy()
            )
    
    async def _analyze_single_photo(self, photo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze individual photo using AI vision.
        """
        try:
            # Prepare photo for analysis
            photo_data = photo.get("data") or photo.get("base64") or photo.get("url")
            if not photo_data:
                return {
                    "quality_score": 0,
                    "room_identified": False,
                    "room_type": "unknown",
                    "technical_issues": ["No photo data available"]
                }
            
            # Use OpenAI Vision API for analysis
            analysis_prompt = f"""
            Analyze this cleaning job photo and provide assessment:
            
            REQUIRED ROOMS TO IDENTIFY: {', '.join(self.required_photos)}
            
            Evaluate:
            1. Image quality (clarity, lighting, focus) - score 0-10
            2. Room identification - which room is this?
            3. Technical issues (blur, darkness, poor angle)
            4. Coverage - does it show the cleaned area adequately?
            
            Respond in JSON format:
            {{
                "quality_score": 8.5,
                "room_type": "kitchen",
                "room_identified": true,
                "technical_issues": ["slightly blurry"],
                "coverage_adequate": true,
                "lighting_score": 7.0,
                "clarity_score": 8.0,
                "composition_score": 9.0
            }}
            """
            
            # For now, use mock analysis (in production, use OpenAI Vision)
            # This is a placeholder for the actual Vision API call
            mock_analysis = self._mock_photo_analysis(photo)
            
            return mock_analysis
            
        except Exception as e:
            logger.error(f"Single photo analysis error: {e}")
            return {
                "quality_score": 3,
                "room_identified": False,
                "room_type": "unknown",
                "technical_issues": [f"Analysis error: {str(e)}"]
            }
    
    def _mock_photo_analysis(self, photo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock photo analysis for development.
        In production, this would use OpenAI Vision API.
        """
        filename = photo.get("filename", "").lower()
        
        # Identify room from filename
        room_type = "unknown"
        room_identified = False
        
        for required_room in self.required_photos:
            if required_room.lower() in filename:
                room_type = required_room
                room_identified = True
                break
        
        # Mock quality scoring based on filename patterns
        quality_score = 8.0  # Default good quality
        technical_issues = []
        
        if "blur" in filename or "dark" in filename:
            quality_score -= 3
            technical_issues.append("poor image quality")
        
        if "missing" in filename:
            room_identified = False
            quality_score -= 2
        
        return {
            "quality_score": max(0, quality_score),
            "room_type": room_type,
            "room_identified": room_identified,
            "technical_issues": technical_issues,
            "coverage_adequate": quality_score >= 6,
            "lighting_score": quality_score,
            "clarity_score": quality_score,
            "composition_score": quality_score
        }
    
    def _validate_checklist(self, service_type: str, checklist_data: Dict[str, Any]) -> bool:
        """
        Validate checklist completion for service type.
        """
        required_items = self._get_required_checklist_items(service_type)
        
        if not checklist_data:
            return False
        
        completed_items = checklist_data.get("completed_items", [])
        completion_rate = len(completed_items) / len(required_items) if required_items else 1.0
        
        return completion_rate >= 0.90  # 90% completion required
    
    def _get_required_checklist_items(self, service_type: str) -> List[str]:
        """Get required checklist items for service type."""
        base_items = [
            "vacuum_all_floors", "mop_hard_surfaces", "dust_all_surfaces",
            "clean_bathrooms", "clean_kitchen", "empty_trash"
        ]
        
        if service_type == "move_out_in":
            return base_items + [
                "clean_inside_cabinets", "clean_inside_appliances",
                "clean_light_fixtures", "clean_baseboards", "clean_windows"
            ]
        elif service_type == "deep_cleaning":
            return base_items + [
                "deep_clean_bathrooms", "kitchen_deep_clean",
                "dust_ceiling_fans", "clean_light_switches"
            ]
        else:  # recurring
            return base_items
    
    async def _check_timing_compliance(
        self, 
        job: JobSchema, 
        contractor: ContractorSchema
    ) -> Optional[ViolationType]:
        """
        Check timing compliance with 15-minute buffer.
        """
        if not job.actual_start_time:
            # No start time recorded - could be no-show
            time_since_scheduled = datetime.utcnow() - job.scheduled_date
            if time_since_scheduled > timedelta(hours=2):  # 2 hours past scheduled
                return ViolationType.NO_SHOW
            return None
        
        # Check if arrival was late
        scheduled_time = job.scheduled_date
        actual_arrival = job.actual_start_time
        buffer_time = timedelta(minutes=settings.checkin_buffer_minutes)  # 15 minutes
        
        if actual_arrival > scheduled_time + buffer_time:
            # Late arrival - check if communication was provided
            # In production, this would check Discord messages for prior communication
            return ViolationType.LATE_ARRIVAL
        
        return None
    
    def _calculate_compliance_score(
        self, 
        violations: List[ViolationType], 
        photo_quality_score: float
    ) -> float:
        """
        Calculate overall compliance score (0-100).
        """
        base_score = 100.0
        
        # Penalty for violations
        violation_penalties = {
            ViolationType.MISSING_PHOTOS: 25,
            ViolationType.POOR_PHOTO_QUALITY: 15,
            ViolationType.INCOMPLETE_CHECKLIST: 20,
            ViolationType.LATE_ARRIVAL: 10,
            ViolationType.NO_SHOW: 50,
            ViolationType.CUSTOMER_COMPLAINT: 30
        }
        
        for violation in violations:
            penalty = violation_penalties.get(violation, 10)
            base_score -= penalty
        
        # Factor in photo quality
        photo_weight = 0.3  # 30% weight for photo quality
        photo_contribution = (photo_quality_score / 10) * 100 * photo_weight
        
        final_score = (base_score * (1 - photo_weight)) + photo_contribution
        
        return max(0, min(100, final_score))
    
    async def _record_violations(
        self,
        job: JobSchema,
        contractor: ContractorSchema,
        violations: List[ViolationType],
        photo_result: PhotoValidationResult
    ) -> None:
        """
        Record violations and manage 3-strike system.
        """
        contractor_id = contractor.id
        
        # Initialize strike records if needed
        if contractor_id not in self.strike_records:
            self.strike_records[contractor_id] = []
        
        current_strikes = len(self.strike_records[contractor_id])
        
        for violation in violations:
            # Create strike record
            strike = StrikeRecord(
                contractor_id=contractor_id,
                strike_number=current_strikes + 1,
                violation_type=violation,
                description=self._generate_violation_description(violation, job, photo_result),
                evidence={
                    "job_id": job.id,
                    "scheduled_time": job.scheduled_date.isoformat(),
                    "actual_start_time": job.actual_start_time.isoformat() if job.actual_start_time else None,
                    "photo_issues": photo_result.issues,
                    "compliance_score": self._calculate_compliance_score([violation], photo_result.quality_score)
                },
                timestamp=datetime.utcnow(),
                job_id=job.id,
                requires_approval=(current_strikes + 1) >= 3  # 3rd strike needs approval
            )
            
            # Add to records
            self.strike_records[contractor_id].append(strike)
            current_strikes += 1
            
            # Send Discord notification
            await self._send_discord_strike_notification(strike, contractor)
            
            # Handle 3rd strike
            if strike.strike_number >= 3:
                await self._handle_third_strike(strike, contractor)
            
            logger.warning(f"Strike #{strike.strike_number} recorded for {contractor_id}: {violation.value}")
    
    def _generate_violation_description(
        self,
        violation: ViolationType,
        job: JobSchema,
        photo_result: PhotoValidationResult
    ) -> str:
        """Generate detailed violation description."""
        base_desc = f"Job {job.id} at {job.address}"
        
        if violation == ViolationType.MISSING_PHOTOS:
            missing = ", ".join(photo_result.missing_rooms)
            return f"{base_desc}: Missing required photos ({missing})"
        elif violation == ViolationType.POOR_PHOTO_QUALITY:
            issues = ", ".join(photo_result.technical_issues)
            return f"{base_desc}: Poor photo quality ({issues})"
        elif violation == ViolationType.INCOMPLETE_CHECKLIST:
            return f"{base_desc}: Incomplete checklist for {job.service_type}"
        elif violation == ViolationType.LATE_ARRIVAL:
            return f"{base_desc}: Late arrival without prior communication"
        elif violation == ViolationType.NO_SHOW:
            return f"{base_desc}: No-show without communication"
        else:
            return f"{base_desc}: {violation.value}"
    
    async def _send_discord_strike_notification(
        self, 
        strike: StrikeRecord, 
        contractor: ContractorSchema
    ) -> None:
        """
        Send strike notification to Discord #❌-strikes channel.
        """
        try:
            # Format strike message
            message = f"""
🚨 **STRIKE #{strike.strike_number}** - {contractor.name}

**Violation:** {strike.violation_type.value}
**Job:** {strike.job_id}
**Time:** {strike.timestamp.strftime('%Y-%m-%d %H:%M')}

**Details:** {strike.description}

**Current Total:** {strike.strike_number}/3 strikes
            """
            
            if strike.strike_number >= 3:
                message += f"\n⚠️ **3RD STRIKE - REQUIRES APPROVAL FOR PENALTY**"
            
            # In production, this would send to Discord API
            # For now, log the notification
            logger.info(f"Discord strike notification: {message}")
            
            # Store for Discord integration
            await self._queue_discord_message("❌-strikes", message)
            
        except Exception as e:
            logger.error(f"Discord strike notification error: {e}")
    
    async def _handle_third_strike(
        self, 
        strike: StrikeRecord, 
        contractor: ContractorSchema
    ) -> None:
        """
        Handle 3rd strike with human approval requirement.
        """
        try:
            # Create human approval request
            approval_request = HumanApprovalRequest(
                request_id=f"strike3_{contractor.id}_{strike.timestamp.strftime('%Y%m%d')}",
                request_type="third_strike_penalty",
                contractor_id=contractor.id,
                violation_details=QualityViolationSchema(
                    contractor_id=contractor.id,
                    job_id=strike.job_id,
                    violation_type=strike.violation_type,
                    description=strike.description,
                    evidence=strike.evidence,
                    strike_number=strike.strike_number
                ),
                recommended_action=f"Apply ${settings.violation_penalty} penalty and place on probation",
                evidence=[
                    f"Strike 1: {self.strike_records[contractor.id][0].description}",
                    f"Strike 2: {self.strike_records[contractor.id][1].description}",
                    f"Strike 3: {strike.description}"
                ],
                urgency=3,  # High urgency
                created_at=datetime.utcnow(),
                requires_response_by=datetime.utcnow() + timedelta(hours=24)
            )
            
            # Send to alerts channel for immediate attention
            alert_message = f"""
🚨 **IMMEDIATE ATTENTION REQUIRED** 🚨

**Contractor:** {contractor.name}
**3rd Strike Reached:** Penalty approval needed

**Recommended Action:** ${settings.violation_penalty} penalty + probation
**Decision Required By:** {approval_request.requires_response_by.strftime('%Y-%m-%d %H:%M')}

**Strike History:**
{chr(10).join(approval_request.evidence)}

React with ✅ to approve penalty or ❌ to override
            """
            
            await self._queue_discord_message("🚨-alerts", alert_message)
            
            logger.critical(f"3rd strike penalty approval required for {contractor.id}")
            
        except Exception as e:
            logger.error(f"3rd strike handling error: {e}")
    
    async def _queue_discord_message(self, channel: str, message: str) -> None:
        """
        Queue Discord message for sending.
        In production, this would integrate with Discord API.
        """
        # For now, store in a queue for the Discord integration layer
        # This will be implemented in Task 7: Integration Layer
        logger.info(f"Discord message queued for #{channel}: {message[:100]}...")
    
    def get_contractor_strikes(self, contractor_id: str) -> List[StrikeRecord]:
        """Get all strike records for contractor."""
        return self.strike_records.get(contractor_id, [])
    
    def get_strike_summary(self) -> Dict[str, Any]:
        """Get system-wide strike summary."""
        total_contractors = len(self.strike_records)
        total_strikes = sum(len(strikes) for strikes in self.strike_records.values())
        
        contractors_at_risk = sum(
            1 for strikes in self.strike_records.values() 
            if len(strikes) >= 2
        )
        
        recent_strikes = sum(
            1 for strikes in self.strike_records.values()
            for strike in strikes
            if strike.timestamp > datetime.utcnow() - timedelta(days=7)
        )
        
        return {
            "total_contractors_with_strikes": total_contractors,
            "total_strikes": total_strikes,
            "contractors_at_risk": contractors_at_risk,  # 2+ strikes
            "recent_strikes_7_days": recent_strikes,
            "average_strikes_per_contractor": total_strikes / max(1, total_contractors)
        }
    
    async def approve_third_strike_penalty(
        self, 
        contractor_id: str, 
        approved_by: str,
        apply_penalty: bool = True
    ) -> Dict[str, Any]:
        """
        Approve or deny 3rd strike penalty.
        """
        try:
            strikes = self.strike_records.get(contractor_id, [])
            third_strikes = [s for s in strikes if s.strike_number >= 3 and not s.approved_by]
            
            if not third_strikes:
                return {"error": "No pending 3rd strike approvals found"}
            
            # Process most recent 3rd strike
            strike = third_strikes[-1]
            strike.approved_by = approved_by
            
            if apply_penalty:
                strike.penalty_amount = Decimal(str(settings.violation_penalty))
                
                # Update contractor status to probation
                result = {
                    "action": "penalty_applied",
                    "penalty_amount": float(strike.penalty_amount),
                    "contractor_status": "probation",
                    "approved_by": approved_by,
                    "timestamp": datetime.utcnow()
                }
                
                # Send Discord confirmation
                message = f"""
✅ **3RD STRIKE PENALTY APPROVED**

**Contractor:** {contractor_id}
**Penalty:** ${strike.penalty_amount}
**Status:** On Probation
**Approved By:** {approved_by}

Contractor has been notified via Discord.
                """
                await self._queue_discord_message("❌-strikes", message)
                
            else:
                result = {
                    "action": "penalty_overridden",
                    "reason": "Management override",
                    "approved_by": approved_by,
                    "timestamp": datetime.utcnow()
                }
                
                # Send Discord override notification
                message = f"""
⚠️ **3RD STRIKE PENALTY OVERRIDDEN**

**Contractor:** {contractor_id}
**Overridden By:** {approved_by}
**Reason:** Management discretion

Strike remains on record but no penalty applied.
                """
                await self._queue_discord_message("❌-strikes", message)
            
            logger.info(f"3rd strike penalty processed for {contractor_id}: {result['action']}")
            return result
            
        except Exception as e:
            logger.error(f"3rd strike approval error: {e}")
            return {"error": str(e)}
    
    def clear_contractor_strikes(self, contractor_id: str, reason: str = "Reset") -> bool:
        """
        Clear all strikes for contractor (administrative function).
        """
        try:
            if contractor_id in self.strike_records:
                old_count = len(self.strike_records[contractor_id])
                self.strike_records[contractor_id] = []
                
                logger.info(f"Cleared {old_count} strikes for {contractor_id}: {reason}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing strikes for {contractor_id}: {e}")
            return False