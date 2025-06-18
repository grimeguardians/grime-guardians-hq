/**
 * Test Message Classification Bug Fix
 * 
 * Tests the fixed messageClassifier.js to ensure operational messages
 * are properly classified and not returning 'undefined'
 */

const MessageClassifier = require('./src/utils/messageClassifier');

async function testClassification() {
  console.log('🧪 Testing Message Classification Fix');
  console.log('=====================================');
  
  const classifier = new MessageClassifier();
  
  const testMessages = [
    {
      message: "Hi, I need to reschedule my cleaning from Tuesday to Wednesday",
      expected: "reschedule_request"
    },
    {
      message: "I have a complaint about the cleaning quality yesterday",
      expected: "complaint"
    },
    {
      message: "Can you add carpet cleaning to my regular service?",
      expected: "operations"
    },
    {
      message: "Hi, I'm looking for a quote for weekly cleaning service",
      expected: "pricing_inquiry"
    },
    {
      message: "What time is my cleaning scheduled for tomorrow?",
      expected: "operations"
    }
  ];

  for (const test of testMessages) {
    try {
      console.log(`\n📨 Message: "${test.message}"`);
      
      const result = await classifier.classifyMessage(test.message);
      
      console.log(`✅ Result:`);
      console.log(`   Type: ${result.type}`);
      console.log(`   Confidence: ${result.confidence}`);
      console.log(`   Method: ${result.method}`);
      console.log(`   Expected: ${test.expected}`);
      
      // Check if result is valid
      if (!result.type || result.type === 'undefined') {
        console.log(`❌ FAILED: Classification returned undefined or null type`);
      } else if (result.type === test.expected) {
        console.log(`✅ PASSED: Correct classification`);
      } else {
        console.log(`⚠️  DIFFERENT: Got ${result.type}, expected ${test.expected}`);
      }
      
    } catch (error) {
      console.log(`❌ ERROR: ${error.message}`);
    }
  }
  
  console.log('\n🏁 Classification test complete');
}

// Run the test
testClassification().catch(console.error);
