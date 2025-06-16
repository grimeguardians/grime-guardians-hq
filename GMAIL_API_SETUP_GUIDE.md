# 📧 GMAIL API SETUP GUIDE - Complete Instructions

## 🎯 Overview
This setup enables your 8-agent system to monitor email communications from Google Voice (612-584-9396) for complete multi-channel communication monitoring.

---

## 📋 STEP-BY-STEP SETUP PROCESS

### 1. Google Cloud Console Setup

#### A. Access Google Cloud Console
- Go to: **https://console.cloud.google.com/**
- Sign in with your Gmail account (the one that receives Google Voice emails)

#### B. Create or Select Project
```
1. Click "Select a project" dropdown (top of page)
2. Click "NEW PROJECT"
3. Project name: "Grime Guardians Communications"
4. Click "CREATE"
5. Wait for project creation, then SELECT the project
```

#### C. Enable Gmail API
```
1. Go to: APIs & Services → Library
2. Search for "Gmail API"
3. Click "Gmail API" from results
4. Click "ENABLE" button
5. Wait for API to be enabled (green checkmark)
```

### 2. OAuth2 Credentials Setup

#### A. Configure OAuth Consent Screen
```
1. Go to: APIs & Services → OAuth consent screen
2. Choose "External" user type
3. Click "CREATE"
4. Fill out required fields:
   - App name: "Grime Guardians Communication Monitor"
   - User support email: [your email]
   - Developer contact info: [your email]
5. Click "SAVE AND CONTINUE"
6. Skip "Scopes" for now → "SAVE AND CONTINUE" 
7. Add test users:
   - Click "ADD USERS"
   - Enter your Gmail address
   - Click "SAVE AND CONTINUE"
8. Review and click "BACK TO DASHBOARD"
```

#### B. Create OAuth2 Credentials
```
1. Go to: APIs & Services → Credentials
2. Click "+ CREATE CREDENTIALS"
3. Select "OAuth 2.0 Client IDs"
4. Application type: "Web application"
5. Name: "Grime Guardians Gmail Monitor"
6. Authorized redirect URIs:
   - Click "ADD URI"
   - Enter: http://localhost:3000/oauth/callback
7. Click "CREATE"
8. **IMPORTANT**: Copy the Client ID and Client Secret
```

### 3. Environment Configuration

Add these lines to your `.env` file:

```bash
# Gmail API Configuration
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:3000/oauth/callback
```

**Replace `your_client_id_here` and `your_client_secret_here` with the actual values from step 2B.**

### 4. Run Authentication Script

```bash
cd "/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ"
node scripts/setup-gmail-auth.js
```

**What happens:**
1. Script opens your browser automatically
2. You'll see Google OAuth consent screen
3. Click "Continue" (it may show "unsafe" warning - that's normal for development)
4. Grant permissions for Gmail access
5. Browser redirects back to localhost
6. Script automatically extracts tokens and updates your `.env` file
7. Tests Gmail connection

### 5. Verification

After successful setup, you should see:
```
✅ Gmail authentication successful!
✅ Gmail API connection test passed
✅ Google Voice email monitoring ready
✅ .env file updated with tokens
```

---

## 🔧 TROUBLESHOOTING

### Common Issues & Solutions

#### Issue: "App isn't verified" warning
**Solution**: 
- Click "Advanced" 
- Click "Go to Grime Guardians Communication Monitor (unsafe)"
- This is normal for development apps

#### Issue: "Access blocked" error
**Solution**: 
- Make sure you added your Gmail address as a test user (Step 2A.7)
- Try using an incognito/private browser window

#### Issue: "Redirect URI mismatch"
**Solution**: 
- Verify the redirect URI in Google Cloud Console exactly matches: `http://localhost:3000/oauth/callback`
- Check your `.env` file has the correct `GMAIL_REDIRECT_URI`

#### Issue: Script hangs on "Waiting for authorization..."
**Solution**: 
- Check if your browser blocked the popup
- Manually go to the URL shown in the terminal
- Make sure no other service is using port 3000

---

## 🚀 WHAT THIS ENABLES

Once Gmail API is configured, your system gains:

### 📧 **Complete Email Monitoring**
- **Google Voice SMS**: Monitor 612-584-9396 texts via Gmail
- **Client Communications**: Track all client email interactions
- **Automated Responses**: Smart reply suggestions powered by GPT-4
- **Communication Logging**: All interactions stored in Notion

### 🤖 **Enhanced Agent Capabilities**
- **Ava**: Can read and respond to client emails
- **Keith**: Monitors email-based check-ins and updates
- **Schedule Manager**: Processes email-based schedule requests
- **Maya**: Sends motivational emails to team members

### 📊 **Advanced Analytics**
- **Response Times**: Track how quickly you respond to clients
- **Communication Patterns**: Identify peak contact times
- **Client Sentiment**: Analyze email tone and satisfaction
- **Automated Reporting**: Email summaries in your daily reports

---

## 🔐 SECURITY NOTES

- **Tokens are stored locally** in your `.env` file (never committed to git)
- **Read-only access** for monitoring, with controlled send permissions
- **OAuth2 standard** - Google's recommended authentication method
- **Automatic token refresh** - no manual maintenance needed

---

## 📱 WHAT TO EXPECT

After setup, you'll see in your system logs:
```
✅ Email communication monitoring started
📧 Monitoring Google Voice (612-584-9396) via Gmail
📬 Processing 3 new messages
[EmailMonitor] Client inquiry detected - routing to Ava
[EmailMonitor] Schedule request detected - routing to Schedule Manager
```

Your **8-agent system** will now have **complete visibility** into all client communications across Discord, phone/text, and email!

---

## ⚡ QUICK SETUP SUMMARY

1. **Google Cloud Console** → Create project → Enable Gmail API
2. **OAuth2 Setup** → Create credentials → Add redirect URI
3. **Update .env** → Add CLIENT_ID and CLIENT_SECRET
4. **Run script** → `node scripts/setup-gmail-auth.js`
5. **Authorize in browser** → Grant permissions
6. **Done!** → System now monitors all communication channels

**Total setup time: ~10 minutes** ⏱️

Ready to set this up? The script will guide you through each step!
