#!/usr/bin/env node

/**
 * High Level OAuth Authorization Flow Helper
 * This script helps you complete the OAuth flow for High Level
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

async function runOAuthFlow() {
  console.log('🔐 High Level OAuth Authorization Flow\n');
  
  const oauth = new HighLevelOAuth();
  
  // Check if already configured
  if (oauth.isConfigured()) {
    console.log('✅ OAuth already configured! Testing current setup...\n');
    
    try {
      const testResult = await oauth.testAPIAccess();
      if (testResult.success) {
        console.log('🎉 OAuth is working perfectly! No action needed.');
        rl.close();
        return;
      } else {
        console.log(`⚠️ OAuth tokens may be expired: ${testResult.error}\n`);
      }
    } catch (error) {
      console.log(`❌ Current OAuth setup has issues: ${error.message}\n`);
    }
  }
  
  // Step 1: Show authorization URL
  console.log('Step 1: Visit the authorization URL');
  console.log('======================================');
  const authUrl = oauth.getAuthUrl();
  console.log(`\n🔗 Click or visit this URL:\n${authUrl}\n`);
  
  console.log('👆 This will:');
  console.log('   • Redirect you to High Level');
  console.log('   • Ask you to select a location');
  console.log('   • Grant permissions for conversations access');
  console.log('   • Redirect back to your local callback URL\n');
  
  // Step 2: Get authorization code
  console.log('Step 2: Get the authorization code');
  console.log('===================================');
  console.log('After authorizing, you\'ll be redirected to:');
  console.log('http://localhost:3000/oauth/callback/gohighlevel?code=AUTHORIZATION_CODE\n');
  
  const authCode = await question('📋 Paste the authorization code from the URL: ');
  
  if (!authCode || authCode.trim().length === 0) {
    console.log('❌ No authorization code provided. Exiting...');
    rl.close();
    return;
  }
  
  // Step 3: Exchange code for tokens
  console.log('\nStep 3: Exchanging code for tokens...');
  console.log('=====================================');
  
  try {
    const tokens = await oauth.exchangeCodeForTokens(authCode.trim());
    
    console.log('✅ Token exchange successful!');
    console.log(`   • Access Token: ${tokens.access_token ? 'Received' : 'Missing'}`);
    console.log(`   • Refresh Token: ${tokens.refresh_token ? 'Received' : 'Missing'}`);
    console.log(`   • Token Type: ${tokens.token_type || 'Unknown'}`);
    console.log(`   • Location ID: ${tokens.locationId || 'Not provided'}\n`);
    
    // Update .env with location ID if provided
    if (tokens.locationId) {
      const fs = require('fs');
      const path = require('path');
      const envPath = path.join(process.cwd(), '.env');
      let envContent = fs.readFileSync(envPath, 'utf8');
      
      const locationRegex = /^HIGHLEVEL_LOCATION_ID=.*$/m;
      if (locationRegex.test(envContent)) {
        envContent = envContent.replace(locationRegex, `HIGHLEVEL_LOCATION_ID=${tokens.locationId}`);
      } else {
        envContent += `\nHIGHLEVEL_LOCATION_ID=${tokens.locationId}`;
      }
      
      fs.writeFileSync(envPath, envContent);
      console.log('📝 Updated .env with location ID');
    }
    
  } catch (error) {
    console.log(`❌ Token exchange failed: ${error.message}`);
    rl.close();
    return;
  }
  
  // Step 4: Test the API
  console.log('Step 4: Testing API access...');
  console.log('==============================');
  
  try {
    const testResult = await oauth.testAPIAccess();
    
    if (testResult.success) {
      console.log('🎉 OAuth setup complete and working!\n');
      
      const results = testResult.results;
      console.log('📊 API Status Summary:');
      console.log(`   • Contacts API: ${results.contacts_v2?.ok ? '✅' : '❌'}`);
      console.log(`   • Conversations API: ${results.conversations_v2?.ok ? '✅' : '❌'}`);
      console.log(`   • Location Access: ${results.location_access?.ok ? '✅' : '❌'}`);
      
      console.log('\n🚀 Your system is now ready to monitor High Level SMS!');
      
    } else {
      console.log(`❌ API test failed: ${testResult.error}`);
    }
    
  } catch (error) {
    console.log(`❌ API test error: ${error.message}`);
  }
  
  rl.close();
}

// Run the OAuth flow
console.log('Starting High Level OAuth setup...\n');
runOAuthFlow().catch(error => {
  console.error('💥 OAuth flow failed:', error.message);
  rl.close();
  process.exit(1);
});
