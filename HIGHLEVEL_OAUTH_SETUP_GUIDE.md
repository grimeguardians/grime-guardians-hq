# High Level OAuth 2.0 Setup Guide

## Overview
This guide walks through setting up High Level OAuth 2.0 integration to access conversations and messages APIs, which are required for SMS monitoring and management.

## Current Setup Status
✅ OAuth redirect URI configured: `http://localhost:3000/oauth/callback/gohighlevel`  
✅ OAuth handler created: `src/utils/highlevelOAuth.js`  
✅ Express callback route added: `/oauth/callback/gohighlevel`  
✅ Server configured to listen on port 3000  
⏳ **PENDING:** Client ID and Secret from High Level dev portal  

## Step 1: Create OAuth App in High Level Developer Portal

1. Go to [High Level Marketplace Developer Portal](https://marketplace.gohighlevel.com/)
2. Sign in with your High Level account
3. Navigate to "Apps" or "Integrations"
4. Click "Create New App" or "Add Integration"
5. Fill out the app details:
   - **App Name:** Grime Guardians Automation
   - **Description:** Backend automation for cleaning operations
   - **Redirect URI:** `http://localhost:3000/oauth/callback/gohighlevel`
   - **Scopes:** 
     - `conversations/message.readonly`
     - `conversations/message.write`

## Step 2: Update Environment Variables

After creating the app, you'll receive a Client ID and Client Secret. Add them to your `.env` file:

```bash
# High Level OAuth 2.0 (replace with your actual values)
HIGHLEVEL_OAUTH_CLIENT_ID=your_client_id_here
HIGHLEVEL_OAUTH_CLIENT_SECRET=your_client_secret_here
HIGHLEVEL_OAUTH_REDIRECT_URI=http://localhost:3000/oauth/callback/gohighlevel
HIGHLEVEL_OAUTH_ACCESS_TOKEN=
HIGHLEVEL_OAUTH_REFRESH_TOKEN=
```

## Step 3: Test OAuth Flow Locally

1. **Start the Grime Guardians system:**
   ```bash
   cd "/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ"
   node src/index.js
   ```

2. **Generate authorization URL:**
   ```bash
   node scripts/generate-highlevel-oauth-url.js
   ```

3. **Complete OAuth flow:**
   - Open the generated URL in your browser
   - Sign in to High Level if prompted
   - Authorize the app for your location/account
   - You'll be redirected to `http://localhost:3000/oauth/callback/gohighlevel`
   - The system will automatically exchange the code for tokens

4. **Verify tokens were saved:**
   - Check your `.env` file for populated `HIGHLEVEL_OAUTH_ACCESS_TOKEN` and `HIGHLEVEL_OAUTH_REFRESH_TOKEN`
   - Check console output for confirmation messages

## Step 4: Test API Access

Once tokens are obtained, the system will automatically use them for High Level API calls. You can verify by:

1. **Check monitoring logs:**
   ```bash
   # Look for High Level conversation monitoring messages
   tail -f logs/system.log | grep "High Level"
   ```

2. **Send a test SMS:**
   - Send an SMS to your High Level phone number
   - Check Discord for monitoring alerts
   - Verify the system can detect and respond to the message

## Troubleshooting

### Common Issues:

1. **"Invalid redirect_uri" error:**
   - Ensure the redirect URI in your High Level app exactly matches: `http://localhost:3000/oauth/callback/gohighlevel`
   - No trailing slashes or extra characters

2. **"Invalid client_id" error:**
   - Double-check the Client ID in your `.env` file matches the one from High Level

3. **Token exchange fails:**
   - Verify Client Secret is correct
   - Check that scopes match what was configured in the app

4. **Still getting 404 on conversations API:**
   - OAuth may take time to propagate permissions
   - Try refreshing tokens or re-authorizing
   - Ensure your High Level account has the necessary permissions

### Debug Commands:

```bash
# Test OAuth URL generation
node scripts/generate-highlevel-oauth-url.js

# Check current environment variables
grep HIGHLEVEL .env

# Test API endpoints after OAuth
node -e "
const { testHighLevelAPI } = require('./src/utils/highlevelOAuth');
testHighLevelAPI().then(console.log).catch(console.error);
"
```

## Production Deployment

For production deployment, you'll need to:

1. Update the redirect URI to your production domain
2. Create a new OAuth app or update the existing one with the production URI
3. Update environment variables on your production server
4. Ensure your production server can receive the OAuth callback

## Security Notes

- Keep Client Secret secure and never commit it to version control
- Tokens are automatically refreshed when they expire
- Access tokens are saved to `.env` for persistence across restarts
- Consider using a secrets management service for production

## Current Integration Status

- ✅ Google Voice SMS monitoring via Gmail API
- ✅ Discord DM alerts with approval workflow
- ✅ High Level v1 API (contacts only)
- ⏳ High Level v2 API with OAuth (conversations/messages)
- ⏳ Unified response management across both channels

Once OAuth is complete, the system will have full access to both communication channels with seamless monitoring and response capabilities.
