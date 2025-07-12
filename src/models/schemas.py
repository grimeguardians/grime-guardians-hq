from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ServiceType(str, Enum):
    """Service type enumeration matching business requirements."""
    MOVE_OUT_IN = "move_out_in"
    DEEP_CLEANING = "deep_cleaning"
    RECURRING = "recurring"
    POST_CONSTRUCTION = "post_construction"
    COMMERCIAL = "commercial"
    HOURLY = "hourly"


class ContractorStatus(str, Enum):
    """Contractor status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_PROBATION = "on_probation"
    TERMINATED = "terminated"


class JobStatus(str, Enum):
    """Job status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REQUIRES_FOLLOWUP = "requires_followup"


class AgentType(str, Enum):
    """Agent type enumeration for the 8-agent system."""
    AVA = "ava"  # Orchestrator
    SOPHIA = "sophia"  # Booking
    KEITH = "keith"  # Check-in
    MAYA = "maya"  # Coaching
    IRIS = "iris"  # Onboarding
    DMITRI = "dmitri"  # Escalation
    BRUNO = "bruno"  # Bonus
    AIDEN = "aiden"  # Analytics


class MessagePriority(int, Enum):
    """Message priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class PricingRequest(BaseModel):
    """Request model for pricing calculations."""
    service_type: ServiceType
    rooms: int = Field(ge=0, le=20)
    full_baths: int = Field(ge=0, le=10)
    half_baths: int = Field(ge=0, le=10)
    square_footage: Optional[int] = Field(None, ge=0)
    add_ons: Optional[List[str]] = Field(default_factory=list)
    modifiers: Optional[Dict[str, bool]] = Field(default_factory=dict)
    
    @validator('add_ons')
    def validate_add_ons(cls, v):
        valid_addons = ["fridge_interior", "oven_interior", "cabinet_interior", "garage_cleaning", "carpet_shampooing"]
        if v:
            for addon in v:
                if addon not in valid_addons:
                    raise ValueError(f"Invalid add-on: {addon}")
        return v


class PricingResponse(BaseModel):
    """Response model for pricing calculations."""
    service_type: ServiceType
    base_price: Decimal
    room_charges: Decimal
    bathroom_charges: Decimal
    addon_charges: Decimal
    modifier_adjustments: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total_price: Decimal
    breakdown: Dict[str, Any]


class ContractorBase(BaseModel):
    """Base contractor model."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: str = Field(..., min_length=10, max_length=15)
    status: ContractorStatus = ContractorStatus.ACTIVE
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    pay_split_percentage: Decimal = Field(default=Decimal("0.45"), ge=0, le=1)
    geographic_preference: Optional[str] = None


class ContractorCreate(ContractorBase):
    """Model for creating a new contractor."""
    pass


class ContractorUpdate(BaseModel):
    """Model for updating contractor information."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    status: Optional[ContractorStatus] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    pay_split_percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    geographic_preference: Optional[str] = None


class Contractor(ContractorBase):
    """Full contractor model with database fields."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContractorPerformance(BaseModel):
    """Contractor performance tracking model."""
    contractor_id: str
    checklist_compliance_rate: Decimal = Field(ge=0, le=1)
    photo_submission_rate: Decimal = Field(ge=0, le=1)
    quality_score: Decimal = Field(ge=0, le=10)
    violation_count: int = Field(ge=0, le=3)
    jobs_completed: int = Field(ge=0)
    average_rating: Optional[Decimal] = Field(None, ge=0, le=5)
    referral_count: int = Field(ge=0)
    bonus_earned: Decimal = Field(ge=0)
    
    class Config:
        from_attributes = True


class JobBase(BaseModel):
    """Base job model."""
    client_name: str = Field(..., min_length=2, max_length=100)
    client_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    client_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    address: str = Field(..., min_length=10, max_length=200)
    service_type: ServiceType
    scheduled_datetime: datetime
    estimated_duration: Optional[int] = Field(None, ge=30, le=480)  # minutes
    special_instructions: Optional[str] = Field(None, max_length=500)
    pricing_details: Optional[Dict[str, Any]] = None


class JobCreate(JobBase):
    """Model for creating a new job."""
    contractor_id: Optional[str] = None


class JobUpdate(BaseModel):
    """Model for updating job information."""
    client_name: Optional[str] = Field(None, min_length=2, max_length=100)
    client_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    client_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    address: Optional[str] = Field(None, min_length=10, max_length=200)
    service_type: Optional[ServiceType] = None
    scheduled_datetime: Optional[datetime] = None
    estimated_duration: Optional[int] = Field(None, ge=30, le=480)
    special_instructions: Optional[str] = Field(None, max_length=500)
    status: Optional[JobStatus] = None
    contractor_id: Optional[str] = None
    pricing_details: Optional[Dict[str, Any]] = None


class Job(JobBase):
    """Full job model with database fields."""
    id: str
    status: JobStatus = JobStatus.SCHEDULED
    contractor_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentMessage(BaseModel):
    """Standardized agent message model."""
    agent_id: AgentType
    message_type: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=2000)
    priority: MessagePriority = MessagePriority.MEDIUM
    requires_response: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class AgentResponse(BaseModel):
    """Standardized agent response model."""
    agent_id: AgentType
    response_to: str  # correlation_id from original message
    content: str = Field(..., min_length=1, max_length=2000)
    success: bool = True
    error_message: Optional[str] = None
    actions_taken: Optional[List[str]] = Field(default_factory=list)
    next_actions: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComplianceViolation(BaseModel):
    """Model for tracking compliance violations."""
    contractor_id: str
    job_id: str
    violation_type: str  # "missing_photos", "incomplete_checklist", "late_checkin", etc.
    description: str
    severity: int = Field(ge=1, le=3)  # 1=warning, 2=strike, 3=immediate_action
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_notes: Optional[str] = None


class ComplianceResult(BaseModel):
    """Result of compliance check."""
    job_id: str
    contractor_id: str
    violations: List[str] = Field(default_factory=list)
    strike_count: int = Field(ge=0, le=3)
    compliance_score: Decimal = Field(ge=0, le=1)
    requires_action: bool = False
    recommended_actions: List[str] = Field(default_factory=list)


class CheckInEvent(BaseModel):
    """Model for contractor check-in events."""
    contractor_id: str
    job_id: str
    event_type: str  # "arrived", "started", "completed", "departed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = None
    notes: Optional[str] = None
    photo_urls: Optional[List[str]] = Field(default_factory=list)


class PerformanceMetric(BaseModel):
    """Model for performance metrics tracking."""
    contractor_id: str
    metric_type: str  # "quality_score", "efficiency", "client_satisfaction", etc.
    value: Decimal
    period_start: datetime
    period_end: datetime
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BonusCalculation(BaseModel):
    """Model for bonus calculations."""
    contractor_id: str
    bonus_type: str  # "referral", "performance", "milestone", etc.
    amount: Decimal = Field(ge=0)
    description: str
    earned_date: datetime = Field(default_factory=datetime.utcnow)
    paid_date: Optional[datetime] = None
    status: str = Field(default="pending")  # "pending", "approved", "paid"


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    agents_status: Dict[str, str] = Field(default_factory=dict)
    integrations_status: Dict[str, str] = Field(default_factory=dict)
    database_status: str = "connected"
    uptime_seconds: int = 0