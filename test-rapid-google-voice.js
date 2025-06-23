/**
 * RAPID TESTING - 10-second intervals for Google Voice
 * For super fast testing and debugging
 */

require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const EmailCommunicationMonitor = require('./src/utils/emailCommunicationMonitor');
const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');

async function rapidTesting() {
  try {
    console.log('⚡ RAPID TESTING MODE - 10 SECOND INTERVALS');
    console.log('='.repeat(60));

    // Initialize Discord
    const client = new Client({ 
      intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.DirectMessages
      ] 
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

    // Initialize Email Monitor
    const emailMonitor = new EmailCommunicationMonitor(client, langchainAgent);
    await emailMonitor.initialize();
    console.log('✅ Email monitor ready');

    // Override the monitoring intervals for rapid testing
    console.log('\n⚡ OVERRIDING TO 10-SECOND INTERVALS');
    
    let checkCount = 0;
    const rapidInterval = setInterval(async () => {
      checkCount++;
      console.log(`\n🔍 Rapid Check #${checkCount} - ${new Date().toLocaleTimeString()}`);
      
      try {
        await emailMonitor.checkGoogleVoiceEmails();
        console.log(`✅ Check #${checkCount} completed`);
      } catch (error) {
        console.log(`❌ Check #${checkCount} failed:`, error.message);
      }
      
      // Stop after 20 checks (200 seconds)
      if (checkCount >= 20) {
        console.log('\n🛑 Rapid testing completed');
        clearInterval(rapidInterval);
        client.destroy();
        process.exit(0);
      }
    }, 10000); // 10 seconds

    console.log('📱 Monitoring Google Voice emails every 10 seconds');
    console.log('💡 Send yourself an SMS now to test!');
    console.log('⏰ Will run for 200 seconds (20 checks)');

    // Initial check
    await emailMonitor.checkGoogleVoiceEmails();

  } catch (error) {
    console.error('❌ Rapid test failed:', error.message);
    process.exit(1);
  }
}

rapidTesting();
