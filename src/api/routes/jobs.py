"""
Job Management Endpoints
API routes for managing cleaning jobs and scheduling operations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from decimal import Decimal

from ...models.jobs import JobRecord, JobStatus
from ...models.pricing import PricingCalculation
from ...integrations import get_integration_manager

router = APIRouter()


class JobRequest(BaseModel):
    """Job creation request model."""
    client_phone: str = Field(..., description="Client phone number")
    client_name: str = Field(..., description="Client name")
    service_type: str = Field(..., description="Type of cleaning service")
    property_address: str = Field(..., description="Property address")
    bedrooms: int = Field(1, ge=1, description="Number of bedrooms")
    bathrooms: int = Field(1, ge=1, description="Number of bathrooms")
    square_footage: Optional[int] = Field(None, ge=1, description="Square footage")
    pet_friendly: bool = Field(False, description="Pet-friendly cleaning required")
    preferred_date: Optional[str] = Field(None, description="Preferred date (YYYY-MM-DD)")
    special_instructions: Optional[str] = Field(None, description="Special instructions")


class JobResponse(BaseModel):
    """Job response model."""
    job_id: str
    client_name: str
    client_phone: str
    service_type: str
    property_address: str
    assigned_contractor: Optional[str] = None
    scheduled_date: Optional[str] = None
    status: str
    total_price: float
    pricing_breakdown: Dict[str, Any]
    created_at: str
    updated_at: str


class JobStatusUpdate(BaseModel):
    """Job status update request."""
    status: str = Field(..., description="New job status")
    notes: Optional[str] = Field(None, description="Update notes")
    contractor_name: Optional[str] = Field(None, description="Assigned contractor")


class JobListResponse(BaseModel):
    """Job list response model."""
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


@router.post("/", response_model=JobResponse)
async def create_job(
    job_request: JobRequest,
    background_tasks: BackgroundTasks
):
    """Create a new cleaning job."""
    try:
        # Create job record
        job_record = JobRecord(
            client_phone=job_request.client_phone,
            client_name=job_request.client_name,
            service_type=job_request.service_type,
            property_address=job_request.property_address,
            bedrooms=job_request.bedrooms,
            bathrooms=job_request.bathrooms,
            square_footage=job_request.square_footage,
            pet_friendly=job_request.pet_friendly,
            special_instructions=job_request.special_instructions,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Calculate pricing
        pricing_calc = PricingCalculation(
            service_type=job_request.service_type,
            bedrooms=job_request.bedrooms,
            bathrooms=job_request.bathrooms,
            square_footage=job_request.square_footage or 0,
            pet_friendly=job_request.pet_friendly
        )
        
        pricing_result = pricing_calc.calculate_total()
        job_record.total_price = pricing_result["total_price"]
        job_record.pricing_breakdown = pricing_result
        
        # Save to database (would use actual DB in production)
        # For now, using in-memory storage
        
        # Sync to external systems
        integration_manager = get_integration_manager()
        background_tasks.add_task(
            integration_manager.sync_job_data,
            job_record
        )
        
        return JobResponse(
            job_id=job_record.job_id,
            client_name=job_record.client_name,
            client_phone=job_record.client_phone,
            service_type=job_record.service_type,
            property_address=job_record.property_address,
            assigned_contractor=job_record.assigned_contractor,
            scheduled_date=job_record.scheduled_date.isoformat() if job_record.scheduled_date else None,
            status=job_record.status.value,
            total_price=float(job_record.total_price),
            pricing_breakdown=job_record.pricing_breakdown,
            created_at=job_record.created_at.isoformat(),
            updated_at=job_record.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Jobs per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    contractor: Optional[str] = Query(None, description="Filter by contractor")
):
    """List jobs with pagination and filtering."""
    try:
        # In production, this would query the database
        # For now, return mock data
        mock_jobs = [
            JobResponse(
                job_id="GG001",
                client_name="John Doe",
                client_phone="555-0123",
                service_type="deep_cleaning",
                property_address="123 Main St, Austin, TX",
                assigned_contractor="jennifer",
                scheduled_date="2024-01-15T10:00:00",
                status="scheduled",
                total_price=180.00,
                pricing_breakdown={
                    "base_price": 150.00,
                    "bedroom_fee": 20.00,
                    "bathroom_fee": 10.00,
                    "total_price": 180.00
                },
                created_at="2024-01-10T08:00:00",
                updated_at="2024-01-10T08:00:00"
            )
        ]
        
        # Apply filters
        filtered_jobs = mock_jobs
        if status:
            filtered_jobs = [j for j in filtered_jobs if j.status == status]
        if contractor:
            filtered_jobs = [j for j in filtered_jobs if j.assigned_contractor == contractor]
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_jobs = filtered_jobs[start_idx:end_idx]
        
        return JobListResponse(
            jobs=paginated_jobs,
            total=len(filtered_jobs),
            page=page,
            per_page=per_page,
            has_next=end_idx < len(filtered_jobs),
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get specific job details."""
    try:
        # In production, this would query the database
        # For now, return mock data
        if job_id == "GG001":
            return JobResponse(
                job_id="GG001",
                client_name="John Doe",
                client_phone="555-0123",
                service_type="deep_cleaning",
                property_address="123 Main St, Austin, TX",
                assigned_contractor="jennifer",
                scheduled_date="2024-01-15T10:00:00",
                status="scheduled",
                total_price=180.00,
                pricing_breakdown={
                    "base_price": 150.00,
                    "bedroom_fee": 20.00,
                    "bathroom_fee": 10.00,
                    "total_price": 180.00
                },
                created_at="2024-01-10T08:00:00",
                updated_at="2024-01-10T08:00:00"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Job '{job_id}' not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job: {str(e)}"
        )


@router.put("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: str,
    status_update: JobStatusUpdate,
    background_tasks: BackgroundTasks
):
    """Update job status."""
    try:
        # In production, this would update the database
        # For now, return updated mock data
        
        # Validate status
        try:
            new_status = JobStatus(status_update.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_update.status}"
            )
        
        # Update job record (mock)
        updated_job = JobResponse(
            job_id=job_id,
            client_name="John Doe",
            client_phone="555-0123",
            service_type="deep_cleaning",
            property_address="123 Main St, Austin, TX",
            assigned_contractor=status_update.contractor_name or "jennifer",
            scheduled_date="2024-01-15T10:00:00",
            status=status_update.status,
            total_price=180.00,
            pricing_breakdown={
                "base_price": 150.00,
                "bedroom_fee": 20.00,
                "bathroom_fee": 10.00,
                "total_price": 180.00
            },
            created_at="2024-01-10T08:00:00",
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Sync status update to external systems
        integration_manager = get_integration_manager()
        background_tasks.add_task(
            integration_manager.route_contractor_status,
            status_update.contractor_name or "unknown",
            status_update.status,
            job_id
        )
        
        return updated_job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update job status: {str(e)}"
        )


@router.get("/{job_id}/pricing", response_model=Dict[str, Any])
async def get_job_pricing(job_id: str):
    """Get detailed pricing breakdown for a job."""
    try:
        # In production, this would query the database
        # For now, return mock pricing data
        return {
            "job_id": job_id,
            "pricing_breakdown": {
                "base_price": 150.00,
                "bedroom_fee": 20.00,
                "bathroom_fee": 10.00,
                "pet_fee": 0.00,
                "square_footage_adjustment": 0.00,
                "total_price": 180.00
            },
            "service_details": {
                "service_type": "deep_cleaning",
                "bedrooms": 3,
                "bathrooms": 2,
                "square_footage": 1200,
                "pet_friendly": False
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job pricing: {str(e)}"
        )