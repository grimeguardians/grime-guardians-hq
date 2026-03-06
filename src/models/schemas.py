"""
Pydantic schemas for data validation and API responses
Following 12-factor methodology with structured outputs
"""

from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any

from .types import ServiceType, MessageType, JobStatus, ViolationType, ContractorStatus


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True


class PricingRequest(BaseSchema):
    """Request schema for pricing calculations."""
    service_type: ServiceType
    rooms: int = Field(ge=0, le=20)
    full_baths: int = Field(ge=0, le=10) 
    half_baths: int = Field(ge=0, le=10)
    square_footage: Optional[int] = Field(None, ge=0)
    pet_homes: bool = False
    buildup: bool = False
    add_ons: Optional[List[str]] = None
    
    @validator('add_ons')
    def validate_add_ons(cls, v):
        if v is None:
            return []
        valid_add_ons = ["fridge_interior", "oven_interior", "cabinet_interior", "garage_cleaning", "carpet_shampooing"]
        for add_on in v:
            if add_on not in valid_add_ons:
                raise ValueError(f"Invalid add-on: {add_on}")
        return v


class PricingResponse(BaseSchema):
    """Response schema for pricing calculations."""
    service_type: ServiceType
    base_price: Decimal
    room_charges: Decimal
    bathroom_charges: Decimal
    add_on_charges: Decimal
    modifier_multiplier: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    final_price: Decimal
    breakdown: Dict[str, Any]
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AgentMessageSchema(BaseSchema):
    """Schema for agent communication messages."""
    agent_id: str
    message_type: MessageType
    content: str
    priority: int = Field(ge=1, le=5, default=3)
    requires_response: bool = False
    job_id: Optional[str] = None
    contractor_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseSchema):
    """Schema for agent responses."""
    agent_id: str
    status: str
    response: str
    actions_taken: List[str] = []
    requires_escalation: bool = False
    next_steps: Optional[List[str]] = None
    processing_time: Optional[float] = None


class ContractorSchema(BaseSchema):
    """Schema for contractor information."""
    id: str
    name: str
    status: ContractorStatus
    hourly_rate: Optional[Decimal] = None
    pay_split_percentage: Decimal = Field(ge=0, le=100)
    territory: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    w9_submitted: bool = False
    contract_signed: bool = False
    total_jobs: int = 0
    violation_count: int = 0
    current_strike_count: int = Field(ge=0, le=3, default=0)


class JobSchema(BaseSchema):
    """Schema for job information."""
    id: str
    service_type: ServiceType
    status: JobStatus
    client_name: str
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    address: str
    zip_code: Optional[str] = None
    scheduled_date: datetime
    estimated_duration: Optional[int] = None
    base_price: Decimal
    final_price: Decimal
    contractor_id: Optional[str] = None
    photos_submitted: bool = False
    checklist_completed: bool = False
    quality_score: Optional[Decimal] = Field(None, ge=0, le=10)
    special_instructions: Optional[str] = None


class ComplianceResult(BaseSchema):
    """Schema for quality compliance check results."""
    job_id: str
    contractor_id: str
    violations: List[ViolationType] = []
    strike_count: int = Field(ge=0, le=3)
    photos_valid: bool
    checklist_complete: bool
    compliance_score: Decimal = Field(ge=0, le=100)
    recommendations: List[str] = []
    requires_human_review: bool = False


class PerformanceMetrics(BaseSchema):
    """Schema for contractor performance metrics."""
    contractor_id: str
    week_ending: datetime
    checklist_compliance_rate: Decimal = Field(ge=0, le=100)
    photo_submission_rate: Decimal = Field(ge=0, le=100)
    on_time_percentage: Decimal = Field(ge=0, le=100)
    average_quality_score: Optional[Decimal] = Field(None, ge=0, le=10)
    customer_satisfaction: Optional[Decimal] = Field(None, ge=0, le=10)
    jobs_completed: int = Field(ge=0)
    total_revenue_generated: Decimal = Field(ge=0)
    violation_count: int = Field(ge=0)


class QualityViolationSchema(BaseSchema):
    """Schema for quality violations."""
    contractor_id: str
    job_id: Optional[str] = None
    violation_type: ViolationType
    description: str
    evidence: Optional[Dict[str, Any]] = None
    strike_number: int = Field(ge=1, le=3)
    penalty_amount: Optional[Decimal] = None
    requires_approval: bool = True


class HumanApprovalRequest(BaseSchema):
    """Schema for human approval requests."""
    request_id: str
    request_type: str
    contractor_id: str
    violation_details: QualityViolationSchema
    recommended_action: str
    evidence: List[str] = []
    urgency: int = Field(ge=1, le=5)
    created_at: datetime
    requires_response_by: Optional[datetime] = None


class KPISnapshot(BaseSchema):
    """Schema for KPI dashboard snapshots."""
    date: datetime
    jobs_completed_today: int
    active_contractors: int
    average_completion_time: Optional[int]  # minutes
    checklist_compliance_rate: Decimal
    photo_submission_rate: Decimal
    customer_satisfaction_score: Optional[Decimal]
    revenue_today: Decimal
    revenue_month_to_date: Decimal
    violations_today: int
    escalations_pending: int


class AgentHealthStatus(BaseSchema):
    """Schema for agent health monitoring."""
    agent_id: str
    status: str
    last_activity: datetime
    messages_processed_today: int
    success_rate: Decimal = Field(ge=0, le=100)
    average_response_time: Optional[float]  # seconds
    error_count: int = 0
    uptime_percentage: Decimal = Field(ge=0, le=100)


class BusinessContext(BaseSchema):
    """Schema for unified business context."""
    active_jobs: List[JobSchema]
    contractor_statuses: List[ContractorSchema]
    current_kpis: KPISnapshot
    pending_violations: List[QualityViolationSchema]
    agent_statuses: List[AgentHealthStatus]
    system_alerts: List[str] = []