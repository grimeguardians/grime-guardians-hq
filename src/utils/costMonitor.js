// Database Cost Monitor
// Tracks and reports database operation costs for decision making

const fs = require('fs');
const path = require('path');

export class CostMonitor {
  constructor() {
    this.costData = {
      notion: {
        operations: 0,
        estimatedCost: 0,
        costPerOperation: 0.005 // $0.005 per operation estimate
      },
      postgres: {
        operations: 0,
        estimatedCost: 0,
        fixedMonthlyCost: 15, // $15/month for hosted PostgreSQL
        costPerOperation: 0.0001 // Negligible per-operation cost
      },
      currentMonth: new Date().toISOString().slice(0, 7), // YYYY-MM
      dailyOperations: {},
      migrationThresholds: {
        costThreshold: 30, // Migrate when Notion costs exceed $30/month
        operationThreshold: 1500, // Migrate when operations exceed 1500/month
        performanceThreshold: 2000 // Migrate when avg response time > 2000ms
      }
    };
    
    this.loadData();
    this.startDailyReset();
  }

  loadData() {
    try {
      const dataPath = path.join(process.cwd(), 'cost_monitor_data.json');
      if (fs.existsSync(dataPath)) {
        const savedData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
        
        // Reset if it's a new month
        const currentMonth = new Date().toISOString().slice(0, 7);
        if (savedData.currentMonth !== currentMonth) {
          console.log(`📊 New month detected (${currentMonth}), resetting cost counters`);
          this.resetMonthlyCounters();
        } else {
          this.costData = { ...this.costData, ...savedData };
        }
      }
    } catch (error) {
      console.warn('Could not load cost data:', error.message);
    }
  }

  saveData() {
    try {
      const dataPath = path.join(process.cwd(), 'cost_monitor_data.json');
      fs.writeFileSync(dataPath, JSON.stringify(this.costData, null, 2));
    } catch (error) {
      console.error('Could not save cost data:', error.message);
    }
  }

  resetMonthlyCounters() {
    this.costData.currentMonth = new Date().toISOString().slice(0, 7);
    this.costData.notion.operations = 0;
    this.costData.notion.estimatedCost = 0;
    this.costData.postgres.operations = 0;
    this.costData.postgres.estimatedCost = this.costData.postgres.fixedMonthlyCost;
    this.costData.dailyOperations = {};
  }

  startDailyReset() {
    // Check every hour if we need to reset for a new month
    setInterval(() => {
      const currentMonth = new Date().toISOString().slice(0, 7);
      if (this.costData.currentMonth !== currentMonth) {
        this.resetMonthlyCounters();
        this.saveData();
      }
    }, 60 * 60 * 1000); // 1 hour
  }

  logOperation(database, operationType = 'read', responseTime = 0) {
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    
    // Initialize daily operations if needed
    if (!this.costData.dailyOperations[today]) {
      this.costData.dailyOperations[today] = {
        notion: 0,
        postgres: 0,
        avgResponseTime: 0,
        totalResponseTime: 0
      };
    }

    const dailyData = this.costData.dailyOperations[today];
    
    if (database === 'notion') {
      this.costData.notion.operations++;
      this.costData.notion.estimatedCost += this.costData.notion.costPerOperation;
      dailyData.notion++;
    } else if (database === 'postgres') {
      this.costData.postgres.operations++;
      this.costData.postgres.estimatedCost = this.costData.postgres.fixedMonthlyCost;
      dailyData.postgres++;
    }

    // Track response times
    dailyData.totalResponseTime += responseTime;
    const totalOps = dailyData.notion + dailyData.postgres;
    dailyData.avgResponseTime = totalOps > 0 ? dailyData.totalResponseTime / totalOps : 0;

    this.saveData();
    
    // Check thresholds
    this.checkMigrationThresholds();
  }

  checkMigrationThresholds() {
    const { migrationThresholds } = this.costData;
    const currentNotionCost = this.costData.notion.estimatedCost;
    const currentOperations = this.costData.notion.operations + this.costData.postgres.operations;
    const currentAvgResponseTime = this.getCurrentAvgResponseTime();

    let recommendations = [];

    // Cost threshold check
    if (currentNotionCost >= migrationThresholds.costThreshold) {
      recommendations.push({
        type: 'COST_THRESHOLD_EXCEEDED',
        message: `Notion costs (${currentNotionCost.toFixed(2)}) exceed threshold ($${migrationThresholds.costThreshold})`,
        severity: 'HIGH',
        action: 'Consider migrating to PostgreSQL'
      });
    }

    // Operations threshold check
    if (currentOperations >= migrationThresholds.operationThreshold) {
      recommendations.push({
        type: 'OPERATION_THRESHOLD_EXCEEDED',
        message: `Monthly operations (${currentOperations}) exceed threshold (${migrationThresholds.operationThreshold})`,
        severity: 'MEDIUM',
        action: 'Evaluate migration to PostgreSQL for cost efficiency'
      });
    }

    // Performance threshold check
    if (currentAvgResponseTime >= migrationThresholds.performanceThreshold) {
      recommendations.push({
        type: 'PERFORMANCE_THRESHOLD_EXCEEDED',
        message: `Average response time (${currentAvgResponseTime.toFixed(0)}ms) exceeds threshold (${migrationThresholds.performanceThreshold}ms)`,
        severity: 'HIGH',
        action: 'Consider PostgreSQL for better performance'
      });
    }

    // Log recommendations if any
    if (recommendations.length > 0 && process.env.NODE_ENV === 'production') {
      console.log('🚨 MIGRATION RECOMMENDATIONS:');
      recommendations.forEach(rec => {
        console.log(`   ${rec.severity}: ${rec.message}`);
        console.log(`   → ${rec.action}`);
      });
    }

    return recommendations;
  }

  getCurrentAvgResponseTime() {
    const recentDays = Object.keys(this.costData.dailyOperations)
      .sort()
      .slice(-7); // Last 7 days
    
    if (recentDays.length === 0) return 0;
    
    const totalResponseTime = recentDays.reduce((sum, day) => {
      return sum + (this.costData.dailyOperations[day]?.avgResponseTime || 0);
    }, 0);
    
    return totalResponseTime / recentDays.length;
  }

  generateCostReport() {
    const report = {
      period: this.costData.currentMonth,
      current_costs: {
        notion: {
          operations: this.costData.notion.operations,
          estimated_cost: this.costData.notion.estimatedCost.toFixed(2),
          cost_per_operation: this.costData.notion.costPerOperation
        },
        postgres: {
          operations: this.costData.postgres.operations,
          estimated_cost: this.costData.postgres.estimatedCost.toFixed(2),
          fixed_monthly_cost: this.costData.postgres.fixedMonthlyCost
        }
      },
      projections: this.generateProjections(),
      recommendations: this.checkMigrationThresholds(),
      daily_breakdown: this.costData.dailyOperations
    };

    return report;
  }

  generateProjections() {
    const daysInMonth = new Date().getDate();
    const daysRemaining = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate() - daysInMonth;
    
    const dailyAvgOperations = this.costData.notion.operations / daysInMonth;
    const projectedMonthlyOperations = dailyAvgOperations * 30;
    const projectedMonthlyCost = projectedMonthlyOperations * this.costData.notion.costPerOperation;

    return {
      projected_monthly_operations: Math.round(projectedMonthlyOperations),
      projected_monthly_cost_notion: projectedMonthlyCost.toFixed(2),
      projected_monthly_cost_postgres: this.costData.postgres.fixedMonthlyCost.toFixed(2),
      break_even_operations: Math.round(this.costData.postgres.fixedMonthlyCost / this.costData.notion.costPerOperation),
      savings_if_migrated: Math.max(0, projectedMonthlyCost - this.costData.postgres.fixedMonthlyCost).toFixed(2),
      days_until_break_even: daysRemaining > 0 ? Math.ceil((this.costData.postgres.fixedMonthlyCost - this.costData.notion.estimatedCost) / (dailyAvgOperations * this.costData.notion.costPerOperation)) : 0
    };
  }

  async generateDashboard() {
    const report = this.generateCostReport();
    
    console.log('\n📊 DATABASE COST DASHBOARD');
    console.log('=' .repeat(50));
    console.log(`Period: ${report.period}`);
    console.log(`\n💰 Current Costs:`);
    console.log(`   Notion: $${report.current_costs.notion.estimated_cost} (${report.current_costs.notion.operations} operations)`);
    console.log(`   PostgreSQL: $${report.current_costs.postgres.estimated_cost} (${report.current_costs.postgres.operations} operations)`);
    
    console.log(`\n📈 Projections:`);
    console.log(`   Monthly Operations: ${report.projections.projected_monthly_operations}`);
    console.log(`   Monthly Cost (Notion): $${report.projections.projected_monthly_cost_notion}`);
    console.log(`   Monthly Cost (PostgreSQL): $${report.projections.projected_monthly_cost_postgres}`);
    console.log(`   Potential Savings: $${report.projections.savings_if_migrated}`);
    
    if (report.recommendations.length > 0) {
      console.log(`\n⚠️  Recommendations:`);
      report.recommendations.forEach(rec => {
        console.log(`   ${rec.type}: ${rec.action}`);
      });
    }
    
    console.log('=' .repeat(50));
    
    return report;
  }

  // Utility methods for integration
  startOperation(database) {
    return {
      database,
      startTime: Date.now(),
      end: () => {
        const responseTime = Date.now() - this.startTime;
        this.logOperation(database, 'operation', responseTime);
        return responseTime;
      }
    };
  }
}

// Singleton instance
const costMonitor = new CostMonitor();

// Express middleware for automatic cost tracking
function costTrackingMiddleware(req, res, next) {
  const operation = costMonitor.startOperation(req.headers['x-database-type'] || 'notion');
  
  res.on('finish', () => {
    operation.end();
  });
  
  next();
}

module.exports = {
  CostMonitor,
  costMonitor,
  costTrackingMiddleware
};
