#!/usr/bin/env node

/**
 * High Level OAuth Scope Fix
 * Re-authorize with proper conversation scopes
 */

require('dotenv').config();
const HighLevelOAuth = require('./src/utils/highlevelOAuth');

async function fixOAuthScopes() {
  console.log('🔧 HIGH LEVEL OAUTH SCOPE FIX');
  console.log('=============================\n');
  
  console.log('🎯 PROBLEM IDENTIFIED:');
  console.log('   Current OAuth token has NO SCOPES');
  console.log('   All endpoints return "not authorized for this scope"');
  console.log('   This is definitely a configuration issue!\n');
  
  console.log('💡 SOLUTION: Re-authorize with correct scopes\n');
  
  // Try different scope combinations
  const scopeOptions = [
    {
      name: 'Full Conversations Access',
      scopes: 'conversations.readonly conversations.write conversations/message.readonly conversations/message.write contacts.readonly locations.readonly'
    },
    {
      name: 'Basic Conversations',
      scopes: 'conversations.readonly conversations/message.readonly'
    },
    {
      name: 'Messages Only',
      scopes: 'conversations/message.readonly conversations/message.write'
    },
    {
      name: 'All Available Scopes',
      scopes: 'conversations.readonly conversations.write conversations/message.readonly conversations/message.write contacts.readonly contacts.write locations.readonly locations.write calendars.readonly calendars.write opportunities.readonly opportunities.write'
    }
  ];
  
  console.log('🔗 Try these authorization URLs:\n');
  
  const baseUrl = 'https://marketplace.gohighlevel.com/oauth/chooselocation';
  const clientId = process.env.HIGHLEVEL_OAUTH_CLIENT_ID;
  const redirectUri = process.env.HIGHLEVEL_OAUTH_REDIRECT_URI;
  
  scopeOptions.forEach((option, index) => {
    const params = new URLSearchParams({
      response_type: 'code',
      redirect_uri: redirectUri,
      client_id: clientId,
      scope: option.scopes
    });
    
    const authUrl = `${baseUrl}?${params.toString()}`;
    
    console.log(`${index + 1}. ${option.name}:`);
    console.log(`   ${authUrl}\n`);
  });
  
  console.log('📋 INSTRUCTIONS:');
  console.log('1. Try URL #1 first (Full Conversations Access)');
  console.log('2. If that fails, try URL #4 (All Available Scopes)');
  console.log('3. After authorizing, run: node process_oauth_code.js');
  console.log('4. Test with: node test_highlevel_oauth.js\n');
  
  console.log('🎯 EXPECTED RESULT:');
  console.log('   OAuth token should include conversation scopes');
  console.log('   API endpoints should return 200 instead of 401');
  console.log('   Ava and Dean will have full High Level monitoring! 🚀');
}

// Run the fix
fixOAuthScopes().catch(error => {
  console.error('💥 Fix failed:', error.message);
  process.exit(1);
});
