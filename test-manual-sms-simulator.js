/**
 * MANUAL SMS SIMULATOR - Force Discord alerts
 * Bypasses email checking and directly triggers Discord alerts
 */

require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const EmailCommunicationMonitor = require('./src/utils/emailCommunicationMonitor');
const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');

async function manualSMSSimulator() {
  try {
    console.log('📱 MANUAL SMS SIMULATOR - FORCE DISCORD ALERTS');
    console.log('='.repeat(60));

    // Initialize Discord
    const client = new Client({ 
      intents: [GatewayIntentBits.Guilds, GatewayIntentBits.DirectMessages] 
    });

    await new Promise((resolve, reject) => {
      client.once('ready', () => {
        console.log(`✅ Discord: ${client.user.tag}`);
        resolve();
      });
      client.login(process.env.DISCORD_BOT_TOKEN).catch(reject);
      setTimeout(() => reject(new Error('Timeout')), 5000);
    });

    // Initialize LangChain
    const langchainAgent = new GrimeGuardiansGmailAgent();
    await langchainAgent.initialize();
    console.log('✅ LangChain ready');

    // Create email monitor
    const emailMonitor = new EmailCommunicationMonitor(client, langchainAgent);
    console.log('✅ Email monitor created (no Gmail init needed for simulation)');

    // Test scenarios
    const testScenarios = [
      {
        name: '🚨 EMERGENCY',
        phone: '+16125849396',
        message: 'EMERGENCY! My pipes burst and there is water everywhere! Need cleaning crew NOW!',
        clientName: 'Panic Customer'
      },
      {
        name: '💰 SALES INQUIRY', 
        phone: '+16515151478',
        message: 'Hi! I need a quote for deep cleaning my 4 bedroom house. When are you available?',
        clientName: 'New Prospect'
      },
      {
        name: '😠 COMPLAINT',
        phone: '+17634567890', 
        message: 'I am NOT happy with the cleaning yesterday. Bathroom was still dirty and floors not mopped properly!',
        clientName: 'Angry Customer'
      },
      {
        name: '📅 SCHEDULING',
        phone: '+12345678901',
        message: 'Can I move my appointment from Tuesday to Thursday? Something came up at work.',
        clientName: 'Regular Client'
      },
      {
        name: '🔧 OPERATIONAL',
        phone: '+19876543210',
        message: 'Hi Brandon, this is Sarah. I arrived at the Johnson house but they are not home. What should I do?',
        clientName: 'Sarah (Cleaner)'
      }
    ];

    console.log(`\n🎭 Running ${testScenarios.length} SMS simulation scenarios...\n`);

    for (let i = 0; i < testScenarios.length; i++) {
      const scenario = testScenarios[i];
      
      console.log(`📱 ${i + 1}/${testScenarios.length}: ${scenario.name}`);
      console.log(`   From: ${scenario.clientName} (${scenario.phone})`);
      console.log(`   Message: "${scenario.message.substring(0, 50)}..."`);

      const smsData = {
        id: `sim-${Date.now()}-${i}`,
        threadId: `thread-${i}`,
        subject: `New text message from ${scenario.phone}`,
        from: 'voice-noreply@google.com',
        date: new Date(),
        content: `Google Voice notification: ${scenario.message}`,
        clientPhone: scenario.phone,
        clientMessage: scenario.message,
        clientName: scenario.clientName
      };

      try {
        // Send Discord alert
        console.log('   📤 Sending Discord alert...');
        await emailMonitor.sendGoogleVoiceAlert(smsData);

        // Analyze with LangChain
        console.log('   🧠 Running LangChain analysis...');
        await emailMonitor.analyzeSMSWithLangChain(smsData);

        console.log(`   ✅ ${scenario.name} simulation complete\n`);

      } catch (error) {
        console.log(`   ❌ ${scenario.name} failed:`, error.message);
      }

      // Wait 3 seconds between scenarios
      if (i < testScenarios.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    }

    console.log('🎉 ALL SIMULATIONS COMPLETED!');
    console.log('='.repeat(60));
    console.log('📱 Check your Discord DMs now!');
    console.log('🔍 You should see multiple SMS alerts and LangChain analyses');
    console.log(`📍 User ID: ${process.env.DISCORD_OPS_LEAD_ID}`);
    
    setTimeout(() => {
      client.destroy();
      process.exit(0);
    }, 5000);

  } catch (error) {
    console.error('❌ SMS simulation failed:', error.message);
    process.exit(1);
  }
}

manualSMSSimulator();
