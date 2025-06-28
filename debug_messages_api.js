#!/usr/bin/env node
/**
 * Debug Raw High Level Messages API Response
 * This script shows the raw API response to understand the data structure
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function debugMessages() {
    console.log('🔍 High Level Messages API Raw Debug\n');
    
    const hl = new HighLevelOAuth();
    
    try {
        // Get a conversation ID
        const conversations = await hl.getConversations({ limit: 1 });
        if (conversations.length === 0) {
            console.log('❌ No conversations found');
            return;
        }
        
        const conversationId = conversations[0].id;
        console.log(`📱 Testing with conversation: ${conversationId}`);
        console.log(`📱 Contact: ${conversations[0].contactName || conversations[0].fullName}`);
        console.log(`📱 Last message: ${conversations[0].lastMessageBody}`);
        console.log(`📱 Last message time: ${new Date(parseInt(conversations[0].lastMessageDate))}\n`);
        
        // Test raw API request to messages endpoint
        const params = new URLSearchParams({
            limit: 5,
            skip: 0
        });
        
        const url = `https://services.leadconnectorhq.com/conversations/${conversationId}/messages?${params.toString()}`;
        console.log(`🔗 API URL: ${url}\n`);
        
        // Make direct API request and show raw response
        const response = await hl.makeAuthenticatedRequest(url);
        console.log(`📊 Response Status: ${response.status} ${response.statusText}`);
        console.log(`📊 Response Headers:`, Object.fromEntries(response.headers));
        
        if (!response.ok) {
            const errorText = await response.text();
            console.log(`❌ Error Response: ${errorText}`);
            return;
        }
        
        const rawData = await response.json();
        console.log(`\n📝 Raw API Response:`);
        console.log(JSON.stringify(rawData, null, 2));
        
        console.log(`\n🔍 Response Analysis:`);
        console.log(`- Type: ${typeof rawData}`);
        console.log(`- Keys: ${Object.keys(rawData)}`);
        
        if (rawData.messages) {
            console.log(`- Messages array length: ${rawData.messages.length}`);
            if (rawData.messages.length > 0) {
                console.log(`- First message keys: ${Object.keys(rawData.messages[0])}`);
                console.log(`- First message: ${JSON.stringify(rawData.messages[0], null, 2)}`);
            }
        } else {
            console.log(`- No 'messages' property found`);
            console.log(`- Available properties: ${Object.keys(rawData)}`);
        }
        
        // Also test the High Level OAuth getMessages method
        console.log(`\n🧪 Testing HighLevelOAuth.getMessages():`);
        try {
            const messages = await hl.getMessages(conversationId, { limit: 5 });
            console.log(`- Returned: ${typeof messages}`);
            console.log(`- Length: ${messages ? messages.length : 'N/A'}`);
            console.log(`- Content: ${JSON.stringify(messages, null, 2)}`);
        } catch (error) {
            console.log(`- Error: ${error.message}`);
        }
        
    } catch (error) {
        console.error('❌ Debug failed:', error.message);
        console.error('Stack:', error.stack);
    }
}

// Run the debug
debugMessages().catch(console.error);
