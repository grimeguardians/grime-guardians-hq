"""
Dean — CMO Discord Bot
Handles sales channel posting, approval interactions, and @mention/DM chat.
Runs concurrently alongside Ava's bot in run_bot.py.
"""

import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class DeanBot(commands.Bot):
    """
    Dean's Discord bot — posts to #sales-comms and handles
    approve/amend/deny interactions for lead and sales messages.
    Also responds to @mentions and DMs using the OpenAI Assistants API.
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!dean ", intents=intents)

        # Lazy-loaded Dean assistant (avoids import at startup)
        self._dean = None

    def _get_dean(self):
        if self._dean is None:
            from ..agents.dean_assistant import get_dean
            self._dean = get_dean()
        return self._dean

    async def on_ready(self):
        logger.info(f"Dean bot {self.user} connected to Discord.")
        for guild in self.guilds:
            logger.info(f"Dean active in guild: {guild.name}")

    async def on_message(self, message: discord.Message):
        """Route messages to Dean when mentioned or in DMs."""
        # Never respond to ourselves or other bots
        if message.author.bot:
            return

        await self.process_commands(message)

        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)

        if not (is_mentioned or is_dm):
            return

        # Strip the mention from content
        content = message.content
        if self.user.mention in content:
            content = content.replace(self.user.mention, "").strip()
        if not content:
            return

        channel_id = str(message.channel.id)
        username = message.author.display_name

        async with message.channel.typing():
            try:
                dean = self._get_dean()
                response = await dean.chat(content, channel_id, username)
            except Exception as e:
                logger.error(f"Dean response error: {e}", exc_info=True)
                response = "Hit an error processing that. Try again or ping Brandon directly."

        if len(response) <= 2000:
            await message.reply(response)
        else:
            for i in range(0, len(response), 1900):
                await message.channel.send(response[i:i + 1900])

    async def on_error(self, event, *args, **kwargs):
        logger.error(f"Dean bot error in {event}", exc_info=True)
