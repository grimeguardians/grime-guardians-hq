### Business Context - Grime Guardians
- **Company**: Grime Guardians (Robgen LLC)
- **Industry**: Residential & Commercial Cleaning Services
- **Structure**: LLC (transitioning to S-Corp)
- **Team**: All contractors, 1099 only — contractor independence MUST be maintained
- **Mission**: "We clean like it's our name on the lease"
- **Market Position**: Premium service for clients who value time over money
- **Key Differentiators**: BBB-accredited, 70+ five-star Google reviews, photo-worthy results
- **Revenue Target**: $500,000 gross by EOY 2026 (~$42K/month, ~$9,615/week)
- **Service Area**: Twin Cities, MN (Primary: Eagan, MN) — South metro preference
- **Ideal Job Volume**: 6-10 cleans per day

---

### Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Use venv_linux** (the virtual environment) whenever executing Python commands, including for unit tests.

---

### Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
  For agents this looks like:
    - `agent.py` - Main agent definition and execution logic
    - `tools.py` - Tool functions used by the agent
    - `prompts.py` - System prompts
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_env()** for environment variables.

---

### Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case

---

### Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under a "Discovered During Work" section.

---

### Technology Stack
- **Primary AI Model**: OpenAI GPT-4 (cost-effective, function-calling)
- **Infrastructure**: Ubuntu droplet on Digital Ocean (self-hosted server)
- **Architecture**: Python agentic suite (FastAPI, asyncio, Pydantic)
- **Memory**: Notion databases (no chat memory)
- **Fallback**: Claude for long-context summarization
- **Core Systems**: GoHighLevel (CRM), Discord (team communication), Google Drive, Notion
- **Agent Architecture**: Ava (COO/orchestrator), Dean (CMO), Emma (CXO), Sophia (booking), Keith (check-in), Maya (coaching), Iris (onboarding), Dmitri (escalation), Bruno (bonus tracking), Aiden (analytics)
- **Development Philosophy**: Zero external dependencies, full creative control, self-contained system

---

### Style & Conventions
- **Python 3.9+**, PEP8, type hints, `black` formatter
- **`pydantic`** for data validation
- **`FastAPI`** for APIs, **`SQLAlchemy`** or `SQLModel` for ORM
- **Security-first** for all financial data handling
- **Decimal arithmetic** for all money calculations (`decimal.Decimal`, `ROUND_HALF_UP`)
- Write **docstrings for every function** (Google style)

---

### Pricing Structure (Source of Truth: GG Operating Manual 2026)

All prices are PRE-TAX. Apply 8.125% tax at invoice (multiplier: 1.08125).

#### Elite Home Reset (Lead Magnet / CAC)
| Home Size | Price | Cleaner Pay (~50%) |
|-----------|-------|---------------------|
| < 2,000 sqft | $299 | $150 |
| 2,000–3,500 sqft | $399 | $200 |
| 3,500–5,000 sqft | $549 | $275 |

#### Move-Out: Elite Listing Polish (30% to cleaner)
| Size | Price |
|------|-------|
| Studio / 1 Bed | $549 |
| 2–3 Bed | $749 |
| 4+ Bed / Estate | $999+ |

#### Move-Out: Deep Reset (30% to cleaner — oven/fridge included)
| Size | Price |
|------|-------|
| Studio / 1 Bed | $849 |
| 2–3 Bed | $1,149 |
| 4+ Bed / Estate | $1,499+ |

#### Continuity Partnerships (40% to cleaner)
| Tier | < 2k sqft | 2k–3.5k sqft | 3.5k–5k sqft |
|------|-----------|--------------|--------------|
| Essentials | $299 | $399 | $499 |
| Prestige | $449 | $549 | $649 |
| VIP Elite | $799 | $899 | $999 |
(5,000+ sqft = custom quote)

#### B2B Turnover / Apartments (30% to cleaner)
| Unit | Price |
|------|-------|
| Studio | $399 |
| 1 Bed / 1 Bath | $499 |
| 2 Bed / 2 Bath | $599 |
| 3 Bed / 2+ Bath | $699 |
| Disaster clause | $900+ |

#### Other
- **Post-Construction**: $0.25–$0.60/sqft (standard: $0.40)
- **Commercial**: Monthly flat retainer — target $80–100+/hr effective. Never bill hourly.
- **Hourly** (non-standard only): $100/hr

#### Add-Ons
- Kitchen Perfection Bundle (Fridge + Oven + Cabinets): $249
- Oven interior: $100 | Fridge interior: $100
- Garage sweep-out: $100 | Carpet shampooing: $40/area | Window tracks: $4/track

#### Modifiers (applied before tax)
- Pet homes: +10% | Buildup: +20%

---

### Payout Structure
| Job Type | Cleaner % | Company % |
|----------|-----------|-----------|
| Elite Reset | ~50% (flat $) | ~50% |
| Move-Out (Listing Polish / Deep Reset) | 30% | 70% |
| Continuity (all tiers) | 40% | 60% |
| B2B Turnover | 30% | 70% |
| Post-Con / Commercial | 30% | 70% |

Hourly (exception use only): $20–$23 (new recruit/training), $23–$26 (standard), $26–$30 (heavy/lead)

"Gross revenue" = service subtotal (base + add-ons). Tax is NOT part of payout.

---

### Team Directory & Dispatch
| Team | Coverage | Excludes | Best For |
|------|----------|----------|----------|
| Katy + Crew (sub) | Anywhere except north | North | High-volume, move-outs, large scope |
| Anna + Oksana (duo) | Anywhere | — | Move-outs, deep cleans, post-con |
| Kateryna (solo) | North, Eagan, Minnetonka, EP, Edina | Mpls, St. Paul, Woodbury+ | Recurring, resets, detail work |
| Liuda (solo) | North only | Everywhere else | Northern recurring routes |

**Dispatch priority**: Territory match → Job type match → Consistency → Quality risk

---

### Operational Compliance & Quality Standards
- **Job Completion Requirements**: 🚗 Arrived ping, 🏁 Finished ping, before/after photos, checklist submission
- **Photo Requirements**: Kitchen, bathrooms, entry area, impacted rooms (clear, well-lit)
- **Timing**: Cleaners scheduled 15 min before client appointment
- **Late arrival without prior communication**: Auto-flag + log to #strikes channel
- **Photo validation**: Primary = submitted yes/no; Secondary = AI quality check (blur, missing rooms, lighting)
- **Performance scoring**: 0–10 fractional scale; recent performance weighted higher; weekly + monthly averages
- **3-Strike Enforcement**: 1st = reminder, 2nd = formal warning, 3rd = $10 deduction (HUMAN APPROVAL required)
- **Violation history**: Starts fresh — no import from legacy system
- **Geographic assignment**: Soft territories (30–45 min travel ok if motivated); Ava optimizes load-balancing; overrides allowed

---

### KPIs
- Checklist compliance: 90%+
- Photo submission: 90%+
- On-time arrival: 95%+
- Customer satisfaction: 9/10+
- Weekly revenue: ~$9,615
- Monthly revenue: ~$42,000
- Annual target: $500,000

---

### 12-Factor Agent Methodology
- **Own Your Context Window**: Strategically manage all information provided to AI agents
- **Own Your Prompts**: Full control of prompt engineering
- **Small, Focused Agents**: Break complex tasks into narrow, specialized components
- **Make Agent a Stateless Reducer**: Predictable input-output transformation
- **Natural Language to Tool Calls**: Translate human language into structured function invocations
- **Own Your Control Flow**: Explicit programmatic control over agent behavior
- **Contact Humans with Tool Calls**: Use tool invocations as communication mechanisms
- **Never hallucinate libraries or functions** — only use known, verified Python packages
- **Always maintain contractor independence** — no employee-like control or management
- **Enforce 3-strike system** consistently with human approval for penalties
