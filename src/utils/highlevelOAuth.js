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
    this.tokenExpiry = process.env.HIGHLEVEL_TOKEN_EXPIRY || null;
    this.rateLimitBuffer = 100; // Buffer for rate limit (ms between requests)
    this.lastRequestTime = 0;
  }

  /**
   * Generate authorization URL for OAuth flow
   * @returns {string} Authorization URL
   */
  getAuthUrl() {
    const scopes = 'contacts.readonly contacts.write conversations.readonly conversations.write conversations/message.readonly conversations/message.write locations.readonly';
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
    
    // Calculate token expiry (24 hours from now as per High Level docs)
    const expiryTime = Date.now() + (24 * 60 * 60 * 1000); // 24 hours in milliseconds
    this.tokenExpiry = expiryTime;

    // Update .env file
    const envPath = path.join(process.cwd(), '.env');
    let envContent = fs.readFileSync(envPath, 'utf8');

    // Update or add token lines
    const updates = {
      'HIGHLEVEL_OAUTH_ACCESS_TOKEN': tokens.access_token,
      'HIGHLEVEL_OAUTH_REFRESH_TOKEN': tokens.refresh_token,
      'HIGHLEVEL_TOKEN_EXPIRY': expiryTime.toString()
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
    console.log(`🕒 Access token expires in 24 hours: ${new Date(expiryTime).toISOString()}`);
  }

  /**
   * Check if access token is expired or will expire soon
   * @returns {boolean} True if token needs refresh
   */
  isTokenExpired() {
    if (!this.tokenExpiry) return true;
    
    // Refresh if token expires within 1 hour (buffer time)
    const oneHour = 60 * 60 * 1000;
    return Date.now() >= (parseInt(this.tokenExpiry) - oneHour);
  }

  /**
   * Implement rate limiting to respect High Level's limits
   * @returns {Promise<void>}
   */
  async rateLimitDelay() {
    const timeSinceLastRequest = Date.now() - this.lastRequestTime;
    if (timeSinceLastRequest < this.rateLimitBuffer) {
      const delay = this.rateLimitBuffer - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    this.lastRequestTime = Date.now();
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

    // Check if token is expired and refresh if needed
    if (this.isTokenExpired()) {
      console.log('🔄 Access token expired or expiring soon, refreshing...');
      await this.refreshAccessToken();
    }

    // Apply rate limiting
    await this.rateLimitDelay();

    // Add authorization header
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      Accept: 'application/json',
      'Version': '2021-07-28', // High Level API version
      ...options.headers
    };

    let response = await fetch(url, {
      ...options,
      headers
    });

    // Handle rate limiting (429 status)
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : 5000; // Default 5 seconds
      
      console.log(`⏳ Rate limited, waiting ${delay/1000} seconds...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Retry request
      return this.makeAuthenticatedRequest(url, options);
    }

    // If unauthorized, try to refresh token once more
    if (response.status === 401 && !this.isTokenExpired()) {
      console.log('🔄 Received 401, attempting token refresh...');
      
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
   * @param {Object} options - Query options (limit, skip, search, etc.)
   * @returns {Promise<Array>} Array of conversation objects
   */
  async getConversations(options = {}) {
    const params = new URLSearchParams({
      locationId: process.env.HIGHLEVEL_LOCATION_ID,
      limit: options.limit || 50,
      skip: options.skip || 0,
      ...options
    });
    
    const url = `https://services.leadconnectorhq.com/conversations?${params.toString()}`;
    
    const response = await this.makeAuthenticatedRequest(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Conversations API failed: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.conversations || [];
  }

  /**
   * Get messages for a specific conversation
   * @param {string} conversationId - Conversation ID
   * @param {Object} options - Query options
   * @returns {Promise<Array>} Array of message objects
   */
  async getMessages(conversationId, options = {}) {
    const params = new URLSearchParams({
      limit: options.limit || 20,
      skip: options.skip || 0,
      ...options
    });
    
    const url = `https://services.leadconnectorhq.com/conversations/${conversationId}/messages?${params.toString()}`;
    
    const response = await this.makeAuthenticatedRequest(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Messages API failed: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.messages || [];
  }

  /**
   * Send message using OAuth token
   * @param {string} contactId - Contact ID
   * @param {string} message - Message content
   * @param {string} type - Message type (SMS, Email, etc.)
   * @returns {Promise<Object>} Send response
   */
  async sendMessage(contactId, message, type = 'SMS') {
    const url = 'https://services.leadconnectorhq.com/conversations/messages';
    
    const response = await this.makeAuthenticatedRequest(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: type,
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
   * Get contact information
   * @param {string} contactId - Contact ID
   * @returns {Promise<Object>} Contact object
   */
  async getContact(contactId) {
    const url = `https://services.leadconnectorhq.com/contacts/${contactId}`;
    
    const response = await this.makeAuthenticatedRequest(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Get contact failed: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.contact;
  }

  /**
   * Search contacts by phone number or email
   * @param {string} query - Phone number or email to search
   * @returns {Promise<Array>} Array of matching contacts
   */
  async searchContacts(query) {
    const params = new URLSearchParams({
      locationId: process.env.HIGHLEVEL_LOCATION_ID,
      query: query
    });
    
    const url = `https://services.leadconnectorhq.com/contacts/search?${params.toString()}`;
    
    const response = await this.makeAuthenticatedRequest(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Search contacts failed: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.contacts || [];
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
      token_status: {
        has_access_token: !!this.accessToken,
        has_refresh_token: !!this.refreshToken,
        token_expired: this.isTokenExpired(),
        expiry_time: this.tokenExpiry ? new Date(parseInt(this.tokenExpiry)).toISOString() : 'unknown'
      },
      contacts_v2: null,
      conversations_v2: null,
      location_access: null
    };

    try {
      // Test v2 contacts endpoint
      const contactsResponse = await this.makeAuthenticatedRequest('https://services.leadconnectorhq.com/contacts/', {
        method: 'GET'
      });
      results.contacts_v2 = { 
        status: contactsResponse.status, 
        ok: contactsResponse.ok,
        headers: Object.fromEntries(contactsResponse.headers.entries())
      };

      // Test v2 conversations endpoint
      const conversationsResponse = await this.makeAuthenticatedRequest(`https://services.leadconnectorhq.com/conversations?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`, {
        method: 'GET'
      });
      results.conversations_v2 = { 
        status: conversationsResponse.status, 
        ok: conversationsResponse.ok,
        headers: Object.fromEntries(conversationsResponse.headers.entries())
      };

      // Test location access
      const locationResponse = await this.makeAuthenticatedRequest(`https://services.leadconnectorhq.com/locations/${process.env.HIGHLEVEL_LOCATION_ID}`, {
        method: 'GET'
      });
      results.location_access = { 
        status: locationResponse.status, 
        ok: locationResponse.ok,
        headers: Object.fromEntries(locationResponse.headers.entries())
      };

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
