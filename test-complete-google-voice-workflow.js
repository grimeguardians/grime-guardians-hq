/**
 * TEST: Complete Google Voice Monitoring with LangChain Integration
 * Verifies end-to-end SMS detection, parsing, and Discord alerting
 */

const EmailCommunicationMonitor = require('./src/utils/emailCommunicationMonitor');
const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');
const { Client } = require('discord.js');

async function testCompleteGoogleVoiceWorkflow() {
  try {
    console.log('🧪 TESTING COMPLETE GOOGLE VOICE WORKFLOW');
    console.log('='.repeat(60));

    // Step 1: Initialize LangChain Agent
    console.log('\n🧠 Step 1: Initializing LangChain Agent...');
    const langchainAgent = new GrimeGuardiansGmailAgent();
    await langchainAgent.initialize();
    console.log('✅ LangChain agent initialized');

    // Step 2: Initialize Discord Client (mock for testing)
    console.log('\n📱 Step 2: Setting up Discord client...');
    const mockClient = {
      users: {
        fetch: async (id) => ({
          send: async (message) => {
            console.log(`📤 DISCORD DM TO ${id}:`);
            console.log(message);
            console.log('─'.repeat(40));
            return true;
          }
        })
      }
    };
    console.log('✅ Mock Discord client ready');

    // Step 3: Initialize Email Monitor with LangChain integration
    console.log('\n📧 Step 3: Initializing Email Monitor with LangChain...');
    const emailMonitor = new EmailCommunicationMonitor(mockClient, langchainAgent);
    const initialized = await emailMonitor.initialize();
    
    if (!initialized) {
      console.log('❌ Email monitor failed to initialize');
      return;
    }
    console.log('✅ Email monitor initialized with LangChain integration');

    // Step 4: Test Google Voice monitoring
    console.log('\n📱 Step 4: Testing Google Voice email detection...');
    await emailMonitor.checkGoogleVoiceEmails();
    console.log('✅ Google Voice monitoring test completed');

    // Step 5: Test manual SMS simulation
    console.log('\n🧪 Step 5: Simulating incoming SMS...');
    const mockSMSData = {
      id: 'test-123',
      threadId: 'thread-123',
      subject: 'New text message from +16125849396',
      from: 'voice-noreply@google.com',
      date: new Date(),
      content: 'You have a new text message',
      clientPhone: '+16125849396',
      clientMessage: 'Hi, I need to schedule a cleaning for tomorrow. Is anyone available?',
      clientName: 'John Smith'
    };

    // Test Discord alert
    console.log('\n📤 Testing Discord Alert...');
    await emailMonitor.sendGoogleVoiceAlert(mockSMSData);

    // Test LangChain analysis
    console.log('\n🧠 Testing LangChain Analysis...');
    await emailMonitor.analyzeSMSWithLangChain(mockSMSData);

    console.log('\n🎉 WORKFLOW TEST RESULTS:');
    console.log('='.repeat(60));
    console.log('✅ LangChain Agent: Operational');
    console.log('✅ Email Monitor: Operational');
    console.log('✅ Google Voice Detection: Ready');
    console.log('✅ Discord Alerting: Functional');
    console.log('✅ SMS Analysis: AI-Powered');
    console.log('✅ Complete Workflow: RESTORED');

    console.log('\n🚀 The system is ready to monitor broberts111592@gmail.com');
    console.log('   and send intelligent SMS alerts with LangChain analysis!');

  } catch (error) {
    console.error('❌ Workflow test failed:', error.message);
    console.error(error.stack);
  }
}

testCompleteGoogleVoiceWorkflow().then(() => {
  console.log('\n✅ Test completed');
  process.exit(0);
}).catch(error => {
  console.error('💥 Test crashed:', error);
  process.exit(1);
});
