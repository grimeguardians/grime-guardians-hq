const MessageClassifier = require('./src/utils/messageClassifier');

async function forceGPTTest() {
  console.log('🧪 Force GPT Test (Bypassing Rule-Based)');
  console.log('=' .repeat(40));
  
  const classifier = new MessageClassifier();
  
  // Test ambiguous messages that need GPT reasoning
  const ambiguousMessages = [
    "Hello, I have a question about your services.",
    "My place needs some work but I'm not sure about timing.",
    "I heard good things about you from a neighbor.",
  ];
  
  for (const message of ambiguousMessages) {
    console.log(`\n📝 Testing: "${message}"`);
    
    try {
      // Force GPT by directly calling gptClassify
      const result = await classifier.gptClassify(message, {});
      
      console.log(`✅ GPT-4o-mini Response:`);
      console.log(`   Category: ${result.category}`);
      console.log(`   Confidence: ${Math.round(result.confidence * 100)}%`);
      console.log(`   Reasoning: ${result.reasoning}`);
      console.log(`🎉 GPT is working with your $10 credit!`);
      
      break; // One successful test is enough
      
    } catch (error) {
      console.log(`❌ Error: ${error.message}`);
      
      if (error.message.includes('429')) {
        console.log('💡 Rate limit hit - this is normal, try again later');
      } else if (error.message.includes('401')) {
        console.log('💡 Check your OpenAI API key in .env file');
      } else {
        console.log('💡 Other error - but billing is likely working');
      }
    }
  }
}

forceGPTTest();
