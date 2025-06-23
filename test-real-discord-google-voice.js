/**
 * REAL DISCORD TESTING - Google Voice Workflow
 * This will actually send Discord messages to test the complete workflow
 */

require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const EmailCommunicationMonitor = require('./src/utils/emailCommunicationMonitor');
const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');

async function realDiscordTest() {
  try {
    console.log('🔥 REAL DISCORD TESTING - GOOGLE VOICE WORKFLOW');
    console.log('='.repeat(60));

    // Step 1: Initialize Real Discord Client
    console.log('\n📱 Step 1: Connecting to Discord...');
    const client = new Client({ 
      intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages, 
        GatewayIntentBits.MessageContent, 
        GatewayIntentBits.DirectMessages
      ] 
    });

    await new Promise((resolve, reject) => {
      client.once('ready', () => {
        console.log(`✅ Discord connected as ${client.user.tag}`);
        resolve();
      });
      
      client.on('error', reject);
      
      client.login(process.env.DISCORD_BOT_TOKEN).catch(reject);
      
      // Timeout after 10 seconds
      setTimeout(() => reject(new Error('Discord login timeout')), 10000);
    });

    // Step 2: Initialize LangChain Agent
    console.log('\n🧠 Step 2: Initializing LangChain Agent...');
    const langchainAgent = new GrimeGuardiansGmailAgent();
    await langchainAgent.initialize();
    console.log('✅ LangChain agent ready');

    // Step 3: Initialize Email Monitor with Real Discord
    console.log('\n📧 Step 3: Initializing Email Monitor with Real Discord...');
    const emailMonitor = new EmailCommunicationMonitor(client, langchainAgent);
    
    // Test 1: Check Gmail Connection
    console.log('\n🔌 Test 1: Checking Gmail connections...');
    const initialized = await emailMonitor.initialize();
    if (!initialized) {
      console.log('❌ Email monitor failed to initialize');
      return;
    }
    console.log('✅ All Gmail accounts connected');

    // Test 2: Test Real Google Voice Email Check
    console.log('\n📱 Test 2: Checking for REAL Google Voice emails...');
    await emailMonitor.checkGoogleVoiceEmails();
    console.log('✅ Real Google Voice check completed');

    // Test 3: Simulate SMS and Send REAL Discord Alert
    console.log('\n🚨 Test 3: Sending REAL Discord alerts...');
    
    const testSMSMessages = [
      {
        id: 'test-urgent-001',
        clientPhone: '+16125849396',
        clientMessage: 'URGENT: Need emergency cleaning! Water damage in my kitchen, need help ASAP!',
        clientName: 'Sarah Emergency',
        date: new Date()
      },
      {
        id: 'test-sales-002', 
        clientPhone: '+16515151478',
        clientMessage: 'Hi! I need a quote for weekly cleaning of my 3 bedroom house. When can you come?',
        clientName: 'Mike NewCustomer',
        date: new Date()
      },
      {
        id: 'test-schedule-003',
        clientPhone: '+17634567890',
        clientMessage: 'Can I reschedule my appointment from tomorrow to next week? Something came up.',
        clientName: 'Lisa Regular',
        date: new Date()
      }
    ];

    for (let i = 0; i < testSMSMessages.length; i++) {
      const sms = testSMSMessages[i];
      console.log(`\n📤 Sending test message ${i + 1}/3: ${sms.clientName}`);
      
      // Send Discord alert
      await emailMonitor.sendGoogleVoiceAlert(sms);
      
      // Analyze with LangChain and send enhanced alert
      await emailMonitor.analyzeSMSWithLangChain(sms);
      
      // Wait 2 seconds between messages
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    console.log('\n🎉 REAL DISCORD TEST RESULTS:');
    console.log('='.repeat(60));
    console.log('✅ Discord Bot Connected');
    console.log('✅ Gmail Monitoring Active');  
    console.log('✅ LangChain Analysis Working');
    console.log('✅ REAL Discord Messages Sent');
    console.log('✅ Check your Discord DMs now!');

    console.log(`\n📱 Check Discord DMs for user ID: ${process.env.DISCORD_OPS_LEAD_ID}`);
    console.log('🔍 You should see 3 test SMS alerts + 3 LangChain analysis messages');

    // Wait 5 seconds then start monitoring
    console.log('\n⏰ Starting 1-minute monitoring in 5 seconds...');
    setTimeout(async () => {
      console.log('🚀 Starting rapid monitoring (1-minute intervals)...');
      await emailMonitor.startMonitoring();
      console.log('📱 Now monitoring for REAL Google Voice emails every 1 minute');
      console.log('💡 Send yourself an SMS to test live monitoring!');
    }, 5000);

    // Keep running for 10 minutes for testing
    setTimeout(() => {
      console.log('\n⏹️  Test completed - shutting down...');
      client.destroy();
      process.exit(0);
    }, 10 * 60 * 1000); // 10 minutes

  } catch (error) {
    console.error('❌ Real Discord test failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

realDiscordTest();
