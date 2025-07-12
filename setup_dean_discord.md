# Dean Discord Setup Instructions

## Required Environment Variables

Add these to your `.env` file on the server:

```bash
# Dean's Discord Bot Token (from Discord Developer Portal)
DEAN_DISCORD_BOT_TOKEN=your_dean_bot_token_here

# Discord Channel IDs for Dean
DEAN_SALES_CHANNEL_ID=your_sales_channel_id
DEAN_ALERTS_CHANNEL_ID=your_alerts_channel_id

# Dean-specific settings
DEAN_APPROVAL_CHANNEL_ID=your_approval_channel_id  # For email approvals
DEAN_REPORTS_CHANNEL_ID=your_reports_channel_id    # For daily/weekly reports
```

## Discord Server Setup

### 1. Create Dean-Specific Channels

Create these channels in your Discord server:

#### **#sales-strategy** (Dean's main channel)
- Purpose: Strategic sales discussions
- Permissions: Management team only
- Channel topic: "Dean's Strategic Sales Command Center"

#### **#email-approvals** (Email approval workflow)
- Purpose: Review and approve outbound emails
- Permissions: Decision-makers only
- Channel topic: "Review pending emails before sending"

#### **#sales-reports** (Analytics and reporting)
- Purpose: Campaign metrics and performance
- Permissions: Management team only
- Channel topic: "Daily/weekly sales performance reports"

#### **#lead-alerts** (New lead notifications)
- Purpose: Real-time lead activity alerts
- Permissions: Sales team access
- Channel topic: "New leads and response notifications"

### 2. Get Channel IDs

For each channel you created:
1. Right-click the channel name
2. Click "Copy Channel ID"
3. Add to your `.env` file

### 3. Invite Dean to Server

Use the OAuth URL from Discord Developer Portal to invite Dean.

## Testing Dean's Functionality

### Basic Commands to Test:

```
!gg dean                    # Show Dean's main menu
!gg dean campaigns          # View active campaigns
!gg dean approvals          # Check pending emails
!gg dean create             # Get campaign creation info
```

### Conversation Testing:

Try these messages to trigger Dean:
```
Dean, how are our sales going?
Dean, let's create a new campaign for property managers
Dean, what's our email performance this week?
```

### Email Approval Workflow:

1. Dean creates email campaign
2. Emails appear in #email-approvals channel
3. React with ✅ to approve, ❌ to reject
4. Approved emails are sent automatically

## Expected Behavior

✅ **Dean should respond to strategic sales keywords**
✅ **Ultra-concise responses (2 sentences max)**
✅ **Email campaign management through Discord**
✅ **Approval workflow for outbound emails**
✅ **Real-time lead notifications**
✅ **Campaign performance reporting**

## Troubleshooting

### Dean Not Responding:
1. Check bot token in `.env` file
2. Verify channel IDs are correct
3. Ensure bot has proper permissions
4. Check systemd service status: `systemctl status grime-guardians-discord`

### Email Approvals Not Working:
1. Verify DEAN_APPROVAL_CHANNEL_ID is set
2. Check that Dean has reaction permissions
3. Ensure Email Agent is properly integrated

### Commands Not Working:
1. Verify bot has "Use Slash Commands" permission
2. Try `!gg help_gg` to see available commands
3. Check Discord bot logs for errors