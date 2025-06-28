#!/usr/bin/env node

/**
 * Webhook Testing Script
 * Test all communication webhook endpoints
 */

const fetch = require('node-fetch');

// Configuration
const BASE_URL = 'http://localhost:3000'; // Change to your production URL
const WEBHOOK_SECRET = 'Chidori25!@';

// Test data for different webhook types
const testData = {
  highlevel_sms: {
    type: 'SMS',
    direction: 'inbound',
    body: 'Hi, can we reschedule our cleaning for tomorrow instead?',
    contact: {
      name: 'Sarah Johnson',
      phone: '+16125559876',
      email: 'sarah@example.com'
    },
    contactId: 'test_contact_123',
    conversationId: 'conv_456',
    dateAdded: new Date().toISOString()
  },
  
  highlevel_email: {
    type: 'Email',
    direction: 'inbound',
    body: 'Hello, I need to cancel my cleaning appointment scheduled for Friday. Can you please confirm the cancellation?',
    subject: 'Cancellation Request',
    contact: {
      name: 'Mike Chen',
      phone: '+16125551234',
      email: 'mike.chen@example.com'
    },
    contactId: 'test_contact_456',
    conversationId: 'conv_789',
    dateAdded: new Date().toISOString()
  },
  
  facebook_messenger: {
    object: 'page',
    entry: [{
      id: '123456789',
      time: Date.now(),
      messaging: [{
        sender: { id: 'user123' },
        recipient: { id: 'page123' },
        timestamp: Date.now(),
        message: {
          mid: 'msg123',
          text: 'Hey! Can I get a quote for cleaning my 3-bedroom house?'
        }
      }]
    }]
  },
  
  instagram_dm: {
    object: 'instagram',
    entry: [{
      id: '987654321',
      time: Date.now(),
      messaging: [{
        sender: { id: 'user456', username: 'sarah_homeowner' },
        recipient: { id: 'page456' },
        timestamp: Date.now(),
        message: {
          mid: 'msg456',
          text: 'Do you offer emergency cleaning services?'
        }
      }]
    }]
  }
};

async function testWebhook(endpoint, data, headers = {}) {
  try {
    console.log(`\n🧪 Testing: ${endpoint}`);
    console.log(`📤 Sending: ${JSON.stringify(data, null, 2).substring(0, 200)}...`);
    
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-webhook-secret': WEBHOOK_SECRET,
        ...headers
      },
      body: JSON.stringify(data)
    });
    
    const responseText = await response.text();
    
    if (response.ok) {
      console.log(`✅ SUCCESS (${response.status}): ${responseText}`);
    } else {
      console.log(`❌ FAILED (${response.status}): ${responseText}`);
    }
    
  } catch (error) {
    console.log(`💥 ERROR: ${error.message}`);
  }
}

async function testAllWebhooks() {
  console.log('🎯 Communication Webhook Testing Suite');
  console.log('=====================================');
  console.log(`🌐 Base URL: ${BASE_URL}`);
  console.log(`🔐 Secret: ${WEBHOOK_SECRET}`);
  
  // Test High Level SMS
  await testWebhook('/webhook/highlevel/sms', testData.highlevel_sms);
  
  // Test High Level Email  
  await testWebhook('/webhook/highlevel/email', testData.highlevel_email);
  
  // Test Facebook Messenger
  await testWebhook('/webhook/facebook/messenger', testData.facebook_messenger);
  
  // Test Instagram DM
  await testWebhook('/webhook/instagram/dm', testData.instagram_dm);
  
  // Test health endpoint
  console.log(`\n🏥 Testing health endpoint...`);
  try {
    const response = await fetch(`${BASE_URL}/health`);
    const health = await response.json();
    console.log(`✅ Health check: ${health.status} (v${health.system_version})`);
    console.log(`📊 Active agents: ${health.agents_active}`);
  } catch (error) {
    console.log(`❌ Health check failed: ${error.message}`);
  }
  
  console.log('\n🎉 Webhook testing complete!');
  console.log('\n💡 Next steps:');
  console.log('   1. Configure webhooks in High Level/Facebook/Instagram');
  console.log('   2. Update BASE_URL to your production domain');
  console.log('   3. Test with real messages from your platforms');
}

// Run tests
testAllWebhooks().catch(error => {
  console.error('💥 Test suite failed:', error.message);
  process.exit(1);
});
