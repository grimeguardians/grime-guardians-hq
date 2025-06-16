// Debug the exact pets extraction issue
const { extractJobForDiscord } = require('./src/utils/highlevel.js');

// Test payload matching your exact case
const testPayload = {
  assignedTo: 'Available 1',
  calendar: {
    title: 'Test Move-Out Clean',
    startTime: '2025-06-12T14:00:00Z', // 9 AM CT
    notes: `4 bedrooms
3 bathrooms
move out
2 cats 2 dogs`
  },
  address1: '1669 Oak Ridge Circle',
  city: 'Dallas'
};

console.log('=== DEBUGGING PETS EXTRACTION ===');
console.log('Input notes:', testPayload.calendar.notes);
console.log('');

const result = extractJobForDiscord(testPayload);
console.log('\nExtracted result:');
console.log(JSON.stringify(result, null, 2));

console.log('\n--- Analysis ---');
console.log(`Pets field: "${result.pets}"`);
console.log(`Notes field: "${result.notes}"`);

if (result.pets === '2 cats, 2 dogs' && !result.notes.includes('cats') && !result.notes.includes('dogs')) {
  console.log('\n✅ SUCCESS: Pets extracted correctly!');
} else {
  console.log('\n❌ FAIL: Pets extraction not working');
  console.log('Expected pets: "2 cats, 2 dogs"');
  console.log('Expected notes to NOT contain pet references');
}

process.exit(0);
