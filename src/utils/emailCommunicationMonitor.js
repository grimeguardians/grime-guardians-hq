/**
 * Email Communication Monitor - Gmail monitoring for direct emails only
 * 
 * Monitors:
 * 1. Direct Gmail emails to your business accounts
 * 2. High Level (651-515-1478) → API + optional email notifications
 * 
 * Features:
 * - Smart schedule request detection
 * - Professional auto-responses (with approval)
 * - Discord alerts and notifications
 * - Comprehensive logging to Notion
 * - Gmail monitoring (Google Voice handled separately via API)
 */

const { google } = require('googleapis');
const { detectScheduleRequest } = require('./scheduleDetection');
const { getAllJobs } = require('./highlevel');
const { createScheduleRequestPage } = require('./notion');
const MessageClassifier = require('./messageClassifier');
const AvaTrainingSystem = require('./avaTrainingSystem');
const ConversationManager = require('./conversationManager');
require('dotenv').config();

class EmailCommunicationMonitor {
  constructor(client) {
    this.discordClient = client;
    this.gmail = null;
    this.isMonitoring = false;
    
    // Enhanced AI components
    this.messageClassifier = new MessageClassifier();
    this.trainingSystem = new AvaTrainingSystem(client);
    this.conversationManager = new ConversationManager(client);
    
    // Tracking
    this.lastEmailCheck = new Date();
    this.lastHighLevelCheck = new Date();
    this.processedEmailIds = new Set();
    this.processedHighLevelIds = new Set();
    this.pendingReplies = new Map();
    
    // Configuration flags
    this.monitorGoogleVoiceEmails = true;  // ENABLED - Monitor Google Voice via Gmail
    this.monitorBusinessEmails = true;     // Monitor direct business emails
    this.monitorHighLevel = true;          // Continue High Level monitoring
    console.log('🧠 Enhanced with GPT-4 classification and training system');
    console.log('📧 Gmail monitoring for Google Voice and business emails');
    console.log('📱 High Level (651-515-1478) → API Monitoring');
    console.log('📱 Google Voice (612-584-9396) → Gmail Integration ACTIVE');
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
      // Initialize Gmail clients for each email account
      this.gmailClients = new Map();
      const emailAddresses = process.env.GMAIL_EMAILS ? process.env.GMAIL_EMAILS.split(',') : [];
      
      if (emailAddresses.length === 0) {
        throw new Error('No Gmail emails configured in GMAIL_EMAILS environment variable');
      }
      
      const fs = require('fs');
      const path = require('path');
      
      for (const email of emailAddresses) {
        const trimmedEmail = email.trim();
        const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${trimmedEmail}.json`);
        
        if (!fs.existsSync(tokenFilePath)) {
          console.warn(`⚠️ Token file not found for ${trimmedEmail}: ${tokenFilePath}`);
          continue;
        }
        
        try {
          const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
          
          const auth = new google.auth.OAuth2(
            process.env.GMAIL_CLIENT_ID,
            process.env.GMAIL_CLIENT_SECRET,
            process.env.GMAIL_REDIRECT_URI
          );
          
          auth.setCredentials(tokens);
          
          const gmailClient = google.gmail({ version: 'v1', auth });
          
          // Test connection
          await gmailClient.users.getProfile({ userId: 'me' });
          
          this.gmailClients.set(trimmedEmail, gmailClient);
          console.log(`✅ Gmail API connected for ${trimmedEmail}`);
          
        } catch (tokenError) {
          console.error(`❌ Failed to initialize Gmail for ${trimmedEmail}:`, tokenError.message);
        }
      }
      
      if (this.gmailClients.size === 0) {
        throw new Error('No Gmail accounts could be initialized');
      }
      
      // Set primary gmail client (for backward compatibility)
      this.gmail = this.gmailClients.values().next().value;
      
      // Log which account is being used for monitoring
      const primaryEmail = this.gmail?.auth?.credentials?.email || 'unknown';
      console.log(`📧 Primary Gmail client set for monitoring: ${primaryEmail}`);
      
      console.log(`✅ Gmail monitoring initialized for ${this.gmailClients.size} email account(s)`);
      
    } catch (error) {
      console.error('❌ Gmail initialization failed:', error.message);
      console.log('💡 Run: node scripts/setup-gmail-auth.js to set up Gmail API');
      throw error;
    }
  }

  async testHighLevelConnection() {
    try {
      // Test with contacts endpoint (we know this works)
      const fetch = require('node-fetch');
      const testUrl = `https://rest.gohighlevel.com/v1/contacts/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`;
      
      const res = await fetch(testUrl, {
        headers: {
          Authorization: `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
          Accept: 'application/json'
        }
      });
      
      if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
      
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
    console.log('📧 Checking business emails every 2 minutes (testing mode)');
    console.log('📱 Checking High Level conversations every 5 minutes');
    
    // Business email monitoring - reduced to 2 minutes for faster testing
    this.emailInterval = setInterval(() => {
      console.log('⏰ INTERVAL TRIGGERED: Checking business emails...');
      this.checkBusinessEmails();
    }, 2 * 60 * 1000); // 2 minutes for testing

    // High Level API monitoring
    this.highLevelInterval = setInterval(() => {
      console.log('⏰ INTERVAL TRIGGERED: Checking High Level...');
      this.checkHighLevelConversations();
    }, 5 * 60 * 1000); // 5 minutes

    // Initial checks
    await Promise.all([
      this.checkBusinessEmails(),
      this.checkHighLevelConversations()
    ]);
  }

  // === BUSINESS EMAIL MONITORING ===
  async checkBusinessEmails() {
    console.log(`🔍 DEBUG: Gmail client exists = ${!!this.gmail}`);
    
    // Use the specific Gmail client that has Google Voice linked
    const googleVoiceGmail = this.gmailClients.get('broberts111592@gmail.com');
    console.log(`🔍 DEBUG: Google Voice Gmail client exists = ${!!googleVoiceGmail}`);
    
    if (!googleVoiceGmail) {
      console.log('⚠️ Google Voice Gmail account (broberts111592@gmail.com) not initialized, skipping Google Voice check');
      return;
    }

    const timestamp = new Date().toISOString();
    console.log(`📧 [${timestamp}] Checking Google Voice emails in broberts111592@gmail.com...`);

    try {
      console.log(`🔍 DEBUG: monitorGoogleVoiceEmails = ${this.monitorGoogleVoiceEmails}`);
      
      // Search for Google Voice SMS notifications - FILTER OUT SPAM
      // Updated to catch all text message formats while filtering spam short codes
      const query = 'from:voice-noreply@google.com ("New text message" OR "New group message") is:unread -"verification code" -"Indeed" -"Stripe" -"Discord" -from:31061 -from:22395 -from:65161';
      console.log(`🔍 DEBUG: Gmail query = ${query}`);
      
      const messages = await googleVoiceGmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 10
      });

      console.log(`🔍 DEBUG: Gmail response - ${messages.data.messages?.length || 0} messages found`);
      
      if (!messages.data.messages || messages.data.messages.length === 0) {
        console.log('📧 No new customer Google Voice messages found (spam filtered out)');
        return;
      }

      console.log(`📧 Found ${messages.data.messages.length} customer Google Voice messages - PROCESSING...`);
      
      // Process each message with additional spam filtering
      for (const messageRef of messages.data.messages) {
        const email = await googleVoiceGmail.users.messages.get({
          userId: 'me',
          id: messageRef.id
        });

        const parsedEmail = this.parseGoogleVoiceEmail(email.data);
        if (parsedEmail && this.isCustomerMessage(parsedEmail)) {
          console.log(`✅ CUSTOMER MESSAGE DETECTED from ${parsedEmail.clientName}`);
          await this.processGoogleVoiceMessage(parsedEmail);
          
          // Mark as read
          await googleVoiceGmail.users.messages.modify({
            userId: 'me',
            id: messageRef.id,
            resource: {
              removeLabelIds: ['UNREAD']
            }
          });
        } else {
          console.log(`� SPAM/VERIFICATION CODE FILTERED: ${parsedEmail?.subject || 'Unknown'}`);
        }
      }

      console.log(`📧 Finished processing customer Google Voice messages`);
      
    } catch (error) {
      console.error('❌ Error checking Google Voice emails:', error.message);
    }
  }

  /**
   * Process a Google Voice message through the conversation manager
   */
  async processGoogleVoiceMessage(email) {
    try {
      console.log(`📞 Processing Google Voice message from ${email.clientPhone}`);
      console.log(`📝 Message content: "${email.clientMessage.substring(0, 100)}..."`);
      
      // Process with conversation manager for context awareness
      const conversationResult = await this.conversationManager.processMessage({
        ...email,
        source: 'google_voice'
      });

      console.log(`🔄 Conversation result: ${conversationResult.action}`);
      console.log(`🎯 DEBUG: About to handle action: ${conversationResult.action}`);
      
      // Handle based on conversation manager decision
      if (conversationResult.action === 'ignore_sales_inquiry') {
        console.log(`🚫 SALES INQUIRY IGNORED - Dean (CMO) will handle this`);
        console.log(`📋 Reason: ${conversationResult.reason}`);
        return; // Ava stays silent - Dean's territory
      } else if (conversationResult.action === 'ignore_non_operational') {
        console.log(`🚫 NON-OPERATIONAL MESSAGE IGNORED - Dean's territory`);
        console.log(`📋 Reason: ${conversationResult.reason}`);
        return; // Ava stays silent - Dean's territory
      } else if (conversationResult.action === 'operational_response') {
        await this.handleOperationalResponse(conversationResult);
        return; // Exit early - Ava handled this
      } else if (conversationResult.action === 'request_guidance') {
        await this.handleGuidanceRequest(conversationResult);
        return; // Exit early - Requested human guidance
      }

      // If we get here, something went wrong - log it
      console.log(`⚠️ Unknown conversation result action: ${conversationResult.action}`);

    } catch (error) {
      console.error('❌ Error processing Google Voice message:', error.message);
    }
  }

  parseGoogleVoiceEmail(emailData) {
    try {
      const headers = emailData.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const from = headers.find(h => h.name === 'From')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';

      console.log(`🔍 DEBUG: Email subject = "${subject}"`);
      console.log(`🔍 DEBUG: Email from = "${from}"`);

      // Extract email body
      let content = this.extractEmailBody(emailData.payload);
      console.log(`🔍 DEBUG: Extracted email content = "${content.substring(0, 200)}..."`);
      
      // Parse Google Voice format
      const clientInfo = this.parseGoogleVoiceContent(subject, content);
      console.log(`🔍 DEBUG: Parsed client info = ${JSON.stringify(clientInfo, null, 2)}`);

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

    console.log(`🔍 DEBUG: Parsing Google Voice - Subject: "${subject}"`);
    console.log(`🔍 DEBUG: Content preview: "${content.substring(0, 200)}..."`);

    // Extract sender name from subject - handle both individual and group messages
    let nameMatch = subject.match(/New text message from (.+)/);
    if (!nameMatch) {
      nameMatch = subject.match(/New group message from (.+)/);
    }
    
    if (nameMatch) {
      result.name = nameMatch[1].trim();
      // Remove trailing period if present
      if (result.name.endsWith('.')) {
        result.name = result.name.slice(0, -1);
      }
      console.log(`🔍 DEBUG: Extracted sender name: "${result.name}"`);
    }

    // Extract the actual SMS content - it's usually in the first few lines
    const lines = content.split('\n');
    let messageLines = [];
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Skip empty lines and Google Voice URLs
      if (!trimmedLine || trimmedLine.startsWith('http') || trimmedLine.includes('voice.google.com')) {
        continue;
      }
      
      // Skip Google Voice footer content
      if (trimmedLine.includes('YOUR ACCOUNT') || 
          trimmedLine.includes('HELP CENTER') ||
          trimmedLine.includes('This email was sent') ||
          trimmedLine.includes('Google LLC') ||
          trimmedLine.includes('Mountain View')) {
        break; // Stop processing when we hit the footer
      }
      
      // This is likely the actual message content
      messageLines.push(trimmedLine);
    }
    
    // Join the message lines and clean up
    result.message = messageLines.join(' ').trim();
    
    // Use sender name from subject or fallback
    if (!result.name) {
      result.name = 'Unknown Customer';
    }
    
    // For now, use the sender name as phone identifier
    result.phone = result.name;
    
    console.log(`🔍 DEBUG: Final extracted message: "${result.message}"`);
    console.log(`🔍 DEBUG: Final sender name: "${result.name}"`);

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

  /**
   * Determine if a Google Voice message is from a real customer (not spam/verification)
   */
  isCustomerMessage(parsedEmail) {
    const message = parsedEmail.clientMessage.toLowerCase();
    const subject = parsedEmail.subject.toLowerCase();
    const senderName = parsedEmail.clientName.toLowerCase();
    
    // Filter out verification codes and automated messages
    const spamKeywords = [
      'verification code',
      'verification pin',
      'confirm your',
      'activate your',
      'security code',
      'login code',
      'indeed',
      'stripe',
      'discord',
      'facebook',
      'google',
      'amazon',
      'paypal',
      'venmo',
      'zelle'
    ];
    
    // Check if message contains spam keywords
    for (const keyword of spamKeywords) {
      if (message.includes(keyword) || subject.includes(keyword)) {
        console.log(`🚫 Filtered out: Contains spam keyword "${keyword}"`);
        return false;
      }
    }
    
    // Filter out numeric-only sender names (usually verification services)
    if (/^\d{4,6}$/.test(senderName)) {
      console.log(`🚫 Filtered out: Numeric sender "${senderName}" (likely verification service)`);
      return false;
    }
    
    // Filter out known spam short codes we've seen in the Gmail history
    const spamShortCodes = ['31061', '22395', '65161'];
    if (spamShortCodes.includes(senderName)) {
      console.log(`🚫 Filtered out: Known spam short code "${senderName}"`);
      return false;
    }
    
    // Check for legitimate cleaning-related content
    const cleaningKeywords = [
      'clean', 'appointment', 'schedule', 'reschedule', 'cancel',
      'service', 'house', 'home', 'tomorrow', 'today', 'friday',
      'monday', 'tuesday', 'wednesday', 'thursday', 'saturday', 'sunday'
    ];
    
    const hasCleaningContent = cleaningKeywords.some(keyword => 
      message.includes(keyword) || subject.includes(keyword)
    );
    
    if (hasCleaningContent) {
      console.log(`✅ Customer message detected: Contains cleaning-related content`);
      return true;
    }
    
    // If it's not obvious spam and doesn't contain verification codes, 
    // it might be a legitimate customer inquiry
    if (message.length > 10 && !message.includes('http')) {
      console.log(`✅ Potential customer message: Not obvious spam, reasonable length`);
      return true;
    }
    
    console.log(`🚫 Filtered out: Does not appear to be customer communication`);
    return false;
  }

  // === HIGH LEVEL CONVERSATION MONITORING ===
  async checkHighLevelConversations() {
    try {
      // High Level conversations API not available in v1 - skipping
      console.log('📱 High Level conversations monitoring disabled (API not available)');
      
      // Update last check time to prevent log spam
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
      await this.sendApprovalRequest(messageData, replyDraft, 'Schedule Change Request');
      
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

  async sendApprovalRequest(messageData, replyDraft, messageType = 'Message') {
    try {
      console.log(`🎯 DEBUG: Sending approval request for ${messageType}`);
      console.log(`🎯 DEBUG: OPS_LEAD_DISCORD_ID = ${process.env.OPS_LEAD_DISCORD_ID}`);
      
      const opsLead = await this.discordClient.users.fetch(process.env.OPS_LEAD_DISCORD_ID);
      console.log(`🎯 DEBUG: Found Discord user: ${opsLead.username}`);
      
      // Choose appropriate color and emoji based on message type
      const colors = {
        'New Prospect Inquiry': 0x00ff00,
        '⚠️ Customer Complaint - URGENT': 0xff0000,
        'Schedule Change Request': 0xffaa00
      };
      
      const color = colors[messageType] || 0x3498db;
      
      const embed = {
        color,
        title: `✅ Reply Draft Ready for Approval`,
        description: `**${messageType}**`,
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
      
      // Store for approval handling (user will add their own reactions)
      this.pendingReplies.set(dmMessage.id, {
        messageData,
        replyDraft,
        messageType,
        timestamp: new Date()
      });

    } catch (error) {
      console.error('❌ Error sending approval request:', error.message);
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
    console.log(`[ApprovalDebug] Reaction received - MessageID: ${messageId}, Emoji: ${emoji}, UserID: ${userId}`);
    console.log(`[ApprovalDebug] Expected OPS_LEAD_ID: ${process.env.OPS_LEAD_DISCORD_ID}`);
    console.log(`[ApprovalDebug] User ID matches: ${userId === process.env.OPS_LEAD_DISCORD_ID}`);
    console.log(`[ApprovalDebug] Pending replies count: ${this.pendingReplies.size}`);
    
    if (userId !== process.env.OPS_LEAD_DISCORD_ID) {
      console.log(`[ApprovalDebug] User ID mismatch - ignoring reaction`);
      return;
    }
    
    const pendingReply = this.pendingReplies.get(messageId);
    console.log(`[ApprovalDebug] Found pending reply: ${!!pendingReply}`);
    
    if (!pendingReply) {
      console.log(`[ApprovalDebug] No pending reply found for message ID: ${messageId}`);
      console.log(`[ApprovalDebug] Available message IDs: ${Array.from(this.pendingReplies.keys()).join(', ')}`);
      return;
    }

    if (emoji === '✅') {
      console.log(`[ApprovalDebug] Approval confirmed - sending reply`);
      await this.sendApprovedReply(pendingReply);
      console.log('✅ Reply approved and sent');
    } else if (emoji === '❌') {
      console.log('❌ Reply cancelled by operator');
    }

    // Clean up
    this.pendingReplies.delete(messageId);
    console.log(`[ApprovalDebug] Cleaned up pending reply - remaining: ${this.pendingReplies.size}`);
  }

  async sendApprovedReply(pendingReply) {
    const { messageData, replyDraft } = pendingReply;
    
    console.log(`[SendReply] Attempting to send reply via ${messageData.source}`);
    console.log(`[SendReply] Reply text: ${replyDraft.substring(0, 100)}...`);
    
    try {
      if (messageData.source === 'google_voice') {
        console.log(`[SendReply] Sending via Gmail for Google Voice`);
        // Send via Gmail (will forward as SMS through Google Voice)
        await this.sendGmailReply(messageData, replyDraft);
      } else if (messageData.source === 'high_level') {
        console.log(`[SendReply] Sending via High Level API`);
        // Send via High Level API
        await this.sendHighLevelReply(messageData, replyDraft);
      }
      console.log(`[SendReply] Reply sent successfully`);
    } catch (error) {
      console.error('❌ Error sending approved reply:', error.message);
      console.error('❌ Full error:', error);
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

  // === NEW PROSPECT INQUIRY HANDLING ===
  async handleProspectInquiry(messageData, classification) {
    try {
      // Generate appropriate response for prospect
      const replyDraft = await this.generateProspectResponse(messageData, classification);
      
      // Send approval request to ops lead
      await this.sendApprovalRequest(messageData, replyDraft, 'New Prospect Inquiry');
      
      // Log to Notion as prospect lead
      await this.logToNotion(messageData, classification, 'prospect_inquiry');
      
    } catch (error) {
      console.error('❌ Error handling prospect inquiry:', error.message);
    }
  }

  async generateProspectResponse(messageData, classification) {
    try {
      const OpenAI = require('openai');
      const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

      const prompt = `You are responding as Grime Guardians cleaning service to a new prospect inquiry.

PROSPECT MESSAGE: "${messageData.clientMessage}"

Create a professional response that:
- Thanks them for their interest
- Asks for key details (property type, size, specific cleaning needs)
- Mentions our quality service and competitive pricing
- Provides next steps to get a quote

Keep it under 160 characters for SMS. Be warm but professional:`;

      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
        max_tokens: 100
      });

      return response.choices[0].message.content.trim();
      
    } catch (error) {
      console.error('❌ Error generating prospect response:', error.message);
      
      // Fallback response
      return `Hi! Thanks for your interest in Grime Guardians! I'd love to provide a quote. Could you share: property type, square footage, and what type of cleaning you need? We offer competitive rates and quality service!`;
    }
  }

  // === COMPLAINT HANDLING ===
  async handleComplaint(messageData, classification) {
    try {
      // Generate empathetic response
      const replyDraft = await this.generateComplaintResponse(messageData, classification);
      
      // Send high-priority approval request
      await this.sendApprovalRequest(messageData, replyDraft, '⚠️ Customer Complaint - URGENT');
      
      // Log to Notion as complaint
      await this.logToNotion(messageData, classification, 'complaint');
      
      // Alert ops lead immediately
      await this.sendUrgentAlert(messageData, 'Customer complaint requires immediate attention');
      
    } catch (error) {
      console.error('❌ Error handling complaint:', error.message);
    }
  }

  async generateComplaintResponse(messageData, classification) {
    try {
      const OpenAI = require('openai');
      const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

      const prompt = `You are responding as Grime Guardians to a customer complaint.

COMPLAINT: "${messageData.clientMessage}"

Create an empathetic, professional response that:
- Sincerely apologizes for their experience
- Shows we take their concerns seriously
- Asks for specific details about the issue
- Assures them we'll make it right
- Provides immediate next steps

Keep under 160 characters for SMS:`;

      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.6,
        max_tokens: 100
      });

      return response.choices[0].message.content.trim();
      
    } catch (error) {
      console.error('❌ Error generating complaint response:', error.message);
      
      // Fallback response
      return `I sincerely apologize for your experience. This is not the quality we strive for. Can you please share specific details about the issue? We will make this right immediately.`;
    }
  }

  async sendUrgentAlert(messageData, alertMessage) {
    try {
      const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
      if (!opsLeadId) return;

      const user = await this.discordClient.users.fetch(opsLeadId);
      
      const embed = {
        title: '🚨 URGENT ALERT',
        color: 0xff0000,
        description: alertMessage,
        fields: [
          { name: '📱 Phone', value: messageData.clientPhone || 'Unknown', inline: true },
          { name: '📅 Time', value: new Date().toLocaleString(), inline: true },
          { name: '💬 Message', value: `\`\`\`${messageData.clientMessage.substring(0, 500)}\`\`\``, inline: false }
        ],
        timestamp: new Date().toISOString()
      };

      await user.send({ embeds: [embed] });
      console.log('🚨 Urgent alert sent to ops lead');
      
    } catch (error) {
      console.error('❌ Error sending urgent alert:', error.message);
    }
  }

  // === NEW CONVERSATION-AWARE HANDLERS ===

  /**
   * Handle CMO handoff for sales inquiries
   */
  async handleCMOHandoff(conversationResult) {
    const { messageData, conversation, classification, transitionMessage } = conversationResult;
    
    console.log(`🔄 Routing to CMO: ${classification.type} inquiry from ${conversation.phoneNumber}`);
    
    // Send transition message if provided
    if (transitionMessage) {
      console.log(`📤 Sending transition message: ${transitionMessage}`);
      
      // For now, just log - in production this would send the message
      // await this.sendMessage(messageData, transitionMessage);
    }

    // Create CMO notification (this would integrate with your CMO suite)
    const cmoNotification = {
      type: 'sales_handoff',
      source: messageData.source,
      phoneNumber: conversation.phoneNumber,
      clientMessage: messageData.clientMessage,
      classification: classification.type,
      confidence: classification.confidence,
      conversationHistory: conversation.messages.slice(-5), // Last 5 messages for context
      transitionSent: !!transitionMessage,
      timestamp: new Date().toISOString()
    };

    console.log('🎯 CMO handoff data prepared:', {
      phone: conversation.phoneNumber,
      type: classification.type,
      historyLength: conversation.messages.length
    });

    // TODO: Integrate with CMO suite API/Discord channel
    // For now, send to ops lead as notification
    await this.sendCMOHandoffNotification(cmoNotification);
  }

  /**
   * Handle operational response from Ava
   */
  async handleOperationalResponse(conversationResult) {
    const { messageData, conversation, response, requiresApproval } = conversationResult;
    
    console.log(`⚙️ Operational response: ${response.confidence}% confidence`);
    
    // EMERGENCY: ALL responses require approval - no auto-sends
    console.log(`� EMERGENCY: All responses require manual approval`);
    await this.sendApprovalRequest(messageData, response.text, 'Operational Inquiry');
  }

  /**
   * Handle guidance requests for uncertain messages
   */
  async handleGuidanceRequest(conversationResult) {
    const { messageData, conversation, classification, question } = conversationResult;
    
    console.log(`❓ Requesting guidance for uncertain message`);
    
    // Send guidance request to ops lead
    await this.sendGuidanceRequest(messageData, conversation, question);
  }

  /**
   * Send CMO handoff notification
   */
  async sendCMOHandoffNotification(cmoData) {
    try {
      const opsLead = await this.discordClient.users.fetch(process.env.OPS_LEAD_DISCORD_ID);
      
      const embed = {
        color: 0xFF6B35, // Orange for sales
        title: '🎯 CMO Handoff - Sales Inquiry',
        description: `**${cmoData.classification.toUpperCase()}** inquiry routed to sales team`,
        fields: [
          { name: '📞 Channel', value: cmoData.source.replace('_', ' ').toUpperCase(), inline: true },
          { name: '📱 Phone', value: cmoData.phoneNumber, inline: true },
          { name: '🎯 Type', value: cmoData.classification, inline: true },
          { name: '💬 Message', value: cmoData.clientMessage.substring(0, 300) + '...', inline: false },
          { name: '🔄 Transition Sent', value: cmoData.transitionSent ? 'Yes' : 'No', inline: true },
          { name: '📊 Confidence', value: `${Math.round(cmoData.confidence * 100)}%`, inline: true }
        ],
        footer: { text: 'CMO Suite will handle sales process' },
        timestamp: cmoData.timestamp
      };

      await opsLead.send({ embeds: [embed] });
      console.log('✅ CMO handoff notification sent');
      
    } catch (error) {
      console.error('❌ Error sending CMO handoff notification:', error.message);
    }
  }

  /**
   * Send operational reply directly (high confidence)
   */
  async sendOperationalReply(messageData, replyText) {
    try {
      if (messageData.source === 'google_voice') {
        await this.sendGmailReply(messageData, replyText);
        console.log(`✅ Operational reply sent automatically`);
      } else if (messageData.source === 'high_level') {
        await this.sendHighLevelReply(messageData, replyText);
        console.log(`✅ Operational reply sent via High Level`);
      }
    } catch (error) {
      console.error('❌ Error sending operational reply:', error.message);
    }
  }

  /**
   * Send guidance request to ops lead
   */
  async sendGuidanceRequest(messageData, conversation, question) {
    try {
      const opsLead = await this.discordClient.users.fetch(process.env.OPS_LEAD_DISCORD_ID);
      
      const embed = {
        color: 0xFFD93D, // Yellow for guidance
        title: '❓ Guidance Request',
        description: question,
        fields: [
          { name: '📞 Channel', value: messageData.source.replace('_', ' ').toUpperCase(), inline: true },
          { name: '📱 Phone', value: conversation.phoneNumber, inline: true },
          { name: '💬 Message', value: messageData.clientMessage, inline: false },
          { name: '🧵 Thread Length', value: conversation.messages.length.toString(), inline: true },
          { name: '⏰ Last Interaction', value: conversation.lastInteraction.toLocaleString(), inline: true }
        ],
        footer: { text: 'Reply with guidance: "Ava, handle this as [operations/sales]"' }
      };

      await opsLead.send({ embeds: [embed] });
      console.log('❓ Guidance request sent to ops lead');
      
    } catch (error) {
      console.error('❌ Error sending guidance request:', error.message);
    }
  }

  /**
   * Learn from Discord feedback
   */
  async processDiscordFeedback(message) {
    if (message.author.id !== process.env.OPS_LEAD_DISCORD_ID) return false;
    
    const feedback = message.content.toLowerCase();
    
    // Check if this is feedback for Ava
    if (feedback.includes('ava,') || feedback.startsWith('ava ')) {
      const instruction = feedback.replace(/^ava,?\s*/, '');
      
      console.log(`📚 Processing feedback: ${instruction}`);
      
      // Parse common feedback patterns
      if (instruction.includes('route') && instruction.includes('cmo')) {
        // "Ava, route pricing questions to CMO"
        await this.conversationManager.learnFromFeedback(instruction, {
          type: 'routing_rule',
          action: 'route_to_cmo'
        });
      } else if (instruction.includes('handle') && instruction.includes('operations')) {
        // "Ava, handle this as operations"
        await this.conversationManager.learnFromFeedback(instruction, {
          type: 'classification_correction',
          action: 'handle_as_operations'
        });
      }
      
      // Send acknowledgment
      await message.react('✅');
      await message.reply('Got it! I\'ll learn from this feedback.');
      
      return true;
    }
    
    return false;
  }
}

module.exports = EmailCommunicationMonitor;
