#!/usr/bin/env node

/**
 * High Level Account Capabilities Investigation
 * Deep dive into what's actually available for your account
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function investigateHighLevelCapabilities() {
  console.log('🔍 High Level Account Capabilities Investigation');
  console.log('==============================================\n');
  
  const oauth = new HighLevelOAuth();
  
  // Test with both OAuth and API key
  const tests = [
    {
      name: 'OAuth Token Access',
      method: 'oauth',
      tests: [
        'https://services.leadconnectorhq.com/locations/me',
        'https://services.leadconnectorhq.com/users/me', 
        'https://services.leadconnectorhq.com/oauth/scopes',
        `https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}`,
        `https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}/conversations`,
        'https://services.leadconnectorhq.com/conversations/',
        'https://services.leadconnectorhq.com/conversations/search',
        'https://services.leadconnectorhq.com/messaging/conversations'
      ]
    },
    {
      name: 'API Key Access',
      method: 'apikey',
      tests: [
        `https://rest.gohighlevel.com/v1/contacts/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`,
        `https://rest.gohighlevel.com/v1/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`,
        `https://rest.gohighlevel.com/v1/conversations/search?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
        `https://rest.gohighlevel.com/v1/conversations/messages/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`,
        `https://rest.gohighlevel.com/v1/messaging/conversations?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
        `https://rest.gohighlevel.com/v1/locations/${process.env.HIGHLEVEL_LOCATION_ID}/conversations`
      ]
    }
  ];

  for (const testGroup of tests) {
    console.log(`\n📋 ${testGroup.name}`);
    console.log('='.repeat(testGroup.name.length + 4));
    
    for (const url of testGroup.tests) {
      try {
        let response;
        
        if (testGroup.method === 'oauth') {
          response = await oauth.makeAuthenticatedRequest(url);
        } else {
          const fetch = require('node-fetch');
          response = await fetch(url, {
            headers: {
              'Authorization': `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
              'Content-Type': 'application/json'
            }
          });
        }
        
        const endpoint = url.split('/').slice(-2).join('/');
        
        if (response.ok) {
          const data = await response.json();
          console.log(`✅ ${endpoint}: SUCCESS (${response.status})`);
          
          // Show relevant data structure
          if (data.conversations) {
            console.log(`   📋 Found ${data.conversations.length} conversations`);
          } else if (data.scopes) {
            console.log(`   🔑 Scopes: ${data.scopes.join(', ')}`);
          } else if (data.email) {
            console.log(`   👤 User: ${data.email}`);
          } else if (data.name) {
            console.log(`   🏢 Location: ${data.name}`);
          } else if (Array.isArray(data)) {
            console.log(`   📊 Array length: ${data.length}`);
          }
          
        } else {
          const errorText = await response.text();
          console.log(`❌ ${endpoint}: FAILED (${response.status})`);
          
          // Show specific error insights
          if (response.status === 404) {
            console.log(`   💡 Endpoint not available`);
          } else if (response.status === 401) {
            console.log(`   🔒 Unauthorized - need different scopes/permissions`);
          } else if (response.status === 403) {
            console.log(`   🚫 Forbidden - account tier limitation`);
          }
        }
        
      } catch (error) {
        const endpoint = url.split('/').slice(-2).join('/');
        console.log(`💥 ${endpoint}: ERROR - ${error.message}`);
      }
    }
  }
  
  console.log('\n📊 Investigation Summary');
  console.log('========================');
  console.log('Look for ✅ SUCCESS endpoints above.');
  console.log('Pay special attention to conversation-related endpoints.');
  console.log('\n💡 Next Steps:');
  console.log('1. If no conversation endpoints work → Contact High Level support');
  console.log('2. If some work with API key → Use hybrid approach');
  console.log('3. If OAuth scopes are limited → Request expanded permissions');
}

// Run the investigation
investigateHighLevelCapabilities().catch(error => {
  console.error('💥 Investigation failed:', error.message);
  process.exit(1);
});
