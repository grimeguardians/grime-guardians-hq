// src/utils/highlevelOAuth.js
// High Level OAuth 2.0 integration for conversations API access

const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

class HighLevelOAuth {
  constructor() {
    this.clientId = process.env.HIGHLEVEL_OAUTH_CLIENT_ID;
    this.clientSecret = process.env.HIGHLEVEL_OAUTH_CLIENT_SECRET;
    this.redirectUri = process.env.HIGHLEVEL_OAUTH_REDIRECT_URI;
    this.accessToken = process.env.HIGHLEVEL_OAUTH_ACCESS_TOKEN;
    this.refreshToken = process.env.HIGHLEVEL_OAUTH_REFRESH_TOKEN;
  }

  /**
   * Generate authorization URL for OAuth flow
   * @returns {string} Authorization URL
   */
  getAuthUrl() {
    const scopes = 'conversations/message.readonly conversations/message.write';
    const baseUrl = 'https://marketplace.gohighlevel.com/oauth/chooselocation';
    
    const params = new URLSearchParams({
      response_type: 'code',
      redirect_uri: this.redirectUri,
      client_id: this.clientId,
      scope: scopes
    });

    return `${baseUrl}?${params.toString()}`;
  }

  /**
   * Exchange authorization code for access token
   * @param {string} code - Authorization code from callback
   * @returns {Promise<Object>} Token response
   */
  async exchangeCodeForTokens(code) {
    const tokenUrl = 'https://services.leadconnectorhq.com/oauth/token';
    
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: new URLSearchParams({
        client_id: this.clientId,
        client_secret: this.clientSecret,
        grant_type: 'authorization_code',
        code: code,
        redirect_uri: this.redirectUri,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Token exchange failed: ${response.status} - ${errorText}`);
    }

    const tokens = await response.json();
    
    // Save tokens to environment and file
    await this.saveTokens(tokens);
    
    return tokens;
  }

  /**
   * Refresh access token using refresh token
   * @returns {Promise<Object>} New token response
   */
  async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const tokenUrl = 'https://services.leadconnectorhq.com/oauth/token';
    
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: new URLSearchParams({
        client_id: this.clientId,
        client_secret: this.clientSecret,
        grant_type: 'refresh_token',
        refresh_token: this.refreshToken,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Token refresh failed: ${response.status} - ${errorText}`);
    }

    const tokens = await response.json();
    
    // Save new tokens
    await this.saveTokens(tokens);
    
    return tokens;
  }

  /**
   * Save tokens to environment file
   * @param {Object} tokens - Token response object
   */
  async saveTokens(tokens) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;

    // Update .env file
    const envPath = path.join(process.cwd(), '.env');
    let envContent = fs.readFileSync(envPath, 'utf8');

    // Update or add token lines
    const updates = {
      'HIGHLEVEL_OAUTH_ACCESS_TOKEN': tokens.access_token,
      'HIGHLEVEL_OAUTH_REFRESH_TOKEN': tokens.refresh_token
    };

    for (const [key, value] of Object.entries(updates)) {
      const regex = new RegExp(`^${key}=.*$`, 'm');
      if (regex.test(envContent)) {
        envContent = envContent.replace(regex, `${key}=${value}`);
      } else {
        envContent += `\n${key}=${value}`;
      }
    }

    fs.writeFileSync(envPath, envContent);
    console.log('✅ High Level OAuth tokens saved to .env file');
  }

  /**
   * Make authenticated API request with automatic token refresh
   * @param {string} url - API endpoint URL
   * @param {Object} options - Fetch options
   * @returns {Promise<Response>} API response
   */
  async makeAuthenticatedRequest(url, options = {}) {
    if (!this.accessToken) {
      throw new Error('No access token available. Please complete OAuth flow first.');
    }

    // Add authorization header
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      Accept: 'application/json',
      ...options.headers
    };

    let response = await fetch(url, {
      ...options,
      headers
    });

    // If unauthorized, try to refresh token
    if (response.status === 401) {
      console.log('🔄 Access token expired, refreshing...');
      
      try {
        await this.refreshAccessToken();
        
        // Retry request with new token
        headers.Authorization = `Bearer ${this.accessToken}`;
        response = await fetch(url, {
          ...options,
          headers
        });
      } catch (refreshError) {
        throw new Error(`Token refresh failed: ${refreshError.message}`);
      }
    }

    return response;
  }

  /**
   * Get conversations using OAuth token
   * @returns {Promise<Array>} Array of conversation objects
   */
  async getConversations() {
    const url = `https://services.leadconnectorhq.com/conversations?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=50`;
    
    const response = await this.makeAuthenticatedRequest(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Conversations API failed: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.conversations || [];
  }

  /**
   * Send message using OAuth token
   * @param {string} contactId - Contact ID
   * @param {string} message - Message content
   * @returns {Promise<Object>} Send response
   */
  async sendMessage(contactId, message) {
    const url = 'https://services.leadconnectorhq.com/conversations/messages';
    
    const response = await this.makeAuthenticatedRequest(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'SMS',
        contactId: contactId,
        message: message,
        locationId: process.env.HIGHLEVEL_LOCATION_ID
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Send message failed: ${response.status} - ${errorText}`);
    }

    return await response.json();
  }

  /**
   * Test API access with current tokens
   * @returns {Promise<Object>} Test results
   */
  async testAPIAccess() {
    if (!this.accessToken) {
      return { success: false, error: 'No access token available' };
    }

    const results = {
      contacts_v1: null,
      contacts_v2: null,
      conversations_v2: null,
      messages_v2: null
    };

    try {
      // Test v1 contacts
      const v1Response = await fetch('https://rest.gohighlevel.com/v1/contacts/', {
        headers: { 'Authorization': `Bearer ${this.accessToken}` }
      });
      results.contacts_v1 = { status: v1Response.status, ok: v1Response.ok };

      // Test v2 contacts
      const v2Response = await fetch('https://services.leadconnectorhq.com/contacts/', {
        headers: { 
          'Authorization': `Bearer ${this.accessToken}`,
          'Version': '2021-07-28'
        }
      });
      results.contacts_v2 = { status: v2Response.status, ok: v2Response.ok };

      // Test v2 conversations
      const convResponse = await fetch('https://services.leadconnectorhq.com/conversations/', {
        headers: { 
          'Authorization': `Bearer ${this.accessToken}`,
          'Version': '2021-07-28'
        }
      });
      results.conversations_v2 = { status: convResponse.status, ok: convResponse.ok };

      // Test v2 messages (if we have a conversation ID, this would need one)
      results.messages_v2 = { status: 'N/A', note: 'Requires conversation ID' };

      return { success: true, results };
    } catch (error) {
      return { success: false, error: error.message, results };
    }
  }

  /**
   * Check if OAuth is configured and tokens are available
   * @returns {boolean} True if OAuth is ready
   */
  isConfigured() {
    return !!(this.clientId && this.clientSecret && this.accessToken);
  }
}

module.exports = HighLevelOAuth;
