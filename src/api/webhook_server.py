"""
GHL Webhook Server
Receives inbound events from GoHighLevel workflows, routes to the correct agent,
posts a drafted response to Discord for Brandon's approval.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

app = FastAPI(title="Grime Guardians Webhook Server")

# Set after Discord bot is ready — see run_bot.py
_router = None


def set_router(router):
    """Called by run_bot.py once the Discord bot is ready."""
    global _router
    _router = router


@app.post("/webhook/ghl")
async def ghl_webhook(request: Request):
    """
    Receives inbound message webhooks from GHL workflows.
    Returns 200 immediately; processing happens in background.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info(f"GHL webhook received: {list(payload.keys())}")

    if _router is None:
        logger.warning("Router not ready yet — webhook received but not processed.")
        return JSONResponse({"status": "not_ready"}, status_code=503)

    # Fire and forget — don't make GHL wait for Discord/OpenAI
    asyncio.create_task(_router.handle(payload))

    return JSONResponse({"status": "received"})


@app.get("/health")
async def health():
    return {"status": "ok", "router_ready": _router is not None}
