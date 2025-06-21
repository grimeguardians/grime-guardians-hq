#!/usr/bin/env node

/**
 * Live SMS Test Monitor
 * Watches for new Google Voice SMS emails in real-time
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function liveMonitor() {
  console.log('🔴 LIVE SMS MONITOR - Watching for new Google Voice SMS...');
  console.log('===========================================================');
  console.log('⏰ This will check every 10 seconds for new SMS notifications');
  console.log('📱 Send a test SMS to 612-584-9396 now!');
  console.log('');

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

    let lastCheckTime = new Date();
    console.log(`🕐 Starting monitor at: ${lastCheckTime.toLocaleTimeString()}`);

    const checkInterval = setInterval(async () => {
      try {
        const now = new Date();
        console.log(`\n🔍 [${now.toLocaleTimeString()}] Checking for new SMS emails...`);

        // Check for ANY new Google Voice emails since last check
        const sinceQuery = `from:voice-noreply@google.com after:${Math.floor(lastCheckTime.getTime() / 1000)}`;
        
        console.log(`   Query: ${sinceQuery}`);

        const messages = await gmail.users.messages.list({
          userId: 'me',
          q: sinceQuery,
          maxResults: 10
        });

        const newCount = messages.data.messages?.length || 0;
        console.log(`   📊 Found ${newCount} new Google Voice emails`);

        if (newCount > 0) {
          console.log('\n🎉 NEW GOOGLE VOICE EMAIL(S) DETECTED!');
          console.log('========================================');
          
          for (const messageRef of messages.data.messages) {
            const email = await gmail.users.messages.get({
              userId: 'me',
              id: messageRef.id
            });

            const headers = email.data.payload.headers;
            const subject = headers.find(h => h.name === 'Subject')?.value || '';
            const from = headers.find(h => h.name === 'From')?.value || '';
            const date = headers.find(h => h.name === 'Date')?.value || '';

            console.log(`📧 Subject: ${subject}`);
            console.log(`📅 Date: ${date}`);
            console.log(`👤 From: ${from}`);

            // Check if this is an SMS
            if (subject.toLowerCase().includes('sms') || subject.toLowerCase().includes('text')) {
              console.log('🎯 SMS NOTIFICATION FOUND! ✅');
              
              // Extract content for testing
              let content = '';
              if (email.data.payload.body?.data) {
                content = Buffer.from(email.data.payload.body.data, 'base64').toString();
              } else if (email.data.payload.parts) {
                for (const part of email.data.payload.parts) {
                  if (part.mimeType === 'text/plain' && part.body?.data) {
                    content += Buffer.from(part.body.data, 'base64').toString();
                  }
                }
              }
              
              console.log(`📝 Content preview: ${content.substring(0, 200)}...`);
              console.log('');
              console.log('🚀 SMS EMAIL NOTIFICATIONS ARE NOW WORKING!');
              console.log('✅ Ava should now be able to detect and process SMS messages');
              
            } else {
              console.log(`ℹ️  Not an SMS (${subject})`);
            }
            console.log('---');
          }
        }

        lastCheckTime = now;

      } catch (error) {
        console.error(`❌ Error during check: ${error.message}`);
      }
    }, 10000); // Check every 10 seconds

    console.log('\n📱 Send your test SMS now...');
    console.log('🛑 Press Ctrl+C to stop monitoring');

    // Handle graceful shutdown
    process.on('SIGINT', () => {
      clearInterval(checkInterval);
      console.log('\n\n🛑 Monitor stopped');
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

liveMonitor().catch(console.error);
