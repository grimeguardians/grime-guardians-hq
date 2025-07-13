#!/usr/bin/env python3
"""
Ava Intelligent Discord Bot
Uses OpenAI Assistant API for natural conversation and comprehensive GoHighLevel integration
"""

import asyncio
import discord
from discord.ext import commands
import structlog
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.config.settings import settings
from src.agents.ava_assistant import ava_assistant
from src.agents.ava_operations_monitor import AvaOperationsMonitor

logger = structlog.get_logger()


class AvaIntelligentBot(commands.Bot):
    """
    Intelligent Discord Bot powered by OpenAI Assistant API.
    
    Features:
    - Natural conversation with GPT-4
    - Comprehensive GoHighLevel data access
    - Learning from corrections
    - Persistent conversation memory
    - Dynamic function calling for real-time data
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!ava ',
            intents=intents,
            description="Ava - Intelligent Grime Guardians Operations Assistant"
        )
        
        self.token = settings.discord_bot_token_ava or settings.discord_bot_token
        self.checkin_channel_id = int(settings.discord_checkin_channel_id)
        self.ops_lead_id = int(settings.discord_ops_lead_id)
        
        # Conversation tracking
        self.user_threads = {}  # Track thread IDs per user
        
        # Operations monitoring system
        self.operations_monitor = AvaOperationsMonitor(self)
        
    async def on_ready(self):
        """Bot startup complete."""
        logger.info(f"Ava Intelligent Bot connected as {self.user}")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Initialize the assistant
        try:
            await ava_assistant._initialize_assistant()
            logger.info("Ava Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ava Assistant: {e}")
        
        # Start operations monitoring
        try:
            await self.operations_monitor.start_monitoring()
            logger.info("🔥 Ava Operations Monitoring started")
        except Exception as e:
            logger.error(f"Failed to start operations monitoring: {e}")
    
    async def on_message(self, message):
        """Handle all incoming messages."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check for check-in messages first (priority)
        username = message.author.display_name
        if await self.operations_monitor.handle_checkin_message(message, username):
            return  # Check-in handled, don't process as conversation
        
        # Handle direct mentions or DMs
        if (isinstance(message.channel, discord.DMChannel) or 
            self.user in message.mentions or
            message.channel.id == self.checkin_channel_id):
            
            await self.handle_conversation(message)
            return
        
        # Process commands
        await self.process_commands(message)
    
    async def handle_conversation(self, message):
        """Handle intelligent conversation with Ava."""
        try:
            user_id = str(message.author.id)
            username = message.author.display_name
            user_message = message.content
            
            # Remove bot mention from message
            if self.user in message.mentions:
                user_message = user_message.replace(f'<@{self.user.id}>', '').strip()
            
            logger.info(f"💬 Conversation from {username}: {user_message[:100]}...")
            
            # Show typing indicator
            async with message.channel.typing():
                # Get or create conversation thread for this user
                if user_id not in self.user_threads:
                    thread_id = await ava_assistant.create_conversation_thread()
                    self.user_threads[user_id] = thread_id
                    logger.info(f"Created new thread for user {username}: {thread_id}")
                else:
                    # Set the thread for this conversation
                    ava_assistant.thread_id = self.user_threads[user_id]
                
                # Get response from Ava Assistant
                response = await ava_assistant.send_message(user_message, user_id)
                
                # Send response, handling Discord's message length limits
                await self.send_long_message(message.channel, response)
                
        except Exception as e:
            logger.error(f"Error in conversation handling: {e}")
            await message.channel.send("I apologize, but I encountered an issue. Please try again in a moment.")
    
    async def send_long_message(self, channel, content: str, max_length: int = 2000):
        """Send long messages by splitting them if necessary."""
        try:
            if len(content) <= max_length:
                await channel.send(content)
                return
            
            # Split by paragraphs first
            paragraphs = content.split('\n\n')
            current_message = ""
            
            for paragraph in paragraphs:
                if len(current_message + paragraph + '\n\n') <= max_length:
                    current_message += paragraph + '\n\n'
                else:
                    if current_message:
                        await channel.send(current_message.strip())
                        current_message = paragraph + '\n\n'
                    else:
                        # Single paragraph too long, split by lines
                        lines = paragraph.split('\n')
                        for line in lines:
                            if len(current_message + line + '\n') <= max_length:
                                current_message += line + '\n'
                            else:
                                if current_message:
                                    await channel.send(current_message.strip())
                                current_message = line + '\n'
            
            if current_message:
                await channel.send(current_message.strip())
                
        except Exception as e:
            logger.error(f"Error sending long message: {e}")
            await channel.send("I have a response for you, but encountered an issue sending it. Please try again.")
    
    @commands.command(name='reset')
    async def reset_conversation(self, ctx):
        """Reset conversation thread for the user."""
        try:
            user_id = str(ctx.author.id)
            
            # Create new thread
            thread_id = await ava_assistant.create_conversation_thread()
            self.user_threads[user_id] = thread_id
            
            await ctx.send("🔄 Conversation reset! I'm ready for a fresh start.")
            logger.info(f"Reset conversation for user {ctx.author.display_name}")
            
        except Exception as e:
            logger.error(f"Error resetting conversation: {e}")
            await ctx.send("Sorry, I couldn't reset the conversation. Please try again.")
    
    @commands.command(name='status')
    async def bot_status(self, ctx):
        """Check bot and assistant status."""
        try:
            # Check assistant status
            assistant_status = "✅ Ready" if ava_assistant.assistant_id else "❌ Not initialized"
            
            # Check GoHighLevel connection
            try:
                from src.integrations.gohighlevel_service import ghl_service
                test_result = await ghl_service.test_connection()
                ghl_status = "✅ Connected" if test_result.get("status") == "success" else "❌ Connection issues"
            except Exception:
                ghl_status = "❌ Connection failed"
            
            # Check user thread
            user_id = str(ctx.author.id)
            thread_status = "✅ Active" if user_id in self.user_threads else "🆕 Will create on first message"
            
            # Check operations monitoring
            ops_status = self.operations_monitor.get_monitoring_status()
            monitoring_status = "✅ Active" if ops_status["monitoring_active"] else "❌ Inactive"
            
            status_message = f"""
🤖 **Ava Intelligent Assistant Status**

**OpenAI Assistant**: {assistant_status}
**GoHighLevel**: {ghl_status}
**Operations Monitoring**: {monitoring_status}
**Your Conversation**: {thread_status}
**Active Threads**: {len(self.user_threads)}

**📊 Operations Overview:**
• Total Appointments: {ops_status["total_appointments"]}
• Checked In: {ops_status["checked_in"]}
• Overdue: {ops_status["overdue"]}
• Upcoming: {ops_status["upcoming"]}

Type any message to start a conversation!
"""
            
            await ctx.send(status_message.strip())
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            await ctx.send("Error checking status.")
    
    @commands.command(name='monitor')
    async def monitor_operations(self, ctx):
        """Show detailed operations monitoring status."""
        try:
            ops_status = self.operations_monitor.get_monitoring_status()
            
            if not ops_status["monitoring_active"]:
                await ctx.send("⚠️ Operations monitoring is not active.")
                return
            
            # Get detailed appointment status
            status_details = []
            now = datetime.now()
            
            for apt in self.operations_monitor.monitored_appointments.values():
                time_to_client = (apt.client_time - now).total_seconds() / 60
                
                if apt.status.value == "checked_in":
                    status_emoji = "✅"
                elif apt.status.value == "overdue":
                    status_emoji = "🚨"
                elif time_to_client < 30:  # Within 30 minutes
                    status_emoji = "⏰"
                else:
                    status_emoji = "📅"
                
                status_details.append(
                    f"{status_emoji} **{apt.contact_name}** ({apt.cleaner_assigned})\n"
                    f"   Client: {apt.client_time.strftime('%I:%M %p')} | "
                    f"Status: {apt.status.value.replace('_', ' ').title()}"
                )
            
            monitor_message = f"""
🔥 **Operations Monitoring Dashboard**

**Summary:**
• Monitoring: {"✅ Active" if ops_status["monitoring_active"] else "❌ Inactive"}
• Total Appointments: {ops_status["total_appointments"]}
• Checked In: {ops_status["checked_in"]}
• Overdue Check-ins: {ops_status["overdue"]}
• Upcoming: {ops_status["upcoming"]}

**Today's Appointments:**
{chr(10).join(status_details[:10]) if status_details else "No appointments today"}

Legend: ✅ Checked In | 🚨 Overdue | ⏰ Due Soon | 📅 Scheduled
"""
            
            await self.send_long_message(ctx.channel, monitor_message.strip())
            
        except Exception as e:
            logger.error(f"Error checking monitor status: {e}")
            await ctx.send("Error checking operations monitor.")
    
    async def close(self):
        """Clean shutdown."""
        logger.info("Shutting down Ava Intelligent Bot")
        await super().close()


async def main():
    """Run the Ava Intelligent Discord Bot."""
    try:
        bot = AvaIntelligentBot()
        
        logger.info("Starting Ava Intelligent Discord Bot...")
        await bot.start(bot.token)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise
    finally:
        if 'bot' in locals():
            await bot.close()


if __name__ == "__main__":
    # Configure logging
    import structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)