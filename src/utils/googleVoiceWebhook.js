// src/utils/googleVoiceWebhook.js
// Google Voice webhook integration for SMS/Voicemail monitoring

class GoogleVoiceWebhookHandler {
  constructor() {
    this.supportedMessageTypes = ['sms', 'voicemail', 'call'];
  }

  /**
   * Parse Google Voice webhook payload
   * Note: Google Voice doesn't have official webhooks, so this handles:
   * 1. Email notifications from Google Voice
   * 2. Third-party services like Zapier/IFTTT
   * 3. Custom polling results formatted as webhook data
   */
  parseGoogleVoiceWebhook(webhookData) {
    // Handle different webhook sources
    if (webhookData.source === 'gmail_notification') {
      return this.parseGmailNotification(webhookData);
    } else if (webhookData.source === 'zapier') {
      return this.parseZapierWebhook(webhookData);
    } else if (webhookData.source === 'custom_polling') {
      return this.parsePollingResult(webhookData);
    }
    
    // Default parsing for direct webhook format
    return {
      id: webhookData.id || `gv_${Date.now()}`,
      source: 'google_voice_webhook',
      type: webhookData.type || 'SMS',
      direction: webhookData.direction || 'inbound',
      message: webhookData.message || webhookData.text,
      clientName: webhookData.contact?.name || this.extractNameFromPhone(webhookData.from),
      clientPhone: this.normalizePhoneNumber(webhookData.from || webhookData.phone),
      clientEmail: '',
      contactId: this.normalizePhoneNumber(webhookData.from || webhookData.phone),
      conversationId: this.normalizePhoneNumber(webhookData.from || webhookData.phone),
      timestamp: new Date(webhookData.timestamp || webhookData.time || Date.now()),
      businessNumber: '651-515-1478',
      from: `${webhookData.contact?.name || 'Unknown'} <${webhookData.from || 'no-phone'}>`,
      subject: `Google Voice ${webhookData.type || 'SMS'} from ${webhookData.from || 'Unknown'}`,
      metadata: {
        duration: webhookData.duration, // for voicemails
        transcript: webhookData.transcript, // for voicemails
        audioUrl: webhookData.audioUrl // for voicemails
      }
    };
  }

  /**
   * Parse Gmail notification about Google Voice activity
   */
  parseGmailNotification(emailData) {
    const subject = emailData.subject || '';
    const body = emailData.body || '';
    
    // Extract message type from subject
    let messageType = 'SMS';
    if (subject.includes('Voicemail')) messageType = 'Voicemail';
    if (subject.includes('Missed call')) messageType = 'Missed_Call';
    
    // Extract phone number from email content
    const phoneMatch = body.match(/(\(\d{3}\)\s?\d{3}-\d{4}|\d{10}|\+1\d{10})/);
    const phone = phoneMatch ? this.normalizePhoneNumber(phoneMatch[1]) : '';
    
    // Extract message content
    let message = '';
    if (messageType === 'SMS') {
      const messageMatch = body.match(/Message:\s*(.+?)(?:\n|$)/s);
      message = messageMatch ? messageMatch[1].trim() : body;
    } else if (messageType === 'Voicemail') {
      const transcriptMatch = body.match(/Transcript:\s*(.+?)(?:\n|$)/s);
      message = transcriptMatch ? transcriptMatch[1].trim() : 'Voicemail received';
    }
    
    return {
      id: `gv_gmail_${emailData.id}`,
      source: 'google_voice_gmail',
      type: messageType,
      direction: 'inbound',
      message: message,
      clientName: this.extractNameFromPhone(phone),
      clientPhone: phone,
      clientEmail: '',
      contactId: phone,
      conversationId: phone,
      timestamp: new Date(emailData.timestamp || Date.now()),
      businessNumber: '651-515-1478',
      from: `${this.extractNameFromPhone(phone)} <${phone}>`,
      subject: `Google Voice ${messageType} from ${phone}`,
      metadata: {
        originalEmailId: emailData.id,
        emailSubject: subject
      }
    };
  }

  /**
   * Parse Zapier webhook for Google Voice
   */
  parseZapierWebhook(webhookData) {
    return {
      id: `gv_zapier_${webhookData.id || Date.now()}`,
      source: 'google_voice_zapier',
      type: webhookData.message_type || 'SMS',
      direction: 'inbound',
      message: webhookData.body || webhookData.message,
      clientName: webhookData.contact_name || this.extractNameFromPhone(webhookData.from_number),
      clientPhone: this.normalizePhoneNumber(webhookData.from_number),
      clientEmail: '',
      contactId: this.normalizePhoneNumber(webhookData.from_number),
      conversationId: this.normalizePhoneNumber(webhookData.from_number),
      timestamp: new Date(webhookData.created_at || Date.now()),
      businessNumber: '651-515-1478',
      from: `${webhookData.contact_name || 'Unknown'} <${webhookData.from_number}>`,
      subject: `Google Voice ${webhookData.message_type || 'SMS'} from ${webhookData.from_number}`
    };
  }

  /**
   * Parse custom polling result formatted as webhook
   */
  parsePollingResult(pollingData) {
    return {
      id: `gv_poll_${pollingData.messageId || Date.now()}`,
      source: 'google_voice_polling',
      type: pollingData.type || 'SMS',
      direction: pollingData.direction || 'inbound',
      message: pollingData.text || pollingData.message,
      clientName: pollingData.displayName || this.extractNameFromPhone(pollingData.phoneNumber),
      clientPhone: this.normalizePhoneNumber(pollingData.phoneNumber),
      clientEmail: '',
      contactId: this.normalizePhoneNumber(pollingData.phoneNumber),
      conversationId: pollingData.conversationId || this.normalizePhoneNumber(pollingData.phoneNumber),
      timestamp: new Date(pollingData.timestamp || Date.now()),
      businessNumber: '651-515-1478',
      from: `${pollingData.displayName || 'Unknown'} <${pollingData.phoneNumber}>`,
      subject: `Google Voice ${pollingData.type || 'SMS'} from ${pollingData.phoneNumber}`
    };
  }

  /**
   * Normalize phone number format
   */
  normalizePhoneNumber(phone) {
    if (!phone) return '';
    
    // Remove all non-digit characters
    const digits = phone.replace(/\D/g, '');
    
    // Handle different formats
    if (digits.length === 10) {
      return `+1${digits}`;
    } else if (digits.length === 11 && digits.startsWith('1')) {
      return `+${digits}`;
    }
    
    return phone; // Return original if can't normalize
  }

  /**
   * Extract name from phone number (basic implementation)
   */
  extractNameFromPhone(phone) {
    if (!phone) return 'Unknown';
    
    // You could integrate with a contact database here
    // For now, just return a formatted version
    const normalized = this.normalizePhoneNumber(phone);
    return `Contact ${normalized.slice(-4)}`;
  }

  /**
   * Validate webhook payload
   */
  validateWebhookPayload(payload) {
    if (!payload) return false;
    
    // Check for required fields based on source
    if (payload.source === 'gmail_notification') {
      return payload.subject && payload.body;
    } else if (payload.source === 'zapier') {
      return payload.from_number && (payload.body || payload.message);
    } else if (payload.source === 'custom_polling') {
      return payload.phoneNumber && payload.text;
    }
    
    // Default validation
    return payload.message || payload.text;
  }

  /**
   * Format Google Voice message for Discord
   */
  formatForDiscord(messageData) {
    const emoji = this.getMessageEmoji(messageData.type);
    const source = this.getSourceDisplay(messageData.source);
    
    return {
      title: `${emoji} ${messageData.type} - ${source}`,
      description: messageData.message,
      fields: [
        { name: 'From', value: messageData.clientName, inline: true },
        { name: 'Phone', value: messageData.clientPhone, inline: true },
        { name: 'Time', value: messageData.timestamp.toLocaleString(), inline: true }
      ],
      color: this.getMessageColor(messageData.type),
      footer: { text: `Business Line: ${messageData.businessNumber}` }
    };
  }

  /**
   * Get emoji for message type
   */
  getMessageEmoji(type) {
    const emojis = {
      'SMS': '📱',
      'Voicemail': '📞',
      'Missed_Call': '📵',
      'Call': '☎️'
    };
    return emojis[type] || '📱';
  }

  /**
   * Get source display name
   */
  getSourceDisplay(source) {
    const displays = {
      'google_voice_webhook': 'Google Voice',
      'google_voice_gmail': 'Google Voice (Email)',
      'google_voice_zapier': 'Google Voice (Zapier)',
      'google_voice_polling': 'Google Voice (Polling)'
    };
    return displays[source] || 'Google Voice';
  }

  /**
   * Get color for message type
   */
  getMessageColor(type) {
    const colors = {
      'SMS': 0x4285f4, // Google Blue
      'Voicemail': 0xff9800, // Orange
      'Missed_Call': 0xf44336, // Red
      'Call': 0x4caf50 // Green
    };
    return colors[type] || 0x4285f4;
  }
}

module.exports = GoogleVoiceWebhookHandler;
