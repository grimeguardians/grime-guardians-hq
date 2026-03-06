"""
Database Operation Tools
Standardized CRUD operations for all business entities
Provides safe, validated database access for agents
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Type
from decimal import Decimal
import json

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, ValidationError

from ..models.database import (
    Base, Job, Contractor, Customer, Agent, QualityViolation,
    PerformanceRecord, PaymentRecord, KPISnapshot
)
from ..models.schemas import (
    JobSchema, ContractorSchema, CustomerSchema, AgentSchema,
    QualityViolationSchema, PerformanceMetrics, PaySplitCalculation
)
from ..models.types import JobStatus, ContractorStatus, ViolationType
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseError(Exception):
    """Custom database operation error."""
    pass


class DatabaseValidator:
    """Validates database operations for business rules."""
    
    @staticmethod
    def validate_job_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate job data before database operations."""
        required_fields = ['customer_id', 'service_type', 'address', 'scheduled_date']
        
        for field in required_fields:
            if field not in job_data or job_data[field] is None:
                raise ValidationError(f"Required field '{field}' is missing")
        
        # Validate service type
        valid_service_types = ['recurring', 'deep_cleaning', 'move_out_in', 'one_time']
        if job_data['service_type'] not in valid_service_types:
            raise ValidationError(f"Invalid service type: {job_data['service_type']}")
        
        # Validate pricing if present
        if 'quoted_price' in job_data and job_data['quoted_price']:
            if not isinstance(job_data['quoted_price'], (int, float, Decimal)):
                raise ValidationError("quoted_price must be numeric")
            if job_data['quoted_price'] <= 0:
                raise ValidationError("quoted_price must be positive")
        
        return job_data
    
    @staticmethod
    def validate_contractor_data(contractor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate contractor data before database operations."""
        required_fields = ['name', 'email', 'phone']
        
        for field in required_fields:
            if field not in contractor_data or not contractor_data[field]:
                raise ValidationError(f"Required field '{field}' is missing")
        
        # Validate hourly rate
        if 'hourly_rate' in contractor_data:
            rate = contractor_data['hourly_rate']
            if not isinstance(rate, (int, float, Decimal)):
                raise ValidationError("hourly_rate must be numeric")
            if rate < 15 or rate > 50:  # Business rule: $15-50/hr range
                raise ValidationError("hourly_rate must be between $15-50/hr")
        
        return contractor_data


class DatabaseTools:
    """
    Comprehensive database tools for agent operations.
    Provides safe, validated CRUD operations with business rule enforcement.
    """
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.validator = DatabaseValidator()
        
        # Operation tracking
        self.operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'jobs_created': 0,
            'jobs_updated': 0,
            'contractors_created': 0,
            'violations_recorded': 0
        }
    
    async def initialize(self, database_url: str = None) -> bool:
        """Initialize database connection."""
        try:
            database_url = database_url or settings.database_url
            self.engine = create_async_engine(database_url, echo=settings.debug)
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tools initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return False
    
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.engine:
            raise DatabaseError("Database not initialized")
        
        return AsyncSession(self.engine)
    
    # Job operations
    
    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new job record."""
        try:
            self.operation_stats['total_operations'] += 1
            
            # Validate data
            validated_data = self.validator.validate_job_data(job_data)
            
            async with self.get_session() as session:
                # Create job record
                job = Job(**validated_data)
                session.add(job)
                await session.commit()
                await session.refresh(job)
                
                self.operation_stats['successful_operations'] += 1
                self.operation_stats['jobs_created'] += 1
                
                logger.info(f"Job created: {job.id}")
                
                return {
                    'status': 'success',
                    'job_id': job.id,
                    'message': 'Job created successfully'
                }
                
        except ValidationError as e:
            self.operation_stats['failed_operations'] += 1
            logger.warning(f"Job creation validation error: {e}")
            return {
                'status': 'error',
                'error': 'validation_error',
                'message': str(e)
            }
        except Exception as e:
            self.operation_stats['failed_operations'] += 1
            logger.error(f"Job creation error: {e}")
            return {
                'status': 'error',
                'error': 'database_error',
                'message': str(e)
            }
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID with related data."""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(Job)
                    .options(
                        joinedload(Job.customer),
                        joinedload(Job.contractor),
                        selectinload(Job.violations)
                    )
                    .where(Job.id == job_id)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    return None
                
                return {
                    'id': job.id,
                    'customer_id': job.customer_id,
                    'contractor_id': job.contractor_id,
                    'service_type': job.service_type,
                    'status': job.status.value,
                    'address': job.address,
                    'scheduled_date': job.scheduled_date.isoformat(),
                    'actual_start_time': job.actual_start_time.isoformat() if job.actual_start_time else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'quoted_price': float(job.quoted_price) if job.quoted_price else None,
                    'final_price': float(job.final_price) if job.final_price else None,
                    'square_footage': job.square_footage,
                    'bedrooms': job.bedrooms,
                    'bathrooms': job.bathrooms,
                    'special_instructions': job.special_instructions,
                    'customer': {
                        'name': job.customer.name if job.customer else None,
                        'email': job.customer.email if job.customer else None,
                        'phone': job.customer.phone if job.customer else None
                    } if job.customer else None,
                    'contractor': {
                        'name': job.contractor.name if job.contractor else None,
                        'email': job.contractor.email if job.contractor else None,
                        'phone': job.contractor.phone if job.contractor else None
                    } if job.contractor else None,
                    'violations': [
                        {
                            'id': v.id,
                            'violation_type': v.violation_type.value,
                            'description': v.description,
                            'created_at': v.created_at.isoformat()
                        } for v in job.violations
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        updates: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update job status and related fields."""
        try:
            self.operation_stats['total_operations'] += 1
            updates = updates or {}
            
            async with self.get_session() as session:
                # Get job
                result = await session.execute(select(Job).where(Job.id == job_id))
                job = result.scalar_one_or_none()
                
                if not job:
                    return {
                        'status': 'error',
                        'error': 'not_found',
                        'message': f'Job {job_id} not found'
                    }
                
                # Update status
                job.status = status
                job.updated_at = datetime.utcnow()
                
                # Apply additional updates
                for field, value in updates.items():
                    if hasattr(job, field):
                        setattr(job, field, value)
                
                # Set timestamps based on status
                if status == JobStatus.IN_PROGRESS and not job.actual_start_time:
                    job.actual_start_time = datetime.utcnow()
                elif status == JobStatus.COMPLETED and not job.completed_at:
                    job.completed_at = datetime.utcnow()
                
                await session.commit()
                
                self.operation_stats['successful_operations'] += 1
                self.operation_stats['jobs_updated'] += 1
                
                logger.info(f"Job {job_id} status updated to {status.value}")
                
                return {
                    'status': 'success',
                    'job_id': job_id,
                    'new_status': status.value,
                    'message': 'Job status updated successfully'
                }
                
        except Exception as e:
            self.operation_stats['failed_operations'] += 1
            logger.error(f"Error updating job {job_id}: {e}")
            return {
                'status': 'error',
                'error': 'database_error',
                'message': str(e)
            }
    
    async def get_jobs_by_contractor(
        self, 
        contractor_id: str, 
        status_filter: List[JobStatus] = None,
        date_range: Dict[str, datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get jobs for specific contractor with filters."""
        try:
            async with self.get_session() as session:
                query = select(Job).where(Job.contractor_id == contractor_id)
                
                # Apply status filter
                if status_filter:
                    query = query.where(Job.status.in_(status_filter))
                
                # Apply date range filter
                if date_range:
                    if 'start_date' in date_range:
                        query = query.where(Job.scheduled_date >= date_range['start_date'])
                    if 'end_date' in date_range:
                        query = query.where(Job.scheduled_date <= date_range['end_date'])
                
                query = query.order_by(Job.scheduled_date.desc())
                
                result = await session.execute(query)
                jobs = result.scalars().all()
                
                return [
                    {
                        'id': job.id,
                        'service_type': job.service_type,
                        'status': job.status.value,
                        'address': job.address,
                        'scheduled_date': job.scheduled_date.isoformat(),
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                        'final_price': float(job.final_price) if job.final_price else None
                    }
                    for job in jobs
                ]
                
        except Exception as e:
            logger.error(f"Error getting jobs for contractor {contractor_id}: {e}")
            return []
    
    # Contractor operations
    
    async def create_contractor(self, contractor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contractor record."""
        try:
            self.operation_stats['total_operations'] += 1
            
            # Validate data
            validated_data = self.validator.validate_contractor_data(contractor_data)
            
            async with self.get_session() as session:
                # Check for duplicate email/phone
                existing = await session.execute(
                    select(Contractor).where(
                        or_(
                            Contractor.email == validated_data['email'],
                            Contractor.phone == validated_data['phone']
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    return {
                        'status': 'error',
                        'error': 'duplicate',
                        'message': 'Contractor with this email or phone already exists'
                    }
                
                # Create contractor
                contractor = Contractor(**validated_data)
                session.add(contractor)
                await session.commit()
                await session.refresh(contractor)
                
                self.operation_stats['successful_operations'] += 1
                self.operation_stats['contractors_created'] += 1
                
                logger.info(f"Contractor created: {contractor.id}")
                
                return {
                    'status': 'success',
                    'contractor_id': contractor.id,
                    'message': 'Contractor created successfully'
                }
                
        except ValidationError as e:
            self.operation_stats['failed_operations'] += 1
            logger.warning(f"Contractor creation validation error: {e}")
            return {
                'status': 'error',
                'error': 'validation_error',
                'message': str(e)
            }
        except Exception as e:
            self.operation_stats['failed_operations'] += 1
            logger.error(f"Contractor creation error: {e}")
            return {
                'status': 'error',
                'error': 'database_error',
                'message': str(e)
            }
    
    async def get_contractor(self, contractor_id: str) -> Optional[Dict[str, Any]]:
        """Get contractor by ID with performance data."""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(Contractor)
                    .options(
                        selectinload(Contractor.jobs),
                        selectinload(Contractor.violations),
                        selectinload(Contractor.performance_records)
                    )
                    .where(Contractor.id == contractor_id)
                )
                contractor = result.scalar_one_or_none()
                
                if not contractor:
                    return None
                
                return {
                    'id': contractor.id,
                    'name': contractor.name,
                    'email': contractor.email,
                    'phone': contractor.phone,
                    'status': contractor.status.value,
                    'hourly_rate': float(contractor.hourly_rate) if contractor.hourly_rate else None,
                    'preferred_territory': contractor.preferred_territory,
                    'emergency_contact': contractor.emergency_contact,
                    'start_date': contractor.start_date.isoformat() if contractor.start_date else None,
                    'total_jobs': len(contractor.jobs),
                    'total_violations': len(contractor.violations),
                    'recent_performance': [
                        {
                            'period_start': pr.period_start.isoformat(),
                            'overall_score': float(pr.overall_score),
                            'performance_tier': pr.performance_tier
                        }
                        for pr in contractor.performance_records[-5:]  # Last 5 records
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting contractor {contractor_id}: {e}")
            return None
    
    async def get_available_contractors(
        self, 
        territory: str = None,
        min_rating: float = None
    ) -> List[Dict[str, Any]]:
        """Get list of available contractors with filters."""
        try:
            async with self.get_session() as session:
                query = select(Contractor).where(Contractor.status == ContractorStatus.AVAILABLE)
                
                if territory:
                    query = query.where(Contractor.preferred_territory == territory)
                
                result = await session.execute(query)
                contractors = result.scalars().all()
                
                contractor_list = []
                for contractor in contractors:
                    # Get recent performance if min_rating specified
                    if min_rating:
                        perf_result = await session.execute(
                            select(PerformanceRecord)
                            .where(PerformanceRecord.contractor_id == contractor.id)
                            .order_by(PerformanceRecord.period_end.desc())
                            .limit(1)
                        )
                        recent_perf = perf_result.scalar_one_or_none()
                        
                        if recent_perf and recent_perf.overall_score < min_rating:
                            continue
                    
                    contractor_list.append({
                        'id': contractor.id,
                        'name': contractor.name,
                        'hourly_rate': float(contractor.hourly_rate) if contractor.hourly_rate else None,
                        'preferred_territory': contractor.preferred_territory,
                        'status': contractor.status.value
                    })
                
                return contractor_list
                
        except Exception as e:
            logger.error(f"Error getting available contractors: {e}")
            return []
    
    # Quality violation operations
    
    async def record_quality_violation(
        self, 
        violation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record quality violation."""
        try:
            self.operation_stats['total_operations'] += 1
            
            required_fields = ['contractor_id', 'job_id', 'violation_type', 'description']
            for field in required_fields:
                if field not in violation_data:
                    raise ValidationError(f"Required field '{field}' is missing")
            
            async with self.get_session() as session:
                violation = QualityViolation(**violation_data)
                session.add(violation)
                await session.commit()
                await session.refresh(violation)
                
                self.operation_stats['successful_operations'] += 1
                self.operation_stats['violations_recorded'] += 1
                
                logger.info(f"Quality violation recorded: {violation.id}")
                
                return {
                    'status': 'success',
                    'violation_id': violation.id,
                    'message': 'Quality violation recorded successfully'
                }
                
        except ValidationError as e:
            self.operation_stats['failed_operations'] += 1
            logger.warning(f"Violation recording validation error: {e}")
            return {
                'status': 'error',
                'error': 'validation_error',
                'message': str(e)
            }
        except Exception as e:
            self.operation_stats['failed_operations'] += 1
            logger.error(f"Violation recording error: {e}")
            return {
                'status': 'error',
                'error': 'database_error',
                'message': str(e)
            }
    
    async def get_contractor_violations(
        self, 
        contractor_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get contractor violations within date range."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            async with self.get_session() as session:
                result = await session.execute(
                    select(QualityViolation)
                    .where(
                        and_(
                            QualityViolation.contractor_id == contractor_id,
                            QualityViolation.created_at >= cutoff_date
                        )
                    )
                    .order_by(QualityViolation.created_at.desc())
                )
                violations = result.scalars().all()
                
                return [
                    {
                        'id': v.id,
                        'job_id': v.job_id,
                        'violation_type': v.violation_type.value,
                        'description': v.description,
                        'strike_number': v.strike_number,
                        'penalty_amount': float(v.penalty_amount) if v.penalty_amount else None,
                        'created_at': v.created_at.isoformat(),
                        'resolved_at': v.resolved_at.isoformat() if v.resolved_at else None
                    }
                    for v in violations
                ]
                
        except Exception as e:
            logger.error(f"Error getting violations for contractor {contractor_id}: {e}")
            return []
    
    # Performance tracking
    
    async def record_performance_metrics(
        self, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record contractor performance metrics."""
        try:
            self.operation_stats['total_operations'] += 1
            
            async with self.get_session() as session:
                performance = PerformanceRecord(**performance_data)
                session.add(performance)
                await session.commit()
                await session.refresh(performance)
                
                self.operation_stats['successful_operations'] += 1
                
                logger.info(f"Performance metrics recorded for contractor {performance.contractor_id}")
                
                return {
                    'status': 'success',
                    'performance_id': performance.id,
                    'message': 'Performance metrics recorded successfully'
                }
                
        except Exception as e:
            self.operation_stats['failed_operations'] += 1
            logger.error(f"Performance recording error: {e}")
            return {
                'status': 'error',
                'error': 'database_error',
                'message': str(e)
            }
    
    # Analytics and reporting
    
    async def get_business_analytics(
        self, 
        date_range: Dict[str, datetime] = None
    ) -> Dict[str, Any]:
        """Get business analytics data."""
        try:
            date_range = date_range or {
                'start_date': datetime.utcnow() - timedelta(days=30),
                'end_date': datetime.utcnow()
            }
            
            async with self.get_session() as session:
                # Jobs analytics
                jobs_result = await session.execute(
                    select(
                        func.count(Job.id).label('total_jobs'),
                        func.sum(Job.final_price).label('total_revenue'),
                        func.avg(Job.final_price).label('avg_job_value')
                    )
                    .where(
                        and_(
                            Job.completed_at >= date_range['start_date'],
                            Job.completed_at <= date_range['end_date'],
                            Job.status == JobStatus.COMPLETED
                        )
                    )
                )
                jobs_stats = jobs_result.first()
                
                # Contractor analytics
                contractors_result = await session.execute(
                    select(
                        func.count(Contractor.id).label('total_contractors'),
                        func.count(Contractor.id).filter(
                            Contractor.status == ContractorStatus.AVAILABLE
                        ).label('available_contractors')
                    )
                )
                contractor_stats = contractors_result.first()
                
                # Violation analytics
                violations_result = await session.execute(
                    select(
                        func.count(QualityViolation.id).label('total_violations'),
                        func.count(QualityViolation.id).filter(
                            QualityViolation.strike_number >= 3
                        ).label('third_strikes')
                    )
                    .where(
                        QualityViolation.created_at >= date_range['start_date']
                    )
                )
                violation_stats = violations_result.first()
                
                return {
                    'period': {
                        'start_date': date_range['start_date'].isoformat(),
                        'end_date': date_range['end_date'].isoformat()
                    },
                    'jobs': {
                        'total_completed': jobs_stats.total_jobs or 0,
                        'total_revenue': float(jobs_stats.total_revenue or 0),
                        'average_job_value': float(jobs_stats.avg_job_value or 0)
                    },
                    'contractors': {
                        'total_contractors': contractor_stats.total_contractors or 0,
                        'available_contractors': contractor_stats.available_contractors or 0
                    },
                    'quality': {
                        'total_violations': violation_stats.total_violations or 0,
                        'third_strikes': violation_stats.third_strikes or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting business analytics: {e}")
            return {
                'error': str(e),
                'period': date_range
            }
    
    async def get_operation_stats(self) -> Dict[str, Any]:
        """Get database operation statistics."""
        stats = self.operation_stats.copy()
        
        if stats['total_operations'] > 0:
            stats['success_rate'] = (stats['successful_operations'] / stats['total_operations']) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
    
    async def cleanup(self) -> None:
        """Cleanup database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections cleaned up")