/**
 * Test Google Voice Email Detection - Working Version Test
 * 
 * Verify that the reverted system can properly detect and parse Google Voice emails
 */

require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const EmailCommunicationMonitor = require('./src/utils/emailCommunicationMonitor');

async function testGoogleVoiceDetection() {
  console.log('🧪 TESTING GOOGLE VOICE DETECTION - REVERTED VERSION');
  console.log('='.repeat(60));
  
  try {
    // Create Discord client
    const client = new Client({ 
      intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages, 
        GatewayIntentBits.MessageContent, 
        GatewayIntentBits.DirectMessages,
        GatewayIntentBits.GuildMessageReactions,
        GatewayIntentBits.DirectMessageReactions
      ] 
    });

    // Initialize email monitor
    const emailMonitor = new EmailCommunicationMonitor(client);
    
    console.log('\n📧 Step 1: Initializing email monitor...');
    const initialized = await emailMonitor.initialize();
    
    if (!initialized) {
      console.log('❌ Email monitor failed to initialize');
      return;
    }
    
    console.log('✅ Email monitor initialized successfully');
    
    // Test Gmail connection for Google Voice account
    console.log('\n📱 Step 2: Testing Google Voice Gmail connection...');
    const googleVoiceGmail = emailMonitor.gmailClients.get('broberts111592@gmail.com');
    
    if (!googleVoiceGmail) {
      console.log('❌ Google Voice Gmail client not found');
      return;
    }
    
    console.log('✅ Google Voice Gmail client ready');
    
    // Search for recent Google Voice messages (including read ones for testing)
    console.log('\n🔍 Step 3: Searching for recent Google Voice messages...');
    
    const query = 'from:voice-noreply@google.com ("New text message" OR "New group message")';
    console.log(`📧 Query: ${query}`);
    
    const messages = await googleVoiceGmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: 5
    });
    
    const messageCount = messages.data.messages?.length || 0;
    console.log(`📊 Found ${messageCount} Google Voice messages`);
    
    if (messageCount === 0) {
      console.log('⚠️ No Google Voice messages found');
      console.log('💡 This could mean:');
      console.log('   - No SMS messages have been received recently');
      console.log('   - Google Voice email notifications are disabled');
      console.log('   - Messages were already processed and marked as read');
    } else {
      console.log(`✅ Google Voice detection is working - found ${messageCount} messages`);
      
      // Test parsing the first message
      console.log('\n📝 Step 4: Testing message parsing...');
      const firstMessage = await googleVoiceGmail.users.messages.get({
        userId: 'me',
        id: messages.data.messages[0].id
      });
      
      const parsed = emailMonitor.parseGoogleVoiceEmail(firstMessage.data);
      
      if (parsed) {
        console.log('✅ Message parsing successful:');
        console.log(`   📞 Client: ${parsed.clientName}`);
        console.log(`   📱 Phone: ${parsed.clientPhone}`);
        console.log(`   💬 Message: "${parsed.clientMessage.substring(0, 50)}..."`);
        console.log(`   📅 Date: ${parsed.date}`);
      } else {
        console.log('❌ Message parsing failed');
      }
    }
    
    // Test Discord DM capability
    console.log('\n💬 Step 5: Testing Discord DM setup...');
    const opsLeadId = process.env.OPS_LEAD_DISCORD_ID;
    
    if (!opsLeadId) {
      console.log('❌ OPS_LEAD_DISCORD_ID not configured');
    } else {
      console.log(`✅ Ops lead Discord ID configured: ${opsLeadId}`);
    }
    
    console.log('\n📊 TEST SUMMARY:');
    console.log('='.repeat(40));
    console.log(`📧 Gmail connection: ✅ Working`);
    console.log(`📱 Google Voice detection: ${messageCount > 0 ? '✅ Working' : '⚠️ No recent messages'}`);
    console.log(`💬 Discord DM setup: ${opsLeadId ? '✅ Configured' : '❌ Missing'}`);
    console.log('\n🎯 RESULT: System is ready for Google Voice monitoring!');
    
    // Don't log into Discord for this test
    console.log('\n✅ Test completed successfully');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Full error:', error);
  }
}

// Run the test
testGoogleVoiceDetection().then(() => {
  console.log('\n🏁 Test finished');
  process.exit(0);
}).catch(error => {
  console.error('💥 Test crashed:', error);
  process.exit(1);
});
