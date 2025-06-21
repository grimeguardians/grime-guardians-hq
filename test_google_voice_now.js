/**
 * IMMEDIATE Google Voice Test - No BS, just results
 */
const { google } = require('googleapis');
require('dotenv').config();

async function testGoogleVoiceNow() {
  console.log('🔥 IMMEDIATE GOOGLE VOICE TEST - RESULTS ONLY');
  console.log('================================================');
  
  try {
    // Load Google Voice Gmail account
    const fs = require('fs');
    const tokens = JSON.parse(fs.readFileSync('gmail-tokens-broberts111592@gmail.com.json', 'utf8'));
    
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });
    
    console.log('✅ Gmail connected');
    
    // Test 1: Check for ANY Google Voice emails (read or unread)
    console.log('\n🔍 SEARCHING FOR GOOGLE VOICE EMAILS...');
    const allQuery = 'from:voice-noreply@google.com "SMS from"';
    const allMessages = await gmail.users.messages.list({
      userId: 'me',
      q: allQuery,
      maxResults: 5
    });
    
    console.log(`📧 Found ${allMessages.data.messages?.length || 0} total Google Voice emails`);
    
    // Test 2: Check for UNREAD Google Voice emails  
    const unreadQuery = 'from:voice-noreply@google.com "SMS from" is:unread';
    const unreadMessages = await gmail.users.messages.list({
      userId: 'me',
      q: unreadQuery,
      maxResults: 5
    });
    
    console.log(`📧 Found ${unreadMessages.data.messages?.length || 0} UNREAD Google Voice emails`);
    
    // Test 3: If we have messages, parse the first one
    if (allMessages.data.messages && allMessages.data.messages.length > 0) {
      console.log('\n🔍 PARSING FIRST MESSAGE...');
      const firstMessage = await gmail.users.messages.get({
        userId: 'me',
        id: allMessages.data.messages[0].id
      });
      
      const headers = firstMessage.data.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      console.log(`📝 Subject: "${subject}"`);
      
      // Extract body
      let body = '';
      if (firstMessage.data.payload.body.data) {
        body = Buffer.from(firstMessage.data.payload.body.data, 'base64').toString();
      } else if (firstMessage.data.payload.parts) {
        for (const part of firstMessage.data.payload.parts) {
          if (part.mimeType === 'text/plain' && part.body.data) {
            body += Buffer.from(part.body.data, 'base64').toString();
          }
        }
      }
      
      console.log(`📝 Body preview: "${body.substring(0, 200)}..."`);
      
      // Parse phone and message
      const phoneMatch = subject.match(/SMS from (\+?\d{10,})/);
      const phone = phoneMatch ? phoneMatch[1] : 'NO PHONE FOUND';
      console.log(`📱 Extracted phone: ${phone}`);
      
      // Find actual message content
      const lines = body.split('\n');
      let actualMessage = 'NO MESSAGE FOUND';
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && 
            !trimmed.includes('voice.google.com') && 
            !trimmed.includes('YOUR ACCOUNT') &&
            !trimmed.includes('HELP CENTER') &&
            !trimmed.includes('SMS from') &&
            !trimmed.startsWith('http')) {
          actualMessage = trimmed;
          break;
        }
      }
      console.log(`💬 Extracted message: "${actualMessage}"`);
    }
    
    // Test 4: Real-time monitoring simulation
    console.log('\n🚀 TESTING REAL-TIME DETECTION...');
    console.log('💡 Send an SMS to 612-584-9396 NOW and watch for detection');
    
    let attempts = 0;
    const maxAttempts = 6; // 30 seconds total
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
      attempts++;
      
      console.log(`⏰ Check ${attempts}/${maxAttempts} - Looking for new messages...`);
      
      const newCheck = await gmail.users.messages.list({
        userId: 'me',
        q: unreadQuery,
        maxResults: 1
      });
      
      if (newCheck.data.messages && newCheck.data.messages.length > 0) {
        console.log('🎉 NEW MESSAGE DETECTED!');
        const newMessage = await gmail.users.messages.get({
          userId: 'me',
          id: newCheck.data.messages[0].id
        });
        
        const subject = newMessage.data.payload.headers.find(h => h.name === 'Subject')?.value || '';
        console.log(`📝 New message subject: "${subject}"`);
        
        // Mark as read to prevent reprocessing
        await gmail.users.messages.modify({
          userId: 'me',
          id: newCheck.data.messages[0].id,
          resource: { removeLabelIds: ['UNREAD'] }
        });
        
        console.log('✅ Message processed and marked as read');
        break;
      } else {
        console.log('⏳ No new messages yet...');
      }
    }
    
    if (attempts >= maxAttempts) {
      console.log('⏰ Timeout reached - no new messages detected');
      console.log('💡 Try sending an SMS to 612-584-9396 and run this test again');
    }
    
  } catch (error) {
    console.error('❌ ERROR:', error.message);
    console.error('Full error:', error);
  }
}

// Run the test
testGoogleVoiceNow().then(() => {
  console.log('\n🏁 Test complete');
  process.exit(0);
}).catch(console.error);
