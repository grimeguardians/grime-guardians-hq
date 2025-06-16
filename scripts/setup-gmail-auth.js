/**
 * Gmail OAuth2 Setup Helper - Enhanced Version
 * 
 * This script helps you get the Gmail API credentials needed for 
 * monitoring Google Voice emails (612-584-9396)
 * 
 * Features:
 * - Built-in HTTP server for OAuth callback
 * - Automatic token extraction and .env update
 * - Gmail connection testing
 */

const { google } = require('googleapis');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
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

async function setupGmailAuth() {
  console.log('🔐 GMAIL API AUTHENTICATION SETUP');
  console.log('=' .repeat(50));
  console.log('Setting up Gmail API access for Google Voice monitoring (612-584-9396)');
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
    console.log('Then run this script again: node scripts/setup-gmail-auth.js');
    return;
  }

  // Check if refresh token already exists
  if (process.env.GMAIL_REFRESH_TOKEN) {
    console.log('✅ Gmail refresh token already configured!');
    console.log('');
    console.log('Testing existing connection...');
    
    const testSuccess = await testExistingConnection();
    if (testSuccess) {
      console.log('✅ Gmail connection is working properly!');
      console.log('');
      console.log('🎯 Ready to monitor Google Voice emails!');
      console.log('Run: node src/index.js to start the system');
      return;
    } else {
      console.log('❌ Existing token is invalid. Setting up new authentication...');
      console.log('');
    }
  }

  const oauth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);

  // Generate auth URL
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent' // Force consent to get refresh token
  });

  console.log('🌐 Please open your browser and visit this URL:');
  console.log(authUrl);
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
    return;
  }

  console.log('✅ Authorization code received!');
  console.log('Exchanging for access tokens...');

  try {
    // Exchange authorization code for tokens
    const { tokens } = await oauth2Client.getToken(authCode);
    oauth2Client.setCredentials(tokens);

    console.log('✅ Tokens obtained successfully!');
    
    // Update .env file with refresh token
    await updateEnvFile(tokens.refresh_token);
    
    // Test the connection
    console.log('🧪 Testing Gmail connection...');
    const testSuccess = await testGmailConnection(oauth2Client);
    
    if (testSuccess) {
      console.log('');
      console.log('🎉 SETUP COMPLETE!');
      console.log('=' .repeat(30));
      console.log('✅ Gmail API authentication configured');
      console.log('✅ Google Voice email monitoring ready');
      console.log('✅ Refresh token saved to .env file');
      console.log('');
      console.log('🚀 Next steps:');
      console.log('1. Run: node test-email-monitor.js (test the system)');
      console.log('2. Run: node src/index.js (start monitoring)');
      console.log('');
      console.log('📧 The system will monitor Google Voice emails every 2 minutes');
      console.log('📱 You\'ll get Discord alerts for all schedule requests');
    }

  } catch (error) {
    console.error('❌ Error during token exchange:', error.message);
  }
}

async function testExistingConnection() {
  try {
    const oauth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
    oauth2Client.setCredentials({
      refresh_token: process.env.GMAIL_REFRESH_TOKEN
    });

    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    await gmail.users.getProfile({ userId: 'me' });
    
    return true;
  } catch (error) {
    console.log(`❌ Connection test failed: ${error.message}`);
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

async function updateEnvFile(refreshToken) {
  try {
    const envPath = path.resolve('.env');
    let envContent = '';
    
    // Read existing .env file
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }
    
    // Check if GMAIL_REFRESH_TOKEN already exists
    if (envContent.includes('GMAIL_REFRESH_TOKEN=')) {
      // Update existing token
      envContent = envContent.replace(/GMAIL_REFRESH_TOKEN=.*/, `GMAIL_REFRESH_TOKEN=${refreshToken}`);
    } else {
      // Add new token
      envContent += `\n# Gmail API for Google Voice monitoring\nGMAIL_REFRESH_TOKEN=${refreshToken}\n`;
    }
    
    // Write back to file
    fs.writeFileSync(envPath, envContent);
    console.log('✅ Refresh token saved to .env file');
    
  } catch (error) {
    console.error('❌ Error updating .env file:', error.message);
    console.log('📝 Please manually add this line to your .env file:');
    console.log(`GMAIL_REFRESH_TOKEN=${refreshToken}`);
  }
}

async function testGmailConnection(auth) {
  try {
    const gmail = google.gmail({ version: 'v1', auth });
    
    // Test basic connection
    const profile = await gmail.users.getProfile({ userId: 'me' });
    console.log(`📧 Connected to Gmail: ${profile.data.emailAddress}`);
    
    // Test search for Google Voice emails
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
    
    console.log('');
    console.log('🎉 Setup complete! Your system is ready to monitor Google Voice emails.');
    
    return true;
  } catch (error) {
    console.error('❌ Gmail test failed:', error.message);
    return false;
  }
}

// Run if called directly
if (require.main === module) {
  setupGmailAuth().catch(console.error);
}

module.exports = { setupGmailAuth };
