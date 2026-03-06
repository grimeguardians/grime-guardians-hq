"""
Contractor Management Endpoints
API routes for managing contractors and performance tracking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...models.contractors import ContractorProfile, ContractorStatus
from ...integrations import get_integration_manager

router = APIRouter()


class ContractorRequest(BaseModel):
    """Contractor creation/update request model."""
    name: str = Field(..., description="Contractor name")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    service_areas: List[str] = Field(..., description="Service areas")
    specializations: List[str] = Field(default_factory=list, description="Service specializations")
    hourly_rate: float = Field(..., ge=0, description="Hourly rate")
    availability: Dict[str, List[str]] = Field(default_factory=dict, description="Availability schedule")


class ContractorResponse(BaseModel):
    """Contractor response model."""
    contractor_id: str
    name: str
    phone: str
    email: str
    status: str
    service_areas: List[str]
    specializations: List[str]
    hourly_rate: float
    availability: Dict[str, List[str]]
    performance_score: float
    total_jobs: int
    completed_jobs: int
    rating: float
    strike_count: int
    created_at: str
    updated_at: str


class ContractorListResponse(BaseModel):
    """Contractor list response model."""
    contractors: List[ContractorResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ContractorStatusUpdate(BaseModel):
    """Contractor status update request."""
    status: str = Field(..., description="New contractor status")
    notes: Optional[str] = Field(None, description="Update notes")


class QualityViolationRequest(BaseModel):
    """Quality violation report request."""
    job_id: str = Field(..., description="Job ID where violation occurred")
    violation_type: str = Field(..., description="Type of violation")
    description: str = Field(..., description="Violation description")
    severity: str = Field(..., description="Violation severity (low, medium, high)")
    photos: Optional[List[str]] = Field(default_factory=list, description="Photo URLs")


@router.post("/", response_model=ContractorResponse)
async def create_contractor(
    contractor_request: ContractorRequest,
    background_tasks: BackgroundTasks
):
    """Create a new contractor profile."""
    try:
        # Create contractor profile
        contractor = ContractorProfile(
            name=contractor_request.name,
            phone=contractor_request.phone,
            email=contractor_request.email,
            service_areas=contractor_request.service_areas,
            specializations=contractor_request.specializations,
            hourly_rate=contractor_request.hourly_rate,
            availability=contractor_request.availability,
            status=ContractorStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database (would use actual DB in production)
        # For now, using in-memory storage
        
        # Sync to external systems
        integration_manager = get_integration_manager()
        background_tasks.add_task(
            integration_manager.sync_contractor_data,
            contractor
        )
        
        return ContractorResponse(
            contractor_id=contractor.contractor_id,
            name=contractor.name,
            phone=contractor.phone,
            email=contractor.email,
            status=contractor.status.value,
            service_areas=contractor.service_areas,
            specializations=contractor.specializations,
            hourly_rate=contractor.hourly_rate,
            availability=contractor.availability,
            performance_score=contractor.performance_score,
            total_jobs=contractor.total_jobs,
            completed_jobs=contractor.completed_jobs,
            rating=contractor.rating,
            strike_count=contractor.strike_count,
            created_at=contractor.created_at.isoformat(),
            updated_at=contractor.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create contractor: {str(e)}"
        )


@router.get("/", response_model=ContractorListResponse)
async def list_contractors(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Contractors per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    service_area: Optional[str] = Query(None, description="Filter by service area")
):
    """List contractors with pagination and filtering."""
    try:
        # In production, this would query the database
        # Mock data for now
        mock_contractors = [
            ContractorResponse(
                contractor_id="CONT001",
                name="Jennifer Martinez",
                phone="555-0101",
                email="jennifer@example.com",
                status="active",
                service_areas=["Austin", "Round Rock"],
                specializations=["deep_cleaning", "move_out"],
                hourly_rate=25.0,
                availability={
                    "monday": ["09:00", "17:00"],
                    "tuesday": ["09:00", "17:00"],
                    "wednesday": ["09:00", "17:00"],
                    "thursday": ["09:00", "17:00"],
                    "friday": ["09:00", "15:00"]
                },
                performance_score=4.8,
                total_jobs=125,
                completed_jobs=120,
                rating=4.9,
                strike_count=0,
                created_at="2023-01-15T08:00:00",
                updated_at="2024-01-10T08:00:00"
            ),
            ContractorResponse(
                contractor_id="CONT002",
                name="Mike Johnson",
                phone="555-0102",
                email="mike@example.com",
                status="active",
                service_areas=["Cedar Park", "Georgetown"],
                specializations=["standard_cleaning", "office_cleaning"],
                hourly_rate=22.0,
                availability={
                    "monday": ["08:00", "16:00"],
                    "tuesday": ["08:00", "16:00"],
                    "wednesday": ["08:00", "16:00"],
                    "thursday": ["08:00", "16:00"],
                    "friday": ["08:00", "14:00"]
                },
                performance_score=4.6,
                total_jobs=98,
                completed_jobs=95,
                rating=4.7,
                strike_count=1,
                created_at="2023-02-20T08:00:00",
                updated_at="2024-01-09T08:00:00"
            )
        ]
        
        # Apply filters
        filtered_contractors = mock_contractors
        if status:
            filtered_contractors = [c for c in filtered_contractors if c.status == status]
        if service_area:
            filtered_contractors = [c for c in filtered_contractors if service_area in c.service_areas]
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_contractors = filtered_contractors[start_idx:end_idx]
        
        return ContractorListResponse(
            contractors=paginated_contractors,
            total=len(filtered_contractors),
            page=page,
            per_page=per_page,
            has_next=end_idx < len(filtered_contractors),
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list contractors: {str(e)}"
        )


@router.get("/{contractor_id}", response_model=ContractorResponse)
async def get_contractor(contractor_id: str):
    """Get specific contractor details."""
    try:
        # In production, this would query the database
        if contractor_id == "CONT001":
            return ContractorResponse(
                contractor_id="CONT001",
                name="Jennifer Martinez",
                phone="555-0101",
                email="jennifer@example.com",
                status="active",
                service_areas=["Austin", "Round Rock"],
                specializations=["deep_cleaning", "move_out"],
                hourly_rate=25.0,
                availability={
                    "monday": ["09:00", "17:00"],
                    "tuesday": ["09:00", "17:00"],
                    "wednesday": ["09:00", "17:00"],
                    "thursday": ["09:00", "17:00"],
                    "friday": ["09:00", "15:00"]
                },
                performance_score=4.8,
                total_jobs=125,
                completed_jobs=120,
                rating=4.9,
                strike_count=0,
                created_at="2023-01-15T08:00:00",
                updated_at="2024-01-10T08:00:00"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Contractor '{contractor_id}' not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contractor: {str(e)}"
        )


@router.put("/{contractor_id}/status", response_model=ContractorResponse)
async def update_contractor_status(
    contractor_id: str,
    status_update: ContractorStatusUpdate,
    background_tasks: BackgroundTasks
):
    """Update contractor status."""
    try:
        # Validate status
        try:
            new_status = ContractorStatus(status_update.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_update.status}"
            )
        
        # Update contractor (mock)
        updated_contractor = ContractorResponse(
            contractor_id=contractor_id,
            name="Jennifer Martinez",
            phone="555-0101",
            email="jennifer@example.com",
            status=status_update.status,
            service_areas=["Austin", "Round Rock"],
            specializations=["deep_cleaning", "move_out"],
            hourly_rate=25.0,
            availability={
                "monday": ["09:00", "17:00"],
                "tuesday": ["09:00", "17:00"],
                "wednesday": ["09:00", "17:00"],
                "thursday": ["09:00", "17:00"],
                "friday": ["09:00", "15:00"]
            },
            performance_score=4.8,
            total_jobs=125,
            completed_jobs=120,
            rating=4.9,
            strike_count=0,
            created_at="2023-01-15T08:00:00",
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Sync status update to external systems
        integration_manager = get_integration_manager()
        background_tasks.add_task(
            integration_manager.route_contractor_status,
            contractor_id,
            status_update.status
        )
        
        return updated_contractor
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update contractor status: {str(e)}"
        )


@router.post("/{contractor_id}/violations", response_model=Dict[str, Any])
async def report_quality_violation(
    contractor_id: str,
    violation_request: QualityViolationRequest,
    background_tasks: BackgroundTasks
):
    """Report a quality violation for a contractor."""
    try:
        # Create violation record
        violation_data = {
            "contractor_id": contractor_id,
            "job_id": violation_request.job_id,
            "violation_type": violation_request.violation_type,
            "description": violation_request.description,
            "severity": violation_request.severity,
            "photos": violation_request.photos,
            "reported_at": datetime.utcnow().isoformat()
        }
        
        # Calculate new strike count (mock logic)
        current_strikes = 0  # Would get from database
        new_strikes = current_strikes + (2 if violation_request.severity == "high" else 1)
        
        # Route violation to appropriate systems
        integration_manager = get_integration_manager()
        background_tasks.add_task(
            integration_manager.route_quality_violation,
            violation_data,
            new_strikes
        )
        
        return {
            "violation_id": f"VIO_{contractor_id}_{int(datetime.utcnow().timestamp())}",
            "contractor_id": contractor_id,
            "strike_count": new_strikes,
            "status": "reported",
            "escalated": new_strikes >= 3,
            "reported_at": violation_data["reported_at"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to report violation: {str(e)}"
        )


@router.get("/{contractor_id}/performance", response_model=Dict[str, Any])
async def get_contractor_performance(contractor_id: str):
    """Get detailed performance metrics for a contractor."""
    try:
        # In production, this would query the database
        return {
            "contractor_id": contractor_id,
            "performance_score": 4.8,
            "total_jobs": 125,
            "completed_jobs": 120,
            "cancelled_jobs": 3,
            "no_show_jobs": 2,
            "rating": 4.9,
            "strike_count": 0,
            "violations": [],
            "metrics": {
                "on_time_percentage": 98.5,
                "quality_score": 4.8,
                "customer_satisfaction": 4.9,
                "response_time_minutes": 12.5
            },
            "recent_performance": {
                "last_30_days": {
                    "jobs_completed": 18,
                    "average_rating": 4.9,
                    "violations": 0
                },
                "last_90_days": {
                    "jobs_completed": 52,
                    "average_rating": 4.8,
                    "violations": 0
                }
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contractor performance: {str(e)}"
        )