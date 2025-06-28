#!/usr/bin/env node

/**
 * OAuth Token Deep Analysis
 * Let's decode the OAuth token properly to see what scopes we actually have
 */

require('dotenv').config();

function decodeJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid JWT format');
    }
    
    const header = JSON.parse(Buffer.from(parts[0], 'base64url').toString());
    const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
    
    return { header, payload };
  } catch (error) {
    // Try regular base64 decoding
    try {
      const parts = token.split('.');
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
      return { payload };
    } catch (e) {
      throw new Error(`Could not decode token: ${error.message}`);
    }
  }
}

async function analyzeOAuthToken() {
  console.log('🔍 OAUTH TOKEN DEEP ANALYSIS');
  console.log('============================\n');
  
  const accessToken = process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN;
  
  if (!accessToken) {
    console.log('❌ No OAuth access token found!');
    return;
  }
  
  console.log('📋 Token Info:');
  console.log(`   Length: ${accessToken.length} characters`);
  console.log(`   Type: ${accessToken.startsWith('eyJ') ? 'JWT' : 'Opaque token'}`);
  console.log(`   First 50 chars: ${accessToken.substring(0, 50)}...`);
  console.log('');
  
  if (accessToken.startsWith('eyJ')) {
    try {
      const decoded = decodeJWT(accessToken);
      
      console.log('🔓 Decoded Token:');
      console.log('================');
      
      if (decoded.header) {
        console.log('Header:');
        console.log(JSON.stringify(decoded.header, null, 2));
        console.log('');
      }
      
      console.log('Payload:');
      console.log(JSON.stringify(decoded.payload, null, 2));
      console.log('');
      
      // Analyze key fields
      const payload = decoded.payload;
      
      console.log('🎯 Key Analysis:');
      console.log('===============');
      console.log(`   Client ID: ${payload.client_id || payload.aud || 'not found'}`);
      console.log(`   Location ID: ${payload.locationId || payload.location_id || payload.sub || 'not found'}`);
      console.log(`   Scopes: ${payload.scope || payload.scopes || 'not found'}`);
      console.log(`   User ID: ${payload.user_id || payload.userId || 'not found'}`);
      console.log(`   Company ID: ${payload.company_id || payload.companyId || 'not found'}`);
      console.log(`   Issued At: ${payload.iat ? new Date(payload.iat * 1000).toISOString() : 'not found'}`);
      console.log(`   Expires At: ${payload.exp ? new Date(payload.exp * 1000).toISOString() : 'not found'}`);
      
      // Check if scopes include conversations
      const scopes = payload.scope || payload.scopes || '';
      const hasConversationsRead = scopes.includes('conversations.readonly') || scopes.includes('conversations/message.readonly');
      const hasConversationsWrite = scopes.includes('conversations.write') || scopes.includes('conversations/message.write');
      
      console.log('');
      console.log('🔐 Scope Analysis:');
      console.log('==================');
      console.log(`   Has Conversations Read: ${hasConversationsRead ? '✅' : '❌'}`);
      console.log(`   Has Conversations Write: ${hasConversationsWrite ? '✅' : '❌'}`);
      console.log(`   All Scopes: ${scopes || 'none found'}`);
      
      if (!hasConversationsRead) {
        console.log('');
        console.log('🚨 PROBLEM IDENTIFIED:');
        console.log('======================');
        console.log('   The OAuth token does NOT have conversations permissions!');
        console.log('   This explains why all conversation endpoints return 401/404.');
        console.log('');
        console.log('🔧 SOLUTION:');
        console.log('   1. Need to re-authorize with expanded scopes');
        console.log('   2. Update OAuth app to request conversations permissions');
        console.log('   3. May need High Level account upgrade');
      }
      
    } catch (error) {
      console.log(`❌ Could not decode JWT: ${error.message}`);
      console.log('   This might be an opaque token, not a JWT');
    }
  } else {
    console.log('ℹ️  This appears to be an opaque (non-JWT) token');
    console.log('   Cannot decode to see scopes directly');
  }
  
  console.log('');
  console.log('🎯 Next Steps:');
  console.log('==============');
  console.log('1. Check High Level marketplace app settings');
  console.log('2. Verify scopes include conversations permissions');
  console.log('3. Re-authorize if needed with correct scopes');
  console.log('4. Contact High Level support about API access level');
}

// Run the analysis
analyzeOAuthToken().catch(error => {
  console.error('💥 Token analysis failed:', error.message);
  process.exit(1);
});
