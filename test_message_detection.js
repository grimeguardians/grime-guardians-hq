#!/usr/bin/env node
/**
 * Test High Level Message Detection with Recent Messages
 * This script simulates the message detection logic with a broader time window for testing
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function testMessageDetection() {
    console.log('🧪 Testing High Level Message Detection Logic\n');
    
    const hl = new HighLevelOAuth();
    
    try {
        // Get conversations
        const conversations = await hl.getConversations({ limit: 10 });
        console.log(`📱 Found ${conversations.length} High Level conversations`);
        
        // Look for messages in the last 30 minutes (for testing)
        const thirtyMinutesAgo = new Date(Date.now() - 30 * 60 * 1000);
        console.log(`🕐 Looking for messages after: ${thirtyMinutesAgo.toISOString()}`);
        
        const processedIds = new Set(); // Simulate processed message tracking
        const recentConversations = [];
        let totalNewMessages = 0;
        
        for (const conversation of conversations) {
            console.log(`\n🔍 Checking conversation: ${conversation.contactName || conversation.fullName} (${conversation.id})`);
            
            try {
                const messages = await hl.getMessages(conversation.id, { limit: 10 });
                console.log(`   📨 Found ${messages.length} messages in conversation`);
                
                if (messages && messages.length > 0) {
                    // Find recent inbound messages
                    const recentMessages = messages.filter(msg => {
                        const messageDate = new Date(msg.dateAdded);
                        const isRecent = messageDate > thirtyMinutesAgo;
                        const isInbound = msg.direction === 'inbound';
                        const isUnprocessed = !processedIds.has(msg.id);
                        
                        console.log(`      🔸 Message: "${msg.body?.substring(0, 50)}..."`);
                        console.log(`         Time: ${messageDate.toISOString()}`);
                        console.log(`         Direction: ${msg.direction}`);
                        console.log(`         Recent: ${isRecent}, Inbound: ${isInbound}, Unprocessed: ${isUnprocessed}`);
                        
                        return isRecent && isInbound && isUnprocessed;
                    });
                    
                    if (recentMessages.length > 0) {
                        console.log(`   ✅ Found ${recentMessages.length} new inbound messages!`);
                        recentMessages.forEach(msg => {
                            console.log(`      📱 NEW: "${msg.body}"`);
                            console.log(`          From: ${conversation.contactName || conversation.fullName}`);
                            console.log(`          Phone: ${conversation.phone}`);
                            console.log(`          Time: ${new Date(msg.dateAdded).toLocaleString()}`);
                        });
                        
                        conversation.newMessages = recentMessages;
                        recentConversations.push(conversation);
                        totalNewMessages += recentMessages.length;
                    } else {
                        console.log(`   ⚪ No new messages in this conversation`);
                    }
                }
            } catch (msgError) {
                console.error(`   ❌ Error getting messages: ${msgError.message}`);
            }
        }
        
        console.log(`\n📊 SUMMARY:`);
        console.log(`   📱 Total conversations checked: ${conversations.length}`);
        console.log(`   🔥 Conversations with new messages: ${recentConversations.length}`);
        console.log(`   📨 Total new messages found: ${totalNewMessages}`);
        
        if (recentConversations.length > 0) {
            console.log(`\n🎯 WOULD TRIGGER PROCESSING FOR:`);
            recentConversations.forEach((conv, idx) => {
                console.log(`   ${idx + 1}. ${conv.contactName || conv.fullName} - ${conv.newMessages.length} message(s)`);
            });
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        console.error('Stack:', error.stack);
    }
}

// Run the test
testMessageDetection().catch(console.error);
