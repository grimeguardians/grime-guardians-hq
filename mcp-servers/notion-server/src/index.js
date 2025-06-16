#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { Client } from "@notionhq/client";

// Initialize Notion client
const notion = new Client({
  auth: process.env.NOTION_SECRET,
});

// Database IDs from environment
const ATTENDANCE_DB = process.env.NOTION_ATTENDANCE_DB_ID;
const STRIKES_DB = process.env.NOTION_STRIKES_DB_ID;
const CLEANER_PROFILES_DB = process.env.NOTION_CLEANER_PROFILES_DB_ID;

class NotionMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: "grime-guardians-notion-server",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "notion_log_checkin",
          description: "Log cleaner check-in event to Notion attendance database",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              timestamp: { type: "string", description: "ISO timestamp" },
              notes: { type: "string", description: "Optional notes" },
              jobId: { type: "string", description: "Job identifier" }
            },
            required: ["username", "timestamp"]
          }
        },
        {
          name: "notion_log_strike",
          description: "Log a strike to the Notion strikes database",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              type: { type: "string", enum: ["punctuality", "quality", "compliance"], description: "Strike type" },
              timestamp: { type: "string", description: "ISO timestamp" },
              notes: { type: "string", description: "Strike details" }
            },
            required: ["username", "type", "timestamp"]
          }
        },
        {
          name: "notion_query_strikes",
          description: "Query strikes for a cleaner within time range",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              days: { type: "number", description: "Days to look back (default 30)" },
              type: { type: "string", enum: ["punctuality", "quality", "compliance"], description: "Filter by strike type" }
            },
            required: ["username"]
          }
        },
        {
          name: "notion_get_cleaner_profile",
          description: "Get cleaner profile and performance data",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" }
            },
            required: ["username"]
          }
        },
        {
          name: "notion_update_cleaner_status",
          description: "Update cleaner status or performance metrics",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              status: { type: "string", description: "New status" },
              performance_score: { type: "number", description: "Performance score" },
              notes: { type: "string", description: "Update notes" }
            },
            required: ["username"]
          }
        }
      ]
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "notion_log_checkin":
            return await this.logCheckin(args);
          
          case "notion_log_strike":
            return await this.logStrike(args);
          
          case "notion_query_strikes":
            return await this.queryStrikes(args);
          
          case "notion_get_cleaner_profile":
            return await this.getCleanerProfile(args);
          
          case "notion_update_cleaner_status":
            return await this.updateCleanerStatus(args);
          
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async logCheckin(args) {
    const { username, timestamp, notes, jobId } = args;
    
    const result = await notion.pages.create({
      parent: { database_id: ATTENDANCE_DB },
      properties: {
        "Name": {
          title: [
            {
              text: { content: username }
            }
          ]
        },
        "Timestamp": {
          date: { start: timestamp }
        },
        "Type": {
          select: { name: "Check-in" }
        },
        "Notes": {
          rich_text: [
            {
              text: { content: notes || "" }
            }
          ]
        },
        "Job ID": {
          rich_text: [
            {
              text: { content: jobId || "" }
            }
          ]
        }
      }
    });

    return {
      content: [
        {
          type: "text",
          text: `✅ Check-in logged for ${username} at ${timestamp}`
        }
      ]
    };
  }

  async logStrike(args) {
    const { username, type, timestamp, notes } = args;
    
    const result = await notion.pages.create({
      parent: { database_id: STRIKES_DB },
      properties: {
        "Name": {
          title: [
            {
              text: { content: username }
            }
          ]
        },
        "Type": {
          select: { name: type }
        },
        "Timestamp": {
          date: { start: timestamp }
        },
        "Notes": {
          rich_text: [
            {
              text: { content: notes || "" }
            }
          ]
        }
      }
    });

    return {
      content: [
        {
          type: "text",
          text: `⚠️ Strike logged: ${type} for ${username} at ${timestamp}`
        }
      ]
    };
  }

  async queryStrikes(args) {
    const { username, days = 30, type } = args;
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    let filter = {
      and: [
        {
          property: "Name",
          title: {
            equals: username
          }
        },
        {
          property: "Timestamp",
          date: {
            after: cutoffDate.toISOString()
          }
        }
      ]
    };

    if (type) {
      filter.and.push({
        property: "Type",
        select: {
          equals: type
        }
      });
    }

    const response = await notion.databases.query({
      database_id: STRIKES_DB,
      filter: filter,
      sorts: [
        {
          property: "Timestamp",
          direction: "descending"
        }
      ]
    });

    const strikes = response.results.map(page => ({
      type: page.properties.Type?.select?.name,
      timestamp: page.properties.Timestamp?.date?.start,
      notes: page.properties.Notes?.rich_text?.[0]?.text?.content
    }));

    return {
      content: [
        {
          type: "text",
          text: `Found ${strikes.length} strikes for ${username} in last ${days} days:\n${JSON.stringify(strikes, null, 2)}`
        }
      ]
    };
  }

  async getCleanerProfile(args) {
    const { username } = args;
    
    const response = await notion.databases.query({
      database_id: CLEANER_PROFILES_DB,
      filter: {
        property: "Name",
        title: {
          equals: username
        }
      }
    });

    if (response.results.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: `No profile found for ${username}`
          }
        ]
      };
    }

    const profile = response.results[0];
    const profileData = {
      name: profile.properties.Name?.title?.[0]?.text?.content,
      status: profile.properties.Status?.select?.name,
      performance: profile.properties["Performance Score"]?.number,
      hire_date: profile.properties["Hire Date"]?.date?.start,
      notes: profile.properties.Notes?.rich_text?.[0]?.text?.content
    };

    return {
      content: [
        {
          type: "text",
          text: `Profile for ${username}:\n${JSON.stringify(profileData, null, 2)}`
        }
      ]
    };
  }

  async updateCleanerStatus(args) {
    const { username, status, performance_score, notes } = args;
    
    // First find the cleaner's profile page
    const queryResponse = await notion.databases.query({
      database_id: CLEANER_PROFILES_DB,
      filter: {
        property: "Name",
        title: {
          equals: username
        }
      }
    });

    if (queryResponse.results.length === 0) {
      throw new Error(`No profile found for ${username}`);
    }

    const pageId = queryResponse.results[0].id;
    
    // Build update properties
    const properties = {};
    
    if (status) {
      properties.Status = { select: { name: status } };
    }
    
    if (performance_score !== undefined) {
      properties["Performance Score"] = { number: performance_score };
    }
    
    if (notes) {
      properties.Notes = {
        rich_text: [{ text: { content: notes } }]
      };
    }

    await notion.pages.update({
      page_id: pageId,
      properties: properties
    });

    return {
      content: [
        {
          type: "text",
          text: `✅ Updated profile for ${username}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Grime Guardians Notion MCP server running on stdio");
  }
}

const server = new NotionMCPServer();
server.run().catch(console.error);
