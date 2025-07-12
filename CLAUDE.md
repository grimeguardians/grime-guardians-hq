### 🏢 Business Context - Grime Guardians
- **Company**: Grime Guardians (Robgen LLC)
- **Industry**: Residential & Commercial Cleaning Services
- **Structure**: LLC (transitioning to S-Corp)
- **Team**: All contractors, no employees (1099 contractors only)
- **Mission**: "We clean like it's our name on the lease"
- **Market Position**: Premium service at premium rates - engineered for realtors, landlords, and commercial property managers
- **Key Differentiators**: BBB-accredited, 70+ five-star Google reviews, photo-worthy results
- **Target**: $300,000 gross revenue by end of 2025 ($25K/month minimum)
- **Service Area**: Twin Cities, MN (Primary: Eagan, MN) - South metro preference
- **Ideal Job Volume**: 6-10 cleans per day
- **Cleaner Efficiency Target**: $7,500+/month revenue per cleaner

### 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn’t listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Use venv_linux** (the virtual environment) whenever executing Python commands, including for unit tests.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
  For agents this looks like:
    - `agent.py` - Main agent definition and execution logic 
    - `tools.py` - Tool functions used by the agent 
    - `prompts.py` - System prompts
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_env()** for environment variables.

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case

### ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under a “Discovered During Work” section.

### 🛠️ Technology Stack & Integration Requirements
- **Primary AI Model**: OpenAI GPT-4 (cost-effective, function-calling)
- **Infrastructure**: Ubuntu droplet on Digital Ocean (self-hosted server)
- **Architecture**: Complete custom Python agentic suite
- **Memory**: Notion databases (no chat memory)
- **Fallback**: Claude for long-context summarization
- **Core Systems**: GoHighLevel (CRM automation only), Discord (team communication), Google Drive, Notion
- **Agent Architecture**: Ava (orchestrator), Keith (check-in), Sophia (booking), Maya (coaching), Iris (onboarding), Dmitri (escalation), Bruno (bonus tracking), Aiden (analytics)
- **Development Philosophy**: Zero external dependencies, full creative control, self-contained system

### 📎 Style & Conventions
- **Use Python 3.9+** as the primary language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation**.
- Use `FastAPI` for APIs and `SQLAlchemy` or `SQLModel` for ORM if applicable.
- **Security-first approach** for all financial data handling.
- **Integration-ready architecture** for GoHighLevel, Discord, Notion, Google Drive.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 💰 Pricing Structure & Financial Rules
- **Move-Out/Move-In**: $300 base + $30 per room + $60 per full bath + $30 per half bath
- **Deep Cleaning**: $180 base (same room modifiers)
- **Recurring Maintenance**: $120 base (same room modifiers)
- **Post-Construction**: $0.35/sq ft
- **Commercial**: $40-$80/hr (requires walkthrough)
- **Hourly Rate**: $60/hr for non-standard jobs
- **Add-Ons**: Fridge/Oven/Cabinet interior ($60 each), Garage ($100), Carpet shampooing ($40/room)
- **Modifiers**: Pet homes (+10%), Buildup (+20%)
- **Tax Policy**: ALL quotes include 8.125% tax (multiplier 1.08125)
- **New Client Incentive**: 15% discount (last resort only)

### 👥 Team Structure & Compensation Rules
- **Base Split**: 45/55 (cleaner/business) for new cleaners
- **Top Performer Split**: 50/50 for consistent high-quality performers
- **Specific Rates**: Jennifer $28/hr, Olga $25/hr, Liuda $30/hr, Zhanna $25/hr
- **Referral Bonus**: $25 if cleaner mentioned in 5-star Google review
- **Penalty System**: -$10 deduction for checklist/photo violations (3-strike system)
- **Geographic Preferences**: Jennifer (south metro), Liuda (north metro only)

### 🔒 Operational Compliance & Quality Standards
- **Job Completion Requirements**: Status pings (🚗 Arrived, 🏁 Finished), before/after photos, checklist submission
- **Photo Requirements**: Kitchen, bathrooms, entry area, impacted rooms (clear, well-lit)
- **Timing Standards**: Cleaners scheduled 15 min before client appointment
- **3-Strike Enforcement**: 1st violation (reminder), 2nd violation (formal warning), 3rd violation ($10 deduction)
- **Quality Metrics**: Checklist compliance, photo submission, cleaning quality, client feedback
- **Contractor vs Employee distinction MUST be maintained** - all cleaners are 1099 contractors
- **Financial calculation accuracy** - all calculations must be auditable
- **Integration testing required** for external payment, scheduling, and communication systems

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case
- **Additional testing requirements**:
  - Unit tests for all business logic
  - Integration tests for external services
  - **Compliance validation tests** for contractor classification
  - **Financial calculation accuracy tests** for pricing and payments

### 📈 Sales & Marketing Protocols
- **Lead Generation**: Google LSAs ($5K/month, 4-5X ROI), 200+ cold calls/day for B2B, GoHighLevel automation
- **Sales Philosophy**: Anchor pricing on perceived value, never apologize for premium pricing
- **Objection Handling**: "We may not be the cheapest — but we're the last call most clients make"
- **Referral Strategy**: BNI partners (Chuck Gollop, Matthew Bjorgum), Real Producers Network
- **Communication Standards**: Text/DM (direct, human-first), Email (polished, professional), Discord (encouraging, culture-aligned)

### 🎯 Key Performance Indicators & Tracking
- **Client Experience**: Average Google/Yelp rating, 5-star review count, follow-up feedback %
- **Cleaning Performance**: Checklist compliance rate, photo submission rate, violation counts
- **Job Volume**: Cleans completed per week, decline detection (7+ day drops)
- **Revenue**: Monthly progress toward $300K annual goal
- **Scorecard Metrics**: Checklist compliance, photo quality, client feedback, attendance/punctuality

### ⚖️ Business Decision Logic & Automation Rules
- **Pricing Logic**: Auto-quote for standard services, hourly rate for non-standard/vague requests
- **Scheduling Logic**: Military-style early check-in system, 15-minute arrival buffer, geographic preferences
- **Escalation Triggers**: 3-strike violation system, multiple missed check-ins, quality complaints
- **Quality Assurance**: Photo documentation for damage claim protection, checklist completion for consistency
- **Service Recovery**: Scope confirmation before work, clear pricing adjustment communication

### 🎯 12-Factor Agent Methodology
Following the 12-Factor Agents principles for production-ready AI systems:

#### Context Engineering & Ownership
- **Own Your Context Window**: Strategically manage all information provided to AI agents
- **Own Your Prompts**: Maintain full control and ownership of prompt engineering
- **Compact Errors into Context Window**: Efficiently capture and represent error states within context
- **Unify Execution State and Business State**: Integrate computational processes with core business logic

#### Agent Architecture & Design
- **Small, Focused Agents**: Break complex tasks into narrow, specialized agent components
- **Make Agent a Stateless Reducer**: Design agents as predictable input-output transformation systems
- **Natural Language to Tool Calls**: Translate human language into structured tool/function invocations
- **Tools are Structured Outputs**: Treat tools as predictable, structured data interfaces

#### Control Flow & Integration
- **Own Your Control Flow**: Maintain explicit programmatic control over agent behavior
- **Launch/Pause/Resume with Simple APIs**: Create flexible, interruptible agent workflows
- **Contact Humans with Tool Calls**: Use tool invocations as communication mechanisms
- **Trigger from Anywhere**: Enable agent activation through diverse entry points

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.
- **Always maintain contractor independence** - no employee-like control or management
- **Prioritize premium service quality** over cost-cutting measures
- **Enforce 3-strike system** for quality violations consistently
- **Follow 12-Factor principles** for all agent development and context management