// src/utils/discordUserMapping.js
// Discord user mapping utilities to convert usernames to user IDs for mentions and DMs

/**
 * Cache for Discord username to user ID mappings
 */
const userCache = new Map();

/**
 * Map Discord username to user ID using the Discord client
 * @param {Object} client - Discord client instance
 * @param {string} username - Discord username to lookup
 * @returns {Promise<string|null>} Discord user ID or null if not found
 */
async function getUserIdFromUsername(client, username) {
  try {
    // Check cache first
    if (userCache.has(username.toLowerCase())) {
      return userCache.get(username.toLowerCase());
    }
    
    // Search through all guilds the bot has access to
    const guilds = client.guilds.cache;
    
    for (const [guildId, guild] of guilds) {
      try {
        // Search by username (without discriminator)
        const member = guild.members.cache.find(member => 
          member.user.username.toLowerCase() === username.toLowerCase() ||
          member.displayName.toLowerCase() === username.toLowerCase()
        );
        
        if (member) {
          // Cache the result
          userCache.set(username.toLowerCase(), member.user.id);
          console.log(`[Discord] Mapped username "${username}" to user ID: ${member.user.id}`);
          return member.user.id;
        }
      } catch (error) {
        console.error(`[Discord] Error searching guild ${guild.name}:`, error.message);
      }
    }
    
    console.warn(`[Discord] Could not find user ID for username: ${username}`);
    return null;
  } catch (error) {
    console.error('[Discord] Error in getUserIdFromUsername:', error);
    return null;
  }
}

/**
 * Get user display name from user ID
 * @param {Object} client - Discord client instance
 * @param {string} userId - Discord user ID
 * @returns {Promise<string>} Display name or username
 */
async function getDisplayNameFromUserId(client, userId) {
  try {
    const user = await client.users.fetch(userId);
    return user.globalName || user.username;
  } catch (error) {
    console.error(`[Discord] Error fetching user ${userId}:`, error);
    return userId; // fallback to ID
  }
}

/**
 * Create a Discord mention string from username
 * @param {Object} client - Discord client instance
 * @param {string} username - Discord username
 * @returns {Promise<string>} Discord mention string or fallback text
 */
async function createMentionFromUsername(client, username) {
  const userId = await getUserIdFromUsername(client, username);
  if (userId) {
    return `<@${userId}>`;
  }
  return `@${username}`; // fallback to text mention
}

/**
 * Bulk map multiple usernames to user IDs
 * @param {Object} client - Discord client instance
 * @param {Array<string>} usernames - Array of usernames to map
 * @returns {Promise<Map>} Map of username -> user ID
 */
async function bulkMapUsernameToId(client, usernames) {
  const results = new Map();
  
  for (const username of usernames) {
    const userId = await getUserIdFromUsername(client, username);
    if (userId) {
      results.set(username, userId);
    }
  }
  
  return results;
}

/**
 * Clear the user cache (useful for testing or periodic cleanup)
 */
function clearUserCache() {
  userCache.clear();
  console.log('[Discord] User cache cleared');
}

/**
 * Get cache statistics
 * @returns {Object} Cache statistics
 */
function getCacheStats() {
  return {
    size: userCache.size,
    entries: Array.from(userCache.entries())
  };
}

/**
 * Pre-populate cache with known user mappings
 * @param {Object} mappings - Object with username -> userId mappings
 */
function prePopulateCache(mappings) {
  for (const [username, userId] of Object.entries(mappings)) {
    userCache.set(username.toLowerCase(), userId);
  }
  console.log(`[Discord] Pre-populated cache with ${Object.keys(mappings).length} mappings`);
}

module.exports = {
  getUserIdFromUsername,
  getDisplayNameFromUserId,
  createMentionFromUsername,
  bulkMapUsernameToId,
  clearUserCache,
  getCacheStats,
  prePopulateCache
};
