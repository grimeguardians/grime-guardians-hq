# Grime Guardians Agentic Suite - Project Requirements Plan

## Goal
Build a comprehensive, self-hosted Python-based agentic suite for Grime Guardians that automates all business operations, contractor management, and client services. The system must be deployed on Ubuntu Digital Ocean droplet with zero external automation dependencies, providing complete creative control and scalability to support $300K annual revenue through 8 specialized AI agents working in concert.

## Why
- **Business Value**: Eliminate operational bottlenecks and scale from $20-22K/month to $25K/month minimum
- **Quality Assurance**: Maintain 90%+ checklist compliance and photo submission rates through automated enforcement
- **Competitive Advantage**: Leverage AI for premium service delivery while maintaining BBB-accredited standards
- **Contractor Independence**: Automate management without compromising 1099 contractor status
- **Revenue Growth**: Support 6-10 concurrent cleaning jobs daily with systematic performance tracking

## What
An 8-agent Python system orchestrating Grime Guardians operations through Discord, integrated with GoHighLevel CRM, Notion databases, and Google services. Each agent specializes in specific business functions while maintaining real-time synchronization and compliance with all business rules.

### Success Criteria
- [ ] All 8 agents (Ava, Sophia, Keith, Maya, Iris, Dmitri, Bruno, Aiden) fully operational
- [ ] 90%+ message classification accuracy maintained from existing system
- [ ] Sub-second response times for critical operations (check-ins, escalations)
- [ ] Zero contractor classification violations
- [ ] $300K annual revenue tracking with real-time KPI monitoring
- [ ] 99.9% uptime with comprehensive error handling
- [ ] Complete integration with GoHighLevel, Discord, Notion, Google Drive

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/agents/
  why: PydanticAI agent patterns for FastAPI-style development
  critical: Agent instantiation and reuse patterns, type safety

- url: https://github.com/openai/openai-agents-python
  why: OpenAI's official multi-agent framework for production use
  critical: GPT-4 function calling patterns, agent handoffs

- url: https://docs.pydantic.dev/latest/concepts/models/
  why: Pydantic v2 data validation patterns
  critical: Type safety, validation schemas for business logic

- url: https://neon.com/guides/fastapi-async  
  why: Async FastAPI + PostgreSQL + Pydantic integration patterns
  critical: Database connection management, async patterns

- url: https://makubob.medium.com/combining-fastapi-and-discord-py-9aad07a5cfb6
  why: Discord.py bot integration with FastAPI
  critical: Async event loop management, startup patterns

- url: https://docs.notion.com/reference/intro
  why: Notion API Python SDK documentation
  critical: Database operations, authentication patterns

- file: CLAUDE.md
  why: Complete business context, rules, and compliance requirements
  critical: All pricing logic, contractor management, quality standards, 12-factor methodology

- file: CONTEXT_ENGINEERING_GUIDE.md
  why: 12-Factor Agents methodology implementation guide
  critical: Context ownership, stateless design, structured tools, control flow

- file: PROJECT_ANALYSIS.md  
  why: Migration strategy from existing JavaScript system
  critical: Preserve 90-95% message classification accuracy

- file: /Users/BROB/Desktop/Brain Assets/
  why: Complete business documentation and agent specifications
  critical: Detailed pricing structures, team management, KPIs
```

### Current Codebase Context
```bash
# Existing JavaScript system to migrate from:
grime-guardians-hq/
├── src/
│   ├── agents/ava.js              # 90-95% message classification accuracy
│   ├── utils/
│   │   ├── messageClassifier.js   # GPT-4o-mini integration patterns  
│   │   ├── conversationManager.js # Context threading logic
│   │   └── avaTrainingSystem.js   # Natural language feedback system
│   ├── webhooks/                  # Discord/external API patterns
│   └── index.js                   # Main orchestration
```

### Desired Codebase Structure
```bash
grime-guardians-agentic-suite/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py          # Abstract base class for all agents
│   │   ├── ava_orchestrator.py    # Master coordination agent
│   │   ├── sophia_booking.py       # Client booking & relationship management
│   │   ├── keith_checkin.py       # Contractor status tracking
│   │   ├── maya_coaching.py       # Performance coaching
│   │   ├── iris_onboarding.py     # New contractor onboarding
│   │   ├── dmitri_escalation.py   # Issue resolution & escalation
│   │   ├── bruno_bonus.py         # Bonus tracking & rewards
│   │   └── aiden_analytics.py     # Financial analytics & reporting
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pricing_engine.py      # Exact business pricing calculations
│   │   ├── contractor_manager.py  # Pay splits, performance tracking
│   │   ├── quality_enforcer.py    # 3-strike system, photo validation
│   │   └── message_classifier.py  # Preserve 90-95% accuracy from JS
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── discord_client.py      # Discord bot and webhook handling
│   │   ├── gohighlevel_client.py  # CRM automation and lead management
│   │   ├── notion_client.py       # Knowledge base and performance tracking
│   │   └── google_client.py       # Drive, Gmail, Calendar integration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy models
│   │   ├── schemas.py             # Pydantic schemas for validation
│   │   └── types.py               # Custom types and enums
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI application
│   │   ├── routes/                # API endpoints
│   │   └── middleware/            # Auth, logging, error handling
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py             # Structured logging
│   │   ├── validators.py          # Business logic validation
│   │   └── helpers.py             # Utility functions
│   └── config/
│       ├── __init__.py
│       ├── settings.py            # Environment configuration
│       └── database.py            # Database connection management
├── tests/
│   ├── unit/                      # Unit tests for each module
│   ├── integration/               # API and database integration tests
│   └── e2e/                       # End-to-end workflow tests
├── migrations/                    # Database migrations
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Local development environment
└── deploy/                        # Ubuntu deployment scripts
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: PydanticAI agent patterns
# Agents should be instantiated once as module globals and reused
# Similar to FastAPI routers - avoid recreating agents per request

# CRITICAL: Discord.py + FastAPI integration
# Use bot.start() coroutine with asyncio.create_task() in FastAPI startup
# Don't use bot.run() as it blocks the event loop

# CRITICAL: OpenAI GPT-4 function calling
# Use structured outputs with Pydantic models for 100% reliability
# Always validate function parameters before execution

# CRITICAL: PostgreSQL + FastAPI async patterns  
# Use asyncpg for async database operations
# Implement proper connection pooling with asynccontextmanager

# CRITICAL: Notion API rate limiting
# Notion API has strict rate limits (3 requests/second)
# Implement exponential backoff and request queueing

# CRITICAL: 12-Factor Agent Implementation
# Follow stateless reducer pattern for all agents
# Own your prompts - version control all prompt templates
# Own your context window - strategic information management
# Tools are structured outputs - use Pydantic models for all tools
# Small, focused agents - single responsibility per agent
# Natural language to tool calls - structured function invocations

# CRITICAL: Business logic preservation
# Pricing calculations MUST match existing JavaScript implementation
# All financial math requires decimal.Decimal for accuracy
# Tax multiplier 1.08125 MUST be applied to all quotes

# CRITICAL: Contractor compliance
# No employee-like control mechanisms in agent logic
# All automation must preserve 1099 contractor independence
# 3-strike system is automated but requires human approval for penalties

# CRITICAL: Context Engineering
# Unify execution state and business state
# Compact errors into context window efficiently
# Launch/pause/resume with simple APIs
# Contact humans with tool calls for approvals
```

## Implementation Blueprint

### Data Models and Structure
```python
# Core business models with exact pricing logic preservation
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator

class ServiceType(str, Enum):
    MOVE_OUT_IN = "move_out_in"
    DEEP_CLEANING = "deep_cleaning" 
    RECURRING = "recurring"
    POST_CONSTRUCTION = "post_construction"
    COMMERCIAL = "commercial"
    HOURLY = "hourly"

class PricingStructure(BaseModel):
    base_price: Decimal
    room_modifier: Decimal = Decimal("30")
    full_bath_modifier: Decimal = Decimal("60") 
    half_bath_modifier: Decimal = Decimal("30")
    
class ContractorPerformance(BaseModel):
    contractor_id: str
    checklist_compliance_rate: Decimal = Field(ge=0, le=1)
    photo_submission_rate: Decimal = Field(ge=0, le=1)
    quality_score: Decimal = Field(ge=0, le=10)
    violation_count: int = Field(ge=0, le=3)
    
class AgentMessage(BaseModel):
    agent_id: str
    message_type: str
    content: str
    priority: int = Field(ge=1, le=5)
    requires_response: bool = False
```

### List of Tasks to Complete PRP Implementation

```yaml
Task 1 - Core Infrastructure Setup:
CREATE src/config/settings.py:
  - Environment variable management
  - Database connection strings
  - API keys and secrets management
  - Agent configuration parameters

CREATE src/models/database.py:
  - SQLAlchemy async engine setup
  - Base model with audit fields
  - Database connection lifecycle management

CREATE src/models/schemas.py:
  - Pydantic models for all business entities
  - Validation rules for pricing calculations
  - Type-safe schemas for agent communication

Task 2 - Pricing Engine Migration:
CREATE src/core/pricing_engine.py:
  - EXACT migration of JavaScript pricing logic
  - Decimal precision for financial calculations  
  - Tax application (8.125% = 1.08125 multiplier)
  - Service type pricing structures
  - Add-on and modifier calculations

CREATE tests/unit/test_pricing_engine.py:
  - Test cases for each service type
  - Edge cases for modifier combinations
  - Financial accuracy validation

Task 3 - Message Classification System:
CREATE src/core/message_classifier.py:
  - Preserve 90-95% accuracy from existing system
  - GPT-4o-mini integration patterns
  - Context understanding and routing logic
  - Natural language feedback processing

CREATE tests/unit/test_message_classifier.py:
  - Classification accuracy benchmarks
  - Response routing validation
  - Context preservation tests

Task 4 - Base Agent Framework:
CREATE src/agents/base_agent.py:
  - Abstract base class for all agents
  - Common messaging patterns
  - Error handling and logging
  - State management and persistence

CREATE src/agents/ava_orchestrator.py:
  - Master coordination logic
  - Agent-to-agent communication
  - Business rule enforcement
  - KPI monitoring and alerts

Task 5 - Quality Management System:
CREATE src/core/quality_enforcer.py:
  - 3-strike system implementation
  - Photo validation requirements
  - Checklist compliance tracking
  - Automated penalty calculations

CREATE src/core/contractor_manager.py:
  - Pay split calculations
  - Performance score tracking
  - Geographic assignment optimization
  - Contractor independence compliance

Task 6 - Specialized Agent Implementation:
CREATE src/agents/sophia_booking.py:
  - Client onboarding workflows
  - Quote generation with pricing engine
  - Communication template management
  - Follow-up automation

CREATE src/agents/keith_checkin.py:
  - Real-time status monitoring
  - 15-minute buffer enforcement
  - Escalation trigger logic
  - Geographic tracking

CREATE src/agents/maya_coaching.py:
  - Performance coaching algorithms
  - Training module delivery
  - Skill development tracking
  - Best practice recommendations

CREATE src/agents/iris_onboarding.py:
  - New contractor workflow automation
  - Document processing (W-9, contracts)
  - SOP training delivery
  - Baseline performance establishment

CREATE src/agents/dmitri_escalation.py:
  - Quality complaint resolution
  - Service recovery protocols
  - Conflict resolution workflows
  - Emergency response coordination

CREATE src/agents/bruno_bonus.py:
  - Referral bonus calculations
  - Performance incentive tracking
  - Recognition system automation
  - Reward distribution logic

CREATE src/agents/aiden_analytics.py:
  - Revenue forecasting models
  - Contractor performance analytics
  - Customer lifetime value calculations
  - Financial reporting automation

Task 7 - Integration Layer Development:
CREATE src/integrations/discord_client.py:
  - Async Discord bot implementation
  - Webhook handling for team communication
  - Channel management and permissions
  - Message formatting and routing

CREATE src/integrations/gohighlevel_client.py:
  - CRM API integration
  - Lead management automation
  - Appointment scheduling sync
  - Contact data synchronization

CREATE src/integrations/notion_client.py:
  - Knowledge base management
  - Performance tracking databases
  - SOP documentation access
  - Scorecard system integration

CREATE src/integrations/google_client.py:
  - Drive file management
  - Gmail monitoring (preserve from JS)
  - Calendar integration
  - Document storage automation

Task 8 - API Layer Implementation:
CREATE src/api/main.py:
  - FastAPI application setup
  - Agent endpoint registration
  - Middleware configuration
  - Health check endpoints

CREATE src/api/routes/:
  - Agent communication endpoints
  - Webhook receivers
  - Status monitoring APIs
  - Admin interface routes

Task 9 - Comprehensive Testing:
CREATE tests/integration/:
  - Agent communication flow tests
  - Database integration validation
  - External API integration tests
  - Performance benchmarking

CREATE tests/e2e/:
  - Complete workflow validation
  - Business rule compliance tests
  - Multi-agent coordination scenarios
  - Error recovery testing

Task 10 - Deployment & Monitoring:
CREATE deploy/ubuntu-setup.sh:
  - Ubuntu server configuration
  - Python environment setup
  - Database installation and configuration
  - Process management with systemd

CREATE src/utils/monitoring.py:
  - Health check implementations
  - Performance metrics collection
  - Error tracking and alerting
  - Usage analytics
```

### Implementation Pseudocode

```python
# Task 1 - Settings and Database
class Settings(BaseSettings):
    # PATTERN: Environment-based configuration
    database_url: str = Field(..., env="DATABASE_URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    discord_token: str = Field(..., env="DISCORD_TOKEN")
    notion_token: str = Field(..., env="NOTION_TOKEN")
    
    class Config:
        env_file = ".env"

# Task 2 - Pricing Engine (CRITICAL: Exact JS migration)
class PricingEngine:
    def calculate_service_price(
        self, 
        service_type: ServiceType,
        rooms: int,
        full_baths: int, 
        half_baths: int,
        add_ons: List[str] = None,
        modifiers: Dict[str, bool] = None
    ) -> Decimal:
        # PRESERVE: Exact JavaScript calculation logic
        base = PRICING_STRUCTURE[service_type]["base"]
        total = base + (rooms * Decimal("30")) + (full_baths * Decimal("60"))
        
        # CRITICAL: Apply modifiers before tax
        if modifiers and modifiers.get("pet_homes"):
            total *= Decimal("1.10")
        if modifiers and modifiers.get("buildup"):
            total *= Decimal("1.20")
            
        # CRITICAL: Always apply tax (8.125%)
        return total * Decimal("1.08125")

# Task 4 - Base Agent Pattern
class BaseAgent:
    def __init__(self, agent_id: str, openai_client: AsyncOpenAI):
        self.agent_id = agent_id
        self.client = openai_client
        self.message_queue = asyncio.Queue()
        
    async def process_message(self, message: AgentMessage) -> AgentResponse:
        # PATTERN: Structured GPT-4 function calling
        completion = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message.content}
            ],
            tools=self.get_available_tools(),
            tool_choice="auto"
        )
        return self.handle_completion(completion)

# Task 5 - Quality Enforcement (CRITICAL: 3-strike system)
class QualityEnforcer:
    async def check_compliance(self, job_id: str, contractor_id: str) -> ComplianceResult:
        # PATTERN: Validate photos and checklist
        photos = await self.get_job_photos(job_id)
        checklist = await self.get_job_checklist(job_id)
        
        violations = []
        if not self.validate_photos(photos):
            violations.append("missing_photos")
        if not self.validate_checklist(checklist):
            violations.append("incomplete_checklist")
            
        if violations:
            await self.record_violation(contractor_id, violations)
            strike_count = await self.get_strike_count(contractor_id)
            
            # CRITICAL: Human approval required for penalties
            if strike_count >= 3:
                await self.request_penalty_approval(contractor_id, violations)
                
        return ComplianceResult(violations=violations, strike_count=strike_count)
```

### Integration Points
```yaml
DATABASE:
  - migration: "Create agents, contractors, jobs, performance_metrics tables"
  - indexes: "CREATE INDEX idx_contractor_performance ON performance_metrics(contractor_id, date)"
  
CONFIG:
  - add to: src/config/settings.py
  - pattern: "AGENT_TIMEOUT = int(os.getenv('AGENT_TIMEOUT', '30'))"
  
DISCORD:
  - bot setup: "Use discord.py with FastAPI async integration"
  - webhook pattern: "POST /webhooks/discord for message routing"
  
AGENTS:
  - orchestration: "Ava coordinates all agent activities"
  - communication: "Standardized AgentMessage protocol"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ --fix                    # Auto-fix formatting issues
mypy src/                               # Type checking validation
black src/                              # Code formatting

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests (Each Agent and Core Component)
```python
# CREATE comprehensive test coverage
def test_pricing_engine_accuracy():
    """Verify exact pricing calculations match business rules"""
    engine = PricingEngine()
    result = engine.calculate_service_price(
        ServiceType.MOVE_OUT_IN, 
        rooms=3, 
        full_baths=2, 
        half_baths=1,
        modifiers={"pet_homes": True}
    )
    # CRITICAL: Exact calculation verification
    expected = Decimal("300") + Decimal("90") + Decimal("120") + Decimal("30") 
    expected *= Decimal("1.10") * Decimal("1.08125")  # Pet modifier + tax
    assert result == expected

def test_quality_enforcer_3_strike_system():
    """Validate 3-strike system compliance"""
    enforcer = QualityEnforcer()
    # Test violation recording and penalty triggers
    
def test_message_classification_accuracy():
    """Preserve 90-95% accuracy from JavaScript system"""
    classifier = MessageClassifier()
    # Use test dataset from existing system
```

```bash
# Run and iterate until passing:
pytest tests/unit/ -v --cov=src --cov-report=html
# Target: 90%+ test coverage, all tests passing
```

### Level 3: Integration Tests
```bash
# Start all services
docker-compose up -d postgres
python -m src.api.main

# Test agent communication
curl -X POST http://localhost:8000/agents/ava/message \
  -H "Content-Type: application/json" \
  -d '{"content": "New job assigned: move-out cleaning", "priority": 2}'

# Expected: {"status": "processed", "agent": "ava", "response": "..."}

# Test pricing accuracy
curl -X POST http://localhost:8000/pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{"service_type": "move_out_in", "rooms": 3, "full_baths": 2}'

# Expected: Exact pricing calculation with tax applied
```

## Final Validation Checklist
- [ ] All 8 agents operational: `pytest tests/agents/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] 90%+ test coverage: `pytest --cov=src --cov-report=term`
- [ ] Database migrations work: `alembic upgrade head`
- [ ] All integrations functional: `pytest tests/integration/ -v`
- [ ] Pricing calculations exact: Manual verification against spreadsheet
- [ ] Message classification ≥90% accuracy: Performance benchmark
- [ ] 3-strike system compliance: Business rule validation
- [ ] Agent communication flows: End-to-end workflow tests
- [ ] Ubuntu deployment successful: Production deployment validation

---

## Anti-Patterns to Avoid
- ❌ Don't create new pricing logic - migrate exactly from JavaScript
- ❌ Don't skip business rule validation - all logic must preserve compliance
- ❌ Don't ignore message classification accuracy - maintain 90-95% minimum
- ❌ Don't implement employee-like contractor controls - preserve 1099 status
- ❌ Don't use sync functions in async agent context
- ❌ Don't hardcode business values - use configuration management
- ❌ Don't catch all exceptions - implement specific error handling
- ❌ Don't compromise on type safety - use Pydantic validation everywhere

## Confidence Score: 9/10
This PRP provides comprehensive context for one-pass implementation success through:
- Complete business rule preservation from existing system
- Exact pricing calculation migration requirements  
- Proven architecture patterns from research
- Comprehensive validation at every level
- Clear task breakdown with specific deliverables
- Integration patterns for all external systems
- Business compliance safeguards throughout