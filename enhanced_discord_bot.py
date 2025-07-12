import asyncio
import re
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
import discord
from discord.ext import commands, tasks
import structlog
import aiohttp

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import settings
from src.models.schemas import AgentType, AgentMessage, MessagePriority, CheckInEvent
from src.agents import ava, keith, sophia, maya
from src.core.ava_conversation import ava_conversation
from src.core.dean_conversation import dean_conversation

logger = structlog.get_logger()


class EnhancedDiscordBot(commands.Bot):
    """
    Enhanced Grime Guardians Discord Bot with real GoHighLevel integration.
    
    Handles contractor check-ins, photo submissions, status updates,
    and provides real-time CRM data access for both Ava and Dean.
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
        
        # Use Ava-specific token if available
        self.token = settings.discord_bot_token_ava or settings.discord_bot_token
        
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
        
        # GoHighLevel integration
        self.ghl_base_url = "https://services.leadconnectorhq.com"
        self.location_id = settings.highlevel_location_id
        self.api_key = settings.highlevel_api_key
        self.oauth_token = settings.highlevel_oauth_access_token
        
        # Add commands
        self.setup_commands()
    
    async def get_ghl_appointments(self, target_date=None):
        """Get appointments from GoHighLevel for specific date."""
        try:
            from src.integrations.gohighlevel_service import ghl_service
            
            if target_date:
                # Get appointments for specific date
                start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                appointments = await ghl_service.get_appointments(start_date, end_date)
            else:
                # Get today's appointments
                appointments = await ghl_service.get_todays_schedule()
            
            # Convert to dict format for compatibility
            appointment_dicts = []
            for apt in appointments:
                apt_dict = {
                    'id': apt.id,
                    'title': apt.title,
                    'startTime': apt.start_time.isoformat(),
                    'endTime': apt.end_time.isoformat(),
                    'contact': {
                        'name': apt.contact_name,
                        'phone': apt.contact_phone,
                        'email': apt.contact_email
                    },
                    'address': apt.address,
                    'status': apt.status,
                    'notes': apt.notes,
                    'assignedUser': apt.assigned_user
                }
                appointment_dicts.append(apt_dict)
            
            return appointment_dicts
            
        except Exception as e:
            logger.error(f"Error getting GoHighLevel appointments: {e}")
            return []
    
    async def get_ghl_conversations(self, limit=20):
        """Get recent conversations from GoHighLevel."""
        try:
            from src.integrations.gohighlevel_service import ghl_service
            
            conversations = await ghl_service.get_conversations(limit)
            
            # Convert to dict format for compatibility
            conv_dicts = []
            for conv in conversations:
                conv_dict = {
                    'id': conv.id,
                    'contactName': conv.contact_name,
                    'type': conv.type,
                    'status': conv.status,
                    'lastMessage': conv.last_message,
                    'lastMessageTime': conv.last_message_time.isoformat(),
                    'unreadCount': conv.unread_count,
                    'assignedUser': conv.assigned_user,
                    'contact': {
                        'name': conv.contact_name
                    }
                }
                conv_dicts.append(conv_dict)
            
            return conv_dicts
            
        except Exception as e:
            logger.error(f"Error getting GoHighLevel conversations: {e}")
            return []
    
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
            dean_keywords = ['dean', 'sales', 'marketing', 'lead', 'campaign', 'revenue', 'email', 'outreach', 'prospect', 'conversion', 'funnel']
            if any(keyword in content for keyword in dean_keywords):
                await self.handle_dean_conversation(message)
            else:
                await self.handle_ava_conversation(message)
            return
        
        # Process commands
        await self.process_commands(message)
    
    async def handle_ava_conversation(self, message):
        """Handle conversations with Ava, including real GoHighLevel data."""
        try:
            user_id = str(message.author.id)
            username = message.author.display_name
            user_message = message.content
            
            # Determine if it's a DM or channel
            channel_id = None if isinstance(message.channel, discord.DMChannel) else str(message.channel.id)
            
            logger.info(f"💬 Ava conversation from {username}: {user_message[:50]}...")
            
            # Use Ava's intelligent response system with enhanced date parsing
            try:
                from ava_intelligence_upgrade import ava_intelligence
                
                # Check if user is asking about schedule with intelligent date parsing
                schedule_keywords = ['schedule', 'appointment', 'calendar', 'today', 'jobs', 'cleaning', 'client', 'who', 'when', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                asking_about_schedule = any(keyword in user_message.lower() for keyword in schedule_keywords)
                
                if asking_about_schedule:
                    response = await ava_intelligence.handle_schedule_question(user_message)
                    await self.send_long_message(message.channel, response)
                    return
                
                # Check if asking about conversations/messages
                conversation_keywords = ['message', 'text', 'conversation', 'chat', 'contact', 'last message', 'who messaged']
                asking_about_conversations = any(keyword in user_message.lower() for keyword in conversation_keywords)
                
                if asking_about_conversations:
                    response = await ava_intelligence.handle_conversation_question(user_message)
                    await self.send_long_message(message.channel, response)
                    return
                
                # Check if asking about analytics/leads
                analytics_keywords = ['analytics', 'leads', 'performance', 'metrics', 'stats']
                asking_about_analytics = any(keyword in user_message.lower() for keyword in analytics_keywords)
                
                if asking_about_analytics:
                    response = await ava_intelligence.handle_analytics_question(user_message)
                    await self.send_long_message(message.channel, response)
                    return
                    
            except ImportError:
                logger.warning("Ava intelligence upgrade not available, using fallback")
                # Fallback to basic schedule check
                appointments = await self.get_ghl_appointments()
                if appointments:
                    await message.channel.send(f"📅 Found {len(appointments)} appointments today.")
                else:
                    await message.channel.send("No appointments found for today.")
                return
            
            # For non-schedule questions, use regular Ava conversation
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
            
            # Send response back to Discord
            await self.send_long_message(message.channel, response)
            
            logger.info(f"✅ Sent Ava response to {username}")
            
        except Exception as e:
            logger.error(f"❌ Error handling Ava conversation: {e}")
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
            
            # Check if user is asking about sales data/analytics
            analytics_keywords = ['analytics', 'leads', 'conversations', 'pipeline', 'performance', 'sales data']
            asking_about_analytics = any(keyword in user_message.lower() for keyword in analytics_keywords)
            
            # Check if asking about commercial calendar specifically
            commercial_keywords = ['commercial', 'walkthrough', 'commercial pipeline', 'commercial calendar']
            asking_about_commercial = any(keyword in user_message.lower() for keyword in commercial_keywords)
            
            if asking_about_commercial:
                # Dean's commercial calendar intelligence
                try:
                    from dean_calendar_intelligence import dean_commercial_intelligence
                    
                    report = await dean_commercial_intelligence.generate_commercial_report()
                    await self.send_long_message(message.channel, report)
                    return
                except ImportError:
                    logger.warning("Dean commercial intelligence not available")
                except Exception as e:
                    logger.error(f"Error generating commercial report: {e}")
            
            if asking_about_analytics:
                # Get real GoHighLevel conversation data
                conversations = await self.get_ghl_conversations()
                appointments = await self.get_ghl_appointments()
                
                analytics_response = f"📊 **SALES INTELLIGENCE** (Real-time from GoHighLevel):\n\n"
                
                # Active conversations
                active_convs = [c for c in conversations if c.get('unreadCount', 0) > 0]
                analytics_response += f"💬 **Active Conversations:** {len(active_convs)}\n"
                analytics_response += f"📞 **Total Conversations:** {len(conversations)}\n"
                analytics_response += f"📅 **Scheduled Today:** {len(appointments)}\n\n"
                
                if active_convs:
                    analytics_response += "**🔥 Urgent Conversations:**\n"
                    for conv in active_convs[:3]:  # Show top 3
                        contact = conv.get('contact', {})
                        name = contact.get('name', 'Unknown')
                        unread = conv.get('unreadCount', 0)
                        analytics_response += f"• {name} ({unread} unread messages)\n"
                
                # Send the real analytics data  
                await self.send_long_message(message.channel, analytics_response)
                return
            
            # For non-analytics questions, use regular Dean conversation
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
            
            # Send response back to Discord
            await self.send_long_message(message.channel, response)
            
            logger.info(f"✅ Sent Dean response to {username}")
            
        except Exception as e:
            logger.error(f"❌ Error handling Dean conversation: {e}")
            await message.channel.send(
                "Strategic systems temporarily offline. Critical sales decisions pending your input."
            )
    
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
    
    def setup_commands(self):
        """Setup bot commands."""
        
        @self.command(name='test_ghl')
        async def test_ghl_command(ctx):
            """Test GoHighLevel integration."""
            try:
                appointments = await self.get_ghl_appointments()
                conversations = await self.get_ghl_conversations(5)
                
                embed = discord.Embed(
                    title="🧪 GoHighLevel Integration Test",
                    description="Live API connection test results",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📅 Appointments Today",
                    value=f"{len(appointments)} appointments found",
                    inline=True
                )
                
                embed.add_field(
                    name="💬 Recent Conversations",
                    value=f"{len(conversations)} conversations retrieved",
                    inline=True
                )
                
                embed.add_field(
                    name="✅ Status",
                    value="GoHighLevel integration working!",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ GoHighLevel Test Failed",
                    description=f"Error: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        
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
        
        @self.command(name='schedule')
        async def schedule_command(ctx):
            """Show today's schedule from GoHighLevel."""
            try:
                appointments = await self.get_ghl_appointments()
                
                if appointments:
                    embed = discord.Embed(
                        title="📅 Today's Schedule",
                        description=f"{len(appointments)} appointments scheduled",
                        color=discord.Color.green()
                    )
                    
                    for i, apt in enumerate(appointments[:5], 1):  # Show first 5
                        contact = apt.get('contact', {})
                        start_time = apt.get('startTime', '')
                        if start_time:
                            try:
                                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                time_str = dt.strftime('%I:%M %p')
                            except:
                                time_str = start_time
                        else:
                            time_str = "Time TBD"
                        
                        client_name = contact.get('name', 'Unknown Client')
                        title = apt.get('title', 'Cleaning Service')
                        
                        embed.add_field(
                            name=f"{i}. {time_str}",
                            value=f"**{client_name}**\n{title}",
                            inline=True
                        )
                    
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="📅 Today's Schedule",
                        description="No appointments scheduled for today",
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                    
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Schedule Error",
                    description=f"Could not retrieve schedule: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        
        @self.command(name='social_calendar')
        async def social_calendar_command(ctx, weeks: int = 2):
            """Generate social media content calendar using Hormozi methodology."""
            try:
                from src.core.social_media_agent import social_media_agent
                
                # Create content calendar
                calendar = await social_media_agent.create_content_calendar(weeks)
                
                embed = discord.Embed(
                    title="📅 Social Media Content Calendar",
                    description=f"Hormozi 'Give Give Give Ask' methodology - {weeks} weeks",
                    color=discord.Color.purple()
                )
                
                # Calendar summary
                give_posts = len([p for p in calendar.posts if p.content_type == 'give'])
                ask_posts = len([p for p in calendar.posts if p.content_type == 'ask'])
                
                embed.add_field(
                    name="📊 Content Overview",
                    value=f"**Total Posts:** {len(calendar.posts)}\n**Give Content:** {give_posts}\n**Ask Content:** {ask_posts}\n**Ratio:** {give_posts}:{ask_posts}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Platforms",
                    value="\n".join(calendar.platforms_active),
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Themes",
                    value="\n".join(calendar.content_themes[:3]) + "...",
                    inline=True
                )
                
                # Show first few posts
                upcoming_posts = sorted(calendar.posts, key=lambda x: x.scheduled_time)[:5]
                posts_preview = ""
                
                for post in upcoming_posts:
                    time_str = post.scheduled_time.strftime('%m/%d %I:%M%p')
                    posts_preview += f"**{time_str}** - {post.platform.title()} ({post.content_type})\n"
                    posts_preview += f"   {post.title[:50]}{'...' if len(post.title) > 50 else ''}\n\n"
                
                embed.add_field(
                    name="🔄 Upcoming Posts",
                    value=posts_preview,
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Social Media Calendar Error",
                    description=f"Could not generate calendar: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        
        @self.command(name='social_test')
        async def social_test_command(ctx):
            """Test social media agent functionality."""
            try:
                from src.core.social_media_agent import social_media_agent
                
                # Test content generation
                test_post = {
                    'content_type': 'give',
                    'category': 'cleaning_tips',
                    'platform': 'facebook'
                }
                
                ab_test = await social_media_agent.create_ab_test(test_post, ['hook_style'])
                
                embed = discord.Embed(
                    title="🧪 Social Media Agent Test",
                    description="A/B test content generation",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🅰️ Variant A",
                    value=f"**{ab_test.variant_a.title}**\n{ab_test.variant_a.content[:150]}...",
                    inline=False
                )
                
                embed.add_field(
                    name="🅱️ Variant B", 
                    value=f"**{ab_test.variant_b.title}**\n{ab_test.variant_b.content[:150]}...",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Test Status",
                    value=f"Test ID: {ab_test.test_id}\nStatus: {ab_test.winner}\nRecommendation: {ab_test.recommendation}",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Social Media Test Failed",
                    description=f"Error: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        
        @self.command(name='hormozi_status')
        async def hormozi_status_command(ctx):
            """Check Give Give Give Ask methodology compliance."""
            try:
                from src.core.social_media_agent import social_media_agent
                
                status = social_media_agent.get_give_give_give_ask_status()
                calendar_summary = social_media_agent.get_content_calendar_summary()
                
                embed = discord.Embed(
                    title="🎯 Hormozi Methodology Status", 
                    description="Give Give Give Ask compliance tracking",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="Current Status",
                    value=status,
                    inline=False
                )
                
                embed.add_field(
                    name="Content Calendar",
                    value=calendar_summary,
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Status Check Failed",
                    description=f"Error: {str(e)}",
                    color=discord.Color.red()
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
                name="Schedule Commands",
                value="`!gg schedule` - View today's appointments\n`!gg test_ghl` - Test GoHighLevel connection",
                inline=False
            )
            embed.add_field(
                name="Social Media Commands",
                value="`!gg social_calendar` - Generate content calendar\n`!gg social_test` - Test A/B content\n`!gg hormozi_status` - Check Give Give Give Ask status",
                inline=False
            )
            embed.add_field(
                name="Natural Language",
                value="Ask Ava: 'What's on the schedule today?'\nAsk Dean: 'Show me sales analytics'",
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
            await chunk.send(chunk)
            # Small delay between messages
            await asyncio.sleep(0.5)
    
    @check_missed_checkins.before_loop
    async def before_check_missed_checkins(self):
        """Wait for bot to be ready before starting the loop."""
        await self.wait_until_ready()
    
    async def close(self):
        """Clean shutdown of the bot."""
        logger.info("Shutting down Discord bot")
        await super().close()


# Global bot instance
enhanced_discord_bot = EnhancedDiscordBot()

async def start_enhanced_bot():
    """Start the enhanced Discord bot with Ava's token."""
    try:
        logger.info("Starting Enhanced Discord Bot (Ava)")
        await enhanced_discord_bot.start(enhanced_discord_bot.token)
    except Exception as e:
        logger.error(f"Failed to start Enhanced Discord Bot: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_enhanced_bot())