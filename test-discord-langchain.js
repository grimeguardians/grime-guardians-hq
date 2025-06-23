/**
 * Test LangChain integration via Discord commands
 */

console.log('🎯 DISCORD LANGCHAIN INTEGRATION TEST');
console.log('='.repeat(50));
console.log('');
console.log('To test the LangChain agent in Discord:');
console.log('');
console.log('1. 📱 Open Discord and find the Ava bot');
console.log('2. 💬 Send a DM to the Ops Lead (you) with test messages:');
console.log('   • "I need to reschedule my appointment"');
console.log('   • "The cleaning was terrible yesterday"'); 
console.log('   • "How much for a 3 bedroom cleaning?"');
console.log('');
console.log('3. 🔍 Check the console logs for LangChain analysis');
console.log('4. ✅ Look for [langchain] agent output in the logs');
console.log('');
console.log('Expected output format:');
console.log('{');
console.log('  "agent_id": "ava_langchain",');
console.log('  "confidence": 0.85,');
console.log('  "message_type": "...",');
console.log('  "urgency_level": "...",');
console.log('  "requires_response": true');
console.log('}');
console.log('');
console.log('💡 Tip: The LangChain agent runs alongside other agents');
console.log('    and provides additional AI-powered analysis!');

