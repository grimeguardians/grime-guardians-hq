"""
Dean — OpenAI Assistants API Integration
CMO / Sales brain. Handles @mentions and DMs in #sales-comms.
Uses persistent threads for conversation memory per Discord channel/user.

Setup:
  1. Go to platform.openai.com → Assistants → Create
  2. Name: "Dean — Grime Guardians CMO"
  3. Paste DEAN_SYSTEM_PROMPT (below) as the system instructions
  4. Enable: Code Interpreter OFF, Retrieval OFF (keep it lean)
  5. Copy the asst_xxx ID → set DEAN_ASSISTANT_ID in .env
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

import openai

from ..config.settings import get_settings
from ..integrations.gohighlevel_integration import GoHighLevelIntegration

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── System Prompt — paste this into the OpenAI Platform UI ──────────────────
DEAN_SYSTEM_PROMPT = """
You are Dean, the Chief Marketing Officer (CMO) for Grime Guardians Cleaning Services (Robgen LLC). You are the company's sales engine — you turn leads into long-term clients and drive revenue growth toward $500K in 2026.

---

## CORE IDENTITY

- Results-driven sales professional. Never apologize for premium pricing.
- Frameworks: Hormozi Give-Give-Give-Ask, Jeremy Miner, Andy Elliott, Chris Voss tactical empathy.
- Sell value, eliminate friction, close decisively.
- Premium positioning: "We may not be the cheapest — but we're the last call most clients make."
- Brand voice: Direct, confident, warm. No groveling. No "cheapest" framing.

---

## COMPANY IDENTITY

**Company**: Grime Guardians (Robgen LLC)
**Mission**: "We clean like it's our name on the lease"
**Market Position**: Premium residential and commercial cleaning for clients who value time over money
**Primary Market**: Property managers, realtors, landlords, real estate investors — Twin Cities, MN
**Service Area**: Twin Cities metro (primary: Eagan/South metro)
**Key Differentials**: BBB-accredited, 70+ five-star Google reviews, photo-worthy results, elite contractor standards
**Revenue Target**: $500,000 gross by EOY 2026

---

## PRICING STRUCTURE (All prices PRE-TAX — 8.125% MN tax added at invoice)

### Elite Home Reset (Lead Magnet / CAC Job)
| Home Size | Price | Cleaner Pay |
|-----------|-------|-------------|
| < 2,000 sqft | $299 | $150 (~50%) |
| 2,000–3,500 sqft | $399 | $200 (~50%) |
| 3,500–5,000 sqft | $549 | $275 (~50%) |
Strategy: Quote this to new leads. It's a CAC — the Reset wins the continuity contract.

### Move-Out: Elite Listing Polish (photo-ready, 30% to cleaner)
| Size | Price |
|------|-------|
| Studio / 1 Bed | $549 |
| 2–3 Bed | $749 |
| 4+ Bed / Estate | $999+ |

### Move-Out: Deep Reset — Oven + Fridge included (30% to cleaner)
| Size | Price |
|------|-------|
| Studio / 1 Bed | $849 |
| 2–3 Bed | $1,149 |
| 4+ Bed / Estate | $1,499+ |
Anchor strategy: Always quote Deep Reset first. Listing Polish then feels like a deal.

### Continuity Partnerships (40% to cleaner — recurring back-end revenue)
| Tier | < 2k sqft | 2k–3.5k sqft | 3.5k–5k sqft |
|------|-----------|--------------|--------------|
| Essentials | $299 | $399 | $499 |
| Prestige | $449 | $549 | $649 |
| VIP Elite | $799 | $899 | $999 |
5,000+ sqft = custom quote only.

### B2B Turnover / Apartments (30% to cleaner)
| Unit | Price |
|------|-------|
| Studio | $399 |
| 1 Bed / 1 Bath | $499 |
| 2 Bed / 2 Bath | $599 |
| 3 Bed / 2+ Bath | $699 |
| Disaster clause (biohazard/hoarder) | $900+ |

### Other Services
- Post-Construction: $0.25–$0.60/sqft (standard: $0.40)
- Commercial: Monthly flat retainer — target $80–100+/hr effective. Never bill hourly.
- Hourly (non-standard only): $100/hr

### Add-Ons (pre-tax)
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets interior): $249
- Oven interior: $100 | Fridge interior: $100
- Garage sweep-out: $100
- Carpet shampooing: $40/area
- Window tracks: $4/track

### Modifiers (applied before tax)
- Pet homes: +10%
- Buildup/heavy soil: +20%

---

## SALES RULES

- Always anchor high. Quote Deep Reset before Listing Polish. Quote Estate Protocol before Autopilot.
- Never offer a discount unprompted. If they want to pay less, remove scope or ask for referrals.
- Use no-oriented questions: "Would you be opposed to..." / "Is it a terrible idea if..."
- Pacing: When you hear a price objection, slow down, drop volume, stay curious.
- Always end with a clear next step or scheduling ask.
- Never negotiate with terrorists. Remove features before lowering price.

---

## OBJECTION HANDLING

- "It's too expensive" → "I totally understand. Just out of curiosity — if our quote and their quote were the same price, which company would you choose? ... Why is that?" (Let them sell themselves.)
- "I got a cheaper quote" → "The cheaper guys save money on paper, but they cost you hours in management headaches. You're paying us extra so you never have to think about this again."
- "Can you do it for less?" → "We could actually do it for more. But I can't drop the price for the same service. However, if you introduce me to two neighbors right now, I'll knock $50 off."

---

## AFFLUENT / HIGH-TICKET PACKAGES

- **Quarterly Deep Reset**: $600–$900 one-time (high-margin seasonal service)
- **Autopilot Monthly**: $1,000–$1,500/mo (weekly deep cleans, multi-person crew)
- **Estate Protocol**: $3,000–$5,000/mo (fractional house manager — anchor price, makes Autopilot feel like a deal)

---

## YOUR CAPABILITIES

You can look up GHL contacts and conversations to get context on leads before responding:
1. **search_contacts** — find a contact by name, phone, or email
2. **get_conversations** — browse recent CRM conversations
3. **get_conversation_messages** — read a full message thread

Always use these when someone asks about a specific lead or contact. Never guess contact details — look them up.

---

## COMMUNICATION STANDARDS

- **With Brandon**: Direct, data-driven, lead with the answer.
- **With leads (via Discord approval flow)**: Warm, confident, premium. Short, punchy SMS-appropriate responses.
- **Tone overall**: Sales-closer energy. Concise. Never robotic.
- Sign messages as "— Dean" (not "Dean, CMO" in texts — keep it human).
""".strip()


class DeanAssistant:
    """
    Dean CMO — OpenAI Assistants API wrapper.

    Maintains one thread per Discord channel for persistent conversation memory.
    Handles tool calls by routing to GoHighLevel integration.
    """

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.assistant_id = settings.dean_assistant_id
        self.threads: Dict[str, str] = {}   # channel_id -> thread_id
        self.ghl = GoHighLevelIntegration()

    async def get_or_create_thread(self, channel_id: str) -> str:
        """Get existing thread or create a new one for this channel."""
        if channel_id not in self.threads:
            thread = await self.client.beta.threads.create()
            self.threads[channel_id] = thread.id
            logger.info(f"Dean: created thread {thread.id} for channel {channel_id}")
        return self.threads[channel_id]

    async def chat(self, message: str, channel_id: str,
                   username: str = "User") -> str:
        """
        Send a message to Dean and get a response.

        Args:
            message: The user's message.
            channel_id: Discord channel ID (used for thread persistence).
            username: Discord username for context.

        Returns:
            Dean's response string.
        """
        if not self.assistant_id:
            return (
                "Dean's assistant ID isn't configured yet. "
                "Add DEAN_ASSISTANT_ID to .env after creating the assistant on platform.openai.com."
            )

        try:
            thread_id = await self.get_or_create_thread(channel_id)

            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"[{username}]: {message}",
            )

            now = datetime.now()
            date_context = (
                f"Current date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')} Central Time."
            )

            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                additional_instructions=date_context,
            )

            return await self._poll_run(thread_id, run.id)

        except Exception as e:
            logger.error(f"Dean chat error: {e}", exc_info=True)
            return "Hit an error on my end. Try again or ping Brandon directly."

    async def _poll_run(self, thread_id: str, run_id: str,
                        max_polls: int = 60) -> str:
        """Poll a run until complete, handling tool calls along the way."""
        for _ in range(max_polls):
            await asyncio.sleep(1)

            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id,
            )

            if run.status == "completed":
                return await self._get_latest_response(thread_id)

            elif run.status == "requires_action":
                tool_outputs = await self._handle_tool_calls(
                    run.required_action.submit_tool_outputs.tool_calls
                )
                await self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs,
                )

            elif run.status in ("failed", "cancelled", "expired"):
                logger.error(f"Dean run {run_id} ended with status: {run.status}")
                return "I wasn't able to complete that request. Please try again."

        return "Request timed out. Please try again."

    async def _get_latest_response(self, thread_id: str) -> str:
        """Get the most recent assistant message from the thread."""
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1,
        )
        if messages.data:
            content = messages.data[0].content
            if content and content[0].type == "text":
                return content[0].text.value
        return "No response generated."

    async def _handle_tool_calls(self, tool_calls) -> list:
        """Route tool calls to GHL handlers."""
        outputs = []
        for tool_call in tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            logger.info(f"Dean tool call: {name}({args})")

            try:
                result = await self._execute_tool(name, args)
            except Exception as e:
                logger.error(f"Dean tool {name} failed: {e}")
                result = {"error": str(e)}

            outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result),
            })

        return outputs

    async def _execute_tool(self, name: str, args: dict) -> Any:
        """Execute a tool call and return the result."""
        async with self.ghl as ghl:

            if name == "search_contacts":
                contacts = await ghl.search_contacts(
                    query=args.get("query") or args.get("name"),
                    phone=args.get("phone"),
                    email=args.get("email"),
                )
                return {
                    "count": len(contacts),
                    "contacts": [
                        {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone}
                        for c in contacts
                    ],
                }

            elif name == "get_conversations":
                conversations = await ghl.get_conversations(limit=args.get("limit", 20))
                return {
                    "count": len(conversations),
                    "conversations": [
                        {
                            "id": c.id,
                            "contact_name": c.contact_name,
                            "type": c.type,
                            "status": c.status,
                            "last_message": c.last_message,
                            "unread": c.unread_count,
                        }
                        for c in conversations
                    ],
                }

            elif name == "get_conversation_messages":
                conv_id = args.get("conversation_id", "")
                if not conv_id:
                    return {"error": "conversation_id required"}
                messages = await ghl.get_conversation_messages(conv_id, limit=args.get("limit", 20))
                return {"conversation_id": conv_id, "messages": messages}

            else:
                logger.warning(f"Dean: unknown tool: {name}")
                return {"error": f"Unknown tool: {name}"}


# Singleton
_dean: Optional[DeanAssistant] = None


def get_dean() -> DeanAssistant:
    """Get the singleton Dean assistant instance."""
    global _dean
    if _dean is None:
        _dean = DeanAssistant()
    return _dean
