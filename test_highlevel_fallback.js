#!/usr/bin/env node

/**
 * High Level Fallback Integration Test
 * Test the original API key approach as a fallback
 */

require('dotenv').config();

async function testHighLevelFallback() {
  console.log('🔄 Testing High Level API Key Fallback');
  console.log('=======================================\n');
  
  const fetch = require('node-fetch');
  
  // Test endpoints that we know work with API key
  const endpoints = [
    {
      name: 'Contacts v1 (API Key)',
      url: `https://rest.gohighlevel.com/v1/contacts/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=3`,
      headers: {
        'Authorization': `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
        'Content-Type': 'application/json'
      }
    },
    {
      name: 'Conversations v1 (API Key)',
      url: `https://rest.gohighlevel.com/v1/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=3`,
      headers: {
        'Authorization': `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
        'Content-Type': 'application/json'
      }
    },
    {
      name: 'Messages v1 (API Key)',
      url: `https://rest.gohighlevel.com/v1/conversations/messages/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=3`,
      headers: {
        'Authorization': `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
        'Content-Type': 'application/json'
      }
    }
  ];
  
  let workingEndpoints = [];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`🧪 Testing: ${endpoint.name}`);
      
      const response = await fetch(endpoint.url, {
        method: 'GET',
        headers: endpoint.headers
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`   ✅ SUCCESS (${response.status})`);
        
        if (data.contacts && data.contacts.length > 0) {
          console.log(`   📋 Found ${data.contacts.length} contacts`);
          workingEndpoints.push({...endpoint, data: data.contacts});
        } else if (data.conversations && data.conversations.length > 0) {
          console.log(`   📋 Found ${data.conversations.length} conversations`);
          workingEndpoints.push({...endpoint, data: data.conversations});
        } else if (data.messages && data.messages.length > 0) {
          console.log(`   📋 Found ${data.messages.length} messages`);
          workingEndpoints.push({...endpoint, data: data.messages});
        } else if (Array.isArray(data) && data.length > 0) {
          console.log(`   📋 Found ${data.length} items`);
          workingEndpoints.push({...endpoint, data});
        } else {
          console.log(`   📝 Response: ${JSON.stringify(data).substring(0, 100)}...`);
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
    console.log('🎉 Found working API endpoints!');
    console.log('📋 Working endpoints:');
    
    workingEndpoints.forEach(endpoint => {
      console.log(`   ✅ ${endpoint.name}`);
      if (endpoint.data && endpoint.data.length > 0) {
        const sample = endpoint.data[0];
        console.log(`      Sample ID: ${sample.id || sample.contactId || 'unknown'}`);
        if (sample.phone) console.log(`      Sample Phone: ${sample.phone}`);
        if (sample.lastMessage) console.log(`      Has Messages: Yes`);
      }
    });
    
    console.log('\n💡 Recommendation: Use API key approach as primary integration');
    console.log('   OAuth can be added later when scopes are resolved.');
    
  } else {
    console.log('❌ No working endpoints found.');
    console.log('💡 Consider using webhooks for real-time notifications instead.');
  }
}

// Run the test
testHighLevelFallback().catch(error => {
  console.error('💥 Fallback test failed:', error.message);
  process.exit(1);
});
