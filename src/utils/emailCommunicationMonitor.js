/**
 * Email Communication Monitor - Unified monitoring system for both phone numbers
 * 
 * Monitors:
 * 1. Google Voice (612-584-9396) → Gmail email notifications
 * 2. High Level (651-515-1478) → API + optional email notifications
 * 
 * Features:
 * - Smart schedule request detection
 * - Professional auto-responses (with approval)
 * - Discord alerts and notifications
 * - Comprehensive logging to Notion
 * - Dual-channel redundancy
 */

const { google } = require('googleapis');
const { detectScheduleRequest } = require('./scheduleDetection');
const { getAllConversations, sendMessage } = require('./highlevel');
const { createScheduleRequestPage } = require('./notion');
require('dotenv').config();

class EmailCommunicationMonitor {
  constructor(client) {
    this.discordClient = client;
    this.gmail = null;
    this.isMonitoring = false;
    
    // Tracking
    this.lastEmailCheck = new Date();
    this.lastHighLevelCheck = new Date();
    this.processedEmailIds = new Set();
    this.processedHighLevelIds = new Set();
    this.pendingReplies = new Map();
    
    console.log('📧 Initializing Email Communication Monitor');
    console.log('📱 Channel 1: Google Voice (612-584-9396) → Gmail');
    console.log('📱 Channel 2: High Level (651-515-1478) → API Monitoring');
  }

  async initialize() {
    try {
      await this.initializeGmail();
      
      // Only test High Level if not disabled
      if (process.env.DISABLE_HIGHLEVEL !== 'true') {
        await this.testHighLevelConnection();
      } else {
        console.log('⚠️ High Level integration disabled - skipping connection test');
      }
      
      console.log('✅ Email communication monitor initialized');
      return true;
    } catch (error) {
      console.error('❌ Email monitor initialization failed:', error.message);
      
      // If High Level fails but Gmail works, continue with Gmail only
      if (process.env.DISABLE_HIGHLEVEL === 'true' || error.message.includes('High Level')) {
        console.log('⚠️ Continuing with Gmail-only monitoring');
        return true;
      }
      
      return false;
    }
  }

  async initializeGmail() {
    try {
      const auth = new google.auth.OAuth2(
        process.env.GMAIL_CLIENT_ID,
        process.env.GMAIL_CLIENT_SECRET,
        process.env.GMAIL_REDIRECT_URI
      );

      auth.setCredentials({
        refresh_token: process.env.GMAIL_REFRESH_TOKEN
      });

      this.gmail = google.gmail({ version: 'v1', auth });
      
      // Test connection
      await this.gmail.users.getProfile({ userId: 'me' });
      console.log('✅ Gmail API connected for Google Voice monitoring');
      
    } catch (error) {
      console.error('❌ Gmail initialization failed:', error.message);
      console.log('💡 Run: node scripts/setup-gmail-auth.js to set up Gmail API');
      throw error;
    }
  }

  async testHighLevelConnection() {
    try {
      const conversations = await getAllConversations();
      console.log('✅ High Level API connected');
    } catch (error) {
      console.error('❌ High Level connection failed:', error.message);
      throw error;
    }
  }

  async startMonitoring() {
    if (this.isMonitoring) {
      console.log('⚠️ Monitoring already active');
      return;
    }
    
    this.isMonitoring = true;
    console.log('🚀 Starting email-based communication monitoring...');
    console.log('📧 Checking Google Voice emails every 2 minutes');
    console.log('📱 Checking High Level conversations every 5 minutes');
    
    // Google Voice email monitoring (more frequent for legacy clients)
    this.googleVoiceInterval = setInterval(() => {
      this.checkGoogleVoiceEmails();
    }, 2 * 60 * 1000); // 2 minutes

    // High Level API monitoring
    this.highLevelInterval = setInterval(() => {
      this.checkHighLevelConversations();
    }, 5 * 60 * 1000); // 5 minutes

    // Initial checks
    await Promise.all([
      this.checkGoogleVoiceEmails(),
      this.checkHighLevelConversations()
    ]);
  }

  // === GOOGLE VOICE EMAIL MONITORING ===
  async checkGoogleVoiceEmails() {
    if (!this.gmail) {
      console.log('⚠️ Gmail not initialized, skipping Google Voice check');
      return;
    }

    try {
      console.log('📧 Checking Google Voice emails...');
      
      const query = this.buildGoogleVoiceQuery();
      
      const response = await this.gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 20
      });

      const messages = response.data.messages || [];
      let newMessages = 0;

      for (const message of messages) {
        if (!this.processedEmailIds.has(message.id)) {
          await this.processGoogleVoiceEmail(message.id);
          this.processedEmailIds.add(message.id);
          newMessages++;
        }
      }

      if (newMessages > 0) {
        console.log(`📧 Processed ${newMessages} new Google Voice messages`);
      }

      this.lastEmailCheck = new Date();
    } catch (error) {
      console.error('❌ Error checking Google Voice emails:', error.message);
    }
  }

  buildGoogleVoiceQuery() {
    // Search for Google Voice SMS emails since last check
    const date = this.lastEmailCheck.toISOString().split('T')[0].replace(/-/g, '/');
    
    return `after:${date} (` +
      `from:txt.voice.google.com OR ` +           // Standard Google Voice format
      `from:voice-noreply@google.com OR ` +       // Alternative format
      `subject:"SMS from +1612584" OR ` +         // Your specific number
      `subject:"New text message"` +              // Alternative subject format
      `)`;
  }

  async processGoogleVoiceEmail(messageId) {
    try {
      const message = await this.gmail.users.messages.get({
        userId: 'me',
        id: messageId,
        format: 'full'
      });

      const email = this.parseGoogleVoiceEmail(message.data);
      
      if (!email || !email.clientMessage) {
        return;
      }

      // Check for schedule requests
      const scheduleRequest = detectScheduleRequest(email.clientMessage);
      
      if (scheduleRequest.isScheduleRequest) {
        console.log(`🎯 Schedule request detected in Google Voice SMS from ${email.clientPhone}`);
        await this.handleScheduleRequest({
          ...email,
          source: 'google_voice',
          businessNumber: '612-584-9396'
        }, scheduleRequest);
      }

    } catch (error) {
      console.error('❌ Error processing Google Voice email:', error.message);
    }
  }

  parseGoogleVoiceEmail(emailData) {
    try {
      const headers = emailData.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const from = headers.find(h => h.name === 'From')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';

      // Extract email body
      let content = this.extractEmailBody(emailData.payload);
      
      // Parse Google Voice format
      const clientInfo = this.parseGoogleVoiceContent(subject, content);

      return {
        id: emailData.id,
        threadId: emailData.threadId,
        subject,
        from,
        date: new Date(date),
        content,
        clientPhone: clientInfo.phone,
        clientMessage: clientInfo.message,
        clientName: clientInfo.name
      };

    } catch (error) {
      console.error('❌ Error parsing Google Voice email:', error.message);
      return null;
    }
  }

  parseGoogleVoiceContent(subject, content) {
    const result = { phone: null, message: null, name: null };

    // Extract phone number from subject: "SMS from +16125849396"
    const phoneMatch = subject.match(/SMS from (\+?\d{10,})/);
    if (phoneMatch) {
      result.phone = phoneMatch[1];
    }

    // Extract message content - Google Voice emails have specific format
    const lines = content.split('\n');
    let messageStartIndex = -1;
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('SMS from') || lines[i].trim() === '') {
        continue;
      } else {
        messageStartIndex = i;
        break;
      }
    }
    
    if (messageStartIndex >= 0) {
      result.message = lines.slice(messageStartIndex).join('\n').trim();
    }

    return result;
  }

  extractEmailBody(payload) {
    let body = '';
    
    if (payload.body.data) {
      body = Buffer.from(payload.body.data, 'base64').toString();
    } else if (payload.parts) {
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          body += Buffer.from(part.body.data, 'base64').toString();
        }
      }
    }
    
    return body;
  }

  // === HIGH LEVEL CONVERSATION MONITORING ===
  async checkHighLevelConversations() {
    try {
      console.log('📱 Checking High Level conversations...');
      
      const conversations = await getAllConversations();
      let newMessages = 0;

      for (const conversation of conversations) {
        // Check for new messages since last check
        const recentMessages = this.filterRecentMessages(conversation.messages, this.lastHighLevelCheck);
        
        for (const message of recentMessages) {
          const messageId = `hl_${conversation.contactId}_${message.id}`;
          
          if (!this.processedHighLevelIds.has(messageId)) {
            await this.processHighLevelMessage(conversation, message);
            this.processedHighLevelIds.add(messageId);
            newMessages++;
          }
        }
      }

      if (newMessages > 0) {
        console.log(`📱 Processed ${newMessages} new High Level messages`);
      }

      this.lastHighLevelCheck = new Date();
    } catch (error) {
      console.error('❌ Error checking High Level conversations:', error.message);
    }
  }

  filterRecentMessages(messages, since) {
    if (!messages || !Array.isArray(messages)) return [];
    
    return messages.filter(msg => {
      const messageDate = new Date(msg.dateAdded);
      return messageDate > since && msg.direction === 'inbound';
    });
  }

  async processHighLevelMessage(conversation, message) {
    try {
      // Check for schedule requests
      const scheduleRequest = detectScheduleRequest(message.body);
      
      if (scheduleRequest.isScheduleRequest) {
        console.log(`🎯 Schedule request detected in High Level from ${conversation.contact?.name || 'Unknown'}`);
        
        await this.handleScheduleRequest({
          source: 'high_level',
          businessNumber: '651-515-1478',
          conversationId: conversation.id,
          contactId: conversation.contactId,
          clientName: conversation.contact?.name || 'Unknown',
          clientPhone: conversation.contact?.phone || '',
          clientMessage: message.body,
          timestamp: new Date(message.dateAdded)
        }, scheduleRequest);
      }

    } catch (error) {
      console.error('❌ Error processing High Level message:', error.message);
    }
  }

  // === UNIFIED SCHEDULE REQUEST HANDLING ===
  async handleScheduleRequest(messageData, scheduleRequest) {
    try {
      // 1. Send Discord alert
      await this.sendDiscordAlert(messageData, scheduleRequest);
      
      // 2. Generate reply draft
      const replyDraft = await this.generateReplyDraft(messageData, scheduleRequest);
      
      // 3. Send draft for approval
      await this.sendReplyForApproval(messageData, replyDraft);
      
      // 4. Log to Notion
      await this.logToNotion(messageData, scheduleRequest);
      
    } catch (error) {
      console.error('❌ Error handling schedule request:', error.message);
    }
  }

  async sendDiscordAlert(messageData, scheduleRequest) {
    try {
      const alertsChannel = this.discordClient.channels.cache.get(process.env.DISCORD_ALERTS_CHANNEL_ID);
      const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
      
      if (!alertsChannel) return;

      const urgencyEmoji = scheduleRequest.urgency === 'high' ? '🚨' : 
                          scheduleRequest.urgency === 'medium' ? '⚠️' : 'ℹ️';
      
      const embed = {
        color: scheduleRequest.urgency === 'high' ? 0xff0000 : 
               scheduleRequest.urgency === 'medium' ? 0xffaa00 : 0x0099ff,
        title: `${urgencyEmoji} Schedule Request Detected`,
        fields: [
          { name: '📞 Source', value: `${messageData.source.replace('_', ' ').toUpperCase()} (${messageData.businessNumber})`, inline: true },
          { name: '👤 Client', value: `${messageData.clientName || 'Unknown'}\n${messageData.clientPhone || 'No phone'}`, inline: true },
          { name: '📝 Request Type', value: scheduleRequest.type || 'General', inline: true },
          { name: '💬 Message', value: messageData.clientMessage.substring(0, 500), inline: false },
          { name: '🎯 Confidence', value: `${Math.round(scheduleRequest.confidence * 100)}%`, inline: true },
          { name: '🔑 Keywords', value: scheduleRequest.keywords.join(', '), inline: true }
        ],
        timestamp: new Date().toISOString(),
        footer: { text: 'Grime Guardians Schedule Monitor' }
      };

      await alertsChannel.send({
        content: `<@${opsLeadId}> New schedule request needs attention`,
        embeds: [embed]
      });

    } catch (error) {
      console.error('❌ Error sending Discord alert:', error.message);
    }
  }

  async generateReplyDraft(messageData, scheduleRequest) {
    const clientName = messageData.clientName || 'there';
    
    let replyTemplate;
    
    switch (scheduleRequest.type) {
      case 'reschedule':
        replyTemplate = `Hi ${clientName}! I received your request to reschedule. I'll check our availability and get back to you shortly with some options. Thanks for letting me know in advance!`;
        break;
      case 'cancellation':
        replyTemplate = `Hi ${clientName}! I got your cancellation request. I'll remove your appointment from our schedule. If you'd like to reschedule for another time, just let me know!`;
        break;
      case 'postpone':
        replyTemplate = `Hi ${clientName}! I understand you need to postpone your cleaning. I'll hold off on scheduling and reach out soon to find a better time that works for you.`;
        break;
      default:
        replyTemplate = `Hi ${clientName}! I received your message about your cleaning appointment. I'll review your request and get back to you shortly. Thanks for reaching out!`;
    }
    
    return replyTemplate;
  }

  async sendReplyForApproval(messageData, replyDraft) {
    try {
      const opsLead = await this.discordClient.users.fetch(process.env.OPS_LEAD_DISCORD_ID);
      
      const embed = {
        color: 0x00ff00,
        title: '✅ Reply Draft Ready for Approval',
        fields: [
          { name: '📞 Channel', value: messageData.source.replace('_', ' ').toUpperCase(), inline: true },
          { name: '👤 Client', value: messageData.clientName || 'Unknown', inline: true },
          { name: '📱 Phone', value: messageData.clientPhone || 'N/A', inline: true },
          { name: '💬 Original Message', value: messageData.clientMessage.substring(0, 200) + '...', inline: false },
          { name: '📝 Suggested Reply', value: replyDraft, inline: false }
        ],
        footer: { text: 'React with ✅ to approve and send, or ❌ to cancel' }
      };

      const dmMessage = await opsLead.send({ embeds: [embed] });
      
      // Add reaction options
      await dmMessage.react('✅');
      await dmMessage.react('❌');
      
      // Store for approval handling
      this.pendingReplies.set(dmMessage.id, {
        messageData,
        replyDraft,
        timestamp: new Date()
      });

    } catch (error) {
      console.error('❌ Error sending reply for approval:', error.message);
    }
  }

  async logToNotion(messageData, scheduleRequest) {
    try {
      const pageData = {
        clientName: messageData.clientName || 'Unknown',
        clientPhone: messageData.clientPhone || '',
        source: messageData.source,
        businessNumber: messageData.businessNumber,
        message: messageData.clientMessage,
        requestType: scheduleRequest.type || 'General',
        urgency: scheduleRequest.urgency || 'medium',
        confidence: scheduleRequest.confidence || 0,
        keywords: scheduleRequest.keywords || [],
        timestamp: messageData.timestamp || new Date(),
        status: 'Pending Response'
      };

      await createScheduleRequestPage(pageData);
      console.log('✅ Schedule request logged to Notion');

    } catch (error) {
      console.error('❌ Error logging to Notion:', error.message);
    }
  }

  // === REPLY APPROVAL HANDLING ===
  async handleApprovalReaction(messageId, emoji, userId) {
    if (userId !== process.env.OPS_LEAD_DISCORD_ID) return;
    
    const pendingReply = this.pendingReplies.get(messageId);
    if (!pendingReply) return;

    if (emoji === '✅') {
      await this.sendApprovedReply(pendingReply);
      console.log('✅ Reply approved and sent');
    } else if (emoji === '❌') {
      console.log('❌ Reply cancelled by operator');
    }

    // Clean up
    this.pendingReplies.delete(messageId);
  }

  async sendApprovedReply(pendingReply) {
    const { messageData, replyDraft } = pendingReply;
    
    try {
      if (messageData.source === 'google_voice') {
        // Send via Gmail (will forward as SMS through Google Voice)
        await this.sendGmailReply(messageData, replyDraft);
      } else if (messageData.source === 'high_level') {
        // Send via High Level API
        await this.sendHighLevelReply(messageData, replyDraft);
      }
    } catch (error) {
      console.error('❌ Error sending approved reply:', error.message);
    }
  }

  async sendGmailReply(messageData, replyText) {
    try {
      // Compose email reply that will trigger SMS through Google Voice
      const emailContent = [
        `To: ${messageData.from}`,
        `Subject: Re: ${messageData.subject}`,
        `In-Reply-To: ${messageData.id}`,
        `References: ${messageData.id}`,
        ``,
        replyText
      ].join('\n');

      const encodedMessage = Buffer.from(emailContent)
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');

      await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          threadId: messageData.threadId,
          raw: encodedMessage
        }
      });

      console.log(`✅ Gmail reply sent (will forward as SMS to ${messageData.clientPhone})`);

    } catch (error) {
      console.error('❌ Error sending Gmail reply:', error.message);
      throw error;
    }
  }

  async sendHighLevelReply(messageData, replyText) {
    try {
      // Use High Level API to send reply
      const { sendMessage } = require('./highlevel');
      
      await sendMessage(messageData.contactId, replyText);
      console.log(`✅ High Level reply sent to ${messageData.clientName}`);

    } catch (error) {
      console.error('❌ Error sending High Level reply:', error.message);
      throw error;
    }
  }

  // === MONITORING CONTROL ===
  stopMonitoring() {
    if (this.googleVoiceInterval) {
      clearInterval(this.googleVoiceInterval);
    }
    if (this.highLevelInterval) {
      clearInterval(this.highLevelInterval);
    }
    
    this.isMonitoring = false;
    console.log('🛑 Email communication monitoring stopped');
  }

  getMonitoringStatus() {
    return {
      isActive: this.isMonitoring,
      lastEmailCheck: this.lastEmailCheck,
      lastHighLevelCheck: this.lastHighLevelCheck,
      processedEmails: this.processedEmailIds.size,
      processedHighLevelMessages: this.processedHighLevelIds.size,
      pendingApprovals: this.pendingReplies.size,
      channels: {
        googleVoice: {
          number: '612-584-9396',
          method: 'Gmail API',
          status: this.gmail ? 'Connected' : 'Disconnected'
        },
        highLevel: {
          number: '651-515-1478',
          method: 'API Monitoring',
          status: 'Connected'
        }
      }
    };
  }
}

module.exports = EmailCommunicationMonitor;
