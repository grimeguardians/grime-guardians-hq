// PostgreSQL MCP Server for Grime Guardians
// Alternative to Notion MCP server for high-volume operations

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import pkg from 'pg';
const { Pool } = pkg;

// Initialize PostgreSQL connection pool
const pool = new Pool({
  user: process.env.POSTGRES_USER || 'postgres',
  host: process.env.POSTGRES_HOST || 'localhost',
  database: process.env.POSTGRES_DB || 'grime_guardians_ops',
  password: process.env.POSTGRES_PASSWORD,
  port: parseInt(process.env.POSTGRES_PORT) || 5432,
  ssl: process.env.POSTGRES_SSL === 'true' ? { rejectUnauthorized: false } : false,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

class PostgreSQLMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: "grime-guardians-postgresql-server",
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
    this.server.onerror = (error) => console.error("[PostgreSQL MCP Error]", error);
    process.on("SIGINT", async () => {
      await pool.end();
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "postgres_log_checkin",
          description: "Log cleaner check-in event to PostgreSQL attendance table",
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
          name: "postgres_log_strike",
          description: "Log a strike to the PostgreSQL strikes table",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              type: { type: "string", enum: ["punctuality", "quality", "compliance"], description: "Strike type" },
              timestamp: { type: "string", description: "ISO timestamp" },
              notes: { type: "string", description: "Strike details" },
              severity: { type: "string", enum: ["low", "medium", "high"], description: "Strike severity" }
            },
            required: ["username", "type", "timestamp"]
          }
        },
        {
          name: "postgres_query_strikes",
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
          name: "postgres_get_cleaner_profile",
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
          name: "postgres_update_cleaner_status",
          description: "Update cleaner status or performance metrics",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              status: { type: "string", enum: ["active", "inactive", "probation", "terminated"], description: "New status" },
              performance_score: { type: "number", description: "Performance score" },
              notes: { type: "string", description: "Update notes" }
            },
            required: ["username"]
          }
        },
        {
          name: "postgres_get_performance_summary",
          description: "Get performance summary for all cleaners or specific cleaner",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Optional: specific cleaner username" },
              days: { type: "number", description: "Days to look back (default 30)" }
            }
          }
        },
        {
          name: "postgres_log_escalation",
          description: "Log an escalation event",
          inputSchema: {
            type: "object",
            properties: {
              username: { type: "string", description: "Cleaner username" },
              type: { type: "string", description: "Escalation type" },
              description: { type: "string", description: "Escalation description" },
              severity: { type: "string", enum: ["low", "medium", "high"], description: "Escalation severity" },
              escalated_to: { type: "string", description: "Person who handled escalation" }
            },
            required: ["username", "type", "description"]
          }
        }
      ]
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "postgres_log_checkin":
            return await this.logCheckin(args);
          
          case "postgres_log_strike":
            return await this.logStrike(args);
          
          case "postgres_query_strikes":
            return await this.queryStrikes(args);
          
          case "postgres_get_cleaner_profile":
            return await this.getCleanerProfile(args);
          
          case "postgres_update_cleaner_status":
            return await this.updateCleanerStatus(args);
          
          case "postgres_get_performance_summary":
            return await this.getPerformanceSummary(args);
          
          case "postgres_log_escalation":
            return await this.logEscalation(args);
          
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        console.error(`Error in ${name}:`, error);
        throw new McpError(
          ErrorCode.InternalError,
          `Database operation failed: ${error.message}`
        );
      }
    });
  }

  async logCheckin(args) {
    const { username, timestamp, notes, jobId } = args;
    
    const query = `
      INSERT INTO attendance (cleaner_name, timestamp, type, job_id, notes)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, created_at
    `;
    
    const result = await pool.query(query, [
      username,
      timestamp,
      'check-in',
      jobId || null,
      notes || null
    ]);

    return {
      content: [
        {
          type: "text",
          text: `✅ Check-in logged for ${username} at ${timestamp} (ID: ${result.rows[0].id})`
        }
      ]
    };
  }

  async logStrike(args) {
    const { username, type, timestamp, notes, severity = 'medium' } = args;
    
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');
      
      // Insert strike
      const strikeQuery = `
        INSERT INTO strikes (cleaner_name, type, timestamp, notes, severity)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
      `;
      
      const strikeResult = await client.query(strikeQuery, [
        username, type, timestamp, notes || null, severity
      ]);
      
      // Update cleaner profile strike counts
      const updateQuery = `
        UPDATE cleaner_profiles 
        SET total_strikes = total_strikes + 1,
            last_strike_date = $2,
            performance_score = calculate_performance_score($1),
            updated_at = NOW()
        WHERE name = $1
      `;
      
      await client.query(updateQuery, [username, timestamp]);
      
      await client.query('COMMIT');

      return {
        content: [
          {
            type: "text",
            text: `⚠️ Strike logged: ${type} (${severity}) for ${username} at ${timestamp} (ID: ${strikeResult.rows[0].id})`
          }
        ]
      };
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async queryStrikes(args) {
    const { username, days = 30, type } = args;
    
    let query = `
      SELECT id, type, timestamp, notes, severity, resolved
      FROM strikes 
      WHERE cleaner_name = $1 
      AND timestamp >= NOW() - INTERVAL '%d days'
    `;
    
    const params = [username];
    
    if (type) {
      query += ' AND type = $2';
      params.push(type);
    }
    
    query += ' ORDER BY timestamp DESC';
    
    // Replace %d with actual days value (safe since it's a number)
    query = query.replace('%d', days);
    
    const result = await pool.query(query, params);

    return {
      content: [
        {
          type: "text",
          text: `Found ${result.rows.length} strikes for ${username} in last ${days} days:\n${JSON.stringify(result.rows, null, 2)}`
        }
      ]
    };
  }

  async getCleanerProfile(args) {
    const { username } = args;
    
    const query = `
      SELECT cp.*,
             COALESCE(recent_strikes.count, 0) as recent_strikes_count
      FROM cleaner_profiles cp
      LEFT JOIN (
        SELECT cleaner_name, COUNT(*) as count
        FROM strikes 
        WHERE timestamp >= NOW() - INTERVAL '30 days'
        GROUP BY cleaner_name
      ) recent_strikes ON cp.name = recent_strikes.cleaner_name
      WHERE cp.name = $1
    `;
    
    const result = await pool.query(query, [username]);

    if (result.rows.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: `No profile found for ${username}`
          }
        ]
      };
    }

    const profile = result.rows[0];

    return {
      content: [
        {
          type: "text",
          text: `Profile for ${username}:\n${JSON.stringify(profile, null, 2)}`
        }
      ]
    };
  }

  async updateCleanerStatus(args) {
    const { username, status, performance_score, notes } = args;
    
    let updates = [];
    let params = [];
    let paramIndex = 1;
    
    if (status) {
      updates.push(`status = $${paramIndex++}`);
      params.push(status);
    }
    
    if (performance_score !== undefined) {
      updates.push(`performance_score = $${paramIndex++}`);
      params.push(performance_score);
    }
    
    if (notes) {
      updates.push(`notes = $${paramIndex++}`);
      params.push(notes);
    }
    
    updates.push(`updated_at = NOW()`);
    params.push(username);
    
    const query = `
      UPDATE cleaner_profiles 
      SET ${updates.join(', ')}
      WHERE name = $${paramIndex}
      RETURNING name, status, performance_score
    `;
    
    const result = await pool.query(query, params);
    
    if (result.rows.length === 0) {
      throw new Error(`No profile found for ${username}`);
    }

    return {
      content: [
        {
          type: "text",
          text: `✅ Updated profile for ${username}: ${JSON.stringify(result.rows[0], null, 2)}`
        }
      ]
    };
  }

  async getPerformanceSummary(args) {
    const { username, days = 30 } = args;
    
    let query;
    let params;
    
    if (username) {
      // Single cleaner summary
      query = `
        SELECT 
          cp.name,
          cp.status,
          cp.performance_score,
          cp.total_strikes,
          COUNT(DISTINCT a.id) as checkins_last_${days}_days,
          COUNT(DISTINCT s.id) as strikes_last_${days}_days
        FROM cleaner_profiles cp
        LEFT JOIN attendance a ON cp.name = a.cleaner_name 
          AND a.timestamp >= NOW() - INTERVAL '${days} days'
          AND a.type = 'check-in'
        LEFT JOIN strikes s ON cp.name = s.cleaner_name 
          AND s.timestamp >= NOW() - INTERVAL '${days} days'
        WHERE cp.name = $1
        GROUP BY cp.name, cp.status, cp.performance_score, cp.total_strikes
      `;
      params = [username];
    } else {
      // All cleaners summary
      query = `
        SELECT 
          cp.name,
          cp.status,
          cp.performance_score,
          cp.total_strikes,
          COUNT(DISTINCT a.id) as checkins_last_${days}_days,
          COUNT(DISTINCT s.id) as strikes_last_${days}_days
        FROM cleaner_profiles cp
        LEFT JOIN attendance a ON cp.name = a.cleaner_name 
          AND a.timestamp >= NOW() - INTERVAL '${days} days'
          AND a.type = 'check-in'
        LEFT JOIN strikes s ON cp.name = s.cleaner_name 
          AND s.timestamp >= NOW() - INTERVAL '${days} days'
        WHERE cp.status = 'active'
        GROUP BY cp.name, cp.status, cp.performance_score, cp.total_strikes
        ORDER BY cp.performance_score DESC
      `;
      params = [];
    }
    
    const result = await pool.query(query, params);

    return {
      content: [
        {
          type: "text",
          text: `Performance summary (last ${days} days):\n${JSON.stringify(result.rows, null, 2)}`
        }
      ]
    };
  }

  async logEscalation(args) {
    const { username, type, description, severity = 'medium', escalated_to } = args;
    
    const query = `
      INSERT INTO escalations (cleaner_name, escalation_type, description, severity, escalated_to)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, created_at
    `;
    
    const result = await pool.query(query, [
      username, type, description, severity, escalated_to || null
    ]);

    return {
      content: [
        {
          type: "text",
          text: `🚨 Escalation logged: ${type} (${severity}) for ${username} (ID: ${result.rows[0].id})`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Grime Guardians PostgreSQL MCP server running on stdio");
  }
}

const server = new PostgreSQLMCPServer();
server.run().catch(console.error);
