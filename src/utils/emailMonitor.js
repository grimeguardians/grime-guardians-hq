/**
 * Email Communication Monitor
 * Monitors Gmail for Google Voice SMS notifications and client emails
 * Responds via email which automatically sends SMS through Google Voice
 */

const { google } = require('googleapis');
const fs = require('fs').promises;
const path = require('path');

class EmailMonitor {
  constructor() {
    this.gmail = null;
    this.lastCheckTime = new Date();
    this.scheduleKeywords = [
      'reschedule', 'schedule', 'move', 'change', 'cancel', 'postpone', 
      'different time', 'another day', 'emergency', 'sick', 'urgent'
    ];
  }

  async initialize() {
    try {
      // Initialize Gmail API
      const auth = await this.getGmailAuth();
      this.gmail = google.gmail({ version: 'v1', auth });
      console.log('✅ Email monitor initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Email monitor initialization failed:', error.message);
      return false;
    }
  }

  async getGmailAuth() {
    // OAuth2 setup for Gmail API
    const oauth2Client = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );

    // Set refresh token (you'll get this during initial OAuth setup)
    oauth2Client.setCredentials({
      refresh_token: process.env.GMAIL_REFRESH_TOKEN
    });

    return oauth2Client;
  }

  async checkForNewMessages() {
    if (!this.gmail) {
      console.log('⚠️ Gmail not initialized, skipping email check');
      return [];
    }

    try {
      // Search for messages since last check
      const query = this.buildSearchQuery();
      
      const response = await this.gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 50
      });

      if (!response.data.messages) {
        return [];
      }

      const messages = [];
      for (const message of response.data.messages) {
        const fullMessage = await this.gmail.users.messages.get({
          userId: 'me',
          id: message.id
        });

        const processedMessage = await this.processMessage(fullMessage.data);
        if (processedMessage) {
          messages.push(processedMessage);
        }
      }

      this.lastCheckTime = new Date();
      return messages;

    } catch (error) {
      console.error('❌ Error checking email messages:', error.message);
      return [];
    }
  }

  buildSearchQuery() {
    // Build Gmail search query for:
    // 1. Google Voice SMS notifications
    // 2. Direct client emails
    // 3. Messages since last check
    
    const timeStamp = Math.floor(this.lastCheckTime.getTime() / 1000);
    
    return [
      `after:${timeStamp}`,
      '(',
      'from:txt.voice.google.com', // Google Voice SMS notifications
      'OR',
      'subject:"New text message"', // Alternative Google Voice format
      'OR',
      '(', // Direct client emails with schedule keywords
      this.scheduleKeywords.map(keyword => `subject:${keyword}`).join(' OR '),
      ')',
      ')'
    ].join(' ');
  }

  async processMessage(message) {
    try {
      const headers = message.payload.headers;
      const from = this.getHeader(headers, 'From');
      const subject = this.getHeader(headers, 'Subject');
      const date = this.getHeader(headers, 'Date');
      
      // Extract message body
      const body = this.extractMessageBody(message.payload);
      
      // Determine if this is a Google Voice SMS or direct email
      const isGoogleVoiceSMS = from.includes('txt.voice.google.com') || 
                               subject.includes('New text message');
      
      let clientPhone = null;
      let clientMessage = body;
      
      if (isGoogleVoiceSMS) {
        // Extract phone number and message from Google Voice notification
        const voiceData = this.parseGoogleVoiceNotification(body, subject);
        clientPhone = voiceData.phone;
        clientMessage = voiceData.message;
        
        if (!clientPhone || !clientMessage) {
          return null; // Skip if we can't parse the notification
        }
      }

      // Check if message contains schedule-related keywords
      const hasScheduleKeywords = this.scheduleKeywords.some(keyword => 
        clientMessage.toLowerCase().includes(keyword.toLowerCase())
      );

      if (!hasScheduleKeywords) {
        return null; // Skip non-schedule messages
      }

      // Determine urgency based on keywords
      const urgentKeywords = ['emergency', 'urgent', 'asap', 'today', 'now', 'sick'];
      const urgency = urgentKeywords.some(keyword => 
        clientMessage.toLowerCase().includes(keyword.toLowerCase())
      ) ? 'HIGH' : 'MEDIUM';

      return {
        id: message.id,
        source: isGoogleVoiceSMS ? 'google_voice_sms' : 'direct_email',
        from: isGoogleVoiceSMS ? clientPhone : from,
        subject: subject,
        message: clientMessage,
        timestamp: new Date(date),
        urgency: urgency,
        hasScheduleRequest: true,
        originalEmailFrom: from,
        threadId: message.threadId
      };

    } catch (error) {
      console.error('❌ Error processing message:', error.message);
      return null;
    }
  }

  parseGoogleVoiceNotification(body, subject) {
    // Parse Google Voice email notification to extract phone number and SMS content
    // Example formats:
    // "New text message from +1 555-123-4567: I need to reschedule..."
    // Body might contain: "(555) 123-4567: I need to reschedule tomorrow's cleaning"
    
    let phone = null;
    let message = null;

    // Try to extract phone from subject line
    const subjectPhoneMatch = subject.match(/from\s+(\+?1?\s?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})/i);
    if (subjectPhoneMatch) {
      phone = subjectPhoneMatch[1].replace(/\D/g, ''); // Remove non-digits
      if (phone.length === 10) phone = '+1' + phone;
      if (phone.length === 11 && phone.startsWith('1')) phone = '+' + phone;
    }

    // Try to extract message from body
    // Look for pattern: "phone: message" or just use full body
    const messageMatch = body.match(/\([0-9]{3}\)\s[0-9]{3}-[0-9]{4}:\s*(.+)/s) ||
                         body.match(/\+1\s[0-9]{3}-[0-9]{3}-[0-9]{4}:\s*(.+)/s);
    
    if (messageMatch) {
      message = messageMatch[1].trim();
    } else {
      // Use full body if no pattern match
      message = body.trim();
    }

    return { phone, message };
  }

  getHeader(headers, name) {
    const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
    return header ? header.value : '';
  }

  extractMessageBody(payload) {
    // Extract text from email body (handle multipart messages)
    if (payload.body && payload.body.data) {
      return Buffer.from(payload.body.data, 'base64').toString('utf-8');
    }

    if (payload.parts) {
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body && part.body.data) {
          return Buffer.from(part.body.data, 'base64').toString('utf-8');
        }
      }
    }

    return '';
  }

  async sendEmailResponse(threadId, recipientEmail, subject, message) {
    try {
      // Compose email response
      const emailContent = [
        `To: ${recipientEmail}`,
        `Subject: Re: ${subject}`,
        ``,
        message
      ].join('\n');

      const encodedMessage = Buffer.from(emailContent).toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');

      // Send email (which will trigger SMS if it's a Google Voice thread)
      await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          threadId: threadId,
          raw: encodedMessage
        }
      });

      console.log(`✅ Email response sent to ${recipientEmail}`);
      return true;

    } catch (error) {
      console.error('❌ Error sending email response:', error.message);
      return false;
    }
  }

  // Generate professional response based on message type
  generateAutoResponse(messageData) {
    const { message, urgency, source } = messageData;
    
    // Determine message type
    let messageType = 'general';
    if (message.toLowerCase().includes('cancel')) {
      messageType = 'cancellation';
    } else if (message.toLowerCase().includes('reschedule') || message.toLowerCase().includes('move')) {
      messageType = 'reschedule';
    } else if (message.toLowerCase().includes('emergency') || message.toLowerCase().includes('urgent')) {
      messageType = 'urgent';
    }

    // Generate appropriate response
    const responses = {
      urgent: `Hi! We received your urgent message and completely understand. We're reviewing your request immediately and will get back to you within 30 minutes. Thank you for letting us know! 💙

- Grime Guardians Team`,

      cancellation: `Hi! We received your cancellation request and completely understand - things come up! We've noted this and will follow up shortly to reschedule when you're ready. Thanks for the heads up! 💙

- Grime Guardians Team`,

      reschedule: `Hi! We'd be happy to help reschedule your cleaning appointment. We received your request and are checking our availability now. We'll get back to you within a few hours with available times. Thank you! 💙

- Grime Guardians Team`,

      general: `Hi! We received your message about your cleaning appointment and are reviewing it now. We'll get back to you shortly with next steps. Thank you for reaching out! 💙

- Grime Guardians Team`
    };

    return responses[messageType] || responses.general;
  }

  // Start monitoring emails at regular intervals
  startMonitoring(intervalMinutes = 5) {
    console.log(`🔄 Starting email monitoring (checking every ${intervalMinutes} minutes)`);
    
    setInterval(async () => {
      try {
        const messages = await this.checkForNewMessages();
        
        if (messages.length > 0) {
          console.log(`📧 Found ${messages.length} new schedule-related messages`);
          
          // Process each message
          for (const message of messages) {
            await this.handleScheduleMessage(message);
          }
        }
      } catch (error) {
        console.error('❌ Error in email monitoring loop:', error.message);
      }
    }, intervalMinutes * 60 * 1000);
  }

  async handleScheduleMessage(messageData) {
    try {
      console.log(`📧 Processing schedule message from ${messageData.from}`);
      
      // Generate and send auto-response
      const autoResponse = this.generateAutoResponse(messageData);
      
      await this.sendEmailResponse(
        messageData.threadId,
        messageData.originalEmailFrom,
        messageData.subject,
        autoResponse
      );

      // Return data for further processing by Schedule Manager
      return {
        success: true,
        messageData,
        responsesent: true
      };

    } catch (error) {
      console.error('❌ Error handling schedule message:', error.message);
      return { success: false, error: error.message };
    }
  }
}

module.exports = EmailMonitor;
