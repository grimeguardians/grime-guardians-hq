// Test the exact output that would be sent to Discord
const { extractJobForDiscord } = require('./src/utils/highlevel.js');

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

console.log('=== Testing Discord Message Format ===');
const job = extractJobForDiscord(testPayload);

if (job) {
  // Format message exactly as it would appear in Discord DM
  const dmMsg = `**New Job Approval Needed**\n\n` +
    `**Job:** ${job.jobTitle}\n` +
    `**Date/Time:** ${job.dateTime}\n` +
    `**Address:** ${job.address}\n` +
    (job.bedrooms ? `**Bedrooms:** ${job.bedrooms}\n` : '') +
    (job.bathrooms ? `**Bathrooms:** ${job.bathrooms}\n` : '') +
    (job.type ? `**Type:** ${job.type}\n` : '') +
    (job.pets ? `**Pets:** ${job.pets}\n` : '') +
    (job.notes ? `**Notes:** ${job.notes}\n` : '') +
    `\nApprove this job for posting to the job board? (Reply 'yes' or 'no')`;
  
  console.log('Discord DM Message:');
  console.log('==================');
  console.log(dmMsg);
  console.log('==================');
  
  console.log('\n=== Extracted Data ===');
  console.log('Job Title:', job.jobTitle);
  console.log('Date/Time:', job.dateTime);
  console.log('Address:', job.address);
  console.log('Bedrooms:', job.bedrooms);
  console.log('Bathrooms:', job.bathrooms);
  console.log('Type:', job.type);
  console.log('Pets:', job.pets);
  console.log('Notes:', job.notes);
  
  console.log('\n=== SUCCESS CHECKS ===');
  console.log('✅ Pets extracted correctly:', job.pets === '2 cats, 2 dogs');
  console.log('✅ Pet lines removed from notes:', !job.notes.includes('cats') && !job.notes.includes('dogs'));
  console.log('✅ Bedroom/bathroom extracted:', job.bedrooms === '3' && job.bathrooms === '2');
  console.log('✅ Type extracted:', job.type === 'Deep Clean');
} else {
  console.log('❌ No job extracted (not assigned to Available _)');
}
