// src/utils/highlevel.js
// Utility for fetching jobs/appointments from High Level API
const fetch = require('node-fetch');

// Check if High Level integration is disabled
const HIGHLEVEL_DISABLED = process.env.DISABLE_HIGHLEVEL === 'true';

if (HIGHLEVEL_DISABLED) {
  console.log('⚠️ High Level integration disabled by environment variable');
  
  // Export mock functions when disabled
  module.exports = {
    fetchAllAppointments: async () => {
      console.log('[HighLevel] Disabled - returning empty appointments');
      return [];
    },
    getAllJobs: async () => {
      console.log('[HighLevel] Disabled - returning empty jobs');
      return [];
    },
    getJobsForCleaner: async () => {
      console.log('[HighLevel] Disabled - returning empty jobs for cleaner');
      return [];
    },
    extractJobForDiscord: () => {
      console.log('[HighLevel] Disabled - skipping job extraction');
      return null;
    }
  };
}

const HIGHLEVEL_PRIVATE_INTEGRATION = process.env.HIGHLEVEL_PRIVATE_INTEGRATION;
const CALENDAR_ID = process.env.HIGHLEVEL_CALENDAR_ID || 'sb6IQR2sx5JXOQqMgtf5';
const BASE_URL = `https://services.leadconnectorhq.com/calendars/${CALENDAR_ID}/appointments`;

/**
 * Fetch all upcoming appointments from High Level calendar using private integration token
 * @returns {Promise<Array>} Array of appointment objects
 */
async function fetchAllAppointments() {
  const res = await fetch(BASE_URL, {
    headers: {
      Authorization: `Bearer ${HIGHLEVEL_PRIVATE_INTEGRATION}`,
      Version: '2021-07-28', // Use latest required by API
      Accept: 'application/json',
    },
  });
  if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
  const data = await res.json();
  // The structure may be { appointments: [...] } or just an array; adjust as needed
  return data.appointments || data || [];
}

/**
 * Transform a raw High Level appointment to a normalized job object
 * @param {Object} appt
 * @returns {Object}
 */
function normalizeAppointment(appt) {
  return {
    id: appt.id,
    title: appt.title || appt.serviceName || '',
    description: appt.description || '',
    date: appt.date || appt.startTime || '',
    startTime: appt.startTime || '',
    address: appt.location || appt.address || '',
    notes: appt.notes || '',
    assignedCleaner: appt.assignedTo || appt.userName || '',
    contact: {
      firstName: appt.contactFirstName || '',
      lastName: appt.contactLastName || '',
      phone: appt.contactPhone || '',
      email: appt.contactEmail || '',
    },
    status: appt.status || '',
    raw: appt
  };
}

/**
 * Fetch and normalize all jobs/appointments
 * @returns {Promise<Array} Array of normalized job objects
 */
async function getAllJobs() {
  const appts = await fetchAllAppointments();
  return appts.map(normalizeAppointment);
}

/**
 * Fetch and normalize jobs for a specific cleaner (by name or ID)
 * @param {string} cleaner
 * @returns {Promise<Array>} Array of normalized job objects
 */
async function getJobsForCleaner(cleaner) {
  const jobs = await getAllJobs();
  return jobs.filter(job =>
    job.assignedCleaner && job.assignedCleaner.toLowerCase().includes(cleaner.toLowerCase())
  );
}

/**
 * Extract and format relevant job info for Discord job board posting
 * Detects pet info in notes and assigns pet type/count if found.
 * @param {Object} payload - Raw webhook payload from High Level
 * @returns {Object} Formatted job info for Discord
 */
function extractJobForDiscord(payload) {
  const cal = payload.calendar || {};
  // Only post if assigned to dummy 'Available _' staff (keep this logic if needed)
  const assigned = (payload.assignedTo || (payload.user && payload.user.firstName) || '').toLowerCase();
  const isAvailable = assigned.startsWith('available');
  if (!isAvailable) return null;

  // --- Job Title ---
  const jobTitle = cal.title || payload.serviceName || 'Cleaning Job';

  // --- Date/Time: Always use calendar.startTime ---
  let dateTime = 'Date not available';
  if (cal.startTime) {
    const date = new Date(cal.startTime);
    if (!isNaN(date.getTime())) {
      dateTime = date.toLocaleString('en-US', {
        timeZone: 'America/Chicago',
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    } else {
      dateTime = 'Invalid date format';
    }
  }

  // --- Address ---
  let address = (payload.address1 || '').trim();
  if (address) {
    // Remove trailing city/state/zip if present
    address = address.replace(/,?\s*[A-Z\s]+\s+[A-Z]{2,}(\s*\d{5})?$/, '').trim();
  }
  const city = payload.city || '';

  // --- Notes extraction (no end time logic) ---
  // Prefer calendar.notes, fallback to Additional info, then other note fields
  let notes = (cal.notes || payload['Additional info'] || payload['Notes'] || '').trim();

  // --- Extraction logic for bedrooms, bathrooms, type, pets, pay ---
  let bedrooms = '';
  let bathrooms = '';
  let type = '';
  let pets = '';
  let pay = '';
  let finalNotes = [];
  
  // Acceptable cleaning types (expand as needed)
  const typeKeywords = [
    'move-out', 'move in', 'move-in', 'move out', 'deep clean', 'deep cleaning', 'turnover', 'post-construction', 'recurring', 'commercial', 'standard', 'one-time', 'post construction', 'postconstruction', 'initial', 'regular', 'maintenance', 'airbnb', 'short-term', 'long-term', 'office', 'apartment', 'condo', 'house', 'studio', 'postrenovation', 'post-renovation', 'renovation', 'post remodel', 'remodel', 'spring clean', 'fall clean', 'holiday', 'event', 'after party', 'before party', 'pre-move', 'post-move', 'pre move', 'post move'
  ];
  
  let petMatches = [];
  
  // Extract from notes (line by line) - process all extractions in one pass
  notes.split('\n').forEach(line => {
    const l = line.trim();
    if (!l) return;
    
    let extracted = false;
    
    // Bedroom
    let m = l.match(/^(\d+)\s*(b|bed|beds|bedroom|bedrooms)$/i);
    if (m && !bedrooms) { 
      bedrooms = m[1]; 
      extracted = true;
    }
    
    // Bathroom
    if (!extracted) {
      m = l.match(/^(\d+)\s*(ba|bath|baths|bathroom|bathrooms)$/i);
      if (m && !bathrooms) { 
        bathrooms = m[1]; 
        extracted = true;
      }
    }
    
    // Pets - handle multiple pets on same line
    if (!extracted) {
      // First, check if the entire line is just pets (like "2 cats 2 dogs")
      const petOnlyPattern = /^((\d+\s+)?(dog|cat|puppy|kitten|pet|rabbit|bird|fish|reptile|hamster|guinea pig|snake|lizard|turtle|parrot|ferret|mouse|rat|animal|dogs|cats|puppies|kittens|pets|rabbits|birds|fishes|reptiles|hamsters|guinea pigs|snakes|lizards|turtles|parrots|ferrets|mice|rats|animals)(\s+\d+)?(\s+(\d+\s+)?(dog|cat|puppy|kitten|pet|rabbit|bird|fish|reptile|hamster|guinea pig|snake|lizard|turtle|parrot|ferret|mouse|rat|animal|dogs|cats|puppies|kittens|pets|rabbits|birds|fishes|reptiles|hamsters|guinea pigs|snakes|lizards|turtles|parrots|ferrets|mice|rats|animals)(\s+\d+)?)*)$/i;
      
      if (petOnlyPattern.test(l)) {
        // Extract all individual pets from this line
        const individualPetPattern = /(\d+\s+)?(dog|cat|puppy|kitten|pet|rabbit|bird|fish|reptile|hamster|guinea pig|snake|lizard|turtle|parrot|ferret|mouse|rat|animal|dogs|cats|puppies|kittens|pets|rabbits|birds|fishes|reptiles|hamsters|guinea pigs|snakes|lizards|turtles|parrots|ferrets|mice|rats|animals)(\s+\d+)?/gi;
        let match;
        while ((match = individualPetPattern.exec(l)) !== null) {
          let count = (match[1] && match[1].trim()) || (match[3] && match[3].trim()) || '1';
          let petType = match[2].toLowerCase();
          if (petType.endsWith('s')) petType = petType.slice(0, -1);
          if (petType === 'mice') petType = 'mouse';
          petMatches.push(`${count} ${petType}${count !== '1' ? 's' : ''}`);
        }
        extracted = true;
      } else {
        // Check if it's a single pet on its own line
        const singlePetMatch = l.match(/^((\d+)\s*)?(dog|cat|puppy|kitten|pet|rabbit|bird|fish|reptile|hamster|guinea pig|snake|lizard|turtle|parrot|ferret|mouse|rat|animal|dogs|cats|puppies|kittens|pets|rabbits|birds|fishes|reptiles|hamsters|guinea pigs|snakes|lizards|turtles|parrots|ferrets|mice|rats|animals)(\s*\d+)?$/i);
        if (singlePetMatch) {
          let count = singlePetMatch[2] || singlePetMatch[4] || '1';
          let petType = singlePetMatch[3].toLowerCase();
          if (petType.endsWith('s')) petType = petType.slice(0, -1);
          if (petType === 'mice') petType = 'mouse';
          petMatches.push(`${count} ${petType}${count !== '1' ? 's' : ''}`);
          extracted = true;
        }
      }
    }
    
    // Pay - extract pay ranges and amounts
    if (!extracted) {
      // Match various pay patterns
      const payPatterns = [
        // $225 - $250, $180-$230, $150 to $200
        /^.*?\$(\d+)\s*[-–—to]+\s*\$?(\d+).*$/i,
        // This job pays between $180 - $230, pays $200-250, etc.
        /^.*?pays?\s+(?:between\s+)?\$(\d+)\s*[-–—to]+\s*\$?(\d+).*$/i,
        // Pay: $200-250, Payment: $150-200
        /^(?:pay|payment|rate|wage):\s*\$(\d+)\s*[-–—to]+\s*\$?(\d+).*$/i,
        // Single amount: $200, Pay: $150, This job pays $225
        /^.*?(?:pay|payment|pays|rate|wage).*?\$(\d+)(?!\d).*$/i,
        // Just dollar amounts: $200, $150-200
        /^\$(\d+)(?:\s*[-–—to]+\s*\$?(\d+))?$/i
      ];
      
      for (const pattern of payPatterns) {
        const match = l.match(pattern);
        if (match && !pay) {
          if (match[2]) {
            // Range found
            pay = `$${match[1]} - $${match[2]}`;
          } else {
            // Single amount
            pay = `$${match[1]}`;
          }
          extracted = true;
          break;
        }
      }
    }
    
    // Type
    if (!extracted) {
      let matchedType = false;
      for (const keyword of typeKeywords) {
        const typePattern = new RegExp(`^${keyword}(\\s*(clean|cleaning|service|services))?$`, 'i');
        if (typePattern.test(l.toLowerCase())) {
          const formatted = keyword.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          if (!type.split(', ').includes(formatted)) {
            type = type ? type + ', ' + formatted : formatted;
          }
          matchedType = true;
          extracted = true;
          break;
        }
      }
    }
    
    // If nothing was extracted, keep this line as a note
    if (!extracted) {
      finalNotes.push(l);
    }
  });

  // --- Fallback: If no type found in notes, check other fields ---
  if (!type) {
    // Check common type fields in payload
    const typeFields = [
      payload['Type of Service Needed (Check all that apply):'],
      payload['Service Type'],
      payload['What type of cleaning do you need?'],
      payload['What type of space needs cleaning?'],
      payload['Is this a residential or commercial property?'],
      payload[' Type of Service Needed (Check all that apply):'], // with leading space
    ];
    for (const field of typeFields) {
      if (Array.isArray(field)) {
        for (const val of field) {
          for (const keyword of typeKeywords) {
            if (val && val.toLowerCase().includes(keyword)) {
              const formatted = keyword.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
              if (!type.split(', ').includes(formatted)) {
                type = type ? type + ', ' + formatted : formatted;
              }
            }
          }
        }
      } else if (typeof field === 'string') {
        for (const keyword of typeKeywords) {
          if (field.toLowerCase().includes(keyword)) {
            const formatted = keyword.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            if (!type.split(', ').includes(formatted)) {
              type = type ? type + ', ' + formatted : formatted;
            }
          }
        }
      }
    }
  }

  pets = petMatches.length > 0 ? petMatches.join(', ') : '';
  notes = finalNotes.join('\n');
  
  // Clean up notes: remove empty lines, trim, and remove any "Must be complete by" text
  notes = notes.split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.match(/Must be complete by .+/i))
    .join('\n');

  // Compose final Discord payload
  return {
    jobTitle,
    dateTime,
    address,
    city,
    bedrooms,
    bathrooms,
    type,
    pets,
    pay,
    notes,
  };
}

/**
 * Schedule a new job/appointment in High Level
 * @param {Object} jobData - Job data to schedule
 * @returns {Promise<Object>} Created appointment object
 */
async function scheduleJob(jobData) {
  const res = await fetch(BASE_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${HIGHLEVEL_PRIVATE_INTEGRATION}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(jobData),
  });
  if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
  return res.json();
}

/**
 * Update an existing job/appointment in High Level
 * @param {string} jobId - ID of the job to update
 * @param {Object} updateData - Data to update
 * @returns {Promise<Object>} Updated appointment object
 */
async function updateJob(jobId, updateData) {
  const res = await fetch(`${BASE_URL}/${jobId}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${HIGHLEVEL_PRIVATE_INTEGRATION}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(updateData),
  });
  if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
  return res.json();
}

/**
 * Delete a job/appointment in High Level
 * @param {string} jobId - ID of the job to delete
 * @returns {Promise<void>}
 */
async function deleteJob(jobId) {
  const res = await fetch(`${BASE_URL}/${jobId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${HIGHLEVEL_PRIVATE_INTEGRATION}`,
      Accept: 'application/json',
    },
  });
  if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
}

/**
 * Get all conversations from High Level
 * @returns {Promise<Array>} Array of conversation objects
 */
async function getAllConversations() {
  const url = new URL('https://services.leadconnectorhq.com/conversations/');
  url.searchParams.append('locationId', process.env.HIGHLEVEL_LOCATION_ID);
  url.searchParams.append('limit', '50');
  url.searchParams.append('startAfterDate', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());
  
  const res = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
      Version: '2021-07-28',
      Accept: 'application/json',
    }
  });
  if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
  const data = await res.json();
  return data.conversations || [];
}

/**
 * Send a message via High Level
 * @param {string} contactId - Contact ID to send message to
 * @param {string} message - Message content
 * @returns {Promise<Object>} Response object
 */
async function sendMessage(contactId, message) {
  const res = await fetch(`https://services.leadconnectorhq.com/conversations/messages`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
      'Content-Type': 'application/json',
      Version: '2021-07-28',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      contactId,
      message,
      type: 'SMS'
    }),
  });
  if (!res.ok) throw new Error(`High Level API error: ${res.status}`);
  return res.json();
}

/**
 * Create a schedule request page in Notion (placeholder)
 * @param {Object} pageData - Data for the page
 * @returns {Promise<Object>} Created page object
 */
async function createScheduleRequestPage(pageData) {
  // This would integrate with your existing Notion functions
  console.log('[HighLevel] Schedule request logged:', pageData);
  return { id: 'mock-page-id', ...pageData };
}

// Export functions for external use
module.exports = {
  fetchAllAppointments,
  normalizeAppointment,
  getAllJobs,
  getJobsForCleaner,
  extractJobForDiscord,
  scheduleJob,
  updateJob,
  deleteJob,
  getAllConversations,
  sendMessage,
  createScheduleRequestPage,
};
