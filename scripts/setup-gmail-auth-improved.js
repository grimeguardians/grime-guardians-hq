#!/usr/bin/env node

/**
 * Improved Gmail OAuth Setup Script
 * Creates token files for each Gmail account configured in GMAIL_EMAILS
 * Uses OOB (Out-of-Band) flow for better server compatibility
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

class GmailAuthSetup {
  constructor() {
    this.clientId = process.env.GMAIL_CLIENT_ID;
    this.clientSecret = process.env.GMAIL_CLIENT_SECRET;
    this.redirectUri = 'urn:ietf:wg:oauth:2.0:oob'; // Use OOB flow instead of web redirect
    this.emailAddresses = process.env.GMAIL_EMAILS ? process.env.GMAIL_EMAILS.split(',').map(e => e.trim()) : [];
    
    console.log('🔐 Gmail OAuth Setup - Improved Version');
    console.log('=====================================');
  }

  validateEnvironment() {
    const missing = [];
    
    if (!this.clientId) missing.push('GMAIL_CLIENT_ID');
    if (!this.clientSecret) missing.push('GMAIL_CLIENT_SECRET');
    if (!this.emailAddresses.length) missing.push('GMAIL_EMAILS');
    
    if (missing.length > 0) {
      console.error('❌ Missing required environment variables:');
      missing.forEach(variable => console.error(`   - ${variable}`));
      console.error('\nPlease check your .env file and try again.');
      process.exit(1);
    }
    
    console.log('✅ Environment variables validated');
    console.log(`📧 Found ${this.emailAddresses.length} email address(es):`);
    this.emailAddresses.forEach((email, i) => {
      console.log(`   ${i + 1}. ${email}`);
    });
    console.log();
  }

  async checkExistingTokens() {
    console.log('🔍 Checking for existing token files...');
    
    const existingTokens = [];
    const missingTokens = [];
    
    for (const email of this.emailAddresses) {
      const tokenPath = path.join(process.cwd(), `gmail-tokens-${email}.json`);
      
      if (fs.existsSync(tokenPath)) {
        try {
          // Try to validate the token
          const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
          if (tokens.access_token || tokens.refresh_token) {
            existingTokens.push({ email, path: tokenPath, valid: true });
            console.log(`   ✅ ${email} - token file exists`);
          } else {
            missingTokens.push(email);
            console.log(`   ⚠️  ${email} - token file invalid`);
          }
        } catch (error) {
          missingTokens.push(email);
          console.log(`   ❌ ${email} - token file corrupted`);
        }
      } else {
        missingTokens.push(email);
        console.log(`   ❌ ${email} - no token file`);
      }
    }
    
    console.log();
    
    if (existingTokens.length > 0) {
      console.log('💡 Some accounts already have tokens. Options:');
      console.log('   1. Skip existing tokens and only set up missing ones');
      console.log('   2. Regenerate all tokens (recommended if having issues)');
      console.log('   3. Exit and use existing tokens');
      
      const choice = await this.promptUser('Enter your choice (1/2/3): ');
      
      switch (choice.trim()) {
        case '1':
          return missingTokens;
        case '2':
          return this.emailAddresses;
        case '3':
          console.log('✅ Using existing tokens');
          process.exit(0);
        default:
          console.log('❌ Invalid choice. Exiting.');
          process.exit(1);
      }
    }
    
    return missingTokens;
  }

  async setupTokensForEmails(emailsToSetup) {
    if (emailsToSetup.length === 0) {
      console.log('✅ All tokens are already set up!');
      return;
    }
    
    console.log(`🔧 Setting up OAuth tokens for ${emailsToSetup.length} email(s)...\n`);
    
    for (let i = 0; i < emailsToSetup.length; i++) {
      const email = emailsToSetup[i];
      console.log(`📧 Setting up: ${email} (${i + 1}/${emailsToSetup.length})`);
      console.log('━'.repeat(50));
      
      try {
        await this.setupSingleEmail(email);
        console.log(`✅ Successfully set up ${email}\n`);
      } catch (error) {
        console.error(`❌ Failed to set up ${email}:`, error.message);
        console.log('   Continuing with next email...\n');
      }
    }
  }

  async setupSingleEmail(email) {
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
      login_hint: email, // Suggest which account to use
      prompt: 'consent' // Force consent screen to get refresh token
    });

    console.log(`🌐 Please open this URL in your browser:`);
    console.log(`\n${authUrl}\n`);
    console.log(`📝 Instructions:`);
    console.log(`   1. Click the URL above (or copy/paste into browser)`);
    console.log(`   2. Sign in to: ${email}`);
    console.log(`   3. Click "Allow" to grant permissions`);
    console.log(`   4. Copy the authorization code from the page`);
    console.log(`   5. Paste it below\n`);

    // Get authorization code from user
    const code = await this.promptUser('Enter the authorization code: ');
    
    if (!code || code.trim().length === 0) {
      throw new Error('No authorization code provided');
    }

    // Exchange code for tokens
    console.log('🔄 Exchanging code for tokens...');
    const { tokens } = await auth.getToken(code.trim());
    
    if (!tokens.access_token) {
      throw new Error('No access token received');
    }

    // Test the tokens
    console.log('🧪 Testing token validity...');
    auth.setCredentials(tokens);
    const gmail = google.gmail({ version: 'v1', auth });
    const profile = await gmail.users.getProfile({ userId: 'me' });
    
    if (profile.data.emailAddress !== email) {
      console.log(`⚠️  Warning: Expected ${email}, got ${profile.data.emailAddress}`);
      console.log('   This might be okay if accounts are linked.');
    }

    // Save tokens to file
    const tokenPath = path.join(process.cwd(), `gmail-tokens-${email}.json`);
    fs.writeFileSync(tokenPath, JSON.stringify(tokens, null, 2));
    console.log(`💾 Tokens saved to: ${tokenPath}`);
    
    // Verify file was written correctly
    const savedTokens = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
    if (!savedTokens.access_token) {
      throw new Error('Token file verification failed');
    }
  }

  async verifyAllTokens() {
    console.log('\n🔍 Verifying all token files...');
    console.log('━'.repeat(50));
    
    let successCount = 0;
    let failCount = 0;
    
    for (const email of this.emailAddresses) {
      const tokenPath = path.join(process.cwd(), `gmail-tokens-${email}.json`);
      
      try {
        if (!fs.existsSync(tokenPath)) {
          console.log(`❌ ${email} - token file missing`);
          failCount++;
          continue;
        }
        
        const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));
        
        const auth = new google.auth.OAuth2(
          this.clientId,
          this.clientSecret,
          this.redirectUri
        );
        
        auth.setCredentials(tokens);
        const gmail = google.gmail({ version: 'v1', auth });
        
        // Test API call
        const profile = await gmail.users.getProfile({ userId: 'me' });
        console.log(`✅ ${email} - API connection successful`);
        successCount++;
        
      } catch (error) {
        console.log(`❌ ${email} - API test failed: ${error.message}`);
        failCount++;
      }
    }
    
    console.log('\n📊 Verification Summary:');
    console.log(`   ✅ Working: ${successCount}`);
    console.log(`   ❌ Failed: ${failCount}`);
    console.log(`   📧 Total: ${this.emailAddresses.length}`);
    
    if (successCount === this.emailAddresses.length) {
      console.log('\n🎉 All Gmail accounts are ready!');
      console.log('💡 You can now restart your application:');
      console.log('   pm2 restart grime-guardians');
    } else {
      console.log('\n⚠️  Some accounts failed verification.');
      console.log('💡 You may want to re-run this script for failed accounts.');
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
    try {
      this.validateEnvironment();
      const emailsToSetup = await this.checkExistingTokens();
      await this.setupTokensForEmails(emailsToSetup);
      await this.verifyAllTokens();
    } catch (error) {
      console.error('\n❌ Setup failed:', error.message);
      console.error('💡 Please check your configuration and try again.');
      process.exit(1);
    }
  }
}

// Run the setup if this file is executed directly
if (require.main === module) {
  const setup = new GmailAuthSetup();
  setup.run().catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = GmailAuthSetup;
