<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a basic JavaScript project for Grime Guardians. Please generate clean, modular code and follow best practices.
<prompt>
  <title>🧠 Ava COO System – GitHub Copilot Handoff (Full Code, No Automation Tools)</title>
  <author>Grime Guardians – Ops Automation Lead</author>
  <date>2025-06</date>

  <purpose>
    This system powers backend ops for a high-performance cleaning team through agent-based automation.
    GitHub Copilot is being onboarded to enhance logic, reduce redundancy, and modularize workflows across JavaScript.
  </purpose>

  <stack>
    <language>JavaScript (modular agent logic, utility logic, scoring)</language>
    <ai_engine>OpenAI GPT-4 (for complex reasoning)</ai_engine>
    <memory_layer>Notion (structured DBs for SOPs, scorecards, violations, agent profiles)</memory_layer>
    <interfaces>Discord (real-time ops feedback), Notion (system-of-record)</interfaces>
  </stack>

  <agents>
    <!--
      Only agents listed here are currently implemented or planned as code modules.
      The table in 'Agent Roles and Architecture' below includes all automation, human, and future roles for full org/ops context.
    -->
    <agent><name>Ava</name><role>Master orchestrator – dispatches sub-agents and escalates to human ops</role></agent>
    <agent><name>Keith</name><role>Check-in monitor – flags lateness, logs punctuality</role></agent>
    <agent><name>Nikolai</name><role>Checklist & photo compliance enforcer – pulls SOP rules and ensures compliance</role></agent>
    <agent><name>Zara</name><role>Bonus engine – computes weekly scores + payouts</role></agent>
    <agent><name>Maya</name><role>Motivational nudgebot – sends shoutouts, reminders, or coaching pings</role></agent>
    <agent><name>Iris</name><role>Pricing logic – builds estimates and manages objections via GPT-4</role></agent>
  </agents>

  <workflow_structure>
    <flow>
      Event Trigger (e.g. missed check-in) → Context Pull (Notion DB) → JavaScript/GPT Logic → Result → Output to Notion or Discord
    </flow>
    <rules>
      <rule>All state lives in Notion – no GPT memory</rule>
      <rule>Use GPT strictly for logic, summarization, or formatting</rule>
      <rule>Use JavaScript modules and utility functions to sanitize/prep data</rule>
      <rule>Workflows should be modular: Trigger → Context → Logic → Output</rule>
    </rules>
  </workflow_structure>

  <logic_patterns>
    <pattern>
      <name>Check-in Escalation</name>
      <description>If lateness exceeds 3x, escalate to Discord and log to Notion</description>
      <tech>Code checks strike count → returns { escalate: true, target: "Brandon" }</tech>
    </pattern>
    <pattern>
      <name>SOP Validator</name>
      <description>Compare cleaner checklist to Notion SOP fields. Use GPT if ambiguity detected.</description>
      <tech>Pull SOP → map vs. checklist → if mismatch, call GPT for review</tech>
    </pattern>
    <pattern>
      <name>Bonus Calculator</name>
      <description>Score weekly KPIs → return bonus eligibility, flags, and summary</description>
      <tech>Notion DB query → JavaScript logic → JSON output to Notion + Discord</tech>
    </pattern>
    <pattern>
      <name>Price Quote Builder</name>
      <description>Dynamic pricing (rooms, sqft, type) + GPT-crafted sales messaging</description>
      <tech>JS formula → markdown table → GPT for persuasive summary</tech>
    </pattern>
  </logic_patterns>

  <enhancement_requests>
    <item>Write modular JS utilities for strike tracking, last-updated versioning, and agent labeling</item>
    <item>Create reusable code structures for: Append, Merge, Compare, and Transform logic</item>
    <item>Ensure all output is labeled (agent, event_type, confidence_score)</item>
    <item>Organize codebase by agent, with clear aliases (e.g. `Keith_Checkin`) in event handlers</item>
    <item>Improve page versioning logic in Notion DB Create/Update nodes (via Last Updated + Content Summary)</item>
  </enhancement_requests>

  <output_guidelines>
    <format>All GPT output must be in Markdown table or JSON object</format>
    <tone>Strictly professional, no conversational or filler language</tone>
    <fields>Every structured message must include: agent_id, task, action_required, and optional confidence</fields>
    <routing>Use Notion for archival logging, Discord for live pings (via Ava bot)</routing>
  </output_guidelines>

  <api_credentials>
    <discord>
      <token_env>DISCORD_BOT_TOKEN</token_env>
      <description>Used to send escalation pings, nudges, or weekly reports</description>
      <infrastructure>Ava’s Discord bot</infrastructure>
    </discord>
    <notion>
      <token_env>NOTION_SECRET</token_env>
      <description>Used to access and update agent memory layers</description>
    </notion>
    <openai>
      <token_env>OPENAI_API_KEY</token_env>
      <description>Used for logic evaluation, summarization, or structured GPT response formatting</description>
    </openai>
    <claude>
      <token_env>CLAUDE_API_KEY</token_env>
      <description>Optional fallback LLM for logic auditing or second-opinion review</description>
    </claude>
  </api_credentials>

  <copilot_instructions>
    <summary>
      Write clean, modular JavaScript logic to power agent workflows.
      Reduce complexity by suggesting reusable patterns.
      Optimize conditional branching, Notion updates, and GPT inputs.
    </summary>
    <context_goals>
      <goal>Streamline Ava’s routing and escalation logic</goal>
      <goal>Make all agents plug-and-play within a pure codebase</goal>
      <goal>Help the system scale to 100+ active clients and 10+ automation agents</goal>
    </context_goals>
  </copilot_instructions>

  ## Agent Roles and Architecture (2025-06)

  | Agent    | Role                    | Primary Function                                               | Tools / APIs                  |
  |----------|-------------------------|----------------------------------------------------------------|-------------------------------|
  | Keith    | Field Operations Manager| Tracks check-ins, sends pre-job reminders, syncs with calendars & attendance | Discord API, GHL, Notion      |
  | Nikolai  | Compliance Enforcer     | Monitors checklist/photo uploads, flags missed SOPs            | Notion, Forms, Discord        |
  | Maya     | Cleaner Coach           | Sends praise, reminders, training nudges                       | Notion, Scorecards, Discord   |
  | Jules    | Scorecard Builder       | Generates weekly performance/KPI reports                       | Excel Tooling, Notion, GHL    |
  | Zara     | Bonus & Violation Tracker| Determines bonuses, issues strikes, monitors behavior          | Notion, Scorecards, Discord   |
  | Kai      | Escalation Strategist   | Alerts Brandon/Lena about repeat issues or critical situations | Discord DM, SMS               |
  | Rhea     | Onboarding Assistant    | Trains new hires with SOPs, checklists, visuals                | Google Drive, Notion          |
  | Talia    | Client Sentiment Profiler| Categorizes client behavior (great/risky/problematic)          | GHL, Feedback Forms           |

  ### Ava (COO) – Master Orchestrator
  - Automates backend ops, coordinates all agents, escalates major issues, and reports to Brandon & Lena.
  - Owns global company memory and routes context to sub-agents as needed.
  - Does not handle direct job check-ins (Keith's domain).

  ### Agent Memory & Cognition
  - Ava: global memory and orchestration.
  - Each agent: domain-specific memory (e.g., Keith = attendance, Maya = praise trends).
  - Selective memory sharing and context routing between agents.

  ### Human Oversight
  - Ava escalates red flags and proposes bonuses/terminations for human approval.
  - Daily syncs and escalation reviews with Brandon & Lena.

  ### Design Principles
  - Modular agents, scalable microservice architecture, platform flexibility (migration-ready), and structured output for all agent actions.
</prompt>
