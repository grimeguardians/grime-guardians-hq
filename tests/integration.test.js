// tests/integration.test.js
// Integration test focused on core system functionality

describe('Grime Guardians Core System Integration', () => {
  let mockDiscordClient;

  beforeEach(() => {
    mockDiscordClient = global.mockDiscordClient;
  });

  describe('8-Agent System Core', () => {
    test('should successfully load all 8 core agents', () => {
      const Ava = require('../src/agents/ava');
      const KeithEnhanced = require('../src/agents/keithEnhanced');
      const Maya = require('../src/agents/maya');
      const Zara = require('../src/agents/zara');
      const Nikolai = require('../src/agents/nikolai');
      const Iris = require('../src/agents/iris');
      const Jules = require('../src/agents/jules');
      const ScheduleManager = require('../src/agents/scheduleManager');

      // All agents should load without errors
      expect(Ava).toBeDefined();
      expect(KeithEnhanced).toBeDefined();
      expect(Maya).toBeDefined();
      expect(Zara).toBeDefined();
      expect(Nikolai).toBeDefined();
      expect(Iris).toBeDefined();
      expect(Jules).toBeDefined();
      expect(ScheduleManager).toBeDefined();
    });

    test('should initialize all agents without crashes', () => {
      const Ava = require('../src/agents/ava');
      const KeithEnhanced = require('../src/agents/keithEnhanced');
      const Maya = require('../src/agents/maya');
      const Zara = require('../src/agents/zara');
      const Nikolai = require('../src/agents/nikolai');
      const Iris = require('../src/agents/iris');
      const Jules = require('../src/agents/jules');

      const agents = [];

      // All should initialize without throwing
      expect(() => {
        agents.push(new Ava(mockDiscordClient));
        agents.push(new KeithEnhanced(mockDiscordClient, {}, {}));
        agents.push(new Maya(mockDiscordClient));
        agents.push(new Zara(mockDiscordClient));
        agents.push(new Nikolai(mockDiscordClient));
        agents.push(new Iris(mockDiscordClient));
        agents.push(new Jules(mockDiscordClient));
      }).not.toThrow();

      expect(agents).toHaveLength(7);
    });

    test('should have unique agent IDs', () => {
      const Ava = require('../src/agents/ava');
      const Maya = require('../src/agents/maya');
      const Zara = require('../src/agents/zara');
      const Nikolai = require('../src/agents/nikolai');
      const Iris = require('../src/agents/iris');
      const Jules = require('../src/agents/jules');

      const agents = [
        new Ava(mockDiscordClient),
        new Maya(mockDiscordClient),
        new Zara(mockDiscordClient),
        new Nikolai(mockDiscordClient),
        new Iris(mockDiscordClient),
        new Jules(mockDiscordClient)
      ];

      const agentIds = agents.map(agent => agent.agentId);
      const uniqueIds = new Set(agentIds);

      expect(uniqueIds.size).toBe(agentIds.length);
    });
  });

  describe('System Health Checks', () => {
    test('agents should have basic required methods', () => {
      const Ava = require('../src/agents/ava');
      const Maya = require('../src/agents/maya');

      const ava = new Ava(mockDiscordClient);
      const maya = new Maya(mockDiscordClient);

      // Core agent methods
      expect(typeof ava.getContext).toBe('function');
      expect(typeof ava.handleEvent).toBe('function');
      expect(typeof maya.getContext).toBe('function');
      expect(typeof maya.handleEvent).toBe('function');
    });

    test('agents should handle basic event structure', () => {
      const Maya = require('../src/agents/maya');
      const maya = new Maya(mockDiscordClient);

      const mockEvent = {
        content: 'test message',
        author: { username: 'testuser' }
      };

      // Should not crash on basic event
      expect(() => maya.getContext(mockEvent)).not.toThrow();
    });

    test('bonus engine should have KPI configuration', () => {
      const Zara = require('../src/agents/zara');
      const zara = new Zara(mockDiscordClient);

      expect(zara.kpiThresholds).toBeDefined();
      expect(zara.kpiThresholds.punctuality).toBeDefined();
      expect(zara.kpiThresholds.quality).toBeDefined();
    });

    test('pricing agent should have quote generation', () => {
      const Iris = require('../src/agents/iris');
      const iris = new Iris(mockDiscordClient);

      expect(typeof iris.generateQuote).toBe('function');
    });
  });

  describe('Error Resilience', () => {
    test('system should handle missing Discord client gracefully', () => {
      const Maya = require('../src/agents/maya');
      
      // Should not crash even without client
      expect(() => new Maya(null)).not.toThrow();
    });

    test('agents should handle undefined events', async () => {
      const Maya = require('../src/agents/maya');
      const maya = new Maya(mockDiscordClient);

      // Should handle undefined/null events gracefully
      await expect(maya.getContext(undefined)).resolves.toBeDefined();
      await expect(maya.getContext({})).resolves.toBeDefined();
    });
  });
});
