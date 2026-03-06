"""
Grime Guardians Integration Layer
Comprehensive external system integrations for the COO operations team
"""

from .gohighlevel_integration import GoHighLevelIntegration, get_gohighlevel_integration
from .discord_integration import DiscordIntegration, GrimeGuardiansBot, get_discord_integration
from .notion_integration import NotionIntegration, get_notion_integration
from .google_integration import GoogleServicesIntegration, get_google_integration

__all__ = [
    # Integration classes
    "GoHighLevelIntegration",
    "DiscordIntegration", 
    "GrimeGuardiansBot",
    "NotionIntegration",
    "GoogleServicesIntegration",
    
    # Singleton getters
    "get_gohighlevel_integration",
    "get_discord_integration",
    "get_notion_integration",
    "get_google_integration",
    
    # Manager
    "IntegrationManager"
]

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class IntegrationManager:
    """
    Centralized integration manager for coordinating all external systems.
    
    Features:
    - Unified interface for all integrations
    - Health monitoring and status checking
    - Automatic failover and retry logic
    - Data synchronization coordination
    - Event routing between systems
    """
    
    def __init__(self):
        self.ghl = None
        self.discord = None
        self.notion = None
        self.google = None
        
        self.health_status = {
            "gohighlevel": False,
            "discord": False,
            "notion": False,
            "google": False
        }
        
        self.last_health_check = None
        
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all integrations."""
        logger.info("Initializing all integrations...")
        
        results = {}
        
        # Initialize GoHighLevel
        try:
            self.ghl = get_gohighlevel_integration()
            results["gohighlevel"] = True
            self.health_status["gohighlevel"] = True
            logger.info("✅ GoHighLevel integration initialized")
        except Exception as e:
            logger.error(f"❌ GoHighLevel initialization failed: {e}")
            results["gohighlevel"] = False
        
        # Initialize Discord
        try:
            self.discord = get_discord_integration()
            results["discord"] = True
            self.health_status["discord"] = True
            logger.info("✅ Discord integration initialized")
        except Exception as e:
            logger.error(f"❌ Discord initialization failed: {e}")
            results["discord"] = False
        
        # Initialize Notion
        try:
            self.notion = get_notion_integration()
            results["notion"] = True
            self.health_status["notion"] = True
            logger.info("✅ Notion integration initialized")
        except Exception as e:
            logger.error(f"❌ Notion initialization failed: {e}")
            results["notion"] = False
        
        # Initialize Google Services
        try:
            self.google = get_google_integration()
            results["google"] = True
            self.health_status["google"] = True
            logger.info("✅ Google Services integration initialized")
        except Exception as e:
            logger.error(f"❌ Google Services initialization failed: {e}")
            results["google"] = False
        
        self.last_health_check = datetime.now()
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logger.info(f"Integration initialization complete: {success_count}/{total_count} systems online")
        
        return results
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health status of all integrations."""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "issues": []
        }
        
        # Check GoHighLevel
        try:
            if self.ghl:
                async with self.ghl as ghl:
                    # Try a simple API call to test connectivity
                    await ghl._make_request("GET", "locations/search", params={"limit": 1})
                health_report["services"]["gohighlevel"] = {"status": "healthy", "last_check": datetime.now().isoformat()}
                self.health_status["gohighlevel"] = True
        except Exception as e:
            health_report["services"]["gohighlevel"] = {"status": "unhealthy", "error": str(e)}
            health_report["issues"].append(f"GoHighLevel: {str(e)}")
            self.health_status["gohighlevel"] = False
        
        # Check Discord
        try:
            if self.discord and self.discord.bot and self.discord.is_running:
                health_report["services"]["discord"] = {"status": "healthy", "bot_ready": True}
                self.health_status["discord"] = True
            else:
                health_report["services"]["discord"] = {"status": "unhealthy", "bot_ready": False}
                health_report["issues"].append("Discord: Bot not running")
                self.health_status["discord"] = False
        except Exception as e:
            health_report["services"]["discord"] = {"status": "unhealthy", "error": str(e)}
            health_report["issues"].append(f"Discord: {str(e)}")
            self.health_status["discord"] = False
        
        # Check Notion
        try:
            if self.notion:
                async with self.notion as notion:
                    # Try to get database info
                    if notion.contractors_db_id:
                        await notion.get_database(notion.contractors_db_id)
                health_report["services"]["notion"] = {"status": "healthy", "last_check": datetime.now().isoformat()}
                self.health_status["notion"] = True
        except Exception as e:
            health_report["services"]["notion"] = {"status": "unhealthy", "error": str(e)}
            health_report["issues"].append(f"Notion: {str(e)}")
            self.health_status["notion"] = False
        
        # Check Google Services
        try:
            if self.google:
                async with self.google as google:
                    # Try to get calendar list
                    await google.get_calendar_list()
                health_report["services"]["google"] = {"status": "healthy", "last_check": datetime.now().isoformat()}
                self.health_status["google"] = True
        except Exception as e:
            health_report["services"]["google"] = {"status": "unhealthy", "error": str(e)}
            health_report["issues"].append(f"Google Services: {str(e)}")
            self.health_status["google"] = False
        
        # Determine overall status
        healthy_services = sum(1 for status in self.health_status.values() if status)
        total_services = len(self.health_status)
        
        if healthy_services == total_services:
            health_report["overall_status"] = "healthy"
        elif healthy_services >= total_services * 0.75:
            health_report["overall_status"] = "degraded"
        else:
            health_report["overall_status"] = "critical"
        
        health_report["healthy_services"] = healthy_services
        health_report["total_services"] = total_services
        health_report["health_percentage"] = (healthy_services / total_services) * 100
        
        self.last_health_check = datetime.now()
        
        return health_report
    
    # Unified data synchronization methods
    async def sync_client_data(self, client_profile) -> Dict[str, bool]:
        """Synchronize client data across all platforms."""
        results = {}
        
        # Sync to GoHighLevel
        if self.ghl and self.health_status["gohighlevel"]:
            try:
                async with self.ghl as ghl:
                    success = await ghl.sync_client_profile(client_profile)
                    results["gohighlevel"] = success
            except Exception as e:
                logger.error(f"Failed to sync client to GoHighLevel: {e}")
                results["gohighlevel"] = False
        
        return results
    
    async def sync_job_data(self, job_record) -> Dict[str, bool]:
        """Synchronize job data across all platforms."""
        results = {}
        
        # Create opportunity in GoHighLevel
        if self.ghl and self.health_status["gohighlevel"]:
            try:
                async with self.ghl as ghl:
                    opportunity_id = await ghl.create_job_opportunity(job_record)
                    results["gohighlevel"] = opportunity_id is not None
            except Exception as e:
                logger.error(f"Failed to create job opportunity in GoHighLevel: {e}")
                results["gohighlevel"] = False
        
        # Create job record in Notion
        if self.notion and self.health_status["notion"]:
            try:
                async with self.notion as notion:
                    success = await notion.create_job_record(job_record)
                    results["notion"] = success
            except Exception as e:
                logger.error(f"Failed to create job record in Notion: {e}")
                results["notion"] = False
        
        # Create calendar event in Google Calendar
        if self.google and self.health_status["google"]:
            try:
                async with self.google as google:
                    event_id = await google.create_job_calendar_event(job_record)
                    results["google"] = event_id is not None
            except Exception as e:
                logger.error(f"Failed to create calendar event: {e}")
                results["google"] = False
        
        # Send job assignment to Discord
        if self.discord and self.health_status["discord"]:
            try:
                success = await self.discord.send_job_assignment(job_record)
                results["discord"] = success
            except Exception as e:
                logger.error(f"Failed to send Discord job assignment: {e}")
                results["discord"] = False
        
        return results
    
    async def sync_contractor_data(self, contractor_profile) -> Dict[str, bool]:
        """Synchronize contractor data across platforms."""
        results = {}
        
        # Sync to Notion
        if self.notion and self.health_status["notion"]:
            try:
                async with self.notion as notion:
                    success = await notion.create_contractor_profile(contractor_profile)
                    results["notion"] = success
            except Exception as e:
                logger.error(f"Failed to sync contractor to Notion: {e}")
                results["notion"] = False
        
        return results
    
    # Event routing methods
    async def route_quality_violation(self, violation_data, strike_count: int) -> Dict[str, bool]:
        """Route quality violation to appropriate systems."""
        results = {}
        
        # Send Discord alert
        if self.discord and self.health_status["discord"]:
            try:
                success = await self.discord.send_quality_alert(violation_data, strike_count)
                results["discord"] = success
            except Exception as e:
                logger.error(f"Failed to send Discord quality alert: {e}")
                results["discord"] = False
        
        return results
    
    async def route_contractor_status(self, contractor_name: str, status: str, job_id: Optional[str] = None) -> Dict[str, bool]:
        """Route contractor status updates to appropriate systems."""
        results = {}
        
        # Send Discord update
        if self.discord and self.health_status["discord"]:
            try:
                success = await self.discord.send_contractor_status(contractor_name, status, job_id)
                results["discord"] = success
            except Exception as e:
                logger.error(f"Failed to send Discord status update: {e}")
                results["discord"] = False
        
        return results
    
    async def route_emergency_alert(self, alert_type: str, description: str, affected_parties: List[str] = None) -> Dict[str, bool]:
        """Route emergency alerts to all appropriate channels."""
        results = {}
        
        # Send Discord emergency alert
        if self.discord and self.health_status["discord"]:
            try:
                success = await self.discord.send_emergency(alert_type, description, affected_parties)
                results["discord"] = success
            except Exception as e:
                logger.error(f"Failed to send Discord emergency alert: {e}")
                results["discord"] = False
        
        # Could also send email alerts, SMS alerts, etc.
        
        return results
    
    # Webhook handling
    async def handle_gohighlevel_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming GoHighLevel webhook."""
        if self.ghl:
            async with self.ghl as ghl:
                return await ghl.handle_webhook(webhook_data)
        return {"status": "no_handler", "reason": "GoHighLevel integration not available"}
    
    async def shutdown_all(self):
        """Gracefully shutdown all integrations."""
        logger.info("Shutting down all integrations...")
        
        if self.discord and self.discord.is_running:
            await self.discord.stop_bot()
            logger.info("Discord bot stopped")
        
        # Other integrations use context managers and will clean up automatically
        
        logger.info("All integrations shut down")


# Singleton instance
_integration_manager = None

def get_integration_manager() -> IntegrationManager:
    """Get singleton integration manager instance."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager