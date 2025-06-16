// Test webhook with pets extraction
const fetch = require('node-fetch');

const WEBHOOK_URL = 'http://localhost:3000/webhook/highlevel-appointment';
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'GG_Hook_2025abc2030';

const testPayload = {
  assignedTo: 'Available 1',
  calendar: {
    title: 'Deep Clean Service',
    startTime: '2025-01-16T15:00:00Z',
    notes: `3 bedrooms
2 bathrooms
deep clean
2 cats
Customer notes: Please be careful with the vase on the mantle
2 dogs
Additional request: Extra attention to kitchen`
  },
  address1: '123 Main St, Dallas, TX 75201',
  city: 'Dallas'
};

async function testWebhook() {
  try {
    console.log('Sending test webhook to:', WEBHOOK_URL);
    console.log('Using secret:', WEBHOOK_SECRET);
    console.log('Payload:', JSON.stringify(testPayload, null, 2));
    
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-webhook-secret': WEBHOOK_SECRET
      },
      body: JSON.stringify(testPayload)
    });
    
    const responseText = await response.text();
    console.log('Response status:', response.status);
    console.log('Response text:', responseText);
    
    if (response.ok) {
      console.log('✅ Webhook sent successfully!');
      console.log('Check the Discord DM and server console for the job details.');
      console.log('Expected: Pets should be "2 cats, 2 dogs" and NOT appear in Notes field.');
    } else {
      console.log('❌ Webhook failed:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('❌ Error sending webhook:', error.message);
    console.error('Stack:', error.stack);
  }
}

testWebhook();
