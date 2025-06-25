#!/usr/bin/env node

/**
 * Google Voice SMS Test - Test the new "New text message from" detection
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function testGoogleVoiceDetection() {
  console.log('🧪 TESTING GOOGLE VOICE SMS DETECTION');
  console.log('=====================================');

  const tokenFilePath = path.join(process.cwd(), 'gmail-tokens-broberts111592@gmail.com.json');
  
  if (!fs.existsSync(tokenFilePath)) {
    console.log('❌ No token file found');
    return;
  }

  try {
    const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
    
    const auth = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      process.env.GMAIL_REDIRECT_URI
    );
    
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });

    // Test the new query for "New text message from"
    console.log('📧 Testing query: "New text message from"...');
    const query = 'from:voice-noreply@google.com "New text message from"';
    
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: 10
    });

    const count = messages.data.messages?.length || 0;
    console.log(`📊 Found ${count} "New text message from" emails`);

    if (count > 0) {
      console.log('\n📝 Analyzing recent SMS messages...');
      
      for (let i = 0; i < Math.min(3, count); i++) {
        const messageRef = messages.data.messages[i];
        const email = await gmail.users.messages.get({
          userId: 'me',
          id: messageRef.id
        });

        const headers = email.data.payload.headers;
        const subject = headers.find(h => h.name === 'Subject')?.value || '';
        const date = headers.find(h => h.name === 'Date')?.value || '';
        
        console.log(`\n📧 Message ${i + 1}:`);
        console.log(`   📅 Date: ${new Date(date).toLocaleString()}`);
        console.log(`   📋 Subject: ${subject}`);
        
        // Extract sender name from subject
        const nameMatch = subject.match(/New text message from (.+)/);
        if (nameMatch) {
          console.log(`   👤 Sender: ${nameMatch[1].trim()}`);
        }
        
        // Extract body content
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
        
        // Show first few lines of content
        const lines = content.split('\n').filter(line => {
          const trimmed = line.trim();
          return trimmed !== '' && 
                 !trimmed.startsWith('http') && 
                 !trimmed.includes('voice.google.com') &&
                 !trimmed.includes('YOUR ACCOUNT') &&
                 !trimmed.includes('HELP CENTER');
        });
        
        console.log(`   💬 Content preview:`);
        lines.slice(0, 3).forEach(line => {
          console.log(`      "${line.trim()}"`);
        });
        
        if (lines.length > 3) {
          console.log(`      ... and ${lines.length - 3} more lines`);
        }
      }
      
      console.log('\n✅ SMS detection query is working!');
      console.log('🎯 Ready to process Google Voice SMS messages');
      
    } else {
      console.log('⚠️ No SMS messages found with this pattern');
      console.log('💡 Try sending a test SMS to 612-584-9396 to verify');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testGoogleVoiceDetection().catch(console.error);
