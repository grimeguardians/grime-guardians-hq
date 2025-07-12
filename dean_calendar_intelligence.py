#!/usr/bin/env python3
"""
Dean's Commercial Calendar Intelligence
Special focus on Commercial Cleaning Walkthrough calendar (qXm41YUW2Cxc0stYERn8)
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class DeanCommercialIntelligence:
    """
    Dean's specialized intelligence for commercial calendar management.
    Focus: Make Commercial Cleaning Walkthrough calendar very busy!
    """
    
    def __init__(self):
        from src.integrations.gohighlevel_service import ghl_service
        from src.config.settings import GOHIGHLEVEL_CALENDARS
        
        self.ghl_service = ghl_service
        self.commercial_calendar = GOHIGHLEVEL_CALENDARS["commercial_walkthrough"]
        self.target_calendar_id = self.commercial_calendar["id"]
    
    async def get_commercial_pipeline_status(self) -> Dict[str, Any]:
        """Get Dean's commercial pipeline status and recommendations."""
        try:
            # Get commercial appointments for next 30 days
            now = datetime.now()
            end_date = now + timedelta(days=30)
            
            # Get appointments from commercial calendar specifically
            appointments = await self.ghl_service.get_appointments(now, end_date)
            
            # Filter for commercial calendar only
            commercial_appointments = [
                apt for apt in appointments 
                if getattr(apt, '_calendar_type', '') == 'commercial_lead_generation'
            ]
            
            # Analyze pipeline
            pipeline_analysis = {
                "commercial_appointments_30_days": len(commercial_appointments),
                "appointments_this_week": len([
                    apt for apt in commercial_appointments 
                    if apt.start_time <= now + timedelta(days=7)
                ]),
                "pipeline_health": self._assess_pipeline_health(commercial_appointments),
                "recommendations": self._generate_recommendations(commercial_appointments),
                "calendar_id": self.target_calendar_id,
                "calendar_name": self.commercial_calendar["name"]
            }
            
            return pipeline_analysis
            
        except Exception as e:
            logger.error(f"Error getting commercial pipeline status: {e}")
            return {
                "commercial_appointments_30_days": 0,
                "appointments_this_week": 0,
                "pipeline_health": "unknown",
                "recommendations": ["Check GoHighLevel API connectivity"],
                "calendar_id": self.target_calendar_id,
                "calendar_name": self.commercial_calendar["name"]
            }
    
    def _assess_pipeline_health(self, appointments: List) -> str:
        """Assess health of commercial pipeline."""
        weekly_appointments = len([
            apt for apt in appointments 
            if apt.start_time <= datetime.now() + timedelta(days=7)
        ])
        
        if weekly_appointments >= 5:
            return "excellent"
        elif weekly_appointments >= 3:
            return "good"
        elif weekly_appointments >= 1:
            return "moderate"
        else:
            return "needs_attention"
    
    def _generate_recommendations(self, appointments: List) -> List[str]:
        """Generate Dean's action recommendations."""
        recommendations = []
        
        weekly_count = len([
            apt for apt in appointments 
            if apt.start_time <= datetime.now() + timedelta(days=7)
        ])
        
        if weekly_count == 0:
            recommendations.extend([
                "🎯 URGENT: Schedule commercial walkthroughs ASAP",
                "📞 Activate cold calling campaign for commercial prospects", 
                "📧 Launch email sequence to commercial leads",
                "🔗 Post commercial cleaning content on LinkedIn"
            ])
        elif weekly_count < 3:
            recommendations.extend([
                "📈 Increase commercial outreach - aim for 5+ walkthroughs/week",
                "🎯 Target property managers and facility managers",
                "📱 Follow up on previous commercial quotes"
            ])
        elif weekly_count < 5:
            recommendations.extend([
                "✅ Good progress! Push for 5+ commercial walkthroughs/week",
                "💼 Focus on larger accounts and recurring contracts"
            ])
        else:
            recommendations.extend([
                "🚀 Excellent pipeline! Maintain momentum",
                "💰 Focus on closing deals and upselling services"
            ])
        
        return recommendations
    
    async def generate_commercial_report(self) -> str:
        """Generate Dean's commercial calendar intelligence report."""
        pipeline_status = await self.get_commercial_pipeline_status()
        
        health = pipeline_status["pipeline_health"]
        health_emoji = {
            "excellent": "🚀",
            "good": "✅", 
            "moderate": "⚠️",
            "needs_attention": "🔴"
        }.get(health, "❓")
        
        report = f"💼 **DEAN'S COMMERCIAL PIPELINE INTELLIGENCE**\n\n"
        report += f"📅 **Calendar: {pipeline_status['calendar_name']}**\n"
        report += f"🎯 **Pipeline Health: {health_emoji} {health.upper()}**\n\n"
        
        report += f"📊 **METRICS:**\n"
        report += f"• This Week: {pipeline_status['appointments_this_week']} commercial walkthroughs\n"
        report += f"• Next 30 Days: {pipeline_status['commercial_appointments_30_days']} total appointments\n\n"
        
        if pipeline_status["recommendations"]:
            report += f"🎯 **ACTION ITEMS FOR DEAN:**\n"
            for i, rec in enumerate(pipeline_status["recommendations"], 1):
                report += f"{i}. {rec}\n"
        
        report += f"\n💡 **Goal: Make this calendar VERY BUSY with commercial prospects!**"
        
        return report


# Global instance for Dean
dean_commercial_intelligence = DeanCommercialIntelligence()