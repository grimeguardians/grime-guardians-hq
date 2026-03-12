"""
Inbound Message Router
Classifies GHL inbound messages, drafts a response via the correct agent persona,
then posts to Discord for Brandon's approval.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

import openai
import discord

from ..config.settings import get_settings
from ..integrations.gohighlevel_integration import GoHighLevelIntegration

logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Routing Table ────────────────────────────────────────────────────────────
# Maps message category keywords → agent persona + Discord channel key

ROUTE_MAP = {
    # New leads, pricing questions, quotes → #sales-comms (Dean's lane)
    "lead": {
        "agent": "Dean (CMO)",
        "emoji": "🎯",
        "channel_id": 1481528969055440940,  # #sales-comms
        "color": discord.Color.blue(),
    },
    # Existing client ops, scheduling, check-ins → #ops-comms (Ava's lane)
    "ops": {
        "agent": "Ava (COO)",
        "emoji": "📋",
        "channel_id": 1481493060667052062,  # #ops-comms
        "color": discord.Color.green(),
    },
    # Complaints, dissatisfied clients, escalations → #🚨-alerts
    "complaint": {
        "agent": "Emma (CXO)",
        "emoji": "🚨",
        "channel_id": 1377516295754350613,  # #🚨-alerts
        "color": discord.Color.red(),
    },
    # Cleaner messages, contractor comms → #ops-comms (Ava's lane)
    "cleaner": {
        "agent": "Ava (COO)",
        "emoji": "🧹",
        "channel_id": 1481493060667052062,  # #ops-comms
        "color": discord.Color.orange(),
    },
}

# Keywords for fast classification (before hitting OpenAI)
KEYWORD_ROUTES = {
    "lead": [
        "price", "pricing", "quote", "how much", "cost", "rate", "rates",
        "interested", "looking for", "do you clean", "do you offer",
        "availability", "available", "book", "booking", "schedule a",
        "move out", "move-out", "deep clean", "first time",
    ],
    "complaint": [
        "unhappy", "not happy", "disappointed", "terrible", "awful",
        "refund", "money back", "never again", "worst", "complaint",
        "didn't clean", "missed", "poor job", "bad job", "unacceptable",
        "disgusting", "furious", "angry", "upset with",
    ],
    "cleaner": [
        "can't make it", "cant make it", "running late", "called out",
        "calling out", "sick", "not feeling well", "emergency",
        "car trouble", "won't be able", "can i switch", "swap",
    ],
}


class InboundRouter:
    """
    Routes inbound GHL messages to the correct agent and posts
    a drafted response to Discord for approval.
    """

    def __init__(self, ava_bot: discord.ext.commands.Bot, dean_bot=None):
        self.ava_bot = ava_bot
        self.dean_bot = dean_bot
        # Legacy alias so nothing else breaks
        self.bot = ava_bot
        self.openai = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def handle(self, payload: Dict[str, Any]):
        """
        Main entry point. Parse payload → fetch missing data → classify → draft → post to Discord.
        """
        try:
            msg = self._parse_payload(payload)
            if not msg:
                # No body in payload — try fetching latest message from GHL via contact ID
                contact_id = (
                    payload.get("contactId") or
                    payload.get("contact_id") or
                    (payload.get("contact") or {}).get("id", "")
                )
                if contact_id:
                    msg = await self._fetch_latest_message(contact_id, payload)
                if not msg:
                    logger.warning(f"Could not extract message from webhook payload: {list(payload.keys())}")
                    return

            logger.info(f"Inbound from {msg['contact_name']} ({msg['msg_type']}): {msg['body'][:80]}")

            route = self._classify(msg["body"])
            draft = await self._draft_response(msg, route)
            await self._post_to_discord(msg, draft, route)

        except Exception as e:
            logger.error(f"InboundRouter.handle error: {e}", exc_info=True)

    async def _fetch_latest_message(
        self, contact_id: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        When the webhook body contains no message text, fetch the latest
        inbound message for this contact directly from GHL.
        GHL fires the webhook before the conversation is fully created,
        so retry a few times with a short delay.
        """
        import asyncio
        try:
            async with GoHighLevelIntegration() as ghl:
                conversations = []
                for attempt in range(4):  # try up to 4x over ~6 seconds
                    if attempt > 0:
                        await asyncio.sleep(2)
                    resp = await ghl._request(
                        "GET",
                        "/conversations/search",
                        params={"contactId": contact_id, "limit": 1},
                    )
                    conversations = resp.get("conversations", [])
                    if conversations:
                        break
                    logger.info(f"Conversation not ready yet for {contact_id}, retrying... (attempt {attempt + 1})")

                if not conversations:
                    logger.warning(f"No conversations found for contact {contact_id}")
                    return None

                conv = conversations[0]
                conversation_id = conv.get("id", "")

                # Fetch messages in that conversation
                msgs_resp = await ghl._request(
                    "GET",
                    f"/conversations/{conversation_id}/messages",
                    params={"limit": 5},
                )
                messages = msgs_resp.get("messages", {}).get("messages", [])

                # Find the most recent inbound message
                inbound = [
                    m for m in messages
                    if m.get("direction", "").lower() == "inbound"
                ]
                if not inbound:
                    logger.warning(f"No inbound messages in conversation {conversation_id}")
                    return None

                latest = inbound[0]
                body = (latest.get("body") or latest.get("text", "")).strip()
                if not body:
                    return None

                # Build contact name from payload fields
                contact_name = (
                    f"{payload.get('firstName', '')} {payload.get('lastName', '')}".strip()
                    or payload.get("phone", "")
                    or "Unknown"
                )

                return {
                    "contact_name": contact_name,
                    "contact_phone": payload.get("phone", ""),
                    "contact_email": payload.get("email", ""),
                    "contact_id": contact_id,
                    "conversation_id": conversation_id,
                    "body": body,
                    "msg_type": str(latest.get("type", "SMS")).upper(),
                    "received_at": datetime.now(),
                }
        except Exception as e:
            logger.error(f"_fetch_latest_message error: {e}", exc_info=True)
            return None

    # ─── Payload Parsing ──────────────────────────────────────────────────────

    def _parse_payload(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse GHL webhook payload into a normalized message dict.
        Handles both native location webhooks (InboundMessage event) and
        workflow webhook shapes.
        """
        # GHL native webhook wraps data under a top-level event key
        # e.g. {"type": "InboundMessage", "message": {...}, "contact": {...}}
        # Normalize nested message/contact objects if present
        nested_msg = payload.get("message", {}) if isinstance(payload.get("message"), dict) else {}
        contact = payload.get("contact", payload.get("Contact", {}))
        if isinstance(contact, str):
            contact = {}

        contact_name = (
            contact.get("name") or
            contact.get("fullName") or
            contact.get("full_name") or
            f"{payload.get('firstName', '') or contact.get('firstName', '')} "
            f"{payload.get('lastName', '') or contact.get('lastName', '')}".strip() or
            payload.get("contact_name", "Unknown")
        )

        contact_phone = (
            contact.get("phone") or
            payload.get("phone") or
            payload.get("Phone", "")
        )

        contact_email = (
            contact.get("email") or
            payload.get("email") or
            payload.get("Email", "")
        )

        contact_id = (
            contact.get("id") or
            payload.get("contactId") or
            payload.get("contact_id") or
            payload.get("ContactId", "")
        )

        conversation_id = (
            payload.get("conversationId") or
            nested_msg.get("conversationId") or
            payload.get("conversation_id") or
            payload.get("ConversationId", "")
        )

        # Message body — native webhook uses nested message.body; workflow uses top-level fields
        body = (
            nested_msg.get("body") or
            nested_msg.get("text") or
            payload.get("messageBody") or
            payload.get("smsBody") or
            payload.get("body") or
            payload.get("Message") or
            ""
        )
        # Skip if payload.message was a string (workflow shape — already handled above)
        if not body and isinstance(payload.get("message"), str):
            body = payload["message"]
        body = body.strip() if body else ""

        if not body:
            logger.warning("Webhook payload has no message body — skipping.")
            return None

        # Skip outbound messages (direction field present in native webhooks)
        direction = (
            nested_msg.get("direction") or
            payload.get("direction", "")
        ).lower()
        if direction == "outbound":
            logger.info("Skipping outbound message webhook.")
            return None

        msg_type = (
            nested_msg.get("type") or
            payload.get("type") or
            payload.get("messageType") or
            payload.get("channel") or
            "SMS"
        ).upper()

        return {
            "contact_name": contact_name or "Unknown",
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "contact_id": contact_id,
            "conversation_id": conversation_id,
            "body": body,
            "msg_type": msg_type,
            "received_at": datetime.now(),
        }

    # ─── Classification ───────────────────────────────────────────────────────

    def _classify(self, body: str) -> Dict[str, Any]:
        """
        Classify message into a route using fast keyword matching.
        Falls back to 'ops' (Ava) if nothing matches.
        """
        lower = body.lower()

        for category, keywords in KEYWORD_ROUTES.items():
            if any(kw in lower for kw in keywords):
                logger.info(f"Classified as '{category}' via keyword match.")
                return ROUTE_MAP[category]

        # Default to Ava for anything unclassified
        logger.info("No keyword match — defaulting to ops (Ava).")
        return ROUTE_MAP["ops"]

    # ─── Draft Generation ─────────────────────────────────────────────────────

    async def _fetch_conversation_history(self, conversation_id: str, limit: int = 20) -> str:
        """Fetch recent messages from GHL to give the agent full conversation context."""
        if not conversation_id:
            return ""
        try:
            async with GoHighLevelIntegration() as ghl:
                resp = await ghl._request(
                    "GET",
                    f"/conversations/{conversation_id}/messages",
                    params={"limit": limit},
                )
                messages = resp.get("messages", {}).get("messages", [])
                if not messages:
                    return ""
                lines = []
                for m in reversed(messages):
                    direction = m.get("direction", "").lower()
                    role = "Client" if direction == "inbound" else "Us"
                    body = (m.get("body") or m.get("text", "")).strip()
                    if body:
                        lines.append(f"{role}: {body}")
                return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Could not fetch conversation history: {e}")
            return ""

    async def _draft_response(
        self, msg: Dict[str, Any], route: Dict[str, Any]
    ) -> str:
        """
        Generate a draft response in the agent's voice using OpenAI.
        Includes recent conversation history so the agent doesn't repeat itself.
        """
        agent = route["agent"]
        contact = msg["contact_name"]
        body = msg["body"]

        history = await self._fetch_conversation_history(msg.get("conversation_id", ""), limit=20)

        system_prompt = self._get_agent_prompt(agent)

        if history:
            context_block = (
                f"Here is the conversation so far:\n{history}\n\n"
                f"The latest message from {contact} is:\n\"{body}\"\n\n"
            )
        else:
            context_block = f"A new message came in from {contact} via {msg['msg_type']}:\n\n\"{body}\"\n\n"

        user_prompt = (
            f"{context_block}"
            f"Draft a reply in your voice. "
            f"Do NOT repeat any opener already used in this conversation. "
            f"Keep it under 160 characters if SMS, 300 if email. "
            f"Do not add a subject line. Do not sign off with your name. "
            f"Output ONLY the message text, nothing else."
        )

        try:
            resp = await self.openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.4,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Draft generation failed: {e}")
            return f"Hi {contact.split()[0]}! Thanks for reaching out to Grime Guardians. We'll be in touch shortly."

    def _get_agent_prompt(self, agent: str) -> str:
        """
        Return the full persona system prompt for the drafting agent.

        ROUTING INTENT (current state vs. target state):
        - Dean (CMO): handles leads, pricing, sales — NOT yet live in Discord.
          Until Dean's Discord bot launches, his drafts still post to #ops-comms
          for Brandon to approve. Once Dean is live, his bot will post independently.
        - Ava (COO): handles ops, scheduling, cleaner comms — LIVE.
          During the interim period, Ava also drafts for sales inquiries with
          full pricing context so nothing falls through the cracks.
        - Emma (CXO): handles complaints/retention — NOT yet live in Discord.
        """
        SMS_RULES = (
            "\n\nDRAFTING RULES FOR SMS:\n"
            "- Keep replies under 160 characters unless the client asked a detailed question.\n"
            "- Never reuse an opener already used earlier in this conversation.\n"
            "- Output ONLY the message text — no subject lines, no sign-off, no markdown.\n"
            "- Be specific to what the client said. No filler phrases."
        )

        # Full pricing block — shared by Dean and Ava (interim)
        PRICING_BLOCK = """
PRICING (always quote pre-tax; 8.125% tax added at invoice):

ELITE HOME RESET (initial deep clean / lead magnet):
- < 2,000 sqft: $299  |  2,000-3,500 sqft: $399  |  3,500-5,000 sqft: $549
- Strategy: Quote this to new leads. It wins the continuity contract.

MOVE-OUTS:
- Elite Listing Polish: Studio/1bd $549 | 2-3bd $749 | 4+bd $999+
- Move-Out Deep Reset (oven/fridge included): Studio/1bd $849 | 2-3bd $1,149 | 4+bd $1,499+
- Always anchor high: quote Deep Reset first, Listing Polish feels like a deal by comparison.

CONTINUITY PARTNERSHIPS (recurring):
- Essentials: $299 / $399 / $499 by home size (<2k / 2-3.5k / 3.5-5k sqft)
- Prestige:   $449 / $549 / $649 by home size
- VIP Elite:  $799 / $899 / $999 by home size
- 5,000+ sqft: custom quote

B2B TURNOVER (apartments / property managers):
- Studio $399 | 1bd/1ba $499 | 2bd/2ba $599 | 3bd/2+ba $699 | Disaster $900+

ADD-ONS:
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets): $249
- Oven: $100 | Fridge: $100 | Garage sweep: $100
- Carpet shampooing: $40/area | Window tracks: $4/track

MODIFIERS: Pet homes +10% | Heavy buildup +20%

OBJECTION HANDLING:
- "Too expensive" → "If our price matched theirs, which would you choose and why?"
- "Cheaper quote" → "Cheaper guys cost you hours in management headaches. We handle it completely."
- "Can you lower it?" → Remove scope before lowering price. Never discount unprompted.

SALES RULES:
- Always anchor high. Never offer a discount unprompted.
- Always end with a clear next step or scheduling ask.
- When home size is unknown, ask one qualifying question before quoting.
- BBB-accredited, 70+ five-star Google reviews. Premium service for clients who value time over money.
"""

        if "Dean" in agent:
            return (
                "You are Dean, CMO of Grime Guardians. You are the sales expert who turns leads "
                "into long-term clients. Results-driven, never apologize for pricing. "
                "Use Hormozi, Jeremy Miner, Andy Elliott, and Chris Voss frameworks. "
                "Premium positioning: 'We may not be the cheapest — but we're the last call most clients make.'"
                + PRICING_BLOCK + SMS_RULES
            )
        elif "Emma" in agent:
            return (
                "You are Emma, CXO of Grime Guardians — a premium Twin Cities cleaning company. "
                "You handle client experience, complaints, and retention. "
                "Your tone is empathetic, calm, and solution-focused. "
                "Acknowledge the specific issue raised, take ownership, and offer a clear next step. "
                "Never get defensive. Turn every complaint into a retention opportunity."
                + SMS_RULES
            )
        else:
            # Ava (COO) — handles ops + sales in the interim until Dean's Discord bot is live.
            return (
                "You are Ava, COO of Grime Guardians — a premium Twin Cities cleaning company. "
                "You handle operations, scheduling, cleaner logistics, and in the interim, "
                "sales inquiries until the CMO bot launches.\n\n"
                "For OPS messages: be direct, efficient, lead with the answer, give a clear next step.\n"
                "For SALES/PRICING messages: use the full pricing context below — never misquote.\n"
                + PRICING_BLOCK + SMS_RULES
            )

    # ─── Discord Posting ──────────────────────────────────────────────────────

    async def _post_to_discord(
        self,
        msg: Dict[str, Any],
        draft: str,
        route: Dict[str, Any],
    ):
        """Post the inbound message + draft response to Discord for approval."""
        from ..integrations.discord_integration import GrimeGuardiansBot
        from .approval_view import ApprovalView

        channel_id = route.get("channel_id") or 1481493060667052062  # fallback: #ops-comms
        is_sales_channel = channel_id == 1481528969055440940

        # Use Dean's bot for #sales-comms if available, otherwise fall back to Ava
        active_bot = (self.dean_bot if self.dean_bot and is_sales_channel else self.ava_bot)

        channel = active_bot.get_channel(channel_id)
        if not channel:
            logger.error(f"Could not find channel ID {channel_id} — falling back to #ops-comms via Ava.")
            channel = self.ava_bot.get_channel(1481493060667052062)
        if not channel:
            logger.error("Could not find #ops-comms fallback channel either.")
            return

        agent = route["agent"]
        emoji = route["emoji"]
        color = route["color"]
        contact = msg["contact_name"]
        received = msg["received_at"].strftime("%I:%M %p")

        embed = discord.Embed(
            title=f"{emoji} Inbound {msg['msg_type']} — {contact}",
            color=color,
            timestamp=msg["received_at"],
        )
        embed.add_field(name="From", value=f"{contact}\n{msg['contact_phone']}", inline=True)
        embed.add_field(name="Routed to", value=agent, inline=True)
        embed.add_field(name="Received", value=received, inline=True)
        embed.add_field(name="📩 Their message", value=f"```{msg['body']}```", inline=False)
        embed.add_field(
            name=f"✍️ {agent} draft",
            value=f"```{draft}```",
            inline=False,
        )
        embed.set_footer(text="Tap ✅ to send via GHL · ❌ to cancel")

        view = ApprovalView(
            conversation_id=msg["conversation_id"],
            contact_id=msg["contact_id"],
            draft=draft,
            contact_name=contact,
            msg_type=msg["msg_type"],
        )

        await channel.send(embed=embed, view=view)
        logger.info(f"Posted inbound approval request for {contact} to #{channel.name}")
