import asyncio
import re
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
import discord
from discord.ext import commands, tasks
import structlog

from ..config import settings
from ..models.schemas import AgentType, AgentMessage, MessagePriority, CheckInEvent
from ..agents import ava, keith, sophia, maya
from ..core.ava_conversation import ava_conversation
from ..core.dean_conversation import dean_conversation

logger = structlog.get_logger()


class DiscordBot(commands.Bot):
    """
    Grime Guardians Discord Bot - Ava Integration
    
    Handles contractor check-ins, photo submissions, status updates,
    and team communication for the Grime Guardians cleaning service.
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!gg ',
            intents=intents,
            description="Grime Guardians Operations Bot"
        )
        
        # Channel configuration
        self.checkin_channel_id = int(settings.discord_checkin_channel_id)
        self.ops_lead_id = int(settings.discord_ops_lead_id)
        
        # State tracking - matching legacy functionality
        self.job_map = {}  # username -> current job_id mapping
        self.contractor_status = {}
        
        # Status emojis
        self.status_emojis = {
            'arrived': '🚗',
            'finished': '🏁',
            'help': '🆘',
            'issue': '⚠️',
            'photo': '📸',
            'checklist': '✅'
        }
        
        # Trigger words - matching legacy patterns
        self.arrival_triggers = ['🚗', 'arrived', "i've arrived", 'here', "i'm here", 'starting']
        self.finished_triggers = ['🏁', 'finished', "i'm finished", 'done', 'all done']
        
        # Add commands
        self.setup_commands()
    
    def generate_job_id(self, username: str, timestamp: str) -> str:
        """Generate job ID matching legacy format: username-MMDDYYYY-XXX"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # Convert to CST (America/Chicago)
            import pytz
            cst = pytz.timezone('America/Chicago')
            cst_dt = dt.astimezone(cst)
            
            # Format as MMDDYYYY
            date_part = cst_dt.strftime('%m%d%Y')
            
            # Random 3-digit number
            random_num = str(random.randint(0, 999)).zfill(3)
            
            return f"{username}-{date_part}-{random_num}"
        except Exception as e:
            logger.error(f"Error generating job ID: {e}")
            # Fallback to simpler format
            date_part = datetime.now().strftime('%m%d%Y')
            random_num = str(random.randint(0, 999)).zfill(3)
            return f"{username}-{date_part}-{random_num}"
    
    async def setup_hook(self):
        """Setup hook called when bot is ready."""
        logger.info("Discord bot setup starting")
        
        # Start background tasks
        self.check_missed_checkins.start()
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Discord bot logged in as {self.user}")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set status
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Grime Guardians Operations"
            )
        )
    
    async def on_message(self, message):
        """Handle incoming messages - check-ins and conversations."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        content = message.content.lower()
        timestamp = datetime.utcnow().isoformat()
        username = message.author.display_name
        
        # Check for arrival triggers
        has_arrival_trigger = any(trigger in content for trigger in self.arrival_triggers)
        if has_arrival_trigger:
            await self.handle_arrival(message, username, timestamp)
            return
        
        # Check for finished triggers  
        has_finished_trigger = any(trigger in content for trigger in self.finished_triggers)
        if has_finished_trigger:
            await self.handle_finished(message, username, timestamp)
            return
        
        # Handle conversational messages (DMs and monitored channels)
        if isinstance(message.channel, discord.DMChannel) or message.channel.id == self.checkin_channel_id:
            # Check if message is directed at Dean (strategic sales)
            if any(keyword in content for keyword in ['dean', 'sales', 'marketing', 'lead', 'campaign', 'revenue']):
                await self.handle_dean_conversation(message)
            else:
                await self.handle_conversation(message)
            return
        
        # Process commands
        await self.process_commands(message)
    
    async def handle_arrival(self, message, username: str, timestamp: str):
        """Handle contractor arrival - matching legacy pattern."""
        logger.info(f"🛬 {username} has ARRIVED at job")
        
        try:
            # Send immediate confirmation - matching legacy format
            await message.channel.send(f"✅ Got it, {username} — you're checked in! 🚗")
            
            # Generate and store job ID
            job_id = self.generate_job_id(username, timestamp)
            self.job_map[username] = job_id
            
            # Create payload for agent system
            payload = {
                'username': username,
                'message': message.content + ' 🚗',
                'timestamp': timestamp,
                'action': 'arrived',
                'job_id': job_id,
                'discord_user_id': str(message.author.id),
                'channel_id': str(message.channel.id),
                'message_id': str(message.id)
            }
            
            # Route to Keith for processing
            agent_message = AgentMessage(
                agent_id=AgentType.KEITH,
                message_type="discord_checkin_arrival",
                content=f"Contractor arrived: {username}",
                priority=MessagePriority.HIGH,
                metadata=payload
            )
            
            await keith.send_message(agent_message)
            logger.info(f"📡 Sent ARRIVED check-in to Keith for {username}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process arrival for {username}: {e}")
    
    async def handle_finished(self, message, username: str, timestamp: str):
        """Handle job completion - matching legacy pattern."""
        logger.info(f"✅ {username} has FINISHED the job")
        
        try:
            # Send immediate confirmation - matching legacy format
            await message.channel.send(f"🎉 Great work, {username}! Job marked as finished.")
            
            # Retrieve job ID for this user
            job_id = self.job_map.get(username)
            
            # Create payload for agent system
            payload = {
                'username': username,
                'message': message.content + ' 🏁',
                'timestamp': timestamp,
                'action': 'finished',
                'job_id': job_id,
                'discord_user_id': str(message.author.id),
                'channel_id': str(message.channel.id),
                'message_id': str(message.id)
            }
            
            # Route to Keith for processing
            agent_message = AgentMessage(
                agent_id=AgentType.KEITH,
                message_type="discord_checkin_finished",
                content=f"Contractor finished: {username}",
                priority=MessagePriority.HIGH,
                metadata=payload
            )
            
            await keith.send_message(agent_message)
            logger.info(f"📡 Sent FINISHED check-in to Keith for {username}")
            
            # Clear job ID after completion - matching legacy behavior
            if username in self.job_map:
                del self.job_map[username]
                
        except Exception as e:
            logger.error(f"❌ Failed to process completion for {username}: {e}")
    
    async def handle_conversation(self, message):
        """Handle conversational messages with Ava."""
        try:
            user_id = str(message.author.id)
            username = message.author.display_name
            user_message = message.content
            
            # Determine if it's a DM or channel
            channel_id = None if isinstance(message.channel, discord.DMChannel) else str(message.channel.id)
            
            logger.info(f"💬 Conversation message from {username}: {user_message[:50]}...")
            
            # Build user context for Ava
            user_context = {
                'username': username,
                'discord_id': user_id,
                'message_type': 'dm' if isinstance(message.channel, discord.DMChannel) else 'channel',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get response from Ava's conversation engine
            response = await ava_conversation.handle_conversation(
                user_id=user_id,
                user_message=user_message,
                channel_id=channel_id,
                user_context=user_context
            )
            
            # Send response back to Discord (handle Discord's 2000 char limit)
            await self.send_long_message(message.channel, response)
            
            logger.info(f"✅ Sent conversation response to {username}")
            
        except Exception as e:
            logger.error(f"❌ Error handling conversation: {e}")
            await message.channel.send(
                "I'm having trouble processing your message right now. Please try again in a moment!"
            )
    
    async def handle_dean_conversation(self, message):
        """Handle strategic sales conversations with Dean."""
        try:
            user_id = str(message.author.id)
            username = message.author.display_name
            user_message = message.content
            
            # Determine if it's a DM or channel
            channel_id = None if isinstance(message.channel, discord.DMChannel) else str(message.channel.id)
            
            logger.info(f"💼 Dean conversation from {username}: {user_message[:50]}...")
            
            # Build user context for Dean
            user_context = {
                'username': username,
                'discord_id': user_id,
                'message_type': 'dm' if isinstance(message.channel, discord.DMChannel) else 'channel',
                'timestamp': datetime.utcnow().isoformat(),
                'context': 'strategic_sales'
            }
            
            # Get response from Dean's conversation engine
            response = await dean_conversation.handle_conversation(
                user_id=user_id,
                user_message=user_message,
                channel_id=channel_id,
                user_context=user_context
            )
            
            # Send response back to Discord (handle Discord's 2000 char limit)
            await self.send_long_message(message.channel, response)
            
            logger.info(f"✅ Sent Dean response to {username}")
            
        except Exception as e:
            logger.error(f"❌ Error handling Dean conversation: {e}")
            await message.channel.send(
                "Strategic systems temporarily offline. Critical sales decisions pending your input."
            )
    
    async def handle_help_request(self, message, author):
        """Handle contractor help requests."""
        logger.warning(f"Help request from {author.display_name}: {message.content}")
        
        # React immediately
        await message.add_reaction('🆘')
        
        # Notify ops lead
        ops_lead = self.get_user(self.ops_lead_id)
        if ops_lead:
            embed = discord.Embed(
                title="🆘 Contractor Help Request",
                description=f"**Contractor:** {author.mention}\n**Message:** {message.content}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            try:
                await ops_lead.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Cannot DM ops lead {ops_lead.id}")
        
        # Route to Dmitri for escalation handling
        agent_message = AgentMessage(
            agent_id=AgentType.DMITRI,
            message_type="help_request",
            content=message.content,
            priority=MessagePriority.URGENT,
            metadata={
                "discord_user_id": str(author.id),
                "discord_username": author.display_name,
                "channel_id": str(message.channel.id),
                "message_id": str(message.id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send immediate response
        embed = discord.Embed(
            title="🆘 Help Request Received",
            description=f"Thanks {author.mention}, help is on the way! The ops team has been notified.",
            color=discord.Color.orange()
        )
        await message.channel.send(embed=embed)
    
    async def handle_photo_submission(self, message, author):
        """Handle photo submissions from contractors."""
        logger.info(f"Photo submission from {author.display_name}: {len(message.attachments)} photos")
        
        # React with photo emoji
        await message.add_reaction('📸')
        
        # Validate photos
        valid_photos = []
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                valid_photos.append(attachment)
        
        if valid_photos:
            embed = discord.Embed(
                title="📸 Photos Received",
                description=f"Thanks {author.mention}! Received {len(valid_photos)} photo(s)",
                color=discord.Color.green()
            )
            
            # Check if all required photos are present
            if len(valid_photos) >= 4:  # Kitchen, bathrooms, entry, impacted rooms
                embed.add_field(
                    name="✅ Photo Requirements",
                    value="All required photos received!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Photo Reminder",
                    value="Please ensure you have photos of:\n• Kitchen\n• All Bathrooms\n• Entry Area\n• All Impacted Rooms",
                    inline=False
                )
            
            await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Invalid Photos",
                description="Please submit valid image files (JPG, PNG, WEBP)",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
    
    
    def setup_commands(self):
        """Setup bot commands."""
        
        @self.command(name='status')
        async def status_command(ctx, contractor_name: Optional[str] = None):
            """Check contractor status."""
            if contractor_name:
                # Check specific contractor
                embed = discord.Embed(
                    title=f"📊 Status: {contractor_name}",
                    description="Contractor status information",
                    color=discord.Color.blue()
                )
                # Add status logic here
            else:
                # Show all contractors
                embed = discord.Embed(
                    title="📊 All Contractor Status",
                    description="Current status of all contractors",
                    color=discord.Color.blue()
                )
                # Add status logic here
            
            await ctx.send(embed=embed)
        
        @self.command(name='jobs')
        async def jobs_command(ctx):
            """Show today's job schedule."""
            embed = discord.Embed(
                title="📅 Today's Jobs",
                description="Current job assignments and schedule",
                color=discord.Color.green()
            )
            # Add job logic here
            await ctx.send(embed=embed)
        
        @self.command(name='dean')
        async def dean_command(ctx, action: str = None, *, args: str = None):
            """Dean's strategic sales commands."""
            if action == 'campaigns':
                from ..core.email_agent import email_agent
                campaigns = email_agent.get_active_campaigns()
                
                embed = discord.Embed(
                    title="📧 Active Email Campaigns",
                    description=f"Total campaigns: {len(campaigns)}",
                    color=discord.Color.green()
                )
                
                for campaign in campaigns[:5]:  # Show first 5
                    embed.add_field(
                        name=campaign['name'],
                        value=f"Status: {campaign['status']}\nSent: {campaign['send_count']}\nResponse: {campaign['response_rate']}%",
                        inline=True
                    )
                
                await ctx.send(embed=embed)
            
            elif action == 'approvals':
                from ..core.email_agent import email_agent
                pending = email_agent.get_pending_approvals()
                
                embed = discord.Embed(
                    title="✅ Pending Email Approvals",
                    description=f"Emails waiting for approval: {len(pending)}",
                    color=discord.Color.orange()
                )
                
                for i, email in enumerate(pending[:3]):  # Show first 3
                    embed.add_field(
                        name=f"Email {i+1}",
                        value=f"To: {email['to']}\nSubject: {email['subject'][:50]}...",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
            
            elif action == 'create':
                embed = discord.Embed(
                    title="📝 Create Campaign",
                    description="Campaign creation requires strategic consultation with Dean",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Next Steps",
                    value="Message Dean directly: 'Dean, let's create a new campaign for property managers'",
                    inline=False
                )
                await ctx.send(embed=embed)
            
            else:
                embed = discord.Embed(
                    title="💼 Dean - Strategic Sales Director",
                    description="Available Dean commands",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Commands",
                    value="`!gg dean campaigns` - View active campaigns\n`!gg dean approvals` - Pending emails\n`!gg dean create` - Create new campaign",
                    inline=False
                )
                embed.add_field(
                    name="Direct Communication",
                    value="Message with 'Dean' to start strategic conversation",
                    inline=False
                )
                await ctx.send(embed=embed)
        
        @self.command(name='help_gg')
        async def help_command(ctx):
            """Show Grime Guardians bot help."""
            embed = discord.Embed(
                title="🤖 Grime Guardians Bot Commands",
                description="Available commands and features",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Check-in Commands",
                value="🚗 Send arrival emoji or 'arrived'\n🏁 Send finished emoji or 'done'\n🆘 Type 'help' for assistance",
                inline=False
            )
            embed.add_field(
                name="Photo Submission",
                value="📸 Attach photos to any message\nRequired: Kitchen, Bathrooms, Entry, Rooms",
                inline=False
            )
            embed.add_field(
                name="Bot Commands",
                value="`!gg status` - Check contractor status\n`!gg jobs` - View today's jobs\n`!gg dean` - Strategic sales\n`!gg help_gg` - Show this help",
                inline=False
            )
            await ctx.send(embed=embed)
    
    @tasks.loop(minutes=5)
    async def check_missed_checkins(self):
        """Check for missed check-ins and escalate."""
        try:
            # Check for contractors who should have checked in
            # Route to Keith for processing
            agent_message = AgentMessage(
                agent_id=AgentType.KEITH,
                message_type="checkin_monitor",
                content="Periodic check-in monitoring",
                priority=MessagePriority.MEDIUM,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "check_type": "missed_checkins"
                }
            )
            
            await keith.send_message(agent_message)
            
        except Exception as e:
            logger.error(f"Error in check_missed_checkins: {e}")
    
    async def send_long_message(self, channel, content: str, max_length: int = 1900):
        """Send message handling Discord's 2000 character limit."""
        if len(content) <= max_length:
            await channel.send(content)
            return
        
        # Split the message into chunks
        chunks = []
        while content:
            if len(content) <= max_length:
                chunks.append(content)
                break
            
            # Find a good break point (newline or space)
            break_point = max_length
            for i in range(max_length - 100, max_length):
                if i < len(content) and content[i] in ['\n', '. ', '! ', '? ']:
                    break_point = i + 1
                    break
            
            chunks.append(content[:break_point])
            content = content[break_point:].lstrip()
        
        # Send each chunk
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Add continuation indicator
                chunk = f"(continued...)\n{chunk}"
            await channel.send(chunk)
            # Small delay between messages
            await asyncio.sleep(0.5)
    
    @check_missed_checkins.before_loop
    async def before_check_missed_checkins(self):
        """Wait for bot to be ready before starting the loop."""
        await self.wait_until_ready()
    
    async def send_to_channel(self, channel_id: int, content: str = None, embed: discord.Embed = None):
        """Send message to specific channel."""
        try:
            channel = self.get_channel(channel_id)
            if channel:
                if embed:
                    await channel.send(content=content, embed=embed)
                else:
                    await channel.send(content=content)
                return True
            else:
                logger.error(f"Channel {channel_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error sending to channel {channel_id}: {e}")
            return False
    
    async def send_dm(self, user_id: int, content: str = None, embed: discord.Embed = None):
        """Send direct message to user."""
        try:
            user = self.get_user(user_id)
            if user:
                if embed:
                    await user.send(content=content, embed=embed)
                else:
                    await user.send(content=content)
                return True
            else:
                logger.error(f"User {user_id} not found")
                return False
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error sending DM to user {user_id}: {e}")
            return False
    
    async def notify_checkin_required(self, contractor_name: str, job_details: Dict[str, Any]):
        """Notify contractor that check-in is required."""
        embed = discord.Embed(
            title="⏰ Check-in Required",
            description=f"Hi {contractor_name}! Please check in for your upcoming job.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Job Details",
            value=f"**Location:** {job_details.get('address', 'TBD')}\n**Time:** {job_details.get('time', 'TBD')}",
            inline=False
        )
        embed.add_field(
            name="How to Check In",
            value="Send 🚗 emoji or type 'arrived' when you get to the job site",
            inline=False
        )
        
        await self.send_to_channel(self.checkin_channel_id, embed=embed)
    
    async def notify_violation(self, contractor_name: str, violation_type: str, details: str):
        """Notify about contractor violations."""
        embed = discord.Embed(
            title="⚠️ Quality Violation Detected",
            description=f"**Contractor:** {contractor_name}\n**Type:** {violation_type}",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Details",
            value=details,
            inline=False
        )
        embed.add_field(
            name="3-Strike System",
            value="This violation has been logged. Please review quality requirements.",
            inline=False
        )
        
        await self.send_to_channel(self.checkin_channel_id, embed=embed)
    
    async def close(self):
        """Clean shutdown of the bot."""
        logger.info("Shutting down Discord bot")
        await super().close()


# Global bot instance
discord_bot = DiscordBot()


async def start_discord_bot():
    """Start the Discord bot."""
    try:
        logger.info("Starting Discord bot")
        await discord_bot.start(settings.discord_bot_token)
    except Exception as e:
        logger.error(f"Failed to start Discord bot: {e}")
        raise


async def stop_discord_bot():
    """Stop the Discord bot."""
    try:
        logger.info("Stopping Discord bot")
        await discord_bot.close()
    except Exception as e:
        logger.error(f"Error stopping Discord bot: {e}")