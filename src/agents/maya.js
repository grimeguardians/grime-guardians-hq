// Maya Agent - Motivational Coach & Team Cheerleader
// Built on existing Keith performance data for instant implementation

const Agent = require('./agent');
const { checkCleanerPerformance, getCleanerStats } = require('../utils/notion');
const { sendDiscordPing } = require('../utils/discord');
const { createMentionFromUsername } = require('../utils/discordUserMapping');
const { getUserIdFromUsername } = require('../utils/discordUserMapping');

class Maya extends Agent {
  constructor(client) {
    super({ agentId: 'maya', role: 'Motivational Coach & Team Cheerleader' });
    this.client = client;
    this.praiseHistory = new Map(); // Track what we've already praised
    this.streakTracking = new Map(); // Track performance streaks
    this.lastMilestoneCheck = null; // Rate limiting for milestone checks
    this.milestoneCheckCooldown = 60 * 60 * 1000; // 1 hour cooldown
  }

  onReady() {
    console.log('🎉 Maya agent is ready to spread positivity and motivation!');
    
    // Check for milestones every hour
    setInterval(() => {
      this.checkForMilestones();
    }, 60 * 60 * 1000);
    
    // Daily team motivation at 8 AM
    this.scheduleDailyMotivation();
  }

  async getContext(event) {
    // Handle undefined/null events gracefully
    if (!event) return { event: null, performance: null, recentActivity: null };
    
    const username = event.author?.username;
    if (!username) return { event, performance: null, recentActivity: null };

    // Get performance context from Keith's data
    return {
      event,
      performance: await this.getPerformanceMetrics(username),
      recentActivity: await this.getRecentActivity(username)
    };
  }

  async handleEvent(event, context) {
    const content = event.content.toLowerCase();
    const username = event.author.username;

    // Detect completion/success messages for immediate praise
    const successTriggers = [
      '🏁', 'finished', 'completed', 'done', 'all finished',
      'client loved it', 'client happy', 'great feedback', 'client praised'
    ];

    const hasSuccessTrigger = successTriggers.some(t => content.includes(t));
    
    if (hasSuccessTrigger) {
      await this.handleJobCompletion(username, event.content);
    }

    // Monitor for team collaboration mentions
    if (content.includes('helped') || content.includes('teamwork')) {
      await this.handleTeamworkMention(username, event.content);
    }

    return null; // Maya spreads positivity but doesn't need responses
  }

  async handleJobCompletion(username, message) {
    const stats = await this.getPerformanceMetrics(username);
    const streakInfo = await this.checkCompletionStreak(username);

    let praiseMessage = `🎉 Amazing work, ${username}! `;

    // Contextual praise based on performance
    if (streakInfo.streak >= 5) {
      praiseMessage += `You're on fire with ${streakInfo.streak} perfect completions in a row! 🔥`;
    } else if (stats.recentQuality > 0.9) {
      praiseMessage += `Your attention to detail is outstanding! Clients love your work! ⭐`;
    } else {
      praiseMessage += `Another job knocked out of the park! Keep up the excellent work! 💪`;
    }

    // Add motivation for improvement if needed
    if (stats.punctualityScore < 0.8) {
      praiseMessage += `\n\n💡 Pro tip: Early arrivals always impress clients and show professionalism!`;
    }

    await this.sendMotivationalMessage(username, praiseMessage);
  }

  async checkForMilestones() {
    // Rate limiting: Don't check more than once per hour
    const now = Date.now();
    if (this.lastMilestoneCheck && (now - this.lastMilestoneCheck) < this.milestoneCheckCooldown) {
      console.log('[Maya] Milestone check on cooldown, skipping');
      return;
    }

    console.log('[Maya] Checking for milestones...');
    this.lastMilestoneCheck = now;

    // Check all active cleaners for milestone achievements
    const cleaners = await this.getActiveCleaners();
    
    console.log('[Maya] Checking milestones for cleaners:', cleaners);
    for (const cleaner of cleaners) {
      await this.checkIndividualMilestones(cleaner);
    }
  }

  async checkIndividualMilestones(username) {
    // Validate username - skip invalid names
    if (!username || typeof username !== 'string' || username.length < 2) {
      console.log(`[Maya] Skipping invalid username: ${username}`);
      return;
    }

    // Skip system/database field names
    const invalidNames = ['name', 'nodes', 'pinData', 'connections', 'active', 'settings', 'versionId', 'meta', 'id', 'tags'];
    if (invalidNames.includes(username)) {
      console.log(`[Maya] Skipping system field name: ${username}`);
      return;
    }

    console.log(`[Maya] Checking milestones for: ${username}`);
    const stats = await this.getPerformanceMetrics(username);
    const milestoneKey = `${username}-${new Date().toDateString()}`;

    // Skip if already praised today
    if (this.praiseHistory.has(milestoneKey)) {
      console.log(`[Maya] Already praised ${username} today, skipping`);
      return;
    }

    const milestones = [];

    // Strike-free milestone
    if (stats.daysSinceLastStrike >= 30) {
      milestones.push({
        type: 'strike_free',
        message: `🌟 MILESTONE ALERT! ${username} has gone ${stats.daysSinceLastStrike} days without any strikes! Absolutely fantastic! 🌟`
      });
    }

    // Perfect punctuality streak
    if (stats.punctualityStreak >= 7) {
      milestones.push({
        type: 'punctuality',
        message: `⏰ Punctuality Champion! ${username} has been perfectly on time for ${stats.punctualityStreak} jobs straight! 🏆`
      });
    }

    // High client satisfaction
    if (stats.clientSatisfactionScore >= 0.95 && stats.recentJobs >= 5) {
      milestones.push({
        type: 'satisfaction',
        message: `😍 Client Favorite! ${username} is absolutely crushing it with 95%+ client satisfaction! Clients LOVE your work! 💝`
      });
    }

    // Send milestone praise
    for (const milestone of milestones) {
      await this.broadcastAchievement(username, milestone);
      this.praiseHistory.set(milestoneKey, milestone.type);
    }
  }

  async broadcastAchievement(username, milestone) {
    const mention = await createMentionFromUsername(this.client, username);
    const channelId = process.env.DISCORD_TEAM_ACHIEVEMENTS_CHANNEL_ID || process.env.DISCORD_CHECKIN_CHANNEL_ID;
    
    const achievementMessage = `🎉 **TEAM ACHIEVEMENT SPOTLIGHT** 🎉\n\n${milestone.message}\n\n${mention} - you're setting an amazing example for the whole team! 👏👏👏`;

    await sendDiscordPing(channelId, achievementMessage);
    console.log(`[Maya] Broadcast achievement: ${milestone.type} for ${username}`);
  }

  async sendMotivationalMessage(username, message) {
    try {
      const userId = await getUserIdFromUsername(this.client, username);
      if (userId) {
        await sendDiscordPing(userId, message);
        console.log(`[Maya] Sent motivation to ${username}: ${message.substring(0, 50)}...`);
      }
    } catch (error) {
      console.error(`[Maya] Error sending motivation to ${username}:`, error);
    }
  }

  async getPerformanceMetrics(username) {
    // Leverage Keith's existing strike data
    try {
      const memoryPath = './COO_Memory_Stack (8).json';
      let memory = {};
      
      if (require('fs').existsSync(memoryPath)) {
        memory = JSON.parse(require('fs').readFileSync(memoryPath, 'utf8'));
      }

      const userMemory = memory[username] || { punctuality: [], quality: [] };
      
      // Ensure arrays exist
      const punctualityData = userMemory.punctuality || [];
      const qualityData = userMemory.quality || [];
      
      // Calculate metrics from Keith's data
      const recentStrikes = {
        punctuality: punctualityData.filter(s => this.isWithinDays(s.timestamp, 30)).length,
        quality: qualityData.filter(s => this.isWithinDays(s.timestamp, 30)).length
      };

      return {
        punctualityScore: Math.max(0, (30 - recentStrikes.punctuality) / 30),
        qualityScore: Math.max(0, (30 - recentStrikes.quality) / 30),
        daysSinceLastStrike: this.daysSinceLastStrike(userMemory),
        punctualityStreak: this.calculatePunctualityStreak(userMemory),
        recentQuality: Math.random() * 0.3 + 0.7, // Placeholder - integrate with actual client feedback
        clientSatisfactionScore: Math.random() * 0.2 + 0.8, // Placeholder
        recentJobs: Math.floor(Math.random() * 10) + 5 // Placeholder
      };
    } catch (error) {
      console.error('[Maya] Error getting performance metrics:', error);
      return { punctualityScore: 0.8, qualityScore: 0.8, daysSinceLastStrike: 0 };
    }
  }

  isWithinDays(timestamp, days) {
    const date = new Date(timestamp);
    const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
    return date.getTime() >= cutoff;
  }

  daysSinceLastStrike(userMemory) {
    const allStrikes = [...(userMemory.punctuality || []), ...(userMemory.quality || [])];
    if (allStrikes.length === 0) return 999; // No strikes ever
    
    const lastStrike = allStrikes.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
    const daysSince = Math.floor((Date.now() - new Date(lastStrike.timestamp)) / (24 * 60 * 60 * 1000));
    return daysSince;
  }

  calculatePunctualityStreak(userMemory) {
    // Count consecutive days without punctuality strikes
    const punctualityStrikes = (userMemory.punctuality || []).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    if (punctualityStrikes.length === 0) return 30; // No strikes = perfect streak
    
    const lastStrike = new Date(punctualityStrikes[0].timestamp);
    const daysSince = Math.floor((Date.now() - lastStrike) / (24 * 60 * 60 * 1000));
    return Math.min(daysSince, 30);
  }

  async getActiveCleaners() {
    // FIXED: Return actual cleaner names, not JSON keys
    // This should pull from a proper cleaner database or hardcoded list
    const activeCleaners = [
      'grimeguardians',
      'TestCleaner'
      // Add more actual cleaner usernames here
    ];
    
    console.log('[Maya] Retrieved active cleaners:', activeCleaners);
    return activeCleaners;
  }

  scheduleDailyMotivation() {
    // Send daily team motivation at 8 AM Central
    const now = new Date();
    const target = new Date();
    target.setHours(8, 0, 0, 0);
    
    if (target <= now) {
      target.setDate(target.getDate() + 1);
    }
    
    const msUntilTarget = target.getTime() - now.getTime();
    
    setTimeout(() => {
      this.sendDailyTeamMotivation();
      
      // Then repeat every 24 hours
      setInterval(() => {
        this.sendDailyTeamMotivation();
      }, 24 * 60 * 60 * 1000);
    }, msUntilTarget);
  }

  async sendDailyTeamMotivation() {
    const teamMessages = [
      "🌅 Good morning, Grime Guardians! Today is a brand new day to make homes sparkle and clients smile! Let's show them what amazing looks like! 💫",
      "🚀 Rise and shine, cleaning champions! Every house you touch today becomes a little piece of paradise. You've got this! 🏡✨",
      "⭐ Another day, another chance to be absolutely amazing! Remember - you're not just cleaning, you're creating happiness for families! 🏠❤️",
      "🔥 Grime Guardians ASSEMBLE! Today we're going to crush our goals and leave a trail of spotless homes behind us! Let's GO! 💪",
      "🌟 Good morning to the most incredible cleaning team in the business! Your attention to detail and care makes all the difference! ✨"
    ];

    const message = teamMessages[Math.floor(Math.random() * teamMessages.length)];
    const channelId = process.env.DISCORD_TEAM_ACHIEVEMENTS_CHANNEL_ID || process.env.DISCORD_CHECKIN_CHANNEL_ID;
    
    await sendDiscordPing(channelId, message);
    console.log('[Maya] Sent daily team motivation');
  }

  async handleMessage(message) {
    const event = {
      content: message.content,
      author: { username: message.author.username, id: message.author.id },
      channel: message.channel,
    };
    const context = await this.getContext(event);
    return await this.handleEvent(event, context);
  }

  async getRecentActivity(username) {
    // Get recent activity for context-aware motivation
    try {
      const memoryPath = './COO_Memory_Stack (8).json';
      if (require('fs').existsSync(memoryPath)) {
        const memory = JSON.parse(require('fs').readFileSync(memoryPath, 'utf8'));
        const userMemory = memory[username] || {};
        
        return {
          recentJobs: (userMemory.jobHistory || []).slice(-3), // Last 3 jobs
          recentPraise: (this.praiseHistory.get(username) || []).slice(-2), // Last 2 praise messages
          lastActivity: userMemory.lastCheckIn || null
        };
      }
    } catch (error) {
      console.error('[Maya] Error getting recent activity:', error);
    }
    return { recentJobs: [], recentPraise: [], lastActivity: null };
  }
}

module.exports = Maya;
