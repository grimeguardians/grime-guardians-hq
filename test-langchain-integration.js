/**
 * LangChain Integration Test
 * Tests the Gmail monitoring agent with LangChain integration
 */

const GrimeGuardiansGmailAgent = require('./src/agents/langchain/GrimeGuardiansGmailAgent');

async function testLangChainIntegration() {
    console.log('🧪 Testing LangChain Gmail Agent Integration...');
    
    try {
        const agent = new GrimeGuardiansGmailAgent();
        console.log('✅ Agent created successfully');
        
        // Test basic functionality
        const testResult = await agent.testConnection();
        console.log('✅ Connection test:', testResult ? 'PASSED' : 'FAILED');
        
        console.log('🎉 LangChain integration test completed');
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

if (require.main === module) {
    testLangChainIntegration();
}

module.exports = { testLangChainIntegration };
