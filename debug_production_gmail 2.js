/**
 * Production Server Gmail Debug Script
 * Upload this to the server to diagnose Gmail issues
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function debugProductionGmail() {
  console.log('🔍 PRODUCTION Gmail Authentication Debug');
  console.log('=========================================');
  
  // Check environment variables
  console.log('\n📋 Environment Variables:');
  console.log(`GMAIL_CLIENT_ID: ${process.env.GMAIL_CLIENT_ID ? 'Set (' + process.env.GMAIL_CLIENT_ID.substring(0, 20) + '...)' : 'MISSING'}`);
  console.log(`GMAIL_CLIENT_SECRET: ${process.env.GMAIL_CLIENT_SECRET ? 'Set' : 'MISSING'}`);
  console.log(`GMAIL_REDIRECT_URI: ${process.env.GMAIL_REDIRECT_URI || 'MISSING'}`);
  console.log(`GMAIL_EMAILS: ${process.env.GMAIL_EMAILS || 'MISSING'}`);
  console.log(`OPS_LEAD_DISCORD_ID: ${process.env.OPS_LEAD_DISCORD_ID || 'MISSING'}`);
  
  // Check current working directory
  console.log(`\n📂 Working Directory: ${process.cwd()}`);
  
  // Check all files in directory
  console.log('\n📁 Files in current directory:');
  try {
    const files = fs.readdirSync(process.cwd());
    const gmailFiles = files.filter(f => f.startsWith('gmail-tokens-'));
    
    if (gmailFiles.length === 0) {
      console.log('❌ No Gmail token files found!');
      console.log('📋 All files:', files.slice(0, 10).join(', '));
    } else {
      console.log('✅ Gmail token files found:');
      gmailFiles.forEach(file => console.log(`   - ${file}`));
    }
  } catch (error) {
    console.log(`❌ Error reading directory: ${error.message}`);
  }
  
  // Test specific account that should have Google Voice
  const targetEmail = 'broberts111592@gmail.com';
  const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${targetEmail}.json`);
  
  console.log(`\n🎯 Testing Google Voice Account: ${targetEmail}`);
  console.log(`Token file path: ${tokenFilePath}`);
  
  if (fs.existsSync(tokenFilePath)) {
    try {
      const tokens = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
      console.log(`✅ Token file exists and is valid JSON`);
      
      // Test authentication
      const auth = new google.auth.OAuth2(
        process.env.GMAIL_CLIENT_ID,
        process.env.GMAIL_CLIENT_SECRET,
        process.env.GMAIL_REDIRECT_URI
      );
      
      auth.setCredentials(tokens);
      
      const gmail = google.gmail({ version: 'v1', auth });
      const profile = await gmail.users.getProfile({ userId: 'me' });
      
      console.log(`✅ Authentication successful`);
      console.log(`📧 Email: ${profile.data.emailAddress}`);
      
      // Test Google Voice query
      const query = 'from:voice-noreply@google.com ("New text message" OR "New group message") is:unread';
      console.log(`🔍 Testing query: ${query}`);
      
      const messages = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 10
      });
      
      console.log(`📱 Google Voice messages found: ${messages.data.messages?.length || 0}`);
      
      if (messages.data.messages && messages.data.messages.length > 0) {
        console.log(`✅ Gmail monitoring should be working!`);
        
        // Test one message
        const firstMessage = await gmail.users.messages.get({
          userId: 'me',
          id: messages.data.messages[0].id
        });
        
        const subject = firstMessage.data.payload.headers.find(h => h.name === 'Subject')?.value;
        console.log(`📝 Sample message subject: ${subject}`);
      } else {
        console.log(`ℹ️ No unread Google Voice messages - this is normal if none are pending`);
      }
      
    } catch (authError) {
      console.log(`❌ Authentication failed: ${authError.message}`);
      console.log(`🔧 May need to refresh tokens or re-authenticate`);
    }
  } else {
    console.log(`❌ Token file not found: ${tokenFilePath}`);
    console.log(`🔧 Need to copy token files to production server`);
  }
  
  console.log('\n🎯 Diagnosis Complete');
}

debugProductionGmail().catch(error => {
  console.error('❌ Debug script failed:', error.message);
  console.error('Full error:', error);
});
