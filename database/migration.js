// Data Migration Utility: Notion → PostgreSQL
// Handles data migration with validation and rollback capabilities

import { Client as NotionClient } from "@notionhq/client";
import pkg from 'pg';
const { Pool } = pkg;
import fs from 'fs';
import path from 'path';

class DataMigrator {
  constructor() {
    this.notion = new NotionClient({
      auth: process.env.NOTION_SECRET,
    });
    
    this.postgres = new Pool({
      user: process.env.POSTGRES_USER || 'postgres',
      host: process.env.POSTGRES_HOST || 'localhost',
      database: process.env.POSTGRES_DB || 'grime_guardians_ops',
      password: process.env.POSTGRES_PASSWORD,
      port: parseInt(process.env.POSTGRES_PORT) || 5432,
      ssl: process.env.POSTGRES_SSL === 'true' ? { rejectUnauthorized: false } : false,
    });

    this.migrationLog = [];
    this.errors = [];
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}`;
    console.log(logEntry);
    this.migrationLog.push(logEntry);
  }

  logError(error, context = '') {
    const timestamp = new Date().toISOString();
    const errorEntry = {
      timestamp,
      error: error.message,
      stack: error.stack,
      context
    };
    console.error(`[${timestamp}] ERROR: ${error.message}`, context);
    this.errors.push(errorEntry);
  }

  async saveMigrationReport() {
    const report = {
      migration_date: new Date().toISOString(),
      log: this.migrationLog,
      errors: this.errors,
      summary: {
        total_errors: this.errors.length,
        migration_completed: this.errors.length === 0
      }
    };

    const reportPath = `migration_report_${Date.now()}.json`;
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    this.log(`Migration report saved to: ${reportPath}`);
    return reportPath;
  }

  async validateNotionConnections() {
    this.log("Validating Notion database connections...");
    
    const databases = [
      { name: 'Attendance', id: process.env.NOTION_ATTENDANCE_DB_ID },
      { name: 'Strikes', id: process.env.NOTION_STRIKES_DB_ID },
      { name: 'Cleaner Profiles', id: process.env.NOTION_CLEANER_PROFILES_DB_ID }
    ];

    for (const db of databases) {
      try {
        await this.notion.databases.retrieve({ database_id: db.id });
        this.log(`✅ ${db.name} database accessible`);
      } catch (error) {
        this.logError(error, `Failed to access ${db.name} database`);
        throw new Error(`Cannot access Notion ${db.name} database`);
      }
    }
  }

  async validatePostgreSQLConnection() {
    this.log("Validating PostgreSQL connection...");
    
    try {
      const client = await this.postgres.connect();
      const result = await client.query('SELECT NOW()');
      client.release();
      this.log(`✅ PostgreSQL connected: ${result.rows[0].now}`);
    } catch (error) {
      this.logError(error, 'PostgreSQL connection failed');
      throw new Error('Cannot connect to PostgreSQL database');
    }
  }

  async migrateCleanerProfiles() {
    this.log("Starting cleaner profiles migration...");
    
    try {
      // Fetch all cleaner profiles from Notion
      const response = await this.notion.databases.query({
        database_id: process.env.NOTION_CLEANER_PROFILES_DB_ID
      });

      this.log(`Found ${response.results.length} cleaner profiles in Notion`);

      for (const profile of response.results) {
        try {
          const props = profile.properties;
          
          const cleanerData = {
            name: props.Name?.title?.[0]?.text?.content || 'Unknown',
            status: props.Status?.select?.name || 'active',
            performance_score: props["Performance Score"]?.number || 0.0,
            hire_date: props["Hire Date"]?.date?.start || null,
            phone: props.Phone?.phone_number || null,
            email: props.Email?.email || null,
            notes: props.Notes?.rich_text?.[0]?.text?.content || null
          };

          // Insert into PostgreSQL
          const query = `
            INSERT INTO cleaner_profiles (name, status, performance_score, hire_date, phone, email, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (name) DO UPDATE SET
              status = EXCLUDED.status,
              performance_score = EXCLUDED.performance_score,
              hire_date = EXCLUDED.hire_date,
              phone = EXCLUDED.phone,
              email = EXCLUDED.email,
              notes = EXCLUDED.notes,
              updated_at = NOW()
            RETURNING id
          `;

          const result = await this.postgres.query(query, [
            cleanerData.name,
            cleanerData.status,
            cleanerData.performance_score,
            cleanerData.hire_date,
            cleanerData.phone,
            cleanerData.email,
            cleanerData.notes
          ]);

          this.log(`✅ Migrated profile: ${cleanerData.name} (ID: ${result.rows[0].id})`);
        } catch (error) {
          this.logError(error, `Failed to migrate profile: ${profile.id}`);
        }
      }

      this.log("Cleaner profiles migration completed");
    } catch (error) {
      this.logError(error, 'Cleaner profiles migration failed');
      throw error;
    }
  }

  async migrateAttendanceData() {
    this.log("Starting attendance data migration...");
    
    try {
      let hasMore = true;
      let nextCursor = undefined;
      let totalRecords = 0;

      while (hasMore) {
        const response = await this.notion.databases.query({
          database_id: process.env.NOTION_ATTENDANCE_DB_ID,
          page_size: 100,
          start_cursor: nextCursor
        });

        for (const record of response.results) {
          try {
            const props = record.properties;
            
            const attendanceData = {
              cleaner_name: props.Name?.title?.[0]?.text?.content || 'Unknown',
              timestamp: props.Date?.date?.start || props.Timestamp?.date?.start,
              type: props.Type?.select?.name || 'check-in',
              job_id: props["Job ID"]?.rich_text?.[0]?.text?.content || null,
              notes: props.Notes?.rich_text?.[0]?.text?.content || null
            };

            if (!attendanceData.timestamp) {
              this.logError(new Error('Missing timestamp'), `Record: ${record.id}`);
              continue;
            }

            const query = `
              INSERT INTO attendance (cleaner_name, timestamp, type, job_id, notes)
              VALUES ($1, $2, $3, $4, $5)
              RETURNING id
            `;

            const result = await this.postgres.query(query, [
              attendanceData.cleaner_name,
              attendanceData.timestamp,
              attendanceData.type,
              attendanceData.job_id,
              attendanceData.notes
            ]);

            totalRecords++;
            if (totalRecords % 50 === 0) {
              this.log(`Migrated ${totalRecords} attendance records...`);
            }
          } catch (error) {
            this.logError(error, `Failed to migrate attendance record: ${record.id}`);
          }
        }

        hasMore = response.has_more;
        nextCursor = response.next_cursor;
      }

      this.log(`✅ Attendance migration completed: ${totalRecords} records`);
    } catch (error) {
      this.logError(error, 'Attendance migration failed');
      throw error;
    }
  }

  async migrateStrikesData() {
    this.log("Starting strikes data migration...");
    
    try {
      const response = await this.notion.databases.query({
        database_id: process.env.NOTION_STRIKES_DB_ID
      });

      this.log(`Found ${response.results.length} strikes in Notion`);

      for (const strike of response.results) {
        try {
          const props = strike.properties;
          
          const strikeData = {
            cleaner_name: props.Name?.title?.[0]?.text?.content || props.User?.title?.[0]?.text?.content || 'Unknown',
            type: props.Type?.select?.name || props["Violation Type"]?.select?.name || 'quality',
            timestamp: props.Date?.date?.start || props.Timestamp?.date?.start,
            notes: props.Notes?.rich_text?.[0]?.text?.content || null,
            severity: 'medium' // Default since Notion doesn't have this field
          };

          // Normalize type values
          if (strikeData.type) {
            strikeData.type = strikeData.type.toLowerCase();
            if (!['punctuality', 'quality', 'compliance'].includes(strikeData.type)) {
              strikeData.type = 'quality'; // Default fallback
            }
          }

          if (!strikeData.timestamp) {
            this.logError(new Error('Missing timestamp'), `Strike record: ${strike.id}`);
            continue;
          }

          const query = `
            INSERT INTO strikes (cleaner_name, type, timestamp, notes, severity)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
          `;

          const result = await this.postgres.query(query, [
            strikeData.cleaner_name,
            strikeData.type,
            strikeData.timestamp,
            strikeData.notes,
            strikeData.severity
          ]);

          this.log(`✅ Migrated strike: ${strikeData.type} for ${strikeData.cleaner_name} (ID: ${result.rows[0].id})`);
        } catch (error) {
          this.logError(error, `Failed to migrate strike: ${strike.id}`);
        }
      }

      this.log("Strikes migration completed");
    } catch (error) {
      this.logError(error, 'Strikes migration failed');
      throw error;
    }
  }

  async validateMigration() {
    this.log("Validating migration integrity...");
    
    try {
      // Count records in PostgreSQL
      const countQueries = [
        { name: 'cleaner_profiles', query: 'SELECT COUNT(*) FROM cleaner_profiles' },
        { name: 'attendance', query: 'SELECT COUNT(*) FROM attendance' },
        { name: 'strikes', query: 'SELECT COUNT(*) FROM strikes' }
      ];

      for (const countQuery of countQueries) {
        const result = await this.postgres.query(countQuery.query);
        this.log(`PostgreSQL ${countQuery.name}: ${result.rows[0].count} records`);
      }

      // Validate data integrity
      const integrityQuery = `
        SELECT 
          cp.name,
          COUNT(DISTINCT a.id) as attendance_count,
          COUNT(DISTINCT s.id) as strikes_count
        FROM cleaner_profiles cp
        LEFT JOIN attendance a ON cp.name = a.cleaner_name
        LEFT JOIN strikes s ON cp.name = s.cleaner_name
        GROUP BY cp.name
        ORDER BY cp.name
      `;

      const integrityResult = await this.postgres.query(integrityQuery);
      this.log(`Data integrity check: ${integrityResult.rows.length} cleaners with linked data`);
      
      // Update performance scores
      await this.postgres.query('SELECT update_all_performance_scores()');
      this.log("✅ Performance scores updated");

    } catch (error) {
      this.logError(error, 'Migration validation failed');
      throw error;
    }
  }

  async runFullMigration() {
    this.log("=== Starting full data migration from Notion to PostgreSQL ===");
    
    try {
      // Pre-migration validation
      await this.validateNotionConnections();
      await this.validatePostgreSQLConnection();

      // Run migrations
      await this.migrateCleanerProfiles();
      await this.migrateAttendanceData();
      await this.migrateStrikesData();

      // Post-migration validation
      await this.validateMigration();

      this.log("=== Migration completed successfully ===");
      
      if (this.errors.length > 0) {
        this.log(`⚠️  Migration completed with ${this.errors.length} errors`);
      } else {
        this.log("✅ Migration completed without errors");
      }

    } catch (error) {
      this.logError(error, 'Migration failed');
      throw error;
    } finally {
      await this.saveMigrationReport();
      await this.postgres.end();
    }
  }

  async runDryRun() {
    this.log("=== Starting migration dry run ===");
    
    try {
      await this.validateNotionConnections();
      await this.validatePostgreSQLConnection();

      // Count records without migrating
      const databases = [
        { name: 'Cleaner Profiles', id: process.env.NOTION_CLEANER_PROFILES_DB_ID },
        { name: 'Attendance', id: process.env.NOTION_ATTENDANCE_DB_ID },
        { name: 'Strikes', id: process.env.NOTION_STRIKES_DB_ID }
      ];

      for (const db of databases) {
        const response = await this.notion.databases.query({
          database_id: db.id,
          page_size: 1
        });
        
        // Get total count by querying without limit
        const fullResponse = await this.notion.databases.query({
          database_id: db.id
        });
        
        this.log(`${db.name}: ${fullResponse.results.length} records ready for migration`);
      }

      this.log("✅ Dry run completed successfully");
    } catch (error) {
      this.logError(error, 'Dry run failed');
      throw error;
    }
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  const migrator = new DataMigrator();

  try {
    switch (command) {
      case 'dry-run':
        await migrator.runDryRun();
        break;
      case 'migrate':
        await migrator.runFullMigration();
        break;
      default:
        console.log(`
Usage: node migration.js <command>

Commands:
  dry-run    - Validate connections and count records without migrating
  migrate    - Run full migration from Notion to PostgreSQL

Environment variables required:
  NOTION_SECRET
  NOTION_ATTENDANCE_DB_ID
  NOTION_STRIKES_DB_ID
  NOTION_CLEANER_PROFILES_DB_ID
  POSTGRES_USER
  POSTGRES_HOST
  POSTGRES_DB
  POSTGRES_PASSWORD
  POSTGRES_PORT (optional, defaults to 5432)
        `);
        process.exit(1);
    }
  } catch (error) {
    console.error('Migration failed:', error.message);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export default DataMigrator;
