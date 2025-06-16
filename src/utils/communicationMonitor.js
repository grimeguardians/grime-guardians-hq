/**
 * Communication Monitor - Tracks client communications across multiple channels
 * Monitors High Level conversations and Google Voice for schedule change requests
 */

const axios = require('axios');
require('dotenv').config();

class CommunicationMonitor {
  constructor() {
    this.highlevelApiKey = process.env.HIGHLEVEL_API_KEY;
    this.highlevelLocationId = process.env.HIGHLEVEL_LOCATION_ID;
    this.googleVoiceEnabled = process.env.GOOGLE_VOICE_ENABLED === 'true';
    
    // Schedule-related keywords to detect
    this.scheduleKeywords = [
      'reschedule', 'schedule', 'move', 'change', 'cancel', 'postpone',
      'different time', 'another day', 'another time', 'push back',
      'earlier', 'later', 'tomorrow', 'next week', 'different day',
      'can we change', 'need to move', 'something came up',
      'emergency', 'sick', 'travel', 'vacation', 'conflict'
    ];
    
    // Time-related patterns
    this.timePatterns = [
      /(\d{1,2}):(\d{2})\s*(am|pm)/gi,
      /(\d{1,2})\s*(am|pm)/gi,
      /(morning|afternoon|evening|night)/gi,
      /(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/gi,
      /(tomorrow|today|next week|this week)/gi
    ];
  }

  /**
   * Monitor High Level conversations for schedule changes
   */
  async monitorHighLevelConversations() {
    try {
      console.log('[CommunicationMonitor] Checking High Level conversations...');
      
      // Get recent conversations
      const conversations = await this.getRecentConversations();
      
      const scheduleRequests = [];
      
      for (const conversation of conversations) {
        const messages = await this.getConversationMessages(conversation.id);
        
        // Analyze recent messages for schedule keywords
        const recentMessages = messages.filter(msg => 
          this.isRecentMessage(msg.dateAdded) && 
          msg.direction === 'inbound' // Client messages only
        );
        
        for (const message of recentMessages) {
          const scheduleDetection = this.analyzeMessageForScheduleRequest(message);
          
          if (scheduleDetection.isScheduleRequest) {
            scheduleRequests.push({
              source: 'highlevel',
              conversationId: conversation.id,
              contactId: conversation.contactId,
              contactName: conversation.contact?.name || 'Unknown',
              contactPhone: conversation.contact?.phone || '',
              message: message.body,
              timestamp: message.dateAdded,
              detection: scheduleDetection,
              urgency: this.calculateUrgency(message.body, scheduleDetection)
            });
          }
        }
      }
      
      return scheduleRequests;
      
    } catch (error) {
      console.error('[CommunicationMonitor] Error monitoring High Level:', error.message);
      return [];
    }
  }

  /**
   * Get recent conversations from High Level
   */
  async getRecentConversations() {
    const response = await axios.get(
      `https://services.leadconnectorhq.com/conversations/`,
      {
        headers: {
          'Authorization': `Bearer ${this.highlevelApiKey}`,
          'Version': '2021-07-28'
        },
        params: {
          locationId: this.highlevelLocationId,
          limit: 50,
          startAfterDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // Last 24 hours
        }
      }
    );
    
    return response.data.conversations || [];
  }

  /**
   * Get messages from a specific conversation
   */
  async getConversationMessages(conversationId) {
    const response = await axios.get(
      `https://services.leadconnectorhq.com/conversations/${conversationId}/messages`,
      {
        headers: {
          'Authorization': `Bearer ${this.highlevelApiKey}`,
          'Version': '2021-07-28'
        },
        params: {
          limit: 20
        }
      }
    );
    
    return response.data.messages || [];
  }

  /**
   * Analyze message content for schedule change requests
   */
  analyzeMessageForScheduleRequest(message) {
    const content = message.body.toLowerCase();
    
    // Check for schedule keywords
    const foundKeywords = this.scheduleKeywords.filter(keyword => 
      content.includes(keyword)
    );
    
    // Check for time patterns
    const timeMatches = [];
    this.timePatterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches) timeMatches.push(...matches);
    });
    
    // Determine if this is a schedule request
    const isScheduleRequest = foundKeywords.length > 0;
    
    // Extract potential new date/time preferences
    const suggestedTimes = this.extractTimePreferences(content);
    
    return {
      isScheduleRequest,
      confidence: foundKeywords.length > 0 ? Math.min(foundKeywords.length * 0.3 + 0.4, 1.0) : 0,
      keywords: foundKeywords,
      timeMatches,
      suggestedTimes,
      messageType: this.categorizeScheduleRequest(content, foundKeywords)
    };
  }

  /**
   * Extract time preferences from message content
   */
  extractTimePreferences(content) {
    const preferences = [];
    
    // Look for specific times
    const timeRegex = /(\d{1,2}):?(\d{2})?\s*(am|pm|morning|afternoon|evening)/gi;
    let match;
    while ((match = timeRegex.exec(content)) !== null) {
      preferences.push({
        type: 'time',
        value: match[0],
        hour: match[1],
        minute: match[2] || '00',
        period: match[3]
      });
    }
    
    // Look for days
    const dayRegex = /(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today)/gi;
    while ((match = dayRegex.exec(content)) !== null) {
      preferences.push({
        type: 'day',
        value: match[0]
      });
    }
    
    return preferences;
  }

  /**
   * Categorize the type of schedule request
   */
  categorizeScheduleRequest(content, keywords) {
    if (keywords.includes('cancel')) return 'cancellation';
    if (keywords.includes('postpone') || keywords.includes('push back')) return 'postponement';
    if (keywords.includes('reschedule') || keywords.includes('move')) return 'reschedule';
    if (keywords.includes('change')) return 'change';
    if (keywords.includes('emergency') || keywords.includes('sick')) return 'urgent_change';
    return 'general_inquiry';
  }

  /**
   * Calculate urgency level
   */
  calculateUrgency(content, detection) {
    let urgency = 'low';
    
    const urgentKeywords = ['emergency', 'urgent', 'asap', 'immediately', 'sick', 'cancel'];
    const hasUrgentKeywords = urgentKeywords.some(keyword => 
      content.toLowerCase().includes(keyword)
    );
    
    if (hasUrgentKeywords) urgency = 'high';
    else if (detection.messageType === 'cancellation') urgency = 'medium';
    else if (detection.confidence > 0.7) urgency = 'medium';
    
    return urgency;
  }

  /**
   * Check if message is recent (within monitoring window)
   */
  isRecentMessage(timestamp) {
    const messageTime = new Date(timestamp);
    const now = new Date();
    const hoursDiff = (now - messageTime) / (1000 * 60 * 60);
    
    return hoursDiff <= 24; // Monitor last 24 hours
  }

  /**
   * Monitor Google Voice messages (placeholder for future implementation)
   */
  async monitorGoogleVoice() {
    if (!this.googleVoiceEnabled) {
      console.log('[CommunicationMonitor] Google Voice monitoring disabled');
      return [];
    }
    
    // TODO: Implement Google Voice API integration
    // This would require Google Voice API or web scraping approach
    console.log('[CommunicationMonitor] Google Voice monitoring not yet implemented');
    
    return [];
  }

  /**
   * Main monitoring function - checks all communication channels
   */
  async checkAllChannels() {
    console.log('[CommunicationMonitor] Starting comprehensive communication check...');
    
    const results = {
      timestamp: new Date().toISOString(),
      sources: {
        highlevel: [],
        googleVoice: []
      },
      totalScheduleRequests: 0,
      urgentRequests: 0
    };
    
    try {
      // Monitor High Level
      results.sources.highlevel = await this.monitorHighLevelConversations();
      
      // Monitor Google Voice (when implemented)
      results.sources.googleVoice = await this.monitorGoogleVoice();
      
      // Calculate totals
      const allRequests = [
        ...results.sources.highlevel,
        ...results.sources.googleVoice
      ];
      
      results.totalScheduleRequests = allRequests.length;
      results.urgentRequests = allRequests.filter(req => req.urgency === 'high').length;
      
      // Log summary
      if (results.totalScheduleRequests > 0) {
        console.log(`[CommunicationMonitor] Found ${results.totalScheduleRequests} schedule requests`);
        if (results.urgentRequests > 0) {
          console.log(`[CommunicationMonitor] ${results.urgentRequests} urgent requests require immediate attention`);
        }
      }
      
      return results;
      
    } catch (error) {
      console.error('[CommunicationMonitor] Error in comprehensive check:', error.message);
      return results;
    }
  }

  /**
   * Format schedule request for agent processing
   */
  formatForAgent(scheduleRequest) {
    return {
      agent_id: 'schedule_manager',
      event_type: 'schedule_request_detected',
      source: scheduleRequest.source,
      urgency: scheduleRequest.urgency,
      client: {
        name: scheduleRequest.contactName,
        phone: scheduleRequest.contactPhone,
        contactId: scheduleRequest.contactId
      },
      request: {
        message: scheduleRequest.message,
        type: scheduleRequest.detection.messageType,
        confidence: scheduleRequest.detection.confidence,
        keywords: scheduleRequest.detection.keywords,
        suggestedTimes: scheduleRequest.detection.suggestedTimes
      },
      timestamp: scheduleRequest.timestamp,
      action_required: scheduleRequest.urgency === 'high' ? 'immediate_response' : 'schedule_review'
    };
  }
}

module.exports = { CommunicationMonitor };
