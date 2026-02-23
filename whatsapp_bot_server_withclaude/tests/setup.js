/**
 * Jest Test Setup
 * Configures test environment and mocks
 */

// Set test environment
process.env.NODE_ENV = 'test';
process.env.PORT = '8081'; // Use different port for tests

// Mock environment variables that might be needed
process.env.REDIS_URL = 'redis://localhost:6379';
process.env.LOG_LEVEL = 'error'; // Reduce logging noise in tests

// Note: jest.setTimeout is moved to jest.config.js (testTimeout setting)
// In ESM modules, jest global is only available in test files
