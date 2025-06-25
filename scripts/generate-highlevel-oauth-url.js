// scripts/generate-highlevel-oauth-url.js
// Generate High Level OAuth authorization URL for local testing

require('dotenv').config();

const HighLevelOAuth = require('../src/utils/highlevelOAuth');

function generateOAuthURL() {
  console.log('\n=== High Level OAuth Setup Helper ===\n');
  
  // Check if required env vars are present
  const clientId = process.env.HIGHLEVEL_OAUTH_CLIENT_ID;
  const clientSecret = process.env.HIGHLEVEL_OAUTH_CLIENT_SECRET;
  const redirectUri = process.env.HIGHLEVEL_OAUTH_REDIRECT_URI;
  
  if (!clientId || !clientSecret || !redirectUri) {
    console.log('❌ Missing required OAuth credentials in .env file:');
    console.log(`   - HIGHLEVEL_OAUTH_CLIENT_ID: ${clientId ? '✅ Set' : '❌ Missing'}`);
    console.log(`   - HIGHLEVEL_OAUTH_CLIENT_SECRET: ${clientSecret ? '✅ Set' : '❌ Missing'}`);
    console.log(`   - HIGHLEVEL_OAUTH_REDIRECT_URI: ${redirectUri ? '✅ Set' : '❌ Missing'}`);
    console.log('\nPlease update your .env file and try again.\n');
    return;
  }
  
  const oauth = new HighLevelOAuth();
  const authUrl = oauth.getAuthUrl();
  
  console.log('✅ OAuth credentials found in .env file');
  console.log(`📍 Redirect URI: ${redirectUri}`);
  console.log('\n🔗 Authorization URL:');
  console.log(authUrl);
  console.log('\n📋 Next Steps:');
  console.log('1. Make sure your Grime Guardians system is running (npm start or node src/index.js)');
  console.log('2. Open the authorization URL above in your browser');
  console.log('3. Complete the High Level OAuth flow');
  console.log('4. The system will automatically receive the callback and exchange tokens');
  console.log('5. Check the console output for confirmation\n');
}

generateOAuthURL();
