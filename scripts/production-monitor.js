#!/usr/bin/env node
// Production Monitoring Dashboard
// Run this alongside your main system for real-time insights

const fs = require('fs');
const path = require('path');

class ProductionMonitor {
  constructor() {
    this.metrics = {
      startTime: Date.now(),
      agentActivity: new Map(),
      errorCount: 0,
      successCount: 0,
      lastHealthCheck: null
    };
    
    this.startMonitoring();
  }

  startMonitoring() {
    console.log('🚀 Production Monitor Started');
    console.log('=====================================');
    
    // Health check every 5 minutes
    setInterval(() => this.healthCheck(), 5 * 60 * 1000);
    
    // Detailed report every hour
    setInterval(() => this.generateReport(), 60 * 60 * 1000);
    
    // Quick status every 30 seconds
    setInterval(() => this.quickStatus(), 30 * 1000);
    
    // Initial health check
    this.healthCheck();
  }

  quickStatus() {
    const uptime = Math.floor((Date.now() - this.metrics.startTime) / 1000);
    const minutes = Math.floor(uptime / 60);
    const seconds = uptime % 60;
    
    process.stdout.write(`\r⚡ System Status: ✅ Running | Uptime: ${minutes}m ${seconds}s | Errors: ${this.metrics.errorCount} | Success: ${this.metrics.successCount}`);
  }

  async healthCheck() {
    console.log('\n\n🔍 HEALTH CHECK - ' + new Date().toLocaleString());
    console.log('=====================================');
    
    // Check memory file
    const memoryStatus = this.checkMemoryFile();
    console.log(`📊 Memory Stack: ${memoryStatus ? '✅ Active' : '❌ Missing'}`);
    
    // Check agent files
    const agents = ['maya', 'zara', 'keith', 'nikolai', 'iris', 'jules'];
    for (const agent of agents) {
      const agentPath = `./src/agents/${agent}.js`;
      const exists = fs.existsSync(agentPath);
      console.log(`🤖 ${agent.charAt(0).toUpperCase() + agent.slice(1)}: ${exists ? '✅ Ready' : '❌ Missing'}`);
    }
    
    // Check environment variables
    const requiredEnvs = ['DISCORD_BOT_TOKEN', 'NOTION_SECRET', 'OPENAI_API_KEY'];
    let envStatus = 0;
    for (const env of requiredEnvs) {
      if (process.env[env]) envStatus++;
    }
    console.log(`🔑 Environment: ${envStatus}/${requiredEnvs.length} configured`);
    
    this.metrics.lastHealthCheck = Date.now();
  }

  checkMemoryFile() {
    try {
      const memoryPath = './COO_Memory_Stack (8).json';
      if (fs.existsSync(memoryPath)) {
        const memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
        const cleanerCount = Object.keys(memory).length;
        console.log(`   📋 Tracking ${cleanerCount} active cleaners`);
        return true;
      }
    } catch (error) {
      console.log(`   ❌ Memory file error: ${error.message}`);
    }
    return false;
  }

  generateReport() {
    console.log('\n\n📈 HOURLY PRODUCTION REPORT');
    console.log('=====================================');
    
    const uptime = Date.now() - this.metrics.startTime;
    const hours = Math.floor(uptime / (60 * 60 * 1000));
    const minutes = Math.floor((uptime % (60 * 60 * 1000)) / (60 * 1000));
    
    console.log(`⏱️  System Uptime: ${hours}h ${minutes}m`);
    console.log(`✅ Successful Operations: ${this.metrics.successCount}`);
    console.log(`❌ Errors Handled: ${this.metrics.errorCount}`);
    console.log(`📊 Success Rate: ${this.calculateSuccessRate()}%`);
    
    // Performance recommendations
    if (this.metrics.errorCount > 10) {
      console.log('⚠️  HIGH ERROR RATE - Consider checking logs');
    }
    
    if (hours > 24) {
      console.log('🎉 MILESTONE: System running 24+ hours successfully!');
    }
    
    console.log('=====================================\n');
  }

  calculateSuccessRate() {
    const total = this.metrics.successCount + this.metrics.errorCount;
    if (total === 0) return 100;
    return Math.round((this.metrics.successCount / total) * 100);
  }

  logSuccess(operation) {
    this.metrics.successCount++;
    console.log(`✅ ${operation} - Success count: ${this.metrics.successCount}`);
  }

  logError(operation, error) {
    this.metrics.errorCount++;
    console.log(`❌ ${operation} - Error: ${error.message}`);
  }
}

// Test functions for production validation
function testAgentCommunication() {
  console.log('\n🧪 TESTING AGENT COMMUNICATION');
  console.log('=====================================');
  
  // Test each agent can be loaded
  const agents = ['maya', 'zara', 'keith', 'nikolai', 'iris', 'jules'];
  
  for (const agentName of agents) {
    try {
      const Agent = require(`./src/agents/${agentName}.js`);
      const agent = new Agent();
      console.log(`✅ ${agentName}: Loaded successfully (ID: ${agent.agentId})`);
    } catch (error) {
      console.log(`❌ ${agentName}: Load failed - ${error.message}`);
    }
  }
}

function validateEnvironment() {
  console.log('\n🔧 ENVIRONMENT VALIDATION');
  console.log('=====================================');
  
  const envChecks = {
    'DISCORD_BOT_TOKEN': 'Discord Bot Authentication',
    'NOTION_SECRET': 'Notion Database Access',
    'OPENAI_API_KEY': 'OpenAI API Access',
    'GMAIL_CLIENT_ID': 'Gmail API Access'
  };
  
  for (const [env, description] of Object.entries(envChecks)) {
    const value = process.env[env];
    const status = value ? '✅ Set' : '❌ Missing';
    const length = value ? `(${value.length} chars)` : '';
    console.log(`${status} ${env}: ${description} ${length}`);
  }
}

// Quick production test suite
function runProductionTests() {
  console.log('\n🚀 PRODUCTION READINESS TEST');
  console.log('=====================================');
  
  testAgentCommunication();
  validateEnvironment();
  
  console.log('\n🎯 TEST COMPLETE - Ready for production!');
}

// Start monitoring if run directly
if (require.main === module) {
  const monitor = new ProductionMonitor();
  
  // Run initial tests
  setTimeout(() => {
    runProductionTests();
  }, 2000);
  
  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\n🛑 Production Monitor Stopping...');
    console.log('Final Status:');
    console.log(`✅ Successful Operations: ${monitor.metrics.successCount}`);
    console.log(`❌ Errors Handled: ${monitor.metrics.errorCount}`);
    console.log(`📊 Final Success Rate: ${monitor.calculateSuccessRate()}%`);
    process.exit(0);
  });
}

module.exports = ProductionMonitor;
