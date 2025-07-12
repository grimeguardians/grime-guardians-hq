# INITIAL_GRIME_GUARDIANS.md

## FEATURE:
Build a comprehensive self-hosted Agentic Suite for Grime Guardians that automates all business operations, contractor management, and client services. The system must be deployed on an Ubuntu Digital Ocean droplet with zero external automation dependencies, providing complete creative control and scalability to support $300K annual revenue.

### Core Agent Systems Required:

#### 1. **Ava - Master Orchestrator Agent**
- Central coordination of all agent activities
- Business rule enforcement and decision making
- KPI monitoring and performance analytics
- Revenue tracking toward $300K annual goal
- Escalation management and workflow coordination

#### 2. **Sophia - Booking & Relationship Coordinator**
- Client onboarding and service booking
- Quote generation with accurate pricing calculations
- Checklist enforcement and photo validation
- 3-strike system implementation for quality control
- Client communication and follow-up management

#### 3. **Keith - Check-in Tracker Agent**
- Real-time contractor status monitoring
- Automated arrival/completion ping tracking
- 15-minute buffer enforcement
- Escalation triggers for missed check-ins
- Geographic assignment optimization

#### 4. **Maya - Contractor Coach Agent**
- Performance coaching and feedback delivery
- Quality improvement recommendations
- Training module delivery
- Skill development tracking
- Best practice reinforcement

#### 5. **Iris - Onboarding Agent**
- New contractor onboarding workflow
- W-9 form processing and policy acknowledgment
- SOP training and checklist familiarization
- Contract execution and documentation
- Initial performance baseline establishment

#### 6. **Dmitri - Escalation Agent**
- Quality complaint resolution
- Service recovery protocols
- Conflict resolution workflows
- Emergency response coordination
- Client satisfaction recovery

#### 7. **Bruno - Bonus Tracker Agent**
- Referral bonus tracking and calculation
- Performance incentive monitoring
- Pay split optimization recommendations
- Financial reward distribution
- Recognition system automation

#### 8. **Aiden - Financial Analytics Agent**
- Revenue forecasting and analysis
- Contractor performance analytics
- Customer lifetime value calculation
- Pricing optimization recommendations
- Financial report generation

## TECHNICAL REQUIREMENTS:

### Infrastructure & Architecture:
- **Platform**: Ubuntu Digital Ocean droplet (self-hosted)
- **Language**: Python 3.9+ with type hints and Pydantic validation
- **AI Model**: OpenAI GPT-4 for cost-effective function calling
- **Fallback**: Claude for long-context summarization
- **Architecture**: Modular agent system with clear separation of concerns
- **Memory**: Notion databases (no chat memory)
- **Communication**: Discord API for team coordination

### Core Business Logic Implementation:

#### Pricing Engine:
```python
# Service pricing calculations with exact business rules
PRICING_STRUCTURE = {
    "move_out_in": {"base": 300, "room": 30, "full_bath": 60, "half_bath": 30},
    "deep_cleaning": {"base": 180, "room": 30, "full_bath": 60, "half_bath": 30},
    "recurring": {"base": 120, "room": 30, "full_bath": 60, "half_bath": 30},
    "post_construction": {"rate": 0.35},  # per sq ft
    "commercial": {"hourly_range": (40, 80)},  # requires walkthrough
    "hourly_rate": 60
}

ADD_ONS = {
    "fridge_interior": 60,
    "oven_interior": 60,
    "cabinet_interior": 60,
    "garage_cleaning": 100,
    "carpet_shampooing": 40  # per room
}

MODIFIERS = {
    "pet_homes": 1.10,
    "buildup": 1.20,
    "tax_multiplier": 1.08125
}
```

#### Contractor Management:
```python
# Pay structure and performance tracking
PAY_STRUCTURE = {
    "base_split": {"cleaner": 0.45, "business": 0.55},
    "top_performer_split": {"cleaner": 0.50, "business": 0.50},
    "specific_rates": {
        "jennifer": 28,
        "olga": 25,
        "liuda": 30,
        "zhanna": 25
    },
    "referral_bonus": 25,
    "violation_penalty": 10
}

QUALITY_REQUIREMENTS = {
    "photos": ["kitchen", "bathrooms", "entry_area", "impacted_rooms"],
    "checklist_types": ["move_in_out", "deep_cleaning", "recurring"],
    "enforcement": "3_strike_system"
}
```

### Integration Requirements:
- **GoHighLevel**: CRM automation, lead management, appointment scheduling
- **Discord**: Team communication, job board, status tracking
- **Notion**: Knowledge base, performance tracking, SOP management
- **Google Drive**: Document storage and sharing

### Compliance & Quality Standards:
- **Contractor Independence**: Maintain 1099 contractor status
- **Financial Accuracy**: All calculations must be auditable
- **Photo Documentation**: Clear, well-lit photos for damage protection
- **3-Strike System**: Automated enforcement with human oversight
- **Performance Metrics**: Weekly scorecards and KPI tracking

## EXAMPLES:
Reference existing code in examples/ directory for:
- Contractor management logic
- Pricing calculation engines
- Quality assurance workflows
- Client communication templates
- Performance tracking systems

## DOCUMENTATION:
- **Internal**: docs/business_requirements.md
- **Compliance**: docs/compliance_rules.md
- **APIs**: GoHighLevel, Discord, Notion, Google Drive documentation
- **Frameworks**: FastAPI, Pydantic, SQLAlchemy for data persistence

## DEPLOYMENT REQUIREMENTS:
- **Server**: Ubuntu Digital Ocean droplet
- **Security**: API key management, secure webhook handling
- **Monitoring**: System health checks, error logging
- **Scalability**: Support for 6-10 cleans per day, multiple contractors
- **Backup**: Regular data backups and disaster recovery

## SUCCESS METRICS:
- **Revenue**: Track progress toward $300K annual goal
- **Quality**: 90%+ checklist compliance, photo submission rates
- **Efficiency**: Automated 80%+ of routine tasks
- **Compliance**: Zero contractor classification violations
- **Performance**: Sub-second response times for critical operations

## OTHER CONSIDERATIONS:
- **Premium Service Focus**: Never compromise on quality for cost savings
- **Contractor Autonomy**: Maintain independence while ensuring quality
- **Client Experience**: BBB-accredited service quality maintenance
- **Territory Management**: Geographic optimization for Twin Cities market
- **Future Expansion**: Architecture must support growth beyond current scale
- **Data Privacy**: Secure handling of financial and personal information
- **Integration Flexibility**: Easy addition of new tools and services
- **Mobile Accessibility**: Contractor-friendly interfaces for field use
- **Real-time Synchronization**: Instant updates across all agent systems

## BUSINESS PHILOSOPHY INTEGRATION:
The system must embody Grime Guardians' core values:
- **"We clean like it's our name on the lease"** - Quality-first approach
- **Premium positioning** - Never apologize for premium pricing
- **Reputation-first** - Maintain 70+ five-star reviews standard
- **Technology-enabled** - Leverage AI for competitive advantage
- **Scalable excellence** - Systems that grow with the business

This agentic suite should eliminate operational bottlenecks, ensure consistent quality delivery, and provide the technological foundation for achieving the $300K revenue target while maintaining the premium service standards that define Grime Guardians' market position.