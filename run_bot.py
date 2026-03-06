"""
Grime Guardians — Discord Bot Runner
Entry point for Ava and the full agent suite on Discord.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.config.settings import get_settings
from src.integrations.discord_integration import DiscordIntegration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log") if Path("logs").exists() else logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()

    if not settings.discord_bot_token:
        logger.error("DISCORD_BOT_TOKEN is not set in .env — cannot start bot.")
        sys.exit(1)

    logger.info("Starting Grime Guardians Discord bot...")
    logger.info(f"Model: {settings.openai_model}")
    logger.info(f"Environment: {settings.environment}")

    integration = DiscordIntegration()

    try:
        await integration.start_bot()
    except KeyboardInterrupt:
        logger.info("Shutting down bot...")
        await integration.stop_bot()
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
