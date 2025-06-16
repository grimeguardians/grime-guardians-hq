module.exports = {
  testEnvironment: 'node',
  testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.jsx?$',
  testPathIgnorePatterns: ['/node_modules/', '/scripts/'],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/index.js', // Skip main entry point for now
    '!**/node_modules/**'
  ],
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  moduleDirectories: ['node_modules', 'src'],
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
  },
  moduleFileExtensions: ['js', 'jsx', 'json', 'node'],
  verbose: true
};