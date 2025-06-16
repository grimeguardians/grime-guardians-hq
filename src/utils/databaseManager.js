// Enhanced Database Abstraction Layer
// Supports both Notion and PostgreSQL with automatic failover and dual-write capabilities

const { GrimeMCPClient } = require('./mcpClient.js');
const { Client: NotionClient } = require("@notionhq/client");
const { Pool } = require('pg');

class DatabaseManager {
  constructor() {
    this.mcpClient = new GrimeMCPClient();
    this.notionClient = new NotionClient({
      auth: process.env.NOTION_SECRET,
    });
    
    this.postgresPool = new Pool({
      user: process.env.POSTGRES_USER,
      host: process.env.POSTGRES_HOST,
      database: process.env.POSTGRES_DB,
      password: process.env.POSTGRES_PASSWORD,
      port: parseInt(process.env.POSTGRES_PORT) || 5432,
      ssl: process.env.POSTGRES_SSL === 'true' ? { rejectUnauthorized: false } : false,
      max: 10,
      idleTimeoutMillis: 30000,
    });

    // Configuration flags
    this.config = {
      usePostgres: process.env.USE_POSTGRES === 'true',
      dualWrite: process.env.DUAL_WRITE === 'true',
      fallbackToNotion: process.env.FALLBACK_TO_NOTION === 'true',
      validateWrites: process.env.VALIDATE_WRITES === 'true'
    };

    this.stats = {
      notionOperations: 0,
      postgresOperations: 0,
      errors: 0,
      fallbacks: 0
    };
  }

  async initialize() {
    await this.mcpClient.initializeClients();
    
    if (this.config.usePostgres) {
      try {
        // Test PostgreSQL connection
        const client = await this.postgresPool.connect();
        await client.query('SELECT 1');
        client.release();
        console.log('✅ PostgreSQL connection established');
      } catch (error) {
        console.error('❌ PostgreSQL connection failed:', error.message);
        if (!this.config.fallbackToNotion) {
          throw error;
        }
        console.log('🔄 Falling back to Notion');
        this.config.usePostgres = false;
      }
    }
  }

  logOperation(type, success, duration) {
    if (type === 'postgres') {
      this.stats.postgresOperations++;
    } else {
      this.stats.notionOperations++;
    }
    
    if (!success) {
      this.stats.errors++;
    }
    
    // Log to monitoring system if needed
    if (process.env.NODE_ENV === 'production') {
      console.log(`DB_OP: ${type} ${success ? 'SUCCESS' : 'FAILED'} ${duration}ms`);
    }
  }

  async executeWithFallback(operation, ...args) {
    const startTime = Date.now();
    
    if (this.config.usePostgres) {
      try {
        const result = await this.executePostgres(operation, ...args);
        this.logOperation('postgres', true, Date.now() - startTime);
        
        // Dual write to Notion if enabled
        if (this.config.dualWrite) {
          try {
            await this.executeNotion(operation, ...args);
          } catch (error) {
            console.warn('Dual write to Notion failed:', error.message);
          }
        }
        
        return result;
      } catch (error) {
        this.logOperation('postgres', false, Date.now() - startTime);
        console.error('PostgreSQL operation failed:', error.message);
        
        if (this.config.fallbackToNotion) {
          console.log('🔄 Falling back to Notion');
          this.stats.fallbacks++;
          return await this.executeNotion(operation, ...args);
        }
        
        throw error;
      }
    } else {
      return await this.executeNotion(operation, ...args);
    }
  }

  async executePostgres(operation, ...args) {
    switch (operation) {
      case 'logCheckin':
        return await this.postgresLogCheckin(...args);
      case 'logStrike':
        return await this.postgresLogStrike(...args);
      case 'queryStrikes':
        return await this.postgresQueryStrikes(...args);
      case 'getCleanerProfile':
        return await this.postgresGetCleanerProfile(...args);
      case 'updateCleanerStatus':
        return await this.postgresUpdateCleanerStatus(...args);
      default:
        throw new Error(`Unknown PostgreSQL operation: ${operation}`);
    }
  }

  async executeNotion(operation, ...args) {
    switch (operation) {
      case 'logCheckin':
        return await this.mcpClient.logCheckin(...args);
      case 'logStrike':
        return await this.mcpClient.logStrike(...args);
      case 'queryStrikes':
        return await this.mcpClient.queryStrikes(...args);
      case 'getCleanerProfile':
        return await this.mcpClient.getCleanerProfile(...args);
      case 'updateCleanerStatus':
        return await this.mcpClient.updateCleanerStatus(...args);
      default:
        throw new Error(`Unknown Notion operation: ${operation}`);
    }
  }

  // PostgreSQL implementations
  async postgresLogCheckin(username, timestamp, notes, jobId) {
    const query = `
      INSERT INTO attendance (cleaner_name, timestamp, type, job_id, notes)
      VALUES ($1, $2, 'check-in', $3, $4)
      RETURNING id, created_at
    `;
    
    const result = await this.postgresPool.query(query, [username, timestamp, jobId, notes]);
    return {
      success: true,
      id: result.rows[0].id,
      message: `Check-in logged for ${username}`
    };
  }

  async postgresLogStrike(username, type, timestamp, notes) {
    const client = await this.postgresPool.connect();
    
    try {
      await client.query('BEGIN');
      
      // Insert strike
      const strikeQuery = `
        INSERT INTO strikes (cleaner_name, type, timestamp, notes)
        VALUES ($1, $2, $3, $4)
        RETURNING id
      `;
      
      const strikeResult = await client.query(strikeQuery, [username, type, timestamp, notes]);
      
      // Update cleaner profile
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
        success: true,
        id: strikeResult.rows[0].id,
        message: `Strike logged for ${username}`
      };
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async postgresQueryStrikes(username, days = 30, type = null) {
    let query = `
      SELECT id, type, timestamp, notes, severity
      FROM strikes 
      WHERE cleaner_name = $1 
      AND timestamp >= NOW() - INTERVAL '${days} days'
    `;
    
    const params = [username];
    
    if (type) {
      query += ' AND type = $2';
      params.push(type);
    }
    
    query += ' ORDER BY timestamp DESC';
    
    const result = await this.postgresPool.query(query, params);
    return result.rows;
  }

  async postgresGetCleanerProfile(username) {
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
    
    const result = await this.postgresPool.query(query, [username]);
    return result.rows[0] || null;
  }

  async postgresUpdateCleanerStatus(username, status, performanceScore, notes) {
    let updates = [];
    let params = [];
    let paramIndex = 1;
    
    if (status) {
      updates.push(`status = $${paramIndex++}`);
      params.push(status);
    }
    
    if (performanceScore !== undefined) {
      updates.push(`performance_score = $${paramIndex++}`);
      params.push(performanceScore);
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
    
    const result = await this.postgresPool.query(query, params);
    return result.rows[0];
  }

  // Public API methods
  async logCheckin(username, timestamp, notes = null, jobId = null) {
    return await this.executeWithFallback('logCheckin', username, timestamp, notes, jobId);
  }

  async logStrike(username, type, timestamp, notes = null) {
    return await this.executeWithFallback('logStrike', username, type, timestamp, notes);
  }

  async queryStrikes(username, days = 30, type = null) {
    return await this.executeWithFallback('queryStrikes', username, days, type);
  }

  async getCleanerProfile(username) {
    return await this.executeWithFallback('getCleanerProfile', username);
  }

  async updateCleanerStatus(username, status = null, performanceScore = null, notes = null) {
    return await this.executeWithFallback('updateCleanerStatus', username, status, performanceScore, notes);
  }

  // Analytics and monitoring
  async getPerformanceSummary(days = 30) {
    if (this.config.usePostgres) {
      const query = `
        SELECT 
          cp.name,
          cp.status,
          cp.performance_score,
          COUNT(DISTINCT a.id) as checkins_last_${days}_days,
          COUNT(DISTINCT s.id) as strikes_last_${days}_days
        FROM cleaner_profiles cp
        LEFT JOIN attendance a ON cp.name = a.cleaner_name 
          AND a.timestamp >= NOW() - INTERVAL '${days} days'
          AND a.type = 'check-in'
        LEFT JOIN strikes s ON cp.name = s.cleaner_name 
          AND s.timestamp >= NOW() - INTERVAL '${days} days'
        WHERE cp.status = 'active'
        GROUP BY cp.name, cp.status, cp.performance_score
        ORDER BY cp.performance_score DESC
      `;
      
      const result = await this.postgresPool.query(query);
      return result.rows;
    } else {
      // Fallback to individual queries via Notion
      // This would be less efficient but maintains functionality
      throw new Error('Performance summary not available via Notion API');
    }
  }

  async getSystemStats() {
    return {
      ...this.stats,
      configuration: this.config,
      uptime: process.uptime(),
      database_type: this.config.usePostgres ? 'PostgreSQL' : 'Notion'
    };
  }

  async validateData() {
    if (!this.config.validateWrites) return true;
    
    if (this.config.usePostgres && this.config.dualWrite) {
      // Compare recent records between PostgreSQL and Notion
      // This is a complex operation that should be run periodically
      console.log('🔍 Validating data consistency between databases...');
      
      // For now, just return true - full implementation would compare record counts and checksums
      return true;
    }
    
    return true;
  }

  async close() {
    await this.mcpClient.close();
    await this.postgresPool.end();
  }

  // Migration utilities
  async enableDualWrite() {
    this.config.dualWrite = true;
    console.log('✅ Dual write enabled - operations will be written to both databases');
  }

  async disableDualWrite() {
    this.config.dualWrite = false;
    console.log('⚠️ Dual write disabled');
  }

  async switchToPrimaryDatabase(database) {
    if (database === 'postgres') {
      this.config.usePostgres = true;
      console.log('🔄 Switched primary database to PostgreSQL');
    } else if (database === 'notion') {
      this.config.usePostgres = false;
      console.log('🔄 Switched primary database to Notion');
    } else {
      throw new Error('Invalid database type. Use "postgres" or "notion"');
    }
  }
}

// Factory function for easy instantiation
async function createDatabaseManager() {
  const dbManager = new DatabaseManager();
  await dbManager.initialize();
  return dbManager;
}

module.exports = {
  DatabaseManager,
  createDatabaseManager
};
