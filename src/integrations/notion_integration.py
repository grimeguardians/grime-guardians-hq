"""
Notion Integration for Contractor Management and Performance Tracking
Comprehensive integration with Notion databases for contractor data and analytics
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json

from ..config.settings import get_settings
from ..models.schemas import ContractorProfile, JobRecord, PerformanceMetrics

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class NotionPage:
    """Notion page representation."""
    id: str
    title: str
    properties: Dict[str, Any]
    created_time: datetime
    last_edited_time: datetime


@dataclass
class NotionDatabase:
    """Notion database representation."""
    id: str
    title: str
    properties: Dict[str, Any]
    created_time: datetime
    last_edited_time: datetime


class NotionIntegration:
    """
    Comprehensive Notion integration for Grime Guardians contractor management.
    
    Capabilities:
    - Contractor profile and performance tracking
    - Job history and analytics
    - Attendance and scheduling data
    - Performance metrics and KPI tracking
    - Training progress and certification tracking
    - Real-time synchronization with operational data
    """
    
    def __init__(self):
        self.notion_token = settings.notion_token
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # Database IDs from settings
        self.contractors_db_id = settings.notion_database_contractors
        self.jobs_db_id = settings.notion_database_jobs
        self.performance_db_id = settings.notion_database_performance
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request to Notion."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Notion API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Notion request: {e}")
            raise
    
    # Database Operations
    async def get_database(self, database_id: str) -> Optional[NotionDatabase]:
        """Get database information from Notion."""
        try:
            response = await self._make_request("GET", f"databases/{database_id}")
            return self._parse_database(response)
        except Exception as e:
            logger.error(f"Error getting database {database_id}: {e}")
            return None
    
    async def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100
    ) -> List[NotionPage]:
        """Query database with filters and sorting."""
        query_data = {"page_size": page_size}
        
        if filter_conditions:
            query_data["filter"] = filter_conditions
        if sorts:
            query_data["sorts"] = sorts
        if start_cursor:
            query_data["start_cursor"] = start_cursor
        
        try:
            response = await self._make_request("POST", f"databases/{database_id}/query", data=query_data)
            results = response.get("results", [])
            return [self._parse_page(page) for page in results]
        except Exception as e:
            logger.error(f"Error querying database {database_id}: {e}")
            return []
    
    async def create_page(
        self,
        database_id: str,
        properties: Dict[str, Any],
        children: Optional[List[Dict]] = None
    ) -> Optional[NotionPage]:
        """Create new page in database."""
        page_data = {
            "parent": {"database_id": database_id},
            "properties": self._format_properties(properties)
        }
        
        if children:
            page_data["children"] = children
        
        try:
            response = await self._make_request("POST", "pages", data=page_data)
            return self._parse_page(response)
        except Exception as e:
            logger.error(f"Error creating page in database {database_id}: {e}")
            return None
    
    async def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any]
    ) -> Optional[NotionPage]:
        """Update existing page properties."""
        update_data = {
            "properties": self._format_properties(properties)
        }
        
        try:
            response = await self._make_request("PATCH", f"pages/{page_id}", data=update_data)
            return self._parse_page(response)
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}")
            return None
    
    async def get_page(self, page_id: str) -> Optional[NotionPage]:
        """Get page by ID."""
        try:
            response = await self._make_request("GET", f"pages/{page_id}")
            return self._parse_page(response)
        except Exception as e:
            logger.error(f"Error getting page {page_id}: {e}")
            return None
    
    # Contractor Management
    async def get_contractor_profile(self, contractor_id: str) -> Optional[Dict[str, Any]]:
        """Get contractor profile from Notion."""
        if not self.contractors_db_id:
            logger.warning("Contractors database ID not configured")
            return None
        
        filter_conditions = {
            "property": "Contractor ID",
            "rich_text": {
                "equals": contractor_id
            }
        }
        
        try:
            pages = await self.query_database(self.contractors_db_id, filter_conditions)
            if pages:
                return self._extract_contractor_data(pages[0])
            return None
        except Exception as e:
            logger.error(f"Error getting contractor profile {contractor_id}: {e}")
            return None
    
    async def create_contractor_profile(self, contractor_profile: ContractorProfile) -> bool:
        """Create new contractor profile in Notion."""
        if not self.contractors_db_id:
            logger.warning("Contractors database ID not configured")
            return False
        
        properties = {
            "Contractor ID": contractor_profile.contractor_id,
            "Full Name": f"{contractor_profile.first_name} {contractor_profile.last_name}",
            "First Name": contractor_profile.first_name,
            "Last Name": contractor_profile.last_name,
            "Phone": contractor_profile.contact_info.phone,
            "Email": contractor_profile.contact_info.email,
            "Territory": contractor_profile.territory,
            "Hourly Rate": contractor_profile.hourly_rate,
            "Start Date": contractor_profile.start_date.isoformat(),
            "Status": contractor_profile.status,
            "Specializations": contractor_profile.specializations,
            "Performance Score": contractor_profile.performance_score,
            "Strike Count": contractor_profile.strike_count,
            "Total Jobs": len(contractor_profile.job_history),
            "Last Active": contractor_profile.last_active.isoformat() if contractor_profile.last_active else None
        }
        
        try:
            page = await self.create_page(self.contractors_db_id, properties)
            if page:
                logger.info(f"Created contractor profile for {contractor_profile.contractor_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating contractor profile {contractor_profile.contractor_id}: {e}")
            return False
    
    async def update_contractor_profile(
        self,
        contractor_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update contractor profile in Notion."""
        if not self.contractors_db_id:
            return False
        
        # First find the contractor page
        filter_conditions = {
            "property": "Contractor ID",
            "rich_text": {
                "equals": contractor_id
            }
        }
        
        try:
            pages = await self.query_database(self.contractors_db_id, filter_conditions)
            if not pages:
                logger.warning(f"Contractor {contractor_id} not found in Notion")
                return False
            
            page = pages[0]
            result = await self.update_page(page.id, updates)
            
            if result:
                logger.info(f"Updated contractor profile for {contractor_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating contractor profile {contractor_id}: {e}")
            return False
    
    # Job Tracking
    async def create_job_record(self, job_record: JobRecord) -> bool:
        """Create job record in Notion."""
        if not self.jobs_db_id:
            logger.warning("Jobs database ID not configured")
            return False
        
        properties = {
            "Job ID": job_record.job_id,
            "Contractor": job_record.assigned_contractor,
            "Client Phone": job_record.client_phone,
            "Client Address": job_record.client_address,
            "Service Type": job_record.service_type,
            "Scheduled Date": job_record.scheduled_date.isoformat(),
            "Status": job_record.status,
            "Total Price": float(job_record.total_price) if job_record.total_price else 0,
            "Duration Hours": job_record.duration_hours,
            "Quality Score": job_record.quality_score,
            "Client Satisfaction": job_record.client_satisfaction,
            "Photos Submitted": job_record.photos_submitted,
            "Checklist Complete": job_record.checklist_complete,
            "Created Date": job_record.created_at.isoformat(),
            "Completed Date": job_record.completed_at.isoformat() if job_record.completed_at else None
        }
        
        try:
            page = await self.create_page(self.jobs_db_id, properties)
            if page:
                logger.info(f"Created job record {job_record.job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating job record {job_record.job_id}: {e}")
            return False
    
    async def update_job_record(
        self,
        job_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update job record in Notion."""
        if not self.jobs_db_id:
            return False
        
        filter_conditions = {
            "property": "Job ID",
            "rich_text": {
                "equals": job_id
            }
        }
        
        try:
            pages = await self.query_database(self.jobs_db_id, filter_conditions)
            if not pages:
                logger.warning(f"Job {job_id} not found in Notion")
                return False
            
            page = pages[0]
            result = await self.update_page(page.id, updates)
            
            if result:
                logger.info(f"Updated job record {job_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating job record {job_id}: {e}")
            return False
    
    # Performance Tracking
    async def create_performance_record(
        self,
        contractor_id: str,
        metrics: PerformanceMetrics,
        period: str = "monthly"
    ) -> bool:
        """Create performance record in Notion."""
        if not self.performance_db_id:
            logger.warning("Performance database ID not configured")
            return False
        
        properties = {
            "Contractor ID": contractor_id,
            "Period": period.title(),
            "Date": datetime.now().isoformat(),
            "Jobs Completed": metrics.jobs_completed,
            "On Time Percentage": metrics.on_time_percentage,
            "Quality Score": metrics.average_quality_score,
            "Client Satisfaction": metrics.average_client_satisfaction,
            "Checklist Compliance": metrics.checklist_compliance_rate,
            "Photo Submission Rate": metrics.photo_submission_rate,
            "Strike Count": metrics.strike_count,
            "Revenue Generated": float(metrics.revenue_generated),
            "Efficiency Score": metrics.efficiency_score,
            "Performance Level": metrics.performance_level,
            "Improvement Areas": metrics.improvement_areas,
            "Achievements": metrics.achievements
        }
        
        try:
            page = await self.create_page(self.performance_db_id, properties)
            if page:
                logger.info(f"Created performance record for {contractor_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating performance record for {contractor_id}: {e}")
            return False
    
    # Analytics and Reporting
    async def get_contractor_analytics(
        self,
        contractor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive contractor analytics."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        analytics = {
            "contractor_id": contractor_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "job_stats": {},
            "performance_metrics": {},
            "trends": {}
        }
        
        try:
            # Get job statistics
            if self.jobs_db_id:
                job_filter = {
                    "and": [
                        {
                            "property": "Contractor",
                            "select": {
                                "equals": contractor_id
                            }
                        },
                        {
                            "property": "Scheduled Date",
                            "date": {
                                "on_or_after": start_date.isoformat()
                            }
                        },
                        {
                            "property": "Scheduled Date",
                            "date": {
                                "on_or_before": end_date.isoformat()
                            }
                        }
                    ]
                }
                
                job_pages = await self.query_database(self.jobs_db_id, job_filter)
                analytics["job_stats"] = self._analyze_job_data(job_pages)
            
            # Get performance metrics
            if self.performance_db_id:
                perf_filter = {
                    "and": [
                        {
                            "property": "Contractor ID",
                            "rich_text": {
                                "equals": contractor_id
                            }
                        },
                        {
                            "property": "Date",
                            "date": {
                                "on_or_after": start_date.isoformat()
                            }
                        }
                    ]
                }
                
                perf_pages = await self.query_database(self.performance_db_id, perf_filter)
                analytics["performance_metrics"] = self._analyze_performance_data(perf_pages)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting contractor analytics for {contractor_id}: {e}")
            return analytics
    
    async def get_team_performance_summary(self) -> Dict[str, Any]:
        """Get team-wide performance summary."""
        summary = {
            "team_stats": {},
            "top_performers": [],
            "improvement_needed": [],
            "overall_metrics": {}
        }
        
        try:
            # Get all contractor profiles
            if self.contractors_db_id:
                contractor_pages = await self.query_database(self.contractors_db_id)
                
                performance_data = []
                for page in contractor_pages:
                    contractor_data = self._extract_contractor_data(page)
                    if contractor_data:
                        performance_data.append(contractor_data)
                
                summary["team_stats"] = self._analyze_team_data(performance_data)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting team performance summary: {e}")
            return summary
    
    # Helper Methods
    def _format_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Format properties for Notion API."""
        formatted = {}
        
        for key, value in properties.items():
            if isinstance(value, str):
                formatted[key] = {"rich_text": [{"text": {"content": value}}]}
            elif isinstance(value, (int, float)):
                formatted[key] = {"number": value}
            elif isinstance(value, bool):
                formatted[key] = {"checkbox": value}
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    formatted[key] = {"multi_select": [{"name": item} for item in value]}
                else:
                    formatted[key] = {"rich_text": [{"text": {"content": str(value)}}]}
            elif isinstance(value, datetime):
                formatted[key] = {"date": {"start": value.isoformat()}}
            else:
                formatted[key] = {"rich_text": [{"text": {"content": str(value)}}]}
        
        return formatted
    
    def _parse_database(self, data: Dict[str, Any]) -> NotionDatabase:
        """Parse Notion database data."""
        return NotionDatabase(
            id=data["id"],
            title=data["title"][0]["text"]["content"] if data["title"] else "",
            properties=data["properties"],
            created_time=datetime.fromisoformat(data["created_time"].replace('Z', '+00:00')),
            last_edited_time=datetime.fromisoformat(data["last_edited_time"].replace('Z', '+00:00'))
        )
    
    def _parse_page(self, data: Dict[str, Any]) -> NotionPage:
        """Parse Notion page data."""
        title = ""
        if "properties" in data:
            title_prop = next((prop for prop in data["properties"].values() if prop.get("type") == "title"), None)
            if title_prop and title_prop.get("title"):
                title = title_prop["title"][0]["text"]["content"]
        
        return NotionPage(
            id=data["id"],
            title=title,
            properties=data.get("properties", {}),
            created_time=datetime.fromisoformat(data["created_time"].replace('Z', '+00:00')),
            last_edited_time=datetime.fromisoformat(data["last_edited_time"].replace('Z', '+00:00'))
        )
    
    def _extract_contractor_data(self, page: NotionPage) -> Optional[Dict[str, Any]]:
        """Extract contractor data from Notion page."""
        try:
            props = page.properties
            
            return {
                "contractor_id": self._get_property_value(props, "Contractor ID"),
                "full_name": self._get_property_value(props, "Full Name"),
                "territory": self._get_property_value(props, "Territory"),
                "hourly_rate": self._get_property_value(props, "Hourly Rate"),
                "performance_score": self._get_property_value(props, "Performance Score"),
                "strike_count": self._get_property_value(props, "Strike Count"),
                "total_jobs": self._get_property_value(props, "Total Jobs"),
                "status": self._get_property_value(props, "Status")
            }
        except Exception as e:
            logger.error(f"Error extracting contractor data: {e}")
            return None
    
    def _get_property_value(self, properties: Dict[str, Any], prop_name: str) -> Any:
        """Extract value from Notion property."""
        prop = properties.get(prop_name, {})
        prop_type = prop.get("type")
        
        if prop_type == "rich_text" and prop.get("rich_text"):
            return prop["rich_text"][0]["text"]["content"]
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "select" and prop.get("select"):
            return prop["select"]["name"]
        elif prop_type == "multi_select":
            return [item["name"] for item in prop.get("multi_select", [])]
        elif prop_type == "date" and prop.get("date"):
            return prop["date"]["start"]
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        elif prop_type == "title" and prop.get("title"):
            return prop["title"][0]["text"]["content"]
        
        return None
    
    def _analyze_job_data(self, job_pages: List[NotionPage]) -> Dict[str, Any]:
        """Analyze job data for analytics."""
        if not job_pages:
            return {}
        
        total_jobs = len(job_pages)
        completed_jobs = 0
        total_revenue = 0
        quality_scores = []
        
        for page in job_pages:
            status = self._get_property_value(page.properties, "Status")
            if status == "completed":
                completed_jobs += 1
            
            price = self._get_property_value(page.properties, "Total Price")
            if price:
                total_revenue += price
            
            quality = self._get_property_value(page.properties, "Quality Score")
            if quality:
                quality_scores.append(quality)
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "completion_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "total_revenue": total_revenue,
            "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0
        }
    
    def _analyze_performance_data(self, perf_pages: List[NotionPage]) -> Dict[str, Any]:
        """Analyze performance data for analytics."""
        if not perf_pages:
            return {}
        
        # Get the most recent performance record
        if perf_pages:
            latest_page = max(perf_pages, key=lambda p: p.last_edited_time)
            return {
                "on_time_percentage": self._get_property_value(latest_page.properties, "On Time Percentage"),
                "quality_score": self._get_property_value(latest_page.properties, "Quality Score"),
                "client_satisfaction": self._get_property_value(latest_page.properties, "Client Satisfaction"),
                "checklist_compliance": self._get_property_value(latest_page.properties, "Checklist Compliance"),
                "photo_submission_rate": self._get_property_value(latest_page.properties, "Photo Submission Rate")
            }
        
        return {}
    
    def _analyze_team_data(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze team-wide performance data."""
        if not performance_data:
            return {}
        
        active_contractors = [c for c in performance_data if c.get("status") == "active"]
        
        return {
            "total_contractors": len(performance_data),
            "active_contractors": len(active_contractors),
            "average_performance": sum(c.get("performance_score", 0) for c in active_contractors) / len(active_contractors) if active_contractors else 0,
            "total_strikes": sum(c.get("strike_count", 0) for c in active_contractors)
        }


# Singleton instance
_notion_integration = None

def get_notion_integration() -> NotionIntegration:
    """Get singleton Notion integration instance."""
    global _notion_integration
    if _notion_integration is None:
        _notion_integration = NotionIntegration()
    return _notion_integration