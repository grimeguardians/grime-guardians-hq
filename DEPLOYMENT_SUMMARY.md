# 🚀 GRIME GUARDIANS UBUNTU DEPLOYMENT - COMPLETE GUIDE

## 📋 **QUICK DEPLOYMENT OVERVIEW**

Your Grime Guardians Agentic Suite is **100% ready for Ubuntu deployment**! This will resolve the macOS SSL issues and get your enhanced Discord bot online immediately.

---

## 🎯 **3-STEP DEPLOYMENT PROCESS**

### **STEP 1: CREATE DIGITAL OCEAN DROPLET**
1. **Go to:** [DigitalOcean Dashboard](https://cloud.digitalocean.com)
2. **Create Droplet:**
   - **OS:** Ubuntu 22.04 LTS
   - **Plan:** Basic $12/month (2GB RAM, 1 vCPU, 50GB SSD)
   - **Region:** Closest to your location
   - **Authentication:** SSH Key or Password
   - **Hostname:** `grime-guardians-production`

### **STEP 2: SETUP UBUNTU SERVER**
Run the automated setup script on your new droplet:

```bash
# SSH into your droplet (replace with your IP)
ssh root@YOUR_DROPLET_IP

# Download and run server setup script
curl -sSL https://raw.githubusercontent.com/your-repo/setup_server.sh | bash

# OR manually upload and run the script
# Upload deploy/setup_server.sh to your server
chmod +x setup_server.sh
sudo ./setup_server.sh
```

### **STEP 3: DEPLOY YOUR APPLICATION**
From your Mac, transfer files and deploy:

```bash
# From your Mac terminal
cd "/Users/BROB/Desktop/Grime Guardians/GG Agentic Suite/grime-guardians-agentic-suite"

# Transfer files to server (replace with your IP)
./deploy/transfer_files.sh YOUR_DROPLET_IP

# SSH into server and deploy
ssh root@YOUR_DROPLET_IP
sudo su - ava
cd /opt/grime-guardians
./deploy/deploy_app.sh
```

---

## 🔧 **MANUAL DEPLOYMENT STEPS**

If you prefer manual deployment, follow these steps:

### **1. Create and Setup Droplet**
```bash
# After creating Ubuntu 22.04 droplet, SSH in:
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y curl wget git nginx postgresql postgresql-contrib python3 python3-pip python3-venv supervisor htop nano ufw

# Create application user
useradd -r -s /bin/bash -d /opt/grime-guardians ava
mkdir -p /opt/grime-guardians
chown -R ava:ava /opt/grime-guardians
```

### **2. Setup PostgreSQL Database**
```bash
# Configure PostgreSQL
sudo -u postgres psql
CREATE DATABASE grime_guardians;
CREATE USER ava_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE grime_guardians TO ava_user;
\q

# Restart PostgreSQL
systemctl restart postgresql
```

### **3. Transfer Application Files**
```bash
# From your Mac, copy files to server
scp -r "/Users/BROB/Desktop/Grime Guardians/GG Agentic Suite/grime-guardians-agentic-suite/"* root@YOUR_DROPLET_IP:/opt/grime-guardians/

# Set permissions on server
ssh root@YOUR_DROPLET_IP
chown -R ava:ava /opt/grime-guardians
```

### **4. Setup Python Environment**
```bash
# Switch to ava user
sudo su - ava
cd /opt/grime-guardians

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn psycopg2-binary
```

### **5. Configure Environment**
```bash
# Create production .env file
nano .env

# Add your production environment variables:
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_secure_secret_key_here
DATABASE_URL=postgresql+asyncpg://ava_user:your_password@localhost:5432/grime_guardians
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
GOHIGHLEVEL_API_KEY=YOUR_GHL_API_KEY_HERE
NOTION_SECRET=YOUR_NOTION_SECRET_HERE
GMAIL_CLIENT_ID=YOUR_GMAIL_CLIENT_ID_HERE
GMAIL_CLIENT_SECRET=YOUR_GMAIL_CLIENT_SECRET_HERE
GMAIL_REFRESH_TOKEN=YOUR_GMAIL_REFRESH_TOKEN_HERE

# Set secure permissions
chmod 600 .env
```

### **6. Initialize Database**
```bash
# Initialize database tables
python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from src.config.database import init_database
asyncio.run(init_database())
print('Database initialized!')
"
```

### **7. Create System Services**
```bash
# Create Discord bot service
sudo nano /etc/systemd/system/grime-guardians-discord.service

# Add service configuration (see deployment guide for full config)

# Create FastAPI service  
sudo nano /etc/systemd/system/grime-guardians-api.service

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable grime-guardians-discord grime-guardians-api
sudo systemctl start grime-guardians-discord grime-guardians-api
```

### **8. Configure Nginx**
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/grime-guardians

# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/grime-guardians /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## ✅ **VERIFICATION CHECKLIST**

After deployment, verify these are working:

### **Discord Bot Verification:**
- [ ] Bot appears **online** in Discord server
- [ ] Test message: `"I need a quote for a 3 bedroom house"` → **Dean CMO responds**
- [ ] Test message: `"Customer complaint about service"` → **Emma CXO responds**
- [ ] Test message: `"URGENT: emergency situation"` → **Brandon CEO responds**
- [ ] Test command: `!ava status` → **Status embed displays**
- [ ] **Approval workflow:** React with ✅ → **Approval confirmation**

### **API Verification:**
- [ ] Health check: `curl http://YOUR_IP/health` → **Returns success**
- [ ] API status: `curl http://YOUR_IP/api/v1/agents/status` → **Returns agent info**

### **System Verification:**
- [ ] **Discord service running:** `systemctl status grime-guardians-discord`
- [ ] **API service running:** `systemctl status grime-guardians-api`
- [ ] **Database connected:** No connection errors in logs
- [ ] **All integrations working:** GoHighLevel, Notion, Gmail accessible

---

## 📊 **EXPECTED RESULTS**

Once deployed successfully, you'll see:

### **🤖 Enhanced Discord Bot Online**
- **Dean (CMO)** provides instant quotes with pricing and sales copy
- **Emma (CXO)** handles complaints with service recovery options  
- **Brandon (CEO)** manages crises with executive intervention
- **Approval workflows** activate with Discord reactions
- **Business context** preserved from your original system

### **🔗 Working Integrations**
- **GoHighLevel CRM** updates and webhooks
- **Notion database** logging and tracking
- **Gmail monitoring** and response workflows
- **FastAPI backend** serving all endpoints

### **📈 Production Ready**
- **SSL certificates** working (no macOS issues)
- **Process management** with automatic restarts
- **Monitoring and logging** for all services
- **Backup system** for data protection
- **Scalable architecture** for growth to $300K revenue

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues and Solutions:**

**Discord Bot Won't Connect:**
```bash
# Check service status
sudo systemctl status grime-guardians-discord

# View logs
sudo journalctl -u grime-guardians-discord -n 50

# Common fixes:
# 1. Verify Discord token in .env file
# 2. Check Message Content Intent is enabled in Discord Developer Portal
# 3. Ensure bot is invited to server with proper permissions
```

**API Not Responding:**
```bash
# Check API service
sudo systemctl status grime-guardians-api

# Test direct connection
curl localhost:8000/health

# Restart if needed
sudo systemctl restart grime-guardians-api
```

**Database Connection Issues:**
```bash
# Test database connection
sudo -u ava psql -h localhost -U ava_user -d grime_guardians

# Check PostgreSQL status
sudo systemctl status postgresql

# Verify .env database URL is correct
```

---

## 🎉 **DEPLOYMENT SUCCESS!**

When your deployment is complete, you'll have:

✅ **Production-ready Ubuntu server** with all services running  
✅ **Enhanced Discord bot** with AI agents online and responding  
✅ **FastAPI backend** serving all endpoints and integrations  
✅ **Database persistence** with PostgreSQL  
✅ **Monitoring and logging** for production operations  
✅ **Backup system** for data protection  
✅ **Scalable architecture** ready for business growth

**Your Grime Guardians Agentic Suite is now live and ready to revolutionize your cleaning business operations!** 🚀

---

## 📞 **SUPPORT COMMANDS**

Once deployed, use these commands for ongoing management:

```bash
# Check system status
./check_status.sh

# View service logs
sudo journalctl -u grime-guardians-discord -f
sudo journalctl -u grime-guardians-api -f

# Restart services
sudo systemctl restart grime-guardians-discord grime-guardians-api

# Run backup
./backup.sh

# Update application (after code changes)
git pull && sudo systemctl restart grime-guardians-discord grime-guardians-api
```

**Ready to deploy? Let's get your enhanced AI cleaning service live!** 🎯