// src/utils/mcpClient.js
// MCP client utilities for Grime Guardians agents

const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

class GrimeMCPClient {
  constructor() {
    this.notionClient = null;
    this.highlevelClient = null;
    this.discordClient = null;
  }

  async initializeClients() {
    // Initialize Notion MCP client
    this.notionClient = new Client(
      {
        name: "grime-guardians-main",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    const notionTransport = new StdioClientTransport({
      command: "node",
      args: ["./mcp-servers/notion-server/src/index.js"],
    });

    await this.notionClient.connect(notionTransport);
    console.log("✅ Connected to Notion MCP server");

    // TODO: Initialize other MCP clients (High Level, Discord)
  }

  // Notion operations
  async logCheckin(username, timestamp, notes, jobId) {
    if (!this.notionClient) {
      throw new Error("Notion MCP client not initialized");
    }

    const result = await this.notionClient.callTool({
      name: "notion_log_checkin",
      arguments: {
        username,
        timestamp,
        notes,
        jobId
      }
    });

    return result;
  }

  async logStrike(username, type, timestamp, notes) {
    if (!this.notionClient) {
      throw new Error("Notion MCP client not initialized");
    }

    const result = await this.notionClient.callTool({
      name: "notion_log_strike",
      arguments: {
        username,
        type,
        timestamp,
        notes
      }
    });

    return result;
  }

  async queryStrikes(username, days = 30, type = null) {
    if (!this.notionClient) {
      throw new Error("Notion MCP client not initialized");
    }

    const args = { username, days };
    if (type) args.type = type;

    const result = await this.notionClient.callTool({
      name: "notion_query_strikes",
      arguments: args
    });

    return result;
  }

  async getCleanerProfile(username) {
    if (!this.notionClient) {
      throw new Error("Notion MCP client not initialized");
    }

    const result = await this.notionClient.callTool({
      name: "notion_get_cleaner_profile",
      arguments: { username }
    });

    return result;
  }

  async updateCleanerStatus(username, status, performanceScore, notes) {
    if (!this.notionClient) {
      throw new Error("Notion MCP client not initialized");
    }

    const args = { username };
    if (status) args.status = status;
    if (performanceScore !== undefined) args.performance_score = performanceScore;
    if (notes) args.notes = notes;

    const result = await this.notionClient.callTool({
      name: "notion_update_cleaner_status",
      arguments: args
    });

    return result;
  }

  // High Level operations (placeholder for future implementation)
  async getJobsForCleaner(cleanerId) {
    // TODO: Implement High Level MCP calls
    throw new Error("High Level MCP client not yet implemented");
  }

  async scheduleJob(jobData) {
    // TODO: Implement High Level MCP calls
    throw new Error("High Level MCP client not yet implemented");
  }

  // Discord operations (placeholder for future implementation)
  async sendEscalationDM(userId, message) {
    // TODO: Implement Discord MCP calls
    throw new Error("Discord MCP client not yet implemented");
  }

  async postToJobBoard(jobData) {
    // TODO: Implement Discord MCP calls
    throw new Error("Discord MCP client not yet implemented");
  }

  async close() {
    if (this.notionClient) {
      await this.notionClient.close();
    }
    if (this.highlevelClient) {
      await this.highlevelClient.close();
    }
    if (this.discordClient) {
      await this.discordClient.close();
    }
  }
}

// Singleton instance
let mcpClient = null;

async function getMCPClient() {
  if (!mcpClient) {
    mcpClient = new GrimeMCPClient();
    await mcpClient.initializeClients();
  }
  return mcpClient;
}

module.exports = { 
  GrimeMCPClient,
  getMCPClient
};
