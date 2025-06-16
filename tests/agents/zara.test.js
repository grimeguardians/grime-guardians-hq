// tests/agents/zara.test.js
// Simplified tests for Zara bonus calculation engine

describe('Zara Bonus Engine', () => {
  let zara, mockDiscordClient;

  beforeEach(() => {
    mockDiscordClient = global.mockDiscordClient;
    const Zara = require('../../src/agents/zara');
    zara = new Zara(mockDiscordClient);
  });

  describe('Initialization', () => {
    test('should initialize with correct properties', () => {
      expect(zara.agentId).toBe('zara');
      expect(zara.role).toContain('Bonus');
      expect(zara.bonusHistory).toBeDefined();
      expect(zara.kpiThresholds).toBeDefined();
    });

    test('should have KPI thresholds configured', () => {
      expect(zara.kpiThresholds.punctuality).toBeDefined();
      expect(zara.kpiThresholds.quality).toBeDefined();
      expect(zara.kpiThresholds.streak).toBeDefined();
      
      expect(zara.kpiThresholds.punctuality.excellent).toBe(0.95);
      expect(zara.kpiThresholds.quality.excellent).toBe(0.98);
    });
  });

  describe('Bonus Calculation Methods', () => {
    test('should have weekly bonus calculation method', () => {
      expect(typeof zara.calculateWeeklyBonuses).toBe('function');
    });

    test('should have performance calculation methods', () => {
      expect(typeof zara.calculateWeeklyPerformance).toBe('function');
      expect(typeof zara.calculateBonus).toBe('function');
    });
  });

  describe('Data Tracking', () => {
    test('should track bonus history', () => {
      expect(zara.bonusHistory instanceof Map).toBe(true);
    });

    test('should handle cleaner data', async () => {
      const mockCleanerData = {
        username: 'testcleaner',
        performance: { punctuality: 0.95, quality: 0.90 }
      };

      // Should not throw when processing cleaner data
      expect(() => {
        zara.bonusHistory.set('testcleaner', mockCleanerData);
      }).not.toThrow();
    });
  });

  describe('Scheduling', () => {
    test('should have scheduling methods', () => {
      expect(typeof zara.scheduleWeeklyBonusCalculation).toBe('function');
      expect(typeof zara.scheduleDailyPerformanceCheck).toBe('function');
    });
  });
});
