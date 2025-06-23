#!/usr/bin/env node

/**
 * Simple Gmail OAuth Setup Script
 * Uses existing redirect URI from .env file
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Gmail OAuth configuration
const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.send',
  'https://www.googleapis.com/auth/gmail.modify'
];

class SimpleGmailSetup {
  constructor() {
    this.clientId = process.env.GMAIL_CLIENT_ID;
    this.clientSecret = process.env.GMAIL_CLIENT_SECRET;
    this.redirectUri = process.env.GMAIL_REDIRECT_URI;
    this.emailAddresses = process.env.GMAIL_EMAILS ? process.env.GMAIL_EMAILS.split(',').map(e => e.trim()) : [];
    
    console.log('🔐 Simple Gmail OAuth Setup');
    console.log('============================');
    console.log(`📧 Emails to setup: ${this.emailAddresses.join(', ')}`);
    console.log(`🔗 Redirect URI: ${this.redirectUri}`);
    console.log();
  }

  async setupEmail(email) {
    console.log(`\n📧 Setting up: ${email}`);
    console.log('━'.repeat(50));

    // Create OAuth2 client
    const auth = new google.auth.OAuth2(
      this.clientId,
      this.clientSecret,
      this.redirectUri
    );

    // Generate auth URL
    const authUrl = auth.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
      login_hint: email,
      prompt: 'consent'
    });

    console.log(`\n🌐 Authorization URL for ${email}:`);
    console.log(authUrl);
    console.log('\n📝 Steps:');
    console.log('1. Copy the URL above and open it in your browser');
    console.log(`2. Sign in to: ${email}`);
    console.log('3. Click "Allow" to grant permissions');
    console.log('4. You\'ll be redirected to grimeguardians.com (this will show an error page)');
    console.log('5. Copy the "code" parameter from the URL in your browser');
    console.log('   Example: if URL is "https://grimeguardians.com/oauth/callback?code=ABC123"');
    console.log('   Then copy: ABC123');
    console.log();

    const code = await this.promptUser('Paste the authorization code here: ');
    
    try {
      // Exchange code for tokens
      console.log('🔄 Getting tokens...');
      const { tokens } = await auth.getToken(code.trim());
      
      // Test the tokens
      console.log('🧪 Testing connection...');
      auth.setCredentials(tokens);
      const gmail = google.gmail({ version: 'v1', auth });
      const profile = await gmail.users.getProfile({ userId: 'me' });
      
      console.log(`✅ Connected to: ${profile.data.emailAddress}`);
      
      // Save tokens
      const tokenPath = path.join(process.cwd(), `gmail-tokens-${email}.json`);
      fs.writeFileSync(tokenPath, JSON.stringify(tokens, null, 2));
      console.log(`💾 Tokens saved to: ${tokenPath}`);
      
      return true;
    } catch (error) {
      console.error(`❌ Failed to setup ${email}:`, error.message);
      return false;
    }
  }

  promptUser(question) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    return new Promise((resolve) => {
      rl.question(question, (answer) => {
        rl.close();
        resolve(answer);
      });
    });
  }

  async run() {
    console.log('🚀 Starting Gmail OAuth setup...\n');
    
    for (const email of this.emailAddresses) {
      const success = await this.setupEmail(email);
      if (success) {
        console.log(`✅ ${email} setup complete!`);
      } else {
        console.log(`❌ ${email} setup failed!`);
      }
      
      if (this.emailAddresses.indexOf(email) < this.emailAddresses.length - 1) {
        const continueSetup = await this.promptUser('\nContinue with next email? (y/n): ');
        if (continueSetup.toLowerCase() !== 'y') {
          break;
        }
      }
    }
    
    console.log('\n🎉 Setup complete! You can now restart your application:');
    console.log('pm2 restart grime-guardians');
  }
}

// Run the setup
const setup = new SimpleGmailSetup();
setup.run().catch(console.error);
