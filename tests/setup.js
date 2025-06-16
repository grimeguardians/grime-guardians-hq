// Jest setup file for Grime Guardians test environment
require('dotenv').config();

// Mock environment variables for testing if they don't exist
if (!process.env.DISCORD_BOT_TOKEN) {
    process.env.DISCORD_BOT_TOKEN = 'test_discord_token';
}

if (!process.env.NOTION_SECRET) {
    process.env.NOTION_SECRET = 'test_notion_secret';
}

if (!process.env.OPENAI_API_KEY) {
    process.env.OPENAI_API_KEY = 'test_openai_key';
}

if (!process.env.HIGH_LEVEL_WEBHOOK_SECRET) {
    process.env.HIGH_LEVEL_WEBHOOK_SECRET = 'test_webhook_secret';
}

// Set longer timeout for integration tests
jest.setTimeout(30000);

// Global test helpers
global.mockDiscordClient = {
    channels: {
        cache: {
            get: jest.fn().mockReturnValue({
                send: jest.fn().mockResolvedValue({ id: 'test-message-id' })
            })
        }
    },
    guilds: {
        cache: {
            get: jest.fn().mockReturnValue({
                members: {
                    cache: {
                        get: jest.fn().mockReturnValue({
                            displayName: 'Test User'
                        })
                    }
                }
            })
        }
    }
};

global.mockNotionClient = {
    pages: {
        create: jest.fn().mockResolvedValue({ id: 'test-page-id' }),
        update: jest.fn().mockResolvedValue({ id: 'test-page-id' })
    },
    databases: {
        query: jest.fn().mockResolvedValue({
            results: []
        })
    }
};

global.mockHighLevelClient = {
    post: jest.fn().mockResolvedValue({
        data: { success: true }
    }),
    get: jest.fn().mockResolvedValue({
        data: { contacts: [] }
    })
};

// Console override for cleaner test output
const originalConsole = console;
global.console = {
    ...originalConsole,
    log: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
};

// Restore console for failed tests
afterEach(() => {
    if (global.console.error.mock.calls.length > 0) {
        originalConsole.error('Test errors:', global.console.error.mock.calls);
    }
});
