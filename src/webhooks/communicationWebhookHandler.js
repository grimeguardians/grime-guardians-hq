// src/webhooks/communicationWebhookHandler.js
// Unified webhook handler for all communication channels

const { createScheduleRequestPage } = require('../utils/notion');
const { detectScheduleRequest } = require('../utils/scheduleDetection');
const GoogleVoiceWebhookHandler = require('../utils/googleVoiceWebhook');

class CommunicationWebhookHandler {
  constructor(discordClient, emailMonitor) {
    this.discordClient = discordClient;
    this.emailMonitor = emailMonitor;
    this.processedMessageIds = new Set();
    this.googleVoiceHandler = new GoogleVoiceWebhookHandler();
    
    // Rate limiting to prevent spam
    this.rateLimiter = new Map();
    this.maxMessagesPerMinute = 10;
    
    // Channel mappings for Discord notifications
    this.channelMappings = {
      'high_level_webhook': process.env.DISCORD_HIGHLEVEL_CHANNEL || process.env.DISCORD_CHANNEL_ID,
      'google_voice_webhook': process.env.DISCORD_GOOGLEVOICE_CHANNEL || process.env.DISCORD_CHANNEL_ID,
      'facebook_webhook': process.env.DISCORD_FACEBOOK_CHANNEL || process.env.DISCORD_CHANNEL_ID,
      'instagram_webhook': process.env.DISCORD_INSTAGRAM_CHANNEL || process.env.DISCORD_CHANNEL_ID,
      'default': process.env.DISCORD_CHANNEL_ID
    };
  }

  /**
   * Handle High Level SMS/Email webhooks
   * @param {Object} webhookData - High Level webhook payload
   */
  async handleHighLevelMessage(webhookData) {
    try {
      console.log('📱 High Level webhook received:', webhookData.type);
      
      // Extract message data from webhook
      const messageData = this.parseHighLevelWebhook(webhookData);
      
      // Prevent duplicate processing
      if (this.processedMessageIds.has(messageData.id)) {
        console.log('⚠️ Duplicate message ignored:', messageData.id);
        return;
      }
      
      this.processedMessageIds.add(messageData.id);
      
      // Only process inbound messages
      if (messageData.direction !== 'inbound') {
        console.log('📤 Outbound message ignored');
        return;
      }
      
      // Detect if this is a schedule request
      const scheduleDetection = await detectScheduleRequest(messageData.message);
      
      if (scheduleDetection.isScheduleRequest && scheduleDetection.confidence > 0.7) {
        await this.handleScheduleRequest(messageData, scheduleDetection);
      } else {
        await this.handleGeneralMessage(messageData);
      }
      
    } catch (error) {
      console.error('❌ Error handling High Level webhook:', error.message);
    }
  }

  /**
   * Handle Facebook Messenger webhooks
   */
  async handleFacebookMessage(webhookData) {
    try {
      console.log('📘 Facebook webhook received');
      
      const messageData = this.parseFacebookWebhook(webhookData);
      await this.handleGeneralMessage(messageData);
      
    } catch (error) {
      console.error('❌ Error handling Facebook webhook:', error.message);
    }
  }

  /**
   * Handle Instagram DM webhooks
   */
  async handleInstagramMessage(webhookData) {
    try {
      console.log('📸 Instagram webhook received');
      
      const messageData = this.parseInstagramWebhook(webhookData);
      await this.handleGeneralMessage(messageData);
      
    } catch (error) {
      console.error('❌ Error handling Instagram webhook:', error.message);
    }
  }

  /**
   * Handle Google Voice webhooks (via Gmail, Zapier, or custom polling)
   */
  async handleGoogleVoiceMessage(webhookData) {
    try {
      console.log('📞 Google Voice webhook received:', webhookData.source);
      
      // Validate payload
      if (!this.googleVoiceHandler.validateWebhookPayload(webhookData)) {
        console.log('⚠️ Invalid Google Voice webhook payload');
        return;
      }
      
      const messageData = this.googleVoiceHandler.parseGoogleVoiceWebhook(webhookData);
      
      // Prevent duplicate processing
      if (this.processedMessageIds.has(messageData.id)) {
        console.log('⚠️ Duplicate Google Voice message ignored:', messageData.id);
        return;
      }
      
      this.processedMessageIds.add(messageData.id);
      
      // Only process inbound messages
      if (messageData.direction !== 'inbound') {
        console.log('📤 Outbound Google Voice message ignored');
        return;
      }
      
      // Handle voicemails differently
      if (messageData.type === 'Voicemail') {
        await this.handleVoicemail(messageData);
      } else {
        // Detect if this is a schedule request
        const scheduleDetection = await detectScheduleRequest(messageData.message);
        
        if (scheduleDetection.isScheduleRequest && scheduleDetection.confidence > 0.7) {
          await this.handleScheduleRequest(messageData, scheduleDetection);
        } else {
          await this.handleGeneralMessage(messageData);
        }
      }
      
    } catch (error) {
      console.error('❌ Error handling Google Voice webhook:', error.message);
    }
  }

  /**
   * Handle Google Business Messages webhooks
   */
  async handleGoogleBusinessMessage(webhookData) {
    try {
      console.log('🏢 Google Business webhook received');
      
      const messageData = this.parseGoogleBusinessWebhook(webhookData);
      await this.handleGeneralMessage(messageData);
      
    } catch (error) {
      console.error('❌ Error handling Google Business webhook:', error.message);
    }
  }

  /**
   * Parse High Level webhook payload
   */
  parseHighLevelWebhook(webhookData) {
    return {
      id: webhookData.id || webhookData.messageId,
      source: 'high_level_webhook',
      type: webhookData.type, // 'SMS', 'Email', etc.
      direction: webhookData.direction,
      message: webhookData.body || webhookData.message,
      clientName: webhookData.contact?.name || 'Unknown',
      clientPhone: webhookData.contact?.phone || '',
      clientEmail: webhookData.contact?.email || '',
      contactId: webhookData.contactId,
      conversationId: webhookData.conversationId,
      timestamp: new Date(webhookData.dateAdded || Date.now()),
      businessNumber: '651-515-1478',
      from: `${webhookData.contact?.name || 'Unknown'} <${webhookData.contact?.phone || webhookData.contact?.email || 'no-contact'}>`,
      subject: `High Level ${webhookData.type} from ${webhookData.contact?.phone || webhookData.contact?.email || 'Unknown'}`
    };
  }

  /**
   * Parse Facebook webhook payload
   */
  parseFacebookWebhook(webhookData) {
    const entry = webhookData.entry?.[0];
    const messaging = entry?.messaging?.[0];
    
    return {
      id: messaging?.message?.mid,
      source: 'facebook_webhook',
      type: 'Facebook_Message',
      direction: 'inbound',
      message: messaging?.message?.text,
      clientName: messaging?.sender?.id, // You'd lookup real name via Graph API
      clientPhone: '',
      clientEmail: '',
      contactId: messaging?.sender?.id,
      conversationId: messaging?.sender?.id,
      timestamp: new Date(messaging?.timestamp || Date.now()),
      businessNumber: 'Facebook',
      from: `Facebook User <${messaging?.sender?.id}>`,
      subject: `Facebook Message from ${messaging?.sender?.id}`
    };
  }

  /**
   * Parse Instagram webhook payload
   */
  parseInstagramWebhook(webhookData) {
    const entry = webhookData.entry?.[0];
    const messaging = entry?.messaging?.[0];
    
    return {
      id: messaging?.message?.mid,
      source: 'instagram_webhook',
      type: 'Instagram_DM',
      direction: 'inbound',
      message: messaging?.message?.text,
      clientName: messaging?.sender?.username || messaging?.sender?.id,
      clientPhone: '',
      clientEmail: '',
      contactId: messaging?.sender?.id,
      conversationId: messaging?.sender?.id,
      timestamp: new Date(messaging?.timestamp || Date.now()),
      businessNumber: 'Instagram',
      from: `Instagram User <${messaging?.sender?.username || messaging?.sender?.id}>`,
      subject: `Instagram DM from ${messaging?.sender?.username || messaging?.sender?.id}`
    };
  }

  /**
   * Parse Google Business Messages webhook payload
   */
  parseGoogleBusinessWebhook(webhookData) {
    return {
      id: webhookData.messageId || `gbm_${Date.now()}`,
      source: 'google_business_webhook',
      type: 'Google_Business_Message',
      direction: 'inbound',
      message: webhookData.text || webhookData.message,
      clientName: webhookData.context?.userDisplayName || 'Business Customer',
      clientPhone: '',
      clientEmail: '',
      contactId: webhookData.context?.conversationId,
      conversationId: webhookData.context?.conversationId,
      timestamp: new Date(webhookData.createTime || Date.now()),
      businessNumber: 'Google Business',
      from: `Business Customer <${webhookData.context?.conversationId}>`,
      subject: `Google Business Message from ${webhookData.context?.userDisplayName || 'Customer'}`
    };
  }

  /**
   * Handle voicemail messages with special processing
   */
  async handleVoicemail(messageData) {
    console.log('📞 Voicemail received from:', messageData.clientPhone);
    
    // Enhanced Discord notification for voicemails
    const embed = {
      title: '📞 New Voicemail Received',
      description: messageData.message || 'Voicemail received (no transcript available)',
      fields: [
        { name: 'From', value: messageData.clientName, inline: true },
        { name: 'Phone', value: messageData.clientPhone, inline: true },
        { name: 'Time', value: messageData.timestamp.toLocaleString(), inline: true }
      ],
      color: 0xff9800, // Orange for voicemails
      footer: { text: `Business Line: ${messageData.businessNumber}` }
    };
    
    // Add voicemail-specific fields
    if (messageData.metadata?.duration) {
      embed.fields.push({ name: 'Duration', value: `${messageData.metadata.duration}s`, inline: true });
    }
    if (messageData.metadata?.audioUrl) {
      embed.fields.push({ name: 'Audio', value: '[Listen](${messageData.metadata.audioUrl})', inline: true });
    }
    
    // Send to appropriate Discord channel
    const channelId = this.channelMappings['google_voice_webhook'] || this.channelMappings['default'];
    await this.sendDiscordNotification(channelId, embed, 'voicemail');
    
    // Create Notion entry for voicemail follow-up
    await createScheduleRequestPage({
      clientName: messageData.clientName,
      clientPhone: messageData.clientPhone,
      clientEmail: messageData.clientEmail,
      requestText: `VOICEMAIL: ${messageData.message}`,
      source: messageData.source,
      confidence: 0.9, // High confidence for voicemails
      urgency: 'high', // Voicemails typically need quick response
      timestamp: messageData.timestamp,
      metadata: messageData.metadata
    });
  }

  /**
   * Enhanced Discord notification with channel routing
   */
  async sendDiscordNotification(channelId, embed, messageType = 'general') {
    try {
      const channel = await this.discordClient.channels.fetch(channelId);
      
      if (!channel) {
        console.error('❌ Discord channel not found:', channelId);
        return false;
      }
      
      // Add timestamp to all embeds
      embed.timestamp = new Date().toISOString();
      
      // Send notification
      await channel.send({ embeds: [embed] });
      
      // Also send DM to ops lead for high priority items
      if (messageType === 'schedule' || messageType === 'voicemail') {
        const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
        if (opsLeadId) {
          try {
            const opsLead = await this.discordClient.users.fetch(opsLeadId);
            await opsLead.send({ embeds: [embed] });
          } catch (dmError) {
            console.log('⚠️ Could not send DM to ops lead:', dmError.message);
          }
        }
      }
      
      return true;
    } catch (error) {
      console.error('❌ Error sending Discord notification:', error.message);
      return false;
    }
  }

  /**
   * Get appropriate Discord channel for message source
   */
  getDiscordChannel(messageSource) {
    return this.channelMappings[messageSource] || this.channelMappings['default'];
  }

  /**
   * Check rate limiting for a contact
   */
  checkRateLimit(contactId) {
    const now = Date.now();
    const windowStart = now - (60 * 1000); // 1 minute window
    
    if (!this.rateLimiter.has(contactId)) {
      this.rateLimiter.set(contactId, []);
    }
    
    const messages = this.rateLimiter.get(contactId);
    
    // Remove old messages outside the window
    const recentMessages = messages.filter(timestamp => timestamp > windowStart);
    
    // Check if over limit
    if (recentMessages.length >= this.maxMessagesPerMinute) {
      console.log(`⚠️ Rate limit exceeded for contact: ${contactId}`);
      return false;
    }
    
    // Add current message timestamp
    recentMessages.push(now);
    this.rateLimiter.set(contactId, recentMessages);
    
    return true;
  }

  /**
   * Enhanced general message handler with rate limiting
   */
  async handleGeneralMessage(messageData) {
    console.log('💬 General message processing');
    
    // Check rate limiting
    if (!this.checkRateLimit(messageData.contactId)) {
      console.log('⚠️ Message rate limited, sending summary notification');
      await this.sendRateLimitNotification(messageData);
      return;
    }
    
    // Create enhanced Discord embed
    const embed = this.createGeneralMessageEmbed(messageData);
    
    // Send to appropriate channel
    const channelId = this.getDiscordChannel(messageData.source);
    await this.sendDiscordNotification(channelId, embed, 'general');
    
    // Generate and suggest response
    const suggestedReply = await this.generateGeneralResponse(messageData);
    await this.sendReplyApproval(messageData, suggestedReply, 'general');
  }

  /**
   * Create enhanced Discord embed for general messages
   */
  createGeneralMessageEmbed(messageData) {
    const sourceEmoji = this.getSourceEmoji(messageData.source);
    const sourceDisplay = this.getSourceDisplay(messageData.source);
    
    return {
      color: this.getSourceColor(messageData.source),
      title: `${sourceEmoji} New ${messageData.type} - ${sourceDisplay}`,
      description: messageData.message.substring(0, 2000),
      fields: [
        {
          name: '👤 Contact',
          value: `${messageData.clientName}\n${messageData.clientPhone || 'No phone'}\n${messageData.clientEmail || 'No email'}`,
          inline: true
        },
        {
          name: '📍 Details',
          value: `**Source:** ${sourceDisplay}\n**Type:** ${messageData.type}\n**Time:** ${messageData.timestamp.toLocaleString()}`,
          inline: true
        }
      ],
      footer: {
        text: `${messageData.source.toUpperCase()} • Webhook Alert`,
        icon_url: 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f4e8.png'
      }
    };
  }

  /**
   * Get emoji for message source
   */
  getSourceEmoji(source) {
    const emojis = {
      'high_level_webhook': '🔥',
      'google_voice_webhook': '📞',
      'facebook_webhook': '📘',
      'instagram_webhook': '📸',
      'google_business_webhook': '🏢'
    };
    return emojis[source] || '💬';
  }

  /**
   * Get display name for source
   */
  getSourceDisplay(source) {
    const displays = {
      'high_level_webhook': 'High Level',
      'google_voice_webhook': 'Google Voice',
      'facebook_webhook': 'Facebook Messenger',
      'instagram_webhook': 'Instagram DM',
      'google_business_webhook': 'Google Business'
    };
    return displays[source] || 'Unknown Source';
  }

  /**
   * Get color for source
   */
  getSourceColor(source) {
    const colors = {
      'high_level_webhook': 0x4CAF50, // Green
      'google_voice_webhook': 0x4285F4, // Google Blue
      'facebook_webhook': 0x1877F2, // Facebook Blue
      'instagram_webhook': 0xE4405F, // Instagram Pink
      'google_business_webhook': 0xFF9800 // Orange
    };
    return colors[source] || 0x6C757D; // Gray
  }

  /**
   * Send rate limit notification
   */
  async sendRateLimitNotification(messageData) {
    const embed = {
      color: 0xFFC107, // Yellow warning
      title: '⚠️ Rate Limit Exceeded',
      description: `Contact ${messageData.clientName} (${messageData.clientPhone}) has exceeded the message rate limit.`,
      fields: [
        { name: 'Source', value: this.getSourceDisplay(messageData.source), inline: true },
        { name: 'Time', value: messageData.timestamp.toLocaleString(), inline: true }
      ],
      footer: { text: 'Consider reaching out directly if this is urgent' }
    };
    
    const channelId = this.getDiscordChannel(messageData.source);
    await this.sendDiscordNotification(channelId, embed, 'warning');
  }

  /**
   * Handle schedule-related requests
   */
  async handleScheduleRequest(messageData, scheduleDetection) {
    console.log('📅 Schedule request detected:', scheduleDetection.confidence);
    
    // Create Notion page for schedule request
    await createScheduleRequestPage({
      clientName: messageData.clientName,
      clientPhone: messageData.clientPhone,
      clientEmail: messageData.clientEmail,
      requestText: messageData.message,
      source: messageData.source,
      confidence: scheduleDetection.confidence,
      urgency: scheduleDetection.urgency || 'medium',
      timestamp: messageData.timestamp
    });
    
    // Send Discord alert with schedule-specific formatting
    await this.sendScheduleAlert(messageData, scheduleDetection);
    
    // Generate and suggest professional response
    const suggestedReply = await this.generateScheduleResponse(messageData, scheduleDetection);
    await this.sendReplyApproval(messageData, suggestedReply, 'schedule');
  }

  /**
   * Send Discord alert for schedule requests
   */
  async sendScheduleAlert(messageData, scheduleDetection) {
    const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
    const opsLead = await this.discordClient.users.fetch(opsLeadId);
    
    const embed = {
      color: 0xFF6B35, // Orange for schedule requests
      title: '📅 SCHEDULE REQUEST DETECTED',
      description: `**${scheduleDetection.confidence * 100}% Confidence** | **${scheduleDetection.urgency?.toUpperCase() || 'MEDIUM'} Priority**`,
      fields: [
        {
          name: '👤 Client Information',
          value: `**Name:** ${messageData.clientName}\n**Phone:** ${messageData.clientPhone || 'N/A'}\n**Email:** ${messageData.clientEmail || 'N/A'}`,
          inline: true
        },
        {
          name: '📱 Source Channel',
          value: `**Platform:** ${messageData.source.replace('_webhook', '').replace('_', ' ').toUpperCase()}\n**Type:** ${messageData.type}\n**Time:** ${messageData.timestamp.toLocaleString()}`,
          inline: true
        },
        {
          name: '💬 Client Message',
          value: `${messageData.message.substring(0, 1000)}${messageData.message.length > 1000 ? '...' : ''}`,
          inline: false
        }
      ],
      footer: {
        text: `${messageData.source.toUpperCase()} • Webhook Alert`,
        icon_url: 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f4c5.png'
      },
      timestamp: messageData.timestamp.toISOString()
    };
    
    await opsLead.send({ embeds: [embed] });
  }

  /**
   * Generate suggested response for schedule requests
   */
  async generateScheduleResponse(messageData, scheduleDetection) {
    const templates = {
      reschedule: `Hi ${messageData.clientName}! I received your request to reschedule. I'll check our availability and get back to you within the hour with some options. Thank you for letting us know in advance!`,
      cancel: `Hi ${messageData.clientName}! I've received your cancellation request. I'll process this right away and send you a confirmation. If you need to reschedule for a future date, just let me know!`,
      emergency: `Hi ${messageData.clientName}! I see this is urgent. I'm checking our emergency availability right now and will respond within 15 minutes with our options. Thank you for reaching out!`,
      general: `Hi ${messageData.clientName}! Thank you for contacting Grime Guardians about scheduling. I'll review your request and get back to you within 30 minutes with availability options.`
    };
    
    const messageType = scheduleDetection.type || 'general';
    return templates[messageType] || templates.general;
  }

  /**
   * Generate suggested response for general messages
   */
  async generateGeneralResponse(messageData) {
    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
    
    return `${greeting} ${messageData.clientName}! Thank you for contacting Grime Guardians. I've received your message and will respond within a few hours. If this is urgent, please call us at (612) 584-9396.`;
  }

  /**
   * Send reply approval to Discord
   */
  async sendReplyApproval(messageData, suggestedReply, type) {
    const opsLeadId = process.env.DISCORD_OPS_LEAD_ID;
    const opsLead = await this.discordClient.users.fetch(opsLeadId);
    
    const embed = {
      color: type === 'schedule' ? 0x10B981 : 0x6366F1, // Green for schedule, indigo for general
      title: `${type === 'schedule' ? '📅' : '💬'} SUGGESTED REPLY`,
      description: `**Platform:** ${messageData.source.replace('_webhook', '').replace('_', ' ').toUpperCase()}\n**Client:** ${messageData.clientName}`,
      fields: [
        {
          name: '📝 Suggested Response',
          value: suggestedReply,
          inline: false
        },
        {
          name: '🎯 Action Required',
          value: '✅ React to approve and send\n❌ React to reject\n✏️ Reply to customize message',
          inline: false
        }
      ],
      footer: {
        text: `Reply Approval • ${messageData.source.toUpperCase()}`,
        icon_url: 'https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/2705.png'
      }
    };
    
    const approvalMessage = await opsLead.send({ embeds: [embed] });
    
    // Add reaction buttons for approval
    await approvalMessage.react('✅');
    await approvalMessage.react('❌');
    
    // Store pending reply for reaction handling
    this.emailMonitor.pendingReplies.set(approvalMessage.id, {
      messageData,
      suggestedReply,
      type: messageData.source
    });
  }
}

module.exports = CommunicationWebhookHandler;
