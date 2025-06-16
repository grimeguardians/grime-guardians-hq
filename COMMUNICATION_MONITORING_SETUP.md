# Communication Monitoring Setup Guide

## 🎯 Overview
This guide shows how to set up comprehensive communication monitoring for schedule changes across High Level conversations and Google Voice messages.

## 📱 High Level Conversation Monitoring

### Setup Steps:

1. **API Access**: Ensure you have your High Level API key and Location ID
   ```bash
   HIGHLEVEL_API_KEY=your_api_key_here
   HIGHLEVEL_LOCATION_ID=your_location_id_here
   ```

2. **Enable Monitoring**: The system automatically monitors High Level conversations every 15 minutes for schedule-related keywords.

3. **Keywords Detected**:
   - reschedule, schedule, move, change, cancel, postpone
   - different time, another day, push back, emergency
   - can we change, need to move, something came up
   - sick, travel, vacation, conflict

### How It Works:
- Monitors conversations from the last 24 hours
- Analyzes inbound messages (from clients)
- Detects schedule change requests with confidence scoring
- Automatically alerts operations team
- Provides intelligent auto-responses

## 📞 Google Voice Integration

### Method 1: Email Notifications (Recommended)

**Setup Gmail Forwarding:**

1. **Enable Google Voice Email Notifications**:
   - Go to Google Voice settings
   - Turn on email notifications for text messages
   - Forward notifications to a dedicated Gmail account

2. **Create App Password**:
   - Go to Google Account settings
   - Security → App passwords
   - Create password for "Mail"

3. **Configure Environment Variables**:
   ```bash
   GOOGLE_VOICE_EMAIL_MONITORING=true
   GOOGLE_VOICE_EMAIL=your_gmail@gmail.com
   GOOGLE_VOICE_EMAIL_PASSWORD=your_app_password
   IMAP_HOST=imap.gmail.com
   IMAP_PORT=993
   ```

4. **Install Required Package**:
   ```bash
   npm install imapflow
   ```

### Method 2: Direct Integration (Future Enhancement)

For direct Google Voice API access, you would need:
- Google Voice API credentials (when available)
- Or browser automation with Puppeteer

## 🔧 Environment Configuration

Add these variables to your `.env` file:

```bash
# High Level Communication Monitoring
HIGHLEVEL_API_KEY=your_api_key
HIGHLEVEL_LOCATION_ID=your_location_id

# Google Voice Email Monitoring
GOOGLE_VOICE_EMAIL_MONITORING=true
GOOGLE_VOICE_EMAIL=monitoring@yourdomain.com
GOOGLE_VOICE_EMAIL_PASSWORD=your_app_password
IMAP_HOST=imap.gmail.com
IMAP_PORT=993

# Discord Alerts
OPS_LEAD_DISCORD_ID=1343301440864780291
DISCORD_ALERTS_CHANNEL_ID=1377516295754350613
```

## 🚀 How The System Works

### 1. Continuous Monitoring
- **High Level**: Checks conversations every 15 minutes
- **Google Voice**: Monitors email notifications in real-time
- **Keywords**: Analyzes content for schedule-related terms

### 2. Intelligent Detection
```javascript
// Example detected request
{
  source: 'highlevel',
  contactName: 'Sarah Johnson',
  contactPhone: '+1-555-0123',
  message: 'Hi, I need to reschedule tomorrow's cleaning to Friday if possible',
  detection: {
    isScheduleRequest: true,
    confidence: 0.9,
    keywords: ['reschedule'],
    messageType: 'reschedule',
    suggestedTimes: [{ type: 'day', value: 'friday' }]
  },
  urgency: 'medium'
}
```

### 3. Automatic Responses
- **Urgent requests**: Immediate acknowledgment + human escalation
- **Standard requests**: Intelligent auto-response based on request type
- **Cancellations**: Confirmation request + reschedule offer
- **Reschedules**: Availability check + alternative suggestions

### 4. Operations Alerts
- **High urgency**: DM to ops lead + alerts channel
- **Standard**: DM to ops lead only
- **Comprehensive details**: Client info, message, suggested response

## 📊 Monitoring Dashboard

The system provides real-time visibility:

```javascript
// Sample monitoring output
[ScheduleManager] Found 3 schedule requests
  - High Level: 2 requests (1 urgent)
  - Google Voice: 1 request (standard)
[ScheduleManager] Sent 3 client responses
[ScheduleManager] Escalated 1 urgent request to ops team
```

## 🎯 Integration Benefits

### For Clients:
- ✅ Faster response times (15-minute detection vs hours)
- ✅ Immediate acknowledgment of urgent requests
- ✅ Professional, consistent responses
- ✅ 24/7 monitoring coverage

### For Operations:
- ✅ No missed schedule requests
- ✅ Automatic prioritization by urgency
- ✅ Comprehensive client communication history
- ✅ Reduced manual monitoring workload

### For Business:
- ✅ Higher client satisfaction
- ✅ Reduced no-shows from missed communications
- ✅ Better schedule optimization
- ✅ Professional brand consistency

## 🔄 Workflow Example

**Client texts**: "Emergency! Need to cancel today's 2pm cleaning - sick kid"

**System detects**: 
- Keywords: "emergency", "cancel"
- Urgency: HIGH
- Message type: urgent_cancellation

**Automatic actions**:
1. Sends immediate acknowledgment to client
2. Alerts ops team via Discord DM + alerts channel
3. Logs request in Notion for tracking
4. Suggests response for ops team review

**Result**: 
- Client receives response within 15 minutes
- Ops team has complete context for decision-making
- No missed communication or scheduling conflicts

## 🚀 Getting Started

1. **Add environment variables** to your `.env` file
2. **Install dependencies**: `npm install imapflow`
3. **Restart your system**: The monitoring starts automatically
4. **Test with a sample message** containing "reschedule" in High Level

Your system will now monitor all client communications for schedule changes and respond intelligently! 🎉
