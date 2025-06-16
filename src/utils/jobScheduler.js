// src/utils/jobScheduler.js
// Job scheduling utilities to integrate with High Level and provide dynamic job timing for Keith

const { getJobsForCleaner, getAllJobs } = require('./highlevel');
const { DateTime } = require('luxon');

/**
 * Get the next scheduled job for a cleaner
 * @param {string} cleanerName - Name of the cleaner
 * @returns {Promise<Object|null>} Next job object or null if none found
 */
async function getNextJobForCleaner(cleanerName) {
  try {
    const jobs = await getJobsForCleaner(cleanerName);
    const now = DateTime.now().setZone('America/Chicago');
    
    // Filter to jobs that are today or in the future
    const upcomingJobs = jobs.filter(job => {
      if (!job.startTime) return false;
      const jobTime = DateTime.fromISO(job.startTime, { zone: 'America/Chicago' });
      return jobTime >= now.startOf('day');
    });
    
    // Sort by start time and return the earliest
    upcomingJobs.sort((a, b) => {
      const timeA = DateTime.fromISO(a.startTime, { zone: 'America/Chicago' });
      const timeB = DateTime.fromISO(b.startTime, { zone: 'America/Chicago' });
      return timeA.toMillis() - timeB.toMillis();
    });
    
    return upcomingJobs[0] || null;
  } catch (error) {
    console.error('[JobScheduler] Error fetching next job for cleaner:', error);
    return null;
  }
}

/**
 * Get current/active job for a cleaner based on time proximity
 * @param {string} cleanerName - Name of the cleaner
 * @param {number} windowMinutes - Time window around job start time (default: 30 minutes)
 * @returns {Promise<Object|null>} Current job object or null if none found
 */
async function getCurrentJobForCleaner(cleanerName, windowMinutes = 30) {
  try {
    const jobs = await getJobsForCleaner(cleanerName);
    const now = DateTime.now().setZone('America/Chicago');
    
    // Find job that's within the time window (before/after start time)
    for (const job of jobs) {
      if (!job.startTime) continue;
      
      const jobTime = DateTime.fromISO(job.startTime, { zone: 'America/Chicago' });
      const timeDiff = Math.abs(now.toMillis() - jobTime.toMillis());
      const windowMs = windowMinutes * 60 * 1000;
      
      if (timeDiff <= windowMs) {
        return job;
      }
    }
    
    return null;
  } catch (error) {
    console.error('[JobScheduler] Error fetching current job for cleaner:', error);
    return null;
  }
}

/**
 * Check if a cleaner is late for their current job
 * @param {string} cleanerName - Name of the cleaner
 * @param {number} lateThresholdMinutes - Minutes after start time to consider late (default: 5)
 * @returns {Promise<Object>} { isLate: boolean, job: Object|null, minutesLate: number }
 */
async function checkLatenessForCleaner(cleanerName, lateThresholdMinutes = 5) {
  try {
    const job = await getCurrentJobForCleaner(cleanerName, 60); // 1 hour window
    if (!job || !job.startTime) {
      return { isLate: false, job: null, minutesLate: 0 };
    }
    
    const now = DateTime.now().setZone('America/Chicago');
    const jobTime = DateTime.fromISO(job.startTime, { zone: 'America/Chicago' });
    const lateThreshold = jobTime.plus({ minutes: lateThresholdMinutes });
    
    const isLate = now > lateThreshold;
    const minutesLate = isLate ? Math.floor((now.toMillis() - lateThreshold.toMillis()) / (60 * 1000)) : 0;
    
    return {
      isLate,
      job,
      minutesLate,
      scheduledTime: jobTime.toISO(),
      currentTime: now.toISO()
    };
  } catch (error) {
    console.error('[JobScheduler] Error checking lateness for cleaner:', error);
    return { isLate: false, job: null, minutesLate: 0 };
  }
}

/**
 * Get all jobs scheduled for today
 * @returns {Promise<Array>} Array of today's jobs
 */
async function getTodaysJobs() {
  try {
    const allJobs = await getAllJobs();
    const today = DateTime.now().setZone('America/Chicago').startOf('day');
    const tomorrow = today.plus({ days: 1 });
    
    return allJobs.filter(job => {
      if (!job.startTime) return false;
      const jobTime = DateTime.fromISO(job.startTime, { zone: 'America/Chicago' });
      return jobTime >= today && jobTime < tomorrow;
    });
  } catch (error) {
    console.error('[JobScheduler] Error fetching today\'s jobs:', error);
    return [];
  }
}

/**
 * Map Discord username to cleaner name (can be expanded with database lookup)
 * @param {string} discordUsername - Discord username
 * @returns {string} Cleaner name for High Level lookup
 */
function mapDiscordUserToCleaner(discordUsername) {
  // Simple mapping for now - can be expanded with database lookup
  const userMapping = {
    // Add your cleaner Discord username mappings here
    // 'discord_username': 'High Level Cleaner Name'
  };
  
  return userMapping[discordUsername.toLowerCase()] || discordUsername;
}

/**
 * Schedule pre-job reminders for a cleaner
 * @param {string} cleanerName - Name of the cleaner
 * @param {Function} reminderCallback - Function to call for sending reminders
 * @returns {Promise<Array>} Array of scheduled reminder timeouts
 */
async function scheduleJobReminders(cleanerName, reminderCallback) {
  try {
    const nextJob = await getNextJobForCleaner(cleanerName);
    if (!nextJob || !nextJob.startTime) {
      console.log(`[JobScheduler] No upcoming job found for ${cleanerName}`);
      return [];
    }
    
    const jobTime = DateTime.fromISO(nextJob.startTime, { zone: 'America/Chicago' });
    const now = DateTime.now().setZone('America/Chicago');
    
    // Schedule 24 hour and 2 hour reminders
    const reminders = [
      { time: jobTime.minus({ hours: 24 }), type: '24h' },
      { time: jobTime.minus({ hours: 2 }), type: '2h' }
    ];
    
    const timeouts = [];
    
    for (const reminder of reminders) {
      const delay = reminder.time.toMillis() - now.toMillis();
      
      if (delay > 0) {
        const timeout = setTimeout(() => {
          reminderCallback({
            type: reminder.type,
            cleaner: cleanerName,
            job: nextJob,
            scheduledTime: jobTime.toISO()
          });
        }, delay);
        
        timeouts.push(timeout);
        console.log(`[JobScheduler] Scheduled ${reminder.type} reminder for ${cleanerName} at ${reminder.time.toFormat('MMM dd HH:mm')}`);
      }
    }
    
    return timeouts;
  } catch (error) {
    console.error('[JobScheduler] Error scheduling reminders:', error);
    return [];
  }
}

module.exports = {
  getNextJobForCleaner,
  getCurrentJobForCleaner,
  checkLatenessForCleaner,
  getTodaysJobs,
  mapDiscordUserToCleaner,
  scheduleJobReminders
};
