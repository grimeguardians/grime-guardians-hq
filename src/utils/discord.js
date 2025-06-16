const { Client, GatewayIntentBits } = require('discord.js');
require('dotenv').config();

// Singleton Discord client for utility use
let discordClient = null;
function getDiscordClient() {
  if (!discordClient) {
    discordClient = new Client({ intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.DirectMessages
    ] });
    discordClient.login(process.env.DISCORD_BOT_TOKEN);
  }
  return discordClient;
}

/**
 * Send a ping/message to a Discord user or channel
 * @param {string} target - Username, user ID, or channel ID
 * @param {string} message - Message to send
 */
async function sendDiscordPing(target, message) {
  const client = getDiscordClient();
  // Wait for client to be ready
  if (!client.isReady()) {
    await new Promise(res => client.once('ready', res));
  }
  // Try channel by ID (fetch if not cached)
  let channel = client.channels.cache.get(target);
  if (!channel) {
    try {
      channel = await client.channels.fetch(target);
    } catch (e) { /* ignore */ }
  }
  if (channel && channel.send) {
    await channel.send(message);
    return;
  }
  // Try user by ID
  try {
    const user = await client.users.fetch(target);
    if (user) {
      await user.send(message);
      return;
    }
  } catch (e) {}
  // Try user by username (first match)
  const user = client.users.cache.find(u => u.username === target);
  if (user) {
    await user.send(message);
    return;
  }
  throw new Error('Discord target not found: ' + target);
}

module.exports = {
  sendDiscordPing,
};