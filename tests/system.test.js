// tests/system.test.js
// Simplified Jest-based system test for all 8 agents

describe('Grime Guardians 8-Agent System', () => {
  let mockDiscordClient, mockNotionClient;

  beforeAll(() => {
    // Set up mocks
    mockDiscordClient = global.mockDiscordClient;
    mockNotionClient = global.mockNotionClient;
  });

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    global.console.log.mockClear();
    global.console.error.mockClear();
  });

  describe('Agent Initialization', () => {
    test('all agents should initialize without errors', () => {
      const Ava = require('../src/agents/ava');
      const KeithEnhanced = require('../src/agents/keithEnhanced');
      const Maya = require('../src/agents/maya');
      const Zara = require('../src/agents/zara');
      const Nikolai = require('../src/agents/nikolai');
      const Iris = require('../src/agents/iris');
      const Jules = require('../src/agents/jules');

      expect(() => new Ava(mockDiscordClient)).not.toThrow();
      expect(() => new KeithEnhanced(mockDiscordClient, {}, {})).not.toThrow();
      expect(() => new Maya(mockDiscordClient)).not.toThrow();
      expect(() => new Zara(mockDiscordClient)).not.toThrow();
      expect(() => new Nikolai(mockDiscordClient)).not.toThrow();
      expect(() => new Iris(mockDiscordClient)).not.toThrow();
      expect(() => new Jules(mockDiscordClient)).not.toThrow();
    });

    test('agents should have required properties', () => {
      const Ava = require('../src/agents/ava');
      const Maya = require('../src/agents/maya');
      const Zara = require('../src/agents/zara');
      
      const ava = new Ava(mockDiscordClient);
      const maya = new Maya(mockDiscordClient);
      const zara = new Zara(mockDiscordClient);

      expect(ava.agentId).toBe('ava');
      expect(maya.agentId).toBe('maya');
      expect(zara.agentId).toBe('zara');
    });
  });

  describe('Maya - Motivational Coach', () => {
    let maya;

    beforeEach(() => {
      const Maya = require('../src/agents/maya');
      maya = new Maya(mockDiscordClient);
    });

    test('should initialize with correct role', () => {
      expect(maya.role).toContain('Motivational Coach');
    });

    test('should have praise tracking capabilities', () => {
      expect(maya.praiseHistory).toBeDefined();
      expect(maya.streakTracking).toBeDefined();
    });

    test('should handle event processing', async () => {
      const mockEvent = {
        content: 'finished cleaning job',
        author: { username: 'testuser' }
      };

      const context = await maya.getContext(mockEvent);
      expect(context).toHaveProperty('event');
    });
  });

  describe('Zara - Bonus Engine', () => {
    let zara;

    beforeEach(() => {
      const Zara = require('../src/agents/zara');
      zara = new Zara(mockDiscordClient);
    });

    test('should initialize with KPI thresholds', () => {
      expect(zara.kpiThresholds).toBeDefined();
      expect(zara.kpiThresholds.punctuality).toBeDefined();
      expect(zara.kpiThresholds.quality).toBeDefined();
    });

    test('should have bonus calculation methods', () => {
      expect(typeof zara.calculateWeeklyBonuses).toBe('function');
    });

    test('should track bonus history', () => {
      expect(zara.bonusHistory).toBeDefined();
    });
  });

  describe('Nikolai - Compliance Enforcer', () => {
    let nikolai;

    beforeEach(() => {
      const Nikolai = require('../src/agents/nikolai');
      nikolai = new Nikolai(mockDiscordClient);
    });

    test('should initialize with compliance tracking', () => {
      expect(nikolai.agentId).toBe('nikolai');
      expect(nikolai.role).toContain('Compliance');
    });

    test('should have violation tracking', () => {
      expect(nikolai.violationHistory).toBeDefined();
    });
  });

  describe('Iris - Pricing & Sales', () => {
    let iris;

    beforeEach(() => {
      const Iris = require('../src/agents/iris');
      iris = new Iris(mockDiscordClient);
    });

    test('should initialize with pricing tiers', () => {
      expect(iris.pricingTiers).toBeDefined();
      expect(iris.pricingTiers.essential).toBeDefined();
      expect(iris.pricingTiers.complete).toBeDefined();
      expect(iris.pricingTiers.luxury).toBeDefined();
    });

    test('should have quote generation capabilities', () => {
      expect(typeof iris.generateQuote).toBe('function');
    });
  });

  describe('Jules - Analytics & Reporting', () => {
    let jules;

    beforeEach(() => {
      const Jules = require('../src/agents/jules');
      jules = new Jules(mockDiscordClient);
    });

    test('should initialize with reporting capabilities', () => {
      expect(jules.agentId).toBe('jules');
      expect(jules.role).toContain('Analytics');
    });

    test('should have KPI tracking', () => {
      expect(jules.kpiMetrics).toBeDefined();
    });
  });

  describe('System Integration', () => {
    test('should load all agents without conflicts', () => {
      const Ava = require('../src/agents/ava');
      const KeithEnhanced = require('../src/agents/keithEnhanced');
      const Maya = require('../src/agents/maya');
      const Zara = require('../src/agents/zara');
      const Nikolai = require('../src/agents/nikolai');
      const Iris = require('../src/agents/iris');
      const Jules = require('../src/agents/jules');

      const agents = [
        new Ava(mockDiscordClient),
        new KeithEnhanced(mockDiscordClient, {}, {}),
        new Maya(mockDiscordClient),
        new Zara(mockDiscordClient),
        new Nikolai(mockDiscordClient),
        new Iris(mockDiscordClient),
        new Jules(mockDiscordClient)
      ];

      expect(agents).toHaveLength(7);
      
      // Check all agents have unique IDs
      const agentIds = agents.map(a => a.agentId);
      const uniqueIds = new Set(agentIds);
      expect(uniqueIds.size).toBe(agentIds.length);
    });
  });

  describe('Error Handling', () => {
    test('agents should handle missing client gracefully', () => {
      const Maya = require('../src/agents/maya');
      
      // Should not crash without client
      expect(() => new Maya(null)).not.toThrow();
    });

    test('should handle malformed events', async () => {
      const Maya = require('../src/agents/maya');
      const maya = new Maya(mockDiscordClient);

      const malformedEvent = {};
      const context = await maya.getContext(malformedEvent);
      
      expect(context).toBeDefined();
    });
  });
});
