# Grime Guardians Agentic Ops Logic Overview

_Last updated: 2025-06-08_

## System Purpose
A modular, agent-driven backend for cleaning ops, with robust attendance, escalation, and bonus logic. All state is stored in Notion; Discord is used for all real-time pings to staff/ops (no SMS/High Level for internal comms).

## Core Agents & Roles
- **Ava (Orchestrator):** Routes events, monitors agent outputs, escalates issues, logs to Notion.
- **Keith (Check-in Monitor):** Detects check-in/out, logs attendance, tracks lateness/strikes, captures notes, manages punctuality escalation.
- **Other Agents:** (Zara, Maya, etc.) handle bonuses, nudges, pricing, etc. (see project instructions for full list).

## Attendance & Escalation Workflow
1. **Check-in/Check-out:**
   - Keith detects check-in/out triggers (emoji, phrase, etc.), logs to Notion, appends notes.
   - If check-in is after 8:05 am, a punctuality strike is logged in `COO_Memory_Stack (8).json` (pillar-specific, rolling 30 days).
   - Strikes are tracked per pillar (punctuality, quality/complaints), and only those within the last 30 days are counted for escalation.
   - If a message contains complaint/quality keywords (e.g., "complaint", "issue", "client unhappy"), a quality strike is logged and flagged for review/escalation.
2. **Punctuality Escalation:**
   - "On time" = 15 min before job start.
   - If not checked in by 5 min late: Ava DMs cleaner ("You're 5 minutes late for arrival. What's your ETA?").
   - 10 min late: Ava DMs cleaner and ops, logs to 🚨-alerts, pings job-check-ins channel.
   - 15 min late: Ava DMs cleaner and escalates to all targets.
   - All escalation logic uses Discord user IDs for reliability and mentions users in channels.
   - Cleaner DMs use direct, human-readable language (no @mention or ID).
3. **Notes:**
   - Notes after check-in/out triggers are parsed and appended to Notion.
4. **Centralized Routing:**
   - All agent outputs are routed through `src/index.js` for logging and escalation.

## Utilities & Integrations
- **Notion API:** CRUD for attendance, notes, strikes (see `src/utils/notion.js`).
- **Discord:** Real-time pings for escalation (see `src/utils/discord.js`).
- **Strike/Violation Memory:** JSON file for persistent strike tracking.
- **Punctuality Escalation Utility:**
  - `schedulePunctualityEscalation`: Schedules and manages escalation pings for late check-ins, using Discord only, with user ID mentions in channels and direct DMs for cleaners.

## Testing & Simulation
- Punctuality escalation can be simulated (1 min = 1 sec) for dev/test.
- All logic is modular and can be extended for new agents or workflows.

## Extensibility
- Add new agents by extending the base Agent class (`src/agents/agent.js`).
- All workflows follow: Trigger → Context → Logic → Output.

---

_This file is the single source of truth for agentic logic. Update as workflows evolve. Every new component, agent, or business logic change should be reflected here for reference and SOP conversion._
