#!/usr/bin/env node

/**
 * Test SMS Detection - Verify Google Voice SMS monitoring works
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function testSMSDetection() {
  console.log('🔍 TESTING SMS DETECTION');
  console.log('========================');

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

    // Search for "Me (SMS)" messages
    console.log('📧 Searching for "Me (SMS)" messages...');
    const query = 'from:voice-noreply@google.com subject:"Me (SMS)"';
    
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: 5
    });

    const count = messages.data.messages?.length || 0;
    console.log(`📊 Found ${count} "Me (SMS)" messages`);

    if (count === 0) {
      console.log('❌ No SMS messages found');
      console.log('💡 Try sending a test SMS to 612-584-9396');
      return;
    }

    // Analyze the most recent message
    console.log('\n📝 Analyzing most recent SMS...');
    const messageRef = messages.data.messages[0];
    const email = await gmail.users.messages.get({
      userId: 'me',
      id: messageRef.id
    });

    const headers = email.data.payload.headers;
    const subject = headers.find(h => h.name === 'Subject')?.value || '';
    const from = headers.find(h => h.name === 'From')?.value || '';
    const date = headers.find(h => h.name === 'Date')?.value || '';

    console.log(`📧 Subject: ${subject}`);
    console.log(`📧 From: ${from}`);
    console.log(`📧 Date: ${new Date(date).toLocaleString()}`);

    // Extract body
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

    console.log('\n📄 EMAIL CONTENT:');
    console.log('='.repeat(50));
    console.log(content);
    console.log('='.repeat(50));

    // Test parsing function
    console.log('\n🔍 TESTING PARSING LOGIC:');
    const parsed = parseGoogleVoiceContent(subject, content);
    console.log(`✅ Parsed result:`);
    console.log(`   📱 Phone: ${parsed.phone}`);
    console.log(`   👤 Name: ${parsed.name}`);
    console.log(`   💬 Message: "${parsed.message}"`);

    if (parsed.message && parsed.message.length > 0) {
      console.log('\n🎯 SUCCESS! SMS content extracted successfully');
      console.log('✅ Ava should be able to detect this message');
    } else {
      console.log('\n❌ PARSING FAILED - Message content not extracted');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

function parseGoogleVoiceContent(subject, content) {
  const result = { phone: null, message: null, name: null };

  console.log(`🔍 DEBUG: Parsing Google Voice - Subject: "${subject}"`);
  console.log(`🔍 DEBUG: Content preview: "${content.substring(0, 200)}..."`);

  // For "Me (SMS)" format, the phone number is in the content, not subject
  // Extract message content - Google Voice emails have specific format
  const lines = content.split('\n');
  console.log(`🔍 DEBUG: Content has ${lines.length} lines`);
  
  let messageContent = '';
  let senderInfo = '';
  
  // Look for the actual message content
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    console.log(`🔍 DEBUG: Line ${i}: "${line.substring(0, 50)}..."`);
    
    // Skip empty lines and URLs
    if (line === '' || line.startsWith('http') || line.includes('voice.google.com')) {
      continue;
    }
    
    // Look for sender signature (- Name format)
    if (line.startsWith('- ') && line.length < 50) {
      senderInfo = line.substring(2).trim();
      console.log(`🔍 DEBUG: Found sender info: "${senderInfo}"`);
      continue;
    }
    
    // Accumulate message content (skip URLs and footers)
    if (!line.includes('YOUR ACCOUNT') && 
        !line.includes('HELP CENTER') &&
        !line.includes('voice.google.com')) {
      messageContent += line + '\n';
    }
  }
  
  // Clean up message content
  result.message = messageContent.trim();
  result.name = senderInfo || 'Unknown';
  
  // Extract phone number from email headers or content if available
  // For now, we'll use the Google Voice number as the business number
  result.phone = '612-584-9396'; // This is our Google Voice number
  
  console.log(`🔍 DEBUG: Extracted message: "${result.message}"`);
  console.log(`🔍 DEBUG: Extracted sender: "${result.name}"`);
  console.log(`🔍 DEBUG: Phone number: "${result.phone}"`);

  return result;
}

testSMSDetection().catch(console.error);
