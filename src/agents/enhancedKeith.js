// src/agents/enhancedKeith.js
// Keith agent enhanced with MCP integration and workflow separation

const Agent = require('./agent');
const { getMCPClient } = require('../utils/mcpClient');

class EnhancedKeith extends Agent {
  constructor(client) {
    super({ agentId: 'keith', role: 'Attendance & Punctuality Manager' });
    this.client = client;
    this.mcpClient = null;
  }

  async initialize() {
    this.mcpClient = await getMCPClient();
    console.log('Keith agent initialized with MCP integration.');
  }

  async getContext(event) {
    // Use MCP to get cleaner profile and recent strikes
    try {
      const username = event.author.username;
      const [profile, recentStrikes] = await Promise.all([
        this.mcpClient.getCleanerProfile(username),
        this.mcpClient.queryStrikes(username, 30) // Last 30 days
      ]);

      return {
        event,
        profile: profile.content[0]?.text ? JSON.parse(profile.content[0].text.split(':\n')[1]) : null,
        recentStrikes: recentStrikes.content[0]?.text ? JSON.parse(recentStrikes.content[0].text.split(':\n')[1]) : []
      };
    } catch (error) {
      console.error('[Keith] Failed to get context via MCP:', error);
      return { event, profile: null, recentStrikes: [] };
    }
  }

  async handleEvent(event, context) {
    const content = event.content.toLowerCase();
    const timestamp = new Date().toISOString();
    const username = event.author.username;

    // WORKFLOW: Check-in detection (deterministic logic)
    const checkinResult = await this.processCheckin(content, username, timestamp, context);
    if (checkinResult) return checkinResult;

    // WORKFLOW: Check-out detection (deterministic logic)  
    const checkoutResult = await this.processCheckout(content, username, timestamp, context);
    if (checkoutResult) return checkoutResult;

    // AGENTIC: Quality/complaint analysis (requires judgment)
    const qualityResult = await this.analyzeQualityIssues(content, username, timestamp, context);
    if (qualityResult) return qualityResult;

    // Default response
    return this.formatOutput({
      task: 'monitor',
      actionRequired: 'none',
      confidence: 0.1,
      extra: { message: 'Message monitored but no action required' }
    });
  }

  // WORKFLOW FUNCTION: Deterministic check-in processing
  async processCheckin(content, username, timestamp, context) {
    const arrivalTriggers = [
      '🚗', 'arrived', "i've arrived", 'here', "i'm here", 'starting',
      'checked in', 'check in', 'clocking in', 'at location', 'on site'
    ];

    const hasArrivalTrigger = arrivalTriggers.some(trigger => content.includes(trigger));
    if (!hasArrivalTrigger) return null;

    // Extract notes
    let notes = '';
    for (const trigger of arrivalTriggers) {
      const idx = content.indexOf(trigger);
      if (idx !== -1) {
        notes = content.slice(idx + trigger.length).trim();
        notes = notes.replace(/^([.,-\s]+)/, '');
        break;
      }
    }

    // WORKFLOW: Determine if late (business logic, not AI decision)
    const isLate = await this.calculateLateness(timestamp, context);
    
    // WORKFLOW: Log via MCP
    try {
      const jobId = this.generateJobId(username, timestamp);
      await this.mcpClient.logCheckin(username, timestamp, notes, jobId);

      // WORKFLOW: Log strike if late
      if (isLate) {
        await this.mcpClient.logStrike(username, 'punctuality', timestamp, `Late check-in: ${notes}`);
        
        // AGENTIC: Determine escalation response based on strike history
        const escalationResponse = await this.determineEscalationResponse(username, context);
        
        return this.formatOutput({
          task: 'checkin_late',
          actionRequired: escalationResponse.action,
          confidence: 1.0,
          extra: {
            username,
            timestamp,
            notes,
            isLate: true,
            escalation: escalationResponse
          }
        });
      }

      return this.formatOutput({
        task: 'checkin',
        actionRequired: 'log_only',
        confidence: 1.0,
        extra: { username, timestamp, notes, isLate: false }
      });

    } catch (error) {
      console.error('[Keith] MCP logging failed:', error);
      return this.formatOutput({
        task: 'checkin_error',
        actionRequired: 'manual_review',
        confidence: 0.8,
        extra: { username, timestamp, notes, error: error.message }
      });
    }
  }

  // WORKFLOW FUNCTION: Deterministic check-out processing
  async processCheckout(content, username, timestamp, context) {
    const departureTriggers = [
      'done', 'finished', 'complete', 'leaving', 'checked out', 'check out',
      'clocking out', 'job finished', 'all done', 'completed', 'heading out'
    ];

    const hasDepartureTrigger = departureTriggers.some(trigger => content.includes(trigger));
    if (!hasDepartureTrigger) return null;

    // Extract notes
    let notes = '';
    for (const trigger of departureTriggers) {
      const idx = content.indexOf(trigger);
      if (idx !== -1) {
        notes = content.slice(idx + trigger.length).trim();
        notes = notes.replace(/^([.,-\s]+)/, '');
        break;
      }
    }

    // Log checkout via MCP (this is workflow logic)
    try {
      // Note: We'd need a checkout logging tool in the Notion MCP server
      // For now, log as a general event
      
      return this.formatOutput({
        task: 'checkout',
        actionRequired: 'log_completion',
        confidence: 1.0,
        extra: { username, timestamp, notes }
      });

    } catch (error) {
      console.error('[Keith] Checkout logging failed:', error);
      return this.formatOutput({
        task: 'checkout_error',
        actionRequired: 'manual_review',
        confidence: 0.8,
        extra: { username, timestamp, notes, error: error.message }
      });
    }
  }

  // AGENTIC FUNCTION: Requires judgment and pattern analysis
  async analyzeQualityIssues(content, username, timestamp, context) {
    const complaintKeywords = [
      'complaint', 'issue', 'problem', 'damage', 'client unhappy', 'client complaint',
      'missed spot', 'redo', 'reclean', 'callback', 'negative feedback',
      'unsatisfied', 'not satisfied', 'not happy', 'bad review', 'poor job',
      'quality issue', 'quality concern'
    ];

    const hasComplaintIndicator = complaintKeywords.some(keyword => content.includes(keyword));
    if (!hasComplaintIndicator) return null;

    // AGENTIC: Analyze severity and context
    const severityAnalysis = await this.analyzeSeverity(content, context);
    
    // WORKFLOW: Log the strike
    try {
      await this.mcpClient.logStrike(username, 'quality', timestamp, content);

      // AGENTIC: Determine appropriate response based on pattern analysis
      const responseStrategy = await this.determineQualityResponse(username, severityAnalysis, context);

      return this.formatOutput({
        task: 'quality_issue',
        actionRequired: responseStrategy.action,
        confidence: severityAnalysis.confidence,
        extra: {
          username,
          timestamp,
          severity: severityAnalysis.level,
          content,
          strategy: responseStrategy
        }
      });

    } catch (error) {
      console.error('[Keith] Quality issue logging failed:', error);
      return this.formatOutput({
        task: 'quality_error',
        actionRequired: 'manual_review',
        confidence: 0.9,
        extra: { username, timestamp, content, error: error.message }
      });
    }
  }

  // WORKFLOW: Business logic calculation
  async calculateLateness(timestamp, context) {
    // This would integrate with scheduling data to determine if actually late
    // For now, simplified logic
    const hour = new Date(timestamp).getHours();
    return hour > 8; // Simplified: late if after 8 AM
  }

  // AGENTIC: Escalation decision requires judgment
  async determineEscalationResponse(username, context) {
    const recentStrikes = context.recentStrikes.filter(s => s.type === 'punctuality');
    const strikeCount = recentStrikes.length;

    // Pattern analysis for escalation decision
    if (strikeCount >= 3) {
      return {
        action: 'escalate_immediate',
        level: 'urgent',
        targets: ['ops_lead', 'manager'],
        confidence: 0.95
      };
    } else if (strikeCount >= 1) {
      return {
        action: 'warn_and_notify',
        level: 'moderate',
        targets: ['ops_lead'],
        confidence: 0.85
      };
    } else {
      return {
        action: 'log_only',
        level: 'low',
        targets: [],
        confidence: 0.9
      };
    }
  }

  // AGENTIC: Severity analysis requires contextual judgment
  async analyzeSeverity(content, context) {
    const urgentIndicators = ['damage', 'angry', 'furious', 'lawsuit', 'police'];
    const moderateIndicators = ['unhappy', 'disappointed', 'issue', 'problem'];
    
    if (urgentIndicators.some(indicator => content.includes(indicator))) {
      return { level: 'urgent', confidence: 0.9 };
    } else if (moderateIndicators.some(indicator => content.includes(indicator))) {
      return { level: 'moderate', confidence: 0.8 };
    } else {
      return { level: 'low', confidence: 0.6 };
    }
  }

  // AGENTIC: Response strategy requires judgment based on patterns
  async determineQualityResponse(username, severityAnalysis, context) {
    const recentQualityStrikes = context.recentStrikes.filter(s => s.type === 'quality');
    
    if (severityAnalysis.level === 'urgent' || recentQualityStrikes.length >= 2) {
      return {
        action: 'escalate_manager',
        coaching: true,
        followUp: true
      };
    } else {
      return {
        action: 'coach_and_monitor',
        coaching: true,
        followUp: false
      };
    }
  }

  generateJobId(username, timestamp) {
    const date = new Date(timestamp);
    const datePart = date.toLocaleDateString('en-US').replace(/\//g, '');
    const randomNum = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `${username}-${datePart}-${randomNum}`;
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
    
    return result;
  }
}

module.exports = EnhancedKeith;
