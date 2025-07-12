#!/usr/bin/env python3
"""
Dean Strategic Sales Discord Bot Runner
Dedicated service for Dean's sales automation and conversation management
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from integrations.discord_bot import DiscordBot
from config import settings
from core.dean_conversation import dean_conversation
from core.email_agent import email_agent
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class DeanDiscordBot(DiscordBot):
    """
    Dean's specialized Discord bot for strategic sales management.
    Extends the base DiscordBot with Dean-specific functionality.
    """
    
    def __init__(self):
        super().__init__()
        # Use Dean-specific token if available, fallback to general token
        self.token = settings.discord_bot_token_dean or settings.discord_bot_token
        
        # Dean-specific channels
        self.sales_channel_id = getattr(settings, 'dean_sales_channel_id', None)
        self.approval_channel_id = getattr(settings, 'dean_approval_channel_id', None)
        self.reports_channel_id = getattr(settings, 'dean_reports_channel_id', None)
        
        logger.info("Dean Discord Bot initialized")
    
    async def on_ready(self):
        """Called when Dean's bot is ready."""
        await super().on_ready()
        logger.info(f"🎯 Dean Strategic Sales Director is online!")
        logger.info(f"💼 Serving {len(self.guilds)} servers with strategic sales automation")
        
        # Set Dean-specific status
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Strategic Sales Pipeline | !gg dean"
            )
        )
        
        # Start Dean's background tasks
        self.start_dean_tasks()
    
    def start_dean_tasks(self):
        """Start Dean's background monitoring tasks."""
        if not hasattr(self, '_dean_tasks_started'):
            self._dean_tasks_started = True
            
            # Start email monitoring
            self.monitor_email_campaigns.start()
            self.check_pending_approvals.start()
            
            logger.info("🤖 Dean's background tasks started")
    
    @tasks.loop(minutes=15)
    async def monitor_email_campaigns(self):
        """Monitor email campaigns and report metrics."""
        try:
            if not self.reports_channel_id:
                return
            
            # Get campaign metrics from Email Agent
            campaigns = email_agent.get_active_campaigns()
            
            if campaigns:
                # Send daily summary at 9 AM
                from datetime import datetime
                if datetime.now().hour == 9 and datetime.now().minute < 15:
                    summary = self.build_campaign_summary(campaigns)
                    await self.send_to_channel(self.reports_channel_id, summary)
                    
        except Exception as e:
            logger.error(f"Error monitoring email campaigns: {e}")
    
    @tasks.loop(minutes=5)
    async def check_pending_approvals(self):
        """Check for pending email approvals and notify."""
        try:
            if not self.approval_channel_id:
                return
            
            pending = email_agent.get_pending_approvals()
            
            # Notify about pending approvals (limit notifications)
            if len(pending) > 0:
                embed = discord.Embed(
                    title="📧 Emails Awaiting Approval",
                    description=f"{len(pending)} emails need review",
                    color=discord.Color.orange()
                )
                
                for i, email in enumerate(pending[:3]):
                    embed.add_field(
                        name=f"Email {i+1}",
                        value=f"To: {email['to']}\nSubject: {email['subject'][:50]}...",
                        inline=False
                    )
                
                # Only send if we haven't notified recently
                if not hasattr(self, '_last_approval_notification'):
                    await self.send_to_channel(self.approval_channel_id, embed=embed)
                    self._last_approval_notification = datetime.now()
                    
        except Exception as e:
            logger.error(f"Error checking pending approvals: {e}")
    
    def build_campaign_summary(self, campaigns):
        """Build daily campaign performance summary."""
        total_sent = sum(campaign.get('send_count', 0) for campaign in campaigns)
        active_campaigns = len([c for c in campaigns if c.get('status') == 'active'])
        
        summary = f"""📊 **Daily Sales Report** - {datetime.now().strftime('%B %d, %Y')}

**Campaign Performance:**
• Active Campaigns: {active_campaigns}
• Emails Sent Today: {total_sent}
• Response Rate: Calculating...

**Strategic Focus:**
Dean is monitoring lead generation and conversion optimization.

*Use `!gg dean campaigns` for detailed metrics*"""
        
        return summary
    
    async def on_message(self, message):
        """Override to prioritize Dean's conversation handling."""
        if message.author.bot:
            return
        
        content = message.content.lower()
        
        # Enhanced Dean keyword detection
        dean_keywords = [
            'dean', 'sales', 'marketing', 'lead', 'campaign', 'revenue',
            'email', 'outreach', 'prospect', 'conversion', 'funnel'
        ]
        
        # Route to Dean if any strategic sales keywords are detected
        if any(keyword in content for keyword in dean_keywords):
            await self.handle_dean_conversation(message)
            return
        
        # Fall back to standard message handling
        await super().on_message(message)


async def main():
    """Main function to run Dean's Discord bot."""
    logger.info("🚀 Starting Dean Strategic Sales Director Bot")
    
    # Initialize Dean's systems
    logger.info("🧠 Initializing Dean's conversation engine...")
    dean_conversation.persona_config  # Initialize Dean
    
    logger.info("📧 Initializing Email Agent...")
    email_agent.templates  # Initialize Email Agent
    
    # Create and start Dean's Discord bot
    dean_bot = DeanDiscordBot()
    
    # Graceful shutdown handler
    def signal_handler(signum, frame):
        logger.info("🛑 Received shutdown signal, closing Dean's systems...")
        asyncio.create_task(dean_bot.close())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start Dean's Discord bot
        await dean_bot.start(dean_bot.token)
    except Exception as e:
        logger.error(f"❌ Failed to start Dean's Discord bot: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())