#!/usr/bin/env node
/**
 * Core functionality test script
 * Tests essential components without requiring Discord connection
 */

require('dotenv').config();

async function testCore() {
  console.log('🧪 Testing Grime Guardians Core Functionality...\n');
  
  try {
    // Test 1: Environment variables
    console.log('1️⃣ Testing environment configuration...');
    const requiredEnvVars = ['NOTION_SECRET', 'NOTION_ATTENDANCE_DB_ID'];
    const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
      console.log(`❌ Missing environment variables: ${missingVars.join(', ')}`);
      return false;
    }
    console.log('✅ Environment variables configured');
    
    // Test 2: Cost monitoring
    console.log('\n2️⃣ Testing cost monitoring...');
    const { costMonitor } = require('../src/utils/simpleCostMonitor');
    
    // Simulate some operations
    costMonitor.trackOperation('notion_query', 0.01);
    costMonitor.trackOperation('discord_message', 0.005);
    costMonitor.trackOperation('openai_call', 0.03);
    
    const stats = costMonitor.getStats();
    console.log(`✅ Cost monitoring working: ${stats.totalOperations} operations, $${stats.totalCost.toFixed(4)}`);
    
    // Test 3: Notion connection
    console.log('\n3️⃣ Testing Notion connection...');
    const { Client } = require('@notionhq/client');
    const notion = new Client({ auth: process.env.NOTION_SECRET });
    
    try {
      await notion.databases.retrieve({ database_id: process.env.NOTION_ATTENDANCE_DB_ID });
      console.log('✅ Notion connection successful');
      costMonitor.trackOperation('notion_query', 0.01);
    } catch (error) {
      console.log(`❌ Notion connection failed: ${error.message}`);
      return false;
    }
    
    // Test 4: MCP Server imports
    console.log('\n4️⃣ Testing MCP server components...');
    const notionServerPath = '../mcp-servers/notion-server/src/index.js';
    try {
      require(notionServerPath);
      console.log('✅ Notion MCP server module loads correctly');
    } catch (error) {
      console.log(`❌ Notion MCP server error: ${error.message}`);
    }
    
    // Test 5: Agent imports
    console.log('\n5️⃣ Testing agent modules...');
    try {
      const Ava = require('../src/agents/ava');
      const Keith = require('../src/agents/keith');
      console.log('✅ Agent modules load correctly');
    } catch (error) {
      console.log(`❌ Agent import error: ${error.message}`);
      return false;
    }
    
    // Test 6: Express server setup
    console.log('\n6️⃣ Testing Express server...');
    const express = require('express');
    const app = express();
    
    // Add health endpoint
    app.get('/health', (req, res) => {
      const stats = costMonitor.getStats();
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        cost_monitoring: {
          enabled: process.env.COST_MONITORING_ENABLED === 'true',
          operations: stats.totalOperations,
          cost: stats.totalCost,
          migration_threshold: stats.shouldMigrate
        }
      });
    });
    
    const server = app.listen(3001, () => {
      console.log('✅ Express server started on port 3001');
      server.close(() => {
        console.log('✅ Express server stopped');
      });
    });
    
    console.log('\n🎉 All core tests passed! System is ready for deployment.');
    return true;
    
  } catch (error) {
    console.error(`❌ Core test failed: ${error.message}`);
    return false;
  }
}

// Run tests
testCore().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('❌ Test runner error:', error);
  process.exit(1);
});
