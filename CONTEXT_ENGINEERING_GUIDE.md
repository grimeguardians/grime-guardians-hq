# Context Engineering Guide for Grime Guardians Agentic Suite

## Overview
This guide implements the 12-Factor Agents methodology to ensure comprehensive context provision and maximum AI assistance effectiveness for building the Grime Guardians agentic suite.

## 12-Factor Implementation for Context Engineering

### 1. Natural Language to Tool Calls
**Principle**: Translate human requests into structured tool/function invocations

**Implementation for Grime Guardians**:
```python
# Example: Converting "Check if Jennifer is available for a job in Eagan tomorrow" 
# Into structured tool calls:
{
    "tool": "check_contractor_availability",
    "parameters": {
        "contractor_name": "jennifer",
        "location": "eagan",
        "date": "2025-07-06",
        "preferred_territory": true
    }
}
```

**Context Requirements**:
- All contractor names and their territories
- Service areas and geographic preferences
- Available tools and their exact parameters
- Business rules for scheduling and assignments

### 2. Own Your Prompts
**Principle**: Maintain full control and ownership of prompt engineering

**Implementation Strategy**:
```python
# Store prompts in versioned configuration
AGENT_PROMPTS = {
    "ava_orchestrator": {
        "system_prompt": "You are Ava, the COO of Grime Guardians...",
        "version": "1.2.0",
        "context_requirements": [
            "current_kpis", "active_jobs", "contractor_status"
        ]
    }
}
```

**Context Management**:
- Maintain prompt templates in version control
- Include all business context in prompts
- Reference specific files and documentation
- Validate prompt effectiveness with metrics

### 3. Own Your Context Window
**Principle**: Strategically manage all information provided to AI agents

**Context Ownership Strategy**:
```yaml
Essential Context Categories:
  Business Rules:
    - Pricing structures (exact calculations)
    - Contractor compliance requirements
    - Quality standards and enforcement
    - Performance metrics and KPIs
  
  Operational Data:
    - Current contractor status and assignments
    - Active jobs and schedules
    - Client information and preferences
    - Territory management and optimization
  
  Technical Context:
    - Available tools and APIs
    - Database schemas and relationships
    - Integration patterns and examples
    - Error handling and recovery procedures
  
  Compliance Context:
    - 1099 contractor independence requirements
    - Financial accuracy and audit requirements
    - Quality assurance protocols
    - Business rule enforcement patterns
```

### 4. Tools are Structured Outputs
**Principle**: Treat tools as predictable, structured data interfaces

**Tool Design Pattern**:
```python
from pydantic import BaseModel
from typing import Optional, List

class PricingCalculationTool(BaseModel):
    service_type: ServiceType
    rooms: int
    full_baths: int
    half_baths: int
    add_ons: Optional[List[str]] = None
    modifiers: Optional[Dict[str, bool]] = None
    
    def execute(self) -> PricingResult:
        # Structured, predictable output
        return PricingResult(
            base_price=self.calculate_base(),
            total_price=self.calculate_total(),
            tax_amount=self.calculate_tax(),
            breakdown=self.get_breakdown()
        )
```

### 5. Unify Execution State and Business State
**Principle**: Integrate computational processes with core business logic

**Implementation Pattern**:
```python
class GrimeGuardiansState(BaseModel):
    # Business State
    active_jobs: List[Job]
    contractor_statuses: Dict[str, ContractorStatus]
    current_kpis: KPISnapshot
    
    # Execution State
    agent_tasks: List[AgentTask]
    pending_escalations: List[Escalation]
    system_alerts: List[Alert]
    
    def update_unified_state(self, event: BusinessEvent):
        # Update both business and execution state atomically
        self.apply_business_rules(event)
        self.schedule_agent_actions(event)
        self.update_monitoring_metrics(event)
```

### 6. Launch/Pause/Resume with Simple APIs
**Principle**: Create flexible, interruptible agent workflows

**API Design**:
```python
@app.post("/agents/{agent_id}/launch")
async def launch_agent(agent_id: str, task: AgentTask):
    return await agent_manager.launch(agent_id, task)

@app.post("/agents/{agent_id}/pause")
async def pause_agent(agent_id: str):
    return await agent_manager.pause(agent_id)

@app.post("/agents/{agent_id}/resume")  
async def resume_agent(agent_id: str):
    return await agent_manager.resume(agent_id)
```

### 7. Contact Humans with Tool Calls
**Principle**: Use tool invocations as communication mechanisms

**Human-in-the-Loop Pattern**:
```python
class HumanApprovalTool(BaseModel):
    violation_type: str
    contractor_id: str
    evidence: List[str]
    recommended_action: str
    
    def execute(self) -> HumanApprovalRequest:
        # Send to Discord channel for human review
        return self.request_human_approval()
```

### 8. Own Your Control Flow
**Principle**: Maintain explicit programmatic control over agent behavior

**Control Flow Management**:
```python
class AgentWorkflow:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.control_flow = WorkflowEngine()
        
    async def execute_task(self, task: AgentTask):
        # Explicit control flow with business rule validation
        if not self.validate_business_rules(task):
            return self.escalate_to_human(task)
            
        result = await self.process_task(task)
        
        if self.requires_validation(result):
            return self.queue_for_review(result)
            
        return self.complete_task(result)
```

### 9. Compact Errors into Context Window
**Principle**: Efficiently capture and represent error states within context

**Error Context Management**:
```python
class ErrorContext(BaseModel):
    error_type: str
    business_impact: str
    recovery_actions: List[str]
    related_context: Dict[str, Any]
    
    def to_context_summary(self) -> str:
        return f"""
        ERROR: {self.error_type}
        IMPACT: {self.business_impact}
        ACTIONS: {', '.join(self.recovery_actions)}
        CONTEXT: {self.essential_context_only()}
        """
```

### 10. Small, Focused Agents
**Principle**: Break complex tasks into narrow, specialized agent components

**Agent Specialization Strategy**:
```yaml
Agent Responsibilities:
  Ava (Orchestrator):
    - Cross-agent coordination
    - Business rule enforcement
    - KPI monitoring
    
  Emma (Booking):
    - Client onboarding only
    - Quote generation only
    - Communication management only
    
  Keith (Check-in):
    - Status monitoring only
    - Escalation triggers only
    - Geographic optimization only
```

### 11. Trigger from Anywhere
**Principle**: Enable agent activation through diverse entry points

**Multi-Channel Triggers**:
```python
# Discord webhook trigger
@app.post("/webhooks/discord")
async def discord_trigger(webhook_data: DiscordWebhook):
    return await route_to_appropriate_agent(webhook_data)

# GoHighLevel CRM trigger  
@app.post("/webhooks/gohighlevel")
async def ghl_trigger(webhook_data: GHLWebhook):
    return await route_to_appropriate_agent(webhook_data)

# Scheduled trigger
@app.post("/triggers/scheduled")
async def scheduled_trigger(schedule_data: ScheduleEvent):
    return await route_to_appropriate_agent(schedule_data)
```

### 12. Make Your Agent a Stateless Reducer
**Principle**: Design agents as predictable input-output transformation systems

**Stateless Agent Pattern**:
```python
class StatelessAgent:
    def __init__(self, agent_config: AgentConfig):
        self.config = agent_config
        # No instance state stored
        
    async def process(self, 
                     input_data: AgentInput, 
                     context: BusinessContext) -> AgentOutput:
        # Pure function: same input + context = same output
        validated_input = self.validate_input(input_data)
        enriched_context = self.enrich_context(context)
        
        result = await self.execute_business_logic(
            validated_input, 
            enriched_context
        )
        
        return self.format_output(result)
```

## Context Overflow Strategy

### Comprehensive Context Provision
To ensure maximum AI assistance effectiveness, provide:

#### 1. Complete Business Context
```yaml
Always Include:
  - Current pricing structures with exact calculations
  - All contractor information and performance data
  - Active jobs, schedules, and status updates
  - Quality standards and compliance requirements
  - KPIs and performance metrics
  - Territory assignments and preferences
```

#### 2. Technical Implementation Context
```yaml
Always Include:
  - Complete database schemas and relationships
  - API integration patterns and examples
  - Error handling and recovery procedures
  - Deployment and infrastructure requirements
  - Testing patterns and validation approaches
```

#### 3. Historical Context and Patterns
```yaml
Always Include:
  - Previous implementation decisions and rationale
  - Migration patterns from JavaScript system
  - Successful integration examples
  - Performance benchmarks and requirements
  - Error patterns and resolution strategies
```

### Context Management Tools

#### 1. Context Validation
```python
def validate_context_completeness(context: Dict[str, Any]) -> bool:
    required_sections = [
        'business_rules', 'pricing_data', 'contractor_info',
        'quality_standards', 'integration_specs', 'error_patterns'
    ]
    return all(section in context for section in required_sections)
```

#### 2. Context Enrichment
```python
async def enrich_context_for_task(
    base_context: BusinessContext, 
    task: AgentTask
) -> EnrichedContext:
    # Add task-specific context
    relevant_contractors = await get_relevant_contractors(task)
    pricing_context = await get_pricing_context(task.service_type)
    compliance_context = await get_compliance_requirements(task)
    
    return EnrichedContext(
        base=base_context,
        contractors=relevant_contractors,
        pricing=pricing_context,
        compliance=compliance_context
    )
```

#### 3. Context Optimization
```python
def optimize_context_for_window(
    full_context: Dict[str, Any], 
    max_tokens: int
) -> Dict[str, Any]:
    # Prioritize critical business context
    critical_sections = extract_critical_context(full_context)
    remaining_space = max_tokens - estimate_tokens(critical_sections)
    
    # Add additional context by priority
    return add_context_by_priority(critical_sections, remaining_space)
```

## Implementation Checklist

### Context Engineering Setup
- [ ] Implement 12-factor methodology in agent design
- [ ] Create comprehensive context templates
- [ ] Establish context validation and enrichment
- [ ] Design stateless, focused agent components
- [ ] Implement structured tool interfaces

### Business Context Integration
- [ ] Include all pricing and financial calculations
- [ ] Provide complete contractor management context
- [ ] Include quality standards and compliance rules
- [ ] Add KPI tracking and performance metrics
- [ ] Include territory and geographic optimization

### Technical Context Provision
- [ ] Provide complete database schemas
- [ ] Include integration patterns and examples
- [ ] Add error handling and recovery procedures
- [ ] Include deployment and infrastructure specs
- [ ] Provide testing and validation approaches

### Monitoring and Optimization
- [ ] Track context effectiveness metrics
- [ ] Monitor agent performance and accuracy
- [ ] Validate business rule compliance
- [ ] Optimize context window utilization
- [ ] Maintain context quality and relevance

---

This context engineering approach ensures that AI assistance is maximally effective by providing comprehensive, structured, and business-aligned context following proven 12-factor agent methodology principles.