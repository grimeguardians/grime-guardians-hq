// Test the pay extraction logic
const { extractJobForDiscord } = require('./src/utils/highlevel.js');

// Test various pay format scenarios
const testCases = [
  {
    name: "Pay range with dash",
    notes: `4 bedrooms
3 bathrooms
deep clean
$225 - $250
2 cats
Customer notes here`
  },
  {
    name: "Pay range without spaces",
    notes: `3 bedrooms
2 bathrooms
$180-$230
move out clean
1 dog`
  },
  {
    name: "Sentence with pays between",
    notes: `This job pays between $150 - $200
4 bedrooms
standard clean`
  },
  {
    name: "Pay field format",
    notes: `Pay: $175-225
3 bedrooms
2 bathrooms`
  },
  {
    name: "Single pay amount",
    notes: `This job pays $200
2 bedrooms
1 bathroom`
  }
];

console.log('Testing pay extraction...\n');

testCases.forEach((testCase, index) => {
  const payload = {
    assignedTo: 'Available 1',
    calendar: {
      title: 'Test Clean',
      startTime: '2025-06-12T15:00:00Z',
      notes: testCase.notes
    },
    address1: '123 Test St',
    city: 'Dallas'
  };

  console.log(`--- Test ${index + 1}: ${testCase.name} ---`);
  console.log(`Input notes:\n${testCase.notes}\n`);
  
  const result = extractJobForDiscord(payload);
  console.log(`Pay extracted: "${result.pay}"`);
  console.log(`Notes after extraction:\n"${result.notes}"\n`);
  
  if (result.pay) {
    console.log('✅ Pay extraction successful!');
  } else {
    console.log('❌ No pay extracted');
  }
  console.log('---\n');
});

process.exit(0);
