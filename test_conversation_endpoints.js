#!/usr/bin/env node

/**
 * High Level Conversations API Deep Dive
 * Test different conversation endpoint structures
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function testConversationEndpoints() {
  console.log('🔍 High Level Conversations API Deep Dive');
  console.log('===========================================\n');
  
  const oauth = new HighLevelOAuth();
  
  if (!oauth.isConfigured()) {
    console.log('❌ OAuth not configured.');
    return;
  }
  
  console.log('📍 Location ID:', process.env.HIGHLEVEL_LOCATION_ID);
  console.log('🔑 Testing with new OAuth token...\n');
  
  // Test various conversation endpoint patterns
  const endpoints = [
    // Standard v2 conversations endpoints
    {
      name: 'Conversations v2 - Standard',
      url: 'https://services.leadconnectorhq.com/conversations/',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 5 }
    },
    {
      name: 'Conversations v2 - Messages',
      url: 'https://services.leadconnectorhq.com/conversations/messages',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 5 }
    },
    // Location-specific endpoints
    {
      name: 'Location Conversations',
      url: `https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}/conversations`,
      params: { limit: 5 }
    },
    {
      name: 'Location Messages',
      url: `https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}/messages`,
      params: { limit: 5 }
    },
    // Alternative API paths
    {
      name: 'Messages v2 Direct',
      url: 'https://services.leadconnectorhq.com/messages/',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 5 }
    },
    {
      name: 'Conversations Search',
      url: 'https://services.leadconnectorhq.com/conversations/search',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 5 }
    },
    // Contact-based conversation access
    {
      name: 'Contact Conversations',
      url: 'https://services.leadconnectorhq.com/contacts/conversations',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 5 }
    }
  ];
  
  let workingEndpoints = [];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`🧪 Testing: ${endpoint.name}`);
      
      const url = new URL(endpoint.url);
      Object.keys(endpoint.params).forEach(key => {
        if (endpoint.params[key]) {
          url.searchParams.append(key, endpoint.params[key]);
        }
      });
      
      const response = await oauth.makeAuthenticatedRequest(url.toString());
      
      if (response.ok) {
        const data = await response.json();
        console.log(`   ✅ SUCCESS (${response.status})`);
        
        // Analyze the response structure
        if (data.conversations && data.conversations.length > 0) {
          console.log(`   📋 Found ${data.conversations.length} conversations`);
          const sample = data.conversations[0];
          console.log(`   📝 Sample: ${sample.id || 'no-id'}`);
          console.log(`   📞 Contact: ${sample.contactId || 'no-contact'}`);
          workingEndpoints.push({...endpoint, data: data.conversations});
        } else if (data.messages && data.messages.length > 0) {
          console.log(`   📋 Found ${data.messages.length} messages`);
          workingEndpoints.push({...endpoint, data: data.messages});
        } else if (Array.isArray(data) && data.length > 0) {
          console.log(`   📋 Found ${data.length} items`);
          workingEndpoints.push({...endpoint, data});
        } else {
          console.log(`   📝 Response: ${JSON.stringify(data).substring(0, 100)}...`);
          if (Object.keys(data).length > 0) {
            workingEndpoints.push({...endpoint, data});
          }
        }
        
      } else {
        const errorText = await response.text();
        console.log(`   ❌ FAILED (${response.status}): ${errorText.substring(0, 100)}...`);
      }
      
    } catch (error) {
      console.log(`   💥 ERROR: ${error.message}`);
    }
    
    console.log(''); // Empty line for readability
  }
  
  if (workingEndpoints.length > 0) {
    console.log('🎉 FOUND WORKING CONVERSATION ENDPOINTS!');
    console.log('==========================================');
    
    workingEndpoints.forEach(endpoint => {
      console.log(`✅ ${endpoint.name}`);
      console.log(`   URL: ${endpoint.url}`);
      if (endpoint.data && endpoint.data.length > 0) {
        const sample = endpoint.data[0];
        console.log(`   Sample Data: ${JSON.stringify(sample).substring(0, 150)}...`);
      }
      console.log('');
    });
    
    console.log('🚀 SUCCESS! Your agents can now monitor High Level conversations!');
    
  } else {
    console.log('❌ No working conversation endpoints found.');
    console.log('💡 High Level might require webhooks for conversation access.');
  }
}

// Run the deep dive
testConversationEndpoints().catch(error => {
  console.error('💥 Conversation endpoint test failed:', error.message);
  process.exit(1);
});
