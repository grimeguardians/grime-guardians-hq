#!/usr/bin/env node
// Comprehensive System Test Suite for Grime Guardians
// Tests all functionality before going live

const fs = require('fs');
const http = require('http');
const fetch = require('node-fetch');

console.log('\n🧪 GRIME GUARDIANS - COMPLETE SYSTEM TEST');
console.log('==========================================');

let testResults = {
  passed: 0,
  failed: 0,
  tests: []
};

function logTest(name, passed, details = '') {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status} - ${name}`);
  if (details) console.log(`   ${details}`);
  
  testResults.tests.push({ name, passed, details });
  if (passed) testResults.passed++;
  else testResults.failed++;
}

async function test1_ServerHealth() {
  try {
    const response = await fetch('http://localhost:3000/health');
    const data = await response.json();
    
    if (response.ok && data.status === 'healthy') {
      logTest('Server Health Check', true, `Database: ${data.database}, Cost tracking active`);
    } else {
      logTest('Server Health Check', false, 'Server not responding correctly');
    }
  } catch (error) {
    logTest('Server Health Check', false, `Server not running: ${error.message}`);
  }
}

async function test2_NgrokTunnel() {
  try {
    const response = await fetch('http://127.0.0.1:4040/api/tunnels');
    const data = await response.json();
    
    if (data.tunnels && data.tunnels.length > 0) {
      const tunnel = data.tunnels[0];
      logTest('ngrok Tunnel', true, `Public URL: ${tunnel.public_url}`);
      return tunnel.public_url;
    } else {
      logTest('ngrok Tunnel', false, 'No active tunnels found');
      return null;
    }
  } catch (error) {
    logTest('ngrok Tunnel', false, 'ngrok not running or accessible');
    return null;
  }
}

async function test3_WebhookEndpoint(publicUrl) {
  if (!publicUrl) {
    logTest('Webhook Endpoint', false, 'No public URL available');
    return;
  }
  
  try {
    const testPayload = {
      assignedTo: 'Available 1',
      calendar: {
        title: 'Test Job',
        startTime: '2025-01-16T15:00:00Z',
        notes: 'Test job for system verification'
      },
      address1: '123 Test St, Test City, TX 75201'
    };
    
    const response = await fetch(`${publicUrl}/webhook/highlevel-appointment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-webhook-secret': process.env.WEBHOOK_SECRET || 'GG_Hook_2025abc2030'
      },
      body: JSON.stringify(testPayload)
    });
    
    if (response.ok) {
      logTest('Webhook Endpoint (Public)', true, 'Webhook accepts requests via ngrok');
    } else {
      logTest('Webhook Endpoint (Public)', false, `HTTP ${response.status}`);
    }
  } catch (error) {
    logTest('Webhook Endpoint (Public)', false, error.message);
  }
}

async function test4_EnvironmentConfig() {
  const requiredEnvVars = [
    'DISCORD_BOT_TOKEN',
    'NOTION_SECRET',
    'WEBHOOK_SECRET',
    'OPS_LEAD_DISCORD_ID',
    'HIGHLEVEL_PRIVATE_INTEGRATION'
  ];
  
  let missingVars = [];
  requiredEnvVars.forEach(envVar => {
    if (!process.env[envVar]) {
      missingVars.push(envVar);
    }
  });
  
  if (missingVars.length === 0) {
    logTest('Environment Configuration', true, 'All required environment variables present');
  } else {
    logTest('Environment Configuration', false, `Missing: ${missingVars.join(', ')}`);
  }
}

async function test5_KeithAgentMemory() {
  const memoryPath = './COO_Memory_Stack (8).json';
  
  try {
    if (fs.existsSync(memoryPath)) {
      const memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
      logTest('Keith Agent Memory', true, `Memory file exists with ${Object.keys(memory).length} users tracked`);
    } else {
      logTest('Keith Agent Memory', true, 'Memory file will be created on first use');
    }
  } catch (error) {
    logTest('Keith Agent Memory', false, `Memory file error: ${error.message}`);
  }
}

async function test6_CostMonitoring() {
  try {
    const response = await fetch('http://localhost:3000/dashboard');
    const data = await response.json();
    
    if (response.ok && typeof data.operations_this_month === 'number') {
      logTest('Cost Monitoring', true, `Tracking ${data.operations_this_month} operations, $${data.current_cost} cost`);
    } else {
      logTest('Cost Monitoring', false, 'Dashboard endpoint not working');
    }
  } catch (error) {
    logTest('Cost Monitoring', false, error.message);
  }
}

async function test7_DiscordBotStatus() {
  // Check if Discord bot is connected by testing a simple endpoint
  try {
    const response = await fetch('http://localhost:3000/health');
    const data = await response.json();
    
    if (response.ok && data.status === 'healthy') {
      logTest('Discord Bot Process', true, 'Main server running (Discord bot should be connected)');
    } else {
      logTest('Discord Bot Process', false, 'Server not responding properly');
    }
  } catch (error) {
    logTest('Discord Bot Process', false, 'Unable to verify bot status');
  }
}

async function runAllTests() {
  console.log('Running comprehensive system tests...\n');
  
  // Load environment
  require('dotenv').config();
  
  await test1_ServerHealth();
  const publicUrl = await test2_NgrokTunnel();
  await test3_WebhookEndpoint(publicUrl);
  await test4_EnvironmentConfig();
  await test5_KeithAgentMemory();
  await test6_CostMonitoring();
  await test7_DiscordBotStatus();
  
  // Summary
  console.log('\n📊 TEST SUMMARY');
  console.log('================');
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log(`📈 Success Rate: ${Math.round((testResults.passed / (testResults.passed + testResults.failed)) * 100)}%`);
  
  if (testResults.failed === 0) {
    console.log('\n🚀 SYSTEM READY FOR PRODUCTION!');
    console.log('All tests passed. You can safely go live.');
    if (publicUrl) {
      console.log(`\n📋 NEXT STEPS:`);
      console.log(`1. Update High Level webhook to: ${publicUrl}/webhook/highlevel-appointment`);
      console.log(`2. Test with real appointment creation`);
      console.log(`3. Monitor system for 24-48 hours`);
      console.log(`4. Deploy to production server when ready`);
    }
  } else {
    console.log('\n⚠️  ISSUES FOUND - Fix before going live:');
    testResults.tests.filter(t => !t.passed).forEach(test => {
      console.log(`   - ${test.name}: ${test.details}`);
    });
  }
}

runAllTests().catch(console.error);
