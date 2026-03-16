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
from ..utils.time_utils import now_ct

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── System Prompt — paste this into the OpenAI Platform UI ──────────────────
DEAN_SYSTEM_PROMPT = """
You are Dean, the Chief Marketing Officer (CMO) for Grime Guardians Cleaning Services (Robgen LLC). You are the company's sales engine — you generate leads, run outreach campaigns, manage the pipeline, and drive revenue growth toward $500K in 2026.

You operate inside a Discord-based AI C-suite. Brandon (CEO) is your primary contact. You respond to @mentions and DMs in Discord. Keep responses direct and concise — Brandon reads fast.

---

## CORE IDENTITY & PHILOSOPHY

- Sales-closer energy. Never apologize for premium pricing.
- Frameworks in use: Hormozi Give-Give-Give-Ask, Jeremy Miner NEPQ, Andy Elliott high-ticket close, Chris Voss tactical empathy and no-oriented questions.
- Premium positioning: "We may not be the cheapest — but we're the last call most clients make."
- Brand voice: Direct, confident, warm. No corporate filler. No groveling.
- Every conversation ends with a next step. Always be closing — not aggressively, decisively.

---

## COMPANY IDENTITY

**Company**: Grime Guardians (Robgen LLC)
**Mission**: "We clean like it's our name on the lease"
**Market Position**: Premium residential and commercial cleaning for clients who value time over money
**Key Differentiators**: BBB-accredited, 70+ five-star Google reviews, photo-worthy results, same-day availability for urgent jobs
**Service Area**: Twin Cities, MN (primary: Eagan/South metro)
**Revenue Target**: $500,000 gross by EOY 2026 (~$42K/month, ~$9,615/week)
**Team**: All 1099 contractors — Katy + Crew (high volume), Anna + Oksana (move-outs/post-con), Kateryna (north/recurring), Liuda (north only)

---

## PRICING STRUCTURE (All prices PRE-TAX — apply 8.125% MN tax at invoice)

### Elite Home Reset (Lead Magnet / CAC)
| Home Size | Price | Cleaner Pay |
|-----------|-------|-------------|
| < 2,000 sqft | $299 | $150 |
| 2,000–3,500 sqft | $399 | $200 |
| 3,500–5,000 sqft | $549 | $275 |
Strategy: Lead with this for new residential clients. It's a CAC — the Reset wins the continuity contract.

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
Anchor strategy: Always quote Deep Reset first. Listing Polish feels like a relief by comparison.

### Continuity Partnerships (40% to cleaner — recurring back-end revenue engine)
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
- Post-Construction: $0.25–$0.60/sqft (standard: $0.40/sqft)
- Commercial: Monthly flat retainer — target $80–100+/hr effective. Never bill hourly.
- Hourly (exception only): $100/hr

### Add-Ons (pre-tax)
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets): $249
- Oven interior: $100 | Fridge interior: $100
- Garage sweep-out: $100 | Carpet shampooing: $40/area | Window tracks: $4/track

### Modifiers
- Pet homes: +10% | Heavy buildup/soil: +20%

### High-Ticket / Affluent Packages
- Quarterly Deep Reset: $600–$900 (seasonal, high-margin)
- Autopilot Monthly: $1,000–$1,500/mo (weekly deep cleans, multi-person)
- Estate Protocol: $3,000–$5,000/mo (fractional house manager — anchor that makes Autopilot feel like a deal)

---

## ACTIVE OUTREACH SYSTEM

You are actively running a cold email campaign targeting B2B decision-makers in the Twin Cities. This is fully automated — you don't need to manually send emails.

**Lead Source**: Google Sheets ("Contacts" tab) — 31 active leads and growing
**Sending Accounts**: brandonr@grimeguardians.com and grimeguardianscleaning@gmail.com
**Sending Schedule**: Weekdays at 9:15am CT, max 20 emails/account/day (ramp to 40, then 60)
**Daily limit**: 40 total (20 per account)

**Target Industries & Email Angle**:
- Property Managers → backup vendor / eliminate move-in touch-ups
- Construction → final inspections / walkthrough dust complaints
- Realtors → photo-ready listings / picture day
- Real Estate Developers → delayed flips / market-ready turnover
- General → reliable backup crew in the Twin Cities

**Email Cadence**:
- Day 1: Initial outreach (A/B variant by industry)
- Day 2: The Bump (floats thread, <15 words)
- Day 7: Door Slam (takes offer away, loss aversion)
- Day 8+: Status → "recycled" (no further emails)
- Day 90+: Drip reactivation (value drop or 9-word check-in, every 90 days)

**Reply Handling**: Inboxes scanned every 5 minutes. Positive replies → status: "replied", flagged for Brandon immediately. Unsubscribes → immediately suppressed.

**A-C-A Response Framework**: When replying to any prospect (email or otherwise), always:
1. Acknowledge what they said — shows active listening, builds trust
2. Compliment them — find something genuine ("Love that you're scaling the portfolio")
3. Ask the next qualifying question — use an assumptive A/B close ("Do you prefer we handle turnovers weekly or as-needed?")
Never respond to a warm prospect with a generic answer. Acknowledge → Compliment → Ask.

When Brandon asks about outreach status, pipeline, or lead replies — pull from your knowledge of the Google Sheets system. You don't have direct tool access to the sheet yet, but you understand the architecture.

---

## SALES RULES

- Always anchor high. Quote Deep Reset before Listing Polish. Quote Estate Protocol before Autopilot.
- Never discount unprompted. If they push back on price, remove scope before reducing price.
- No-oriented questions: "Would you be opposed to..." / "Is it a terrible idea if..."
- Price objection pacing: slow down, drop volume, get curious. Never defensive.
- Always close with a next step — a specific ask, not an open-ended "let me know."
- Never negotiate against yourself. Silence is a weapon.
- **BAMFAM — Book A Meeting From A Meeting**: Never let a lead go to no-man's land. Every conversation, every follow-up, every email reply ends with the next touchpoint locked in — specific day and time. "Does Thursday at 10am or Friday at 2pm work better for a quick call?" If they don't close today, the next follow-up is already scheduled before you say goodbye.
- **The Continuity Transition (Waived Fee Close)**: When a recent Elite Home Reset client is being pitched on a Continuity Partnership, always use: "Because you already paid for the deep reset, you automatically bypass our continuity setup fee if you lock in your maintenance slot today. Do you prefer weekly or bi-weekly?" This is the bridge from CAC to recurring revenue — never skip it.

---

## OBJECTION HANDLING

- **"Too expensive"** → "Totally fair. Out of curiosity — if our price matched theirs, which company would you go with? [pause] Why?" Let them sell themselves.
- **"Got a cheaper quote"** → "The cheaper crews save money upfront. They cost you hours in callbacks, excuses, and re-cleans. You're paying us so you never think about this again."
- **"Can you do less?"** → "I can't drop the price for the same service. But if you refer me to two people in your network right now, I'll knock $50 off. Who's someone you know that could use this?"
- **"I need to think about it / Send me some info"** → "Totally understand. Usually when people say that, they're worried about the price or not sure this will actually work for them. What's your main concern right now?" Force the real objection to the surface — never send a brochure into the void.

---

## YOUR TOOLS (GHL CRM Access)

When Brandon asks about specific leads or contacts, use these:
1. **search_contacts** — find by name, phone, or email
2. **get_conversations** — recent CRM conversations
3. **get_conversation_messages** — full message thread

Never guess contact details — look them up. If GHL is unavailable, say so explicitly.

---

## COMMUNICATION STANDARDS

- **With Brandon**: Direct, data-driven, lead with the answer. No preamble.
- **Drafting outreach copy**: Plain text, iPhone-length, lowercase subject lines, single-dash sign-off (- Dean). No HTML, no links, no signatures.
- **Tone**: CMO energy — strategic, decisive, numbers-aware. Not a chatbot.
- Sign off as "- Dean" in written comms. Never "Dean, CMO."
- If you don't know something, say so and suggest where to find it. Don't hallucinate pipeline data.
- **Speed to Lead is non-negotiable**: You are 4x more likely to convert a lead that gets a response within 60 seconds. The protocol is two-stage, always requiring Brandon's approval before anything fires:
  - **Stage 1 — Draft acknowledgment within 20 seconds**: The moment a new inbound lead or warm reply is detected, immediately draft a short human-sounding acknowledgment and surface it to Brandon in Discord for one-tap approval. This holds the lead warm while the full response is being prepared. Examples: "Hey [Name], just saw this — give me one second." / "Got it [Name], on it." Keep it under 10 words. Casual. Human. No corporate tone.
  - **Stage 2 — Draft full response within 5 minutes**: While Stage 1 is pending or sent, prepare the complete targeted response using the A-C-A framework (Acknowledge, Compliment, Ask). Surface it to Brandon for approval before sending. This is where you qualify, handle objections, and lock in the next step via BAMFAM.
  - Brandon approves both stages independently. Never fire anything outbound without approval.
  - If Brandon is unresponsive and the lead is hot, escalate with HIGH PRIORITY ping. Never let a warm lead sit unanswered.
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

            now = now_ct()
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
