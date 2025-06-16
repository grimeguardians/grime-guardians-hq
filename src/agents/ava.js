// Remove Discord bot startup code from this file. Ava is now a class only.
// All Discord client logic is in src/index.js

const Agent = require('./agent');
const axios = require('axios');

class Ava extends Agent {
  constructor(client) {
    super({ agentId: 'ava', role: 'Master orchestrator' });
    this.client = client;
    this.jobMap = new Map();
  }

  onReady() {
    console.log('Ava agent is ready.');
  }

  generateJobId(username, isoTimestamp) {
    const d = new Date(isoTimestamp);
    const datePart = d
      .toLocaleDateString('en-US', {
        timeZone: 'America/Chicago',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      })
      .replace(/\//g, '');
    const randomNum = Math.floor(Math.random() * 1000)
      .toString()
      .padStart(3, '0');
    return `${username}-${datePart}-${randomNum}`;
  }

  async getContext(event) {
    // Implement context pull from Notion or other sources as needed
    // For now, return event as context
    return event;
  }

  async handleEvent(event, context) {
    // Main agentic logic for Ava (refactored from handleMessage)
    const content = event.content.toLowerCase();
    const timestamp = new Date().toISOString();
    const arrivalTriggers = ['🚗','arrived',"i've arrived",'here',"i'm here",'starting'];
    const hasArrivalTrigger = arrivalTriggers.some(t => content.includes(t));
    if (hasArrivalTrigger) {
      const jobId = this.generateJobId(event.author.username, timestamp);
      this.jobMap.set(event.author.username, jobId);
      const payload = {
        username: event.author.username,
        message: event.content + ' 🚗',
        timestamp,
        action: 'arrived',
        jobId,
      };
      // Example: Log to console for now
      console.log('ARRIVED payload:', payload);
      return this.formatOutput({
        task: 'checkin',
        actionRequired: 'log_arrival',
        confidence: 1.0,
        extra: { payload }
      });
    }
    const finishedTriggers = ['🏁','finished',"i'm finished",'done','all done'];
    const hasFinishedTrigger = finishedTriggers.some(t => content.includes(t));
    if (hasFinishedTrigger) {
      const jobId = this.jobMap.get(event.author.username) || null;
      const payload = {
        username: event.author.username,
        message: event.content + ' 🏁',
        timestamp,
        action: 'finished',
        jobId,
      };
      // Example: Log to console for now
      console.log('FINISHED payload:', payload);
      return this.formatOutput({
        task: 'checkout',
        actionRequired: 'log_completion',
        confidence: 1.0,
        extra: { payload }
      });
    }
    // No action
    return null;
  }

  // For Discord compatibility
  async handleMessage(message) {
    const event = {
      content: message.content,
      author: { username: message.author.username },
      channel: message.channel,
    };
    const context = await this.getContext(event);
    const result = await this.handleEvent(event, context);
    if (result && message.channel && message.channel.send) {
      if (result.task === 'checkin') {
        await message.channel.send(`✅ Got it, ${message.author.username} — you're checked in! 🚗`);
      } else if (result.task === 'checkout') {
        await message.channel.send(`🎉 Great work, ${message.author.username}! Job marked as finished.`);
      }
    }
    return result;
  }
}

module.exports = Ava;