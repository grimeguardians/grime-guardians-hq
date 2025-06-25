#!/usr/bin/env node

/**
 * Manual OAuth Code Processor
 * Use this when you have the authorization code from the redirect URL
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function processOAuthCode() {
  // The authorization code from your URL
  const authCode = 'b53b301981cc8e8f7e73abf3cdd383c32368d8d4';
  
  console.log('🔐 Processing High Level OAuth Code');
  console.log('====================================\n');
  
  const oauth = new HighLevelOAuth();
  
  try {
    console.log('🔄 Exchanging authorization code for tokens...');
    
    const tokens = await oauth.exchangeCodeForTokens(authCode);
    
    console.log('✅ Token exchange successful!');
    console.log(`   • Access Token: ${tokens.access_token ? 'Received' : 'Missing'}`);
    console.log(`   • Refresh Token: ${tokens.refresh_token ? 'Received' : 'Missing'}`);
    console.log(`   • Token Type: ${tokens.token_type || 'Bearer'}`);
    console.log(`   • Scope: ${tokens.scope || 'conversations'}`);
    
    // Test the API access
    console.log('\n🧪 Testing API access...');
    
    const testResult = await oauth.testAPIAccess();
    
    if (testResult.success) {
      const results = testResult.results;
      
      console.log('\n📊 API Test Results:');
      console.log(`   • Token Status: ${results.token_status.has_access_token ? '✅' : '❌'} Access, ${results.token_status.has_refresh_token ? '✅' : '❌'} Refresh`);
      console.log(`   • Token Expiry: ${results.token_status.expiry_time}`);
      console.log(`   • Contacts API: ${results.contacts_v2?.ok ? '✅' : '❌'} (${results.contacts_v2?.status})`);
      console.log(`   • Conversations API: ${results.conversations_v2?.ok ? '✅' : '❌'} (${results.conversations_v2?.status})`);
      console.log(`   • Location Access: ${results.location_access?.ok ? '✅' : '❌'} (${results.location_access?.status})`);
      
      if (results.conversations_v2?.ok) {
        console.log('\n🎉 High Level OAuth setup complete and working!');
        console.log('🚀 Your system can now monitor High Level SMS conversations.');
        
        // Test getting conversations
        console.log('\n🧪 Testing conversation retrieval...');
        const conversations = await oauth.getConversations({ limit: 3 });
        console.log(`   Retrieved ${conversations.length} conversations`);
        
      } else {
        console.log('\n⚠️  Conversations API returned an error.');
        console.log('   This might be due to:');
        console.log('   • Insufficient permissions/scopes');
        console.log('   • New app needs approval by High Level');
        console.log('   • Location-specific restrictions');
        console.log('\n   The tokens are saved and will retry automatically.');
      }
      
    } else {
      console.log(`\n❌ API test failed: ${testResult.error}`);
    }
    
  } catch (error) {
    console.error('\n❌ OAuth processing failed:', error.message);
    
    if (error.message.includes('invalid_grant')) {
      console.log('\n💡 The authorization code may have expired or been used already.');
      console.log('   Try getting a new authorization code from:');
      console.log(`   ${oauth.getAuthUrl()}`);
    }
  }
}

// Run the processor
processOAuthCode().catch(error => {
  console.error('💥 Processing failed:', error.message);
  process.exit(1);
});
