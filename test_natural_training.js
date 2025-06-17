/**
 * Test Natural Language Training System
 * Shows how Brandon/Lena can train Ava conversationally
 */

require('dotenv').config();
const AvaTrainingSystem = require('./src/utils/avaTrainingSystem');

async function testNaturalLanguageTraining() {
  console.log('🗣️ Testing Natural Language Training');
  console.log('=' .repeat(50));

  // Mock Discord client for testing
  const mockClient = {
    users: {
      fetch: () => ({ username: 'TestUser' })
    }
  };

  const trainingSystem = new AvaTrainingSystem(mockClient);

  // Simulate a recent classification that was wrong
  trainingSystem.logClassification('msg_test_123', 
    'Hi, I need to cancel my cleaning tomorrow due to illness',
    { category: 'new_prospect', confidence: 0.85 }
  );

  console.log('\n🧠 Recent Classification Logged:');
  console.log('Message: "Hi, I need to cancel my cleaning tomorrow due to illness"');
  console.log('Ava\'s Classification: new_prospect (85%)');
  console.log('Status: ❌ WRONG - This is clearly a cancellation!');

  console.log('\n💬 Natural Language Training Examples:');
  console.log('-'.repeat(40));

  const naturalFeedback = [
    "Thank you Ava! This happens to be a cancellation request, not for a new prospect. You can tell by them using the words 'cancel my clean tomorrow'.",
    
    "Ava, this is actually a schedule change because they want to cancel their appointment.",
    
    "This should be classified as a complaint - the customer is clearly upset about the service quality.",
    
    "Actually Ava, this is a new prospect asking for a quote. Look for keywords like 'interested in' and 'pricing'."
  ];

  for (let i = 0; i < naturalFeedback.length; i++) {
    const feedback = naturalFeedback[i];
    console.log(`\n${i + 1}. Human Says:`);
    console.log(`   "${feedback}"`);
    
    try {
      const correction = await trainingSystem.extractCorrectionFromNaturalLanguage(feedback);
      
      if (correction) {
        console.log(`✅ Ava Understands:`);
        console.log(`   Category: ${correction.correctCategory}`);
        console.log(`   Reasoning: ${correction.reasoning}`);
        console.log(`   Key Indicators: ${correction.keyIndicators.join(', ')}`);
      } else {
        console.log(`❌ Not recognized as training feedback`);
      }
    } catch (error) {
      console.log(`⚠️ Error: ${error.message}`);
    }
  }

  console.log('\n🎯 Training Flow Comparison');
  console.log('=' .repeat(50));
  
  console.log('\n❌ OLD WAY (Complex):');
  console.log('1. !train review');
  console.log('2. Find message ID: msg_1750132088006');
  console.log('3. !train correct msg_1750132088006 schedule_change This is a cancellation');
  console.log('4. Remember exact syntax and message IDs');

  console.log('\n✅ NEW WAY (Natural):');
  console.log('1. Just talk to Ava naturally in DM:');
  console.log('   "Ava, this is actually a cancellation, not a new prospect"');
  console.log('2. Ava automatically understands and learns');
  console.log('3. No commands, no IDs, no syntax to remember');

  console.log('\n🚀 Benefits of Natural Language Training:');
  console.log('• Talk to Ava like a human team member');
  console.log('• No memorizing commands or message IDs');
  console.log('• Explain reasoning in your own words');
  console.log('• Ava learns context and key indicators');
  console.log('• Much faster and more intuitive');

  console.log('\n💡 Example Conversations:');
  console.log('"Ava, you got this wrong - this is clearly a complaint"');
  console.log('"This should be a new prospect, they\'re asking for pricing"');
  console.log('"Actually this is a schedule change, they want to reschedule"');
  console.log('"This is spam, ignore messages like this in the future"');

  console.log('\n✅ Natural Language Training Ready!');
}

testNaturalLanguageTraining().catch(console.error);
