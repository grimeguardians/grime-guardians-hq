/**
 * Test the updated Gmail query to see if it finds existing text messages
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function testUpdatedQuery() {
  console.log('🧪 Testing updated Gmail query...');
  console.log('=================================');

  try {
    const tokenFilePath = path.join(process.cwd(), 'gmail-tokens-broberts111592@gmail.com.json');
    const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
    
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });

    // Test the NEW query (without unread filter for testing)
    const newQuery = 'from:voice-noreply@google.com ("New text message" OR "New group message") -"verification code" -"Indeed" -"Stripe" -"Discord" -from:31061 -from:22395 -from:65161';
    console.log(`🔍 Testing query: ${newQuery}`);

    const results = await gmail.users.messages.list({
      userId: 'me',
      q: newQuery,
      maxResults: 10
    });

    console.log(`📧 Found ${results.data.messages?.length || 0} text messages`);

    if (results.data.messages) {
      for (const msgRef of results.data.messages) {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id: msgRef.id
        });

        const headers = msg.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        const isUnread = msg.data.labelIds?.includes('UNREAD') ? '🆕 UNREAD' : '📖 READ';
        
        console.log(`  ${isUnread} | ${new Date(date).toLocaleDateString()} | ${subject}`);

        // Test the parsing logic
        let nameMatch = subject.match(/New text message from (.+)/);
        if (!nameMatch) {
          nameMatch = subject.match(/New group message from (.+)/);
        }
        
        if (nameMatch) {
          let senderName = nameMatch[1].trim();
          if (senderName.endsWith('.')) {
            senderName = senderName.slice(0, -1);
          }
          console.log(`    📱 Sender: "${senderName}"`);
          
          // Test spam filtering
          const spamShortCodes = ['31061', '22395', '65161'];
          const isSpam = /^\d{4,6}$/.test(senderName) || spamShortCodes.includes(senderName);
          console.log(`    ${isSpam ? '🚫 SPAM' : '✅ LEGITIMATE'}: Would ${isSpam ? 'filter out' : 'process'}`);
        }
      }
    }

    console.log('');
    console.log('✅ Query test complete!');
    console.log('Now try sending a new test message to 612-584-9396');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testUpdatedQuery();
