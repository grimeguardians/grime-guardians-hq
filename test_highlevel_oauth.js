#!/usr/bin/env node

/**
 * Test High Level OAuth Integration
 * Run this script to test the High Level OAuth setup
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function testHighLevelOAuth() {
  console.log('🧪 Testing High Level OAuth Integration\n');
  
  const oauth = new HighLevelOAuth();
  
  // Check configuration
  console.log('1️⃣ Checking OAuth Configuration...');
  const isConfigured = oauth.isConfigured();
  console.log(`   ✅ OAuth Configured: ${isConfigured ? 'YES' : 'NO'}`);
  
  if (!isConfigured) {
    console.log('\n❌ OAuth not configured. Please complete these steps:');
    console.log('   1. Ensure .env has all OAuth credentials');
    console.log('   2. Complete the OAuth flow by visiting:');
    console.log(`   ${oauth.getAuthUrl()}`);
    console.log('   3. Exchange the authorization code for tokens\n');
    return;
  }
  
  // Test API access
  console.log('\n2️⃣ Testing API Access...');
  try {
    const testResult = await oauth.testAPIAccess();
    
    if (testResult.success) {
      console.log('   ✅ API Test: SUCCESS\n');
      
      const results = testResult.results;
      
      console.log('📊 Token Status:');
      console.log(`   • Access Token: ${results.token_status.has_access_token ? '✅' : '❌'}`);
      console.log(`   • Refresh Token: ${results.token_status.has_refresh_token ? '✅' : '❌'}`);
      console.log(`   • Token Expired: ${results.token_status.token_expired ? '❌ YES' : '✅ NO'}`);
      console.log(`   • Expires: ${results.token_status.expiry_time}`);
      
      console.log('\n🔗 API Endpoints:');
      console.log(`   • Contacts v2: ${results.contacts_v2?.ok ? '✅' : '❌'} (${results.contacts_v2?.status})`);
      console.log(`   • Conversations v2: ${results.conversations_v2?.ok ? '✅' : '❌'} (${results.conversations_v2?.status})`);
      console.log(`   • Location Access: ${results.location_access?.ok ? '✅' : '❌'} (${results.location_access?.status})`);
      
    } else {
      console.log(`   ❌ API Test: FAILED - ${testResult.error}\n`);
    }
    
  } catch (error) {
    console.log(`   ❌ API Test: ERROR - ${error.message}\n`);
  }
  
  // Test conversations (if API access is working)
  console.log('\n3️⃣ Testing Conversations API...');
  try {
    const conversations = await oauth.getConversations({ limit: 3 });
    console.log(`   ✅ Retrieved ${conversations.length} conversations`);
    
    if (conversations.length > 0) {
      console.log('   📋 Sample conversation:');
      const sample = conversations[0];
      console.log(`      • ID: ${sample.id}`);
      console.log(`      • Contact: ${sample.contactId || 'N/A'}`);
      console.log(`      • Created: ${sample.dateAdded || 'N/A'}`);
    }
    
  } catch (error) {
    console.log(`   ❌ Conversations Test: ERROR - ${error.message}`);
  }
  
  console.log('\n🎉 High Level OAuth test complete!');
}

// Run the test
testHighLevelOAuth().catch(error => {
  console.error('💥 Test failed:', error.message);
  process.exit(1);
});
