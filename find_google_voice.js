/**
 * FIND GOOGLE VOICE EMAILS - Check ALL accounts
 */
const { google } = require('googleapis');
require('dotenv').config();

async function findGoogleVoiceEmails() {
  console.log('🔍 SEARCHING ALL GMAIL ACCOUNTS FOR GOOGLE VOICE');
  console.log('==============================================');
  
  const accounts = [
    'broberts111592@gmail.com',
    'grimeguardianscleaning@gmail.com', 
    'brandonr@grimeguardians.com'
  ];
  
  for (const email of accounts) {
    console.log(`\n📧 Checking ${email}...`);
    
    try {
      const fs = require('fs');
      const tokenFile = `gmail-tokens-${email}.json`;
      
      if (!fs.existsSync(tokenFile)) {
        console.log(`❌ No token file: ${tokenFile}`);
        continue;
      }
      
      const tokens = JSON.parse(fs.readFileSync(tokenFile, 'utf8'));
      
      const auth = new google.auth.OAuth2(
        process.env.GMAIL_CLIENT_ID,
        process.env.GMAIL_CLIENT_SECRET,
        process.env.GMAIL_REDIRECT_URI
      );
      
      auth.setCredentials(tokens);
      const gmail = google.gmail({ version: 'v1', auth });
      
      // Check for Google Voice emails
      const voiceQuery = 'from:voice-noreply@google.com';
      const voiceMessages = await gmail.users.messages.list({
        userId: 'me',
        q: voiceQuery,
        maxResults: 10
      });
      
      console.log(`📧 Found ${voiceMessages.data.messages?.length || 0} Google Voice emails`);
      
      if (voiceMessages.data.messages && voiceMessages.data.messages.length > 0) {
        console.log('✅ FOUND GOOGLE VOICE EMAILS! Checking first one...');
        
        const firstMessage = await gmail.users.messages.get({
          userId: 'me',
          id: voiceMessages.data.messages[0].id
        });
        
        const headers = firstMessage.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        
        console.log(`📝 Subject: "${subject}"`);
        console.log(`📅 Date: ${date}`);
        
        // Check if it's SMS
        if (subject.includes('SMS from')) {
          console.log('🎯 THIS IS AN SMS NOTIFICATION!');
          const phoneMatch = subject.match(/SMS from (\+?\d{10,})/);
          if (phoneMatch) {
            console.log(`📱 Phone: ${phoneMatch[1]}`);
          }
        }
      }
      
      // Also check for any SMS-related emails
      const smsQuery = 'SMS';
      const smsMessages = await gmail.users.messages.list({
        userId: 'me',
        q: smsQuery,
        maxResults: 5
      });
      
      console.log(`📱 Found ${smsMessages.data.messages?.length || 0} SMS-related emails`);
      
    } catch (error) {
      console.log(`❌ Error checking ${email}: ${error.message}`);
    }
  }
  
  console.log('\n🔍 RECOMMENDATION:');
  console.log('1. Check which Gmail account is linked to Google Voice number 612-584-9396');
  console.log('2. Verify SMS email notifications are enabled in Google Voice settings');
  console.log('3. Test by sending SMS to 612-584-9396 and see which account receives it');
}

findGoogleVoiceEmails().then(() => {
  console.log('\n🏁 Search complete');
  process.exit(0);
}).catch(console.error);
