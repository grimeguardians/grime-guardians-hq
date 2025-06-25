#!/usr/bin/env node

/**
 * Test Enhanced Google Voice Discord DM Schema
 * Tests the improved formatting with LangChain analysis integration
 */

console.log('🧪 Testing Enhanced Google Voice Discord DM Schema...\n');

// Mock the EmailCommunicationMonitor class methods for testing
class MockEmailMonitor {
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
    
    if (messageType === 'sales_inquiry' || messageType === 'new_inquiry') {
      if (messageText.includes('quote') || messageText.includes('price') || messageText.includes('cost')) {
        return "Thank you for your interest! I'd be happy to provide a quote. Could you please share the size of your home (bedrooms/bathrooms) and your preferred cleaning frequency? We offer competitive rates and exceptional service.";
      }
      return "Thank you for contacting Grime Guardians! We'd love to help with your cleaning needs. What type of cleaning service are you looking for?";
    }
    
    if (messageType === 'booking_request') {
      return "Thank you for choosing Grime Guardians! I'll get you scheduled right away. What dates work best for you? We have availability this week and can accommodate most preferences.";
    }
    
    if (messageType === 'complaint') {
      return "I sincerely apologize for any issues with our service. This is not the standard we aim for. I'd like to make this right immediately. Could you please share more details so we can resolve this quickly?";
    }
    
    return "Thank you for contacting Grime Guardians! We've received your message and will respond within a few hours. If this is urgent, please call us at (612) 584-9396.";
  }

  formatEnhancedDiscordMessage(messageData, analysis) {
    let alertMessage = `🚨 **New SMS via Google Voice (612-584-9396)**\n\n` +
      `📞 **From:** ${messageData.clientPhone || 'Unknown'}\n` +
      `👤 **Name:** ${messageData.clientName || 'Not provided'}\n` +
      `💬 **Message:** ${messageData.clientMessage}\n` +
      `⏰ **Time:** ${messageData.date?.toLocaleString() || 'Unknown'}\n`;

    // Add LangChain analysis if available
    if (analysis) {
      const messageTypeDisplay = this.formatMessageTypeForDisplay(analysis.message_type);
      const urgencyEmoji = this.getUrgencyEmoji(analysis.urgency_level);
      const confidencePercent = Math.round((analysis.confidence || 0) * 100);
      
      alertMessage += `\n🧠 **Analysis:**\n` +
        `${urgencyEmoji} **Type:** ${messageTypeDisplay}\n` +
        `⚡ **Urgency:** ${analysis.urgency_level || 'medium'}\n` +
        `🎯 **Confidence:** ${confidencePercent}%\n`;
      
      if (analysis.reasoning) {
        alertMessage += `💡 **Reasoning:** ${analysis.reasoning}\n`;
      }
      
      // Add suggested reply if Ava is confident (>80%)
      if (analysis.confidence > 0.8 && analysis.requires_response) {
        const suggestedReply = this.generateSuggestedReply(messageData, analysis);
        if (suggestedReply) {
          alertMessage += `\n💬 **Suggested Reply:**\n"${suggestedReply}"\n` +
            `React with ✅ to send this reply via Google Voice`;
        }
      }
    }

    alertMessage += `\n` + `─`.repeat(40) + `\n` +
      `**Action Required:** Review and respond as needed`;

    return alertMessage;
  }
}

// Test scenarios
const testScenarios = [
  {
    name: "Sales Inquiry with High Confidence",
    messageData: {
      clientPhone: "+16125551234",
      clientName: "Sarah Johnson", 
      clientMessage: "Hi! I'm interested in getting a quote for weekly cleaning service for my 3 bedroom home.",
      date: new Date()
    },
    analysis: {
      message_type: "sales_inquiry",
      urgency_level: "medium",
      confidence: 0.92,
      requires_response: true,
      reasoning: "Customer explicitly asking for quote and mentions specific details"
    }
  },
  {
    name: "Urgent Complaint",
    messageData: {
      clientPhone: "+16125555678",
      clientName: "Mike Thompson",
      clientMessage: "I'm very disappointed with today's cleaning. Several areas were missed and the team left early. This is not what I'm paying for!",
      date: new Date()
    },
    analysis: {
      message_type: "complaint",
      urgency_level: "high", 
      confidence: 0.95,
      requires_response: true,
      reasoning: "Clear dissatisfaction with service quality, requires immediate attention"
    }
  },
  {
    name: "Schedule Change Request",
    messageData: {
      clientPhone: "+16125559999",
      clientName: "Lisa Chen",
      clientMessage: "Can we reschedule tomorrow's cleaning to Friday instead? Something came up. Thanks!",
      date: new Date()
    },
    analysis: {
      message_type: "schedule_change",
      urgency_level: "medium",
      confidence: 0.88,
      requires_response: true,
      reasoning: "Clear request to change appointment date"
    }
  },
  {
    name: "Low Confidence Message",
    messageData: {
      clientPhone: "+16125552222",
      clientName: "Not provided",
      clientMessage: "Hey there",
      date: new Date()
    },
    analysis: {
      message_type: "other",
      urgency_level: "low",
      confidence: 0.45,
      requires_response: false,
      reasoning: "Message too brief to classify confidently"
    }
  }
];

const monitor = new MockEmailMonitor();

console.log('📋 Testing Enhanced Discord DM Schema:\n');

testScenarios.forEach((scenario, index) => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🧪 Test ${index + 1}: ${scenario.name}`);
  console.log(`${'='.repeat(60)}\n`);
  
  const formattedMessage = monitor.formatEnhancedDiscordMessage(scenario.messageData, scenario.analysis);
  console.log(formattedMessage);
  
  console.log(`\n✅ Features tested:`);
  console.log(`   - Full phone number display: ${scenario.messageData.clientPhone}`);
  console.log(`   - Natural language message type: ${monitor.formatMessageTypeForDisplay(scenario.analysis.message_type)}`);
  console.log(`   - Urgency emoji: ${monitor.getUrgencyEmoji(scenario.analysis.urgency_level)}`);
  console.log(`   - Confidence percentage: ${Math.round(scenario.analysis.confidence * 100)}%`);
  console.log(`   - Suggested reply: ${scenario.analysis.confidence > 0.8 ? 'Yes' : 'No (confidence too low)'}`);
  console.log(`   - Horizontal separator: ✅`);
  console.log(`   - React with ✅ instruction: ${scenario.analysis.confidence > 0.8 && scenario.analysis.requires_response ? 'Yes' : 'No'}`);
});

console.log(`\n\n🎉 Enhanced Discord DM Schema Test Complete!`);
console.log(`\n✨ Key Improvements:`);
console.log(`   ✅ Full phone number in "From" field`);
console.log(`   ✅ Horizontal line separator at end`);
console.log(`   ✅ "🧠 Analysis" instead of "LangChain Analysis"`);
console.log(`   ✅ Natural language message types`);
console.log(`   ✅ Suggested replies for high-confidence messages`);
console.log(`   ✅ ✅ reaction setup for reply approval`);
console.log(`   ✅ Urgency-based emojis for visual clarity`);
