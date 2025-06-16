/**
 * Dual-Channel Communication Monitor for Grime Guardians
 * 
 * Monitors BOTH communication channels:
 * 1. Google Voice (612-584-9396) → broberts111592@gmail.com 
 * 2. High Level (651-515-1478) → High Level API + email notifications
 * 
 * Detects schedule requests and routes them to Schedule Manager
 */

const { google } = require('googleapis');
const { detectScheduleRequest } = require('./scheduleDetection');
const { getAllConversations } = require('./highlevel');

class DualChannelCommunicationMonitor {
  constructor(client) {
    this.discordClient = client;
    this.gmail = null;
    this.isMonitoring = false;
    this.lastEmailCheck = new Date();
    this.lastHighLevelCheck = new Date();
    
    // Track processed messages to avoid duplicates
    this.processedEmailIds = new Set();
    this.processedHighLevelIds = new Set();
    
    console.log('🎯 Initializing Dual-Channel Communication Monitor');
    console.log('📱 Channel 1: Google Voice (612-584-9396) → Gmail');
    console.log('📱 Channel 2: High Level (651-515-1478) → High Level API');
  }

  async initialize() {
    try {
      // Initialize Gmail API for Google Voice monitoring
      await this.initializeGmail();
      
      // Test High Level API connection
      await this.testHighLevelConnection();
      
      console.log('✅ Dual-channel monitoring initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize communication monitor:', error.message);
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
      
      // Test the connection
      await this.gmail.users.getProfile({ userId: 'me' });
      console.log('✅ Gmail API connected for Google Voice monitoring');
      
    } catch (error) {
      console.error('❌ Gmail initialization failed:', error.message);
      throw error;
    }
  }

  async testHighLevelConnection() {
    try {
      // Test with a simple API call
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
    console.log('🚀 Starting dual-channel communication monitoring...');
    console.log('📧 Checking Google Voice emails every 3 minutes');
    console.log('📱 Checking High Level conversations every 5 minutes');
    
    // Check Google Voice emails every 3 minutes (more responsive for legacy clients)
    this.googleVoiceInterval = setInterval(() => {
      this.checkGoogleVoiceEmails();
    }, 3 * 60 * 1000);

    // Check High Level conversations every 5 minutes
    this.highLevelInterval = setInterval(() => {
      this.checkHighLevelConversations();
    }, 5 * 60 * 1000);

    // Initial checks
    await Promise.all([
      this.checkGoogleVoiceEmails(),
      this.checkHighLevelConversations()
    ]);
  }

  // === GOOGLE VOICE EMAIL MONITORING ===
  async checkGoogleVoiceEmails() {
    try {
      console.log('📧 Checking Google Voice emails...');
      
      // Search for new Google Voice SMS emails
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
      `subject:"Voicemail from +1612584"` +       // Voicemails too
      `) -label:processed`;                       // Exclude already processed
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

        // Label as processed in Gmail
        await this.labelEmailAsProcessed(messageId);
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

      // Extract SMS content
      let content = this.extractEmailBody(emailData.payload);
      
      // Parse Google Voice format
      const clientInfo = this.parseGoogleVoiceContent(subject, content);

      return {
        id: emailData.id,
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
    // Usually: "SMS from +number at time\n\nActual message here"
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
    return messages.filter(msg => {
      const msgDate = new Date(msg.dateAdded);
      return msgDate > since && msg.direction === 'inbound'; // Only client messages
    });
  }

  async processHighLevelMessage(conversation, message) {
    try {
      // Check for schedule requests
      const scheduleRequest = detectScheduleRequest(message.body);
      
      if (scheduleRequest.isScheduleRequest) {
        console.log(`🎯 Schedule request detected in High Level conversation from ${conversation.contact.phone}`);
        
        await this.handleScheduleRequest({
          id: message.id,
          clientPhone: conversation.contact.phone,
          clientMessage: message.body,
          clientName: `${conversation.contact.firstName} ${conversation.contact.lastName}`.trim(),
          source: 'high_level',
          businessNumber: '651-515-1478',
          conversationId: conversation.id,
          contactId: conversation.contactId,
          date: new Date(message.dateAdded)
        }, scheduleRequest);
      }

    } catch (error) {
      console.error('❌ Error processing High Level message:', error.message);
    }
  }

  // === UNIFIED SCHEDULE REQUEST HANDLING ===
  async handleScheduleRequest(messageData, scheduleRequest) {
    try {
      // Send Discord alert
      await this.sendDiscordAlert(messageData, scheduleRequest);
      
      // Generate and send reply draft for approval
      const replyDraft = this.generateReplyDraft(messageData, scheduleRequest);
      await this.sendReplyDraftForApproval(messageData, replyDraft);
      
      // Log to system
      await this.logScheduleRequest(messageData, scheduleRequest);
      
    } catch (error) {
      console.error('❌ Error handling schedule request:', error.message);
    }
  }

  async sendDiscordAlert(messageData, scheduleRequest) {
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    
    const sourceDisplay = messageData.source === 'google_voice' ? 
      '📧 Google Voice (612-584-9396)' : 
      '📱 High Level (651-515-1478)';
      
    const clientDisplay = messageData.clientName ? 
      `${messageData.clientName} (${messageData.clientPhone})` : 
      messageData.clientPhone;

    const alertMessage = `🚨 **Schedule Request Detected** 🚨\n\n` +
      `📍 **Source**: ${sourceDisplay}\n` +
      `👤 **Client**: ${clientDisplay}\n` +
      `⏰ **Received**: ${messageData.date.toLocaleString()}\n` +
      `🎯 **Type**: ${scheduleRequest.type}\n` +
      `⚠️ **Urgency**: ${scheduleRequest.urgency.toUpperCase()}\n\n` +
      `💬 **Message**: "${messageData.clientMessage}"\n\n` +
      `📝 Reply draft being prepared for your approval...`;

    try {
      const user = await this.discordClient.users.fetch(opsLeadId);
      await user.send(alertMessage);
      console.log('✅ Discord alert sent to ops lead');
    } catch (error) {
      console.error('❌ Failed to send Discord alert:', error.message);
    }
  }

  generateReplyDraft(messageData, scheduleRequest) {
    const isUrgent = scheduleRequest.urgency === 'high';
    const isCancellation = scheduleRequest.type === 'cancellation';
    
    if (isUrgent) {
      return `Hi ${messageData.clientName || 'there'}! 👋\n\n` +
        `I received your urgent message and wanted to respond right away. I completely understand this is time-sensitive.\n\n` +
        `I'm checking our schedule now and will get back to you within the next hour with options.\n\n` +
        `Thanks for letting me know!\n` +
        `Brandon - Grime Guardians`;
    }
    
    if (isCancellation) {
      return `Hi ${messageData.clientName || 'there'}! 👋\n\n` +
        `I received your cancellation request and completely understand that things come up!\n\n` +
        `I've noted the cancellation in our system. When you're ready to reschedule, just let me know and we'll find a time that works perfectly.\n\n` +
        `Thanks for giving us a heads up!\n` +
        `Brandon - Grime Guardians`;
    }
    
    // Standard reschedule request
    return `Hi ${messageData.clientName || 'there'}! 👋\n\n` +
      `I received your message about rescheduling your cleaning appointment. I'd be happy to help you find a new time that works better.\n\n` +
      `Could you please let me know:\n` +
      `1. Which specific appointment you'd like to reschedule (date/time if you remember)\n` +
      `2. A few days/times that would work better for you\n\n` +
      `I'll check our availability and get back to you within a few hours to confirm the new time.\n\n` +
      `Thanks!\n` +
      `Brandon - Grime Guardians`;
  }

  async sendReplyDraftForApproval(messageData, replyDraft) {
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    
    const sourceEmoji = messageData.source === 'google_voice' ? '📧' : '📱';
    const replyMethod = messageData.source === 'google_voice' ? 
      'Reply to Gmail (→ Google Voice SMS)' : 
      'Send via High Level';

    const approvalMessage = `📝 **Reply Draft Ready** 📝\n\n` +
      `${sourceEmoji} **To**: ${messageData.clientName || 'Client'} (${messageData.clientPhone})\n` +
      `📤 **Method**: ${replyMethod}\n\n` +
      `**Draft Reply:**\n\`\`\`\n${replyDraft}\n\`\`\`\n\n` +
      `React with ✅ to approve and send, or ❌ to skip\n` +
      `(Or reply with your own message to customize)`;

    try {
      const user = await this.discordClient.users.fetch(opsLeadId);
      const message = await user.send(approvalMessage);
      
      // Add reaction options
      await message.react('✅');
      await message.react('❌');
      
      // Store for handling approval
      this.pendingReplies = this.pendingReplies || new Map();
      this.pendingReplies.set(message.id, {
        messageData,
        replyDraft,
        timestamp: new Date()
      });
      
      console.log('✅ Reply draft sent for approval');
    } catch (error) {
      console.error('❌ Failed to send reply draft:', error.message);
    }
  }

  async logScheduleRequest(messageData, scheduleRequest) {
    try {
      console.log(`📝 Logging schedule request from ${messageData.clientPhone} (${messageData.source})`);
      
      // This would integrate with your existing Notion logging
      // For now, just console log the structured data
      const logData = {
        timestamp: messageData.date.toISOString(),
        source: messageData.source,
        businessNumber: messageData.businessNumber,
        clientPhone: messageData.clientPhone,
        clientName: messageData.clientName,
        requestType: scheduleRequest.type,
        urgency: scheduleRequest.urgency,
        originalMessage: messageData.clientMessage,
        keywords: scheduleRequest.keywords
      };
      
      console.log('📋 Schedule request logged:', JSON.stringify(logData, null, 2));
      
    } catch (error) {
      console.error('❌ Failed to log schedule request:', error.message);
    }
  }

  // === UTILITY METHODS ===
  extractEmailBody(payload) {
    let content = '';
    
    if (payload.body && payload.body.data) {
      content = Buffer.from(payload.body.data, 'base64').toString();
    } else if (payload.parts) {
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          content += Buffer.from(part.body.data, 'base64').toString();
        }
      }
    }
    
    return content;
  }

  async labelEmailAsProcessed(messageId) {
    try {
      // Create or find "processed" label
      const labelsResponse = await this.gmail.users.labels.list({ userId: 'me' });
      const labels = labelsResponse.data.labels;
      
      let processedLabelId = labels.find(label => label.name === 'processed')?.id;
      
      if (!processedLabelId) {
        // Create the label if it doesn't exist
        const newLabel = await this.gmail.users.labels.create({
          userId: 'me',
          requestBody: {
            name: 'processed',
            messageListVisibility: 'hide',
            labelListVisibility: 'labelHide'
          }
        });
        processedLabelId = newLabel.data.id;
      }
      
      // Apply the label
      await this.gmail.users.messages.modify({
        userId: 'me',
        id: messageId,
        requestBody: {
          addLabelIds: [processedLabelId]
        }
      });
      
    } catch (error) {
      console.error('❌ Failed to label email as processed:', error.message);
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
    console.log('🛑 Dual-channel monitoring stopped');
  }

  getMonitoringStatus() {
    return {
      isActive: this.isMonitoring,
      lastEmailCheck: this.lastEmailCheck,
      lastHighLevelCheck: this.lastHighLevelCheck,
      processedEmails: this.processedEmailIds.size,
      processedHighLevelMessages: this.processedHighLevelIds.size,
      pendingReplies: this.pendingReplies?.size || 0
    };
  }
}

module.exports = DualChannelCommunicationMonitor;
