#!/usr/bin/env node
// Dashboard Command for Grime Guardians
// Usage: node scripts/dashboard.js

const { costMonitor } = require('../src/utils/simpleCostMonitor');
const http = require('http');

console.log('\n🎯 GRIME GUARDIANS DASHBOARD');
console.log('============================');

// Display cost dashboard
costMonitor.printDashboard();

// Also try to fetch from running server
function fetchServerStats() {
  const req = http.get('http://localhost:3000/dashboard', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      try {
        const stats = JSON.parse(data);
        console.log('📊 LIVE SERVER STATS');
        console.log('====================');
        console.log(`Operations: ${stats.operations_this_month}`);
        console.log(`Current cost: $${stats.current_cost}`);
        console.log(`Projected: $${stats.projected_monthly_cost}`);
        console.log(`Migration needed: ${stats.migration_recommended ? 'YES' : 'No'}`);
        console.log('====================\n');
      } catch (e) {
        console.log('💡 Note: Start server with `npm run start` for live stats\n');
      }
    });
  });
  
  req.on('error', () => {
    console.log('💡 Note: Start server with `npm run start` for live stats\n');
  });
  
  req.setTimeout(2000, () => {
    req.destroy();
    console.log('💡 Note: Start server with `npm run start` for live stats\n');
  });
}

fetchServerStats();
