#!/usr/bin/env node

/**
 * High Level Token Inspector
 * Decode and inspect the OAuth token to see what scopes were granted
 */

require('dotenv').config();

function inspectToken() {
  console.log('🔍 High Level OAuth Token Inspector');
  console.log('====================================\n');
  
  const accessToken = process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN;
  
  if (!accessToken) {
    console.log('❌ No access token found in .env');
    return;
  }
  
  console.log('🔑 Access Token Found');
  console.log(`Length: ${accessToken.length} characters`);
  console.log(`Starts with: ${accessToken.substring(0, 20)}...`);
  
  // JWT tokens have 3 parts separated by dots
  const parts = accessToken.split('.');
  console.log(`\n📋 Token Structure:`);
  console.log(`   • Parts: ${parts.length} (${parts.length === 3 ? 'JWT format' : 'Not JWT'})`);
  
  if (parts.length === 3) {
    try {
      // Decode JWT payload (base64)
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
      console.log('\n🔓 Token Payload:');
      console.log(JSON.stringify(payload, null, 2));
      
      if (payload.scope) {
        console.log(`\n✅ Scopes Found: ${payload.scope}`);
      } else {
        console.log('\n❌ No scopes in token payload!');
      }
      
      if (payload.locationId) {
        console.log(`📍 Location ID: ${payload.locationId}`);
      }
      
      if (payload.exp) {
        const expiry = new Date(payload.exp * 1000);
        console.log(`⏰ Expires: ${expiry.toISOString()}`);
      }
      
    } catch (error) {
      console.log('\n❌ Failed to decode JWT payload:', error.message);
    }
  } else {
    console.log('\n💡 This appears to be an opaque token (not JWT)');
    console.log('   Scopes might be stored server-side by High Level');
  }
  
  // Check what scopes we requested
  console.log('\n📝 Scopes We Requested:');
  console.log('   contacts.readonly contacts.write');
  console.log('   conversations.readonly conversations.write');
  console.log('   conversations/message.readonly conversations/message.write');
  console.log('   locations.readonly');
  
  console.log('\n💡 Next Steps:');
  console.log('   1. Re-authorize with specific scopes');
  console.log('   2. Check High Level app permissions');
  console.log('   3. Contact High Level support if needed');
}

inspectToken();
