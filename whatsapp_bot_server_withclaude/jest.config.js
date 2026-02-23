/**
 * Jest configuration for ES modules
 */
export default {
  testEnvironment: 'node',

  // ES modules support
  transform: {},

  // Test file patterns
  testMatch: [
    '**/tests/**/*.test.js',
    '**/*.test.js'
  ],

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/logs/'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    '**/*.js',
    '!node_modules/**',
    '!coverage/**',
    '!tests/**',
    '!jest.config.js',
    '!pm2.config.json'
  ],

  // Setup files
  setupFilesAfterEnv: ['./tests/setup.js'],

  // Module name mapper for absolute imports
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1'
  },

  // Timeout for tests
  testTimeout: 30000,

  // Verbose output
  verbose: true,

  // Force exit after tests complete
  forceExit: true,

  // Detect open handles
  detectOpenHandles: true
};
