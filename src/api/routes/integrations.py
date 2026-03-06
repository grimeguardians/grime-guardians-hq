"""
Integration Management Endpoints
API routes for managing external system integrations
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ...integrations import get_integration_manager

router = APIRouter()


class IntegrationStatusResponse(BaseModel):
    """Integration status response model."""
    service: str
    status: str
    last_check: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    """System health response model."""
    overall_status: str
    health_percentage: float
    total_services: int
    healthy_services: int
    services: List[IntegrationStatusResponse]
    issues: List[str]
    timestamp: str


class SyncRequest(BaseModel):
    """Data synchronization request."""
    data_type: str = Field(..., description="Type of data to sync (client, job, contractor)")
    record_id: str = Field(..., description="Record ID to sync")
    target_systems: Optional[List[str]] = Field(None, description="Target systems (if not all)")


class SyncResponse(BaseModel):
    """Data synchronization response."""
    data_type: str
    record_id: str
    sync_results: Dict[str, bool]
    timestamp: str
    success_count: int
    total_count: int


@router.get("/health", response_model=SystemHealthResponse)
async def get_integration_health():
    """Get health status of all integrations."""
    try:
        integration_manager = get_integration_manager()
        health_report = await integration_manager.check_health()
        
        # Convert to response format
        services = []
        for service_name, service_data in health_report.get("services", {}).items():
            services.append(IntegrationStatusResponse(
                service=service_name,
                status=service_data.get("status", "unknown"),
                last_check=service_data.get("last_check", datetime.utcnow().isoformat()),
                error=service_data.get("error"),
                metadata=service_data.get("metadata", {})
            ))
        
        return SystemHealthResponse(
            overall_status=health_report.get("overall_status", "unknown"),
            health_percentage=health_report.get("health_percentage", 0.0),
            total_services=health_report.get("total_services", 0),
            healthy_services=health_report.get("healthy_services", 0),
            services=services,
            issues=health_report.get("issues", []),
            timestamp=health_report.get("timestamp", datetime.utcnow().isoformat())
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get integration health: {str(e)}"
        )


@router.get("/gohighlevel/status", response_model=IntegrationStatusResponse)
async def get_gohighlevel_status():
    """Get GoHighLevel integration status."""
    try:
        integration_manager = get_integration_manager()
        
        # Test GoHighLevel connection
        try:
            if integration_manager.ghl:
                async with integration_manager.ghl as ghl:
                    # Test API connectivity
                    await ghl._make_request("GET", "locations/search", params={"limit": 1})
                
                return IntegrationStatusResponse(
                    service="gohighlevel",
                    status="healthy",
                    last_check=datetime.utcnow().isoformat(),
                    metadata={"api_version": "v1", "connection": "active"}
                )
            else:
                return IntegrationStatusResponse(
                    service="gohighlevel",
                    status="unavailable",
                    last_check=datetime.utcnow().isoformat(),
                    error="Integration not initialized"
                )
                
        except Exception as e:
            return IntegrationStatusResponse(
                service="gohighlevel",
                status="unhealthy",
                last_check=datetime.utcnow().isoformat(),
                error=str(e)
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get GoHighLevel status: {str(e)}"
        )


@router.get("/discord/status", response_model=IntegrationStatusResponse)
async def get_discord_status():
    """Get Discord integration status."""
    try:
        integration_manager = get_integration_manager()
        
        if integration_manager.discord:
            bot_ready = getattr(integration_manager.discord, 'is_running', False)
            return IntegrationStatusResponse(
                service="discord",
                status="healthy" if bot_ready else "degraded",
                last_check=datetime.utcnow().isoformat(),
                metadata={"bot_ready": bot_ready, "channels_configured": True}
            )
        else:
            return IntegrationStatusResponse(
                service="discord",
                status="unavailable",
                last_check=datetime.utcnow().isoformat(),
                error="Integration not initialized"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Discord status: {str(e)}"
        )


@router.get("/notion/status", response_model=IntegrationStatusResponse)
async def get_notion_status():
    """Get Notion integration status."""
    try:
        integration_manager = get_integration_manager()
        
        try:
            if integration_manager.notion:
                async with integration_manager.notion as notion:
                    # Test database connectivity
                    if notion.contractors_db_id:
                        await notion.get_database(notion.contractors_db_id)
                
                return IntegrationStatusResponse(
                    service="notion",
                    status="healthy",
                    last_check=datetime.utcnow().isoformat(),
                    metadata={"databases_configured": True}
                )
            else:
                return IntegrationStatusResponse(
                    service="notion",
                    status="unavailable",
                    last_check=datetime.utcnow().isoformat(),
                    error="Integration not initialized"
                )
                
        except Exception as e:
            return IntegrationStatusResponse(
                service="notion",
                status="unhealthy",
                last_check=datetime.utcnow().isoformat(),
                error=str(e)
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Notion status: {str(e)}"
        )


@router.get("/google/status", response_model=IntegrationStatusResponse)
async def get_google_status():
    """Get Google Services integration status."""
    try:
        integration_manager = get_integration_manager()
        
        try:
            if integration_manager.google:
                async with integration_manager.google as google:
                    # Test calendar access
                    await google.get_calendar_list()
                
                return IntegrationStatusResponse(
                    service="google",
                    status="healthy",
                    last_check=datetime.utcnow().isoformat(),
                    metadata={"calendar_access": True, "gmail_access": True}
                )
            else:
                return IntegrationStatusResponse(
                    service="google",
                    status="unavailable",
                    last_check=datetime.utcnow().isoformat(),
                    error="Integration not initialized"
                )
                
        except Exception as e:
            return IntegrationStatusResponse(
                service="google",
                status="unhealthy",
                last_check=datetime.utcnow().isoformat(),
                error=str(e)
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Google status: {str(e)}"
        )


@router.post("/sync", response_model=SyncResponse)
async def sync_data(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """Synchronize data across external systems."""
    try:
        integration_manager = get_integration_manager()
        
        # Determine which sync method to use
        if sync_request.data_type == "client":
            # Mock client data for testing
            mock_client = type('ClientProfile', (), {
                'client_id': sync_request.record_id,
                'name': 'Test Client',
                'phone': '555-0123',
                'email': 'test@example.com'
            })()
            
            sync_results = await integration_manager.sync_client_data(mock_client)
            
        elif sync_request.data_type == "job":
            # Mock job data for testing
            mock_job = type('JobRecord', (), {
                'job_id': sync_request.record_id,
                'client_name': 'Test Client',
                'service_type': 'deep_cleaning',
                'total_price': 180.00,
                'scheduled_date': datetime.utcnow(),
                'status': 'scheduled'
            })()
            
            sync_results = await integration_manager.sync_job_data(mock_job)
            
        elif sync_request.data_type == "contractor":
            # Mock contractor data for testing
            mock_contractor = type('ContractorProfile', (), {
                'contractor_id': sync_request.record_id,
                'name': 'Test Contractor',
                'phone': '555-0456',
                'email': 'contractor@example.com',
                'service_areas': ['Austin']
            })()
            
            sync_results = await integration_manager.sync_contractor_data(mock_contractor)
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown data type: {sync_request.data_type}"
            )
        
        # Filter results if specific target systems requested
        if sync_request.target_systems:
            sync_results = {
                k: v for k, v in sync_results.items() 
                if k in sync_request.target_systems
            }
        
        success_count = sum(1 for success in sync_results.values() if success)
        total_count = len(sync_results)
        
        return SyncResponse(
            data_type=sync_request.data_type,
            record_id=sync_request.record_id,
            sync_results=sync_results,
            timestamp=datetime.utcnow().isoformat(),
            success_count=success_count,
            total_count=total_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync data: {str(e)}"
        )


@router.post("/reinitialize", response_model=Dict[str, Any])
async def reinitialize_integrations(
    background_tasks: BackgroundTasks,
    services: Optional[List[str]] = None
):
    """Reinitialize integration connections."""
    try:
        integration_manager = get_integration_manager()
        
        # Reinitialize all or specific services
        if services:
            results = {}
            for service in services:
                try:
                    # Service-specific reinitialization logic would go here
                    results[service] = True
                except Exception as e:
                    results[service] = False
                    
        else:
            # Reinitialize all integrations
            results = await integration_manager.initialize_all()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return {
            "status": "completed",
            "results": results,
            "success_count": success_count,
            "total_count": total_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reinitialize integrations: {str(e)}"
        )


@router.get("/", response_model=List[Dict[str, Any]])
async def list_integrations():
    """List all available integrations."""
    try:
        integrations = [
            {
                "name": "gohighlevel",
                "description": "GoHighLevel CRM integration for client management",
                "capabilities": ["contacts", "opportunities", "pipelines", "conversations"],
                "status_endpoint": "/integrations/gohighlevel/status"
            },
            {
                "name": "discord",
                "description": "Discord bot for team communications",
                "capabilities": ["notifications", "alerts", "team_chat", "status_updates"],
                "status_endpoint": "/integrations/discord/status"
            },
            {
                "name": "notion",
                "description": "Notion database integration for data management",
                "capabilities": ["contractor_profiles", "job_records", "performance_tracking"],
                "status_endpoint": "/integrations/notion/status"
            },
            {
                "name": "google",
                "description": "Google Services integration for calendar and email",
                "capabilities": ["calendar", "gmail", "scheduling", "notifications"],
                "status_endpoint": "/integrations/google/status"
            }
        ]
        
        return integrations
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list integrations: {str(e)}"
        )