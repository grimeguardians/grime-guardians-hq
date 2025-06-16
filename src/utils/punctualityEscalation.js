// src/utils/punctualityEscalation.js
// Schedules and manages punctuality escalation pings for check-ins
const { DateTime } = require('luxon');
const { sendDiscordPing } = require('./discord');

/**
 * Schedules punctuality escalation for a job/check-in event.
 * @param {Object} params
 * @param {string} params.cleaner - Username or ID of the cleaner
 * @param {string} params.scheduledTime - ISO string of the job start time (local time)
 * @param {function} params.hasCheckedIn - async function returning true if checked in
 * @param {string[]} params.escalationTargets - Array of Discord channel IDs to ping at 10/15 min
 * @param {boolean} [params.simulate=false] - If true, fast-forwards time (1 min = 1 sec)
 * @param {string} [params.opsDM] - Discord username or user ID for direct DM at 10 min
 * @param {string} [params.alertsChannel] - Channel ID for 🚨-alerts logging
 * @param {Object} params.client - Discord client for fetching usernames
 * @returns {Promise<void>}
 */
async function schedulePunctualityEscalation({
  cleaner,
  scheduledTime,
  hasCheckedIn,
  escalationTargets = [],
  simulate = false,
  opsDM,
  alertsChannel,
  client
}) {
  const { DateTime } = require('luxon');
  let cleanerName = cleaner;
  if (client) {
    try {
      // Fetch user object and use displayName or username#discriminator for clarity
      const userObj = await client.users.fetch(cleaner);
      if (userObj) {
        cleanerName = userObj.globalName || `${userObj.username}#${userObj.discriminator}`;
      }
    } catch (e) { /* fallback to ID */ }
  }
  const mention = `<@${cleaner}>`;
  const base = DateTime.fromISO(scheduledTime, { zone: 'America/Chicago' });
  const onTime = base.minus({ minutes: 15 });
  const intervals = [5, 10, 15]; // minutes late
  // Channel messages use mention, DMs use direct text
  const channelMessages = [
    `${mention} is 5 min late for check-in. Please check in ASAP.`,
    `${mention} is 10 min late. Escalating to ops.`,
    `${mention} is 15 min late. Immediate action required!`
  ];
  const dmMessages = [
    `You're 5 minutes late for arrival. What's your ETA?`,
    `You're 10 minutes late for arrival. Please reply with your ETA immediately.`,
    `You're 15 minutes late for arrival. This has been escalated to ops. Reply ASAP.`
  ];
  for (let i = 0; i < intervals.length; i++) {
    const waitMs = (intervals[i] * (simulate ? 1000 : 60000));
    await new Promise(res => setTimeout(res, waitMs));
    if (await hasCheckedIn()) return;
    // DM the cleaner at every escalation point
    await sendDiscordPing(cleaner, dmMessages[i]);
    if (i === 0) {
      // Optionally, also post to channel at 5 min (if desired)
    } else if (i === 1) {
      // Channel escalation at 10 min
      if (opsDM) {
        await sendDiscordPing(opsDM, `${cleanerName} is 10 mins late to arrival`);
      }
      if (alertsChannel) {
        await sendDiscordPing(alertsChannel, channelMessages[i]);
      }
      for (const target of escalationTargets) {
        await sendDiscordPing(target, channelMessages[i]);
      }
    } else {
      // Channel escalation at 15 min
      for (const target of escalationTargets) {
        await sendDiscordPing(target, channelMessages[i]);
      }
    }
  }
}

module.exports = { schedulePunctualityEscalation };
