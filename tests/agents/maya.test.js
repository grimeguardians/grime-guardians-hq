// tests/agents/maya.test.js
// Simplified tests for Maya motivational coach agent

describe('Maya Motivational Coach', () => {
  let maya, mockDiscordClient;

  beforeEach(() => {
    mockDiscordClient = global.mockDiscordClient;
    const Maya = require('../../src/agents/maya');
    maya = new Maya(mockDiscordClient);
  });

  describe('Initialization', () => {
    test('should initialize with correct properties', () => {
      expect(maya.agentId).toBe('maya');
      expect(maya.role).toContain('Motivational Coach');
      expect(maya.praiseHistory).toBeDefined();
      expect(maya.streakTracking).toBeDefined();
    });
  });

  describe('Event Handling', () => {
    test('should process events with context', async () => {
      const mockEvent = {
        content: 'finished cleaning job',
        author: { username: 'testuser' }
      };

      const context = await maya.getContext(mockEvent);
      expect(context).toHaveProperty('event');
      expect(context.event).toBe(mockEvent);
    });

    test('should handle events without username gracefully', async () => {
      const mockEvent = {
        content: 'test message'
      };

      const context = await maya.getContext(mockEvent);
      expect(context.event).toBe(mockEvent);
      expect(context.performance).toBeNull();
      expect(context.recentActivity).toBeNull();
    });
  });

  describe('Performance Tracking', () => {
    test('should have performance tracking methods', () => {
      expect(typeof maya.getPerformanceMetrics).toBe('function');
      expect(typeof maya.checkForMilestones).toBe('function');
    });

    test('should track praise history', () => {
      expect(maya.praiseHistory instanceof Map).toBe(true);
      expect(maya.streakTracking instanceof Map).toBe(true);
    });
  });
});
