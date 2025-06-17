require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const Ava = require('./agents/ava');
const KeithEnhanced = require('./agents/keithEnhanced');
const ScheduleManager = require('./agents/scheduleManager');
const EmailCommunicationMonitor = require('./utils/emailCommunicationMonitor');
const Maya = require('./agents/maya');
const Zara = require('./agents/zara');
const Nikolai = require('./agents/nikolai');
const Iris = require('./agents/iris');
const Jules = require('./agents/jules');
const AgentCoordinator = require('./utils/agentCoordinator');
const { logCheckin, logCheckout } = require('./utils/notion');
const { schedulePunctualityEscalation } = require('./utils/punctualityEscalation');
const { getAllJobs, extractJobForDiscord } = require('./utils/highlevel');
const { costMonitor, costTrackingMiddleware } = require('./utils/simpleCostMonitor');
const { handleJobBoardReaction, handlePreAssignedJob } = require('./utils/jobAssignment');
// const { createDatabaseManager } = require('./utils/databaseManager');
const express = require('express');
const bodyParser = require('body-parser');

const client = new Client({ 
  intents: [
    GatewayIntentBits.Guilds, 
    GatewayIntentBits.GuildMessages, 
    GatewayIntentBits.MessageContent, 
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.GuildMessageReactions
  ] 
});

// Initialize database manager
let dbManager;

// Initialize Agent Coordinator for smart routing and spam prevention
const coordinator = new AgentCoordinator();

// Instantiate agents
const ava = new Ava(client);
const keith = new KeithEnhanced(client);
const scheduleManager = new ScheduleManager(client);
const emailMonitor = new EmailCommunicationMonitor(client);
const maya = new Maya(client);
const zara = new Zara(client);
const nikolai = new Nikolai(client);
const iris = new Iris(client);
const jules = new Jules(client);

// Create agent registry for coordinator
const agentRegistry = [
  { agentId: 'ava', instance: ava, getContext: (msg) => ava.getContext ? ava.getContext(msg) : {}, handleEvent: (msg, ctx) => ava.handleMessage(msg) },
  { agentId: 'keith', instance: keith, getContext: (msg) => keith.getContext ? keith.getContext(msg) : {}, handleEvent: (msg, ctx) => keith.handleMessage(msg) },
  { agentId: 'scheduleManager', instance: scheduleManager, getContext: (msg) => scheduleManager.getContext ? scheduleManager.getContext(msg) : {}, handleEvent: (msg, ctx) => scheduleManager.handleMessage(msg) },
  { agentId: 'maya', instance: maya, getContext: (msg) => maya.getContext(msg), handleEvent: (msg, ctx) => maya.handleEvent(msg, ctx) },
  { agentId: 'zara', instance: zara, getContext: (msg) => zara.getContext(msg), handleEvent: (msg, ctx) => zara.handleEvent(msg, ctx) },
  { agentId: 'nikolai', instance: nikolai, getContext: (msg) => nikolai.getContext(msg), handleEvent: (msg, ctx) => nikolai.handleEvent(msg, ctx) },
  { agentId: 'iris', instance: iris, getContext: (msg) => iris.getContext(msg), handleEvent: (msg, ctx) => iris.handleEvent(msg, ctx) },
  { agentId: 'jules', instance: jules, getContext: (msg) => jules.getContext(msg), handleEvent: (msg, ctx) => jules.handleEvent(msg, ctx) }
];

// Initialize simple monitoring on startup
async function initializeSystem() {
  try {
    // dbManager = await createDatabaseManager();
    console.log('✅ Simple cost monitoring initialized');
    
    // Start cost monitoring dashboard (every hour)
    setInterval(() => {
      if (process.env.COST_MONITORING_ENABLED === 'true') {
        costMonitor.printDashboard();
      }
    }, 60 * 60 * 1000); // 1 hour
    
    console.log('✅ Cost monitoring started');
  } catch (error) {
    console.error('❌ Failed to initialize monitoring:', error.message);
  }
}

client.once('ready', async () => {
  console.log(`Discord bot logged in as ${client.user.tag}`);
  ava.onReady();
  keith.onReady();
  scheduleManager.onReady();
  maya.onReady();
  zara.onReady();
  nikolai.onReady();
  iris.onReady();
  jules.onReady();
  
  // Initialize email communication monitor
  console.log('🚀 Initializing email communication monitor...');
  const emailInitialized = await emailMonitor.initialize();
  if (emailInitialized) {
    await emailMonitor.startMonitoring();
    console.log('✅ Email communication monitoring started');
  } else {
    console.log('⚠️ Email monitoring failed to initialize - continuing without it');
  }
  
  // Initialize database and monitoring systems
  await initializeSystem();
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  
  // --- Approval reply logic ---
  if (message.channel.type === 1 && message.author.id === OPS_LEAD_DISCORD_ID) {
    const content = message.content.trim().toLowerCase();
    if (content === 'yes' || content === 'approve') {
      // Find the last job DM sent for approval (store in memory for now)
      if (client.lastJobForApproval) {
        // Post to job-board channel
        const jobBoardChannelId = process.env.DISCORD_JOB_BOARD_CHANNEL_ID || '1367338545802383401';
        const channel = await client.channels.fetch(jobBoardChannelId);
        const job = client.lastJobForApproval;
        let postMsg = `**New Job Available!**\n\n` +
          `📣 **Title:** ${job.jobTitle}\n` +
          `📅 **Date/Time:** ${job.dateTime}\n` +
          `📍 **Address:** ${job.address}\n` +
          (job.bedrooms ? `🛏️ **Bedrooms:** ${job.bedrooms}\n` : '') +
          (job.bathrooms ? `🚽 **Bathrooms:** ${job.bathrooms}\n` : '') +
          // (job.type ? `🧹 **Type:** ${job.type}\n` : '') +
          (job.pay ? `💵 **Pay:** ${job.pay}\n` : '') +
          (job.pets ? `🐕 **Pets:** ${job.pets}\n` : '') +
          (job.notes ? `📜 **Special Instructions:** ${job.notes}\n` : '');
        await channel.send(postMsg);
        await message.reply('Job posted to the job board!');
        client.lastJobForApproval = null;
      } else {
        await message.reply('No job found for approval.');
      }
    } else if (content === 'no' || content === 'reject') {
      client.lastJobForApproval = null;
      await message.reply('Job not posted.');
    }
    return;
  }
  
  // --- Enhanced Multi-Agent Message Routing with Coordinator ---
  try {
    console.log(`[Coordinator] 🎯 Processing message from ${message.author.username}: "${message.content.substring(0, 50)}..."`);
    
    // Use AgentCoordinator for intelligent routing and spam prevention
    const coordinationResult = await coordinator.routeEvent(message, agentRegistry);
    
    if (coordinationResult.duplicate) {
      console.log(`[Coordinator] ⏭️ Skipped duplicate event processing`);
      return;
    }
    
    if (!coordinationResult.processed) {
      console.log(`[Coordinator] ⚠️ Event not processed: ${coordinationResult.reason}`);
      return;
    }
    
    // Process coordination results and handle Notion logging
    const { results, processing_time } = coordinationResult;
    console.log(`[Coordinator] ✅ Event processed by ${coordinationResult.agents_involved.length} agents in ${processing_time}ms`);
    
    // Handle Notion logging from agent results
    for (const agentResult of results) {
      if (agentResult.error) {
        console.error(`[${agentResult.agent_id.toUpperCase()}] Agent Error:`, agentResult.error);
        continue;
      }
      
      const result = agentResult.result;
      console.log(`[${agentResult.agent_id.toUpperCase()}] Agent Output (Confidence: ${agentResult.confidence}):`, JSON.stringify(result, null, 2));
      
      // Handle specific agent outputs for Notion logging
      const payload = result.extra && result.extra.payload ? result.extra.payload : result.payload;
      if (payload) {
        try {
          if (result.task === 'checkin') {
            await logCheckin({
              username: payload.user || payload.username,
              timestamp: payload.timestamp,
              notes: payload.notes
            });
            console.log('[Notion] Check-in event logged successfully.');
          } else if (result.task === 'checkout') {
            await logCheckout({
              username: payload.user || payload.username,
              timestamp: payload.timestamp,
              notes: payload.notes
            });
            console.log('[Notion] Checkout event logged successfully.');
          }
        } catch (err) {
          console.error('[Notion] Failed to log event:', err.message);
        }
      }
    }
    
    // Log coordination metrics for monitoring
    const metrics = coordinator.getMetrics();
    console.log(`[Coordinator] 📊 System Metrics - Events/hr: ${metrics.events_last_hour}, Avg Processing: ${Math.round(metrics.average_processing_time)}ms, High Confidence: ${Math.round(metrics.high_confidence_rate * 100)}%`);
    
  } catch (error) {
    console.error('[Coordinator] Error processing message:', error);
  }
});

// 🚀 NEW: Handle Discord reactions for job assignment
client.on('messageReactionAdd', async (reaction, user) => {
  // Ignore bot reactions
  if (user.bot) return;

  try {
    // Fetch the reaction if it's partial
    if (reaction.partial) {
      await reaction.fetch();
    }

    // Check if this is a job board reaction
    const isJobBoardChannel = reaction.message.channel.id === process.env.DISCORD_JOB_BOARD_CHANNEL_ID;
    const isCheckmark = reaction.emoji.name === '✅';

    if (isJobBoardChannel && isCheckmark) {
      console.log(`[JobAssignment] Processing job board reaction from ${user.username}`);
      
      const success = await handleJobBoardReaction(reaction, user, client);
      
      if (success) {
        console.log(`[JobAssignment] Successfully assigned job to ${user.username}`);
      } else {
        console.log(`[JobAssignment] Failed to assign job to ${user.username}`);
      }
    }

    // Check if this is an email reply approval reaction (DM to ops lead)
    if (reaction.message.channel.type === 1) { // DM channel
      const emoji = reaction.emoji.name;
      if (emoji === '✅' || emoji === '❌') {
        console.log(`[EmailMonitor] Processing reply approval reaction: ${emoji}`);
        await emailMonitor.handleApprovalReaction(reaction.message.id, emoji, user.id);
      }
    }

  } catch (error) {
    console.error('[MessageReaction] Error handling reaction:', error);
  }
});

// Poll High Level for new jobs every 2 minutes
// setInterval(async () => {
//   try {
//     const jobs = await getAllJobs();
//     for (const job of jobs) {
//       // For now, just log to console for verification
//       console.log('[HighLevel Job]', JSON.stringify(job, null, 2));
//       // TODO: In production, check if job is new (not already posted), then post to 🪧-job-board
//     }
//   } catch (err) {
//     console.error('[HighLevel] Failed to fetch jobs:', err.message);
//   }
// }, 2 * 60 * 1000); // 2 minutes

// Example: Ava triggers punctuality escalation for a job (simulate mode for dev)
// async function simulateEscalation() {
//   const cleaner = '1381296611610853536'; // User ID for lena_r_97
//   const scheduledTime = new Date(Date.now() + 60 * 60 * 1000).toISOString(); // 1 hour from now
//   let checkedIn = false;
//   await schedulePunctualityEscalation({
//     cleaner,
//     scheduledTime,
//     hasCheckedIn: async () => checkedIn,
//     escalationTargets: ['1343301440864780291', '1368634674003447979'], // Your user ID and job-check-ins channel
//     simulate: true, // 1 min = 1 sec
//     opsDM: '1343301440864780291', // DM you at 10 min late
//     alertsChannel: '1377516295754350613', // 🚨-alerts channel for 10 min late log
//     client // pass Discord client for username lookup
//   });
// }

// Uncomment to test escalation logic on startup
// simulateEscalation();

client.login(process.env.DISCORD_BOT_TOKEN);

// --- Express Webhook Server Setup ---
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'supersecret'; // Set this in your .env for production
const WEBHOOK_PORT = process.env.WEBHOOK_PORT || 3000;
const WEBHOOK_PATH = '/webhook/highlevel-appointment';

// Replace with your Discord user ID (for Ava to DM you)
const OPS_LEAD_DISCORD_ID = '1343301440864780291';

const app = express();
app.use(bodyParser.json());

// Health check endpoint with simple stats and coordination metrics
app.get('/health', async (req, res) => {
  try {
    const stats = costMonitor.getStats();
    const coordinatorMetrics = coordinator.getMetrics();
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'Notion',
      cost_stats: stats,
      coordination_metrics: coordinatorMetrics,
      agents_active: agentRegistry.length,
      system_version: '2.0-enhanced'
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      error: error.message
    });
  }
});

// Cost dashboard endpoint
app.get('/dashboard', async (req, res) => {
  try {
    const stats = costMonitor.getStats();
    const coordinatorMetrics = coordinator.getMetrics();
    res.json({
      cost_stats: stats,
      coordination_metrics: coordinatorMetrics,
      active_agents: agentRegistry.map(a => a.agentId)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Secure High Level appointment webhook endpoint
app.post(WEBHOOK_PATH, async (req, res) => {
  try {
    const secret = req.headers['x-webhook-secret'];
    if (secret !== WEBHOOK_SECRET) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    const appointment = req.body;
    console.log('[Webhook] Appointment received:', JSON.stringify(appointment, null, 2));
    res.status(200).json({ status: 'received' });

    // Check if this is a schedule change request
    const isScheduleChange = appointment.type === 'appointment_updated' || 
                            appointment.eventType === 'AppointmentUpdate' ||
                            (appointment.appointmentStatus && appointment.appointmentStatus.includes('reschedule'));
    
    if (isScheduleChange) {
      console.log('[ScheduleManager] Processing schedule change webhook');
      const scheduleResult = await scheduleManager.handleWebhook(appointment);
      if (scheduleResult) {
        console.log('[ScheduleManager] Schedule change processed:', scheduleResult);
        return;
      }
    }

    // --- Discord job board logic ---
    const job = extractJobForDiscord(appointment);
    if (job) {
      // 🚀 NEW: Check if this is a pre-assigned job first
      const isPreAssigned = await handlePreAssignedJob(job, client);
      
      if (isPreAssigned) {
        console.log('[Webhook] Job was pre-assigned, skipping approval workflow');
        return;
      }
      
      // Continue with normal approval workflow for unassigned jobs
      const dmMsg = `**New Job Approval Needed**\n\n` +
        `📣 **Title:** ${job.jobTitle}\n` +
        `📅 **Date/Time:** ${job.dateTime}\n` +
        `📍 **Address:** ${job.address}\n` +
        (job.bedrooms ? `🛏️ **Bedrooms:** ${job.bedrooms}\n` : '') +
        (job.bathrooms ? `🚽 **Bathrooms:** ${job.bathrooms}\n` : '') +
        // (job.type ? `🧹 **Type:** ${job.type}\n` : '') +
        (job.pay ? `💵 **Pay:** ${job.pay}\n` : '') +        (job.pets ? `🐕 **Pets:** ${job.pets}\n` : '') +
        (job.notes ? `📜 **Special Instructions:** ${job.notes}\n` : '') +
        `\nApprove this job for posting to the job board? (Reply 'yes' or 'no')`;
      
      try {
        const user = await client.users.fetch(OPS_LEAD_DISCORD_ID);
        await user.send(dmMsg);
        client.lastJobForApproval = job; // Store for approval
        console.log('[Ava] Sent job approval DM to ops lead.');
        
        // Track cost
        costMonitor.logOperation('notion');
      } catch (err) {
        console.error('[Ava] Failed to DM ops lead:', err.message);
      }
    } else {
      console.log('[Ava] Job is not up for grabs (not assigned to Available _), skipping job board DM.');
    }
    
  } catch (error) {
    console.error('[Webhook] Error processing appointment:', error.message);
  }
});

app.listen(WEBHOOK_PORT, () => {
  console.log(`[Express] Webhook server listening on port ${WEBHOOK_PORT}`);
  console.log(`[Express] POST endpoint: http://localhost:${WEBHOOK_PORT}${WEBHOOK_PATH}`);
});

// Gmail OAuth callback route
app.get('/oauth/callback', async (req, res) => {
  try {
    const { code, state } = req.query;
    
    if (!code) {
      return res.status(400).send('Authorization code not found');
    }
    
    console.log('[Gmail OAuth] Received authorization code for email:', state);
    
    // Exchange authorization code for tokens
    const { google } = require('googleapis');
    const oauth2Client = new google.auth.OAuth2(
      process.env.GMAIL_CLIENT_ID,
      process.env.GMAIL_CLIENT_SECRET,
      'https://grimeguardians.com/oauth/callback'
    );
    
    try {
      const { tokens } = await oauth2Client.getToken(code);
      console.log('[Gmail OAuth] Successfully received tokens for:', state);
      
      // Save tokens to a file for the specific email
      const fs = require('fs');
      const tokenFilePath = `/root/grime-guardians-hq/gmail-tokens-${state || 'default'}.json`;
      fs.writeFileSync(tokenFilePath, JSON.stringify(tokens, null, 2));
      console.log('[Gmail OAuth] Tokens saved to:', tokenFilePath);
      
      res.send(`
        <html>
          <body>
            <h2>Gmail OAuth Authorization Successful!</h2>
            <p>Tokens have been saved for: <strong>${state || 'default account'}</strong></p>
            <p>You can close this window and return to your application.</p>
            <script>
              setTimeout(function() {
                window.close();
              }, 3000);
            </script>
          </body>
        </html>
      `);
      
    } catch (tokenError) {
      console.error('[Gmail OAuth] Token exchange failed:', tokenError);
      res.status(500).send('Failed to exchange authorization code for tokens: ' + tokenError.message);
    }
    
  } catch (error) {
    console.error('[Gmail OAuth] Callback error:', error);
    res.status(500).send('OAuth callback error: ' + error.message);
  }
});
