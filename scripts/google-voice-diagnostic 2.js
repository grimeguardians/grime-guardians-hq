#!/usr/bin/env node

/**
 * Google Voice Diagnostic Script
 * Checks ALL Gmail accounts for Google Voice emails to find the correct one
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function diagnosticGoogleVoice() {
  console.log('🔍 GOOGLE VOICE DIAGNOSTIC - Checking all Gmail accounts');
  console.log('========================================================');

  const emailAddresses = process.env.GMAIL_EMAILS ? process.env.GMAIL_EMAILS.split(',') : [];
  
  if (emailAddresses.length === 0) {
    console.log('❌ No Gmail emails configured in GMAIL_EMAILS');
    return;
  }

  for (const email of emailAddresses) {
    const trimmedEmail = email.trim();
    console.log(`\n📧 Checking ${trimmedEmail}...`);
    
    const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${trimmedEmail}.json`);
    
    if (!fs.existsSync(tokenFilePath)) {
      console.log(`❌ No token file for ${trimmedEmail}`);
      continue;
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

      // Search for ALL Google Voice emails (read and unread)
      console.log(`   🔍 Searching for Google Voice emails...`);
      const query = 'from:voice-noreply@google.com';
      
      const messages = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 20
      });

      const count = messages.data.messages?.length || 0;
      console.log(`   📊 Found ${count} Google Voice emails total`);

      if (count > 0) {
        // Check recent messages for SMS content
        console.log(`   📝 Analyzing recent messages...`);
        
        for (let i = 0; i < Math.min(3, count); i++) {
          const messageRef = messages.data.messages[i];
          const email = await gmail.users.messages.get({
            userId: 'me',
            id: messageRef.id
          });

          const headers = email.data.payload.headers;
          const subject = headers.find(h => h.name === 'Subject')?.value || '';
          const date = headers.find(h => h.name === 'Date')?.value || '';
          
          console.log(`     📧 ${new Date(date).toLocaleDateString()}: ${subject.substring(0, 60)}...`);
          
          // Check if this is an SMS notification
          if (subject.includes('SMS from')) {
            console.log(`     ✅ SMS NOTIFICATION FOUND!`);
            
            // Extract phone number
            const phoneMatch = subject.match(/SMS from (\+?\d{10,})/);
            if (phoneMatch) {
              console.log(`     📱 Phone: ${phoneMatch[1]}`);
            }
          }
        }

        // Check for unread messages specifically
        const unreadQuery = 'from:voice-noreply@google.com is:unread';
        const unreadMessages = await gmail.users.messages.list({
          userId: 'me',
          q: unreadQuery,
          maxResults: 5
        });

        const unreadCount = unreadMessages.data.messages?.length || 0;
        console.log(`   📬 Unread Google Voice emails: ${unreadCount}`);

        if (unreadCount > 0) {
          console.log(`   🎯 THIS ACCOUNT HAS UNREAD GOOGLE VOICE MESSAGES!`);
        }
      }

    } catch (error) {
      console.log(`   ❌ Error checking ${trimmedEmail}: ${error.message}`);
    }
  }

  console.log('\n🎯 RECOMMENDATION:');
  console.log('1. Send a test SMS to 612-584-9396');
  console.log('2. Check which Gmail account receives the notification');
  console.log('3. Update the code to use that specific account');
}

diagnosticGoogleVoice().catch(console.error);
