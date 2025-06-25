/**
 * Check Google Voice Email Settings - Verify SMS notifications are enabled
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function checkGoogleVoiceSettings() {
  console.log('🔍 Checking Google Voice email notification patterns...');
  console.log('=========================================================');

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

    // Search for ALL subject line patterns from Google Voice
    console.log('📧 All Google Voice email subject patterns:');
    
    const allMessages = await gmail.users.messages.list({
      userId: 'me',
      q: 'from:voice-noreply@google.com',
      maxResults: 20
    });

    const subjectPatterns = new Set();
    
    if (allMessages.data.messages) {
      for (const msgRef of allMessages.data.messages) {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id: msgRef.id
        });

        const headers = msg.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        
        // Extract pattern (remove specific names/numbers)
        let pattern = subject
          .replace(/\(\d{3}\) \d{3}-\d{4}/g, '(XXX) XXX-XXXX')  // Phone numbers
          .replace(/🧽 \w+/g, '🧽 [NAME]')  // Named contacts
          .replace(/from \w+/g, 'from [NAME]');  // Names after "from"
        
        subjectPatterns.add(pattern);
        
        console.log(`${new Date(date).toLocaleDateString()} | ${subject}`);
      }
    }

    console.log('');
    console.log('📋 Unique subject patterns found:');
    subjectPatterns.forEach(pattern => {
      console.log(`  - "${pattern}"`);
    });

    console.log('');
    console.log('🔍 Looking specifically for TEXT MESSAGE patterns...');
    
    // Search more broadly for text-related keywords
    const textQueries = [
      'from:voice-noreply@google.com text',
      'from:voice-noreply@google.com message',
      'from:voice-noreply@google.com SMS',
      'from:voice-noreply@google.com "New text"'
    ];

    for (const query of textQueries) {
      console.log(`\nTrying: ${query}`);
      const results = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 5
      });
      
      console.log(`  Results: ${results.data.messages?.length || 0} messages`);
      
      if (results.data.messages) {
        for (const msgRef of results.data.messages) {
          const msg = await gmail.users.messages.get({
            userId: 'me',
            id: msgRef.id
          });

          const headers = msg.data.payload.headers;
          const subject = headers.find(h => h.name === 'Subject')?.value || '';
          console.log(`    - ${subject}`);
        }
      }
    }

    console.log('');
    console.log('💡 RECOMMENDATIONS:');
    console.log('===================');
    console.log('1. Check if SMS notifications are enabled in Google Voice settings');
    console.log('2. Verify the test message was sent to 612-584-9396');
    console.log('3. Wait a few minutes - Google Voice emails can be delayed');
    console.log('4. Try sending from a different phone number');
    console.log('5. Check Google Voice app/web interface to confirm message arrived');

  } catch (error) {
    console.error('❌ Check failed:', error.message);
  }
}

checkGoogleVoiceSettings();
