"""
Analytics Endpoints
API routes for business metrics and operational analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class MetricsSummary(BaseModel):
    """Metrics summary response model."""
    total_jobs: int
    completed_jobs: int
    active_contractors: int
    total_revenue: float
    average_job_value: float
    completion_rate: float
    customer_satisfaction: float
    period_start: str
    period_end: str


class RevenueBreakdown(BaseModel):
    """Revenue breakdown response model."""
    total_revenue: float
    service_breakdown: Dict[str, float]
    contractor_breakdown: Dict[str, float]
    geographic_breakdown: Dict[str, float]
    period_start: str
    period_end: str


class PerformanceMetrics(BaseModel):
    """Performance metrics response model."""
    contractor_performance: Dict[str, Dict[str, Any]]
    service_quality: Dict[str, float]
    response_times: Dict[str, float]
    completion_rates: Dict[str, float]
    customer_feedback: Dict[str, float]


class TrendsAnalysis(BaseModel):
    """Trends analysis response model."""
    job_volume_trend: List[Dict[str, Any]]
    revenue_trend: List[Dict[str, Any]]
    service_demand_trend: List[Dict[str, Any]]
    contractor_utilization_trend: List[Dict[str, Any]]


@router.get("/summary", response_model=MetricsSummary)
async def get_metrics_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get overall business metrics summary."""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # In production, this would query the database
        # Mock data for now
        return MetricsSummary(
            total_jobs=156,
            completed_jobs=142,
            active_contractors=8,
            total_revenue=28440.00,
            average_job_value=182.31,
            completion_rate=91.03,
            customer_satisfaction=4.7,
            period_start=start_date,
            period_end=end_date
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics summary: {str(e)}"
        )


@router.get("/revenue", response_model=RevenueBreakdown)
async def get_revenue_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get detailed revenue breakdown."""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Mock revenue data
        return RevenueBreakdown(
            total_revenue=28440.00,
            service_breakdown={
                "deep_cleaning": 15280.00,
                "standard_cleaning": 8640.00,
                "move_out": 3200.00,
                "office_cleaning": 1320.00
            },
            contractor_breakdown={
                "jennifer": 12180.00,
                "mike": 7850.00,
                "sarah": 5420.00,
                "david": 2990.00
            },
            geographic_breakdown={
                "Austin": 18200.00,
                "Round Rock": 5440.00,
                "Cedar Park": 3200.00,
                "Georgetown": 1600.00
            },
            period_start=start_date,
            period_end=end_date
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get revenue breakdown: {str(e)}"
        )


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get performance metrics for contractors and services."""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Mock performance data
        return PerformanceMetrics(
            contractor_performance={
                "jennifer": {
                    "jobs_completed": 52,
                    "average_rating": 4.9,
                    "on_time_percentage": 98.1,
                    "quality_score": 4.8,
                    "strike_count": 0
                },
                "mike": {
                    "jobs_completed": 38,
                    "average_rating": 4.6,
                    "on_time_percentage": 94.7,
                    "quality_score": 4.5,
                    "strike_count": 1
                },
                "sarah": {
                    "jobs_completed": 31,
                    "average_rating": 4.8,
                    "on_time_percentage": 96.8,
                    "quality_score": 4.7,
                    "strike_count": 0
                },
                "david": {
                    "jobs_completed": 21,
                    "average_rating": 4.3,
                    "on_time_percentage": 90.5,
                    "quality_score": 4.2,
                    "strike_count": 2
                }
            },
            service_quality={
                "deep_cleaning": 4.8,
                "standard_cleaning": 4.6,
                "move_out": 4.7,
                "office_cleaning": 4.5
            },
            response_times={
                "initial_response": 8.5,
                "job_assignment": 15.2,
                "completion_confirmation": 12.8
            },
            completion_rates={
                "on_time": 95.2,
                "early": 18.7,
                "late": 4.8,
                "cancelled": 2.1
            },
            customer_feedback={
                "overall_satisfaction": 4.7,
                "would_recommend": 4.8,
                "value_for_money": 4.6,
                "communication": 4.5
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/trends", response_model=TrendsAnalysis)
async def get_trends_analysis(
    days: int = Query(30, ge=7, le=365, description="Number of days for trend analysis")
):
    """Get trend analysis for business metrics."""
    try:
        # Generate mock trend data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Mock job volume trend (weekly aggregation)
        job_volume_trend = []
        for i in range(0, days, 7):
            week_start = start_date + timedelta(days=i)
            job_volume_trend.append({
                "date": week_start.strftime("%Y-%m-%d"),
                "jobs": 25 + (i % 15),  # Mock variation
                "completed": 23 + (i % 12)
            })
        
        # Mock revenue trend
        revenue_trend = []
        for i in range(0, days, 7):
            week_start = start_date + timedelta(days=i)
            revenue_trend.append({
                "date": week_start.strftime("%Y-%m-%d"),
                "revenue": 4500 + (i * 50) + (i % 1000),  # Mock growth with variation
                "average_job_value": 180 + (i % 40)
            })
        
        # Mock service demand trend
        service_demand_trend = []
        for i in range(0, days, 7):
            week_start = start_date + timedelta(days=i)
            service_demand_trend.append({
                "date": week_start.strftime("%Y-%m-%d"),
                "deep_cleaning": 12 + (i % 8),
                "standard_cleaning": 8 + (i % 5),
                "move_out": 3 + (i % 3),
                "office_cleaning": 2 + (i % 2)
            })
        
        # Mock contractor utilization trend
        contractor_utilization_trend = []
        for i in range(0, days, 7):
            week_start = start_date + timedelta(days=i)
            contractor_utilization_trend.append({
                "date": week_start.strftime("%Y-%m-%d"),
                "average_utilization": 75 + (i % 20),
                "active_contractors": 6 + (i % 3),
                "total_hours": 320 + (i * 10)
            })
        
        return TrendsAnalysis(
            job_volume_trend=job_volume_trend,
            revenue_trend=revenue_trend,
            service_demand_trend=service_demand_trend,
            contractor_utilization_trend=contractor_utilization_trend
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trends analysis: {str(e)}"
        )


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data():
    """Get comprehensive dashboard data."""
    try:
        # Combine multiple metrics for dashboard view
        return {
            "summary": {
                "total_jobs": 156,
                "completed_jobs": 142,
                "active_contractors": 8,
                "total_revenue": 28440.00,
                "completion_rate": 91.03,
                "customer_satisfaction": 4.7
            },
            "recent_activity": [
                {
                    "type": "job_completed",
                    "description": "Jennifer completed deep cleaning at 123 Main St",
                    "timestamp": "2024-01-15T14:30:00"
                },
                {
                    "type": "new_booking",
                    "description": "New booking: Standard cleaning for Jane Doe",
                    "timestamp": "2024-01-15T13:45:00"
                },
                {
                    "type": "quality_alert",
                    "description": "Quality issue reported for job GG142",
                    "timestamp": "2024-01-15T12:20:00"
                }
            ],
            "top_performers": [
                {"name": "Jennifer", "score": 4.9, "jobs": 52},
                {"name": "Sarah", "score": 4.8, "jobs": 31},
                {"name": "Mike", "score": 4.6, "jobs": 38}
            ],
            "service_distribution": {
                "deep_cleaning": 54,
                "standard_cleaning": 48,
                "move_out": 18,
                "office_cleaning": 8
            },
            "alerts": [
                {
                    "type": "warning",
                    "message": "David has 2 strikes - monitor performance",
                    "timestamp": "2024-01-15T10:00:00"
                }
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/export", response_model=Dict[str, Any])
async def export_analytics_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Export format (json, csv)")
):
    """Export analytics data for external analysis."""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Generate export data
        export_data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "period_start": start_date,
                "period_end": end_date,
                "format": format
            },
            "summary": {
                "total_jobs": 156,
                "completed_jobs": 142,
                "total_revenue": 28440.00,
                "active_contractors": 8
            },
            "jobs": [
                {
                    "job_id": "GG001",
                    "date": "2024-01-10",
                    "service_type": "deep_cleaning",
                    "contractor": "jennifer",
                    "revenue": 180.00,
                    "rating": 5.0
                }
                # Would include all jobs in the period
            ],
            "contractors": [
                {
                    "name": "jennifer",
                    "jobs_completed": 52,
                    "total_revenue": 9360.00,
                    "average_rating": 4.9
                }
                # Would include all contractors
            ]
        }
        
        return {
            "status": "success",
            "format": format,
            "data": export_data,
            "record_count": {
                "jobs": len(export_data["jobs"]),
                "contractors": len(export_data["contractors"])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export analytics data: {str(e)}"
        )