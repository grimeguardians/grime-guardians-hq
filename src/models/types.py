"""
Custom types and enums for Grime Guardians Agentic Suite
Following business rules from CLAUDE.md
"""

from enum import Enum
from typing import Dict, List


class ServiceType(str, Enum):
    """Service types matching GG Operating Manual pricing structure."""
    # Lead magnet / paid trial
    ELITE_RESET = "elite_reset"
    # Move-out (primary profit center)
    LISTING_POLISH = "listing_polish"
    DEEP_RESET = "deep_reset"
    # Continuity partnerships (back-end revenue engine)
    ESSENTIALS = "essentials"
    PRESTIGE = "prestige"
    VIP_ELITE = "vip_elite"
    # B2B / commercial
    B2B_TURNOVER = "b2b_turnover"
    POST_CONSTRUCTION = "post_construction"
    COMMERCIAL = "commercial"
    # Specialty
    HOURLY = "hourly"
    QUARTERLY_DEEP_RESET = "quarterly_deep_reset"
    AUTOPILOT_MONTHLY = "autopilot_monthly"
    ESTATE_PROTOCOL = "estate_protocol"


class MessageType(str, Enum):
    """Agent message types for classification."""
    JOB_ASSIGNMENT = "job_assignment"
    STATUS_UPDATE = "status_update"
    QUALITY_VIOLATION = "quality_violation"
    PERFORMANCE_FEEDBACK = "performance_feedback"
    ESCALATION = "escalation"
    COMPLIANCE_CHECK = "compliance_check"
    BONUS_CALCULATION = "bonus_calculation"
    ANALYTICS_REPORT = "analytics_report"


class JobStatus(str, Enum):
    """Job status tracking throughout lifecycle."""
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    QUALITY_REVIEW = "quality_review"
    APPROVED = "approved"
    CANCELLED = "cancelled"
    REWORK_REQUIRED = "rework_required"


class ViolationType(str, Enum):
    """Quality violation types for 3-strike system."""
    MISSING_PHOTOS = "missing_photos"
    INCOMPLETE_CHECKLIST = "incomplete_checklist"
    LATE_ARRIVAL = "late_arrival"
    NO_SHOW = "no_show"
    POOR_PHOTO_QUALITY = "poor_photo_quality"
    CUSTOMER_COMPLAINT = "customer_complaint"
    SOP_VIOLATION = "sop_violation"


class ContractorStatus(str, Enum):
    """Contractor status for independence compliance."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_PROBATION = "on_probation"  # After 2 strikes
    TERMINATED = "terminated"  # After 3 strikes with approval


class AgentStatus(str, Enum):
    """Agent operational status."""
    ACTIVE = "active"
    PAUSED = "paused"
    PROCESSING = "processing"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class PriorityLevel(int, Enum):
    """Message priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class GeographicTerritory(str, Enum):
    """Geographic territories for contractor dispatch."""
    NORTH = "north"
    EAGAN = "eagan"
    MINNETONKA = "minnetonka"
    EDEN_PRAIRIE = "eden_prairie"
    EDINA = "edina"
    CENTRAL = "central"
    WEST_SW = "west_sw"
    MINNEAPOLIS = "minneapolis"
    SAINT_PAUL = "saint_paul"
    EAST_METRO = "east_metro"
    SOUTH = "south"


# Active team coverage (soft territories — 30-45 min travel ok if motivated)
CONTRACTOR_TERRITORIES: Dict[str, list] = {
    "katy_crew":   ["south", "central", "west_sw", "east_metro", "eagan",
                    "minnetonka", "eden_prairie", "edina", "minneapolis", "saint_paul"],
    "anna_oksana": ["south", "central", "west_sw", "east_metro", "eagan",
                    "minnetonka", "eden_prairie", "edina", "minneapolis", "saint_paul", "north"],
    "kateryna":    ["north", "eagan", "minnetonka", "eden_prairie", "edina", "central"],
    "liuda":       ["north"],
}

REQUIRED_PHOTOS: List[str] = [
    "kitchen", "bathrooms", "entry_area", "impacted_rooms"
]

CHECKLIST_TYPES: List[str] = [
    "move_in_out", "deep_cleaning", "recurring"
]