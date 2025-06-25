#!/usr/bin/env node

/**
 * High Level API Endpoint Explorer
 * Test different API endpoints to find what works
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function exploreHighLevelAPI() {
  console.log('🔍 High Level API Endpoint Explorer');
  console.log('====================================\n');
  
  const oauth = new HighLevelOAuth();
  
  if (!oauth.isConfigured()) {
    console.log('❌ OAuth not configured. Please run setup first.');
    return;
  }
  
  console.log('📍 Testing with Location ID:', process.env.HIGHLEVEL_LOCATION_ID);
  console.log('🔑 Using OAuth tokens...\n');
  
  // Test various API endpoints
  const endpoints = [
    {
      name: 'Contacts v2',
      url: 'https://services.leadconnectorhq.com/contacts/',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 1 }
    },
    {
      name: 'Conversations v2 (with locationId param)',
      url: 'https://services.leadconnectorhq.com/conversations/',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 1 }
    },
    {
      name: 'Conversations v2 (no params)',
      url: 'https://services.leadconnectorhq.com/conversations/',
      params: { limit: 1 }
    },
    {
      name: 'Location Details',
      url: `https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}`,
      params: {}
    },
    {
      name: 'User Info',
      url: 'https://services.leadconnectorhq.com/users/me',
      params: {}
    },
    {
      name: 'Conversations v1 (old API)',
      url: 'https://rest.gohighlevel.com/v1/conversations/',
      params: { locationId: process.env.HIGHLEVEL_LOCATION_ID, limit: 1 }
    }
  ];
  
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
        
        // Show some sample data structure
        if (data.conversations && data.conversations.length > 0) {
          console.log(`   📋 Found ${data.conversations.length} conversations`);
          const sample = data.conversations[0];
          console.log(`   📝 Sample ID: ${sample.id}`);
        } else if (data.contacts && data.contacts.length > 0) {
          console.log(`   📋 Found ${data.contacts.length} contacts`);
        } else if (data.id) {
          console.log(`   📝 Resource ID: ${data.id}`);
        } else if (data.email) {
          console.log(`   👤 User: ${data.email}`);
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
  
  console.log('🎯 API exploration complete!');
  console.log('\nℹ️  Look for ✅ SUCCESS endpoints above. These are the working API endpoints.');
}

// Run the explorer
exploreHighLevelAPI().catch(error => {
  console.error('💥 API exploration failed:', error.message);
  process.exit(1);
});
