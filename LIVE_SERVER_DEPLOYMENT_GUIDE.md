# 🚀 Live Server Deployment Guide - Grime Guardians

## 📊 Current Server Status Analysis

### Your Current Setup:
- ✅ **Main Application**: Production-ready Discord bot with 8 AI agents
- ✅ **MCP Servers**: Built but not currently running (notion-server, postgresql-server)
- ✅ **Local Testing**: Fully functional on localhost:3000
- ⚠️ **High Level Integration**: Disabled (ready to reconnect)

### MCP Server Status:
- **Notion MCP Server**: Available but not active
- **PostgreSQL MCP Server**: Available but not active
- **Recommendation**: Not needed for initial deployment (your system uses direct Notion API)

## 🎯 Recommended Deployment Strategy

### Option 1: Railway (RECOMMENDED - Lowest Cost)
**Cost**: $5/month, perfect for your scale
**Why Railway**:
- ✅ Simple Git-based deployment
- ✅ Automatic scaling
- ✅ Built-in domain (custom domain available)
- ✅ Perfect for Discord bots
- ✅ Generous free tier, then $5/month

### Option 2: DigitalOcean App Platform
**Cost**: $5-12/month
**Why DigitalOcean**:
- ✅ Reliable performance
- ✅ Easy scaling
- ✅ Good for long-term growth
- ✅ Integrated database options

### Option 3: Heroku
**Cost**: $7/month (after free tier)
**Why Heroku**:
- ✅ Very simple deployment
- ✅ Well-documented
- ⚠️ Can be more expensive as you scale

## 🚀 STEP-BY-STEP DEPLOYMENT (Railway - Recommended)

### Step 1: Prepare Your Repository
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - Production ready system"

# Create GitHub repository (recommended)
# Push your code to GitHub
```

### Step 2: Deploy to Railway
1. **Sign up**: Go to [Railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub account
3. **Deploy**: Select your Grime Guardians repository
4. **Configure**: Railway will auto-detect Node.js

### Step 3: Configure Environment Variables
```bash
# In Railway dashboard, add these environment variables:
DISCORD_BOT_TOKEN=your_bot_token
NOTION_SECRET=your_notion_secret
OPENAI_API_KEY=your_openai_key
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
HIGHLEVEL_API_KEY=your_highlevel_key

# Production settings
PRODUCTION_MODE=true
DISABLE_HIGHLEVEL=false  # Enable High Level once server is live
COST_MONITORING_ENABLED=true

# Server settings
PORT=3000
NODE_ENV=production
```

### Step 4: Set Up Custom Domain (Optional)
```bash
# Railway provides free subdomain: your-app.railway.app
# For custom domain (like bot.grimeguardians.com):
# 1. Add domain in Railway dashboard
# 2. Update DNS records
# 3. SSL automatically configured
```

## 🔗 High Level Integration Setup

### Once Your Server is Live:

### Step 1: Update High Level Webhook URL
```bash
# Your new webhook URL will be:
https://your-app.railway.app/webhook/highlevel-appointment

# OR with custom domain:
https://bot.grimeguardians.com/webhook/highlevel-appointment
```

### Step 2: Configure High Level
1. **Login to High Level**
2. **Go to Settings → Integrations → Webhooks**
3. **Add New Webhook**:
   - URL: `https://your-app.railway.app/webhook/highlevel-appointment`
   - Events: `appointment_created`, `appointment_updated`
   - Secret: Use your `WEBHOOK_SECRET` from .env

### Step 3: Enable High Level in Production
```bash
# Update environment variable in Railway:
DISABLE_HIGHLEVEL=false
```

### Step 4: Test Integration
```bash
# Test webhook endpoint:
curl -X POST https://your-app.railway.app/webhook/highlevel-appointment \
  -H "Content-Type: application/json" \
  -H "x-webhook-secret: your_secret" \
  -d '{"test": "webhook"}'
```

## 📋 Complete Deployment Checklist

### Pre-Deployment
- [ ] Code committed to GitHub
- [ ] All tests passing (45/45)
- [ ] Environment variables documented
- [ ] Discord bot permissions configured

### Railway Deployment
- [ ] Railway account created
- [ ] GitHub repository connected
- [ ] Environment variables configured
- [ ] First deployment successful
- [ ] Health endpoint responding

### High Level Integration
- [ ] Live server URL obtained
- [ ] High Level webhook configured
- [ ] DISABLE_HIGHLEVEL set to false
- [ ] Webhook secret configured
- [ ] Test appointment created

### Post-Deployment Testing
- [ ] Discord bot online and responding
- [ ] Agent coordination working
- [ ] High Level webhooks received
- [ ] Notion integration functional
- [ ] Gmail monitoring active

## 💰 Cost Breakdown

### Railway (Recommended)
- **Free Tier**: 512MB RAM, $5 credit/month
- **Pro Plan**: $5/month for increased limits
- **Total Monthly Cost**: $0-5 for your scale

### Additional Costs to Consider
- **Custom Domain**: $10-15/year (optional)
- **Backup Storage**: Usually included
- **Scaling**: Automatic within plan limits

### Estimated Total Monthly Cost: $5

## 🛠️ MCP Server Configuration (If Needed Later)

### Current MCP Servers:
Your system has MCP servers built but not currently needed because:
- ✅ **Direct Notion API**: Your agents use @notionhq/client directly
- ✅ **No PostgreSQL**: You're using Notion as primary database
- ✅ **Simplified Architecture**: Fewer moving parts = more reliable

### If You Want to Enable MCP Later:
```bash
# Start Notion MCP server
cd mcp-servers/notion-server
npm install
npm start

# Update main app to use MCP instead of direct API
# (This would require code changes)
```

## 🚀 Quick Start Deployment Commands

### Option A: Railway CLI (Fastest)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Option B: Manual GitHub Connection
1. Push code to GitHub
2. Go to railway.app
3. "Deploy from GitHub"
4. Select repository
5. Add environment variables
6. Deploy

## 📊 Monitoring Your Live Server

### Built-in Monitoring Endpoints
```bash
# Health check
GET https://your-app.railway.app/health

# Coordination metrics dashboard
GET https://your-app.railway.app/dashboard

# System status
curl https://your-app.railway.app/health | jq '.'
```

### Railway Dashboard
- **CPU/Memory usage**
- **Request logs**
- **Build logs**
- **Environment variables**
- **Custom metrics**

## 🎯 Next Steps After Deployment

1. **Deploy to Railway** (15 minutes)
2. **Configure High Level webhooks** (10 minutes)
3. **Test complete integration** (15 minutes)
4. **Monitor for 24 hours** to ensure stability
5. **Enable advanced features** as needed

## ⚡ Emergency Rollback Plan

If anything goes wrong:
```bash
# Quick rollback options:
# 1. Revert to previous Railway deployment (1-click)
# 2. Re-enable DISABLE_HIGHLEVEL=true
# 3. Fall back to local development
# 4. Use Railway logs to debug issues
```

Your system is **production-ready** and the deployment should be smooth. Railway is perfect for your scale and will handle your cleaning operation's growth easily.

**Ready to deploy? Let me know if you want me to walk through any of these steps in detail!**
