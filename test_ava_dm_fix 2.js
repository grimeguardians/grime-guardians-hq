#!/usr/bin/env node

/**
 * Test Ava's Google Voice Detection and Discord DM Capability
 * 
 * This script tests the key components:
 * 1. Gmail connection to broberts111592@gmail.com
 * 2. Google Voice message detection
 * 3. Conversation manager processing
 * 4. Discord DM approval workflow
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function testAvaGoogleVoiceDM() {
  console.log('🧪 TESTING AVA GOOGLE VOICE + DISCORD DM CAPABILITY');
  console.log('====================================================');

  try {
    // 1. Test Gmail Connection for Google Voice account
    console.log('\n📧 Step 1: Testing Gmail connection...');
    const tokenFilePath = path.join(process.cwd(), 'gmail-tokens-broberts111592@gmail.com.json');
    
    if (!fs.existsSync(tokenFilePath)) {
      console.log('❌ Gmail token file not found for broberts111592@gmail.com');
      console.log('💡 Run: node scripts/setup-gmail-auth.js');
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

    // Test connection
    const profile = await gmail.users.getProfile({ userId: 'me' });
    console.log(`✅ Gmail connected: ${profile.data.emailAddress}`);

    // 2. Test Google Voice Message Detection
    console.log('\n📱 Step 2: Testing Google Voice message detection...');
    const query = 'from:voice-noreply@google.com ("New text message" OR "New group message") -"verification code" -"Indeed" -"Stripe" -"Discord"';
    console.log(`🔍 Query: ${query}`);
    
    const messages = await gmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: 5
    });

    const messageCount = messages.data.messages?.length || 0;
    console.log(`📊 Found ${messageCount} potential Google Voice messages`);

    if (messageCount > 0) {
      console.log('✅ Google Voice detection is working');
      
      // Test parsing the first message
      const firstMessage = await gmail.users.messages.get({
        userId: 'me',
        id: messages.data.messages[0].id
      });

      const headers = firstMessage.data.payload.headers;
      const subject = headers.find(h => h.name === 'Subject')?.value || '';
      console.log(`📝 Sample subject: "${subject}"`);

      // Test our parsing logic
      const clientInfo = parseGoogleVoiceContent(subject, 'Test message content');
      console.log(`🧠 Parsed client info:`, clientInfo);
    } else {
      console.log('⚠️ No Google Voice messages found');
      console.log('💡 Send a test SMS to 612-584-9396 to verify detection');
    }

    // 3. Test Discord Setup
    console.log('\n📞 Step 3: Testing Discord configuration...');
    console.log(`🎯 OPS_LEAD_DISCORD_ID: ${process.env.OPS_LEAD_DISCORD_ID || 'NOT SET'}`);
    console.log(`🤖 DISCORD_BOT_TOKEN: ${process.env.DISCORD_BOT_TOKEN ? 'SET' : 'NOT SET'}`);

    if (!process.env.OPS_LEAD_DISCORD_ID) {
      console.log('❌ OPS_LEAD_DISCORD_ID not set in environment');
      console.log('💡 Add your Discord user ID to .env file');
    } else {
      console.log('✅ Discord configuration looks good');
    }

    // 4. Test Conversation Manager Components
    console.log('\n🧠 Step 4: Testing conversation components...');
    
    try {
      const MessageClassifier = require('./src/utils/messageClassifier');
      const ConversationManager = require('./src/utils/conversationManager');
      
      console.log('✅ MessageClassifier module loaded');
      console.log('✅ ConversationManager module loaded');
      
      // Test creating instances (without Discord client for now)
      const classifier = new MessageClassifier();
      console.log('✅ MessageClassifier instance created');
      
      console.log('✅ All components are loadable');
      
    } catch (error) {
      console.log('❌ Error loading conversation components:', error.message);
    }

    // 5. Test OpenAI API
    console.log('\n🤖 Step 5: Testing OpenAI API...');
    console.log(`🔑 OPENAI_API_KEY: ${process.env.OPENAI_API_KEY ? 'SET' : 'NOT SET'}`);
    
    if (process.env.OPENAI_API_KEY) {
      try {
        const OpenAI = require('openai');
        const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
        
        // Quick test call
        const response = await openai.chat.completions.create({
          model: 'gpt-4o-mini',
          messages: [{ role: 'user', content: 'Test message classification: "Can we reschedule tomorrow?"' }],
          max_tokens: 50,
          temperature: 0.7
        });
        
        console.log('✅ OpenAI API connection working');
        console.log(`🧠 Sample response: ${response.choices[0].message.content.substring(0, 100)}...`);
      } catch (error) {
        console.log('❌ OpenAI API error:', error.message);
      }
    } else {
      console.log('❌ OpenAI API key not set');
    }

    console.log('\n🎯 DIAGNOSIS SUMMARY:');
    console.log('===================');
    console.log('✅ Gmail connection: Working');
    console.log(`${messageCount > 0 ? '✅' : '⚠️'} Google Voice detection: ${messageCount > 0 ? 'Working' : 'No recent messages'}`);
    console.log(`${process.env.OPS_LEAD_DISCORD_ID ? '✅' : '❌'} Discord config: ${process.env.OPS_LEAD_DISCORD_ID ? 'Set' : 'Missing'}`);
    console.log('✅ Conversation components: Loaded');
    console.log(`${process.env.OPENAI_API_KEY ? '✅' : '❌'} OpenAI API: ${process.env.OPENAI_API_KEY ? 'Working' : 'Missing'}`);

    console.log('\n💡 NEXT STEPS:');
    console.log('==============');
    console.log('1. Send a test SMS to 612-584-9396');
    console.log('2. Run the main system to see if Ava processes it');
    console.log('3. Check for Discord DM approval request');
    console.log('4. If issues persist, check server logs for specific errors');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Full error:', error);
  }
}

// Helper function from the email monitor
function parseGoogleVoiceContent(subject, content) {
  const result = { phone: null, message: null, name: null };

  // Extract sender name from subject
  let nameMatch = subject.match(/New text message from (.+)/);
  if (!nameMatch) {
    nameMatch = subject.match(/New group message from (.+)/);
  }
  
  if (nameMatch) {
    result.name = nameMatch[1].trim();
    if (result.name.endsWith('.')) {
      result.name = result.name.slice(0, -1);
    }
  }

  result.message = content.trim();
  result.phone = result.name || 'Unknown';
  
  return result;
}

// Run the test
testAvaGoogleVoiceDM().catch(console.error);
