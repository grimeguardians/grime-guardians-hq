"""
SQLAlchemy database models for Grime Guardians Agentic Suite
Following exact business rules from CLAUDE.md and 12-factor patterns
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from ..config.database import Base
from .types import ServiceType, MessageType, JobStatus, ViolationType, ContractorStatus, AgentStatus


class TimestampMixin:
    """Mixin for created/updated timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Agent(Base, TimestampMixin):
    """Agent model for 8-agent system tracking."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True)  # e.g., "ava", "sophia", "keith"
    name = Column(String, nullable=False)  # e.g., "Ava Orchestrator"
    role = Column(String, nullable=False)
    status = Column(String, nullable=False, default=AgentStatus.ACTIVE)
    priority = Column(Integer, nullable=False)
    config = Column(JSON, nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    error_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)

    # Relationships
    messages = relationship("AgentMessage", back_populates="agent")


class Contractor(Base, TimestampMixin):
    """Contractor model with 1099 compliance tracking."""
    __tablename__ = "contractors"

    id = Column(String, primary_key=True)  # e.g., "jennifer", "olga"
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default=ContractorStatus.ACTIVE)
    hourly_rate = Column(Numeric(10, 2), nullable=True)  # For specific rate contractors
    pay_split_percentage = Column(Numeric(5, 2), nullable=False, default=45.0)  # 45% default
    territory = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    w9_submitted = Column(Boolean, default=False)
    contract_signed = Column(Boolean, default=False)
    
    # Performance tracking
    total_jobs = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    current_strike_count = Column(Integer, default=0)
    
    # Relationships
    jobs = relationship("Job", back_populates="contractor")
    performance_records = relationship("ContractorPerformance", back_populates="contractor")
    violations = relationship("QualityViolation", back_populates="contractor")


class Job(Base, TimestampMixin):
    """Job model tracking complete job lifecycle."""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    service_type = Column(String, nullable=False)  # ServiceType enum
    status = Column(String, nullable=False, default=JobStatus.SCHEDULED)
    
    # Client information
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    
    # Job details
    address = Column(Text, nullable=False)
    zip_code = Column(String, nullable=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    estimated_duration = Column(Integer, nullable=True)  # minutes
    
    # Pricing
    base_price = Column(Numeric(10, 2), nullable=False)
    final_price = Column(Numeric(10, 2), nullable=False)
    pricing_breakdown = Column(JSON, nullable=True)
    
    # Quality tracking
    photos_submitted = Column(Boolean, default=False)
    checklist_completed = Column(Boolean, default=False)
    quality_score = Column(Numeric(3, 1), nullable=True)  # 0-10 scale
    
    # Contractor assignment
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=True)
    contractor = relationship("Contractor", back_populates="jobs")
    
    # Timing
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Notes and special instructions
    special_instructions = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)


class ContractorPerformance(Base, TimestampMixin):
    """Weekly performance tracking for contractors."""
    __tablename__ = "contractor_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)
    week_ending = Column(DateTime(timezone=True), nullable=False)
    
    # Compliance metrics
    checklist_compliance_rate = Column(Numeric(5, 2), nullable=False)  # 0-100%
    photo_submission_rate = Column(Numeric(5, 2), nullable=False)  # 0-100%
    on_time_percentage = Column(Numeric(5, 2), nullable=False)  # 0-100%
    
    # Quality metrics
    average_quality_score = Column(Numeric(3, 1), nullable=True)  # 0-10
    customer_satisfaction = Column(Numeric(3, 1), nullable=True)  # 0-10
    
    # Productivity metrics
    jobs_completed = Column(Integer, nullable=False, default=0)
    total_revenue_generated = Column(Numeric(10, 2), nullable=False, default=0)
    average_job_duration = Column(Integer, nullable=True)  # minutes
    
    # Violations
    violation_count = Column(Integer, nullable=False, default=0)
    
    contractor = relationship("Contractor", back_populates="performance_records")


class AgentMessage(Base, TimestampMixin):
    """Agent communication and message tracking."""
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    message_type = Column(String, nullable=False)  # MessageType enum
    content = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=3)  # 1=critical, 5=background
    
    # Response tracking
    requires_response = Column(Boolean, default=False)
    response_content = Column(Text, nullable=True)
    response_time = Column(DateTime(timezone=True), nullable=True)
    
    # Context
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=True)
    
    # Processing
    processed = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    agent = relationship("Agent", back_populates="messages")


class QualityViolation(Base, TimestampMixin):
    """Quality violations for 3-strike system."""
    __tablename__ = "quality_violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    violation_type = Column(String, nullable=False)  # ViolationType enum
    
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)  # Photos, timestamps, etc.
    
    # Strike tracking
    strike_number = Column(Integer, nullable=False)  # 1, 2, or 3
    penalty_applied = Column(Numeric(6, 2), nullable=True)  # Dollar amount
    penalty_approved_by = Column(String, nullable=True)  # Human approver
    penalty_approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    
    contractor = relationship("Contractor", back_populates="violations")


class PricingQuote(Base, TimestampMixin):
    """Pricing calculations for audit trail."""
    __tablename__ = "pricing_quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_type = Column(String, nullable=False)
    
    # Input parameters
    rooms = Column(Integer, nullable=False, default=0)
    full_baths = Column(Integer, nullable=False, default=0)
    half_baths = Column(Integer, nullable=False, default=0)
    square_footage = Column(Integer, nullable=True)
    
    # Modifiers
    pet_homes = Column(Boolean, default=False)
    buildup = Column(Boolean, default=False)
    add_ons = Column(JSON, nullable=True)
    
    # Calculated prices
    base_price = Column(Numeric(10, 2), nullable=False)
    modifier_total = Column(Numeric(10, 2), nullable=False, default=0)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False)
    final_price = Column(Numeric(10, 2), nullable=False)
    
    # Audit info
    calculation_breakdown = Column(JSON, nullable=False)
    quoted_by_agent = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    
    # Conversion tracking
    converted_to_job = Column(Boolean, default=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)