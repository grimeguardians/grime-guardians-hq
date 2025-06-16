// tests/agents/keith.test.js
// Simplified tests for Keith Enhanced agent

describe('Keith Enhanced Agent', () => {
  let keith, mockDiscordClient;

  beforeEach(() => {
    mockDiscordClient = global.mockDiscordClient;
    const KeithEnhanced = require('../../src/agents/keithEnhanced');
    keith = new KeithEnhanced(mockDiscordClient, {}, {});
  });

  describe('Initialization', () => {
    test('should initialize with correct properties', () => {
      expect(keith.agentId).toBe('keithEnhanced');
      expect(keith.role).toContain('Operations');
    });

    test('should have required tracking maps', () => {
      expect(keith.activeJobs).toBeDefined();
      expect(keith.cleanerPerformance).toBeDefined();
      expect(keith.strikeSystem).toBeDefined();
    });
  });

  describe('Job Processing', () => {
    test('should have job processing methods', () => {
      expect(typeof keith.processWebhookData).toBe('function');
      expect(typeof keith.postJobAssignment).toBe('function');
    });

    test('should handle job data structure', () => {
      const mockJobData = {
        client: 'Test Client',
        type: 'Standard Clean',
        date: '2025-06-15',
        time: '10:00 AM'
      };

      // Should not throw when processing job data
      expect(() => {
        keith.activeJobs.set('test-job-id', mockJobData);
      }).not.toThrow();
    });
  });

  describe('Performance Tracking', () => {
    test('should track cleaner performance', () => {
      const performanceData = {
        username: 'testcleaner',
        punctuality: 0.95,
        strikes: 0
      };

      keith.cleanerPerformance.set('testcleaner', performanceData);
      
      expect(keith.cleanerPerformance.get('testcleaner')).toEqual(performanceData);
    });

    test('should handle strike system', () => {
      expect(keith.strikeSystem instanceof Map).toBe(true);
      
      // Should handle strike data
      keith.strikeSystem.set('testcleaner', { count: 1, reasons: ['Late arrival'] });
      
      expect(keith.strikeSystem.get('testcleaner').count).toBe(1);
    });
  });

  describe('Event Handling', () => {
    test('should process events with context', async () => {
      const mockEvent = {
        content: 'test message',
        author: { username: 'testuser' }
      };

      const context = await keith.getContext(mockEvent);
      expect(context).toHaveProperty('event');
    });
  });
});
