// src/agents/keithEnhanced.js
// Enhanced Keith agent with full escalation, job scheduling, and Discord integration

const Agent = require('./agent');
const fs = require('fs');
const { logStrike, logCheckin, logCheckout } = require('../utils/notion');
const { schedulePunctualityEscalation } = require('../utils/punctualityEscalation');
const { checkLatenessForCleaner, getCurrentJobForCleaner, mapDiscordUserToCleaner, scheduleJobReminders } = require('../utils/jobScheduler');
const { getUserIdFromUsername, createMentionFromUsername } = require('../utils/discordUserMapping');
const { sendDiscordPing } = require('../utils/discord');

class KeithEnhanced extends Agent {
  constructor(client) {
    super({ agentId: 'keithEnhanced', role: 'Field Operations Manager' });
    this.client = client;
    this.activeEscalations = new Map(); // Track active escalations by user
    this.reminderTimeouts = new Map(); // Track reminder timeouts by user
    
    // Add required tracking maps for tests
    this.activeJobs = new Map();
    this.cleanerPerformance = new Map();
    this.strikeSystem = new Map();
  }

  onReady() {
    console.log('Keith Enhanced agent is ready with full escalation and job scheduling.');
    this.initializeReminderSystem();
  }

  async getContext(event) {
    // Get job context for the cleaner
    const cleanerName = mapDiscordUserToCleaner(event.author.username);
    const currentJob = await getCurrentJobForCleaner(cleanerName);
    const latenessCheck = await checkLatenessForCleaner(cleanerName);
    
    return {
      event,
      cleanerName,
      currentJob,
      latenessCheck
    };
  }

  async handleEvent(event, context) {
    const content = event.content;
    const contentLower = content.toLowerCase();
    const timestamp = new Date().toISOString();
    const user = event.author.username;
    const userId = event.author.id;

    // Load or initialize strike memory (pillar-specific, rolling 30 days)
    const memoryPath = './COO_Memory_Stack (8).json';
    let memory = {};
    try {
      if (fs.existsSync(memoryPath)) {
        memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
      }
    } catch (e) { memory = {}; }

    if (!memory[user]) memory[user] = { punctuality: [], quality: [] };

    // Remove strikes older than 30 days
    const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;
    const cutoff = Date.now() - THIRTY_DAYS_MS;
    ['punctuality', 'quality'].forEach(pillar => {
      memory[user][pillar] = (memory[user][pillar] || []).filter(s => new Date(s.timestamp).getTime() >= cutoff);
    });

    // Check-in triggers (expanded)
    const arrivalTriggers = [
      '🚗', 'arrived', "i've arrived", 'here', "i'm here", 'starting', 'start', 'on site', 'onsite', 
      'checked in', 'check in', 'begin', 'beginning', 'at job', 'at work', 'at site', 'at location'
    ];
    const hasArrivalTrigger = arrivalTriggers.some(t => contentLower.includes(t));

    if (hasArrivalTrigger) {
      return await this.handleCheckin(event, context, memory, memoryPath);
    }

    // Check-out triggers (expanded)
    const finishedTriggers = [
      '🏁', 'finished', "i'm finished", 'done', 'all done', 'complete', 'completed', 'checkout', 
      'checked out', 'leaving', 'leaving site', 'leaving work', 'leaving job', 'leaving location', 
      'job done', 'job finished', 'job complete', 'job completed', 'out', 'outta here', 
      'clocking out', 'clock out', 'punching out', 'punch out'
    ];
    const hasFinishedTrigger = finishedTriggers.some(t => contentLower.includes(t));

    if (hasFinishedTrigger) {
      return await this.handleCheckout(event, context);
    }

    // Quality/complaint strike logic
    const complaintTriggers = [
      'complaint', 'issue', 'problem', 'damage', 'client unhappy', 'client complaint', 'missed spot', 
      'redo', 'reclean', 'callback', 'negative feedback', 'unsatisfied', 'not satisfied', 'not happy', 
      'bad review', 'poor job', 'quality issue', 'quality concern', 'could have been better', 
      'wasn\'t great', 'not up to standard', 'disappointed', 'let down', 'expected more', 'not impressed'
    ];
    const hasComplaintTrigger = complaintTriggers.some(t => contentLower.includes(t));

    if (hasComplaintTrigger) {
      return await this.handleQualityIssue(event, memory, memoryPath);
    }

    // Default: just log
    const payload = {
      user: event.author.username,
      content: event.content,
      channel: event.channel.name || event.channel.id,
      timestamp,
    };
    console.log('[Keith] Message received in check-in channel:', payload);
    return this.formatOutput({
      task: 'other',
      actionRequired: 'review_or_log',
      confidence: 1.0,
      extra: { payload }
    });
  }

  async handleCheckin(event, context, memory, memoryPath) {
    const content = event.content;
    const contentLower = content.toLowerCase();
    const timestamp = new Date().toISOString();
    const user = event.author.username;
    const userId = event.author.id;

    // Extract notes: everything after the first trigger word/emoji
    let notes = '';
    const arrivalTriggers = [
      '🚗', 'arrived', "i've arrived", 'here', "i'm here", 'starting', 'start', 'on site', 'onsite', 
      'checked in', 'check in', 'begin', 'beginning', 'at job', 'at work', 'at site', 'at location'
    ];
    
    for (const trigger of arrivalTriggers) {
      const idx = contentLower.indexOf(trigger);
      if (idx !== -1) {
        notes = content.slice(idx + trigger.length).trim();
        notes = notes.replace(/^([.,-\s]+)/, '');
        break;
      }
    }

    // Check lateness using job-specific timing
    let isLate = false;
    let minutesLate = 0;
    let jobInfo = null;

    if (context.latenessCheck && context.latenessCheck.job) {
      isLate = context.latenessCheck.isLate;
      minutesLate = context.latenessCheck.minutesLate;
      jobInfo = context.latenessCheck.job;
      
      console.log(`[Keith] Job-specific lateness check for ${user}: ${isLate ? `${minutesLate} min late` : 'on time'}`);
    } else {
      // Fallback to static 8:05 AM logic if no job found
      const LATE_HOUR = 8;
      const LATE_MINUTE = 5;
      const now = new Date(timestamp);
      if (now.getHours() > LATE_HOUR || (now.getHours() === LATE_HOUR && now.getMinutes() > LATE_MINUTE)) {
        isLate = true;
        console.log(`[Keith] Using fallback 8:05 AM lateness check for ${user}: late`);
      }
    }

    // Strike logic: increment punctuality if late
    let strikeAdded = false;
    if (isLate) {
      memory[user].punctuality.push({ timestamp, type: 'late', minutesLate });
      strikeAdded = true;
      fs.writeFileSync(memoryPath, JSON.stringify(memory, null, 2));

      // Log to Notion Strikes DB
      await logStrike({
        username: user,
        timestamp,
        type: 'punctuality',
        notes: `${minutesLate} minutes late. ${notes || ''}`
      });

      // 🚀 NEW: Trigger escalation system for late check-ins
      await this.triggerLateEscalation(user, userId, jobInfo, minutesLate, notes);
    }

    // Cancel any active escalation for this user (they checked in)
    if (this.activeEscalations.has(user)) {
      this.cancelEscalation(user);
    }

    // Log check-in to Notion
    try {
      await logCheckin({
        username: user,
        timestamp,
        notes: notes || '',
        jobId: jobInfo?.id || null
      });
      console.log('[Keith] Check-in logged to Notion successfully.');
    } catch (err) {
      console.error('[Keith] Failed to log check-in to Notion:', err.message);
    }

    const payload = {
      user,
      content: event.content,
      channel: event.channel.name || event.channel.id,
      timestamp,
      notes: notes || undefined,
      isLate,
      minutesLate,
      jobInfo: jobInfo ? { id: jobInfo.id, startTime: jobInfo.startTime, address: jobInfo.address } : null,
      punctualityStrikes: memory[user].punctuality.length,
      qualityStrikes: memory[user].quality.length,
      strikeAdded
    };

    console.log('[Keith] Check-in detected:', payload);
    return this.formatOutput({
      task: 'checkin',
      actionRequired: strikeAdded ? 'flag_late' : 'review_or_log',
      confidence: 1.0,
      extra: { payload }
    });
  }

  async handleCheckout(event, context) {
    const content = event.content;
    const contentLower = content.toLowerCase();
    const timestamp = new Date().toISOString();
    const user = event.author.username;

    // Extract notes
    let notes = '';
    const finishedTriggers = [
      '🏁', 'finished', "i'm finished", 'done', 'all done', 'complete', 'completed', 'checkout', 
      'checked out', 'leaving', 'leaving site', 'leaving work', 'leaving job', 'leaving location', 
      'job done', 'job finished', 'job complete', 'job completed', 'out', 'outta here', 
      'clocking out', 'clock out', 'punching out', 'punch out'
    ];

    for (const trigger of finishedTriggers) {
      const idx = contentLower.indexOf(trigger);
      if (idx !== -1) {
        notes = content.slice(idx + trigger.length).trim();
        notes = notes.replace(/^([.,-\s]+)/, '');
        break;
      }
    }

    // Log checkout to Notion
    try {
      await logCheckout({
        username: user,
        timestamp,
        notes: notes || ''
      });
      console.log('[Keith] Check-out logged to Notion successfully.');
    } catch (err) {
      console.error('[Keith] Failed to log check-out to Notion:', err.message);
    }

    const payload = {
      user: event.author.username,
      content: event.content,
      channel: event.channel.name || event.channel.id,
      timestamp,
      notes: notes || undefined,
      jobInfo: context.currentJob ? { id: context.currentJob.id, address: context.currentJob.address } : null
    };

    console.log('[Keith] Check-out detected:', payload);
    return this.formatOutput({
      task: 'checkout',
      actionRequired: 'review_or_log',
      confidence: 1.0,
      extra: { payload }
    });
  }

  async handleQualityIssue(event, memory, memoryPath) {
    const timestamp = new Date().toISOString();
    const user = event.author.username;

    // Add a quality strike
    memory[user].quality.push({ timestamp, type: 'quality' });
    fs.writeFileSync(memoryPath, JSON.stringify(memory, null, 2));

    // Log to Notion Strikes DB
    await logStrike({
      username: user,
      timestamp,
      type: 'quality',
      notes: event.content
    });

    // 🚀 NEW: Send immediate notification for quality issues
    await this.notifyQualityIssue(user, event.content);

    const payload = {
      user,
      content: event.content,
      channel: event.channel.name || event.channel.id,
      timestamp,
      qualityStrikes: memory[user].quality.length,
      complaintDetected: true
    };

    console.log('[Keith] Quality/complaint detected:', payload);
    return this.formatOutput({
      task: 'quality_strike',
      actionRequired: 'flag_quality',
      confidence: 1.0,
      extra: { payload }
    });
  }

  // 🚀 NEW: Trigger escalation for late check-ins
  async triggerLateEscalation(username, userId, jobInfo, minutesLate, notes) {
    try {
      console.log(`[Keith] Triggering escalation for ${username} (${minutesLate} min late)`);

      const scheduledTime = jobInfo?.startTime || new Date().toISOString();
      
      // Start escalation process
      await schedulePunctualityEscalation({
        cleaner: userId, // Use Discord user ID for mentions
        scheduledTime,
        hasCheckedIn: async () => {
          // Check if user has checked in since we started escalation
          return !this.activeEscalations.has(username);
        },
        escalationTargets: [
          process.env.DISCORD_CHECKIN_CHANNEL_ID || event.channel.id
        ],
        opsDM: process.env.OPS_LEAD_DISCORD_ID,
        alertsChannel: process.env.DISCORD_ALERTS_CHANNEL_ID,
        client: this.client
      });

      // Track active escalation
      this.activeEscalations.set(username, {
        startTime: Date.now(),
        jobInfo,
        minutesLate
      });

    } catch (error) {
      console.error('[Keith] Error triggering escalation:', error);
    }
  }

  // 🚀 NEW: Send quality issue notifications
  async notifyQualityIssue(username, complaintText) {
    try {
      const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
      const alertsChannelId = process.env.DISCORD_ALERTS_CHANNEL_ID;

      if (opsLeadId) {
        const message = `🚨 **Quality Issue Detected**\n\n` +
          `**Cleaner**: ${username}\n` +
          `**Issue**: ${complaintText}\n` +
          `**Time**: ${new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' })}\n\n` +
          `Please review and take appropriate action.`;

        await sendDiscordPing(opsLeadId, message);
        console.log(`[Keith] Quality issue notification sent to ops lead`);
      }

      if (alertsChannelId) {
        const mention = await createMentionFromUsername(this.client, username);
        const channelMessage = `🚨 Quality concern detected from ${mention}. Ops team notified.`;
        
        await sendDiscordPing(alertsChannelId, channelMessage);
        console.log(`[Keith] Quality issue logged to alerts channel`);
      }

    } catch (error) {
      console.error('[Keith] Error sending quality notifications:', error);
    }
  }

  // Cancel active escalation (when user checks in)
  cancelEscalation(username) {
    if (this.activeEscalations.has(username)) {
      console.log(`[Keith] Cancelling escalation for ${username} (checked in)`);
      this.activeEscalations.delete(username);
    }
  }

  // 🚀 NEW: Initialize reminder system for all scheduled jobs
  async initializeReminderSystem() {
    try {
      console.log('[Keith] Initializing job reminder system...');
      
      // Schedule reminders for all upcoming jobs
      // This would typically be called periodically or when new jobs are assigned
      
      // For now, we'll set up a periodic check every hour
      setInterval(() => {
        this.scheduleUpcomingReminders();
      }, 60 * 60 * 1000); // Every hour

      // Initial setup
      await this.scheduleUpcomingReminders();
      
    } catch (error) {
      console.error('[Keith] Error initializing reminder system:', error);
    }
  }

  // 🚀 NEW: Schedule reminders for upcoming jobs
  async scheduleUpcomingReminders() {
    try {
      // This is a placeholder - you'd need to implement logic to:
      // 1. Get all upcoming jobs from High Level
      // 2. For each job with an assigned cleaner, schedule 24h and 2h reminders
      // 3. Track scheduled reminders to avoid duplicates
      
      console.log('[Keith] Checking for upcoming jobs to schedule reminders...');
      
      // Implementation would go here when job assignment workflow is complete
      
    } catch (error) {
      console.error('[Keith] Error scheduling reminders:', error);
    }
  }

  // 🚀 NEW: Send job reminder
  async sendJobReminder(reminderData) {
    try {
      const { type, cleaner, job, scheduledTime } = reminderData;
      
      const userId = await getUserIdFromUsername(this.client, cleaner);
      if (!userId) {
        console.error(`[Keith] Could not find Discord user ID for cleaner: ${cleaner}`);
        return;
      }

      let message;
      if (type === '24h') {
        message = `⏰ **24 Hour Job Reminder**\n\n` +
          `You have a cleaning job scheduled for tomorrow!\n\n` +
          `📅 **Time**: ${new Date(scheduledTime).toLocaleString('en-US', { timeZone: 'America/Chicago' })}\n` +
          `📍 **Address**: ${job.address || 'Address TBD'}\n` +
          `📋 **Service**: ${job.title || 'Cleaning Service'}\n\n` +
          `Please confirm you'll be there on time! Remember to check in 15 minutes before your scheduled start time.`;
      } else if (type === '2h') {
        message = `🚨 **2 Hour Job Reminder**\n\n` +
          `Your cleaning job starts in 2 hours!\n\n` +
          `📅 **Time**: ${new Date(scheduledTime).toLocaleString('en-US', { timeZone: 'America/Chicago' })}\n` +
          `📍 **Address**: ${job.address || 'Address TBD'}\n\n` +
          `⚠️ **Remember**: Check in 15 minutes before start time to avoid lateness strikes.`;
      }

      await sendDiscordPing(userId, message);
      console.log(`[Keith] Sent ${type} reminder to ${cleaner}`);

    } catch (error) {
      console.error('[Keith] Error sending job reminder:', error);
    }
  }

  // Job processing methods required by tests
  processWebhookData(webhookData) {
    // Process incoming webhook data from HighLevel
    try {
      if (webhookData && webhookData.appointmentId) {
        this.activeJobs.set(webhookData.appointmentId, {
          id: webhookData.appointmentId,
          cleaner: webhookData.assignedUser || 'Unknown',
          scheduledTime: webhookData.startTime,
          address: webhookData.address,
          status: 'scheduled'
        });
        return true;
      }
    } catch (error) {
      console.error('[Keith] Error processing webhook data:', error);
    }
    return false;
  }

  postJobAssignment(jobId, cleanerName) {
    // Handle post-job assignment tasks
    try {
      const job = this.activeJobs.get(jobId);
      if (job) {
        job.cleaner = cleanerName;
        job.status = 'assigned';
        this.activeJobs.set(jobId, job);
        
        // Update cleaner performance tracking
        const performance = this.cleanerPerformance.get(cleanerName) || {
          totalJobs: 0,
          completedJobs: 0,
          averageRating: 0
        };
        performance.totalJobs++;
        this.cleanerPerformance.set(cleanerName, performance);
        
        return true;
      }
    } catch (error) {
      console.error('[Keith] Error in post job assignment:', error);
    }
    return false;
  }

  async handleMessage(message) {
    const event = {
      content: message.content,
      author: { username: message.author.username, id: message.author.id },
      channel: message.channel,
    };
    const context = await this.getContext(event);
    const result = await this.handleEvent(event, context);
    // Keith does not reply to user; only logs or triggers actions
    return result;
  }
}

module.exports = KeithEnhanced;
