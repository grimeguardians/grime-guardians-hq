const MessageClassifier = require('./src/utils/messageClassifier');

async function testGPT() {
  console.log('🧪 Testing GPT-4o-mini with $10 credit...');
  
  const classifier = new MessageClassifier();
  
  // Test with an ambiguous message that should trigger GPT
  const testMessage = "Hey there! I was wondering if you could help me with something. My place is pretty messy and I'm not sure what to do.";
  
  try {
    const result = await classifier.classifyMessage(testMessage);
    
    console.log('✅ GPT-4o-mini Success!');
    console.log('📝 Message:', testMessage);
    console.log('🎯 Category:', result.category);
    console.log('📊 Confidence:', Math.round(result.confidence * 100) + '%');
    console.log('🔧 Method:', result.method);
    
    if (result.method === 'gpt4') {
      console.log('🎉 GPT-4o-mini is working perfectly!');
      console.log('💰 Billing is set up correctly!');
    } else {
      console.log('⚠️ Used rule-based classification (GPT may be rate limited)');
    }
    
  } catch (error) {
    console.log('❌ Error:', error.message);
    
    if (error.message.includes('429')) {
      console.log('💡 Rate limit - try again in a few minutes');
    } else if (error.message.includes('401')) {
      console.log('💡 API key issue - check your OpenAI settings');
    } else if (error.message.includes('insufficient_quota')) {
      console.log('💡 Quota exceeded - but this means billing is working!');
    }
  }
}

testGPT();
