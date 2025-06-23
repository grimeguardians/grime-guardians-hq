/**
 * Debug Google Voice Email Format - Check actual message structure
 */

require('dotenv').config();
const { google } = require('googleapis');

async function debugGoogleVoiceFormat() {
  console.log('🔍 DEBUGGING GOOGLE VOICE EMAIL FORMAT');
  console.log('='.repeat(50));
  
  try {
    // Initialize Gmail for Google Voice account
    const fs = require('fs');
    const path = require('path');
    
    const tokenFilePath = path.join(process.cwd(), 'gmail-tokens-broberts111592@gmail.com.json');
    const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
    
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });
    
    // Get recent Google Voice messages
    console.log('📧 Fetching recent Google Voice messages...');
    
    const query = 'from:voice-noreply@google.com ("New text message" OR "New group message")';
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: 3
    });
    
    if (!messages.data.messages || messages.data.messages.length === 0) {
      console.log('❌ No Google Voice messages found');
      return;
    }
    
    console.log(`📊 Found ${messages.data.messages.length} messages to analyze`);
    
    // Analyze each message
    for (let i = 0; i < messages.data.messages.length; i++) {
      const messageRef = messages.data.messages[i];
      console.log(`\n📧 ANALYZING MESSAGE ${i + 1}:`);
      console.log('='.repeat(30));
      
      const email = await gmail.users.messages.get({
        userId: 'me',
        id: messageRef.id
      });
      
      const headers = email.data.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const from = headers.find(h => h.name === 'From')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';
      
      console.log(`📋 Subject: "${subject}"`);
      console.log(`📧 From: "${from}"`);
      console.log(`📅 Date: "${date}"`);
      
      // Extract email body
      let content = '';
      
      if (email.data.payload.body.data) {
        content = Buffer.from(email.data.payload.body.data, 'base64').toString();
      } else if (email.data.payload.parts) {
        for (const part of email.data.payload.parts) {
          if (part.mimeType === 'text/plain' && part.body.data) {
            content += Buffer.from(part.body.data, 'base64').toString();
          }
        }
      }
      
      console.log(`📝 Content (first 300 chars):`);
      console.log(`"${content.substring(0, 300)}..."`);
      
      console.log(`\n🔍 Content Analysis:`);
      console.log(`   Length: ${content.length} characters`);
      console.log(`   Lines: ${content.split('\n').length}`);
      
      // Check for common patterns
      const patterns = [
        /New text message from (.+)/,
        /New group message from (.+)/,
        /SMS from (\+?\d+)/,
        /(\+\d{11})/,
        /\d{3}-\d{3}-\d{4}/
      ];
      
      console.log(`\n🎯 Pattern Matches:`);
      patterns.forEach((pattern, idx) => {
        const match = subject.match(pattern) || content.match(pattern);
        console.log(`   Pattern ${idx + 1}: ${match ? `✅ "${match[1] || match[0]}"` : '❌ No match'}`);
      });
    }
    
  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  }
}

debugGoogleVoiceFormat().then(() => {
  console.log('\n🏁 Debug completed');
  process.exit(0);
}).catch(error => {
  console.error('💥 Debug crashed:', error);
  process.exit(1);
});
