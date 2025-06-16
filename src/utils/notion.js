// src/utils/notion.js
// Utility for Notion API integration (CRUD for attendance, strikes, escalations)
const { Client } = require('@notionhq/client');
const { DateTime } = require('luxon');

const notion = new Client({ auth: process.env.NOTION_SECRET });

/**
 * Log a check-in event to Notion (creates a new row)
 */
async function logCheckin({ username, timestamp, notes }) {
  const databaseId = process.env.NOTION_ATTENDANCE_DB_ID;
  const dt = DateTime.fromISO(timestamp, { zone: 'utc' }).setZone('America/Chicago');
  const properties = {
    Name: { title: [{ text: { content: username } }] },
    Date: { date: { start: dt.toISO() } },
  };
  if (notes) {
    properties.Notes = { rich_text: [{ text: { content: notes } }] };
  }
  return notion.pages.create({
    parent: { database_id: databaseId },
    properties,
  });
}

/**
 * Update the most recent unfinished row for a user with a finished timestamp and notes
 */
async function logCheckout({ username, timestamp, notes }) {
  const databaseId = process.env.NOTION_ATTENDANCE_DB_ID;
  // Find the most recent row for this user where Finished is empty
  const response = await notion.databases.query({
    database_id: databaseId,
    filter: {
      and: [
        { property: 'Name', title: { equals: username } },
        { property: 'Finished', date: { is_empty: true } }
      ]
    },
    sorts: [{ property: 'Date', direction: 'descending' }],
    page_size: 1
  });
  if (response.results.length === 0) {
    throw new Error('No unfinished check-in found for user: ' + username);
  }
  const pageId = response.results[0].id;
  const dt = DateTime.fromISO(timestamp, { zone: 'utc' }).setZone('America/Chicago');
  // Get existing notes (if any)
  let existingNotes = '';
  const notesProp = response.results[0].properties.Notes;
  if (notesProp && notesProp.rich_text && notesProp.rich_text.length > 0) {
    existingNotes = notesProp.rich_text.map(rt => rt.plain_text).join(' ');
  }
  let combinedNotes = existingNotes;
  if (notes) {
    combinedNotes = existingNotes ? `${existingNotes}\n${notes}` : notes;
  }
  const properties = {
    Finished: { date: { start: dt.toISO() } }
  };
  if (combinedNotes) {
    properties.Notes = { rich_text: [{ text: { content: combinedNotes } }] };
  }
  return notion.pages.update({
    page_id: pageId,
    properties,
  });
}

/**
 * Log a strike/violation event to Notion (creates a new row in Strikes & Violations DB)
 * @param {Object} param0
 * @param {string} param0.username - User's name
 * @param {string} param0.timestamp - ISO timestamp
 * @param {string} param0.type - Violation type ("punctuality" or "quality")
 * @param {string} [param0.notes] - Optional notes/details
 */
async function logStrike({ username, timestamp, type, notes }) {
  const databaseId = process.env.NOTION_STRIKES_DB_ID;
  const dt = DateTime.fromISO(timestamp, { zone: 'utc' }).setZone('America/Chicago');
  const properties = {
    User: { title: [{ text: { content: username } }] },
    Date: { date: { start: dt.toISO() } },
    'Violation Type': { select: { name: type.charAt(0).toUpperCase() + type.slice(1) } },
  };
  if (notes) {
    properties.Notes = { rich_text: [{ text: { content: notes } }] };
  }
  return notion.pages.create({
    parent: { database_id: databaseId },
    properties,
  });
}

/**
 * Create a schedule request page in Notion
 * @param {Object} pageData - Data for the schedule request page
 * @returns {Promise<Object>} Created page object
 */
async function createScheduleRequestPage(pageData) {
  try {
    const databaseId = process.env.NOTION_SCHEDULE_REQUESTS_DB_ID || process.env.NOTION_ATTENDANCE_DB_ID; // Fallback to attendance DB if schedule DB not set
    
    const properties = {
      'Client Name': { title: [{ text: { content: pageData.clientName || 'Unknown' } }] },
      'Client Phone': { phone_number: pageData.clientPhone || '' },
      'Request Type': { select: { name: pageData.requestType || 'General' } },
      'Source': { select: { name: pageData.source || 'Unknown' } },
      'Message': { rich_text: [{ text: { content: pageData.message || '' } }] },
      'Status': { select: { name: 'Pending' } },
      'Date': { date: { start: (pageData.timestamp || new Date()).toISOString() } },
    };

    if (pageData.urgency) {
      properties['Urgency'] = { select: { name: pageData.urgency } };
    }

    if (pageData.confidence) {
      properties['Confidence'] = { number: Math.round(pageData.confidence * 100) };
    }

    return notion.pages.create({
      parent: { database_id: databaseId },
      properties,
    });
  } catch (error) {
    console.error('❌ Error creating schedule request page:', error.message);
    // Return a mock response so the system doesn't crash
    return { 
      id: 'mock-page-id', 
      ...pageData,
      created_time: new Date().toISOString()
    };
  }
}

module.exports = {
  logCheckin,
  logCheckout,
  logStrike,
  createScheduleRequestPage,
  notion,
};
