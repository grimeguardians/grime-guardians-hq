#!/usr/bin/env node

/**
 * Google Voice SMS Pattern Analysis
 * Finds actual SMS notification patterns in Google Voice emails
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function analyzeSMSPatterns() {
  console.log('🔍 ANALYZING GOOGLE VOICE SMS PATTERNS');
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

    // Get ALL Google Voice emails and analyze subjects
    console.log('📧 Getting recent Google Voice emails...');
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: 'from:voice-noreply@google.com',
      maxResults: 50
    });

    if (!messages.data.messages) {
      console.log('❌ No messages found');
      return;
    }

    console.log(`📊 Found ${messages.data.messages.length} Google Voice emails`);
    console.log('\n📝 SUBJECT LINE PATTERNS:');
    console.log('=' .repeat(60));

    const subjectPatterns = new Map();
    
    for (const messageRef of messages.data.messages) {
      const email = await gmail.users.messages.get({
        userId: 'me',
        id: messageRef.id
      });

      const headers = email.data.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      const date = headers.find(h => h.name === 'Date')?.value || '';
      
      // Categorize by subject pattern
      let category = 'OTHER';
      if (subject.includes('SMS from') || subject.includes('text message')) {
        category = 'SMS';
      } else if (subject.includes('missed call')) {
        category = 'MISSED_CALL';
      } else if (subject.includes('voicemail')) {
        category = 'VOICEMAIL';
      }

      if (!subjectPatterns.has(category)) {
        subjectPatterns.set(category, []);
      }
      
      subjectPatterns.get(category).push({
        subject,
        date: new Date(date).toLocaleDateString()
      });
    }

    // Display patterns
    for (const [category, messages] of subjectPatterns) {
      console.log(`\n📋 ${category} (${messages.length} messages):`);
      messages.slice(0, 5).forEach(msg => {
        console.log(`   ${msg.date}: ${msg.subject}`);
      });
      if (messages.length > 5) {
        console.log(`   ... and ${messages.length - 5} more`);
      }
    }

    // Check for SMS specifically
    const smsCount = subjectPatterns.get('SMS')?.length || 0;
    console.log(`\n🎯 RESULT: Found ${smsCount} SMS notifications`);
    
    if (smsCount === 0) {
      console.log('⚠️  NO SMS NOTIFICATIONS FOUND!');
      console.log('💡 This means:');
      console.log('   1. Google Voice SMS → Email notifications might be disabled');
      console.log('   2. SMS notifications might use a different subject pattern');
      console.log('   3. SMS might be going to a different email account');
      console.log('\n🚨 ACTION REQUIRED: Send a test SMS to 612-584-9396 and check email!');
    } else {
      console.log('✅ SMS notifications found - checking patterns...');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

analyzeSMSPatterns().catch(console.error);
