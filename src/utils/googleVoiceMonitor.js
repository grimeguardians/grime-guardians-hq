/**
 * Google Voice Monitor - Monitors Google Voice messages for schedule changes
 * Uses email forwarding or IMAP to monitor Google Voice notifications
 */

const { ImapFlow } = require('imapflow');
require('dotenv').config();

class GoogleVoiceMonitor {
  constructor() {
    this.emailEnabled = process.env.GOOGLE_VOICE_EMAIL_MONITORING === 'true';
    this.imapConfig = {
      host: process.env.IMAP_HOST || 'imap.gmail.com',
      port: process.env.IMAP_PORT || 993,
      secure: true,
      auth: {
        user: process.env.GOOGLE_VOICE_EMAIL,
        pass: process.env.GOOGLE_VOICE_EMAIL_PASSWORD // App password for Gmail
      }
    };
    
    this.scheduleKeywords = [
      'reschedule', 'schedule', 'move', 'change', 'cancel', 'postpone',
      'different time', 'another day', 'push back', 'emergency',
      'can we change', 'need to move', 'something came up'
    ];
  }

  /**
   * Monitor Google Voice messages via email notifications
   * Google Voice can forward SMS/voicemail notifications to email
   */
  async monitorViaEmail() {
    if (!this.emailEnabled) {
      console.log('[GoogleVoiceMonitor] Email monitoring disabled');
      return [];
    }

    try {
      console.log('[GoogleVoiceMonitor] Checking Google Voice email notifications...');
      
      const client = new ImapFlow(this.imapConfig);
      await client.connect();
      
      // Select inbox
      await client.mailboxOpen('INBOX');
      
      // Search for recent Google Voice messages (last 24 hours)
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      
      const messages = client.search({
        from: 'voice-noreply@google.com',
        since: yesterday
      });
      
      const scheduleRequests = [];
      
      for await (let message of client.fetch(messages, { envelope: true, bodyText: true })) {
        const content = message.bodyText?.text || '';
        const subject = message.envelope.subject || '';
        
        // Extract phone number from Google Voice notification
        const phoneMatch = subject.match(/from ([\+\d\-\(\)\s]+)/);
        const phoneNumber = phoneMatch ? phoneMatch[1].trim() : '';
        
        // Analyze content for schedule keywords
        const detection = this.analyzeForScheduleRequest(content);
        
        if (detection.isScheduleRequest) {
          scheduleRequests.push({
            source: 'google_voice',
            phoneNumber,
            content: content.substring(0, 500), // Limit content length
            timestamp: message.envelope.date,
            detection,
            urgency: this.calculateUrgency(content)
          });
        }
      }
      
      await client.logout();
      return scheduleRequests;
      
    } catch (error) {
      console.error('[GoogleVoiceMonitor] Email monitoring error:', error.message);
      return [];
    }
  }

  /**
   * Alternative: Monitor via Google Voice web interface (requires browser automation)
   */
  async monitorViaWebInterface() {
    // This would require puppeteer or similar for web scraping
    // Implementation placeholder for future enhancement
    console.log('[GoogleVoiceMonitor] Web interface monitoring not implemented yet');
    return [];
  }

  /**
   * Analyze message content for schedule requests
   */
  analyzeForScheduleRequest(content) {
    const lowerContent = content.toLowerCase();
    
    const foundKeywords = this.scheduleKeywords.filter(keyword => 
      lowerContent.includes(keyword)
    );
    
    const isScheduleRequest = foundKeywords.length > 0;
    
    return {
      isScheduleRequest,
      confidence: foundKeywords.length > 0 ? Math.min(foundKeywords.length * 0.3 + 0.5, 1.0) : 0,
      keywords: foundKeywords,
      messageType: this.categorizeMessage(lowerContent, foundKeywords)
    };
  }

  /**
   * Categorize message type
   */
  categorizeMessage(content, keywords) {
    if (keywords.includes('cancel')) return 'cancellation';
    if (keywords.includes('emergency')) return 'urgent_change';
    if (keywords.includes('reschedule') || keywords.includes('move')) return 'reschedule';
    return 'general_inquiry';
  }

  /**
   * Calculate urgency
   */
  calculateUrgency(content) {
    const urgentWords = ['emergency', 'urgent', 'asap', 'immediately', 'sick', 'cancel'];
    const hasUrgent = urgentWords.some(word => content.toLowerCase().includes(word));
    
    return hasUrgent ? 'high' : 'medium';
  }

  /**
   * Main monitoring function
   */
  async checkForScheduleRequests() {
    console.log('[GoogleVoiceMonitor] Starting Google Voice monitoring...');
    
    const results = {
      timestamp: new Date().toISOString(),
      emailResults: [],
      webResults: [],
      totalRequests: 0
    };
    
    try {
      // Monitor via email (primary method)
      results.emailResults = await this.monitorViaEmail();
      
      // Monitor via web interface (future enhancement)
      results.webResults = await this.monitorViaWebInterface();
      
      results.totalRequests = results.emailResults.length + results.webResults.length;
      
      if (results.totalRequests > 0) {
        console.log(`[GoogleVoiceMonitor] Found ${results.totalRequests} potential schedule requests`);
      }
      
      return results;
      
    } catch (error) {
      console.error('[GoogleVoiceMonitor] Monitoring error:', error.message);
      return results;
    }
  }
}

module.exports = { GoogleVoiceMonitor };
