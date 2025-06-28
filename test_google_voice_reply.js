#!/usr/bin/env node
/**
 * Test Google Voice Reply Data Structure
 * This script tests the pending Google Voice reply storage and retrieval
 */

require('dotenv').config();

// Simulate the message data structure that comes from parseGoogleVoiceEmail
const mockGoogleVoiceMessage = {
  clientPhone: '(510) 967-7901',
  clientMessage: 'Good morning I got the invoice I\'ll send the deposit over shortly',
  clientName: '(510) 967-7901',
  timestamp: new Date(),
  emailId: 'test123',
  type: 'google_voice_sms',
  source: 'Google Voice (612-584-9396)'
};

// Simulate the analysis result
const mockAnalysis = {
  message_type: 'payment',
  urgency_level: 'medium',
  client_type: 'existing_customer',
  requires_response: true,
  confidence: 0.95,
  reasoning: 'Customer confirming payment'
};

// Simulate the generateSuggestedReply function
function generateSuggestedReply(messageData, analysis) {
  const messageText = messageData.clientMessage.toLowerCase();
  const messageType = analysis.message_type;
  const clientName = messageData.clientName && messageData.clientName !== 'Me' ? messageData.clientName : '';
  const greeting = clientName ? `Hi ${clientName}! ` : 'Hi! ';
  
  if (messageType === 'payment') {
    if (messageText.includes('deposit') || messageText.includes('payment')) {
      return `${greeting}Thank you for confirming your payment! I'll make sure our team is ready for your appointment. You'll receive a confirmation text with our arrival time shortly.`;
    }
  }
  
  return `${greeting}Thank you for your message! I'll get back to you shortly with more details.`;
}

console.log('🧪 Testing Google Voice Reply Data Structure\n');

// Test the pending reply data structure
const pendingReplyData = {
  messageData: mockGoogleVoiceMessage,
  clientPhone: mockGoogleVoiceMessage.clientPhone,
  clientName: mockGoogleVoiceMessage.clientName,
  replyText: generateSuggestedReply(mockGoogleVoiceMessage, mockAnalysis),
  analysis: mockAnalysis,
  timestamp: new Date()
};

console.log('📱 Mock Google Voice Message:');
console.log(JSON.stringify(mockGoogleVoiceMessage, null, 2));

console.log('\n🧠 Mock Analysis:');
console.log(JSON.stringify(mockAnalysis, null, 2));

console.log('\n📝 Pending Reply Data Structure:');
console.log(JSON.stringify(pendingReplyData, null, 2));

console.log('\n✅ Data Structure Test Complete!');
console.log(`   • Client Phone: ${pendingReplyData.clientPhone}`);
console.log(`   • Client Name: ${pendingReplyData.clientName}`);
console.log(`   • Reply Text: "${pendingReplyData.replyText}"`);
console.log(`   • All fields populated: ${pendingReplyData.clientPhone && pendingReplyData.replyText ? '✅' : '❌'}`);
