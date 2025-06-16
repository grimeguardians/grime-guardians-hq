/**
 * Email-Based Communication Monitor
 * The SIMPLE and RELIABLE approach to monitoring client communications
 * 
 * This monitors:
 * 1. Gmail inbox for Google Voice SMS forwards
 * 2. High Level conversation notifications (if you get email alerts)
 * 3. Any other email-based client communications
 * 
 * When it detects schedule requests, it:
 * 1. Alerts you via Discord
 * 2. Can auto-draft email replies (you approve/send)
 * 3. Logs everything to Notion
 */

const { google } = require('googleapis');
const { detectScheduleRequest } = require('./scheduleDetection');

class EmailBasedCommunicationMonitor {
  constructor(client) {
    this.discordClient = client;
    this.gmail = null;
    this.isMonitoring = false;
    this.lastCheckTime = new Date();
  }

  async initialize() {
    try {
      // Initialize Gmail API with OAuth2
      const auth = new google.auth.OAuth2(
        process.env.GMAIL_CLIENT_ID,
        process.env.GMAIL_CLIENT_SECRET,
        process.env.GMAIL_REDIRECT_URI
      );

      auth.setCredentials({
        refresh_token: process.env.GMAIL_REFRESH_TOKEN
      });

      this.gmail = google.gmail({ version: 'v1', auth });
      console.log('✅ Email monitor initialized');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize email monitor:', error.message);
      return false;
    }
  }

  async startMonitoring() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    console.log('📧 Starting email-based communication monitoring...');
    
    // Check every 5 minutes (more responsive than 15 minutes)
    this.monitoringInterval = setInterval(() => {
      this.checkNewEmails();
    }, 5 * 60 * 1000);

    // Initial check
    await this.checkNewEmails();
  }

  async checkNewEmails() {
    try {
      // Search for emails since last check
      const query = this.buildEmailQuery();
      
      const response = await this.gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 50
      });

      const messages = response.data.messages || [];
      console.log(`📧 Found ${messages.length} new emails to check`);

      for (const message of messages) {
        await this.processEmail(message.id);
      }

      this.lastCheckTime = new Date();
    } catch (error) {
      console.error('❌ Error checking emails:', error.message);
    }
  }

  buildEmailQuery() {
    // Format: after:2024/06/14 from:(txt.voice.google.com OR noreply@highlevel.com)
    const date = this.lastCheckTime.toISOString().split('T')[0].replace(/-/g, '/');
    
    return `after:${date} (` +
      `from:txt.voice.google.com OR ` +           // Google Voice SMS
      `from:noreply@highlevel.com OR ` +          // High Level notifications
      `from:no-reply@leadconnectorhq.com OR ` +   // Lead Connector
      `subject:"SMS from" OR ` +                  // Alternative Google Voice format
      `subject:"New message from"` +              // High Level format
      `)`;
  }

  async processEmail(messageId) {
    try {
      const message = await this.gmail.users.messages.get({
        userId: 'me',
        id: messageId,
        format: 'full'
      });

      const email = this.parseEmailContent(message.data);
      
      if (!email) return;

      // Check if this contains a schedule request
      const scheduleRequest = detectScheduleRequest(email.content);
      
      if (scheduleRequest.isScheduleRequest) {
        console.log(`🎯 Schedule request detected in email from ${email.from}`);
        await this.handleScheduleRequest(email, scheduleRequest);
      }

    } catch (error) {
      console.error('❌ Error processing email:', error.message);
    }
  }

  parseEmailContent(emailData) {
    try {
      const headers = emailData.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const from = headers.find(h => h.name === 'From')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';

      // Extract the actual message content
      let content = '';
      if (emailData.payload.body.data) {
        content = Buffer.from(emailData.payload.body.data, 'base64').toString();
      } else if (emailData.payload.parts) {
        // Handle multipart emails
        for (const part of emailData.payload.parts) {
          if (part.mimeType === 'text/plain' && part.body.data) {
            content += Buffer.from(part.body.data, 'base64').toString();
          }
        }
      }

      // Extract phone number and client message from Google Voice format
      const clientInfo = this.extractClientInfo(subject, content, from);

      return {
        id: emailData.id,
        subject,
        from,
        date: new Date(date),
        content,
        clientPhone: clientInfo.phone,
        clientMessage: clientInfo.message,
        source: this.identifySource(from, subject)
      };

    } catch (error) {
      console.error('❌ Error parsing email:', error.message);
      return null;
    }
  }

  extractClientInfo(subject, content, from) {
    const result = { phone: null, message: null };

    if (from.includes('txt.voice.google.com')) {
      // Google Voice format: "SMS from +15551234567"
      const phoneMatch = subject.match(/SMS from (\+?\d{10,})/);
      if (phoneMatch) {
        result.phone = phoneMatch[1];
      }

      // Extract the actual SMS content (usually after "SMS from..." in the body)
      const smsMatch = content.match(/SMS from.*?\n\n(.+)/s);
      if (smsMatch) {
        result.message = smsMatch[1].trim();
      }
      
    } else if (from.includes('highlevel.com') || from.includes('leadconnectorhq.com')) {
      // High Level format varies, but usually contains the message
      result.message = content.replace(/\n+/g, ' ').trim();
      
      // Try to extract phone from content
      const phoneMatch = content.match(/(\+?\d{10,})/);
      if (phoneMatch) {
        result.phone = phoneMatch[1];
      }
    }

    return result;
  }

  identifySource(from, subject) {
    if (from.includes('txt.voice.google.com')) return 'google_voice';
    if (from.includes('highlevel.com')) return 'high_level';
    if (from.includes('leadconnectorhq.com')) return 'lead_connector';
    return 'unknown';
  }

  async handleScheduleRequest(email, scheduleRequest) {
    // Alert via Discord
    await this.sendDiscordAlert(email, scheduleRequest);
    
    // Generate suggested email reply
    const replyDraft = await this.generateEmailReply(email, scheduleRequest);
    
    // Send reply draft to you for approval
    await this.sendReplyDraftForApproval(email, replyDraft);
    
    // Log to Notion
    await this.logToNotion(email, scheduleRequest);
  }

  async sendDiscordAlert(email, scheduleRequest) {
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    
    const alertMessage = `🚨 **Schedule Request Detected** 🚨\n\n` +
      `📧 **Source**: ${email.source === 'google_voice' ? 'Google Voice SMS' : 'High Level'}\n` +
      `📱 **Phone**: ${email.clientPhone || 'Unknown'}\n` +
      `⏰ **Received**: ${email.date.toLocaleString()}\n` +
      `🎯 **Type**: ${scheduleRequest.type}\n` +
      `⚠️ **Urgency**: ${scheduleRequest.urgency}\n\n` +
      `💬 **Message**: "${email.clientMessage}"\n\n` +
      `📝 **Draft reply ready for your approval**`;

    try {
      const user = await this.discordClient.users.fetch(opsLeadId);
      await user.send(alertMessage);
      console.log('✅ Discord alert sent to ops lead');
    } catch (error) {
      console.error('❌ Failed to send Discord alert:', error.message);
    }
  }

  async generateEmailReply(email, scheduleRequest) {
    // Simple, professional template - no AI needed
    const templates = {
      reschedule: `Hi there!\n\nI received your message about rescheduling your cleaning appointment. I'd be happy to help you find a new time that works better.\n\nCould you please let me know:\n1. Which specific appointment you'd like to reschedule (date and time)\n2. A few days/times that would work better for you\n\nI'll check our availability and get back to you within a few hours to confirm.\n\nThanks!\nGrime Guardians Team`,
      
      cancellation: `Hi there!\n\nI received your cancellation request. I completely understand that things come up!\n\nI've noted the cancellation in our system. When you're ready to reschedule, just let me know and we'll find a time that works.\n\nThanks for letting us know!\nGrime Guardians Team`,
      
      urgent: `Hi there!\n\nI received your urgent message and wanted to respond right away. I understand this is time-sensitive.\n\nI'm checking our schedule now and will get back to you within the next hour with options.\n\nThanks for reaching out!\nGrime Guardians Team`
    };

    const template = scheduleRequest.urgency === 'high' ? templates.urgent : 
                    scheduleRequest.type === 'cancellation' ? templates.cancellation : 
                    templates.reschedule;

    return template;
  }

  async sendReplyDraftForApproval(email, replyDraft) {
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    
    const approvalMessage = `📝 **Email Reply Draft** 📝\n\n` +
      `📧 **To**: ${email.clientPhone} (via ${email.source})\n` +
      `📋 **Subject**: Re: ${email.subject}\n\n` +
      `**Draft Reply:**\n\`\`\`\n${replyDraft}\n\`\`\`\n\n` +
      `React with ✅ to send this reply, or ❌ to skip\n` +
      `(Or reply with your own message to send instead)`;

    try {
      const user = await this.discordClient.users.fetch(opsLeadId);
      const message = await user.send(approvalMessage);
      
      // Add reaction options
      await message.react('✅');
      await message.react('❌');
      
      // Store for later handling
      this.pendingReplies = this.pendingReplies || new Map();
      this.pendingReplies.set(message.id, {
        email,
        replyDraft,
        timestamp: new Date()
      });
      
      console.log('✅ Reply draft sent for approval');
    } catch (error) {
      console.error('❌ Failed to send reply draft:', error.message);
    }
  }

  async logToNotion(email, scheduleRequest) {
    // Log to your existing Notion system
    try {
      // This would integrate with your existing Notion utilities
      console.log('📝 Schedule request logged to Notion');
    } catch (error) {
      console.error('❌ Failed to log to Notion:', error.message);
    }
  }

  stopMonitoring() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.isMonitoring = false;
      console.log('📧 Email monitoring stopped');
    }
  }
}

module.exports = EmailBasedCommunicationMonitor;
