#!/usr/bin/env node
/**
 * High Level SMS Reply Test
 * Tests sending a reply via High Level OAuth
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function testHighLevelReply() {
    console.log('📱 Testing High Level SMS Reply...\n');
    
    const hl = new HighLevelOAuth();
    
    try {
        // First, get recent conversations
        console.log('1️⃣ Getting recent conversations...');
        const conversations = await hl.getConversations({ limit: 5 });
        
        if (!conversations || conversations.length === 0) {
            console.log('❌ No conversations found. Cannot test reply functionality.');
            return;
        }
        
        console.log(`✅ Found ${conversations.length} conversations`);
        
        // Pick the most recent conversation
        const testConversation = conversations[0];
        console.log(`\n2️⃣ Testing with conversation: ${testConversation.id}`);
        console.log(`   Contact ID: ${testConversation.contactId}`);
        
        // Get recent messages for context
        console.log('\n3️⃣ Getting recent messages...');
        const messages = await hl.getMessages(testConversation.id, { limit: 3 });
        
        if (messages && messages.length > 0) {
            console.log(`✅ Found ${messages.length} messages`);
            const lastMessage = messages[0];
            console.log(`   Last message: "${lastMessage.body?.substring(0, 50)}..." (${lastMessage.direction})`);
        }
        
        // TEST REPLY (commented out for safety)
        console.log('\n4️⃣ Reply functionality test...');
        console.log('⚠️ Reply test disabled for safety. To enable:');
        console.log('   1. Uncomment the sendMessage call below');
        console.log('   2. Update the test message');
        console.log('   3. Ensure you have permission to send messages');
        
        /*
        // UNCOMMENT TO TEST ACTUAL REPLY
        const testReply = "This is a test message from the Grime Guardians automation system. Please ignore.";
        console.log(`\n🚀 Sending test reply: "${testReply}"`);
        
        const result = await hl.sendMessage(testConversation.contactId, testReply);
        
        if (result.success) {
            console.log('✅ Test reply sent successfully!');
            console.log(`   Message ID: ${result.messageId}`);
        } else {
            console.log(`❌ Reply failed: ${result.error}`);
        }
        */
        
        console.log('\n✅ High Level SMS integration test complete!');
        console.log('\n📋 Summary:');
        console.log(`   • OAuth Connection: ✅`);
        console.log(`   • Read Conversations: ✅ (${conversations.length} found)`);
        console.log(`   • Read Messages: ✅ (${messages?.length || 0} found)`);
        console.log(`   • Send Messages: ⚠️ (disabled for safety)`);
        
    } catch (error) {
        console.error('❌ High Level SMS test failed:', error.message);
        console.error('Stack:', error.stack);
    }
}

// Run the test
testHighLevelReply().catch(console.error);
