// Agent Coordinator - Prevents duplicate processing and optimizes agent routing
// Implements smart event routing and coordination to reduce Discord spam

class AgentCoordinator {
  constructor() {
    this.eventLog = new Map();
    this.processingQueue = [];
    this.agentPriority = {
      'ava': 10,           // Master orchestrator - highest priority
      'keith': 9,          // Field operations - critical
      'scheduleManager': 8, // Schedule changes - time sensitive
      'zara': 7,           // Bonus calculations - important
      'maya': 6,           // Motivation - enhancing
      'nikolai': 5,        // Compliance - monitoring
      'iris': 4,           // Pricing - as needed
      'jules': 3           // Analytics - background
    };
  }

  async routeEvent(event, availableAgents) {
    const startTime = Date.now();
    const eventId = this.generateEventId(event);
    
    // Check if event already processed (within last 5 minutes)
    if (this.isDuplicateEvent(eventId)) {
      console.log(`[Coordinator] 🔄 Skipping duplicate event: ${eventId}`);
      return { processed: true, duplicate: true };
    }

    // Classify and route to relevant agents only
    const relevantAgents = this.selectRelevantAgents(event, availableAgents);
    
    if (relevantAgents.length === 0) {
      console.log(`[Coordinator] ⚠️ No relevant agents for event type: ${this.classifyEvent(event)}`);
      return { processed: false, reason: 'no_relevant_agents' };
    }

    console.log(`[Coordinator] 🎯 Routing to ${relevantAgents.length} relevant agents: ${relevantAgents.map(a => a.agentId).join(', ')}`);

    // Coordinate agent responses to prevent conflicts
    const results = await this.coordinatedProcessing(event, relevantAgents);
    
    // Log event as processed
    this.logProcessedEvent(eventId, relevantAgents, results, Date.now() - startTime);

    return {
      processed: true,
      event_id: eventId,
      agents_involved: relevantAgents.map(a => a.agentId),
      results,
      processing_time: Date.now() - startTime
    };
  }

  selectRelevantAgents(event, agents) {
    const relevantAgents = [];
    const eventType = this.classifyEvent(event);
    const agentMap = new Map(agents.map(a => [a.agentId, a]));

    console.log(`[Coordinator] 📋 Event classified as: ${eventType}`);

    switch(eventType) {
      case 'schedule_request':
        this.addAgent(relevantAgents, agentMap, 'scheduleManager'); // Primary handler
        this.addAgent(relevantAgents, agentMap, 'ava');            // Escalation if needed
        break;
        
      case 'job_completion':
        this.addAgent(relevantAgents, agentMap, 'maya');           // Praise and motivation
        this.addAgent(relevantAgents, agentMap, 'zara');           // Bonus tracking
        this.addAgent(relevantAgents, agentMap, 'nikolai');        // Compliance check
        break;
        
      case 'attendance_issue':
        this.addAgent(relevantAgents, agentMap, 'keith');          // Primary attendance handler
        this.addAgent(relevantAgents, agentMap, 'ava');            // Escalation management
        break;
        
      case 'pricing_inquiry':
        this.addAgent(relevantAgents, agentMap, 'iris');           // Pricing specialist
        this.addAgent(relevantAgents, agentMap, 'ava');            // Sales support
        break;
        
      case 'compliance_issue':
        this.addAgent(relevantAgents, agentMap, 'nikolai');        // Primary compliance
        this.addAgent(relevantAgents, agentMap, 'keith');          // Operational context
        break;
        
      case 'performance_question':
        this.addAgent(relevantAgents, agentMap, 'jules');          // Analytics
        this.addAgent(relevantAgents, agentMap, 'zara');           // Bonus context
        break;
        
      default:
        // General communications go to Ava for intelligent routing
        this.addAgent(relevantAgents, agentMap, 'ava');
    }

    // Sort by priority (highest first)
    return relevantAgents.sort((a, b) => 
      (this.agentPriority[b.agentId] || 0) - (this.agentPriority[a.agentId] || 0)
    );
  }

  addAgent(relevantAgents, agentMap, agentId) {
    const agent = agentMap.get(agentId);
    if (agent && !relevantAgents.includes(agent)) {
      relevantAgents.push(agent);
    }
  }

  async coordinatedProcessing(event, agents) {
    const results = [];
    let primaryResponseSent = false;
    
    // Process in priority order to prevent conflicts
    for (const agent of agents) {
      try {
        const context = await agent.getContext(event);
        const result = await agent.handleEvent(event, context);
        
        if (result) {
          const confidence = this.calculateConfidence(result, agent.agentId);
          
          const processedResult = {
            agent_id: agent.agentId,
            result,
            confidence,
            timestamp: new Date().toISOString(),
            action_taken: this.determineActionTaken(result)
          };
          
          results.push(processedResult);
          
          // If high-confidence response with Discord action, prevent spam
          if (confidence > 0.8 && processedResult.action_taken && !primaryResponseSent) {
            console.log(`[Coordinator] ✅ High-confidence response from ${agent.agentId} (${confidence}), limiting additional Discord responses`);
            primaryResponseSent = true;
            
            // Continue processing for data collection but suppress Discord outputs
            this.suppressDiscordForRemainingAgents(agents.slice(agents.indexOf(agent) + 1));
          }
        }
      } catch (error) {
        console.error(`[Coordinator] ❌ Error processing with ${agent.agentId}:`, error.message);
        results.push({
          agent_id: agent.agentId,
          error: error.message,
          confidence: 0,
          timestamp: new Date().toISOString()
        });
      }
    }

    return results;
  }

  classifyEvent(event) {
    const content = (event.content || '').toLowerCase();
    const author = event.author?.username || '';
    
    // Schedule-related keywords
    if (this.containsKeywords(content, ['reschedule', 'move', 'change time', 'different time', 'shift'])) {
      return 'schedule_request';
    }
    
    // Job completion indicators
    if (this.containsKeywords(content, ['finished', 'done', 'complete', 'all set', '🏁', 'wrapped up'])) {
      return 'job_completion';
    }
    
    // Attendance issues
    if (this.containsKeywords(content, ['late', 'sick', "can't make", 'running behind', 'emergency'])) {
      return 'attendance_issue';
    }
    
    // Pricing inquiries
    if (this.containsKeywords(content, ['quote', 'price', 'cost', 'how much', 'estimate'])) {
      return 'pricing_inquiry';
    }
    
    // Compliance issues
    if (this.containsKeywords(content, ['missing', 'forgot', 'checklist', 'photos', 'sop'])) {
      return 'compliance_issue';
    }
    
    // Performance questions
    if (this.containsKeywords(content, ['bonus', 'performance', 'score', 'rating', 'how am i doing'])) {
      return 'performance_question';
    }
    
    return 'general_communication';
  }

  containsKeywords(text, keywords) {
    return keywords.some(keyword => text.includes(keyword));
  }

  calculateConfidence(result, agentId) {
    // Agent-specific confidence scoring
    let baseConfidence = 0.5;
    
    if (result.confidence) {
      return Math.min(result.confidence, 1.0);
    }
    
    // Infer confidence from result content
    if (result.action_required === 'escalation') baseConfidence = 0.9;
    if (result.response && result.response.length > 50) baseConfidence = 0.7;
    if (result.data_logged) baseConfidence += 0.2;
    if (result.discord_notification) baseConfidence += 0.1;
    
    return Math.min(baseConfidence, 1.0);
  }

  determineActionTaken(result) {
    return !!(
      result.discord_notification || 
      result.escalation || 
      result.response || 
      result.action_required === 'immediate'
    );
  }

  suppressDiscordForRemainingAgents(remainingAgents) {
    // Temporarily disable Discord notifications for remaining agents
    remainingAgents.forEach(agent => {
      if (agent.suppressDiscord) {
        agent.suppressDiscord(true);
      }
    });
  }

  isDuplicateEvent(eventId) {
    const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
    
    // Clean old events
    for (const [id, data] of this.eventLog.entries()) {
      if (data.timestamp < fiveMinutesAgo) {
        this.eventLog.delete(id);
      }
    }
    
    return this.eventLog.has(eventId);
  }

  logProcessedEvent(eventId, agents, results, processingTime) {
    this.eventLog.set(eventId, {
      timestamp: Date.now(),
      agents: agents.map(a => a.agentId),
      results: results.length,
      processing_time: processingTime,
      high_confidence_response: results.some(r => r.confidence > 0.8)
    });
  }

  generateEventId(event) {
    const content = (event.content || '').replace(/\s+/g, ' ').trim();
    const author = event.author?.username || 'unknown';
    const timestamp = Math.floor(Date.now() / 60000); // 1-minute resolution
    
    // Create hash of content for better duplicate detection
    const contentHash = this.simpleHash(content.substring(0, 50));
    
    return `${author}_${timestamp}_${contentHash}`;
  }

  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  getMetrics() {
    const now = Date.now();
    const oneHourAgo = now - (60 * 60 * 1000);
    
    const recentEvents = Array.from(this.eventLog.values())
      .filter(event => event.timestamp > oneHourAgo);
    
    return {
      total_events_processed: this.eventLog.size,
      events_last_hour: recentEvents.length,
      average_processing_time: recentEvents.length > 0 
        ? recentEvents.reduce((sum, e) => sum + e.processing_time, 0) / recentEvents.length 
        : 0,
      high_confidence_rate: recentEvents.length > 0
        ? recentEvents.filter(e => e.high_confidence_response).length / recentEvents.length
        : 0
    };
  }
}

module.exports = AgentCoordinator;
