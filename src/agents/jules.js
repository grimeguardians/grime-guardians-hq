// Jules Agent - Analytics & Reporting Engine
// Generates KPI dashboards, trend analysis, and operational insights

const Agent = require('./agent');
const fs = require('fs');
const { logToNotion } = require('../utils/notion');
const { sendDiscordPing } = require('../utils/discord');

class Jules extends Agent {
  constructor(client) {
    super({ agentId: 'jules', role: 'Analytics & Reporting Engine' });
    this.client = client;
    this.analyticsCache = new Map();
    this.reportHistory = new Map();
    this.kpiMetrics = {
      punctuality: { target: 0.95, weight: 0.25 },
      quality: { target: 0.92, weight: 0.30 },
      client_satisfaction: { target: 0.90, weight: 0.25 },
      efficiency: { target: 0.85, weight: 0.20 }
    };
  }

  onReady() {
    console.log('📊 Jules agent is ready to analyze data and generate insights!');
    
    // Daily analytics at 7 AM
    this.scheduleDailyAnalytics();
    
    // Weekly comprehensive report on Sundays at 6 PM
    this.scheduleWeeklyReport();
    
    // Monthly trend analysis on the 1st at 9 AM
    this.scheduleMonthlyTrends();
  }

  async getContext(event) {
    return {
      event,
      currentMetrics: await this.getCurrentMetrics(),
      historicalData: await this.getHistoricalData(),
      benchmarks: this.getBenchmarks()
    };
  }

  async handleEvent(event, context) {
    const content = event.content.toLowerCase();
    
    // Handle report requests
    if (this.isReportRequest(content)) {
      return await this.generateRequestedReport(event, context);
    }

    // Handle analytics queries
    if (this.isAnalyticsQuery(content)) {
      return await this.handleAnalyticsQuery(event, context);
    }

    return null;
  }

  isReportRequest(content) {
    const indicators = [
      'report', 'analytics', 'dashboard', 'metrics', 'kpi',
      'performance summary', 'stats', 'data', 'trends'
    ];
    return indicators.some(indicator => content.includes(indicator));
  }

  isAnalyticsQuery(content) {
    const queries = [
      'how are we doing', 'performance', 'numbers',
      'team stats', 'cleaner performance', 'trends'
    ];
    return queries.some(query => content.includes(query));
  }

  async generateRequestedReport(event, context) {
    try {
      const reportType = await this.determineReportType(event.content);
      const report = await this.generateReport(reportType);
      
      // Send report
      await sendDiscordPing(this.client, event.channel.id, report.message);
      
      // Log report generation
      await this.logReportGenerated(reportType, report, event);
      
      return {
        agent_id: 'jules',
        task: 'report_generation',
        action_required: false,
        confidence: 0.9,
        report_type: reportType,
        message: 'Report generated and sent'
      };
      
    } catch (error) {
      console.error('[Jules] Error generating report:', error);
      return null;
    }
  }

  async handleAnalyticsQuery(event, context) {
    try {
      const insight = await this.generateQuickInsight(event.content, context);
      
      // Send insight
      await sendDiscordPing(this.client, event.channel.id, insight);
      
      return {
        agent_id: 'jules',
        task: 'analytics_query',
        action_required: false,
        confidence: 0.85,
        message: 'Analytics insight provided'
      };
      
    } catch (error) {
      console.error('[Jules] Error handling analytics query:', error);
      return null;
    }
  }

  async generateDailyReport() {
    console.log('[Jules] Generating daily analytics report...');
    
    try {
      const analytics = await this.calculateDailyMetrics();
      const report = await this.formatDailyReport(analytics);
      
      // Send to operations channel
      const opsChannelId = process.env.OPS_CHANNEL_ID || process.env.DISCORD_JOB_BOARD_CHANNEL_ID;
      await sendDiscordPing(this.client, opsChannelId, report);
      
      // Cache analytics
      this.analyticsCache.set(`daily_${Date.now()}`, analytics);
      
      return {
        agent_id: 'jules',
        task: 'daily_report',
        action_required: false,
        confidence: 0.9,
        message: 'Daily report generated'
      };
      
    } catch (error) {
      console.error('[Jules] Error generating daily report:', error);
      return null;
    }
  }

  async generateWeeklyReport() {
    console.log('[Jules] Generating weekly comprehensive report...');
    
    try {
      const analytics = await this.calculateWeeklyMetrics();
      const report = await this.formatWeeklyReport(analytics);
      
      // Send to operations channel
      const opsChannelId = process.env.OPS_CHANNEL_ID || process.env.DISCORD_JOB_BOARD_CHANNEL_ID;
      await sendDiscordPing(this.client, opsChannelId, report);
      
      // Log comprehensive analytics
      await this.logWeeklyAnalytics(analytics);
      
      return {
        agent_id: 'jules',
        task: 'weekly_report',
        action_required: false,
        confidence: 0.95,
        message: 'Weekly report generated'
      };
      
    } catch (error) {
      console.error('[Jules] Error generating weekly report:', error);
      return null;
    }
  }

  async generateMonthlyTrends() {
    console.log('[Jules] Generating monthly trend analysis...');
    
    try {
      const trends = await this.calculateMonthlyTrends();
      const report = await this.formatTrendReport(trends);
      
      // Send to operations channel
      const opsChannelId = process.env.OPS_CHANNEL_ID || process.env.DISCORD_JOB_BOARD_CHANNEL_ID;
      await sendDiscordPing(this.client, opsChannelId, report);
      
      // Log trend analysis
      await this.logTrendAnalysis(trends);
      
      return {
        agent_id: 'jules',
        task: 'monthly_trends',
        action_required: true,
        confidence: 0.95,
        message: 'Monthly trend analysis completed'
      };
      
    } catch (error) {
      console.error('[Jules] Error generating monthly trends:', error);
      return null;
    }
  }

  async calculateDailyMetrics() {
    const today = new Date();
    const startOfDay = new Date(today.setHours(0, 0, 0, 0));
    
    // Collect data from all agent operations
    const data = await this.collectOperationalData(startOfDay, new Date());
    
    return {
      date: startOfDay.toISOString().split('T')[0],
      jobs_completed: data.jobs?.completed || 0,
      jobs_scheduled: data.jobs?.scheduled || 0,
      punctuality_rate: this.calculatePunctualityRate(data.checkins),
      quality_score: this.calculateQualityScore(data.completions),
      agent_activity: this.calculateAgentActivity(data.agent_logs),
      alerts_generated: data.alerts?.length || 0,
      escalations: data.escalations?.length || 0,
      revenue_generated: this.calculateRevenue(data.jobs?.completed),
      efficiency_score: this.calculateEfficiencyScore(data)
    };
  }

  async calculateWeeklyMetrics() {
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - (7 * 24 * 60 * 60 * 1000));
    
    const data = await this.collectOperationalData(startDate, endDate);
    
    // Calculate weekly aggregates
    const weeklyMetrics = {
      week_ending: endDate.toISOString().split('T')[0],
      total_jobs: data.jobs?.completed || 0,
      total_revenue: this.calculateRevenue(data.jobs?.completed),
      avg_punctuality: this.calculatePunctualityRate(data.checkins),
      avg_quality: this.calculateQualityScore(data.completions),
      cleaner_performance: await this.calculateCleanerPerformance(data),
      client_satisfaction: this.calculateClientSatisfaction(data),
      operational_efficiency: this.calculateOperationalEfficiency(data),
      growth_metrics: await this.calculateGrowthMetrics(startDate, endDate),
      top_performers: await this.identifyTopPerformers(data),
      improvement_areas: await this.identifyImprovementAreas(data)
    };

    return weeklyMetrics;
  }

  async calculateMonthlyTrends() {
    const endDate = new Date();
    const startDate = new Date(endDate.getFullYear(), endDate.getMonth() - 3, 1); // 3 months back
    
    const data = await this.collectOperationalData(startDate, endDate);
    
    return {
      period: `${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}`,
      revenue_trend: await this.calculateRevenueTrend(data),
      performance_trends: await this.calculatePerformanceTrends(data),
      client_retention: await this.calculateClientRetention(data),
      operational_trends: await this.calculateOperationalTrends(data),
      seasonal_patterns: await this.identifySeasonalPatterns(data),
      predictive_insights: await this.generatePredictiveInsights(data),
      recommendations: await this.generateStrategicRecommendations(data)
    };
  }

  async formatDailyReport(analytics) {
    const { date, jobs_completed, punctuality_rate, quality_score, efficiency_score } = analytics;
    
    return `📊 **Daily Operations Report - ${date}**\n\n` +
      `**📈 Key Metrics:**\n` +
      `• **Jobs Completed**: ${jobs_completed}\n` +
      `• **Punctuality Rate**: ${(punctuality_rate * 100).toFixed(1)}%\n` +
      `• **Quality Score**: ${(quality_score * 100).toFixed(1)}%\n` +
      `• **Efficiency Score**: ${(efficiency_score * 100).toFixed(1)}%\n\n` +
      `**🤖 Agent Activity:**\n` +
      `${this.formatAgentActivity(analytics.agent_activity)}\n\n` +
      `**⚠️ Alerts & Escalations:**\n` +
      `• Alerts Generated: ${analytics.alerts_generated}\n` +
      `• Escalations: ${analytics.escalations}\n\n` +
      `${this.getPerformanceEmoji(analytics)} **Overall Performance**: ${this.getPerformanceStatus(analytics)}`;
  }

  async formatWeeklyReport(analytics) {
    const { week_ending, total_jobs, total_revenue, avg_punctuality, avg_quality } = analytics;
    
    return `📊 **Weekly Performance Report - Week Ending ${week_ending}**\n\n` +
      `**💼 Business Metrics:**\n` +
      `• **Total Jobs**: ${total_jobs}\n` +
      `• **Revenue Generated**: $${total_revenue.toLocaleString()}\n` +
      `• **Average Job Value**: $${(total_revenue / total_jobs).toFixed(2)}\n\n` +
      `**⭐ Performance Metrics:**\n` +
      `• **Punctuality Rate**: ${(avg_punctuality * 100).toFixed(1)}%\n` +
      `• **Quality Score**: ${(avg_quality * 100).toFixed(1)}%\n` +
      `• **Client Satisfaction**: ${(analytics.client_satisfaction * 100).toFixed(1)}%\n\n` +
      `**🏆 Top Performers:**\n` +
      `${this.formatTopPerformers(analytics.top_performers)}\n\n` +
      `**🎯 Areas for Improvement:**\n` +
      `${this.formatImprovementAreas(analytics.improvement_areas)}\n\n` +
      `**📈 Growth Metrics:**\n` +
      `${this.formatGrowthMetrics(analytics.growth_metrics)}`;
  }

  async formatTrendReport(trends) {
    return `📈 **Monthly Trends & Strategic Insights**\n\n` +
      `**💰 Revenue Trends:**\n` +
      `${this.formatRevenueTrend(trends.revenue_trend)}\n\n` +
      `**📊 Performance Trends:**\n` +
      `${this.formatPerformanceTrends(trends.performance_trends)}\n\n` +
      `**🔮 Predictive Insights:**\n` +
      `${this.formatPredictiveInsights(trends.predictive_insights)}\n\n` +
      `**💡 Strategic Recommendations:**\n` +
      `${this.formatRecommendations(trends.recommendations)}`;
  }

  // Utility calculation methods
  calculatePunctualityRate(checkins) {
    if (!checkins || checkins.length === 0) return 0;
    const onTime = checkins.filter(c => !c.late).length;
    return onTime / checkins.length;
  }

  calculateQualityScore(completions) {
    if (!completions || completions.length === 0) return 0;
    const totalScore = completions.reduce((sum, c) => sum + (c.quality_score || 0.8), 0);
    return totalScore / completions.length;
  }

  calculateEfficiencyScore(data) {
    // Composite efficiency based on multiple factors
    const factors = {
      time_efficiency: data.avg_job_time / data.target_job_time || 0.8,
      resource_utilization: data.jobs_completed / data.jobs_scheduled || 0.9,
      automation_impact: data.automated_actions / data.total_actions || 0.7
    };
    
    return Object.values(factors).reduce((sum, val) => sum + val, 0) / Object.keys(factors).length;
  }

  calculateRevenue(jobsCompleted) {
    // Estimate revenue based on average job value
    const avgJobValue = 135; // Based on current pricing
    return jobsCompleted * avgJobValue;
  }

  async collectOperationalData(startDate, endDate) {
    try {
      // Collect data from COO Memory Stack
      const cooMemoryPath = '/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ/COO_Memory_Stack (8).json';
      
      let cooData = {};
      if (fs.existsSync(cooMemoryPath)) {
        const rawData = fs.readFileSync(cooMemoryPath, 'utf8');
        cooData = JSON.parse(rawData);
      }

      // Filter data by date range
      const filteredData = this.filterDataByDateRange(cooData, startDate, endDate);
      
      return {
        jobs: filteredData.jobs || {},
        checkins: filteredData.checkins || [],
        completions: filteredData.completions || [],
        agent_logs: filteredData.agent_logs || [],
        alerts: filteredData.alerts || [],
        escalations: filteredData.escalations || []
      };
      
    } catch (error) {
      console.error('[Jules] Error collecting operational data:', error);
      return {};
    }
  }

  filterDataByDateRange(data, startDate, endDate) {
    // Filter COO data by date range
    // This would need to be customized based on your actual data structure
    return data;
  }

  // Scheduling methods
  scheduleDailyAnalytics() {
    const scheduleTime = new Date();
    scheduleTime.setHours(7, 0, 0, 0); // 7 AM daily
    
    const msUntilNext = scheduleTime.getTime() - Date.now();
    const msInDay = 24 * 60 * 60 * 1000;
    
    setTimeout(() => {
      this.generateDailyReport();
      setInterval(() => {
        this.generateDailyReport();
      }, msInDay);
    }, msUntilNext > 0 ? msUntilNext : msUntilNext + msInDay);
  }

  scheduleWeeklyReport() {
    const scheduleTime = new Date();
    scheduleTime.setDate(scheduleTime.getDate() + (7 - scheduleTime.getDay())); // Next Sunday
    scheduleTime.setHours(18, 0, 0, 0); // 6 PM
    
    const msUntilNext = scheduleTime.getTime() - Date.now();
    const msInWeek = 7 * 24 * 60 * 60 * 1000;
    
    setTimeout(() => {
      this.generateWeeklyReport();
      setInterval(() => {
        this.generateWeeklyReport();
      }, msInWeek);
    }, msUntilNext > 0 ? msUntilNext : msUntilNext + msInWeek);
  }

  scheduleMonthlyTrends() {
    const scheduleTime = new Date();
    scheduleTime.setMonth(scheduleTime.getMonth() + 1, 1); // First of next month
    scheduleTime.setHours(9, 0, 0, 0); // 9 AM
    
    const msUntilNext = scheduleTime.getTime() - Date.now();
    
    setTimeout(() => {
      this.generateMonthlyTrends();
      setInterval(() => {
        this.generateMonthlyTrends();
      }, 30 * 24 * 60 * 60 * 1000); // Approximately monthly
    }, msUntilNext);
  }

  // Formatting helper methods
  formatAgentActivity(activity) {
    if (!activity || Object.keys(activity).length === 0) {
      return '• No agent activity recorded';
    }
    
    return Object.entries(activity)
      .map(([agent, count]) => `• ${agent}: ${count} actions`)
      .join('\n');
  }

  getPerformanceEmoji(analytics) {
    const overall = (analytics.punctuality_rate + analytics.quality_score + analytics.efficiency_score) / 3;
    if (overall >= 0.9) return '🟢';
    if (overall >= 0.75) return '🟡';
    return '🔴';
  }

  getPerformanceStatus(analytics) {
    const overall = (analytics.punctuality_rate + analytics.quality_score + analytics.efficiency_score) / 3;
    if (overall >= 0.9) return 'Excellent';
    if (overall >= 0.75) return 'Good';
    return 'Needs Improvement';
  }

  async getCurrentMetrics() {
    return await this.calculateDailyMetrics();
  }

  async getHistoricalData() {
    return Array.from(this.analyticsCache.entries()).slice(-30); // Last 30 entries
  }

  getBenchmarks() {
    return this.kpiMetrics;
  }

  async logReportGenerated(reportType, report, event) {
    await logToNotion('reports_generated', {
      agent: 'jules',
      report_type: reportType,
      generated_at: new Date().toISOString(),
      channel_id: event.channel.id
    });
  }

  async logWeeklyAnalytics(analytics) {
    await logToNotion('weekly_analytics', {
      agent: 'jules',
      analytics_data: analytics,
      generated_at: new Date().toISOString()
    });
  }

  async logTrendAnalysis(trends) {
    await logToNotion('trend_analysis', {
      agent: 'jules',
      trends_data: trends,
      generated_at: new Date().toISOString()
    });
  }
}

module.exports = Jules;
