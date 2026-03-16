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
from src.integrations.dean_bot import DeanBot
from src.api.webhook_server import app as webhook_app, set_router
from src.core.inbound_router import InboundRouter
from src.core.email_cron import run_email_cron

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

    # Ava — COO bot (ops-comms, slash commands, GHL tools)
    ava_bot = GrimeGuardiansBot()

    # Dean — CMO bot (sales-comms), optional if token not set
    dean_bot = DeanBot() if settings.discord_dean_bot_token else None
    if not dean_bot:
        logger.warning("DISCORD_DEAN_BOT_TOKEN not set — Dean bot will not start. Sales posts will use Ava.")

    router = InboundRouter(ava_bot=ava_bot, dean_bot=dean_bot)
    set_router(router)
    logger.info(f"Inbound router wired. Ava: ✅  Dean: {'✅' if dean_bot else '⚠️ offline'}")

    # Email cron — only starts if at least one Gmail account is configured
    email_enabled = bool(settings.gmail_account_1_email and settings.gmail_account_1_refresh_token)
    logger.info(f"Email cron: {'✅ enabled' if email_enabled else '⚠️ disabled (no GMAIL_ACCOUNT_1 configured)'}")

    tasks = [
        ava_bot.start(settings.discord_bot_token),
        run_webhook_server(port=8000),
    ]
    if dean_bot:
        tasks.append(dean_bot.start(settings.discord_dean_bot_token))
    if email_enabled:
        tasks.append(run_email_cron())

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await ava_bot.close()
        if dean_bot:
            await dean_bot.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
