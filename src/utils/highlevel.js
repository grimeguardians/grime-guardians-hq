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
    },
    getAllConversations: async () => {
      console.log('[HighLevel] Disabled - returning empty conversations');
      return [];
    },
    sendMessage: async () => {
      console.log('[HighLevel] Disabled - skipping message send');
      return null;
    }
  };
}

const HIGHLEVEL_API_KEY = process.env.HIGHLEVEL_API_KEY;
const HIGHLEVEL_LOCATION_ID = process.env.HIGHLEVEL_LOCATION_ID;
const CALENDAR_ID = process.env.HIGHLEVEL_CALENDAR_ID || 'sb6IQR2sx5JXOQqMgtf5';
const BASE_URL = 'https://rest.gohighlevel.com/v1/appointments/';

/**
 * Fetch all upcoming appointments from High Level calendar using correct API format
 * @returns {Promise<Array>} Array of appointment objects
 */
async function fetchAllAppointments() {
  // Get timestamps for today and 90 days from now
  const today = Date.now();
  const futureDate = Date.now() + (90*24*60*60*1000); // 90 days
  
  const params = new URLSearchParams({
    locationId: HIGHLEVEL_LOCATION_ID,
    calendarId: CALENDAR_ID,
    startDate: today.toString(),
    endDate: futureDate.toString()
  });

  const url = `${BASE_URL}?${params}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${HIGHLEVEL_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    console.log(`📅 Fetched ${data.appointments?.length || 0} appointments from High Level`);
    
    return data.appointments || [];
  } catch (error) {
    console.error('❌ Error fetching High Level appointments:', error.message);
    return [];
  }
}

/**
 * Process appointments into job format
 * @returns {Promise<Array>} Array of job objects
 */
async function getAllJobs() {
  try {
    const appointments = await fetchAllAppointments();
    
    return appointments.map(appointment => ({
      id: appointment.id,
      title: appointment.title || 'Cleaning Service',
      startTime: new Date(parseInt(appointment.startTime)),
      endTime: new Date(parseInt(appointment.endTime)),
      address: appointment.address || 'No address provided',
      contactId: appointment.contactId,
      contact: appointment.contact || {},
      calendarId: appointment.calendarId,
      appointmentStatus: appointment.appointmentStatus || 'confirmed'
    }));
  } catch (error) {
    console.error('❌ Error processing jobs:', error.message);
    return [];
  }
}

/**
 * Get jobs for a specific cleaner based on their assigned calendar
 * @param {string} cleanerId - The cleaner's identifier
 * @returns {Promise<Array>} Array of job objects for the cleaner
 */
async function getJobsForCleaner(cleanerId) {
  try {
    const allJobs = await getAllJobs();
    
    // For now, return all jobs since we don't have cleaner-specific assignment logic
    // This can be enhanced later based on your specific business logic
    return allJobs.filter(job => {
      // Add your cleaner assignment logic here
      // For example, you might check a custom field or calendar assignment
      return true; // Return all jobs for now
    });
  } catch (error) {
    console.error(`❌ Error getting jobs for cleaner ${cleanerId}:`, error.message);
    return [];
  }
}

/**
 * Extract job information for Discord display
 * @param {Object} job - Job object from High Level
 * @returns {Object} Formatted job data for Discord
 */
function extractJobForDiscord(job) {
  if (!job) return null;
  
  try {
    return {
      id: job.id,
      title: job.title || 'Cleaning Service',
      clientName: job.contact?.firstName && job.contact?.lastName 
        ? `${job.contact.firstName} ${job.contact.lastName}`
        : job.contact?.name || 'Unknown Client',
      phone: job.contact?.phone || 'No phone',
      email: job.contact?.email || 'No email',
      address: job.address || 'No address provided',
      startTime: job.startTime,
      endTime: job.endTime,
      status: job.appointmentStatus || 'confirmed',
      notes: job.notes || 'No special notes'
    };
  } catch (error) {
    console.error('❌ Error extracting job for Discord:', error.message);
    return null;
  }
}

/**
 * Get all conversations from High Level API - Enhanced with comprehensive testing
 * @returns {Promise<Array>} Array of conversation objects
 */
async function getAllConversations() {
  console.log(`📱 Testing High Level API with both JWT token and Private Integration...`);
  
  // Test 1: v1 API with JWT token (what we know works for contacts)
  console.log(`🔄 Testing v1 API conversations with JWT token...`);
  const v1Url = `https://rest.gohighlevel.com/v1/conversations/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=50`;
  
  let res = await fetch(v1Url, {
    headers: {
      Authorization: `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
      Accept: 'application/json',
    }
  });
  
  if (res.ok) {
    const data = await res.json();
    console.log(`✅ High Level v1 JWT API successful: found ${data.conversations?.length || 0} conversations`);
    return data.conversations || [];
  } else {
    console.log(`❌ v1 JWT API failed: ${res.status} - ${res.statusText}`);
    const v1Error = await res.text();
    console.log(`❌ v1 Error details: ${v1Error}`);
  }
  
  // Test 2: v2 API with private integration token
  console.log(`🔄 Testing v2 API conversations with Private Integration...`);
  const v2Url = `https://services.leadconnectorhq.com/conversations?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=50`;
  
  res = await fetch(v2Url, {
    headers: {
      Authorization: `Bearer ${process.env.HIGHLEVEL_PRIVATE_INTEGRATION}`,
      'Version': '2021-07-28',
      Accept: 'application/json',
    }
  });
  
  if (res.ok) {
    const data = await res.json();
    console.log(`✅ High Level v2 Private Integration successful: found ${data.conversations?.length || 0} conversations`);
    return data.conversations || [];
  } else {
    console.log(`❌ v2 Private Integration failed: ${res.status} - ${res.statusText}`);
  }
  
  // Test 3: Check what endpoints are actually available
  console.log(`🔄 Testing available endpoints...`);
  const endpoints = [
    { url: `https://rest.gohighlevel.com/v1/contacts/?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`, auth: process.env.HIGHLEVEL_API_KEY, name: 'v1 Contacts (JWT)' },
    { url: `https://services.leadconnectorhq.com/contacts?locationId=${process.env.HIGHLEVEL_LOCATION_ID}&limit=1`, auth: process.env.HIGHLEVEL_PRIVATE_INTEGRATION, name: 'v2 Contacts (PI)', version: '2021-07-28' },
    { url: `https://rest.gohighlevel.com/v1/locations/${process.env.HIGHLEVEL_LOCATION_ID}`, auth: process.env.HIGHLEVEL_API_KEY, name: 'v1 Location Info' },
  ];
  
  for (const endpoint of endpoints) {
    const headers = {
      Authorization: `Bearer ${endpoint.auth}`,
      Accept: 'application/json',
    };
    
    if (endpoint.version) {
      headers['Version'] = endpoint.version;
    }
    
    try {
      const testRes = await fetch(endpoint.url, { headers });
      
      if (testRes.ok) {
        console.log(`✅ ${endpoint.name}: Works!`);
        const data = await testRes.json();
        if (data.contacts) console.log(`   - Found ${data.contacts.length} contacts`);
        if (data.location) console.log(`   - Location: ${data.location.name || 'N/A'}`);
      } else {
        console.log(`❌ ${endpoint.name}: ${testRes.status}`);
      }
    } catch (error) {
      console.log(`❌ ${endpoint.name}: Error - ${error.message}`);
    }
  }
  
  console.log(`⚠️ Conversations API not available - will continue monitoring and retry`);
  return [];
}

/**
 * Send a message via High Level API
 * @param {string} contactId - Contact ID to send message to
 * @param {string} message - Message content
 * @returns {Promise<Object>} Response object
 */
async function sendMessage(contactId, message) {
  try {
    // Try v2 API first with Private Integration
    const res = await fetch(`https://services.leadconnectorhq.com/conversations/messages`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.HIGHLEVEL_PRIVATE_INTEGRATION}`,
        'Version': '2021-07-28',
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        type: 'SMS',
        contactId: contactId,
        message: message,
        locationId: process.env.HIGHLEVEL_LOCATION_ID
      })
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error(`❌ High Level v2 send message failed: ${res.status} - ${errorText}`);
      
      // Fallback to v1 API if available
      console.log(`🔄 Trying v1 API for sending message...`);
      const v1Res = await fetch(`https://rest.gohighlevel.com/v1/conversations/messages`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.HIGHLEVEL_API_KEY}`,
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          type: 'SMS',
          contactId: contactId,
          message: message,
          locationId: process.env.HIGHLEVEL_LOCATION_ID
        })
      });
      
      if (!v1Res.ok) {
        const v1ErrorText = await v1Res.text();
        throw new Error(`Both v2 and v1 APIs failed: ${v1ErrorText}`);
      }
      
      return await v1Res.json();
    }

    return await res.json();
    
  } catch (error) {
    console.error('❌ Error sending High Level message:', error.message);
    throw error;
  }
}

module.exports = {
  fetchAllAppointments,
  getAllJobs,
  getJobsForCleaner,
  extractJobForDiscord,
  getAllConversations,
  sendMessage
};
