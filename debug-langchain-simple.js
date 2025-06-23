/**
 * Simple LangChain Debug Test
 */

const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');

async function simpleLangChainTest() {
  try {
    console.log('🔍 Starting simple LangChain test...');
    
    const agent = new GrimeGuardiansGmailAgent();
    console.log('✅ Agent created');
    
    await agent.initialize();
    console.log('✅ Agent initialized');
    
    // Test with minimal data
    const testMessage = {
      subject: 'Need cleaning quote',
      from: 'customer@test.com',
      body: 'How much for a 3 bedroom house cleaning?',
      timestamp: new Date().toISOString()
    };
    
    console.log('📧 Testing message:', testMessage.subject);
    
    const result = await agent.analyzeMessage(testMessage);
    
    console.log('📊 RESULT:');
    console.log('- Message Type:', result.message_type);
    console.log('- Urgency:', result.urgency_level);
    console.log('- Requires Response:', result.requires_response);
    console.log('- Confidence:', result.confidence);
    
    if (result.raw_analysis) {
      console.log('- Raw Analysis Length:', result.raw_analysis.length);
    }
    
    console.log('✅ Test completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
  
  process.exit(0);
}

simpleLangChainTest();
