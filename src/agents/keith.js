const Agent = require('./agent');
const fs = require('fs');
const { logStrike } = require('../utils/notion');

class Keith extends Agent {
  constructor(client) {
    super({ agentId: 'keith', role: 'Check-in monitor' });
    this.client = client;
  }
  onReady() {
    console.log('Keith agent is ready.');
  }
  async getContext(event) {
    // Implement context pull from Notion or other sources as needed
    return event;
  }
  async handleEvent(event, context) {
    const content = event.content;
    const contentLower = content.toLowerCase();
    const timestamp = new Date().toISOString();
    // --- STRIKE/VIOLATION LOGIC ---
    // Define lateness threshold (e.g., after 8:05 AM is late)
    const LATE_HOUR = 8;
    const LATE_MINUTE = 5;
    let isLate = false;
    const now = new Date(timestamp);
    if (now.getHours() > LATE_HOUR || (now.getHours() === LATE_HOUR && now.getMinutes() > LATE_MINUTE)) {
      isLate = true;
    }
    // Load or initialize strike memory (pillar-specific, rolling 30 days)
    const memoryPath = './COO_Memory_Stack (8).json';
    let memory = {};
    try {
      if (fs.existsSync(memoryPath)) {
        memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));
      }
    } catch (e) { memory = {}; }
    const user = event.author.username;
    if (!memory[user]) memory[user] = { punctuality: [], quality: [] };
    // Remove strikes older than 30 days
    const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;
    const cutoff = Date.now() - THIRTY_DAYS_MS;
    ['punctuality', 'quality'].forEach(pillar => {
      memory[user][pillar] = (memory[user][pillar] || []).filter(s => new Date(s.timestamp).getTime() >= cutoff);
    });
    // Check-in triggers (expanded)
    const arrivalTriggers = [
      '🚗', 'arrived', "i've arrived", 'here', "i'm here", 'starting', 'start', 'on site', 'onsite', 'checked in', 'check in', 'begin', 'beginning', 'at job', 'at work', 'at site', 'at location'
    ];
    const hasArrivalTrigger = arrivalTriggers.some(t => contentLower.includes(t));
    if (hasArrivalTrigger) {
      // Extract notes: everything after the first trigger word/emoji
      let notes = '';
      for (const trigger of arrivalTriggers) {
        const idx = contentLower.indexOf(trigger);
        if (idx !== -1) {
          notes = content.slice(idx + trigger.length).trim();
          notes = notes.replace(/^([.,-\s]+)/, '');
          break;
        }
      }
      // Strike logic: increment punctuality if late
      let strikeAdded = false;
      if (isLate) {
        memory[user].punctuality.push({ timestamp, type: 'late' });
        strikeAdded = true;
        fs.writeFileSync(memoryPath, JSON.stringify(memory, null, 2));
        // Log to Notion Strikes DB
        await logStrike({
          username: user,
          timestamp,
          type: 'punctuality',
          notes: notes || ''
        });
      }
      const payload = {
        user,
        content: event.content,
        channel: event.channel.name || event.channel.id,
        timestamp,
        notes: notes || undefined,
        isLate,
        punctualityStrikes: memory[user].punctuality.length,
        qualityStrikes: memory[user].quality.length,
        strikeAdded
      };
      console.log('[Keith] Check-in detected:', payload);
      return this.formatOutput({
        task: 'checkin',
        actionRequired: strikeAdded ? 'flag_late' : 'review_or_log',
        confidence: 1.0,
        extra: { payload }
      });
    }
    // Check-out triggers (expanded)
    const finishedTriggers = [
      '🏁', 'finished', "i'm finished", 'done', 'all done', 'complete', 'completed', 'checkout', 'checked out', 'leaving', 'leaving site', 'leaving work', 'leaving job', 'leaving location', 'job done', 'job finished', 'job complete', 'job completed', 'out', 'outta here', 'clocking out', 'clock out', 'punching out', 'punch out'
    ];
    const hasFinishedTrigger = finishedTriggers.some(t => contentLower.includes(t));
    if (hasFinishedTrigger) {
      // Extract notes: everything after the first trigger word/emoji
      let notes = '';
      for (const trigger of finishedTriggers) {
        const idx = contentLower.indexOf(trigger);
        if (idx !== -1) {
          notes = content.slice(idx + trigger.length).trim();
          // Remove leading punctuation and whitespace
          notes = notes.replace(/^([.,-\s]+)/, '');
          break;
        }
      }
      const payload = {
        user: event.author.username,
        content: event.content,
        channel: event.channel.name || event.channel.id,
        timestamp,
        notes: notes || undefined
      };
      console.log('[Keith] Check-out detected:', payload);
      return this.formatOutput({
        task: 'checkout',
        actionRequired: 'review_or_log',
        confidence: 1.0,
        extra: { payload }
      });
    }
    // Quality/complaint strike logic (triggered by complaint keywords or events)
    const complaintTriggers = [
      'complaint', 'issue', 'problem', 'damage', 'client unhappy', 'client complaint', 'missed spot', 'redo', 'reclean', 'callback', 'negative feedback', 'unsatisfied', 'not satisfied', 'not happy', 'bad review', 'poor job', 'quality issue', 'quality concern',
      'could have been better', 'wasn\'t great', 'not up to standard', 'disappointed', 'let down', 'expected more', 'not impressed', 'subpar', 'mediocre', 'barely acceptable', 'not what I hoped', 'room for improvement', 'wasn\'t thorough', 'overlooked', 'missed details', 'not as promised', 'not worth it', 'felt rushed', 'not attentive', 'seemed careless', 'not the best', 'not ideal', 'not what I paid for', 'not what I expected', 'almost good', 'just okay', 'could use work', 'not quite right', 'not fully satisfied', 'not the usual', 'not your best', 'could be improved', 'not up to par'
    ];
    const hasComplaintTrigger = complaintTriggers.some(t => contentLower.includes(t));
    if (hasComplaintTrigger) {
      // Add a quality strike
      memory[user].quality.push({ timestamp, type: 'quality' });
      fs.writeFileSync(memoryPath, JSON.stringify(memory, null, 2));
      // Log to Notion Strikes DB
      await logStrike({
        username: user,
        timestamp,
        type: 'quality',
        notes: event.content
      });
      const payload = {
        user,
        content: event.content,
        channel: event.channel.name || event.channel.id,
        timestamp,
        qualityStrikes: memory[user].quality.length,
        complaintDetected: true
      };
      console.log('[Keith] Quality/complaint detected:', payload);
      return this.formatOutput({
        task: 'quality_strike',
        actionRequired: 'flag_quality',
        confidence: 1.0,
        extra: { payload }
      });
    }
    // Default: just log
    const payload = {
      user: event.author.username,
      content: event.content,
      channel: event.channel.name || event.channel.id,
      timestamp,
    };
    console.log('[Keith] Message received in check-in channel:', payload);
    return this.formatOutput({
      task: 'other',
      actionRequired: 'review_or_log',
      confidence: 1.0,
      extra: { payload }
    });
  }
  async handleMessage(message) {
    const event = {
      content: message.content,
      author: { username: message.author.username },
      channel: message.channel,
    };
    const context = await this.getContext(event);
    const result = await this.handleEvent(event, context);
    // Keith does not reply to user; only logs or triggers actions
    return result;
  }
}

module.exports = Keith;