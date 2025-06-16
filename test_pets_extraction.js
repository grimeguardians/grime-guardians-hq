// Test the pets extraction logic
const { extractJobForDiscord } = require('./src/utils/highlevel.js');

// Mock payload with pets in notes
const testPayload = {
  assignedTo: 'Available 1',
  calendar: {
    title: 'Deep Clean',
    startTime: '2025-01-16T15:00:00Z',
    notes: `3 bedrooms
2 bathrooms
deep clean
2 cats
Some additional cleaning notes here
2 dogs
More notes after pets`
  },
  address1: '123 Main St, Dallas, TX 75201',
  city: 'Dallas'
};

console.log('Testing pets extraction...');
try {
  const result = extractJobForDiscord(testPayload);
  console.log('Result:', JSON.stringify(result, null, 2));

  console.log('\n--- Expected Results ---');
  console.log('Pets should be: "2 cats, 2 dogs"');
  console.log('Notes should NOT contain pet lines');
  console.log('Bedrooms should be: "3"');
  console.log('Bathrooms should be: "2"');
  console.log('Type should be: "Deep Clean"');
  
  console.log('\n--- Actual Results ---');
  console.log(`Pets: "${result.pets}"`);
  console.log(`Notes: "${result.notes}"`);
  console.log(`Bedrooms: "${result.bedrooms}"`);
  console.log(`Bathrooms: "${result.bathrooms}"`);
  console.log(`Type: "${result.type}"`);
  
  // Check if pets extraction worked
  if (result.pets === '2 cats, 2 dogs') {
    console.log('\n✅ SUCCESS: Pets extracted correctly!');
  } else {
    console.log('\n❌ FAIL: Pets extraction failed');
  }
  
  // Check if pets were removed from notes
  if (!result.notes.includes('cats') && !result.notes.includes('dogs')) {
    console.log('✅ SUCCESS: Pet lines removed from notes!');
  } else {
    console.log('❌ FAIL: Pet lines still in notes');
  }
} catch (error) {
  console.error('Error:', error.message);
}

process.exit(0);
