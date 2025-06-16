#!/usr/bin/env node

/**
 * Enhanced Coordination System Test
 * Tests the new AgentCoordinator integration for spam prevention and intelligent routing
 */

require('dotenv').config();
const AgentCoordinator = require('./src/utils/agentCoordinator');

// Mock agent implementations for testing
class MockAgent {
  constructor(agentId, responsePattern = null) {
    this.agentId = agentId;
    this.responsePattern = responsePattern;
    this.callCount = 0;
    this.suppressedCalls = 0;
    this.discordSuppressed = false;
  }

  async getContext(event) {
    return { 
      user: event.author?.username || 'test_user',
      timestamp: new Date().toISOString()
    };
  }

  async handleEvent(event, context) {
    this.callCount++;
    
    if (this.discordSuppressed) {
      this.suppressedCalls++;
      console.log(`[MockAgent-${this.agentId}] Discord suppressed - continuing background processing`);
    }

    // Simulate different response patterns
    switch(this.responsePattern) {
      case 'high_confidence':
        return {
          agent_id: this.agentId,
          confidence: 0.9,
          response: `High confidence response from ${this.agentId}`,
          discord_notification: !this.discordSuppressed,
          action_required: 'immediate',
          data_logged: true
        };
      
      case 'low_confidence':
        return {
          agent_id: this.agentId,
          confidence: 0.3,
          response: `Low confidence response from ${this.agentId}`,
          action_required: 'monitor'
        };
      
      case 'escalation':
        return {
          agent_id: this.agentId,
          confidence: 0.95,
          action_required: 'escalation',
          escalation: {
            target: 'ops_lead',
            priority: 'high'
          },
          discord_notification: !this.discordSuppressed
        };
      
      case 'error':
        throw new Error(`Simulated error in ${this.agentId}`);
      
      default:
        return {
          agent_id: this.agentId,
          confidence: 0.6,
          response: `Standard response from ${this.agentId}`,
          data_logged: true
        };
    }
  }

  suppressDiscord(suppress) {
    this.discordSuppressed = suppress;
  }
}

// Test scenarios
const testScenarios = [
  {
    name: 'Schedule Request Routing',
    event: {
      content: 'Can I reschedule my 3pm job to 4pm?',
      author: { username: 'cleaner_jane' }
    },
    expectedAgents: ['scheduleManager', 'ava']
  },
  {
    name: 'Job Completion Processing',
    event: {
      content: 'Just finished the downtown cleaning job! All done 🏁',
      author: { username: 'cleaner_bob' }
    },
    expectedAgents: ['maya', 'zara', 'nikolai']
  },
  {
    name: 'Attendance Issue Escalation',
    event: {
      content: 'Running really late due to traffic emergency',
      author: { username: 'cleaner_sarah' }
    },
    expectedAgents: ['keith', 'ava']
  },
  {
    name: 'Pricing Inquiry',
    event: {
      content: 'What would you quote for a 3 bedroom house cleaning?',
      author: { username: 'potential_client' }
    },
    expectedAgents: ['iris', 'ava']
  },
  {
    name: 'Compliance Issue',
    event: {
      content: 'I forgot to take the before photos, what should I do?',
      author: { username: 'cleaner_mike' }
    },
    expectedAgents: ['nikolai', 'keith']
  },
  {
    name: 'Performance Question',
    event: {
      content: 'How am I doing this week? What\'s my current bonus status?',
      author: { username: 'cleaner_lisa' }
    },
    expectedAgents: ['jules', 'zara']
  },
  {
    name: 'General Communication',
    event: {
      content: 'Hey team! Hope everyone is having a great day',
      author: { username: 'ops_lead' }
    },
    expectedAgents: ['ava']
  }
];

async function runCoordinationTests() {
  console.log('🧪 Enhanced Agent Coordination System Test\n');
  console.log('='.repeat(50));
  
  const coordinator = new AgentCoordinator();
  
  // Create mock agent registry
  const mockAgents = [
    new MockAgent('ava', 'high_confidence'),
    new MockAgent('keith', 'standard'),
    new MockAgent('scheduleManager', 'high_confidence'),
    new MockAgent('maya', 'standard'),
    new MockAgent('zara', 'standard'),
    new MockAgent('nikolai', 'low_confidence'),
    new MockAgent('iris', 'high_confidence'),
    new MockAgent('jules', 'standard')
  ];

  const agentRegistry = mockAgents.map(agent => ({
    agentId: agent.agentId,
    instance: agent,
    getContext: (event) => agent.getContext(event),
    handleEvent: (event, context) => agent.handleEvent(event, context),
    suppressDiscord: (suppress) => agent.suppressDiscord(suppress)
  }));

  let totalTests = 0;
  let passedTests = 0;

  // Test each scenario
  for (const scenario of testScenarios) {
    totalTests++;
    console.log(`\n📋 Test: ${scenario.name}`);
    console.log(`   Event: "${scenario.event.content}"`);
    console.log(`   Expected Agents: ${scenario.expectedAgents.join(', ')}`);

    try {
      const result = await coordinator.routeEvent(scenario.event, agentRegistry);
      
      if (result.processed) {
        console.log(`   ✅ Processed by: ${result.agents_involved.join(', ')}`);
        console.log(`   ⏱️  Processing time: ${result.processing_time}ms`);
        console.log(`   📊 Results: ${result.results.length} agent responses`);

        // Check if expected agents were involved
        const expectedFound = scenario.expectedAgents.every(expectedAgent => 
          result.agents_involved.includes(expectedAgent)
        );

        if (expectedFound) {
          console.log(`   ✅ Routing successful - all expected agents involved`);
          passedTests++;
        } else {
          console.log(`   ❌ Routing issue - missing expected agents`);
          console.log(`   Expected: ${scenario.expectedAgents.join(', ')}`);
          console.log(`   Actual: ${result.agents_involved.join(', ')}`);
        }

        // Log high-confidence responses
        const highConfidenceResults = result.results.filter(r => r.confidence > 0.8);
        if (highConfidenceResults.length > 0) {
          console.log(`   🎯 High-confidence responses: ${highConfidenceResults.map(r => r.agent_id).join(', ')}`);
        }
      } else {
        console.log(`   ❌ Not processed: ${result.reason}`);
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
    }
  }

  // Test duplicate detection
  console.log(`\n🔄 Testing Duplicate Detection`);
  totalTests++;
  
  const duplicateEvent = {
    content: 'This is a duplicate message for testing',
    author: { username: 'test_user' }
  };

  const firstResult = await coordinator.routeEvent(duplicateEvent, agentRegistry);
  const secondResult = await coordinator.routeEvent(duplicateEvent, agentRegistry);

  if (firstResult.processed && secondResult.duplicate) {
    console.log(`   ✅ Duplicate detection working correctly`);
    passedTests++;
  } else {
    console.log(`   ❌ Duplicate detection failed`);
    console.log(`   First: processed=${firstResult.processed}, duplicate=${firstResult.duplicate}`);
    console.log(`   Second: processed=${secondResult.processed}, duplicate=${secondResult.duplicate}`);
  }

  // Test error handling
  console.log(`\n⚠️  Testing Error Handling`);
  totalTests++;
  
  const errorAgent = new MockAgent('error_agent', 'error');
  const errorAgent2 = new MockAgent('ava', 'high_confidence'); // Ensure ava is available for general communication
  const errorRegistry = [
    {
      agentId: 'error_agent',
      instance: errorAgent,
      getContext: (event) => errorAgent.getContext(event),
      handleEvent: (event, context) => errorAgent.handleEvent(event, context)
    },
    {
      agentId: 'ava',
      instance: errorAgent2,
      getContext: (event) => errorAgent2.getContext(event),
      handleEvent: (event, context) => errorAgent2.handleEvent(event, context)
    }
  ];

  const errorEvent = {
    content: 'This should trigger an error in error_agent - error handling test',
    author: { username: 'test_user_error' }
  };

  // Create a coordinator that will route to both agents
  const errorCoordinator = new AgentCoordinator();
  
  // Override selectRelevantAgents to include the error agent
  const originalSelect = errorCoordinator.selectRelevantAgents;
  errorCoordinator.selectRelevantAgents = function(event, agents) {
    return agents; // Return all agents for this test
  };

  const errorResult = await errorCoordinator.routeEvent(errorEvent, errorRegistry);
  
  if (errorResult.processed && errorResult.results) {
    const errorAgentResult = errorResult.results.find(r => r.agent_id === 'error_agent');
    
    if (errorAgentResult && errorAgentResult.error) {
      console.log(`   ✅ Error handling working - captured: ${errorAgentResult.error}`);
      passedTests++;
    } else {
      console.log(`   ❌ Error handling failed - no error captured`);
      console.log(`   Results:`, JSON.stringify(errorResult.results.map(r => ({agent: r.agent_id, error: r.error})), null, 2));
    }
  } else {
    console.log(`   ❌ Error handling failed - event not processed`);
  }

  // Display metrics
  console.log(`\n📊 System Metrics:`);
  const metrics = coordinator.getMetrics();
  console.log(`   Total Events Processed: ${metrics.total_events_processed}`);
  console.log(`   Events in Last Hour: ${metrics.events_last_hour}`);
  console.log(`   Average Processing Time: ${Math.round(metrics.average_processing_time)}ms`);
  console.log(`   High Confidence Rate: ${Math.round(metrics.high_confidence_rate * 100)}%`);

  // Display agent call counts
  console.log(`\n🤖 Agent Call Statistics:`);
  mockAgents.forEach(agent => {
    console.log(`   ${agent.agentId}: ${agent.callCount} calls (${agent.suppressedCalls} suppressed)`);
  });

  // Final results
  console.log(`\n${'='.repeat(50)}`);
  console.log(`📋 Test Summary: ${passedTests}/${totalTests} tests passed`);
  
  if (passedTests === totalTests) {
    console.log(`🎉 All tests passed! Agent coordination system is working correctly.`);
    process.exit(0);
  } else {
    console.log(`❌ Some tests failed. Please review the coordination logic.`);
    process.exit(1);
  }
}

// Run the tests
runCoordinationTests().catch(error => {
  console.error('❌ Test execution failed:', error);
  process.exit(1);
});
