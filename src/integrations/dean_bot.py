"""
Dean — CMO Discord Bot
Handles sales channel posting and approval interactions.
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
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        logger.info(f"Dean bot {self.user} connected to Discord.")
        for guild in self.guilds:
            logger.info(f"Dean active in guild: {guild.name}")

    async def on_error(self, event, *args, **kwargs):
        logger.error(f"Dean bot error in {event}", exc_info=True)
