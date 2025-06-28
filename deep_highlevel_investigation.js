#!/usr/bin/env node

/**
 * Deep High Level Configuration Investigation
 * Let's figure out exactly what's blocking conversations access
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function deepInvestigation() {
  console.log('🔍 DEEP HIGH LEVEL INVESTIGATION');
  console.log('=================================\n');
  
  const oauth = new HighLevelOAuth();
  
  // Step 1: Check all environment variables
  console.log('1️⃣ Environment Configuration Check:');
  console.log('===================================');
  console.log(`HIGHLEVEL_LOCATION_ID: ${process.env.HIGHLEVEL_LOCATION_ID || 'MISSING'}`);
  console.log(`HIGHLEVEL_API_KEY: ${process.env.HIGHLEVEL_API_KEY ? 'Present (' + process.env.HIGHLEVEL_API_KEY.substring(0, 20) + '...)' : 'MISSING'}`);
  console.log(`HIGHLEVEL_OAUTH_CLIENT_ID: ${process.env.HIGHLEVEL_OAUTH_CLIENT_ID || 'MISSING'}`);
  console.log(`HIGHLEVEL_OAUTH_ACCESS_TOKEN: ${process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN ? 'Present (' + process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN.substring(0, 20) + '...)' : 'MISSING'}`);
  console.log(`HIGHLEVEL_OAUTH_REFRESH_TOKEN: ${process.env.HIGHLEVEL_OAUTH_REFRESH_TOKEN ? 'Present' : 'MISSING'}`);
  console.log('');
  
  // Step 2: Test multiple conversation endpoints with different approaches
  console.log('2️⃣ Testing ALL Possible Conversation Endpoints:');
  console.log('==============================================');
  
  const fetch = require('node-fetch');
  
  const endpoints = [
    // v2 API endpoints
    {
      name: 'v2 Conversations (locationId param)',
      url: `https://services.leadconnectorhq.com/conversations?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'oauth'
    },
    {
      name: 'v2 Conversations (no params)',
      url: 'https://services.leadconnectorhq.com/conversations',
      auth: 'oauth'
    },
    {
      name: 'v2 Messages by location',
      url: `https://services.leadconnectorhq.com/conversations/messages?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'oauth'
    },
    // v1 API endpoints with OAuth
    {
      name: 'v1 Conversations (OAuth)',
      url: `https://rest.gohighlevel.com/v1/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'oauth'
    },
    {
      name: 'v1 Messages (OAuth)',
      url: `https://rest.gohighlevel.com/v1/conversations/messages/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'oauth'
    },
    // v1 API endpoints with API key
    {
      name: 'v1 Conversations (API Key)',
      url: `https://rest.gohighlevel.com/v1/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'apikey'
    },
    {
      name: 'v1 Messages (API Key)',
      url: `https://rest.gohighlevel.com/v1/conversations/messages/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'apikey'
    },
    // Alternative endpoints
    {
      name: 'SMS endpoint (v1)',
      url: `https://rest.gohighlevel.com/v1/sms/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'apikey'
    },
    {
      name: 'Activities endpoint',
      url: `https://rest.gohighlevel.com/v1/contacts/activities/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      auth: 'apikey'
    }
  ];
  
  let workingEndpoints = [];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`🧪 Testing: ${endpoint.name}`);
      
      let response;
      
      if (endpoint.auth === 'oauth') {
        response = await oauth.makeAuthenticatedRequest(endpoint.url);
      } else {
        response = await fetch(endpoint.url, {
          headers: {
            'Authorization': `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      console.log(`   Status: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`   ✅ SUCCESS! Response type: ${typeof data}`);
        
        if (Array.isArray(data)) {
          console.log(`   📋 Array with ${data.length} items`);
        } else if (data.conversations) {
          console.log(`   💬 Found ${data.conversations.length} conversations`);
        } else if (data.messages) {
          console.log(`   📨 Found ${data.messages.length} messages`);
        } else if (data.activities) {
          console.log(`   📊 Found ${data.activities.length} activities`);
        } else {
          console.log(`   📝 Keys: ${Object.keys(data).join(', ')}`);
        }
        
        workingEndpoints.push({...endpoint, data});
        
      } else {
        const errorText = await response.text();
        const shortError = errorText.substring(0, 150);
        console.log(`   ❌ FAILED: ${shortError}${errorText.length > 150 ? '...' : ''}`);
      }
      
    } catch (error) {
      console.log(`   💥 ERROR: ${error.message}`);
    }
    
    console.log(''); // Space for readability
  }
  
  // Step 3: OAuth scope investigation
  console.log('3️⃣ OAuth Scope Analysis:');
  console.log('========================');
  
  if (process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN) {
    try {
      // Decode the JWT token to see the scopes
      const token = process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN;
      const base64Payload = token.split('.')[1];
      const payload = JSON.parse(Buffer.from(base64Payload, 'base64').toString());
      
      console.log('Token payload:');
      console.log(`   Issued for: ${payload.aud || 'unknown'}`);
      console.log(`   Location ID: ${payload.locationId || payload.location_id || 'not found'}`);
      console.log(`   Scopes: ${payload.scope || payload.scopes || 'not found'}`);
      console.log(`   Expires: ${new Date(payload.exp * 1000).toISOString()}`);
      
    } catch (error) {
      console.log(`   ❌ Could not decode token: ${error.message}`);
    }
  } else {
    console.log('   ⚠️ No OAuth access token found');
  }
  
  console.log('');
  
  // Step 4: Results summary
  console.log('4️⃣ INVESTIGATION RESULTS:');
  console.log('=========================');
  
  if (workingEndpoints.length > 0) {
    console.log('✅ WORKING ENDPOINTS FOUND:');
    workingEndpoints.forEach(endpoint => {
      console.log(`   🎯 ${endpoint.name} (${endpoint.auth})`);
    });
    
    console.log('\n💡 RECOMMENDATION:');
    console.log('   Use the working endpoints above for conversation monitoring!');
    
  } else {
    console.log('❌ NO WORKING CONVERSATION ENDPOINTS');
    console.log('\n🔧 TROUBLESHOOTING STEPS:');
    console.log('   1. Check if your High Level plan includes API access');
    console.log('   2. Verify location ID is correct');
    console.log('   3. Request higher API permissions from High Level');
    console.log('   4. Consider webhook-based monitoring as alternative');
  }
  
  console.log('\n🎯 Investigation complete!');
}

// Run the investigation
deepInvestigation().catch(error => {
  console.error('💥 Investigation failed:', error.message);
  process.exit(1);
});
