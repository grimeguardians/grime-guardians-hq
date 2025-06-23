/**
 * Tool Capability Test File
 * Testing if GitHub Copilot can create, edit, and modify files
 */

console.log('🧪 Initial test file created');

// Test function 1 - UPDATED
function testFunction() {
  return 'MODIFIED version - replace_string_in_file works!';
}

// Test function 2 - ADDED via insert_edit_into_file
function testInsertFunction() {
  return 'insert_edit_into_file tool works!';
}

// Test variable
let testVariable = 'original value';

// Additional test variable
const additionalVar = 'Added via insert tool';

// Export for testing
module.exports = { testFunction, testVariable };
