// scripts/test-highlevel-oauth.js
// Test High Level OAuth API access after tokens are obtained

require('dotenv').config();

const HighLevelOAuth = require('../src/utils/highlevelOAuth');

async function testOAuthAccess() {
  console.log('\n=== High Level OAuth API Test ===\n');
  
  const oauth = new HighLevelOAuth();
  
  // Check configuration
  if (!oauth.isConfigured()) {
    console.log('❌ OAuth not fully configured. Missing:');
    console.log(`   - Client ID: ${oauth.clientId ? '✅' : '❌'}`);
    console.log(`   - Client Secret: ${oauth.clientSecret ? '✅' : '❌'}`);
    console.log(`   - Access Token: ${oauth.accessToken ? '✅' : '❌'}`);
    console.log('\nPlease complete OAuth setup first.\n');
    return;
  }
  
  console.log('✅ OAuth configured, testing API access...\n');
  
  try {
    const testResults = await oauth.testAPIAccess();
    
    if (testResults.success) {
      console.log('📊 API Test Results:');
      console.log('┌─────────────────────┬────────┬─────────┐');
      console.log('│ Endpoint            │ Status │ Success │');
      console.log('├─────────────────────┼────────┼─────────┤');
      
      for (const [endpoint, result] of Object.entries(testResults.results)) {
        const status = result.status || 'N/A';
        const success = result.ok ? '✅' : (result.status ? '❌' : 'N/A');
        console.log(`│ ${endpoint.padEnd(19)} │ ${String(status).padEnd(6)} │ ${success.padEnd(7)} │`);
      }
      
      console.log('└─────────────────────┴────────┴─────────┘\n');
      
      // Analysis
      const v2ConvSuccess = testResults.results.conversations_v2?.ok;
      if (v2ConvSuccess) {
        console.log('🎉 SUCCESS: High Level conversations API is accessible!');
        console.log('   The system can now monitor and manage SMS messages.\n');
      } else {
        const convStatus = testResults.results.conversations_v2?.status;
        if (convStatus === 404) {
          console.log('⚠️  Conversations API still returns 404');
          console.log('   This may be due to:');
          console.log('   - Permissions not yet propagated');
          console.log('   - Account level restrictions');
          console.log('   - Different endpoint needed\n');
        } else {
          console.log(`❌ Conversations API error: ${convStatus}`);
          console.log('   Check token permissions and scopes.\n');
        }
      }
    } else {
      console.log('❌ API test failed:', testResults.error);
      if (testResults.results) {
        console.log('Partial results:', testResults.results);
      }
    }
  } catch (error) {
    console.log('❌ Test error:', error.message);
  }
}

testOAuthAccess();
