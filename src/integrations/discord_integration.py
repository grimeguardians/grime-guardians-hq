"""
Discord Integration for Enhanced Team Communication
Advanced Discord bot integration for real-time operations coordination
"""

import asyncio
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json

from ..config.settings import get_settings
from ..models.schemas import JobSchema as JobRecord, QualityViolationSchema as QualityViolation
from ..models.types import ContractorStatus

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DiscordChannelConfig:
    """Discord channel configuration."""
    name: str
    channel_id: Optional[int]
    purpose: str
    auto_create: bool = True


class GrimeGuardiansBot(commands.Bot):
    """
    Enhanced Discord bot for Grime Guardians operations.
    
    Features:
    - Real-time contractor status updates
    - Job assignment and tracking notifications
    - Quality violation alerts and strike tracking
    - Photo submission validation reminders
    - Performance recognition and celebrations
    - Emergency alert system
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.dm_messages = True
        
        super().__init__(
            command_prefix='!gg ',
            intents=intents,
            description="Grime Guardians Operations Bot"
        )
        
        self.guild_id = settings.discord_guild_id
        self.ops_lead_id = settings.discord_ops_lead_id
        
        # Channel configurations
        self.channel_configs = {
            "strikes": DiscordChannelConfig("❌-strikes", None, "Quality violations and strike tracking"),
            "alerts": DiscordChannelConfig("🚨-alerts", None, "Emergency alerts and urgent notifications"),
            "checkins": DiscordChannelConfig("✔️-job-check-ins", None, "Contractor check-ins and status updates"),
            "photos": DiscordChannelConfig("📸-photo-submissions", None, "Photo submission tracking and reminders"),
            "jobs": DiscordChannelConfig("🪧-job-board", None, "Job assignments and scheduling"),
            "general": DiscordChannelConfig("💬-general", None, "General team communication"),
            "management": DiscordChannelConfig("👔-management", None, "Management and administrative updates"),
            "announcements": DiscordChannelConfig("📢-announcements", None, "Company announcements and news"),
            "recognition": DiscordChannelConfig("🌟-recognition", None, "Performance recognition and celebrations")
        }
        
        self.channels: Dict[str, discord.TextChannel] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
    async def on_ready(self):
        """Bot ready event handler."""
        logger.info(f'{self.user} has connected to Discord!')
        
        # Get guild
        guild = discord.utils.get(self.guilds, id=int(self.guild_id)) if self.guild_id else self.guilds[0]
        if guild:
            logger.info(f'Connected to guild: {guild.name}')
            await self._setup_channels(guild)
            await self._start_background_tasks()
        else:
            logger.error("Could not find guild to connect to")
    
    async def _setup_channels(self, guild: discord.Guild):
        """Setup and organize Discord channels."""
        existing_channels = {channel.name: channel for channel in guild.text_channels}
        
        for key, config in self.channel_configs.items():
            if config.name in existing_channels:
                self.channels[key] = existing_channels[config.name]
                logger.info(f"Found existing channel: {config.name}")
            elif config.auto_create:
                try:
                    # Create channel with proper permissions
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
                    }
                    
                    channel = await guild.create_text_channel(
                        config.name,
                        topic=config.purpose,
                        overwrites=overwrites
                    )
                    self.channels[key] = channel
                    logger.info(f"Created channel: {config.name}")
                except Exception as e:
                    logger.error(f"Failed to create channel {config.name}: {e}")
        
        # Send startup notification
        if "general" in self.channels:
            await self.channels["general"].send(
                "🤖 **Grime Guardians Operations Bot Online**\n"
                "Ready to coordinate cleaning operations and team communication!"
            )
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks."""
        if not self.background_monitor.is_running():
            self.background_monitor.start()
    
    @tasks.loop(minutes=15)
    async def background_monitor(self):
        """Background monitoring for overdue check-ins and reminders."""
        try:
            await self._check_overdue_checkins()
            await self._send_photo_reminders()
        except Exception as e:
            logger.error(f"Error in background monitor: {e}")
    
    # Job Management Commands
    @commands.command(name='status')
    async def contractor_status(self, ctx, contractor_name: str = None):
        """Get contractor status information."""
        if contractor_name:
            # Get specific contractor status
            embed = discord.Embed(
                title=f"📊 {contractor_name.title()} Status",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Current Status", value="Available", inline=True)
            embed.add_field(name="Today's Jobs", value="2 completed, 1 in progress", inline=True)
            embed.add_field(name="Territory", value="South Metro", inline=True)
            await ctx.send(embed=embed)
        else:
            # Get all contractor statuses
            embed = discord.Embed(
                title="📊 All Contractor Status",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            contractors = [
                ("Jennifer", "✅ Available", "South Metro"),
                ("Olga", "🚗 En Route", "East Metro"),
                ("Zhanna", "🧽 Working", "Central Metro"),
                ("Liuda", "📱 Off Today", "North Metro")
            ]
            
            for name, status, territory in contractors:
                embed.add_field(name=name, value=f"{status}\n{territory}", inline=True)
            
            await ctx.send(embed=embed)
    
    @commands.command(name='jobs')
    async def active_jobs(self, ctx):
        """Show active jobs and assignments."""
        embed = discord.Embed(
            title="🪧 Active Jobs Today",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        jobs = [
            ("JOB001", "Deep Clean", "Jennifer", "123 Main St", "In Progress"),
            ("JOB002", "Move Out", "Olga", "456 Oak Ave", "Scheduled 2:00 PM"),
            ("JOB003", "Recurring", "Zhanna", "789 Pine Rd", "Completed")
        ]
        
        for job_id, service_type, contractor, address, status in jobs:
            embed.add_field(
                name=f"{job_id} - {service_type}",
                value=f"👤 {contractor}\n📍 {address}\n📊 {status}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='strike')
    @commands.has_permissions(manage_guild=True)
    async def add_strike(self, ctx, contractor_name: str, *, reason: str):
        """Add a strike to a contractor (management only)."""
        embed = discord.Embed(
            title="⚠️ Strike Added",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Contractor", value=contractor_name.title(), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Action Required", value="Performance coaching scheduled", inline=True)
        
        if "strikes" in self.channels:
            await self.channels["strikes"].send(embed=embed)
        await ctx.send("✅ Strike recorded and notifications sent.")
    
    # Public Methods for Agent Integration
    async def send_job_assignment(
        self,
        job_id: str,
        contractor_name: str,
        service_type: str,
        client_address: str,
        scheduled_time: str
    ) -> bool:
        """Send job assignment notification."""
        if "jobs" not in self.channels:
            return False
        
        embed = discord.Embed(
            title="🆕 New Job Assignment",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Job ID", value=job_id, inline=True)
        embed.add_field(name="Contractor", value=contractor_name.title(), inline=True)
        embed.add_field(name="Service", value=service_type.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Address", value=client_address, inline=False)
        embed.add_field(name="Scheduled", value=scheduled_time, inline=True)
        
        try:
            await self.channels["jobs"].send(embed=embed)
            logger.info(f"Job assignment sent: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send job assignment: {e}")
            return False
    
    async def send_checkin_update(
        self,
        contractor_name: str,
        status: str,
        job_id: Optional[str] = None,
        location: Optional[str] = None
    ) -> bool:
        """Send contractor check-in status update."""
        if "checkins" not in self.channels:
            return False
        
        status_emojis = {
            "arrived": "📍",
            "started": "🧽",
            "completed": "✅",
            "delayed": "⏰",
            "issue": "⚠️"
        }
        
        emoji = status_emojis.get(status.lower(), "📝")
        
        message = f"{emoji} **{contractor_name.title()}**: {status.replace('_', ' ').title()}"
        if job_id:
            message += f" (Job: {job_id})"
        if location:
            message += f"\n📍 {location}"
        
        try:
            await self.channels["checkins"].send(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send check-in update: {e}")
            return False
    
    async def send_quality_violation(
        self,
        contractor_name: str,
        violation_type: str,
        severity: str,
        job_id: str,
        strike_count: int
    ) -> bool:
        """Send quality violation alert."""
        if "strikes" not in self.channels:
            return False
        
        color = discord.Color.red() if severity == "high" else discord.Color.orange()
        
        embed = discord.Embed(
            title="⚠️ Quality Violation Alert",
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Contractor", value=contractor_name.title(), inline=True)
        embed.add_field(name="Violation", value=violation_type.replace('_', ' ').title(), inline=True)
        embed.add_field(name="Severity", value=severity.title(), inline=True)
        embed.add_field(name="Job ID", value=job_id, inline=True)
        embed.add_field(name="Strike Count", value=f"{strike_count}/3", inline=True)
        
        if strike_count >= 3:
            embed.add_field(
                name="🚨 CRITICAL ALERT",
                value="3rd Strike - Human approval required for penalty",
                inline=False
            )
            embed.color = discord.Color.dark_red()
        
        try:
            await self.channels["strikes"].send(embed=embed)
            
            # Ping ops lead for critical violations
            if strike_count >= 3 and self.ops_lead_id:
                await self.channels["strikes"].send(f"<@{self.ops_lead_id}> 3rd strike requires immediate attention!")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send quality violation: {e}")
            return False
    
    async def send_photo_reminder(
        self,
        contractor_name: str,
        job_id: str,
        hours_overdue: int
    ) -> bool:
        """Send photo submission reminder."""
        if "photos" not in self.channels:
            return False
        
        urgency = "🚨 URGENT" if hours_overdue >= 2 else "⏰ REMINDER"
        
        message = (
            f"{urgency} **Photo Submission Needed**\n"
            f"👤 Contractor: {contractor_name.title()}\n"
            f"🆔 Job: {job_id}\n"
            f"⏱️ Overdue: {hours_overdue} hours\n\n"
            f"Please submit completion photos ASAP for quality validation."
        )
        
        try:
            await self.channels["photos"].send(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send photo reminder: {e}")
            return False
    
    async def send_emergency_alert(
        self,
        alert_type: str,
        description: str,
        affected_parties: List[str] = None,
        action_required: Optional[str] = None
    ) -> bool:
        """Send emergency alert to management."""
        if "alerts" not in self.channels:
            return False
        
        embed = discord.Embed(
            title="🚨 EMERGENCY ALERT",
            description=description,
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Alert Type", value=alert_type.title(), inline=True)
        
        if affected_parties:
            embed.add_field(name="Affected", value=", ".join(affected_parties), inline=True)
        
        if action_required:
            embed.add_field(name="Action Required", value=action_required, inline=False)
        
        try:
            await self.channels["alerts"].send(embed=embed)
            
            # Ping ops lead for all emergencies
            if self.ops_lead_id:
                await self.channels["alerts"].send(f"<@{self.ops_lead_id}> Emergency requires immediate attention!")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
            return False
    
    async def send_recognition(
        self,
        contractor_name: str,
        achievement: str,
        details: Optional[str] = None
    ) -> bool:
        """Send performance recognition message."""
        if "recognition" not in self.channels:
            return False
        
        embed = discord.Embed(
            title="🌟 Performance Recognition",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Contractor", value=contractor_name.title(), inline=True)
        embed.add_field(name="Achievement", value=achievement, inline=True)
        
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        
        embed.set_footer(text="Keep up the excellent work! 🎉")
        
        try:
            await self.channels["recognition"].send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Failed to send recognition: {e}")
            return False
    
    async def send_general_notification(
        self,
        title: str,
        message: str,
        channel_type: str = "general"
    ) -> bool:
        """Send general notification to specified channel."""
        if channel_type not in self.channels:
            return False
        
        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        try:
            await self.channels[channel_type].send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Failed to send general notification: {e}")
            return False
    
    # Background Monitoring Methods
    async def _check_overdue_checkins(self):
        """Check for overdue contractor check-ins."""
        # This would integrate with the database to check for overdue check-ins
        # For now, we'll implement a placeholder
        pass
    
    async def _send_photo_reminders(self):
        """Send reminders for missing photo submissions."""
        # This would integrate with the database to check for missing photos
        # For now, we'll implement a placeholder
        pass


class DiscordIntegration:
    """
    Discord integration wrapper for easy use by agents.
    """
    
    def __init__(self):
        self.bot: Optional[GrimeGuardiansBot] = None
        self.is_running = False
        
    async def start_bot(self):
        """Start the Discord bot."""
        if self.is_running:
            return
        
        self.bot = GrimeGuardiansBot()
        
        try:
            await self.bot.start(settings.discord_bot_token)
            self.is_running = True
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            raise
    
    async def stop_bot(self):
        """Stop the Discord bot."""
        if self.bot and self.is_running:
            await self.bot.close()
            self.is_running = False
    
    # Proxy methods for agent use
    async def send_job_assignment(self, job_record: JobRecord) -> bool:
        """Send job assignment notification."""
        if not self.bot:
            return False
        
        return await self.bot.send_job_assignment(
            job_id=job_record.job_id,
            contractor_name=job_record.assigned_contractor,
            service_type=job_record.service_type,
            client_address=job_record.client_address,
            scheduled_time=job_record.scheduled_date.strftime("%m/%d %I:%M %p")
        )
    
    async def send_contractor_status(
        self,
        contractor_name: str,
        status: str,
        job_id: Optional[str] = None
    ) -> bool:
        """Send contractor status update."""
        if not self.bot:
            return False
        
        return await self.bot.send_checkin_update(contractor_name, status, job_id)
    
    async def send_quality_alert(
        self,
        violation: QualityViolation,
        strike_count: int
    ) -> bool:
        """Send quality violation alert."""
        if not self.bot:
            return False
        
        return await self.bot.send_quality_violation(
            contractor_name=violation.contractor_id,
            violation_type=violation.violation_type,
            severity=violation.severity,
            job_id=violation.job_id,
            strike_count=strike_count
        )
    
    async def send_emergency(
        self,
        alert_type: str,
        description: str,
        affected_parties: List[str] = None
    ) -> bool:
        """Send emergency alert."""
        if not self.bot:
            return False
        
        return await self.bot.send_emergency_alert(alert_type, description, affected_parties)
    
    async def send_achievement(
        self,
        contractor_name: str,
        achievement: str,
        details: Optional[str] = None
    ) -> bool:
        """Send achievement recognition."""
        if not self.bot:
            return False
        
        return await self.bot.send_recognition(contractor_name, achievement, details)


# Singleton instance
_discord_integration = None

def get_discord_integration() -> DiscordIntegration:
    """Get singleton Discord integration instance."""
    global _discord_integration
    if _discord_integration is None:
        _discord_integration = DiscordIntegration()
    return _discord_integration