const { google } = require('googleapis');
require('dotenv').config();

async function debugGoogleVoiceEmails() {
  try {
    const fs = require('fs');
    const path = require('path');
    
    // Connect to Gmail for broberts111592@gmail.com
    const tokenFilePath = path.join(process.cwd(), 'gmail-tokens-broberts111592@gmail.com.json');
    const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
    
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });
    
    // Search for Google Voice messages
    const query = 'from:@txt.voice.google.com subject:("New text message from") is:unread';
    console.log('🔍 Searching for Google Voice emails...');
    
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: 3 // Just get a few for debugging
    });
    
    if (!messages.data.messages || messages.data.messages.length === 0) {
      console.log('❌ No Google Voice messages found');
      return;
    }
    
    console.log(`📱 Found ${messages.data.messages.length} messages. Analyzing first one...`);
    
    // Get the first message for detailed analysis
    const email = await gmail.users.messages.get({
      userId: 'me',
      id: messages.data.messages[0].id
    });
    
    const headers = email.data.payload.headers;
    const subject = headers.find(h => h.name === 'Subject')?.value || '';
    const from = headers.find(h => h.name === 'From')?.value || '';
    
    console.log('\n📧 EMAIL DETAILS:');
    console.log('Subject:', subject);
    console.log('From:', from);
    
    // Extract email body
    let body = '';
    if (email.data.payload.body.data) {
      body = Buffer.from(email.data.payload.body.data, 'base64').toString();
    } else if (email.data.payload.parts) {
      for (const part of email.data.payload.parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          body += Buffer.from(part.body.data, 'base64').toString();
        }
      }
    }
    
    console.log('\n📝 EMAIL BODY:');
    console.log('---START OF BODY---');
    console.log(body);
    console.log('---END OF BODY---');
    
    // Test our parsing logic
    console.log('\n🔧 TESTING PARSING LOGIC:');
    const lines = body.split('\n');
    console.log('Total lines:', lines.length);
    
    lines.forEach((line, index) => {
      console.log(`Line ${index}: "${line.trim()}"`);
    });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

debugGoogleVoiceEmails();
