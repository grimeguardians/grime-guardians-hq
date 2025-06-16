// src/agents/agent.js
// Base class for all Grime Guardians agents

class Agent {
  constructor({ agentId, role }) {
    this.agentId = agentId;
    this.role = role;
  }

  // Pull context from Notion or other sources
  async getContext(event) {
    // To be implemented by subclass or injected utility
    throw new Error('getContext() must be implemented by agent subclass');
  }

  // Main agentic logic (to be overridden)
  async handleEvent(event, context) {
    throw new Error('handleEvent() must be implemented by agent subclass');
  }

  // Format output for Notion/Discord
  formatOutput({ task, actionRequired, confidence = 1.0, extra = {} }) {
    return {
      agent_id: this.agentId,
      role: this.role,
      task,
      action_required: actionRequired,
      confidence,
      ...extra
    };
  }
}

module.exports = Agent;
