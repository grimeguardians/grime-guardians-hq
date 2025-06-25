#!/usr/bin/env node

/**
 * Debug Gmail Query - Find all recent messages to debug search
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function debugGmailQuery() {
  console.log('🔍 DEBUGGING GMAIL SEARCH');
  console.log('=========================');

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

    // Get recent messages from Google Voice
    console.log('📧 Getting recent Google Voice messages...');
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: 'from:voice-noreply@google.com',
      maxResults: 10
    });

    if (!messages.data.messages) {
      console.log('❌ No Google Voice messages found');
      return;
    }

    console.log(`📊 Found ${messages.data.messages.length} recent Google Voice messages`);
    
    // Check each message's subject
    for (let i = 0; i < Math.min(5, messages.data.messages.length); i++) {
      const messageRef = messages.data.messages[i];
      const email = await gmail.users.messages.get({
        userId: 'me',
        id: messageRef.id
      });

      const headers = email.data.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';
      
      console.log(`\n📧 Message ${i + 1}:`);
      console.log(`   📅 Date: ${new Date(date).toLocaleDateString()}`);
      console.log(`   📝 Subject: "${subject}"`);
      
      if (subject.includes('SMS') || subject.includes('Me (')) {
        console.log(`   🎯 POTENTIAL SMS MESSAGE FOUND!`);
        
        // Get content
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
        
        console.log(`   📄 Content preview: "${content.substring(0, 100)}..."`);
      }
    }

    // Try different search queries
    console.log('\n🔍 TESTING DIFFERENT SEARCH QUERIES:');
    
    const queries = [
      'from:voice-noreply@google.com subject:"Me (SMS)"',
      'from:voice-noreply@google.com subject:Me',
      'from:voice-noreply@google.com SMS',
      'from:voice-noreply@google.com "reschedule"',
      'from:voice-noreply@google.com "Barron"'
    ];

    for (const query of queries) {
      console.log(`\n🔍 Query: ${query}`);
      try {
        const result = await gmail.users.messages.list({
          userId: 'me',
          q: query,
          maxResults: 3
        });
        const count = result.data.messages?.length || 0;
        console.log(`   📊 Results: ${count} messages`);
      } catch (error) {
        console.log(`   ❌ Error: ${error.message}`);
      }
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

debugGmailQuery().catch(console.error);
