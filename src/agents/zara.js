// Zara Agent - Bonus & Performance Engine
// Calculates weekly bonuses and KPI scores based on Keith's strike data

const Agent = require('./agent');
const fs = require('fs');
const { logToNotion } = require('../utils/notion');
const { sendDiscordPing, createMentionFromUsername } = require('../utils/discord');

class Zara extends Agent {
  constructor(client) {
    super({ agentId: 'zara', role: 'Bonus & Performance Engine' });
    this.client = client;
    this.bonusHistory = new Map();
    this.kpiThresholds = {
      punctuality: { excellent: 0.95, good: 0.85, fair: 0.70 },
      quality: { excellent: 0.98, good: 0.90, fair: 0.80 },
      streak: { excellent: 14, good: 7, fair: 3 }
    };
  }

  onReady() {
    console.log('💰 Zara agent is ready to calculate bonuses and track performance!');
    
    // Schedule weekly bonus calculations for Sunday evenings
    this.scheduleWeeklyBonusCalculation();
    
    // Daily performance check at 6 PM
    this.scheduleDailyPerformanceCheck();
  }

  async getContext(event) {
    return { event };
  }

  async handleEvent(event, context) {
    // Zara primarily works on scheduled intervals, not reactive events
    return null;
  }

  async calculateWeeklyBonuses() {
    console.log('[Zara] Starting weekly bonus calculations...');
    
    const cleaners = await this.getActiveCleaners();
    const bonusReport = [];
    
    for (const cleaner of cleaners) {
      const performance = await this.calculateWeeklyPerformance(cleaner);
      const bonus = await this.calculateBonus(cleaner, performance);
      
      bonusReport.push({
        cleaner,
        performance,
        bonus,
        timestamp: new Date().toISOString()
      });

      // Log to Notion for record keeping
      await this.logBonusCalculation(cleaner, performance, bonus);
    }

    // Send bonus report to management
    await this.sendBonusReport(bonusReport);
    
    return bonusReport;
  }

  async calculateWeeklyPerformance(cleaner) {
    const memoryPath = './COO_Memory_Stack (8).json';
    let memory = {};
    
    try {
      if (fs.existsSync(memoryPath)) {
        memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
      }
    } catch (error) {
      console.error(`[Zara] Error reading memory for ${cleaner}:`, error);
      return this.getDefaultPerformance();
    }

    const cleanerMemory = memory[cleaner] || { punctuality: [], quality: [] };
    
    // Calculate 7-day performance window
    const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    
    const recentPunctualityStrikes = cleanerMemory.punctuality
      .filter(strike => new Date(strike.timestamp).getTime() >= weekAgo);
    
    const recentQualityStrikes = cleanerMemory.quality
      .filter(strike => new Date(strike.timestamp).getTime() >= weekAgo);

    // Estimate jobs completed (placeholder - could integrate with High Level data)
    const estimatedJobs = Math.floor(Math.random() * 5) + 3; // 3-7 jobs per week
    
    // Calculate performance scores
    const punctualityScore = Math.max(0, (estimatedJobs - recentPunctualityStrikes.length) / estimatedJobs);
    const qualityScore = Math.max(0, (estimatedJobs - recentQualityStrikes.length) / estimatedJobs);
    
    // Calculate current streak (days without any strikes)
    const allStrikes = [...cleanerMemory.punctuality, ...cleanerMemory.quality]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    const streak = allStrikes.length > 0 
      ? Math.floor((Date.now() - new Date(allStrikes[0].timestamp)) / (24 * 60 * 60 * 1000))
      : 30; // Max streak if no strikes

    return {
      cleaner,
      period: this.getCurrentWeekPeriod(),
      jobsCompleted: estimatedJobs,
      punctualityScore: Math.round(punctualityScore * 100) / 100,
      qualityScore: Math.round(qualityScore * 100) / 100,
      currentStreak: Math.min(streak, 30),
      punctualityStrikes: recentPunctualityStrikes.length,
      qualityStrikes: recentQualityStrikes.length,
      overallScore: Math.round(((punctualityScore + qualityScore) / 2) * 100) / 100
    };
  }

  async calculateBonus(cleaner, performance) {
    const baseRate = 45; // $45 per job base rate
    const { jobsCompleted, punctualityScore, qualityScore, currentStreak } = performance;
    
    let bonus = {
      base: jobsCompleted * baseRate,
      punctualityBonus: 0,
      qualityBonus: 0,
      streakBonus: 0,
      total: 0,
      eligible: true,
      tier: 'standard'
    };

    // Punctuality bonus
    if (punctualityScore >= this.kpiThresholds.punctuality.excellent) {
      bonus.punctualityBonus = jobsCompleted * 10; // $10 per job
      bonus.tier = 'excellent';
    } else if (punctualityScore >= this.kpiThresholds.punctuality.good) {
      bonus.punctualityBonus = jobsCompleted * 5; // $5 per job
      bonus.tier = 'good';
    }

    // Quality bonus
    if (qualityScore >= this.kpiThresholds.quality.excellent) {
      bonus.qualityBonus = jobsCompleted * 15; // $15 per job for excellent quality
    } else if (qualityScore >= this.kpiThresholds.quality.good) {
      bonus.qualityBonus = jobsCompleted * 8; // $8 per job for good quality
    }

    // Streak bonus (consecutive days without strikes)
    if (currentStreak >= this.kpiThresholds.streak.excellent) {
      bonus.streakBonus = 100; // $100 for 2+ week streak
    } else if (currentStreak >= this.kpiThresholds.streak.good) {
      bonus.streakBonus = 50; // $50 for 1 week streak
    } else if (currentStreak >= this.kpiThresholds.streak.fair) {
      bonus.streakBonus = 25; // $25 for 3+ day streak
    }

    // Apply performance penalties
    if (performance.punctualityScore < 0.7 || performance.qualityScore < 0.7) {
      bonus.eligible = false;
      bonus.tier = 'improvement_needed';
    }

    bonus.total = bonus.eligible 
      ? bonus.base + bonus.punctualityBonus + bonus.qualityBonus + bonus.streakBonus
      : bonus.base * 0.8; // 20% reduction for poor performance

    return bonus;
  }

  async sendBonusReport(bonusReport) {
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    if (!opsLeadId) return;

    let report = `💰 **WEEKLY BONUS REPORT** 💰\n`;
    report += `📅 Week of: ${this.getCurrentWeekPeriod()}\n\n`;

    let totalPayout = 0;

    for (const { cleaner, performance, bonus } of bonusReport) {
      const emoji = bonus.tier === 'excellent' ? '🌟' : bonus.tier === 'good' ? '⭐' : bonus.tier === 'improvement_needed' ? '⚠️' : '✅';
      
      report += `${emoji} **${cleaner}**\n`;
      report += `   💼 Jobs: ${performance.jobsCompleted} | ⏰ Punctuality: ${(performance.punctualityScore * 100).toFixed(0)}% | 🎯 Quality: ${(performance.qualityScore * 100).toFixed(0)}%\n`;
      report += `   🔥 Streak: ${performance.currentStreak} days | 💵 Bonus: $${bonus.total.toFixed(2)}\n`;
      
      if (bonus.punctualityBonus > 0) report += `      + $${bonus.punctualityBonus} punctuality bonus\n`;
      if (bonus.qualityBonus > 0) report += `      + $${bonus.qualityBonus} quality bonus\n`;
      if (bonus.streakBonus > 0) report += `      + $${bonus.streakBonus} streak bonus\n`;
      
      if (!bonus.eligible) {
        report += `      ⚠️ Performance improvement needed\n`;
      }
      
      report += `\n`;
      totalPayout += bonus.total;
    }

    report += `📊 **TOTAL WEEKLY PAYOUT: $${totalPayout.toFixed(2)}**\n\n`;
    report += `✅ Approve bonuses? React with ✅ to process payments.`;

    try {
      const message = await sendDiscordPing(opsLeadId, report);
      console.log('[Zara] Sent weekly bonus report to ops lead');
      
      // Also send to bonus updates channel if configured
      const bonusChannelId = process.env.DISCORD_BONUS_CHANNEL_ID;
      if (bonusChannelId) {
        const publicReport = report.replace('✅ Approve bonuses? React with ✅ to process payments.', 
          '💼 Bonus calculations complete! Management review in progress.');
        await sendDiscordPing(bonusChannelId, publicReport);
      }
    } catch (error) {
      console.error('[Zara] Error sending bonus report:', error);
    }
  }

  async logBonusCalculation(cleaner, performance, bonus) {
    try {
      // Log to Notion for record keeping
      await logToNotion('bonus_calculations', {
        cleaner,
        week_period: performance.period,
        jobs_completed: performance.jobsCompleted,
        punctuality_score: performance.punctualityScore,
        quality_score: performance.qualityScore,
        current_streak: performance.currentStreak,
        bonus_amount: bonus.total,
        bonus_tier: bonus.tier,
        eligible: bonus.eligible,
        calculated_at: new Date().toISOString()
      });
    } catch (error) {
      console.error(`[Zara] Error logging bonus calculation for ${cleaner}:`, error);
    }
  }

  async getActiveCleaners() {
    // Get list of cleaners from Keith's memory
    try {
      const memoryPath = './COO_Memory_Stack (8).json';
      if (fs.existsSync(memoryPath)) {
        const memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
        return Object.keys(memory);
      }
    } catch (error) {
      console.error('[Zara] Error getting active cleaners:', error);
    }
    return [];
  }

  getCurrentWeekPeriod() {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay()); // Start of current week (Sunday)
    
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6); // End of current week (Saturday)
    
    return `${startOfWeek.toLocaleDateString()} - ${endOfWeek.toLocaleDateString()}`;
  }

  getDefaultPerformance() {
    return {
      jobsCompleted: 0,
      punctualityScore: 0,
      qualityScore: 0,
      currentStreak: 0,
      punctualityStrikes: 0,
      qualityStrikes: 0,
      overallScore: 0
    };
  }

  scheduleWeeklyBonusCalculation() {
    // Calculate bonuses every Sunday at 6 PM
    const now = new Date();
    const nextSunday = new Date();
    nextSunday.setDate(now.getDate() + (7 - now.getDay()) % 7);
    nextSunday.setHours(18, 0, 0, 0);
    
    if (nextSunday <= now) {
      nextSunday.setDate(nextSunday.getDate() + 7);
    }
    
    const msUntilSunday = nextSunday.getTime() - now.getTime();
    
    setTimeout(() => {
      this.calculateWeeklyBonuses();
      
      // Then repeat every week
      setInterval(() => {
        this.calculateWeeklyBonuses();
      }, 7 * 24 * 60 * 60 * 1000);
    }, msUntilSunday);
    
    console.log(`[Zara] Next bonus calculation scheduled for: ${nextSunday.toLocaleString()}`);
  }

  scheduleDailyPerformanceCheck() {
    // Daily performance summary at 6 PM
    const now = new Date();
    const target = new Date();
    target.setHours(18, 0, 0, 0);
    
    if (target <= now) {
      target.setDate(target.getDate() + 1);
    }
    
    const msUntilTarget = target.getTime() - now.getTime();
    
    setTimeout(() => {
      this.sendDailyPerformanceUpdate();
      
      setInterval(() => {
        this.sendDailyPerformanceUpdate();
      }, 24 * 60 * 60 * 1000);
    }, msUntilTarget);
  }

  async sendDailyPerformanceUpdate() {
    // Send a brief daily performance summary
    const cleaners = await this.getActiveCleaners();
    const topPerformers = [];
    
    for (const cleaner of cleaners) {
      const performance = await this.calculateWeeklyPerformance(cleaner);
      if (performance.overallScore >= 0.9) {
        topPerformers.push({ cleaner, score: performance.overallScore });
      }
    }
    
    if (topPerformers.length > 0) {
      topPerformers.sort((a, b) => b.score - a.score);
      
      let message = `📊 **Daily Performance Spotlight** 📊\n\n`;
      message += `Top performers today:\n`;
      
      topPerformers.slice(0, 3).forEach((performer, index) => {
        const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉';
        message += `${medal} ${performer.cleaner} - ${(performer.score * 100).toFixed(0)}% performance\n`;
      });
      
      message += `\nKeep up the excellent work, team! 💪`;
      
      const channelId = process.env.DISCORD_PERFORMANCE_CHANNEL_ID || process.env.DISCORD_CHECKIN_CHANNEL_ID;
      await sendDiscordPing(channelId, message);
    }
  }

  async handleMessage(message) {
    // Zara primarily works on scheduled calculations
    return null;
  }
}

module.exports = Zara;
