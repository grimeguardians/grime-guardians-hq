"""
Grime Guardians — Bot + Webhook Server Runner
Runs the Discord bot and FastAPI webhook server concurrently in one process.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import uvicorn

from src.config.settings import get_settings
from src.integrations.discord_integration import GrimeGuardiansBot
from src.api.webhook_server import app as webhook_app, set_router
from src.core.inbound_router import InboundRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        *(
            [logging.FileHandler("logs/bot.log")]
            if Path("logs").exists()
            else []
        ),
    ],
)
logger = logging.getLogger(__name__)


async def run_webhook_server(port: int = 8000):
    """Run the FastAPI webhook server."""
    config = uvicorn.Config(
        app=webhook_app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    logger.info(f"Webhook server listening on 0.0.0.0:{port}")
    await server.serve()


async def main():
    settings = get_settings()

    if not settings.discord_bot_token:
        logger.error("DISCORD_BOT_TOKEN not set — cannot start.")
        sys.exit(1)

    logger.info(f"Starting Grime Guardians | model: {settings.openai_model} | env: {settings.environment}")

    # Create bot and wire the inbound router before starting
    # (channels populate on on_ready; router posts after that point)
    bot = GrimeGuardiansBot()
    router = InboundRouter(bot=bot)
    set_router(router)
    logger.info("Inbound router wired to bot.")

    try:
        await asyncio.gather(
            bot.start(settings.discord_bot_token),
            run_webhook_server(port=8000),
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
