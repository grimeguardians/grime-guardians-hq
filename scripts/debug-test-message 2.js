/**
 * Debug Test Message - Find and analyze the test SMS you just sent
 * This will help us understand why Ava didn't detect it
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function debugTestMessage() {
  console.log('🔍 DEBUG: Searching for your test message...');
  console.log('==================================================');

  try {
    // Load Google Voice Gmail account
    const tokenFilePath = path.join(process.cwd(), 'gmail-tokens-broberts111592@gmail.com.json');
    
    if (!fs.existsSync(tokenFilePath)) {
      console.error('❌ Token file not found:', tokenFilePath);
      return;
    }

    const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
    
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });

    console.log('✅ Gmail connection established');
    console.log('');

    // 1. Check for ALL Google Voice emails (including read ones)
    console.log('1️⃣ Checking ALL recent Google Voice emails...');
    const allGoogleVoice = await gmail.users.messages.list({
      userId: 'me',
      q: 'from:voice-noreply@google.com',
      maxResults: 5
    });

    console.log(`Found ${allGoogleVoice.data.messages?.length || 0} total Google Voice emails`);

    if (allGoogleVoice.data.messages) {
      for (const msgRef of allGoogleVoice.data.messages) {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id: msgRef.id
        });

        const headers = msg.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        const isUnread = msg.data.labelIds?.includes('UNREAD') ? '🆕 UNREAD' : '📖 READ';
        
        console.log(`  - ${isUnread} | ${new Date(date).toLocaleString()} | ${subject}`);
      }
    }

    console.log('');

    // 2. Check ONLY unread messages with our exact filter
    console.log('2️⃣ Checking with PRODUCTION filter...');
    const filteredQuery = 'from:voice-noreply@google.com "New text message from" is:unread -"verification code" -"Indeed" -"Stripe" -"Discord"';
    console.log(`Query: ${filteredQuery}`);

    const filtered = await gmail.users.messages.list({
      userId: 'me',
      q: filteredQuery,
      maxResults: 10
    });

    console.log(`Filtered results: ${filtered.data.messages?.length || 0} messages`);

    if (filtered.data.messages) {
      for (const msgRef of filtered.data.messages) {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id: msgRef.id
        });

        const headers = msg.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        
        console.log(`  ✅ MATCH: ${new Date(date).toLocaleString()} | ${subject}`);
        
        // Extract and show the content
        let content = extractEmailBody(msg.data.payload);
        console.log(`  📝 Content preview: "${content.substring(0, 200)}..."`);
      }
    }

    console.log('');

    // 3. Check for messages from the last 10 minutes
    console.log('3️⃣ Checking messages from last 10 minutes...');
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
    const recentQuery = `from:voice-noreply@google.com after:${Math.floor(tenMinutesAgo.getTime() / 1000)}`;
    console.log(`Recent query: ${recentQuery}`);

    const recent = await gmail.users.messages.list({
      userId: 'me',
      q: recentQuery,
      maxResults: 10
    });

    console.log(`Recent messages (last 10 min): ${recent.data.messages?.length || 0}`);

    if (recent.data.messages) {
      for (const msgRef of recent.data.messages) {
        const msg = await gmail.users.messages.get({
          userId: 'me',
          id: msgRef.id
        });

        const headers = msg.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        const isUnread = msg.data.labelIds?.includes('UNREAD') ? '🆕 UNREAD' : '📖 READ';
        
        console.log(`  - ${isUnread} | ${new Date(date).toLocaleString()} | ${subject}`);
        
        // Show if this would be filtered out and why
        let content = extractEmailBody(msg.data.payload);
        console.log(`    Content: "${content.substring(0, 100)}..."`);
        
        // Check spam filters
        const spamKeywords = ['verification code', 'verification pin', 'indeed', 'stripe', 'discord'];
        const hasSpam = spamKeywords.some(keyword => 
          subject.toLowerCase().includes(keyword) || content.toLowerCase().includes(keyword)
        );
        
        if (hasSpam) {
          console.log(`    🚫 Would be FILTERED as spam`);
        } else {
          console.log(`    ✅ Would PASS spam filter`);
        }
      }
    }

    console.log('');
    console.log('🎯 DIAGNOSIS:');
    console.log('===============');
    
    if (allGoogleVoice.data.messages?.length === 0) {
      console.log('❌ No Google Voice emails found at all - check if test message was sent to 612-584-9396');
    } else if (filtered.data.messages?.length === 0) {
      console.log('⚠️ Messages exist but are being filtered out - check subject line and spam filters');
    } else {
      console.log('✅ Messages found and should be processed by Ava');
    }

  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  }
}

function extractEmailBody(payload) {
  let body = '';
  
  if (payload.body.data) {
    body = Buffer.from(payload.body.data, 'base64').toString();
  } else if (payload.parts) {
    for (const part of payload.parts) {
      if (part.mimeType === 'text/plain' && part.body.data) {
        body += Buffer.from(part.body.data, 'base64').toString();
      }
    }
  }
  
  return body;
}

debugTestMessage();
