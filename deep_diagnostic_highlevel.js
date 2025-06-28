#!/usr/bin/env node

/**
 * High Level API Diagnostic - Deep Investigation
 * Let's determine EXACTLY what's blocking conversations access
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function deepDiagnostic() {
  console.log('🔍 HIGH LEVEL API DEEP DIAGNOSTIC');
  console.log('==================================\n');
  
  const oauth = new HighLevelOAuth();
  
  // 1. Check OAuth token structure
  console.log('1️⃣ OAuth Token Analysis:');
  console.log('  Access Token Present:', !!process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN);
  console.log('  Refresh Token Present:', !!process.env.HIGHLEVEL_OAUTH_REFRESH_TOKEN);
  console.log('  Location ID:', process.env.HIGHLEVEL_LOCATION_ID);
  console.log('  Client ID:', process.env.HIGHLEVEL_OAUTH_CLIENT_ID);
  
  if (process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN) {
    // Decode JWT token to see scopes (if it's a JWT)
    const token = process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN;
    console.log('  Token Length:', token.length);
    console.log('  Token Prefix:', token.substring(0, 20) + '...');
    
    // Try to decode if it's a JWT
    if (token.includes('.')) {
      try {
        const parts = token.split('.');
        const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
        console.log('  Token Scopes:', payload.scope || 'No scopes in token');
        console.log('  Token Expires:', new Date(payload.exp * 1000).toISOString());
        console.log('  Token Subject:', payload.sub || 'No subject');
      } catch (e) {
        console.log('  Token Type: Opaque (not JWT)');
      }
    }
  }
  
  console.log('\n2️⃣ Testing All Possible Endpoints:');
  
  // Test different endpoint variations
  const endpointTests = [
    {
      name: 'Conversations v2 (Standard)',
      url: `https://services.leadconnectorhq.com/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      headers: { 'Version': '2021-07-28' }
    },
    {
      name: 'Conversations v2 (No Version Header)',
      url: `https://services.leadconnectorhq.com/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      headers: {}
    },
    {
      name: 'Conversations v2 (Different Path)',
      url: `https://services.leadconnectorhq.com/conversations/search?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      headers: { 'Version': '2021-07-28' }
    },
    {
      name: 'Messages v2 (Direct)',
      url: `https://services.leadconnectorhq.com/conversations/messages?locationId=${process.env.HIGHLEVEL_LOCATION_ID}`,
      headers: { 'Version': '2021-07-28' }
    },
    {
      name: 'Locations Endpoint',
      url: `https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}`,
      headers: { 'Version': '2021-07-28' }
    },
    {
      name: 'User Profile',
      url: 'https://services.leadconnectorhq.com/users/me',
      headers: { 'Version': '2021-07-28' }
    }
  ];
  
  for (const test of endpointTests) {
    try {
      console.log(`\n🧪 Testing: ${test.name}`);
      
      const response = await oauth.makeAuthenticatedRequest(test.url, {
        headers: test.headers
      });
      
      console.log(`   Status: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`   ✅ SUCCESS!`);
        
        if (data.conversations) {
          console.log(`   📋 Found ${data.conversations.length} conversations`);
        } else if (data.messages) {
          console.log(`   📋 Found ${data.messages.length} messages`);
        } else if (data.name || data.email) {
          console.log(`   👤 User data received`);
        } else if (data.id) {
          console.log(`   📝 Resource ID: ${data.id}`);
        }
        
        // Show first few keys of response
        console.log(`   🔑 Response keys: ${Object.keys(data).slice(0, 5).join(', ')}`);
        
      } else {
        const errorText = await response.text();
        console.log(`   ❌ FAILED: ${errorText.substring(0, 200)}`);
        
        // Parse error for specific issues
        if (response.status === 401) {
          console.log(`   🔍 Analysis: Authentication/Authorization issue`);
        } else if (response.status === 403) {
          console.log(`   🔍 Analysis: Forbidden - likely scope/permission issue`);
        } else if (response.status === 404) {
          console.log(`   🔍 Analysis: Endpoint not found - wrong URL or not available`);
        } else if (response.status === 429) {
          console.log(`   🔍 Analysis: Rate limited`);
        }
      }
      
    } catch (error) {
      console.log(`   💥 ERROR: ${error.message}`);
    }
  }
  
  console.log('\n3️⃣ Testing with API Key (Fallback):');
  
  // Test what works with API key
  const fetch = require('node-fetch');
  try {
    const apiKeyTest = await fetch(`https://rest.gohighlevel.com/v1/contacts/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`, {
      headers: {
        'Authorization': `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`   API Key Contacts: ${apiKeyTest.status} ${apiKeyTest.ok ? '✅' : '❌'}`);
    
    if (apiKeyTest.ok) {
      const data = await apiKeyTest.json();
      console.log(`   📋 API Key has access to ${data.contacts?.length || 0} contacts`);
    }
    
  } catch (error) {
    console.log(`   API Key Test Failed: ${error.message}`);
  }
  
  console.log('\n4️⃣ DIAGNOSIS:');
  
  // Provide analysis
  console.log('   Based on the tests above:');
  console.log('   - If OAuth endpoints all return 401/403: Scope issue');
  console.log('   - If OAuth endpoints return 404: Account tier/feature not available');
  console.log('   - If API key works but OAuth doesn\'t: OAuth configuration issue');
  console.log('   - If nothing works: Account/subscription limitation');
  
  console.log('\n🎯 RECOMMENDATION:');
  console.log('   1. Check any ✅ SUCCESS endpoints above');
  console.log('   2. Review error patterns for root cause');
  console.log('   3. Contact High Level support with specific error codes');
}

// Run the diagnostic
deepDiagnostic().catch(error => {
  console.error('💥 Diagnostic failed:', error.message);
  process.exit(1);
});
