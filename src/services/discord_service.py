import asyncio
import os
from typing import Optional
import structlog

from ..integrations.discord_bot import discord_bot, start_discord_bot, stop_discord_bot

logger = structlog.get_logger()


class DiscordService:
    """
    Discord service manager for the Grime Guardians bot.
    
    Manages the lifecycle of the Discord bot as a background service
    that runs alongside the main FastAPI application.
    """
    
    def __init__(self):
        self.bot = discord_bot
        self.task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Discord service manager - bot runs as separate service."""
        logger.info("Discord service manager initialized (bot runs separately)")
        # Mark as running for status checks, but don't actually start the bot
        # The bot runs as a separate systemd service to avoid worker duplication
        self.running = True
    
    async def stop(self):
        """Stop the Discord service manager."""
        logger.info("Discord service manager stopped (bot runs separately)")
        self.running = False
    
    def is_running(self) -> bool:
        """Check if the Discord service is running."""
        # For now, always return True since we manage this separately
        # In the future, this could check if the separate Discord service is running
        return True
    
    async def send_message(self, channel_id: int, content: str = None, embed: dict = None):
        """Send message through Discord bot."""
        if not self.is_running():
            logger.error("Discord service not running, cannot send message")
            return False
        
        try:
            import discord
            discord_embed = None
            if embed:
                discord_embed = discord.Embed.from_dict(embed)
            
            return await self.bot.send_to_channel(channel_id, content, discord_embed)
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False
    
    async def send_dm(self, user_id: int, content: str = None, embed: dict = None):
        """Send direct message through Discord bot."""
        if not self.is_running():
            logger.error("Discord service not running, cannot send DM")
            return False
        
        try:
            import discord
            discord_embed = None
            if embed:
                discord_embed = discord.Embed.from_dict(embed)
            
            return await self.bot.send_dm(user_id, content, discord_embed)
        except Exception as e:
            logger.error(f"Error sending Discord DM: {e}")
            return False
    
    async def notify_checkin_required(self, contractor_name: str, job_details: dict):
        """Notify contractor that check-in is required."""
        if not self.is_running():
            logger.error("Discord service not running, cannot send notification")
            return False
        
        try:
            await self.bot.notify_checkin_required(contractor_name, job_details)
            return True
        except Exception as e:
            logger.error(f"Error sending check-in notification: {e}")
            return False
    
    async def notify_violation(self, contractor_name: str, violation_type: str, details: str):
        """Notify about contractor violations."""
        if not self.is_running():
            logger.error("Discord service not running, cannot send violation notification")
            return False
        
        try:
            await self.bot.notify_violation(contractor_name, violation_type, details)
            return True
        except Exception as e:
            logger.error(f"Error sending violation notification: {e}")
            return False


# Global Discord service instance
discord_service = DiscordService()