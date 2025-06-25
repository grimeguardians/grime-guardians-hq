/**
 * Gmail Authentication Debug Script
 * This will help us understand why Gmail monitoring stopped working
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function debugGmailAuth() {
  console.log('🔍 Gmail Authentication Debug Started');
  console.log('=====================================');
  
  // Check environment variables
  console.log('\n📋 Environment Variables:');
  console.log(`GMAIL_CLIENT_ID: ${process.env.GMAIL_CLIENT_ID ? 'Set' : 'MISSING'}`);
  console.log(`GMAIL_CLIENT_SECRET: ${process.env.GMAIL_CLIENT_SECRET ? 'Set' : 'MISSING'}`);
  console.log(`GMAIL_REDIRECT_URI: ${process.env.GMAIL_REDIRECT_URI || 'MISSING'}`);
  console.log(`GMAIL_EMAILS: ${process.env.GMAIL_EMAILS || 'MISSING'}`);
  
  // Check token files
  console.log('\n📁 Token Files:');
  const emailAddresses = process.env.GMAIL_EMAILS ? process.env.GMAIL_EMAILS.split(',') : [];
  
  for (const email of emailAddresses) {
    const trimmedEmail = email.trim();
    const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${trimmedEmail}.json`);
    
    if (fs.existsSync(tokenFilePath)) {
      try {
        const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
        console.log(`✅ ${trimmedEmail}: Token file exists`);
        console.log(`   - Access Token: ${tokens.access_token ? 'Present' : 'MISSING'}`);
        console.log(`   - Refresh Token: ${tokens.refresh_token ? 'Present' : 'MISSING'}`);
        console.log(`   - Expiry: ${tokens.expiry_date ? new Date(tokens.expiry_date).toISOString() : 'Not set'}`);
        
        // Test authentication
        try {
          const auth = new google.auth.OAuth2(
            process.env.GMAIL_CLIENT_ID,
            process.env.GMAIL_CLIENT_SECRET,
            process.env.GMAIL_REDIRECT_URI
          );
          
          auth.setCredentials(tokens);
          
          const gmail = google.gmail({ version: 'v1', auth });
          const profile = await gmail.users.getProfile({ userId: 'me' });
          
          console.log(`   - Authentication: ✅ SUCCESS`);
          console.log(`   - Email Address: ${profile.data.emailAddress}`);
          
          // Test Google Voice email search
          const query = 'from:voice-noreply@google.com ("New text message" OR "New group message") is:unread';
          const messages = await gmail.users.messages.list({
            userId: 'me',
            q: query,
            maxResults: 5
          });
          
          console.log(`   - Google Voice Messages: ${messages.data.messages?.length || 0} found`);
          
        } catch (authError) {
          console.log(`   - Authentication: ❌ FAILED`);
          console.log(`   - Error: ${authError.message}`);
        }
        
      } catch (parseError) {
        console.log(`❌ ${trimmedEmail}: Invalid token file - ${parseError.message}`);
      }
    } else {
      console.log(`❌ ${trimmedEmail}: Token file missing at ${tokenFilePath}`);
    }
  }
  
  console.log('\n🎯 Next Steps:');
  if (emailAddresses.length === 0) {
    console.log('- Set GMAIL_EMAILS environment variable');
  } else {
    console.log('- If authentication failed, run: node scripts/setup-gmail-auth.js');
    console.log('- Ensure token files are present and valid');
    console.log('- Check if tokens need refreshing');
  }
}

debugGmailAuth().catch(console.error);
