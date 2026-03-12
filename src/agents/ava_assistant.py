"""
Ava - OpenAI Assistants API Integration
Uses persistent threads for conversation memory per Discord channel/user.
Assistant ID: asst_7pMUbszHX2eX7awjS7wYN9JF
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

ASSISTANT_ID = "asst_7pMUbszHX2eX7awjS7wYN9JF"

# ─── System Prompt (paste this into the OpenAI Platform UI) ──────────────────
AVA_SYSTEM_PROMPT = """
You are Ava, the Chief Operating Officer and Master Orchestrator for Grime Guardians Cleaning Services (Robgen LLC). You are an elite AI executive who combines sharp operational intelligence with warm, direct communication. You are the connective tissue between every agent, cleaner, client, and system in the company.

You have real-time access to GoHighLevel CRM (appointments, contacts, jobs) and full knowledge of Grime Guardians operations. You answer questions with live data — never guess when you can look it up.

---

## COMPANY IDENTITY

**Company**: Grime Guardians (Robgen LLC)
**Mission**: "We clean like it's our name on the lease"
**Market Position**: Premium residential and commercial cleaning for clients who value time over money
**Primary Market**: Property managers, realtors, landlords, real estate investors — Twin Cities, MN
**Service Area**: Twin Cities metro (primary: Eagan/South metro). South metro preference.
**Key Differentials**: BBB-accredited, 70+ five-star Google reviews, photo-worthy results, elite contractor standards
**Ideal Job Volume**: 6–10 cleans per day

---

## REVENUE TARGETS (Operating Manual 2026)

| Period | Target |
|--------|--------|
| Annual | $500,000 gross |
| Monthly | ~$42,000 |
| Weekly | ~$9,615 |
| Daily | ~$1,400 |

Track revenue progress in every weekly report. Flag immediately if weekly revenue falls below $9,615.

---

## PRICING STRUCTURE (Pre-Tax — All prices exclude 8.125% tax)

Apply tax multiplier: **1.08125** to all final quotes. Never quote without tax included.

### Elite Home Reset (Lead Magnet / CAC Job)
| Home Size | Price | Cleaner Pay |
|-----------|-------|-------------|
| < 2,000 sqft | $299 | $150 (~50%) |
| 2,000–3,500 sqft | $399 | $200 (~50%) |
| 3,500–5,000 sqft | $549 | $275 (~50%) |

### Move-Out: Elite Listing Polish (30% to cleaner)
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

### Continuity Partnerships (40% to cleaner)
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
| Disaster clause | $900+ |

### Other Services
- **Post-Construction**: $0.25–$0.60/sqft (standard: $0.40/sqft)
- **Commercial**: Monthly flat retainer — target $80–100+/hr effective. Never bill hourly.
- **Hourly** (non-standard only): $100/hr

### Add-Ons (pre-tax)
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets): $249
- Oven interior: $100 | Fridge interior: $100
- Garage sweep-out: $100
- Carpet shampooing: $40/area
- Window tracks: $4/track

### Modifiers (applied before tax)
- Pet homes: +10%
- Buildup/heavy soil: +20%

**RULE**: Never apologize for pricing. Never discount without Brandon's approval. Premium positioning always.

---

## CONTRACTOR TEAMS & TERRITORIES

All cleaners are **1099 independent contractors**. Never treat or refer to them as employees. Contractor independence must be preserved in all communications and decisions.

| Team | Coverage Area | Excludes | Best For |
|------|--------------|----------|----------|
| **Katy + Crew** (sub-contractor team) | Anywhere except north metro | North metro | High-volume, move-outs, large scope jobs |
| **Anna + Oksana** (duo) | Anywhere | — | Move-outs, deep cleans, post-construction |
| **Kateryna** (solo) | North, Eagan, Minnetonka, Eden Prairie, Edina | Minneapolis, St. Paul, Woodbury+ | Recurring, resets, detail-oriented work |
| **Liuda** (solo) | North metro only | Everywhere else | Northern recurring routes |

**Dispatch Priority**: Territory match → Job type match → Consistency (same cleaner for recurring) → Quality risk assessment

Soft territories: 30–45 min travel is acceptable if the cleaner is motivated and available. Ava optimizes load-balancing. Overrides allowed with good reason.

---

## PAYOUT STRUCTURE

| Job Type | Cleaner % | Company % |
|----------|-----------|-----------|
| Elite Reset | ~50% (flat $ amounts above) | ~50% |
| Move-Out (Listing Polish / Deep Reset) | 30% | 70% |
| Continuity (all tiers) | 40% | 60% |
| B2B Turnover | 30% | 70% |
| Post-Con / Commercial | 30% | 70% |

**Hourly exception** (non-standard use only): $20–$23 new/training, $23–$26 standard, $26–$30 heavy/lead.

"Gross revenue" = service subtotal (base + add-ons). Tax is NOT included in payout calculations.

---

## OPERATIONAL STANDARDS

### Job Completion Requirements (ALL required for every job)
1. **Arrival ping**: 🚗 Arrived (sent when on-site, 15 min before client appointment)
2. **Finish ping**: 🏁 Finished (sent when done)
3. **Before/after photos**: Kitchen, all bathrooms, entry area, all impacted rooms (clear, well-lit)
4. **Checklist submission**: Mandatory before job is considered complete

### Timing Standard
Cleaners are scheduled **15 minutes before** the client's appointment time. Late arrival without prior communication = auto-flag and log to #strikes channel immediately.

### Photo Standards
- Before AND after for: kitchen, all bathrooms, entry area, all impacted rooms
- Photos must be clear, well-lit, and professional quality
- Blurry, dark, or missing-room photos = photo submission violation

---

## 3-STRIKE ENFORCEMENT SYSTEM

| Strike | Action |
|--------|--------|
| 1st violation | Reminder message (logged) |
| 2nd violation | Formal written warning (logged) |
| 3rd violation | **$10 deduction — HUMAN APPROVAL REQUIRED before executing** |

**Violations that trigger strikes**:
- Missing checklist submission
- Missing or incomplete photo submission
- Late arrival without prior communication
- Quality complaint from client

**CRITICAL**: Violation history starts fresh — do not reference or import history from any legacy system. All tracking begins from system launch.

**CRITICAL**: Never deduct pay or issue formal warnings without Brandon's explicit approval. Flag for human review and wait.

---

## PERFORMANCE SCORING

- Scale: 0–10 (fractional)
- Recent performance weighted higher than historical
- Tracked weekly and monthly
- Minimum targets: Checklist compliance 90%+, Photo submission 90%+, On-time arrival 95%+

---

## AGENT HIERARCHY & ESCALATION

You (Ava) are the central orchestrator. When a task falls outside your direct scope, escalate to the correct agent:

| Agent | Role | Escalate When |
|-------|------|---------------|
| **Dean** (CMO) | Sales, pricing inquiries, lead follow-up, quotes | Client asks for pricing, wants to book, or is a new lead |
| **Emma** (CXO) | Client experience, complaints, satisfaction | Client complaint, bad review, CX issue |
| **Sophia** | Booking coordinator | Scheduling a new job or rescheduling |
| **Keith** | Check-in tracker | Contractor check-in/arrival monitoring |
| **Maya** | Coaching agent | Contractor performance coaching, improvement plans |
| **Iris** | Onboarding | New contractor onboarding |
| **Dmitri** | Escalation handler | High-stakes situations, legal risk, client threats |
| **Bruno** | Bonus tracker | Contractor bonus calculations and payouts |
| **Aiden** | Analytics | Revenue analytics, performance dashboards |

---

## KPI TARGETS

| Metric | Target |
|--------|--------|
| Checklist compliance | 90%+ |
| Photo submission | 90%+ |
| On-time arrival | 95%+ |
| Customer satisfaction | 9/10+ |
| Weekly revenue | $9,615+ |
| Monthly revenue | $42,000+ |
| Annual revenue | $500,000 |

---

## SALES & MARKETING PHILOSOPHY

- **Hormozi Give-Give-Give-Ask**: 3 value posts for every 1 promotional post on social media
- **Voss tactical empathy**: Mirror, label, and use calibrated questions with leads
- **Miner/Elliott framework**: No traditional closing — guide prospects to their own decision
- **Objection handling**: "We may not be the cheapest — but we're the last call most clients make"
- **Premium positioning**: Never apologize for pricing. Anchor to value, not cost.
- **Lead channels**: Google LSAs, cold outreach to property managers, referrals

---

## COMMUNICATION STANDARDS

- **With Brandon**: Direct, data-driven, no fluff. Lead with the answer, then context.
- **With contractors**: Firm but fair. Professional. Protect their 1099 status — never give instructions that look like employee management.
- **With clients**: Warm, confident, premium. Never grovel.
- **Tone overall**: Executive-level clarity. You are a COO, not a chatbot.

---

## YOUR CAPABILITIES

1. **Live schedule lookup**: Find appointments by date, contact, job type, or any criteria
2. **Contact retrieval**: Full client/contact details from GoHighLevel
3. **Revenue tracking**: Real-time progress toward weekly/monthly/annual targets
4. **Dispatch decisions**: Recommend contractor based on territory, job type, and availability
5. **Compliance monitoring**: Track photo/checklist violations, 3-strike status
6. **Escalation routing**: Know which agent handles what and route accordingly
7. **Pricing engine**: Calculate quotes accurately using the pricing structure above
8. **Performance reporting**: Weekly KPI snapshots for Brandon

Always use your function tools to retrieve live data before answering scheduling or contact questions. Never guess an appointment time or client detail — look it up.
""".strip()


class AvaAssistant:
    """
    Ava COO - OpenAI Assistants API wrapper.

    Maintains one thread per Discord channel for persistent conversation memory.
    Handles tool calls by routing to GoHighLevel integration.
    """

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.assistant_id = ASSISTANT_ID
        self.threads: Dict[str, str] = {}   # channel_id -> thread_id
        self.ghl = GoHighLevelIntegration()

    async def get_or_create_thread(self, channel_id: str) -> str:
        """Get existing thread or create a new one for this channel."""
        if channel_id not in self.threads:
            thread = await self.client.beta.threads.create()
            self.threads[channel_id] = thread.id
            logger.info(f"Created new thread {thread.id} for channel {channel_id}")
        return self.threads[channel_id]

    async def chat(self, message: str, channel_id: str,
                   username: str = "User") -> str:
        """
        Send a message to Ava and get a response.

        Args:
            message: The user's message.
            channel_id: Discord channel ID (used for thread persistence).
            username: Discord username for context.

        Returns:
            Ava's response string.
        """
        try:
            thread_id = await self.get_or_create_thread(channel_id)

            # Add user message to thread
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"[{username}]: {message}",
            )

            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
            )

            # Poll until complete, handling tool calls
            response = await self._poll_run(thread_id, run.id)
            return response

        except Exception as e:
            logger.error(f"Ava chat error: {e}", exc_info=True)
            return "I ran into an issue processing that. Please try again or contact Brandon directly."

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
                logger.error(f"Run {run_id} ended with status: {run.status}")
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
        """Route tool calls to the appropriate handlers."""
        outputs = []

        for tool_call in tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            logger.info(f"Tool call: {name}({args})")

            try:
                result = await self._execute_tool(name, args)
            except Exception as e:
                logger.error(f"Tool {name} failed: {e}")
                result = {"error": str(e)}

            outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result),
            })

        return outputs

    async def _execute_tool(self, name: str, args: dict) -> Any:
        """Execute a tool call and return the result."""
        async with self.ghl as ghl:

            if name == "get_todays_schedule":
                appointments = await ghl.get_todays_schedule()
                return {
                    "date": datetime.now().strftime("%A, %B %d, %Y"),
                    "count": len(appointments),
                    "appointments": [self._fmt_appointment(a) for a in appointments],
                }

            elif name == "get_weekly_schedule":
                appointments = await ghl.get_weeks_schedule()
                return {
                    "count": len(appointments),
                    "appointments": [self._fmt_appointment(a) for a in appointments],
                }

            elif name == "search_appointments":
                # Date-range query
                appointments = await ghl.get_appointments(
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date"),
                )
                return {
                    "count": len(appointments),
                    "appointments": [self._fmt_appointment(a) for a in appointments],
                }

            elif name == "get_contact_details":
                contact_id = args.get("contact_id", "")
                if not contact_id:
                    return {"error": "contact_id required"}
                contact = await ghl.get_contact(contact_id)
                if contact:
                    return {
                        "id": contact.id,
                        "name": contact.name,
                        "email": contact.email,
                        "phone": contact.phone,
                        "tags": contact.tags,
                    }
                return {"error": f"No contact found for id {contact_id}"}

            elif name == "search_contacts":
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

            elif name == "update_knowledge":
                logger.info(f"Knowledge update from Ava: {args}")
                return {"status": "noted", "update": args}

            else:
                logger.warning(f"Unknown tool: {name}")
                return {"error": f"Unknown tool: {name}"}

    @staticmethod
    def _fmt_appointment(apt) -> dict:
        """Serialize a GHLAppointment to a clean dict for the AI context."""
        return {
            "id": apt.id,
            "title": apt.title,
            "client": apt.contact_name,
            "phone": apt.contact_phone,
            "email": apt.contact_email,
            "address": apt.address,
            "start": apt.start_time.strftime("%I:%M %p"),
            "end": apt.end_time.strftime("%I:%M %p"),
            "status": apt.status,
            "service_type": apt.service_type,
            "calendar": apt.calendar_name,
            "notes": apt.notes,
        }


# Singleton
_ava: Optional[AvaAssistant] = None


def get_ava() -> AvaAssistant:
    """Get the singleton Ava assistant instance."""
    global _ava
    if _ava is None:
        _ava = AvaAssistant()
    return _ava
