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
const HighLevelOAuth = require('./highlevelOAuth');
require('dotenv').config();

class EmailCommunicationMonitor {
  constructor(client, langchainAgent = null) {
    this.discordClient = client;
    this.gmail = null;
    this.isMonitoring = false;
    this.langchainAgent = langchainAgent; // LangChain integration
    
    // Enhanced AI components
    this.messageClassifier = new MessageClassifier();
    this.trainingSystem = new AvaTrainingSystem(client);
    this.conversationManager = new ConversationManager(client);
    
    // High Level OAuth integration
    this.highLevelOAuth = new HighLevelOAuth();
    
    // Tracking
    this.lastEmailCheck = new Date();
    this.lastHighLevelCheck = new Date();
    this.processedEmailIds = new Set();
    this.processedHighLevelIds = new Set();
    this.pendingReplies = new Map();
    this.pendingGoogleVoiceReplies = new Map(); // NEW: For Google Voice approvals
    
    // Configuration flags
    this.monitorGoogleVoiceEmails = true;     // ENABLED - Monitor Google Voice emails via Gmail
    this.monitorBusinessEmails = true;        // Monitor direct business emails
    this.monitorHighLevel = true;             // Continue High Level monitoring
    console.log('🧠 Enhanced with GPT-4 classification and training system');
    console.log('📧 Gmail monitoring for direct business emails');
    console.log('📱 High Level (651-515-1478) → OAuth API Monitoring');
    console.log('📱 Google Voice monitoring → Separate API integration');
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
      
      console.log(`✅ Gmail monitoring initialized for ${this.gmailClients.size} email account(s)`);
      
    } catch (error) {
      console.error('❌ Gmail initialization failed:', error.message);
      console.log('💡 Run: node scripts/setup-gmail-auth.js to set up Gmail API');
      throw error;
    }
  }

  async testHighLevelConnection() {
    try {
      console.log('🔗 Testing High Level OAuth connection...');
      
      if (!this.highLevelOAuth.isConfigured()) {
        throw new Error('High Level OAuth not configured. Please complete OAuth flow first.');
      }
      
      // Test API access
      const testResult = await this.highLevelOAuth.testAPIAccess();
      
      if (!testResult.success) {
        throw new Error(`High Level API test failed: ${testResult.error}`);
      }
      
      console.log('✅ High Level OAuth API connection successful');
      
      // Log test results
      const results = testResult.results;
      console.log(`📊 Token Status: ${results.token_status.has_access_token ? '✅' : '❌'} Access Token, ${results.token_status.has_refresh_token ? '✅' : '❌'} Refresh Token`);
      console.log(`⏰ Token Expires: ${results.token_status.expiry_time} (Expired: ${results.token_status.token_expired ? '❌' : '✅'})`);
      console.log(`📞 Contacts API: ${results.contacts_v2?.ok ? '✅' : '❌'} (${results.contacts_v2?.status})`);
      console.log(`💬 Conversations API: ${results.conversations_v2?.ok ? '✅' : '❌'} (${results.conversations_v2?.status})`);
      console.log(`🏢 Location Access: ${results.location_access?.ok ? '✅' : '❌'} (${results.location_access?.status})`);
      
      return true;
    } catch (error) {
      console.error('❌ High Level connection test failed:', error.message);
      throw new Error(`High Level connection failed: ${error.message}`);
    }
  }

  async startMonitoring() {
    if (this.isMonitoring) {
      console.log('⚠️ Monitoring already active');
      return;
    }
    
    this.isMonitoring = true;
    console.log('🚀 Starting email-based communication monitoring...');
    console.log('📧 Checking business emails every 1 minute (TESTING MODE)');
    console.log('📱 Checking High Level conversations every 1 minute (TESTING MODE)');
    
    // Business email monitoring - TESTING: 1 minute interval
    this.emailInterval = setInterval(() => {
      this.checkBusinessEmails();
    }, 1 * 60 * 1000); // 1 minute for testing

    // High Level API monitoring - TESTING: 1 minute interval
    this.highLevelInterval = setInterval(() => {
      this.checkHighLevelConversations();
    }, 1 * 60 * 1000); // 1 minute for testing

    // Initial checks
    await Promise.all([
      this.checkBusinessEmails(),
      this.checkHighLevelConversations()
    ]);
  }

  // === BUSINESS EMAIL MONITORING ===
  async checkBusinessEmails() {
    if (!this.gmail) {
      console.log('⚠️ Gmail not initialized, skipping business email check');
      return;
    }

    if (!this.monitorGoogleVoiceEmails) {
      console.log('📱 Google Voice monitoring disabled - handled by separate API monitor');
      return;
    }

    try {
      console.log('📧 Checking Google Voice emails...');
      
      // Check Google Voice emails using broberts111592@gmail.com account
      await this.checkGoogleVoiceEmails();
      
    } catch (error) {
      console.error('❌ Error checking business emails:', error.message);
    }
  }

  async checkGoogleVoiceEmails() {
    try {
      // Use broberts111592@gmail.com for Google Voice monitoring
      const googleVoiceAccount = 'broberts111592@gmail.com';
      
      if (!this.gmailClients.has(googleVoiceAccount)) {
        console.log(`⚠️ Gmail account ${googleVoiceAccount} not initialized`);
        return;
      }

      const gmail = this.gmailClients.get(googleVoiceAccount);
      
      // Calculate date filter for last 2 hours only
      const twoHoursAgo = new Date();
      twoHoursAgo.setHours(twoHoursAgo.getHours() - 2);
      const dateFilter = twoHoursAgo.toISOString().split('T')[0].replace(/-/g, '/'); // Format: YYYY/MM/DD
      
      // Search for Google Voice messages from last 2 hours only
      const query = `from:@txt.voice.google.com subject:("New text message from") after:${dateFilter} is:unread`;
      
      console.log(`🔍 Searching Gmail with query: ${query}`);
      
      const messages = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 10
      });

      if (!messages.data.messages || messages.data.messages.length === 0) {
        return; // No new messages
      }

      console.log(`📱 Found ${messages.data.messages.length} new Google Voice messages`);

      for (const messageRef of messages.data.messages) {
        if (this.processedEmailIds.has(messageRef.id)) {
          continue;
        }

        const email = await gmail.users.messages.get({
          userId: 'me',
          id: messageRef.id
        });

        const parsedMessage = this.parseGoogleVoiceEmail(email.data);
        
        if (parsedMessage && parsedMessage.clientMessage) {
          console.log(`📱 Processing Google Voice message from: ${parsedMessage.clientPhone}`);
          
          // Analyze with LangChain first, then send enhanced Discord DM
          let analysis = null;
          if (this.langchainAgent) {
            analysis = await this.analyzeSMSWithLangChain(parsedMessage);
          }
          
          // Send enhanced Discord DM to ops lead
          await this.sendGoogleVoiceAlert(parsedMessage, analysis);
          
          // Mark as read
          await gmail.users.messages.modify({
            userId: 'me',
            id: messageRef.id,
            resource: {
              removeLabelIds: ['UNREAD']
            }
          });
        }

        this.processedEmailIds.add(messageRef.id);
      }

      console.log(`📧 Processed ${messages.data.messages.length} new Google Voice messages`);

    } catch (error) {
      console.error('❌ Error checking Google Voice emails:', error.message);
    }
  }

  async sendGoogleVoiceAlert(messageData, analysis = null) {
    try {
      const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
      if (!opsLeadId) {
        console.log('⚠️ No ops lead Discord ID configured');
        return;
      }

      const user = await this.discordClient.users.fetch(opsLeadId);
      if (!user) {
        console.log('❌ Could not find ops lead user');
        return;
      }

      // Discord DM schema for Google Voice SMS - exact format match
      let alertMessage = `🚨 NEW SMS VIA GOOGLE VOICE (612-584-9396)\n` +
        `📞 From: ${messageData.clientPhone || 'Unknown Number'}\n` +
        `👤 Name: ${messageData.clientName || 'Not provided'}\n` +
        `💬 Message: ${messageData.clientMessage}\n` +
        `⏰ Time: ${messageData.date?.toLocaleString() || 'Unknown'}\n`;

      // Add LangChain analysis if available
      if (analysis) {
        const messageTypeDisplay = this.formatMessageTypeForDisplay(analysis.message_type);
        const confidencePercent = Math.round((analysis.confidence || 0) * 100);
        
        alertMessage += `_________\n` +
          `ANALYSIS\n` +
          `_________\n` +
          `👤 Type: ${messageTypeDisplay}\n` +
          `⚡ Urgency: ${analysis.urgency_level || 'medium'}\n` +
          `🎯 Confidence: ${confidencePercent}%\n`;
        
        if (analysis.reasoning) {
          // Change 'The email is from...' to 'This text is from...'
          let reasoning = analysis.reasoning.replace(/The email is from/gi, 'This text is from');
          alertMessage += `💡 Reasoning: ${reasoning}\n`;
        }
        
        // Add suggested reply if Ava is confident (>80%)
        if (analysis.confidence > 0.8 && analysis.requires_response) {
          const suggestedReply = this.generateSuggestedReply(messageData, analysis);
          if (suggestedReply) {
            alertMessage += `_______________\n` +
              `SUGGESTED REPLY\n` +
              `_______________\n` +
              `💬 Recommended Response:\n` +
              `"${suggestedReply}"\n\n` +
              `________________\n` +
              `ACTION REQUIRED\n` +
              `________________\n` +
              `React with ✅ to send this reply via Google Voice\n`;
          }
        } else {
          // If no suggested reply, still show action required
          alertMessage += `________________\n` +
            `ACTION REQUIRED\n` +
            `________________\n` +
            `⚠️ Review and respond as needed\n`;
        }
      } else {
        // If no analysis, just show action required
        alertMessage += `________________\n` +
          `ACTION REQUIRED\n` +
          `________________\n` +
          `⚠️ Review and respond as needed\n`;
      }

      // Send the message (do NOT prefill the green checkmark reaction)
      const sentMessage = await user.send(alertMessage);
      
      // Store for Google Voice reply approval if applicable (no prefilled reaction)
      if (analysis && analysis.confidence > 0.8 && analysis.requires_response) {
        this.pendingGoogleVoiceReplies.set(sentMessage.id, {
          messageData,
          analysis,
          suggestedReply: this.generateSuggestedReply(messageData, analysis),
          timestamp: new Date()
        });
        console.log(`📝 Stored pending Google Voice reply for approval (ID: ${sentMessage.id})`);
      }
      
      console.log(`✅ Enhanced Google Voice alert sent to ops lead`);

    } catch (error) {
      console.error('❌ Error sending Google Voice alert:', error.message);
    }
  }

  async analyzeSMSWithLangChain(messageData) {
    try {
      if (!this.langchainAgent) {
        return null;
      }

      const analysis = await this.langchainAgent.analyzeMessage({
        subject: `SMS from ${messageData.clientPhone}`,
        from: messageData.clientPhone || 'unknown',
        body: messageData.clientMessage,
        timestamp: messageData.date?.toISOString() || new Date().toISOString()
      });

      console.log(`🧠 LangChain SMS Analysis:`, {
        messageType: analysis.message_type,
        urgency: analysis.urgency_level,
        confidence: analysis.confidence
      });

      return analysis;

    } catch (error) {
      console.error('❌ Error analyzing SMS with LangChain:', error.message);
      return null;
    }
  }

  async analyzeHighLevelMessageWithLangChain(messageData) {
    try {
      if (!this.langchainAgent) {
        return null;
      }

      const analysis = await this.langchainAgent.analyzeMessage({
        subject: `High Level SMS from ${messageData.clientPhone}`,
        from: messageData.clientPhone || 'unknown',
        body: messageData.clientMessage,
        timestamp: messageData.timestamp?.toISOString() || new Date().toISOString()
      });

      console.log(`🧠 LangChain High Level Analysis:`, {
        messageType: analysis.message_type,
        urgency: analysis.urgency_level,
        confidence: analysis.confidence
      });

      return analysis;

    } catch (error) {
      console.error('❌ Error analyzing High Level message with LangChain:', error.message);
      return null;
    }
  }

  // === GOOGLE VOICE REPLY APPROVAL HANDLING ===
  async handleGoogleVoiceApproval(messageId, emoji, userId) {
    console.log(`[GoogleVoiceApproval] Reaction received - MessageID: ${messageId}, Emoji: ${emoji}, UserID: ${userId}`);
    
    if (userId !== process.env.DISCORD_OPS_LEAD_ID) {
      console.log(`[GoogleVoiceApproval] User ID mismatch - ignoring reaction`);
      return false;
    }
    
    const pendingReply = this.pendingGoogleVoiceReplies.get(messageId);
    if (!pendingReply) {
      console.log(`[GoogleVoiceApproval] No pending Google Voice reply found for message ID: ${messageId}`);
      return false;
    }

    if (emoji === '✅') {
      console.log(`[GoogleVoiceApproval] Approval confirmed - sending Google Voice reply`);
      await this.sendGoogleVoiceReply(pendingReply);
      console.log('✅ Google Voice reply approved and sent');
      
      // Clean up
      this.pendingGoogleVoiceReplies.delete(messageId);
      return true;
    }

    return false;
  }

  async sendGoogleVoiceReply(pendingReply) {
    const { messageData, suggestedReply } = pendingReply;
    
    console.log(`[GoogleVoiceReply] Sending reply to ${messageData.clientPhone}: ${suggestedReply.substring(0, 50)}...`);
    
    try {
      // Use broberts111592@gmail.com for Google Voice replies
      const googleVoiceAccount = 'broberts111592@gmail.com';
      
      if (!this.gmailClients.has(googleVoiceAccount)) {
        throw new Error(`Gmail account ${googleVoiceAccount} not available for Google Voice replies`);
      }

      const gmail = this.gmailClients.get(googleVoiceAccount);
      
      // FIXED: Reply to the original Google Voice email instead of creating new email
      // This maintains proper threading and recipient information
      const emailContent = [
        `To: ${messageData.from}`,
        `Subject: Re: ${messageData.subject}`,
        `In-Reply-To: ${messageData.id}`,
        `References: ${messageData.id}`,
        ``,
        suggestedReply
      ].join('\n');

      const encodedMessage = Buffer.from(emailContent)
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');

      await gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          threadId: messageData.threadId,  // Maintain thread continuity
          raw: encodedMessage
        }
      });

      console.log(`✅ Google Voice reply sent to ${messageData.clientPhone} via thread reply`);
      
      // Send confirmation to ops lead
      await this.sendReplyConfirmation(messageData, suggestedReply);

    } catch (error) {
      console.error('❌ Error sending Google Voice reply:', error.message);
      
      // Send error notification to ops lead
      await this.sendReplyError(messageData, error.message);
      throw error;
    }
  }

  async sendHighLevelReply(messageData, replyText) {
    try {
      console.log(`[HighLevelReply] Sending reply to contact ${messageData.contactId}: ${replyText.substring(0, 50)}...`);
      
      // Use OAuth handler to send message
      const result = await this.highLevelOAuth.sendMessage(messageData.contactId, replyText, 'SMS');
      
      console.log(`✅ High Level reply sent to ${messageData.clientName} (${messageData.clientPhone})`);
      console.log(`📋 Message ID: ${result.id || 'unknown'}`);
      
      // Send confirmation to ops lead
      await this.sendHighLevelReplyConfirmation(messageData, replyText);

    } catch (error) {
      console.error('❌ Error sending High Level reply:', error.message);
      
      // Send error notification to ops lead
      await this.sendHighLevelReplyError(messageData, error.message);
      throw error;
    }
  }

  async sendHighLevelReplyConfirmation(messageData, replyText) {
    try {
      const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
      if (!opsLeadId) return;

      const user = await this.discordClient.users.fetch(opsLeadId);
      
      const confirmationMessage = `✅ **High Level Reply Sent Successfully**\n\n` +
        `📞 **To:** ${messageData.clientPhone}\n` +
        `👤 **Name:** ${messageData.clientName || 'Unknown'}\n` +
        `💬 **Reply:** "${replyText}"\n` +
        `⏰ **Sent:** ${new Date().toLocaleString()}`;

      await user.send(confirmationMessage);
      console.log('✅ High Level reply confirmation sent to ops lead');
      
    } catch (error) {
      console.error('❌ Error sending High Level reply confirmation:', error.message);
    }
  }

  async sendHighLevelReplyError(messageData, errorMessage) {
    try {
      const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
      if (!opsLeadId) return;

      const user = await this.discordClient.users.fetch(opsLeadId);
      
      const errorAlert = `❌ **High Level Reply Failed**\n\n` +
        `📞 **To:** ${messageData.clientPhone}\n` +
        `👤 **Name:** ${messageData.clientName || 'Unknown'}\n` +
        `⚠️ **Error:** ${errorMessage}\n` +
        `💡 **Action:** Please send reply manually via High Level`;

      await user.send(errorAlert);
      console.log('❌ High Level reply error notification sent to ops lead');
      
    } catch (error) {
      console.error('❌ Error sending High Level reply error notification:', error.message);
    }
  }

  async sendHighLevelAlert(messageData, analysis = null) {
    try {
      const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
      if (!opsLeadId) {
        console.log('⚠️ No ops lead Discord ID configured');
        return;
      }

      const user = await this.discordClient.users.fetch(opsLeadId);
      if (!user) {
        console.log('❌ Could not find ops lead user');
        return;
      }

      // Discord DM schema for High Level SMS - matching Google Voice format
      let alertMessage = `🚨 NEW SMS VIA HIGH LEVEL (651-515-1478)\n` +
        `📞 From: ${messageData.clientPhone || 'Unknown Number'}\n` +
        `👤 Name: ${messageData.clientName || 'Not provided'}\n` +
        `💬 Message: ${messageData.clientMessage}\n` +
        `⏰ Time: ${messageData.timestamp?.toLocaleString() || 'Unknown'}\n`;

      // Add LangChain analysis if available
      if (analysis) {
        const messageTypeDisplay = this.formatMessageTypeForDisplay(analysis.message_type);
        const confidencePercent = Math.round((analysis.confidence || 0) * 100);
        
        alertMessage += `_________\n` +
          `ANALYSIS\n` +
          `_________\n` +
          `👤 Type: ${messageTypeDisplay}\n` +
          `⚡ Urgency: ${analysis.urgency_level || 'medium'}\n` +
          `🎯 Confidence: ${confidencePercent}%\n`;
        
        if (analysis.reasoning) {
          // Change 'The email is from...' to 'This text is from...'
          let reasoning = analysis.reasoning.replace(/The email is from/gi, 'This text is from');
          alertMessage += `💡 Reasoning: ${reasoning}\n`;
        }
        
        // Add suggested reply if Ava is confident (>80%)
        if (analysis.confidence > 0.8 && analysis.requires_response) {
          const suggestedReply = this.generateSuggestedReply(messageData, analysis);
          if (suggestedReply) {
            alertMessage += `_______________\n` +
              `SUGGESTED REPLY\n` +
              `_______________\n` +
              `💬 Recommended Response:\n` +
              `"${suggestedReply}"\n\n` +
              `________________\n` +
              `ACTION REQUIRED\n` +
              `________________\n` +
              `React with ✅ to send this reply via High Level\n`;
          }
        } else {
          // If no suggested reply, still show action required
          alertMessage += `________________\n` +
            `ACTION REQUIRED\n` +
            `________________\n` +
            `⚠️ Review and respond as needed\n`;
        }
      } else {
        // If no analysis, just show action required
        alertMessage += `________________\n` +
          `ACTION REQUIRED\n` +
          `________________\n` +
          `⚠️ Review and respond as needed\n`;
      }

      // Send the message (do NOT prefill the green checkmark reaction)
      const sentMessage = await user.send(alertMessage);
      
      // Store for High Level reply approval if applicable (no prefilled reaction)
      if (analysis && analysis.confidence > 0.8 && analysis.requires_response) {
        this.pendingReplies.set(sentMessage.id, {
          messageData,
          replyDraft: this.generateSuggestedReply(messageData, analysis),
          messageType: 'High Level SMS',
          timestamp: new Date()
        });
        console.log(`📝 Stored pending High Level reply for approval (ID: ${sentMessage.id})`);
      }
      
      console.log(`✅ Enhanced High Level alert sent to ops lead`);

    } catch (error) {
      console.error('❌ Error sending High Level alert:', error.message);
    }
  }

  async sendReplyConfirmation(messageData, replyText) {
    try {
      const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
      if (!opsLeadId) return;

      const user = await this.discordClient.users.fetch(opsLeadId);
      
      const confirmationMessage = `✅ **Google Voice Reply Sent Successfully**\n\n` +
        `📞 **To:** ${messageData.clientPhone}\n` +
        `👤 **Name:** ${messageData.clientName || 'Unknown'}\n` +
        `💬 **Reply:** "${replyText}"\n` +
        `⏰ **Sent:** ${new Date().toLocaleString()}`;

      await user.send(confirmationMessage);
      console.log('✅ Reply confirmation sent to ops lead');
      
    } catch (error) {
      console.error('❌ Error sending reply confirmation:', error.message);
    }
  }

  async sendReplyError(messageData, errorMessage) {
    try {
      const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
      if (!opsLeadId) return;

      const user = await this.discordClient.users.fetch(opsLeadId);
      
      const errorAlert = `❌ **Google Voice Reply Failed**\n\n` +
        `📞 **To:** ${messageData.clientPhone}\n` +
        `👤 **Name:** ${messageData.clientName || 'Unknown'}\n` +
        `⚠️ **Error:** ${errorMessage}\n` +
        `💡 **Action:** Please send reply manually`;

      await user.send(errorAlert);
      console.log('❌ Reply error notification sent to ops lead');
      
    } catch (error) {
      console.error('❌ Error sending reply error notification:', error.message);
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

  // Helper methods for enhanced Discord DM formatting
  formatMessageTypeForDisplay(messageType) {
    const typeMap = {
      'customer_service': 'Customer service',
      'sales_inquiry': 'Sales inquiry',
      'complaint': 'Complaint',
      'operational': 'Operational',
      'payment': 'Payment',
      'spam': 'Spam',
      'new_inquiry': 'New inquiry',
      'booking_request': 'Booking request',
      'schedule_change': 'Schedule change',
      'compliment': 'Compliment',
      'payment_question': 'Payment question',
      'service_question': 'Service question',
      'other': 'Other'
    };
    return typeMap[messageType] || messageType;
  }

  getUrgencyEmoji(urgencyLevel) {
    const emojiMap = {
      'critical': '🚨',
      'high': '⚠️',
      'medium': '📋',
      'low': '💭'
    };
    return emojiMap[urgencyLevel] || '📋';
  }

  generateSuggestedReply(messageData, analysis) {
    const messageText = messageData.clientMessage.toLowerCase();
    const messageType = analysis.message_type;
    const clientName = messageData.clientName && messageData.clientName !== 'Me' ? messageData.clientName : '';
    const greeting = clientName ? `Hi ${clientName}! ` : 'Hi! ';
    
    // Enhanced contextual replies with specific keyword detection
    if (messageType === 'sales_inquiry' || messageType === 'new_inquiry') {
      if (messageText.includes('quote') || messageText.includes('price') || messageText.includes('cost') || messageText.includes('how much')) {
        if (messageText.includes('bedroom') || messageText.includes('bathroom') || messageText.includes('house') || messageText.includes('apartment')) {
          return `${greeting}Thank you for your interest! Based on what you've shared, I can provide a personalized quote. Could you confirm the number of bedrooms/bathrooms and your preferred frequency? We start at $80 for smaller homes with competitive rates for all sizes.`;
        }
        return `${greeting}I'd be happy to provide a quote! Could you please share the size of your home (bedrooms/bathrooms) and your preferred cleaning frequency? Our rates are very competitive and we offer exceptional service.`;
      }
      if (messageText.includes('available') || messageText.includes('schedule') || messageText.includes('appointment')) {
        return `${greeting}Great question! We have availability this week and can usually accommodate same-week bookings. What days work best for you? We're flexible with timing.`;
      }
      return `${greeting}Thank you for contacting Grime Guardians! We'd love to help with your cleaning needs. What type of cleaning service are you looking for?`;
    }
    
    if (messageType === 'booking_request') {
      if (messageText.includes('tomorrow') || messageText.includes('today') || messageText.includes('asap') || messageText.includes('urgent')) {
        return `${greeting}We can definitely help with short notice! Let me check our availability for tomorrow and get back to you within 30 minutes. What time would work best?`;
      }
      return `${greeting}Thank you for choosing Grime Guardians! I'll get you scheduled right away. What dates and times work best for you? We have good availability this week.`;
    }
    
    if (messageType === 'schedule_change') {
      if (messageText.includes('cancel')) {
        return `${greeting}No problem at all! I've noted your cancellation request. Would you like to reschedule for a different date, or shall I process this as a full cancellation?`;
      }
      if (messageText.includes('reschedule') || messageText.includes('move') || messageText.includes('change')) {
        return `${greeting}Absolutely! We understand schedules change. What new date and time would work better for you? I'll update your appointment right away.`;
      }
      return `${greeting}I'd be happy to help adjust your appointment. What changes do you need to make?`;
    }
    
    if (messageType === 'complaint') {
      if (messageText.includes('disappointed') || messageText.includes('unsatisfied') || messageText.includes('poor') || messageText.includes('bad')) {
        return `${greeting}I sincerely apologize - this is absolutely not the standard we maintain at Grime Guardians. I want to make this right immediately. Can we schedule a time today for me to call you to discuss how we can resolve this?`;
      }
      return `${greeting}I sincerely apologize for any issues with our service. This is not acceptable and I want to resolve it quickly. Could you please share more details so we can address this immediately?`;
    }
    
    if (messageType === 'payment' || messageType === 'payment_question') {
      if (messageText.includes('charge') || messageText.includes('bill') || messageText.includes('invoice')) {
        return `${greeting}I'll review your billing details right away and send you a detailed breakdown within the hour. If there are any discrepancies, we'll resolve them immediately.`;
      }
      return `${greeting}Thank you for reaching out about your payment. I'll review your account and get back to you within the hour with all the details you need.`;
    }
    
    if (messageType === 'customer_service' || messageType === 'service_question') {
      // Time-related inquiries
      if ((messageText.includes('time') || messageText.includes('when')) && 
          (messageText.includes('tomorrow') || messageText.includes('today') || messageText.includes('scheduled') || messageText.includes('coming'))) {
        return `${greeting}Let me check your appointment details right away! I'll text you back within 15 minutes with your exact scheduled time and our team member's name.`;
      }
      
      // Adding services
      if (messageText.includes('add') && (messageText.includes('dish') || messageText.includes('kitchen') || messageText.includes('extra'))) {
        return `${greeting}Absolutely! We can add dishes and any other kitchen tasks to your service. I'll note this in your appointment details and inform the team. Anything else you'd like us to include?`;
      }
      
      // Rescheduling within customer service
      if (messageText.includes('reschedule') || messageText.includes('change') || 
          messageText.includes('move') || messageText.includes('different day') ||
          messageText.includes('different time')) {
        return `${greeting}No problem! Life happens and we're flexible. What new date would work better for you? I can update your appointment right now.`;
      }
      
      // General questions
      if (messageText.includes('question') || messageText.includes('help') || messageText.includes('info') || messageText.includes('wondering')) {
        return `${greeting}I'm here to help! What specific questions do you have about your cleaning service? I'll get you the answers you need right away.`;
      }
      
      // Key access or entry issues
      if (messageText.includes('key') || messageText.includes('lock') || messageText.includes('door') || messageText.includes('entry')) {
        return `${greeting}Thanks for reaching out about access! I'll coordinate with our team to ensure smooth entry. Let me know the best way to handle this for your appointment.`;
      }
      
      return `${greeting}Thank you for reaching out! I'm here to help with your cleaning service. Let me assist you with that right away.`;
    }
    
    if (messageType === 'operational') {
      // Handle employee/team communications differently
      if (messageData.clientName && (messageData.clientName.includes('🧹') || messageData.clientName.includes('Team'))) {
        if (messageText.includes('running late') || messageText.includes('delay')) {
          return `Got it! Thanks for the heads up. I'll notify the client about the slight delay and adjust the schedule. Keep me posted on your ETA.`;
        }
        return `Understood! Thanks for the update. I'll coordinate accordingly and handle any client communication needed. Let me know if anything else comes up.`;
      }
      return `${greeting}Thank you for the update. I'll process this information and coordinate as needed. Is there anything else I should know?`;
    }
    
    if (messageType === 'compliment') {
      if (messageText.includes('amazing') || messageText.includes('excellent') || messageText.includes('perfect') || messageText.includes('outstanding')) {
        return `${greeting}Wow, thank you so much! This absolutely made our day. Our team takes such pride in their work and will be thrilled to hear this. We truly appreciate you taking the time to share this feedback!`;
      }
      return `${greeting}Thank you so much for the kind words! Our team will be thrilled to hear this feedback. We truly appreciate you taking the time to share your experience with Grime Guardians.`;
    }
    
    // Enhanced default response based on urgency
    if (analysis && analysis.urgency_level === 'high') {
      return `${greeting}Thank you for reaching out! I can see this is time-sensitive. I'll prioritize your message and respond within the hour. If it's extremely urgent, please call us at (612) 584-9396.`;
    }
    
    // Default response for other types
    return `${greeting}Thank you for contacting Grime Guardians! We've received your message and will respond within a few hours. If this is urgent, please call us at (612) 584-9396.`;
  }
  
  // === HIGH LEVEL CONVERSATION MONITORING ===
  async checkHighLevelConversations() {
    try {
      console.log('📱 Checking High Level conversations via OAuth...');
      
      if (!this.highLevelOAuth.isConfigured()) {
        console.log('⚠️ High Level OAuth not configured, skipping conversation check');
        this.lastHighLevelCheck = new Date();
        return;
      }
      
      // Get conversations from High Level OAuth API
      const conversations = await this.highLevelOAuth.getConversations();
      
      if (!conversations || conversations.length === 0) {
        console.log('📱 No High Level conversations found');
        this.lastHighLevelCheck = new Date();
        return;
      }
      
      console.log(`📱 Found ${conversations.length} High Level conversations`);
      
      // Filter for new messages since last check
      const recentConversations = [];
      
      for (const conversation of conversations) {
        // Get recent messages for this conversation
        try {
          const messages = await this.highLevelOAuth.getMessages(conversation.id, { limit: 5 });
          
          if (messages && messages.length > 0) {
            // Find the most recent inbound message
            const recentInbound = messages.find(msg => {
              const messageDate = new Date(msg.dateAdded);
              return messageDate > this.lastHighLevelCheck && 
                     msg.direction === 'inbound' &&
                     !this.processedHighLevelIds.has(msg.id);
            });
            
            if (recentInbound) {
              conversation.lastMessage = recentInbound;
              recentConversations.push(conversation);
            }
          }
        } catch (msgError) {
          console.error(`❌ Error getting messages for conversation ${conversation.id}:`, msgError.message);
        }
      }
      
      console.log(`📱 Found ${recentConversations.length} new High Level messages`);
      
      // Process each new conversation
      for (const conversation of recentConversations) {
        const lastMessage = conversation.lastMessage;
        
        if (lastMessage && !this.processedHighLevelIds.has(lastMessage.id)) {
          console.log(`📱 Processing High Level message from: ${conversation.contact?.name || conversation.contact?.phone || 'Unknown'}`);
          
          // Get contact details if needed
          let contactDetails = conversation.contact;
          if (!contactDetails && conversation.contactId) {
            try {
              contactDetails = await this.highLevelOAuth.getContact(conversation.contactId);
            } catch (contactError) {
              console.error(`❌ Error getting contact details:`, contactError.message);
              contactDetails = { name: 'Unknown', phone: '' };
            }
          }
          
          // Create message data for processing
          const messageData = {
            source: 'high_level',
            businessNumber: '651-515-1478',
            conversationId: conversation.id,
            contactId: conversation.contactId,
            clientName: contactDetails?.name || 'Unknown',
            clientPhone: contactDetails?.phone || '',
            clientMessage: lastMessage.body || '',
            timestamp: new Date(lastMessage.dateAdded),
            from: `${contactDetails?.name || 'Unknown'} <${contactDetails?.phone || 'no-phone'}>`,
            subject: `High Level SMS from ${contactDetails?.phone || 'Unknown'}`,
            id: lastMessage.id,
            threadId: conversation.id
          };
          
          // Analyze with LangChain if available
          let analysis = null;
          if (this.langchainAgent) {
            analysis = await this.analyzeHighLevelMessageWithLangChain(messageData);
          }
          
          // Send enhanced Discord DM to ops lead
          await this.sendHighLevelAlert(messageData, analysis);
          
          // Mark as processed
          this.processedHighLevelIds.add(lastMessage.id);
        }
      }
      
      // Update last check time
      this.lastHighLevelCheck = new Date();
      console.log(`📱 Processed ${recentConversations.length} new High Level messages`);
      
    } catch (error) {
      console.error('❌ Error checking High Level conversations:', error.message);
      // Update last check time even on error to prevent spam
      this.lastHighLevelCheck = new Date();
    }
  }
}

module.exports = EmailCommunicationMonitor;
