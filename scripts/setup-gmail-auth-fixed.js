#!/usr/bin/env node

/**
 * Gmail OAuth Setup Script - Fixed Version
 * 
 * This script sets up Gmail OAuth tokens for each email account individually.
 * It generates unique authorization URLs for each account and saves tokens properly.
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
require('dotenv').config();

// Gmail OAuth configuration
const GMAIL_CONFIG = {
  clientId: process.env.GMAIL_CLIENT_ID,
  clientSecret: process.env.GMAIL_CLIENT_SECRET,
  redirectUri: 'urn:ietf:wg:oauth:2.0:oob', // Use OOB flow instead of web redirect
};

// Email accounts to set up
const EMAIL_ACCOUNTS = process.env.GMAIL_EMAILS ? 
  process.env.GMAIL_EMAILS.split(',').map(email => email.trim()) : 
  [];

// Required Gmail scopes
const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.send',
  'https://www.googleapis.com/auth/gmail.modify'
];

class GmailAuthSetup {
  constructor() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  async validateEnvironment() {
    console.log('🔍 Validating environment configuration...\n');
    
    if (!GMAIL_CONFIG.clientId) {
      throw new Error('GMAIL_CLIENT_ID not found in environment variables');
    }
    
    if (!GMAIL_CONFIG.clientSecret) {
      throw new Error('GMAIL_CLIENT_SECRET not found in environment variables');
    }
    
    if (EMAIL_ACCOUNTS.length === 0) {
      throw new Error('GMAIL_EMAILS not found or empty in environment variables');
    }
    
    console.log('✅ Environment configuration valid');
    console.log(`📧 Email accounts to configure: ${EMAIL_ACCOUNTS.length}`);
    EMAIL_ACCOUNTS.forEach((email, index) => {
      console.log(`   ${index + 1}. ${email}`);
    });
    console.log('');
  }

  async setupEmailAccount(email) {
    console.log(`\n🔐 Setting up OAuth for: ${email}`);
    console.log('━'.repeat(50));
    
    // Create OAuth2 client
    const oauth2Client = new google.auth.OAuth2(
      GMAIL_CONFIG.clientId,
      GMAIL_CONFIG.clientSecret,
      GMAIL_CONFIG.redirectUri
    );
    
    // Generate authorization URL
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
      prompt: 'consent', // Force consent screen to get refresh token
      login_hint: email // Suggest which account to use
    });
    
    console.log(`\n📋 Steps for ${email}:`);
    console.log('1. Open this URL in your browser:');
    console.log('');
    console.log(`🔗 ${authUrl}`);
    console.log('');
    console.log('2. Sign in to the Google account:', email);
    console.log('3. Grant permissions to Grime Guardians');
    console.log('4. Copy the authorization code from the page');
    console.log('');
    
    // Get authorization code from user
    const code = await this.askQuestion('📝 Enter the authorization code: ');
    
    try {
      // Exchange code for tokens
      console.log('🔄 Exchanging code for tokens...');
      const { tokens } = await oauth2Client.getToken(code);
      
      // Verify tokens are complete
      if (!tokens.access_token) {
        throw new Error('No access token received');
      }
      
      if (!tokens.refresh_token) {
        console.warn('⚠️ No refresh token received - you may need to revoke app access and try again');
      }
      
      // Test the tokens by making a simple API call
      oauth2Client.setCredentials(tokens);
      const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
      const profile = await gmail.users.getProfile({ userId: 'me' });
      
      console.log(`✅ Successfully authenticated as: ${profile.data.emailAddress}`);
      
      // Verify email matches
      if (profile.data.emailAddress.toLowerCase() !== email.toLowerCase()) {
        console.warn(`⚠️ Warning: Expected ${email} but got ${profile.data.emailAddress}`);
        const proceed = await this.askQuestion('Continue anyway? (y/n): ');
        if (proceed.toLowerCase() !== 'y') {
          console.log('❌ Skipping this account');
          return false;
        }
      }
      
      // Save tokens to file
      const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${email}.json`);
      const tokenData = {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        scope: tokens.scope,
        token_type: tokens.token_type,
        expiry_date: tokens.expiry_date,
        email_address: profile.data.emailAddress,
        setup_date: new Date().toISOString()
      };
      
      fs.writeFileSync(tokenFilePath, JSON.stringify(tokenData, null, 2));
      console.log(`💾 Tokens saved to: ${tokenFilePath}`);
      
      return true;
      
    } catch (error) {
      console.error(`❌ Failed to set up ${email}:`, error.message);
      return false;
    }
  }

  async askQuestion(question) {
    return new Promise((resolve) => {
      this.rl.question(question, (answer) => {
        resolve(answer.trim());
      });
    });
  }

  async checkExistingTokens() {
    console.log('🔍 Checking for existing token files...\n');
    
    const existingTokens = [];
    const missingTokens = [];
    
    for (const email of EMAIL_ACCOUNTS) {
      const tokenFilePath = path.join(process.cwd(), `gmail-tokens-${email}.json`);
      
      if (fs.existsSync(tokenFilePath)) {
        try {
          const tokenData = JSON.parse(fs.readFileSync(tokenFilePath, 'utf8'));
          console.log(`✅ ${email} - Token file exists (setup: ${tokenData.setup_date || 'unknown'})`);
          existingTokens.push(email);
        } catch (error) {
          console.log(`⚠️ ${email} - Token file corrupted`);
          missingTokens.push(email);
        }
      } else {
        console.log(`❌ ${email} - No token file found`);
        missingTokens.push(email);
      }
    }
    
    console.log('');
    
    if (existingTokens.length > 0) {
      console.log(`📊 Summary: ${existingTokens.length} configured, ${missingTokens.length} need setup`);
      
      if (missingTokens.length === 0) {
        console.log('🎉 All email accounts are already configured!');
        const reconfigure = await this.askQuestion('Reconfigure all accounts? (y/n): ');
        if (reconfigure.toLowerCase() !== 'y') {
          return [];
        }
        return EMAIL_ACCOUNTS;
      }
      
      const setupAll = await this.askQuestion('Setup missing accounts only? (y/n): ');
      if (setupAll.toLowerCase() === 'y') {
        return missingTokens;
      } else {
        return EMAIL_ACCOUNTS;
      }
    }
    
    return missingTokens;
  }

  async run() {
    try {
      console.log('📧 Gmail OAuth Setup - Fixed Version');
      console.log('═'.repeat(50));
      
      // Validate environment
      await this.validateEnvironment();
      
      // Check existing tokens
      const accountsToSetup = await this.checkExistingTokens();
      
      if (accountsToSetup.length === 0) {
        console.log('✅ No accounts need setup. Exiting.');
        this.rl.close();
        return;
      }
      
      console.log(`\n🚀 Setting up ${accountsToSetup.length} Gmail account(s)...\n`);
      
      const results = {
        successful: [],
        failed: []
      };
      
      // Setup each account
      for (let i = 0; i < accountsToSetup.length; i++) {
        const email = accountsToSetup[i];
        console.log(`\n📍 Progress: ${i + 1}/${accountsToSetup.length}`);
        
        const success = await this.setupEmailAccount(email);
        
        if (success) {
          results.successful.push(email);
        } else {
          results.failed.push(email);
        }
        
        // Pause between accounts
        if (i < accountsToSetup.length - 1) {
          console.log('\n⏳ Pausing 3 seconds before next account...');
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
      }
      
      // Show final results
      console.log('\n📊 Setup Complete!');
      console.log('═'.repeat(50));
      
      if (results.successful.length > 0) {
        console.log(`✅ Successfully configured (${results.successful.length}):`);
        results.successful.forEach(email => console.log(`   • ${email}`));
      }
      
      if (results.failed.length > 0) {
        console.log(`❌ Failed to configure (${results.failed.length}):`);
        results.failed.forEach(email => console.log(`   • ${email}`));
      }
      
      if (results.successful.length > 0) {
        console.log('\n🎉 Gmail authentication setup complete!');
        console.log('💡 You can now restart your application:');
        console.log('   pm2 restart grime-guardians');
      }
      
    } catch (error) {
      console.error('\n❌ Setup failed:', error.message);
      process.exit(1);
    } finally {
      this.rl.close();
    }
  }
}

// Run the setup
const setup = new GmailAuthSetup();
setup.run();
