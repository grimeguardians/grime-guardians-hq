/**
 * Quick Google Voice Email Test
 * Tests if we can successfully monitor the Google Voice account
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function testGoogleVoiceMonitoring() {
  console.log('🧪 Testing Google Voice Email Monitoring');
  console.log('=' .repeat(50));
  
  try {
    // Load tokens for the Google Voice account
    const tokenFile = 'gmail-tokens-broberts111592@gmail.com.json';
    if (!fs.existsSync(tokenFile)) {
      console.log('❌ Token file not found for broberts111592@gmail.com');
      console.log('Run: node scripts/setup-gmail-multi-auth.js first');
      return;
    }
    
    const tokens = JSON.parse(fs.readFileSync(tokenFile, 'utf8'));
    
    // Create auth client
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    
    const gmail = google.gmail({ version: 'v1', auth });
    
    // Test connection
    const profile = await gmail.users.getProfile({ userId: 'me' });
    console.log(`✅ Connected to: ${profile.data.emailAddress}`);
    
    // Search for Google Voice SMS emails
    console.log('🔍 Searching for Google Voice SMS emails...');
    const response = await gmail.users.messages.list({
      userId: 'me',
      q: 'from:txt.voice.google.com OR from:voice-noreply@google.com',
      maxResults: 10
    });
    
    const messages = response.data.messages || [];
    console.log(`📱 Found ${messages.length} Google Voice emails`);
    
    if (messages.length > 0) {
      console.log('');
      console.log('📧 Recent Google Voice emails:');
      
      for (let i = 0; i < Math.min(3, messages.length); i++) {
        const messageData = await gmail.users.messages.get({
          userId: 'me',
          id: messages[i].id
        });
        
        const headers = messageData.data.payload.headers || [];
        const subject = headers.find(h => h.name === 'Subject')?.value || 'No subject';
        const from = headers.find(h => h.name === 'From')?.value || 'Unknown sender';
        const date = headers.find(h => h.name === 'Date')?.value || 'Unknown date';
        
        console.log(`  ${i + 1}. ${subject}`);
        console.log(`     From: ${from}`);
        console.log(`     Date: ${date}`);
        console.log('');
      }
    } else {
      console.log('ℹ️  No Google Voice emails found. This is normal if no SMS have been received recently.');
    }
    
    console.log('✅ Google Voice monitoring test completed successfully!');
    console.log('');
    console.log('🚀 The system is ready to monitor Google Voice SMS messages');
    console.log('   Phone: 612-584-9396');
    console.log('   Email: broberts111592@gmail.com');
    console.log('');
    console.log('💡 To test: Send an SMS to 612-584-9396 and it should be detected');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    if (error.message.includes('invalid_grant')) {
      console.log('💡 The token may have expired. Run the setup script again:');
      console.log('   node scripts/setup-gmail-multi-auth.js');
    }
  }
}

// Run the test
testGoogleVoiceMonitoring();
