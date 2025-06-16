// src/utils/jobAssignment.js
// Job assignment utilities for handling Discord reactions and cleaner assignments

const { updateJob } = require('./highlevel');
const { scheduleJobReminders } = require('./jobScheduler');
const { sendDiscordPing } = require('./discord');

/**
 * Track job assignments and reactions
 */
const jobAssignments = new Map();
const reactionTracking = new Map();

/**
 * Handle reaction to job board post - assign cleaner to job
 * @param {Object} reaction - Discord reaction object
 * @param {Object} user - Discord user object
 * @param {Object} client - Discord client
 * @returns {Promise<boolean>} True if assignment was successful
 */
async function handleJobBoardReaction(reaction, user, client) {
  try {
    // Only handle checkmark reactions
    if (reaction.emoji.name !== '✅') {
      return false;
    }

    // Get the message content to extract job information
    const message = reaction.message;
    const jobInfo = extractJobInfoFromMessage(message.content);
    
    if (!jobInfo) {
      console.log('[JobAssignment] Could not extract job info from message');
      return false;
    }

    // Check if job is already assigned
    if (jobAssignments.has(jobInfo.id)) {
      const existingAssignment = jobAssignments.get(jobInfo.id);
      if (existingAssignment.assignedTo !== user.username) {
        // Job already assigned to someone else
        await user.send(`❌ Sorry, this job has already been assigned to ${existingAssignment.assignedTo}.`);
        return false;
      } else {
        // User already assigned to this job
        await user.send(`✅ You're already assigned to this job!`);
        return true;
      }
    }

    // Assign the job
    const assignment = {
      jobId: jobInfo.id,
      assignedTo: user.username,
      assignedUserId: user.id,
      assignedAt: new Date().toISOString(),
      jobInfo
    };

    // Update High Level with assignment
    try {
      await updateJob(jobInfo.id, {
        assignedTo: user.username,
        status: 'assigned'
      });
      console.log(`[JobAssignment] Updated High Level job ${jobInfo.id} with assignment to ${user.username}`);
    } catch (error) {
      console.error('[JobAssignment] Error updating High Level:', error);
      // Continue with local assignment even if High Level update fails
    }

    // Store assignment locally
    jobAssignments.set(jobInfo.id, assignment);

    // Send confirmation to cleaner
    const confirmationMessage = `✅ **Job Assignment Confirmed**\n\n` +
      `📅 **Date/Time**: ${jobInfo.dateTime}\n` +
      `📍 **Address**: ${jobInfo.address}\n` +
      `💵 **Pay**: ${jobInfo.pay}\n\n` +
      `⏰ **Important Reminders**:\n` +
      `• You'll receive a 24-hour reminder\n` +
      `• You'll receive a 2-hour reminder\n` +
      `• Check in 15 minutes before start time to avoid lateness\n` +
      `• Complete all required checklists and photos\n\n` +
      `Good luck with your job! 🧽✨`;

    await user.send(confirmationMessage);

    // 🚀 Schedule job reminders for this cleaner
    await scheduleJobReminders(user.username, async (reminderData) => {
      // This callback will be called for 24h and 2h reminders
      await sendJobReminder(user.id, reminderData);
    });

    // Notify ops team
    const opsNotification = `👷 **Job Assignment Update**\n\n` +
      `**Job**: ${jobInfo.title || 'Cleaning Job'}\n` +
      `**Assigned to**: ${user.username}\n` +
      `**Date/Time**: ${jobInfo.dateTime}\n` +
      `**Address**: ${jobInfo.address}\n\n` +
      `Reminders have been scheduled automatically.`;

    if (process.env.OPS_LEAD_DISCORD_ID) {
      await sendDiscordPing(process.env.OPS_LEAD_DISCORD_ID, opsNotification);
    }

    // Update the job board message to show assignment
    try {
      const updatedContent = addAssignmentToJobPost(message.content, user.username);
      await message.edit(updatedContent);
    } catch (error) {
      console.error('[JobAssignment] Error updating job board message:', error);
    }

    console.log(`[JobAssignment] Successfully assigned job ${jobInfo.id} to ${user.username}`);
    return true;

  } catch (error) {
    console.error('[JobAssignment] Error handling job board reaction:', error);
    await user.send('❌ Sorry, there was an error processing your job assignment. Please contact ops team.');
    return false;
  }
}

/**
 * Extract job information from Discord job board message
 * @param {string} messageContent - The job board message content
 * @returns {Object|null} Extracted job info or null if not found
 */
function extractJobInfoFromMessage(messageContent) {
  try {
    const lines = messageContent.split('\n');
    const jobInfo = {};

    // Extract basic info using regex patterns
    for (const line of lines) {
      if (line.includes('📅 **Date/Time**:')) {
        jobInfo.dateTime = line.replace('📅 **Date/Time**:', '').trim();
      }
      if (line.includes('📍 **Address**:')) {
        jobInfo.address = line.replace('📍 **Address**:', '').trim();
      }
      if (line.includes('💵 **Pay**:')) {
        jobInfo.pay = line.replace('💵 **Pay**:', '').trim();
      }
      if (line.includes('🛏️ **Bedrooms**:')) {
        jobInfo.bedrooms = line.replace('🛏️ **Bedrooms**:', '').trim();
      }
      if (line.includes('🚽 **Bathrooms**:')) {
        jobInfo.bathrooms = line.replace('🚽 **Bathrooms**:', '').trim();
      }
    }

    // Generate a job ID if not present (based on address and time)
    if (jobInfo.address && jobInfo.dateTime) {
      jobInfo.id = generateJobId(jobInfo.address, jobInfo.dateTime);
      jobInfo.title = `Cleaning Job - ${jobInfo.address}`;
      return jobInfo;
    }

    return null;
  } catch (error) {
    console.error('[JobAssignment] Error extracting job info:', error);
    return null;
  }
}

/**
 * Generate a unique job ID from address and date/time
 * @param {string} address - Job address
 * @param {string} dateTime - Job date/time
 * @returns {string} Generated job ID
 */
function generateJobId(address, dateTime) {
  const addressHash = address.replace(/[^\w]/g, '').substring(0, 10);
  const timeHash = new Date(dateTime).getTime().toString().substring(-6);
  return `job_${addressHash}_${timeHash}`;
}

/**
 * Add assignment information to job board post
 * @param {string} originalContent - Original job board message
 * @param {string} assignedTo - Username of assigned cleaner
 * @returns {string} Updated message content
 */
function addAssignmentToJobPost(originalContent, assignedTo) {
  const assignmentNote = `\n\n✅ **ASSIGNED TO**: ${assignedTo}`;
  
  // Check if already assigned
  if (originalContent.includes('**ASSIGNED TO**:')) {
    return originalContent.replace(/✅ \*\*ASSIGNED TO\*\*:.*/, assignmentNote);
  }
  
  return originalContent + assignmentNote;
}

/**
 * Send job reminder to cleaner
 * @param {string} userId - Discord user ID
 * @param {Object} reminderData - Reminder data from scheduler
 */
async function sendJobReminder(userId, reminderData) {
  try {
    const { type, job, scheduledTime } = reminderData;
    
    let message;
    if (type === '24h') {
      message = `⏰ **24 Hour Job Reminder**\n\n` +
        `You have a cleaning job scheduled for tomorrow!\n\n` +
        `📅 **Time**: ${new Date(scheduledTime).toLocaleString('en-US', { timeZone: 'America/Chicago' })}\n` +
        `📍 **Address**: ${job.address || 'Address TBD'}\n` +
        `💵 **Pay**: ${job.pay || 'TBD'}\n\n` +
        `Please prepare your supplies and confirm you'll be there on time!`;
    } else if (type === '2h') {
      message = `🚨 **2 Hour Job Reminder**\n\n` +
        `Your cleaning job starts in 2 hours!\n\n` +
        `📅 **Time**: ${new Date(scheduledTime).toLocaleString('en-US', { timeZone: 'America/Chicago' })}\n` +
        `📍 **Address**: ${job.address || 'Address TBD'}\n\n` +
        `⚠️ **Remember**: Check in 15 minutes before start time to avoid lateness strikes.`;
    }

    await sendDiscordPing(userId, message);
    console.log(`[JobAssignment] Sent ${type} reminder`);

  } catch (error) {
    console.error('[JobAssignment] Error sending job reminder:', error);
  }
}

/**
 * Handle pre-assigned jobs (scheduled directly in High Level with cleaner assigned)
 * @param {Object} jobData - Job data from High Level webhook
 * @param {Object} client - Discord client
 */
async function handlePreAssignedJob(jobData, client) {
  try {
    const assignedCleaner = jobData.assignedTo || jobData.userName;
    
    if (!assignedCleaner || assignedCleaner.toLowerCase().startsWith('available')) {
      // Not pre-assigned, will go through normal job board process
      return false;
    }

    console.log(`[JobAssignment] Handling pre-assigned job for ${assignedCleaner}`);

    // Find the cleaner's Discord user ID
    const cleanerUserId = await getUserIdFromUsername(client, assignedCleaner);
    
    if (!cleanerUserId) {
      console.error(`[JobAssignment] Could not find Discord user for cleaner: ${assignedCleaner}`);
      // Notify ops team
      if (process.env.OPS_LEAD_DISCORD_ID) {
        await sendDiscordPing(process.env.OPS_LEAD_DISCORD_ID, 
          `⚠️ Job assigned to ${assignedCleaner} but couldn't find their Discord account. Please verify manually.`);
      }
      return false;
    }

    // Store assignment
    const assignment = {
      jobId: jobData.id,
      assignedTo: assignedCleaner,
      assignedUserId: cleanerUserId,
      assignedAt: new Date().toISOString(),
      jobInfo: jobData,
      preAssigned: true
    };

    jobAssignments.set(jobData.id, assignment);

    // Send notification to cleaner
    const notificationMessage = `📋 **New Job Assignment**\n\n` +
      `You've been assigned a cleaning job!\n\n` +
      `📅 **Date/Time**: ${jobData.dateTime || 'TBD'}\n` +
      `📍 **Address**: ${jobData.address || 'TBD'}\n` +
      `💵 **Pay**: ${jobData.pay || 'TBD'}\n\n` +
      `⏰ **Important**:\n` +
      `• You'll receive automatic reminders\n` +
      `• Check in 15 minutes before start time\n` +
      `• Complete all checklists and photos\n\n` +
      `Contact ops if you have any questions!`;

    await sendDiscordPing(cleanerUserId, notificationMessage);

    // 🚀 Schedule reminders
    await scheduleJobReminders(assignedCleaner, async (reminderData) => {
      await sendJobReminder(cleanerUserId, reminderData);
    });

    console.log(`[JobAssignment] Pre-assigned job setup complete for ${assignedCleaner}`);
    return true;

  } catch (error) {
    console.error('[JobAssignment] Error handling pre-assigned job:', error);
    return false;
  }
}

/**
 * Get assignment information for a job
 * @param {string} jobId - Job ID
 * @returns {Object|null} Assignment info or null if not assigned
 */
function getJobAssignment(jobId) {
  return jobAssignments.get(jobId) || null;
}

/**
 * Get all jobs assigned to a cleaner
 * @param {string} username - Cleaner username
 * @returns {Array} Array of assigned jobs
 */
function getJobsForCleaner(username) {
  const assignments = [];
  for (const [jobId, assignment] of jobAssignments) {
    if (assignment.assignedTo === username) {
      assignments.push(assignment);
    }
  }
  return assignments;
}

/**
 * Clear assignment cache (for testing or maintenance)
 */
function clearAssignmentCache() {
  jobAssignments.clear();
  reactionTracking.clear();
  console.log('[JobAssignment] Assignment cache cleared');
}

module.exports = {
  handleJobBoardReaction,
  handlePreAssignedJob,
  getJobAssignment,
  getJobsForCleaner,
  extractJobInfoFromMessage,
  addAssignmentToJobPost,
  sendJobReminder,
  clearAssignmentCache
};
