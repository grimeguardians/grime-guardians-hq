"""
Discord Integration Tools
Real-time contractor communication and notification system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import discord
from discord.ext import commands
from pydantic import BaseModel

from ..config.settings import get_settings
from ..models.schemas import JobSchema, ContractorSchema
from ..utils.time_utils import now_ct

logger = logging.getLogger(__name__)
settings = get_settings()


class DiscordChannelType(str, Enum):
    """Discord channel types for business workflow."""
    STRIKES = "❌-strikes"
    ALERTS = "🚨-alerts"
    JOB_CHECKINS = "✔️-job-check-ins"
    PHOTO_SUBMISSIONS = "📸-photo-submissions"
    JOB_BOARD = "🪧-job-board"
    GENERAL = "💬-general"
    MANAGEMENT = "👔-management"
    ANNOUNCEMENTS = "📢-announcements"


@dataclass
class DiscordMessage:
    """Discord message structure."""
    channel: str
    content: str
    embeds: List[discord.Embed] = None
    files: List[discord.File] = None
    components: List[Any] = None
    thread_name: Optional[str] = None


@dataclass
class DiscordNotification:
    """Business notification for Discord."""
    notification_type: str
    priority: str  # 'low', 'normal', 'high', 'urgent'
    title: str
    message: str
    data: Dict[str, Any]
    recipients: List[str] = None
    requires_action: bool = False
    expires_at: Optional[datetime] = None


class DiscordToolkit:
    """
    Discord integration toolkit for contractor communication.
    Provides standardized tools for agent use.
    """
    
    def __init__(self):
        self.bot = None
        self.guild = None
        self.channels: Dict[str, discord.TextChannel] = {}
        self.is_ready = False
        
        # Message queue for when bot is not ready
        self.message_queue: List[DiscordMessage] = []
        
        # Channel mapping
        self.channel_map = {
            DiscordChannelType.STRIKES: None,
            DiscordChannelType.ALERTS: None,
            DiscordChannelType.JOB_CHECKINS: None,
            DiscordChannelType.PHOTO_SUBMISSIONS: None,
            DiscordChannelType.JOB_BOARD: None,
            DiscordChannelType.GENERAL: None,
            DiscordChannelType.MANAGEMENT: None,
            DiscordChannelType.ANNOUNCEMENTS: None
        }
    
    async def initialize(self, bot_token: str, guild_id: int) -> bool:
        """Initialize Discord bot connection."""
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.members = True
            
            self.bot = commands.Bot(command_prefix='!', intents=intents)
            
            @self.bot.event
            async def on_ready():
                logger.info(f"Discord bot logged in as {self.bot.user}")
                self.guild = self.bot.get_guild(guild_id)
                
                if self.guild:
                    await self._map_channels()
                    self.is_ready = True
                    
                    # Process queued messages
                    await self._process_message_queue()
                    
                    logger.info("Discord toolkit ready")
                else:
                    logger.error(f"Could not find guild with ID {guild_id}")
            
            # Start bot in background
            asyncio.create_task(self.bot.start(bot_token))
            
            # Wait for ready state
            timeout = 30  # 30 second timeout
            while not self.is_ready and timeout > 0:
                await asyncio.sleep(1)
                timeout -= 1
            
            return self.is_ready
            
        except Exception as e:
            logger.error(f"Discord initialization error: {e}")
            return False
    
    async def _map_channels(self) -> None:
        """Map business channels to Discord channels."""
        for channel in self.guild.text_channels:
            channel_name = channel.name
            
            # Map known business channels
            for channel_type in DiscordChannelType:
                if channel_type.value.lstrip('🔥❌🚨✔️📸🪧💬👔📢') in channel_name:
                    self.channel_map[channel_type] = channel
                    self.channels[channel_type.value] = channel
                    logger.info(f"Mapped channel: {channel_name} -> {channel_type.value}")
    
    async def _process_message_queue(self) -> None:
        """Process queued messages when bot becomes ready."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            await self._send_message_internal(message)
    
    # Core messaging tools for agents
    
    async def send_message(
        self, 
        channel: str, 
        content: str, 
        embed: discord.Embed = None,
        files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send message to Discord channel.
        Primary tool for agent communication.
        """
        try:
            discord_message = DiscordMessage(
                channel=channel,
                content=content,
                embeds=[embed] if embed else None,
                files=await self._prepare_files(files) if files else None
            )
            
            if not self.is_ready:
                self.message_queue.append(discord_message)
                return {
                    "status": "queued",
                    "message": "Bot not ready, message queued"
                }
            
            result = await self._send_message_internal(discord_message)
            return {
                "status": "sent",
                "message_id": result.id if result else None,
                "channel": channel
            }
            
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _send_message_internal(self, discord_message: DiscordMessage) -> Optional[discord.Message]:
        """Internal message sending logic."""
        try:
            channel = self.channels.get(discord_message.channel)
            if not channel:
                logger.error(f"Channel not found: {discord_message.channel}")
                return None
            
            # Send message
            sent_message = await channel.send(
                content=discord_message.content,
                embeds=discord_message.embeds,
                files=discord_message.files
            )
            
            # Create thread if requested
            if discord_message.thread_name:
                await sent_message.create_thread(name=discord_message.thread_name)
            
            return sent_message
            
        except Exception as e:
            logger.error(f"Internal message send error: {e}")
            return None
    
    async def _prepare_files(self, file_paths: List[str]) -> List[discord.File]:
        """Prepare files for Discord upload."""
        files = []
        for file_path in file_paths:
            try:
                files.append(discord.File(file_path))
            except Exception as e:
                logger.warning(f"Could not prepare file {file_path}: {e}")
        return files
    
    # Business workflow tools
    
    async def send_job_checkin(
        self,
        contractor_name: str,
        job_id: str,
        status: str,
        location: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Send job check-in notification."""
        
        # Determine status emoji
        status_emoji = {
            "arrived": "🟢",
            "started": "🔵", 
            "completed": "✅",
            "delayed": "🟡",
            "issue": "🔴"
        }.get(status, "⚪")
        
        timestamp = now_ct().strftime("%I:%M %p")
        
        content = f"""{status_emoji} **{status.upper()}** - {contractor_name}

**Job:** {job_id}
**Location:** {location}
**Time:** {timestamp}

{f"**Notes:** {notes}" if notes else ""}"""
        
        return await self.send_message(
            DiscordChannelType.JOB_CHECKINS.value,
            content
        )
    
    async def send_strike_notification(
        self,
        contractor_name: str,
        strike_number: int,
        violation_type: str,
        job_id: str,
        description: str
    ) -> Dict[str, Any]:
        """Send quality violation strike notification."""
        
        embed = discord.Embed(
            title=f"🚨 STRIKE #{strike_number} - {contractor_name}",
            description=description,
            color=discord.Color.red() if strike_number >= 3 else discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Violation Type", value=violation_type, inline=True)
        embed.add_field(name="Job ID", value=job_id, inline=True)
        embed.add_field(name="Total Strikes", value=f"{strike_number}/3", inline=True)
        
        if strike_number >= 3:
            embed.add_field(
                name="⚠️ ACTION REQUIRED", 
                value="3rd strike reached - Management approval needed for penalty",
                inline=False
            )
        
        content = f"<@&management> " if strike_number >= 3 else ""
        
        return await self.send_message(
            DiscordChannelType.STRIKES.value,
            content,
            embed=embed
        )
    
    async def send_job_posting(
        self,
        job_details: Dict[str, Any],
        preferred_contractors: List[str] = None
    ) -> Dict[str, Any]:
        """Post new job opportunity to job board."""
        
        embed = discord.Embed(
            title="🪧 New Job Available",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Service Type", value=job_details.get('service_type', 'N/A'), inline=True)
        embed.add_field(name="Date", value=job_details.get('date', 'N/A'), inline=True)
        embed.add_field(name="Location", value=job_details.get('location', 'N/A'), inline=True)
        embed.add_field(name="Pay Rate", value=f"${job_details.get('pay_rate', 0)}/hr", inline=True)
        embed.add_field(name="Duration", value=f"{job_details.get('duration', 0)} hours", inline=True)
        embed.add_field(name="Territory", value=job_details.get('territory', 'Any'), inline=True)
        
        if job_details.get('special_notes'):
            embed.add_field(name="Special Notes", value=job_details['special_notes'], inline=False)
        
        # Mention preferred contractors
        mentions = ""
        if preferred_contractors:
            mentions = " ".join([f"<@{contractor}>" for contractor in preferred_contractors])
        
        content = f"{mentions}\n\nReact with ✅ to claim this job!"
        
        result = await self.send_message(
            DiscordChannelType.JOB_BOARD.value,
            content,
            embed=embed
        )
        
        # Add reaction for claiming
        if result.get('status') == 'sent':
            try:
                channel = self.channels[DiscordChannelType.JOB_BOARD.value]
                message = await channel.fetch_message(result['message_id'])
                await message.add_reaction('✅')
            except Exception as e:
                logger.warning(f"Could not add reaction to job posting: {e}")
        
        return result
    
    async def send_urgent_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send urgent business alert to management."""
        
        embed = discord.Embed(
            title=f"🚨 URGENT ALERT: {title}",
            description=message,
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Alert Type", value=alert_type, inline=True)
        embed.add_field(name="Priority", value="URGENT", inline=True)
        
        if data:
            for key, value in data.items():
                embed.add_field(name=key.replace('_', ' ').title(), value=str(value), inline=True)
        
        content = "<@&management> IMMEDIATE ATTENTION REQUIRED"
        
        return await self.send_message(
            DiscordChannelType.ALERTS.value,
            content,
            embed=embed
        )
    
    async def send_photo_submission(
        self,
        contractor_name: str,
        job_id: str,
        photo_paths: List[str],
        photo_type: str = "completion"
    ) -> Dict[str, Any]:
        """Send job completion photos to photo submissions channel."""
        
        content = f"📸 **{photo_type.title()} Photos** - {contractor_name}\n**Job:** {job_id}\n**Submitted:** {now_ct().strftime('%I:%M %p')}"
        
        return await self.send_message(
            DiscordChannelType.PHOTO_SUBMISSIONS.value,
            content,
            files=photo_paths
        )
    
    async def create_job_thread(
        self,
        job_id: str,
        job_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create dedicated thread for job coordination."""
        
        initial_message = f"""🧵 **Job Thread Created**

**Job ID:** {job_id}
**Service:** {job_details.get('service_type', 'N/A')}
**Client:** {job_details.get('client_name', 'N/A')}
**Address:** {job_details.get('address', 'N/A')}
**Scheduled:** {job_details.get('scheduled_date', 'N/A')}

This thread will track all communications for this job."""
        
        discord_message = DiscordMessage(
            channel=DiscordChannelType.JOB_CHECKINS.value,
            content=initial_message,
            thread_name=f"Job {job_id}"
        )
        
        if not self.is_ready:
            self.message_queue.append(discord_message)
            return {"status": "queued"}
        
        result = await self._send_message_internal(discord_message)
        return {
            "status": "created" if result else "error",
            "thread_id": result.id if result else None
        }
    
    # User management tools
    
    async def get_user_by_name(self, name: str) -> Optional[discord.Member]:
        """Find Discord user by name."""
        if not self.guild:
            return None
        
        # Try exact match first
        member = discord.utils.get(self.guild.members, display_name=name)
        if not member:
            member = discord.utils.get(self.guild.members, name=name)
        
        # Try partial match
        if not member:
            for member in self.guild.members:
                if name.lower() in member.display_name.lower():
                    return member
        
        return member
    
    async def send_direct_message(
        self,
        user_name: str,
        message: str
    ) -> Dict[str, Any]:
        """Send direct message to contractor."""
        try:
            member = await self.get_user_by_name(user_name)
            if not member:
                return {
                    "status": "error",
                    "error": f"User {user_name} not found"
                }
            
            await member.send(message)
            
            return {
                "status": "sent",
                "recipient": member.display_name
            }
            
        except discord.Forbidden:
            return {
                "status": "error", 
                "error": "Cannot send DM to user (privacy settings)"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # System management
    
    async def get_channel_list(self) -> List[Dict[str, Any]]:
        """Get list of available channels."""
        channels = []
        for name, channel in self.channels.items():
            channels.append({
                "name": name,
                "id": channel.id if channel else None,
                "mapped": channel is not None
            })
        return channels
    
    async def get_online_contractors(self) -> List[Dict[str, str]]:
        """Get list of online contractors."""
        if not self.guild:
            return []
        
        online_members = []
        for member in self.guild.members:
            if (member.status != discord.Status.offline and 
                not member.bot and 
                any(role.name.lower() in ['contractor', 'cleaner'] for role in member.roles)):
                online_members.append({
                    "name": member.display_name,
                    "status": str(member.status),
                    "id": str(member.id)
                })
        
        return online_members
    
    async def shutdown(self) -> None:
        """Gracefully shutdown Discord bot."""
        if self.bot:
            await self.bot.close()
            self.is_ready = False
            logger.info("Discord bot shutdown")


# Agent tool wrappers for easy integration

class DiscordAgentTools:
    """
    Simplified Discord tools for agent use.
    Provides high-level business functions.
    """
    
    def __init__(self):
        self.toolkit = DiscordToolkit()
    
    async def initialize(self, bot_token: str, guild_id: int) -> bool:
        """Initialize Discord connection."""
        return await self.toolkit.initialize(bot_token, guild_id)
    
    async def notify_job_status(
        self, 
        contractor_id: str, 
        job_id: str, 
        status: str, 
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Agent tool: Notify job status change."""
        details = details or {}
        
        return await self.toolkit.send_job_checkin(
            contractor_name=details.get('contractor_name', contractor_id),
            job_id=job_id,
            status=status,
            location=details.get('location', 'Unknown'),
            notes=details.get('notes', '')
        )
    
    async def escalate_quality_issue(
        self, 
        contractor_id: str, 
        violation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agent tool: Escalate quality violation."""
        
        return await self.toolkit.send_strike_notification(
            contractor_name=violation_details.get('contractor_name', contractor_id),
            strike_number=violation_details.get('strike_number', 1),
            violation_type=violation_details.get('violation_type', 'Quality Issue'),
            job_id=violation_details.get('job_id', 'Unknown'),
            description=violation_details.get('description', 'Quality violation detected')
        )
    
    async def post_job_opportunity(
        self, 
        job_data: Dict[str, Any], 
        target_contractors: List[str] = None
    ) -> Dict[str, Any]:
        """Agent tool: Post job to contractor board."""
        
        return await self.toolkit.send_job_posting(
            job_details=job_data,
            preferred_contractors=target_contractors
        )
    
    async def send_urgent_notification(
        self, 
        notification_type: str, 
        title: str, 
        message: str, 
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Agent tool: Send urgent business notification."""
        
        return await self.toolkit.send_urgent_alert(
            alert_type=notification_type,
            title=title,
            message=message,
            data=data
        )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Agent tool: Get Discord system status."""
        
        return {
            "is_ready": self.toolkit.is_ready,
            "channels_mapped": len([c for c in self.toolkit.channels.values() if c]),
            "queued_messages": len(self.toolkit.message_queue),
            "online_contractors": await self.toolkit.get_online_contractors()
        }