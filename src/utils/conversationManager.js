/**
 * Conversation Manager - Maintains context and threading for all client communications
 * 
 * Features:
 * - Thread continuity across messages
 * - Context-aware response generation
 * - Operations vs Sales classification
 * - Natural language learning from feedback
 * - Client relationship memory
 */

const MessageClassifier = require('./messageClassifier');

class ConversationManager {
  constructor(discordClient) {
    this.discordClient = discordClient;
    this.conversations = new Map(); // phoneNumber -> conversationData
    this.clientProfiles = new Map(); // phoneNumber -> clientProfile
    this.messageClassifier = new MessageClassifier();
    
    console.log('🧠 Conversation Manager initialized');
    console.log('📝 Features: Threading, Context Awareness, Ops/Sales Classification');
  }

  /**
   * Process new message with full context awareness
   */
  async processMessage(messageData) {
    const phoneNumber = this.extractPhoneNumber(messageData);
    const conversation = this.getOrCreateConversation(phoneNumber);
    
    // Add message to conversation thread
    conversation.messages.push({
      timestamp: new Date(),
      content: messageData.clientMessage,
      source: messageData.source,
      type: 'incoming'
    });

    // Classify message with conversation context
    const classification = await this.classifyWithContext(messageData, conversation);
    
    console.log(`🧠 Ava Classification: ${classification.type} (${classification.confidence}% confidence)`);
    console.log(`📞 Phone: ${phoneNumber}, Thread length: ${conversation.messages.length}`);

    // 🚫 AVA (COO) OPERATIONS-ONLY SCOPE:
    // All sales/pricing inquiries are ignored - Dean (CMO) handles those
    const salesTypes = ['sales', 'pricing', 'new_prospect', 'pricing_inquiry', 'quote_request'];
    
    if (salesTypes.includes(classification.type)) {
      console.log(`🚫 SALES INQUIRY DETECTED - Ava ignoring (Dean will handle)`);
      console.log(`📋 Message: "${messageData.clientMessage.substring(0, 50)}..."`);
      
      return {
        action: 'ignore_sales_inquiry',
        reason: 'Sales inquiries handled by Dean (CMO) system',
        classification,
        messageData
      };
    }

    // Route operational inquiries only
    if (classification.type === 'operations' || 
        classification.type === 'scheduling_inquiry' ||
        classification.type === 'reschedule_request' ||
        classification.type === 'complaint') {
      return await this.handleOperationalInquiry(messageData, conversation, classification);
    } else {
      // Non-operational messages also ignored (Dean's territory)
      console.log(`🚫 NON-OPERATIONAL MESSAGE - Ava ignoring (Dean's territory)`);
      return {
        action: 'ignore_non_operational',
        reason: 'Only operational inquiries handled by Ava',
        classification,
        messageData
      };
    }
  }

  /**
   * Get or create conversation thread for phone number
   */
  getOrCreateConversation(phoneNumber) {
    if (!this.conversations.has(phoneNumber)) {
      this.conversations.set(phoneNumber, {
        phoneNumber,
        messages: [],
        context: {},
        clientType: 'unknown', // 'new_prospect', 'booked_client', 'recurring_client'
        lastInteraction: new Date(),
        awaitingResponse: null, // What we're waiting for from client
        handoffStatus: null, // 'pending_cmo', 'with_cmo', 'operations'
        clientProfile: this.getClientProfile(phoneNumber)
      });
    }
    
    const conversation = this.conversations.get(phoneNumber);
    conversation.lastInteraction = new Date();
    return conversation;
  }

  /**
   * Enhanced classification with conversation context
   */
  async classifyWithContext(messageData, conversation) {
    const contextPrompt = this.buildContextPrompt(messageData, conversation);
    
    // Use existing classifier but with enhanced context
    const classification = await this.messageClassifier.classifyMessage(
      messageData.clientMessage,
      contextPrompt
    );

    // Override classification based on conversation state
    if (conversation.awaitingResponse) {
      classification.context = `Responding to: ${conversation.awaitingResponse}`;
    }

    return classification;
  }

  /**
   * Build context prompt for better classification
   */
  buildContextPrompt(messageData, conversation) {
    let context = `
Conversation Context:
- Phone: ${conversation.phoneNumber}
- Client Type: ${conversation.clientType}
- Thread Length: ${conversation.messages.length}
- Last 3 messages: ${conversation.messages.slice(-3).map(m => `${m.type}: ${m.content}`).join(' | ')}
`;

    if (conversation.awaitingResponse) {
      context += `- Awaiting Response To: ${conversation.awaitingResponse}\n`;
    }

    if (conversation.clientProfile.isRecurring) {
      context += `- Recurring Client: ${conversation.clientProfile.frequency}\n`;
      context += `- Preferences: ${conversation.clientProfile.preferences.join(', ')}\n`;
    }

    return context;
  }

  /**
   * Handle sales handoff to CMO suite
   */
  async handleSalesHandoff(messageData, conversation, classification) {
    conversation.handoffStatus = 'pending_cmo';
    
    // Send transitional message if first sales inquiry
    const shouldSendTransition = conversation.messages.length <= 1 || 
      !conversation.messages.some(m => m.type === 'outgoing');

    let transitionMessage = null;
    if (shouldSendTransition) {
      transitionMessage = this.generateTransitionMessage(classification);
      
      // Add to conversation thread
      conversation.messages.push({
        timestamp: new Date(),
        content: transitionMessage,
        source: 'ava',
        type: 'outgoing',
        classification: 'sales_handoff'
      });
    }

    // Create CMO handoff notification
    const handoffData = {
      messageData,
      conversation,
      classification,
      transitionMessage,
      action: 'cmo_handoff'
    };

    console.log(`🔄 Handing off ${classification.type} inquiry to CMO suite`);
    console.log(`📱 Phone: ${conversation.phoneNumber}, Context: ${classification.context || 'Initial inquiry'}`);

    return handoffData;
  }

  /**
   * Handle operational inquiries with Ava
   */
  async handleOperationalInquiry(messageData, conversation, classification) {
    conversation.handoffStatus = 'operations';

    // Generate contextual operational response
    const response = await this.generateOperationalResponse(messageData, conversation, classification);
    
    // Add to conversation thread
    conversation.messages.push({
      timestamp: new Date(),
      content: response.text,
      source: 'ava',
      type: 'outgoing',
      classification: 'operational',
      confidence: response.confidence
    });

    // Set awaiting response if we asked a question
    if (response.awaitingResponse) {
      conversation.awaitingResponse = response.awaitingResponse;
    }

    const responseData = {
      messageData,
      conversation,
      classification,
      response,
      action: 'operational_response',
      requiresApproval: true // EMERGENCY: All responses require approval
    };

    console.log(`⚙️ Operational response generated (${response.confidence}% confidence)`);
    if (response.confidence < 80) {
      console.log(`❓ Low confidence - requesting approval`);
    }

    return responseData;
  }

  /**
   * Handle uncertain messages - request guidance
   */
  async handleUncertainMessage(messageData, conversation, classification) {
    const guidanceRequest = {
      messageData,
      conversation,
      classification,
      action: 'request_guidance',
      question: `I'm not sure how to classify this message. Should I handle it as operations or route to CMO?`
    };

    console.log(`❓ Uncertain classification - requesting guidance`);
    return guidanceRequest;
  }

  /**
   * Generate transition message for sales handoff
   */
  generateTransitionMessage(classification) {
    const transitions = [
      "Great! Let me connect you with our pricing specialist who can provide detailed quotes.",
      "Perfect! I'll have our sales team reach out with pricing and availability.",
      "Excellent! Our pricing expert will get back to you shortly with a custom quote.",
      "Thanks for your interest! Let me connect you with someone who can discuss pricing details."
    ];

    return transitions[Math.floor(Math.random() * transitions.length)];
  }

  /**
   * Generate operational response with context
   */
  async generateOperationalResponse(messageData, conversation, classification) {
    // Map classification types to handlers
    const classType = classification.type;
    
    console.log(`🎯 Generating response for type: ${classType}`);
    
    if (classType === 'reschedule_request' || classType === 'scheduling') {
      return this.handleSchedulingInquiry(messageData, conversation, classification);
    } else if (classType === 'service_inquiry' || classType === 'service_status') {
      return this.handleServiceStatusInquiry(messageData, conversation, classification);
    } else if (classType === 'complaint') {
      return this.handleComplaintInquiry(messageData, conversation, classification);
    } else if (classType === 'operations') {
      return this.handleGeneralOperationsInquiry(messageData, conversation, classification);
    }

    // Default operational response
    console.log(`⚠️ Using default response for unhandled type: ${classType}`);
    return {
      text: "I'd be happy to help with your service needs. Could you provide more details about what you need assistance with?",
      confidence: 60,
      awaitingResponse: "service_details"
    };
  }

  /**
   * Handle scheduling inquiries (reschedule requests)
   */
  handleSchedulingInquiry(messageData, conversation, classification) {
    const message = messageData.content || messageData.text || '';
    
    // Check if this is a recurring client with existing schedule
    if (conversation.clientProfile && conversation.clientProfile.isRecurring) {
      return {
        text: `Hi ${conversation.clientProfile.name || 'there'}! I can help reschedule your ${conversation.clientProfile.frequency || 'regular'} cleaning. What day would work better for you?`,
        confidence: 85,
        awaitingResponse: "schedule_change_details"
      };
    }

    // Generic reschedule response
    return {
      text: "I can help you reschedule your cleaning appointment. What day and time would work better for you?",
      confidence: 80,
      awaitingResponse: "schedule_change_details"
    };
  }

  /**
   * Handle general operations inquiries
   */
  handleGeneralOperationsInquiry(messageData, conversation, classification) {
    const message = (messageData.content || messageData.text || '').toLowerCase();
    
    // Check for common operations patterns
    if (message.includes('time') || message.includes('when')) {
      return {
        text: "Let me check your appointment time. Could you provide your name or phone number so I can look up your booking?",
        confidence: 75,
        awaitingResponse: "customer_info"
      };
    }
    
    if (message.includes('add') || message.includes('extra') || message.includes('additional')) {
      return {
        text: "I'd be happy to help add services to your cleaning. What additional service would you like to include?",
        confidence: 80,
        awaitingResponse: "service_addition"
      };
    }
    
    if (message.includes('cancel')) {
      return {
        text: "I can help you with cancellation. Could you provide your appointment date so I can locate your booking?",
        confidence: 75,
        awaitingResponse: "cancellation_details"
      };
    }

    // General operational response
    return {
      text: "I'm here to help with your cleaning service needs. Are you looking to schedule, reschedule, add services, or have questions about an existing appointment?",
      confidence: 70,
      awaitingResponse: "service_intent"
    };
  }

  /**
   * Handle service status inquiries
   */
  handleServiceStatusInquiry(messageData, conversation, classification) {
    const message = (messageData.content || messageData.text || '').toLowerCase();
    
    if (message.includes('when') || message.includes('time')) {
      return {
        text: "I can check when your cleaning is scheduled. Could you provide your name or the phone number for your booking?",
        confidence: 80,
        awaitingResponse: "customer_lookup"
      };
    }
    
    if (message.includes('status') || message.includes('update')) {
      return {
        text: "I can provide an update on your service. What's your booking date or reference number?",
        confidence: 75,
        awaitingResponse: "service_reference"
      };
    }

    return {
      text: "I can help check on your service status. Could you provide your appointment date or booking reference so I can look this up for you?",
      confidence: 70,
      awaitingResponse: "service_reference"
    };
  }

  /**
   * Handle complaint inquiries
   */
  handleComplaintInquiry(messageData, conversation, classification) {
    const message = (messageData.content || messageData.text || '').toLowerCase();
    
    // Determine complaint urgency
    const urgentWords = ['terrible', 'awful', 'damaged', 'broken', 'refund', 'unacceptable'];
    const isUrgent = urgentWords.some(word => message.includes(word));
    
    if (isUrgent) {
      return {
        text: "I'm very sorry to hear about this issue. This needs immediate attention. I'm escalating this to management right away. Could you please provide details about what happened so we can address it promptly?",
        confidence: 90, // High confidence but still needs approval for complaints
        awaitingResponse: "urgent_complaint_details",
        escalate: true
      };
    }

    return {
      text: "I apologize for any concerns with your cleaning service. I'd like to make this right. Could you please describe what happened so I can address it appropriately?",
      confidence: 85,
      awaitingResponse: "complaint_details"
    };
  }

  /**
   * Extract phone number from message data
   */
  extractPhoneNumber(messageData) {
    // Extract from email subject, from field, or message content
    return messageData.clientPhone || 
           messageData.from || 
           'unknown_' + Date.now();
  }

  /**
   * Get or create client profile
   */
  getClientProfile(phoneNumber) {
    if (!this.clientProfiles.has(phoneNumber)) {
      this.clientProfiles.set(phoneNumber, {
        phoneNumber,
        name: null,
        isRecurring: false,
        frequency: null, // 'weekly', 'biweekly', 'monthly'
        preferences: [],
        pastIssues: [],
        lastService: null,
        totalServices: 0,
        notes: []
      });
    }
    return this.clientProfiles.get(phoneNumber);
  }

  /**
   * Learn from manual feedback/corrections
   */
  async learnFromFeedback(feedback, messageContext) {
    console.log(`📚 Learning from feedback: ${feedback}`);
    
    // Parse natural language feedback
    const learningData = {
      timestamp: new Date(),
      feedback,
      context: messageContext,
      phoneNumber: messageContext.phoneNumber
    };

    // Store for pattern recognition
    // This will be enhanced to train the classification model
    
    console.log(`✅ Feedback recorded for pattern learning`);
    return learningData;
  }

  /**
   * Update conversation after response is sent
   */
  updateConversationAfterResponse(phoneNumber, response, wasApproved = true) {
    const conversation = this.conversations.get(phoneNumber);
    if (conversation) {
      const lastMessage = conversation.messages[conversation.messages.length - 1];
      if (lastMessage && lastMessage.type === 'outgoing') {
        lastMessage.wasApproved = wasApproved;
        lastMessage.sentAt = new Date();
      }
    }
  }

  /**
   * Get conversation summary for debugging
   */
  getConversationSummary(phoneNumber) {
    const conversation = this.conversations.get(phoneNumber);
    if (!conversation) return null;

    return {
      phoneNumber,
      messageCount: conversation.messages.length,
      clientType: conversation.clientType,
      handoffStatus: conversation.handoffStatus,
      awaitingResponse: conversation.awaitingResponse,
      lastInteraction: conversation.lastInteraction,
      recentMessages: conversation.messages.slice(-3)
    };
  }
}

module.exports = ConversationManager;
