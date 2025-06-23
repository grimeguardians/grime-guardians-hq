/**
 * Direct LangChain Agent Test
 * Tests the Gmail agent with various message scenarios
 */

require('dotenv').config();
const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');

async function testLangChainAgent() {
  console.log('🧪 TESTING LANGCHAIN AGENT FUNCTIONALITY');
  console.log('='.repeat(50));
  
  try {
    // Initialize agent
    const agent = new GrimeGuardiansGmailAgent();
    await agent.initialize();
    console.log('✅ Agent initialized successfully\n');
    
    // Test scenarios
    const testCases = [
      {
        name: "Customer Service Inquiry",
        messageData: {
          subject: "Reschedule Request",
          from: "test_customer@email.com",
          body: "Hi, I need to reschedule my cleaning appointment for tomorrow to next week",
          timestamp: new Date().toISOString()
        }
      },
      {
        name: "Sales Inquiry",  
        messageData: {
          subject: "Pricing Question",
          from: "potential_client@email.com", 
          body: "How much do you charge for a 3 bedroom house cleaning?",
          timestamp: new Date().toISOString()
        }
      },
      {
        name: "Complaint",
        messageData: {
          subject: "Service Complaint",
          from: "upset_customer@email.com",
          body: "I'm not happy with the cleaning service yesterday. The bathroom wasn't cleaned properly.",
          timestamp: new Date().toISOString()
        }
      },
      {
        name: "Check-in Message",
        messageData: {
          subject: "Arrived at Job Site",
          from: "cleaner_sarah@grimeguardians.com",
          body: "Hi, I'm at the Johnson residence and ready to start cleaning. Everything looks good.",
          timestamp: new Date().toISOString()
        }
      },
      {
        name: "Operational Question",
        messageData: {
          subject: "Supply Question",
          from: "cleaner_mike@grimeguardians.com",
          body: "What supplies should I bring for today's deep clean at 123 Main St?",
          timestamp: new Date().toISOString()
        }
      }
    ];
    
    // Run test cases
    for (let i = 0; i < testCases.length; i++) {
      const testCase = testCases[i];
      console.log(`📋 TEST ${i + 1}: ${testCase.name}`);
      console.log(`💬 Message: "${testCase.messageData.body}"`);
      console.log(`👤 From: ${testCase.messageData.from}`);
      
      try {
        const result = await agent.analyzeMessage(testCase.messageData);
        console.log(`🤖 Analysis:`, JSON.stringify(result, null, 2));
        console.log(`⭐ Confidence: ${result.confidence || 'N/A'}`);
        console.log('─'.repeat(40));
      } catch (error) {
        console.error(`❌ Test failed:`, error.message);
      }
      
      // Wait between tests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('🎉 LangChain agent testing completed!');
    
  } catch (error) {
    console.error('❌ Testing failed:', error);
  }
}

testLangChainAgent().then(() => {
  console.log('\n✅ Test script completed');
  process.exit(0);
}).catch(error => {
  console.error('💥 Test script crashed:', error);
  process.exit(1);
});
