/**
 * Gmail OAuth2 Multi-Account Setup Helper
 * 
 * This script helps you set up Gmail API credentials for multiple email accounts
 * specifically for monitoring Google Voice emails (612-584-9396) and business emails
 * 
 * Features:
 * - Multiple account authentication
 * - Individual token file creation
 * - Gmail connection testing per account
 */

const { google } = require('googleapis');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
require('dotenv').config();

// OAuth2 configuration
const CLIENT_ID = process.env.GMAIL_CLIENT_ID;
const CLIENT_SECRET = process.env.GMAIL_CLIENT_SECRET;
const REDIRECT_URI = process.env.GMAIL_REDIRECT_URI || 'http://localhost:3000/oauth/callback';

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/gmail.send'
];

// Get email addresses from environment
const EMAIL_ADDRESSES = process.env.GMAIL_EMAILS ? process.env.GMAIL_EMAILS.split(',').map(e => e.trim()) : [];

function askQuestion(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function setupGmailMultiAuth() {
  console.log('🔐 GMAIL API MULTI-ACCOUNT AUTHENTICATION SETUP');
  console.log('=' .repeat(60));
  console.log('Setting up Gmail API access for multiple accounts');
  console.log('');

  // Check if credentials are configured
  if (!CLIENT_ID || !CLIENT_SECRET) {
    console.log('❌ Missing Gmail API credentials!');
    console.log('');
    console.log('📋 Setup Steps:');
    console.log('1. Go to https://console.cloud.google.com/');
    console.log('2. Create/select a project');
    console.log('3. Enable Gmail API (APIs & Services → Library)');
    console.log('4. Create OAuth2 credentials (APIs & Services → Credentials)');
    console.log('5. Add to your .env file:');
    console.log('   GMAIL_CLIENT_ID=your_client_id_here');
    console.log('   GMAIL_CLIENT_SECRET=your_client_secret_here');
    console.log('   GMAIL_REDIRECT_URI=http://localhost:3000/oauth/callback');
    console.log('');
    console.log('Then run this script again: node scripts/setup-gmail-multi-auth.js');
    return;
  }

  if (EMAIL_ADDRESSES.length === 0) {
    console.log('❌ No email addresses configured in GMAIL_EMAILS!');
    console.log('Please add email addresses to your .env file:');
    console.log('GMAIL_EMAILS=brandonr@grimeguardians.com,grimeguardianscleaning@gmail.com,broberts111592@gmail.com');
    return;
  }

  console.log('📧 Email addresses to configure:');
  EMAIL_ADDRESSES.forEach((email, index) => {
    const tokenFile = `gmail-tokens-${email}.json`;
    const exists = fs.existsSync(tokenFile);
    console.log(`   ${index + 1}. ${email} ${exists ? '✅ (already configured)' : '❌ (needs setup)'}`);
  });
  console.log('');

  // Check which accounts need setup
  const accountsNeedingSetup = EMAIL_ADDRESSES.filter(email => {
    const tokenFile = `gmail-tokens-${email}.json`;
    return !fs.existsSync(tokenFile);
  });

  if (accountsNeedingSetup.length === 0) {
    console.log('✅ All accounts are already configured!');
    console.log('Testing existing connections...');
    
    let allWorking = true;
    for (const email of EMAIL_ADDRESSES) {
      const testSuccess = await testExistingConnection(email);
      if (!testSuccess) {
        allWorking = false;
        console.log(`❌ ${email} - connection failed`);
      } else {
        console.log(`✅ ${email} - connection working`);
      }
    }
    
    if (allWorking) {
      console.log('');
      console.log('🎯 All Gmail connections are working properly!');
      console.log('Ready to monitor emails!');
    } else {
      console.log('');
      console.log('⚠️ Some connections failed. You may need to re-authenticate those accounts.');
    }
    return;
  }

  // Setup accounts that need authentication
  console.log(`Setting up ${accountsNeedingSetup.length} account(s):`);
  accountsNeedingSetup.forEach(email => console.log(`  - ${email}`));
  console.log('');

  for (const email of accountsNeedingSetup) {
    console.log(`🔐 Setting up authentication for: ${email}`);
    console.log(`Please make sure you'll log in with ${email} when prompted.`);
    console.log('');
    
    const proceed = await askQuestion('Press Enter to continue, or type "skip" to skip this account: ');
    if (proceed.toLowerCase() === 'skip') {
      console.log(`⏭️ Skipping ${email}`);
      console.log('');
      continue;
    }

    const success = await setupSingleAccount(email);
    if (success) {
      console.log(`✅ Successfully configured ${email}`);
    } else {
      console.log(`❌ Failed to configure ${email}`);
    }
    console.log('');
  }

  console.log('🎉 Multi-account setup complete!');
  console.log('You can now run: node src/index.js to start monitoring');
}

async function setupSingleAccount(emailAddress) {
  const oauth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);

  // Generate auth URL
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent', // Force consent to get refresh token
    login_hint: emailAddress // Suggest which account to use
  });

  console.log('🌐 Please open your browser and visit this URL:');
  console.log(authUrl);
  console.log('');
  console.log(`⚠️ IMPORTANT: Make sure to log in with ${emailAddress}`);
  console.log('');

  // Start local server to handle OAuth callback
  const server = await startCallbackServer();
  const port = server.address().port;
  
  console.log(`🚀 Callback server started on port ${port}`);
  console.log('Waiting for OAuth callback...');
  
  // Wait for callback
  const authCode = await waitForCallback(server);
  
  if (!authCode) {
    console.log('❌ No authorization code received');
    return false;
  }

  console.log('✅ Authorization code received!');
  console.log('Exchanging for access tokens...');

  try {
    // Exchange authorization code for tokens
    const { tokens } = await oauth2Client.getToken(authCode);
    oauth2Client.setCredentials(tokens);

    console.log('✅ Tokens obtained successfully!');
    
    // Save tokens to individual file
    const tokenFile = `gmail-tokens-${emailAddress}.json`;
    fs.writeFileSync(tokenFile, JSON.stringify(tokens, null, 2));
    console.log(`✅ Tokens saved to ${tokenFile}`);
    
    // Test the connection
    console.log('🧪 Testing Gmail connection...');
    const testSuccess = await testGmailConnection(oauth2Client, emailAddress);
    
    return testSuccess;

  } catch (error) {
    console.error('❌ Error during token exchange:', error.message);
    return false;
  }
}

async function testExistingConnection(emailAddress) {
  try {
    const tokenFile = `gmail-tokens-${emailAddress}.json`;
    if (!fs.existsSync(tokenFile)) {
      return false;
    }

    const tokens = JSON.parse(fs.readFileSync(tokenFile, 'utf8'));
    const oauth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
    oauth2Client.setCredentials(tokens);

    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    await gmail.users.getProfile({ userId: 'me' });
    
    return true;
  } catch (error) {
    return false;
  }
}

async function startCallbackServer() {
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.listen(3000, 'localhost', () => {
      resolve(server);
    }).on('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        console.log('⚠️ Port 3000 is in use. Trying port 3001...');
        server.listen(3001, 'localhost', () => {
          console.log('📝 Note: Using port 3001 instead of 3000');
          console.log('   Update your Google Cloud Console redirect URI to: http://localhost:3001/oauth/callback');
          resolve(server);
        });
      } else {
        reject(err);
      }
    });
  });
}

async function waitForCallback(server) {
  return new Promise((resolve) => {
    server.on('request', (req, res) => {
      const parsedUrl = url.parse(req.url, true);
      const queryParams = parsedUrl.query;
      
      // Only handle the oauth callback path
      if (parsedUrl.pathname === '/oauth/callback') {
        if (queryParams.code) {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
                <h1 style="color: green;">✅ Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p style="color: #666;">Gmail API access has been granted to Grime Guardians.</p>
              </body>
            </html>
          `);
          
          server.close();
          resolve(queryParams.code);
        } else if (queryParams.error) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ Authentication Failed</h1>
                <p>Error: ${queryParams.error}</p>
                <p>Please try again or check your Google Cloud Console setup.</p>
              </body>
            </html>
          `);
          
          server.close();
          resolve(null);
        }
      } else {
        // Handle other paths
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.end(`
          <html>
            <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
              <h1>404 - Not Found</h1>
              <p>Please use the correct OAuth callback URL: /oauth/callback</p>
            </body>
          </html>
        `);
      }
    });
  });
}

async function testGmailConnection(auth, emailAddress) {
  try {
    const gmail = google.gmail({ version: 'v1', auth });
    
    // Test basic connection
    const profile = await gmail.users.getProfile({ userId: 'me' });
    console.log(`📧 Connected to Gmail: ${profile.data.emailAddress}`);
    
    // Verify we're connected to the correct account
    if (profile.data.emailAddress !== emailAddress) {
      console.log(`⚠️ Warning: Expected ${emailAddress} but connected to ${profile.data.emailAddress}`);
    }
    
    // Special test for Google Voice account
    if (emailAddress === 'broberts111592@gmail.com') {
      console.log('📱 Testing Google Voice email detection...');
      const query = 'from:txt.voice.google.com OR from:voice-noreply@google.com';
      const response = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 5
      });
      
      const messageCount = response.data.messages ? response.data.messages.length : 0;
      console.log(`📱 Found ${messageCount} recent Google Voice emails`);
      
      if (messageCount === 0) {
        console.log('ℹ️  No recent Google Voice emails found (this is normal if you haven\'t received any)');
      }
    }
    
    return true;
  } catch (error) {
    console.error('❌ Gmail test failed:', error.message);
    return false;
  }
}

// Run if called directly
if (require.main === module) {
  setupGmailMultiAuth().catch(console.error);
}

module.exports = { setupGmailMultiAuth };
