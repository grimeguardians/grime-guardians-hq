#!/usr/bin/env node
/**
 * Debug Gmail API Structure
 * This script will show us the actual structure of Gmail API responses
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function debugGmailStructure() {
    console.log('🔍 Debugging Gmail API Structure for Google Voice Messages\n');
    
    try {
        // Initialize Gmail for the Google Voice account
        const googleVoiceAccount = 'broberts111592@gmail.com';
        const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${googleVoiceAccount}.json`);
        
        if (!fs.existsSync(tokenFilePath)) {
            console.log(`❌ Token file not found: ${tokenFilePath}`);
            return;
        }
        
        const credentials = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
        
        const auth = new google.auth.OAuth2(
            process.env.GMAIL_CLIENT_ID,
            process.env.GMAIL_CLIENT_SECRET,
            process.env.GMAIL_REDIRECT_URI
        );
        
        auth.setCredentials(credentials);
        const gmail = google.gmail({ version: 'v1', auth });
        
        // Search for Google Voice messages
        const dateFilter = new Date().toISOString().split('T')[0].replace(/-/g, '/');
        const query = `from:@txt.voice.google.com subject:("New text message from") after:${dateFilter}`;
        
        console.log(`🔍 Searching with query: ${query}`);
        
        const messages = await gmail.users.messages.list({
            userId: 'me',
            q: query,
            maxResults: 1
        });
        
        if (!messages.data.messages || messages.data.messages.length === 0) {
            console.log('❌ No Google Voice messages found');
            return;
        }
        
        console.log(`📱 Found ${messages.data.messages.length} message(s)`);
        
        // Get the first message with full details
        const messageRef = messages.data.messages[0];
        const email = await gmail.users.messages.get({
            userId: 'me',
            id: messageRef.id
        });
        
        console.log('📧 Gmail API Response Structure:');
        console.log('================================');
        console.log('Keys in email:', Object.keys(email));
        console.log('Keys in email.data:', Object.keys(email.data));
        
        if (email.data.payload) {
            console.log('Keys in email.data.payload:', Object.keys(email.data.payload));
            
            if (email.data.payload.headers) {
                console.log('\n📝 Headers:');
                email.data.payload.headers.forEach(header => {
                    if (header.name.toLowerCase() === 'subject' || header.name.toLowerCase() === 'from') {
                        console.log(`  ${header.name}: ${header.value}`);
                    }
                });
            }
            
            if (email.data.payload.body) {
                console.log('\n📄 Body structure:', Object.keys(email.data.payload.body));
                if (email.data.payload.body.data) {
                    const bodyText = Buffer.from(email.data.payload.body.data, 'base64').toString();
                    console.log('\n📄 Body content (first 200 chars):');
                    console.log(bodyText.substring(0, 200));
                }
            }
            
            if (email.data.payload.parts) {
                console.log('\n📦 Parts:', email.data.payload.parts.length);
                email.data.payload.parts.forEach((part, index) => {
                    console.log(`  Part ${index}: ${part.mimeType}`);
                    if (part.body && part.body.data) {
                        const partText = Buffer.from(part.body.data, 'base64').toString();
                        console.log(`    Content (first 100 chars): ${partText.substring(0, 100)}`);
                    }
                });
            }
        }
        
        console.log('\n📊 Full email.data structure:');
        console.log(JSON.stringify(email.data, null, 2));
        
    } catch (error) {
        console.error('❌ Debug failed:', error.message);
        console.error('Stack:', error.stack);
    }
}

// Run the debug
debugGmailStructure().catch(console.error);
