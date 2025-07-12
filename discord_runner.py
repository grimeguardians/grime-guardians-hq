#!/usr/bin/env python3
"""
Standalone Discord bot runner for Grime Guardians.
This runs as a separate service to avoid duplicate responses from multiple workers.
"""

import asyncio
import sys
import os
import structlog

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.integrations.discord_bot import start_discord_bot
from src.config.settings import settings

logger = structlog.get_logger()


async def main():
    """Main function to run the Discord bot."""
    try:
        logger.info("Starting standalone Discord bot service")
        await start_discord_bot()
    except KeyboardInterrupt:
        logger.info("Discord bot service interrupted")
    except Exception as e:
        logger.error(f"Discord bot service error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())