// Simple Cost Monitor for Grime Guardians
// Tracks database operations and provides cost insights

const fs = require('fs');
const path = require('path');

class SimpleCostMonitor {
  constructor() {
    this.operations = {
      daily: {},
      monthly: 0,
      currentMonth: new Date().toISOString().slice(0, 7)
    };
    
    this.costs = {
      notion: 0.005, // $0.005 per operation
      postgres: 15,  // $15/month fixed
      threshold: 30  // Migration trigger at $30/month
    };
    
    this.loadData();
  }

  loadData() {
    try {
      const dataFile = path.join(process.cwd(), 'cost_data.json');
      if (fs.existsSync(dataFile)) {
        const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
        
        // Reset if new month
        const currentMonth = new Date().toISOString().slice(0, 7);
        if (data.currentMonth !== currentMonth) {
          this.operations.monthly = 0;
          this.operations.daily = {};
          this.operations.currentMonth = currentMonth;
        } else {
          this.operations = { ...this.operations, ...data };
        }
      }
    } catch (error) {
      console.log('Cost monitor: Starting fresh');
    }
  }

  saveData() {
    try {
      const dataFile = path.join(process.cwd(), 'cost_data.json');
      fs.writeFileSync(dataFile, JSON.stringify(this.operations, null, 2));
    } catch (error) {
      // Ignore save errors in development
    }
  }

  logOperation(type = 'notion') {
    const today = new Date().toISOString().slice(0, 10);
    
    // Update counters
    this.operations.monthly++;
    if (!this.operations.daily[today]) {
      this.operations.daily[today] = 0;
    }
    this.operations.daily[today]++;
    
    // Save data
    this.saveData();
    
    // Check thresholds
    this.checkThresholds();
  }

  checkThresholds() {
    const currentCost = this.operations.monthly * this.costs.notion;
    
    if (currentCost >= this.costs.threshold) {
      console.log(`\n🚨 MIGRATION ALERT: Notion costs ($${currentCost.toFixed(2)}) exceed threshold ($${this.costs.threshold})`);
      console.log(`   → Consider migrating to PostgreSQL for cost savings`);
    }
  }

  getStats() {
    const currentCost = this.operations.monthly * this.costs.notion;
    const projected = (this.operations.monthly / new Date().getDate()) * 30 * this.costs.notion;
    
    return {
      operations_this_month: this.operations.monthly,
      current_cost: currentCost.toFixed(2),
      projected_monthly_cost: projected.toFixed(2),
      migration_recommended: projected >= this.costs.threshold
    };
  }

  printDashboard() {
    const stats = this.getStats();
    console.log('\n📊 COST DASHBOARD');
    console.log('==================');
    console.log(`Operations this month: ${stats.operations_this_month}`);
    console.log(`Current cost: $${stats.current_cost}`);
    console.log(`Projected monthly: $${stats.projected_monthly_cost}`);
    console.log(`Migration needed: ${stats.migration_recommended ? 'YES' : 'No'}`);
    console.log('==================\n');
  }
}

// Singleton
const costMonitor = new SimpleCostMonitor();

// Simple middleware
function costTrackingMiddleware(req, res, next) {
  // Track operation on response finish
  res.on('finish', () => {
    if (res.statusCode < 400) { // Only count successful operations
      costMonitor.logOperation('notion');
    }
  });
  next();
}

module.exports = {
  costMonitor,
  costTrackingMiddleware
};
