// src/agents/scheduleManager.js
// Schedule management agent for handling reschedules, cancellations, and availability

const Agent = require('./agent');
const { getAllJobs, updateJob } = require('../utils/highlevel');
const { sendDiscordPing } = require('../utils/discord');
const { logScheduleChange } = require('../utils/notion');
const DualChannelCommunicationMonitor = require('../utils/dualChannelCommunicationMonitor');

class ScheduleManager extends Agent {
  constructor(client) {
    super({ agentId: 'schedule_manager', role: 'Schedule & Availability Manager' });
    this.client = client;
    
    // Initialize dual-channel communication monitoring
    this.communicationMonitor = new DualChannelCommunicationMonitor(client);
    
    console.log('📅 Schedule Manager initialized with dual-channel monitoring');
    console.log('📱 Monitoring: Google Voice (612-584-9396) + High Level (651-515-1478)');
  }

  async onReady() {
    console.log('📅 Schedule Manager agent is ready for intelligent schedule management.');
    
    // Initialize and start dual-channel monitoring
    const initialized = await this.communicationMonitor.initialize();
    if (initialized) {
      await this.communicationMonitor.startMonitoring();
      console.log('✅ Dual-channel communication monitoring active');
      console.log('   📧 Google Voice (612-584-9396) → Gmail monitoring');
      console.log('   📱 High Level (651-515-1478) → API monitoring');
    } else {
      console.error('❌ Failed to initialize communication monitoring');
    }
  }

  /**
   * Start periodic monitoring of communication channels
   */
  startPeriodicMonitoring() {
    // Check every 15 minutes for new schedule requests
    setInterval(async () => {
      await this.checkAllCommunicationChannels();
    }, 15 * 60 * 1000); // 15 minutes
    
    console.log('[ScheduleManager] Periodic monitoring started (15-minute intervals)');
  }

  /**
   * Check all communication channels for schedule requests
   */
  async checkAllCommunicationChannels() {
    try {
      console.log('[ScheduleManager] Checking all communication channels...');
      
      // Monitor High Level conversations
      const hlResults = await this.communicationMonitor.checkAllChannels();
      
      // Monitor Google Voice
      const gvResults = await this.googleVoiceMonitor.checkForScheduleRequests();
      
      // Process any found schedule requests
      await this.processDiscoveredRequests(hlResults, gvResults);
      
    } catch (error) {
      console.error('[ScheduleManager] Error in periodic monitoring:', error.message);
    }
  }

  /**
   * Process discovered schedule requests from monitoring
   */
  async processDiscoveredRequests(hlResults, gvResults) {
    const allRequests = [
      ...hlResults.sources.highlevel,
      ...gvResults.emailResults
    ];
    
    if (allRequests.length === 0) return;
    
    console.log(`[ScheduleManager] Processing ${allRequests.length} discovered schedule requests`);
    
    for (const request of allRequests) {
      await this.handleDiscoveredScheduleRequest(request);
    }
  }

  /**
   * Handle a discovered schedule request from monitoring
   */
  async handleDiscoveredScheduleRequest(request) {
    try {
      const formattedRequest = this.communicationMonitor.formatForAgent(request);
      
      // Send alert to operations team
      const alertMessage = this.formatScheduleRequestAlert(request);
      await this.sendScheduleAlert(alertMessage, request.urgency);
      
      // Log the discovery
      console.log(`[ScheduleManager] Schedule request detected: ${request.detection?.messageType} from ${request.contactName || request.phoneNumber}`);
      
      // Auto-respond based on urgency and type
      if (request.urgency === 'high') {
        await this.handleUrgentScheduleRequest(request);
      } else {
        await this.handleStandardScheduleRequest(request);
      }
      
    } catch (error) {
      console.error('[ScheduleManager] Error handling discovered request:', error.message);
    }
  }

  /**
   * Format schedule request alert for operations team
   */
  formatScheduleRequestAlert(request) {
    const source = request.source === 'highlevel' ? '📱 High Level' : '📞 Google Voice';
    const urgencyEmoji = request.urgency === 'high' ? '🚨' : '⚠️';
    
    return `${urgencyEmoji} **Schedule Request Detected**\n\n` +
      `**Source**: ${source}\n` +
      `**Client**: ${request.contactName || 'Unknown'}\n` +
      `**Phone**: ${request.contactPhone || request.phoneNumber || 'N/A'}\n` +
      `**Type**: ${request.detection?.messageType || 'Unknown'}\n` +
      `**Urgency**: ${request.urgency}\n` +
      `**Message**: "${request.message || request.content}"\n` +
      `**Time**: ${new Date(request.timestamp).toLocaleString()}\n\n` +
      `${request.urgency === 'high' ? '**Immediate response required!**' : 'Please review and respond when possible.'}`;
  }

  /**
   * Send schedule alert to operations team
   */
  async sendScheduleAlert(message, urgency) {
    try {
      const opsLeadId = process.env.OPS_LEAD_DISCORD_ID || '1343301440864780291';
      const alertsChannelId = process.env.DISCORD_ALERTS_CHANNEL_ID || '1377516295754350613';
      
      // Send DM to ops lead
      const user = await this.client.users.fetch(opsLeadId);
      await user.send(message);
      
      // Send to alerts channel if urgent
      if (urgency === 'high') {
        const channel = await this.client.channels.fetch(alertsChannelId);
        await channel.send(`<@${opsLeadId}> ${message}`);
      }
      
    } catch (error) {
      console.error('[ScheduleManager] Error sending schedule alert:', error.message);
    }
  }

  /**
   * Handle urgent schedule requests (immediate response)
   */
  async handleUrgentScheduleRequest(request) {
    console.log(`[ScheduleManager] Handling urgent schedule request from ${request.contactName}`);
    
    // For urgent requests, we want immediate human attention
    // Auto-acknowledge receipt but escalate to human
    
    if (request.source === 'highlevel' && request.contactId) {
      // Send immediate acknowledgment via High Level
      await this.sendHighLevelResponse(request.contactId, 
        "Thank you for contacting Grime Guardians. We've received your urgent scheduling request and our team will respond within 30 minutes. For immediate assistance, please call us directly."
      );
    }
  }

  /**
   * Handle standard schedule requests
   */
  async handleStandardScheduleRequest(request) {
    console.log(`[ScheduleManager] Handling standard schedule request from ${request.contactName}`);
    
    // For standard requests, attempt intelligent processing
    const response = await this.generateIntelligentResponse(request);
    
    if (request.source === 'highlevel' && request.contactId) {
      await this.sendHighLevelResponse(request.contactId, response);
    }
  }

  /**
   * Generate intelligent response based on request analysis
   */
  async generateIntelligentResponse(request) {
    const messageType = request.detection?.messageType || 'general_inquiry';
    
    switch (messageType) {
      case 'cancellation':
        return "Hi! We received your cancellation request. We understand things come up! Please confirm the appointment date/time you'd like to cancel, and we'll process this right away. If you'd like to reschedule instead, we're happy to find a new time that works better for you.";
        
      case 'reschedule':
        return "Hi! We'd be happy to help reschedule your cleaning appointment. Could you please let me know:\n\n1. Which appointment you'd like to reschedule (date/time)\n2. Your preferred new date and time\n\nWe'll check our availability and confirm the new time within a few hours. Thank you!";
        
      case 'urgent_change':
        return "Hi! We received your urgent scheduling request. Our team is reviewing this now and will respond within 30 minutes. If this is an emergency, please call us directly at your convenience.";
        
      default:
        return "Hi! Thank you for contacting Grime Guardians. We received your message about scheduling and our team will review your request and respond within a few hours. If you need immediate assistance, please feel free to call us directly.";
    }
  }

  /**
   * Send response via High Level
   */
  async sendHighLevelResponse(contactId, message) {
    try {
      // This would use High Level's messaging API
      console.log(`[ScheduleManager] Sending High Level response to ${contactId}: ${message}`);
      
      // TODO: Implement actual High Level messaging API call
      // For now, just log the intended response
      
    } catch (error) {
      console.error('[ScheduleManager] Error sending High Level response:', error.message);
    }
  }

  async getContext(event) {
    return { event, timestamp: new Date().toISOString() };
  }

  async handleEvent(event, context) {
    const content = event.content.toLowerCase();
    const timestamp = context.timestamp;

    // Detect schedule change requests
    const scheduleKeywords = [
      'reschedule', 'move', 'change date', 'change time', 'postpone', 'delay',
      'earlier', 'later', 'different day', 'cancel', 'cancellation'
    ];

    const hasScheduleRequest = scheduleKeywords.some(keyword => content.includes(keyword));
    
    if (hasScheduleRequest) {
      return await this.processScheduleRequest(event, context);
    }

    return this.formatOutput({
      task: 'monitor',
      actionRequired: 'none',
      confidence: 0.1,
      extra: { message: 'No schedule management action required' }
    });
  }

  async processScheduleRequest(event, context) {
    const content = event.content;
    const author = event.author.username;
    
    console.log(`[ScheduleManager] Processing schedule request from ${author}`);
    
    // Extract key information
    const scheduleInfo = await this.extractScheduleInfo(content);
    
    if (scheduleInfo.type === 'reschedule') {
      return await this.handleRescheduleRequest(scheduleInfo, author, context);
    } else if (scheduleInfo.type === 'cancellation') {
      return await this.handleCancellationRequest(scheduleInfo, author, context);
    }

    return this.formatOutput({
      task: 'schedule_change',
      actionRequired: 'manual_review',
      confidence: 0.7,
      extra: { scheduleInfo, author }
    });
  }

  async extractScheduleInfo(content) {
    // Use AI-powered extraction for schedule details
    const reschedulePatterns = /(?:move|reschedule|change).*(?:to|for)\s*((?:july|august|september|october|november|december)\s*\d{1,2}|\d{1,2}\/\d{1,2}|\d{1,2}th|\d{1,2}nd|\d{1,2}st)/i;
    const timePatterns = /(\d{1,2}:\d{2}\s*(?:am|pm)|morning|afternoon|evening)/i;
    
    const rescheduleMatch = content.match(reschedulePatterns);
    const timeMatch = content.match(timePatterns);
    
    const type = content.includes('cancel') ? 'cancellation' : 'reschedule';
    
    return {
      type,
      originalRequest: content,
      newDate: rescheduleMatch ? rescheduleMatch[1] : null,
      newTime: timeMatch ? timeMatch[1] : null,
      urgency: content.includes('urgent') || content.includes('asap') ? 'high' : 'normal'
    };
  }

  async handleRescheduleRequest(scheduleInfo, clientContact, context) {
    console.log(`[ScheduleManager] Processing reschedule request:`, scheduleInfo);

    // Step 1: Check availability for new date
    const availability = await this.checkAvailability(scheduleInfo.newDate, scheduleInfo.newTime);
    
    // Step 2: Notify ops team for approval
    const approvalMessage = `📅 **Schedule Change Request**\n\n` +
      `**Client Contact**: ${clientContact}\n` +
      `**Request**: ${scheduleInfo.originalRequest}\n` +
      `**New Date**: ${scheduleInfo.newDate || 'TBD'}\n` +
      `**New Time**: ${scheduleInfo.newTime || 'TBD'}\n` +
      `**Availability Check**: ${availability.status}\n\n` +
      `${availability.status === 'available' ? 
        '✅ **AVAILABLE** - Reply "approve" to confirm reschedule' :
        '❌ **CONFLICT** - Alternative times suggested below'}\n\n` +
      `${availability.alternatives ? `**Alternative Options**:\n${availability.alternatives.join('\n')}` : ''}`;

    // Send to ops team
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    if (opsLeadId) {
      await sendDiscordPing(opsLeadId, approvalMessage);
    }

    // Step 3: If available, prepare client response
    if (availability.status === 'available') {
      const clientResponse = `Hi ${clientContact}! 👋\n\n` +
        `We'd be happy to reschedule your cleaning for ${scheduleInfo.newDate}${scheduleInfo.newTime ? ` at ${scheduleInfo.newTime}` : ''}!\n\n` +
        `✅ That time slot is available\n` +
        `📋 Your assigned cleaner will be notified\n` +
        `⏰ You'll receive updated reminders\n\n` +
        `We're confirming this change now and will send you a confirmation shortly. Thanks for choosing Grime Guardians! 🧽✨`;

      // Log to channel for ops awareness
      const channelMessage = `📅 **Auto-Response Sent**\n\n` +
        `Confirmed availability for ${clientContact}'s reschedule request.\n` +
        `New date: ${scheduleInfo.newDate}\n` +
        `Awaiting ops approval to finalize.`;

      const alertsChannelId = process.env.DISCORD_ALERTS_CHANNEL_ID;
      if (alertsChannelId) {
        await sendDiscordPing(alertsChannelId, channelMessage);
      }

      return this.formatOutput({
        task: 'reschedule_approved',
        actionRequired: 'send_client_confirmation',
        confidence: 0.9,
        extra: { 
          scheduleInfo, 
          clientContact, 
          clientResponse, 
          availability 
        }
      });
    } else {
      // Conflict - need manual handling
      return this.formatOutput({
        task: 'reschedule_conflict',
        actionRequired: 'manual_coordination',
        confidence: 0.8,
        extra: { 
          scheduleInfo, 
          clientContact, 
          availability 
        }
      });
    }
  }

  async checkAvailability(newDate, newTime) {
    try {
      // Get all appointments for the requested date
      const allJobs = await getAllJobs();
      const requestedDate = this.parseDate(newDate);
      
      if (!requestedDate) {
        return {
          status: 'date_unclear',
          message: 'Could not parse requested date',
          alternatives: []
        };
      }

      // Check for conflicts
      const conflictsOnDate = allJobs.filter(job => {
        const jobDate = new Date(job.startTime);
        return jobDate.toDateString() === requestedDate.toDateString();
      });

      const timeSlot = this.parseTime(newTime);
      let hasConflict = false;

      if (timeSlot && conflictsOnDate.length > 0) {
        hasConflict = conflictsOnDate.some(job => {
          const jobTime = new Date(job.startTime);
          const timeDiff = Math.abs(jobTime.getTime() - timeSlot.getTime());
          return timeDiff < (3 * 60 * 60 * 1000); // 3 hour buffer
        });
      }

      if (hasConflict) {
        // Generate alternative times
        const alternatives = this.generateAlternatives(requestedDate, conflictsOnDate);
        
        return {
          status: 'conflict',
          message: 'Time slot has conflicts',
          alternatives,
          conflictCount: conflictsOnDate.length
        };
      } else {
        return {
          status: 'available',
          message: 'Time slot is available',
          alternatives: []
        };
      }

    } catch (error) {
      console.error('[ScheduleManager] Error checking availability:', error);
      return {
        status: 'error',
        message: 'Could not check availability',
        alternatives: []
      };
    }
  }

  parseDate(dateString) {
    if (!dateString) return null;
    
    try {
      // Handle various date formats
      const patterns = [
        /july\s*(\d{1,2})/i,
        /august\s*(\d{1,2})/i,
        /(\d{1,2})\/(\d{1,2})/,
        /(\d{1,2})(?:st|nd|rd|th)/
      ];

      for (const pattern of patterns) {
        const match = dateString.match(pattern);
        if (match) {
          const day = parseInt(match[1]);
          const month = dateString.toLowerCase().includes('july') ? 6 : 
                       dateString.toLowerCase().includes('august') ? 7 : 
                       new Date().getMonth(); // Current month as fallback
          
          const year = new Date().getFullYear();
          return new Date(year, month, day);
        }
      }
    } catch (error) {
      console.error('[ScheduleManager] Date parsing error:', error);
    }
    
    return null;
  }

  parseTime(timeString) {
    if (!timeString) return null;
    
    try {
      // Default times for general references
      if (timeString.toLowerCase().includes('morning')) {
        return new Date(2025, 0, 1, 10, 0); // 10 AM
      } else if (timeString.toLowerCase().includes('afternoon')) {
        return new Date(2025, 0, 1, 14, 0); // 2 PM
      } else if (timeString.toLowerCase().includes('evening')) {
        return new Date(2025, 0, 1, 18, 0); // 6 PM
      }

      // Parse specific times like "2:30 PM"
      const timeMatch = timeString.match(/(\d{1,2}):(\d{2})\s*(am|pm)/i);
      if (timeMatch) {
        let hours = parseInt(timeMatch[1]);
        const minutes = parseInt(timeMatch[2]);
        const period = timeMatch[3].toLowerCase();
        
        if (period === 'pm' && hours !== 12) hours += 12;
        if (period === 'am' && hours === 12) hours = 0;
        
        return new Date(2025, 0, 1, hours, minutes);
      }
    } catch (error) {
      console.error('[ScheduleManager] Time parsing error:', error);
    }
    
    return null;
  }

  generateAlternatives(requestedDate, conflicts) {
    const alternatives = [];
    const baseDate = new Date(requestedDate);
    
    // Suggest times around conflicts
    const suggestedTimes = ['9:00 AM', '11:00 AM', '1:00 PM', '3:00 PM', '5:00 PM'];
    
    for (const time of suggestedTimes) {
      const testTime = this.parseTime(time);
      const hasConflict = conflicts.some(job => {
        const jobTime = new Date(job.startTime);
        const timeDiff = Math.abs(jobTime.getTime() - testTime.getTime());
        return timeDiff < (3 * 60 * 60 * 1000);
      });
      
      if (!hasConflict) {
        alternatives.push(`${baseDate.toLocaleDateString()} at ${time}`);
      }
    }

    // If no alternatives on same day, suggest next day
    if (alternatives.length === 0) {
      const nextDay = new Date(baseDate);
      nextDay.setDate(nextDay.getDate() + 1);
      alternatives.push(`${nextDay.toLocaleDateString()} (next day) - Multiple times available`);
    }

    return alternatives.slice(0, 3); // Limit to 3 suggestions
  }

  async handleCancellationRequest(scheduleInfo, clientContact, context) {
    console.log(`[ScheduleManager] Processing cancellation request from ${clientContact}`);

    // Notify ops team
    const cancellationAlert = `❌ **Cancellation Request**\n\n` +
      `**Client**: ${clientContact}\n` +
      `**Request**: ${scheduleInfo.originalRequest}\n` +
      `**Urgency**: ${scheduleInfo.urgency}\n\n` +
      `Please review and process cancellation in High Level.\n` +
      `Remember to notify assigned cleaner if applicable.`;

    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    if (opsLeadId) {
      await sendDiscordPing(opsLeadId, cancellationAlert);
    }

    return this.formatOutput({
      task: 'cancellation_request',
      actionRequired: 'process_cancellation',
      confidence: 0.9,
      extra: { scheduleInfo, clientContact }
    });
  }

  // For Discord compatibility
  async handleMessage(message) {
    const event = {
      content: message.content,
      author: { username: message.author.username, id: message.author.id },
      channel: message.channel,
    };
    const context = await this.getContext(event);
    const result = await this.handleEvent(event, context);
    return result;
  }
}

module.exports = ScheduleManager;
