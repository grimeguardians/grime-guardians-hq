#!/usr/bin/env node
/**
 * Debug High Level Conversations - Detailed Data Dump
 * This script shows detailed conversation and message data to help debug message detection
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function debugConversations() {
    console.log('🔍 High Level Conversations Debug Tool\n');
    
    const hl = new HighLevelOAuth();
    
    try {
        // 1. Get all conversations
        console.log('1️⃣ Fetching all conversations...');
        const conversations = await hl.getConversations({ limit: 10 });
        console.log(`Found ${conversations.length} conversations\n`);
        
        // 2. Show sample conversation structure
        if (conversations.length > 0) {
            console.log('2️⃣ Sample conversation structure:');
            console.log('===============================');
            const sample = conversations[0];
            console.log('Sample conversation keys:', Object.keys(sample));
            console.log('Sample conversation data:');
            console.log(JSON.stringify(sample, null, 2));
            console.log('\n');
        }
        
        // 3. Check recent conversations for messages
        console.log('3️⃣ Checking recent conversations for messages...');
        console.log('================================================');
        
        for (let i = 0; i < Math.min(5, conversations.length); i++) {
            const conv = conversations[i];
            console.log(`\n--- Conversation ${i + 1}: ${conv.id} ---`);
            console.log(`Contact ID: ${conv.contactId || 'Unknown'}`);
            console.log(`Created: ${conv.dateAdded ? new Date(parseInt(conv.dateAdded)) : 'Unknown'}`);
            console.log(`Last Message: ${conv.lastMessageDate ? new Date(parseInt(conv.lastMessageDate)) : 'Unknown'}`);
            console.log(`Unread: ${conv.unread || 0}`);
            
            try {
                // Get messages for this conversation
                const messages = await hl.getMessages(conv.id, { limit: 3 });
                console.log(`Messages found: ${messages.length}`);
                
                if (messages.length > 0) {
                    console.log('Recent messages:');
                    messages.forEach((msg, idx) => {
                        console.log(`  ${idx + 1}. [${msg.direction || 'unknown'}] ${msg.body || msg.message || 'No content'}`);
                        console.log(`     Time: ${msg.dateAdded ? new Date(parseInt(msg.dateAdded)) : 'Unknown'}`);
                        console.log(`     Type: ${msg.type || 'Unknown'}`);
                        console.log(`     Message Keys: ${Object.keys(msg).join(', ')}`);
                    });
                }
            } catch (error) {
                console.log(`     ❌ Error getting messages: ${error.message}`);
            }
        }
        
        // 4. Check what the monitoring logic is looking for
        console.log('\n4️⃣ Message Detection Logic Analysis:');
        console.log('====================================');
        
        // Simulate the message detection logic
        const now = Date.now();
        const fiveMinutesAgo = now - (5 * 60 * 1000);
        
        console.log(`Current time: ${new Date(now)}`);
        console.log(`Looking for messages after: ${new Date(fiveMinutesAgo)}`);
        
        let newMessageCount = 0;
        for (const conv of conversations.slice(0, 10)) {
            try {
                const messages = await hl.getMessages(conv.id, { limit: 5 });
                for (const msg of messages) {
                    const messageTime = parseInt(msg.dateAdded || 0);
                    if (messageTime > fiveMinutesAgo) {
                        newMessageCount++;
                        console.log(`✅ NEW MESSAGE: ${msg.body || msg.message || 'No content'}`);
                        console.log(`   Time: ${new Date(messageTime)}`);
                        console.log(`   Direction: ${msg.direction || 'unknown'}`);
                        console.log(`   Type: ${msg.type || 'unknown'}`);
                        console.log(`   From: ${msg.contactId || msg.from || 'unknown'}`);
                    }
                }
            } catch (error) {
                console.log(`❌ Error checking conversation ${conv.id}: ${error.message}`);
            }
        }
        
        console.log(`\n📊 Summary: Found ${newMessageCount} new messages in last 5 minutes`);
        
        // 5. Test a single conversation in detail
        if (conversations.length > 0) {
            console.log('\n5️⃣ Detailed Analysis of Most Recent Conversation:');
            console.log('==================================================');
            const latest = conversations[0];
            
            try {
                const detailedMessages = await hl.getMessages(latest.id, { limit: 10 });
                console.log(`\nConversation ${latest.id} has ${detailedMessages.length} messages:`);
                
                detailedMessages.forEach((msg, idx) => {
                    console.log(`\nMessage ${idx + 1}:`);
                    console.log(`  Full message object:`, JSON.stringify(msg, null, 2));
                });
                
            } catch (error) {
                console.log(`❌ Error getting detailed messages: ${error.message}`);
            }
        }
        
    } catch (error) {
        console.error('❌ Debug failed:', error.message);
        console.error('Stack:', error.stack);
    }
}

// Run the debug
debugConversations().catch(console.error);
