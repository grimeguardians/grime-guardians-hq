# 🚀 Ubuntu Digital Ocean Deployment Guide
## Grime Guardians Agentic Suite Production Deployment

### 📋 **DEPLOYMENT OVERVIEW**

This guide will deploy your enhanced Python agentic suite to Ubuntu Digital Ocean, providing:
- ✅ **Production-ready Discord bot** with AI agents
- ✅ **PostgreSQL database** for data persistence
- ✅ **FastAPI backend** with all integrations
- ✅ **SSL certificate resolution** (no macOS issues)
- ✅ **Process management** with PM2
- ✅ **Monitoring and logging** for production operations

---

## 🖥️ **STEP 1: DIGITAL OCEAN DROPLET SETUP**

### **Create Ubuntu Droplet:**
1. **Go to:** [DigitalOcean Dashboard](https://cloud.digitalocean.com)
2. **Click:** "Create" → "Droplets"
3. **Choose:**
   - **OS:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($12/month recommended for production)
   - **CPU:** Regular with SSD (2 GB RAM, 1 vCPU, 50 GB SSD)
   - **Region:** Closest to your location
   - **Authentication:** SSH Key (recommended) or Password
4. **Hostname:** `grime-guardians-production`
5. **Click:** "Create Droplet"

### **Initial Server Access:**
```bash
# SSH into your new server (replace with your droplet IP)
ssh root@YOUR_DROPLET_IP

# Update system packages
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git nginx postgresql postgresql-contrib python3 python3-pip python3-venv supervisor htop nano
```

---

## 🐍 **STEP 2: PYTHON ENVIRONMENT SETUP**

```bash
# Create application directory
mkdir -p /opt/grime-guardians
cd /opt/grime-guardians

# Create dedicated user for security
useradd -r -s /bin/bash -d /opt/grime-guardians ava
chown -R ava:ava /opt/grime-guardians

# Switch to application user
su - ava
cd /opt/grime-guardians

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

---

## 📁 **STEP 3: CODE DEPLOYMENT**

### **Option A: Git Clone (if you have a repository)**
```bash
# Clone your repository
git clone YOUR_REPOSITORY_URL .
```

### **Option B: Direct File Transfer**
From your Mac, transfer files to the server:

```bash
# From your local machine
cd "/Users/BROB/Desktop/Grime Guardians/GG Agentic Suite/grime-guardians-agentic-suite"

# Copy files to server (replace with your droplet IP)
scp -r . root@YOUR_DROPLET_IP:/opt/grime-guardians/

# Set permissions on server
ssh root@YOUR_DROPLET_IP
chown -R ava:ava /opt/grime-guardians
```

### **Install Python Dependencies:**
```bash
# As ava user with venv activated
cd /opt/grime-guardians
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Install additional production packages
pip install gunicorn supervisor psycopg2-binary
```

---

## 🗄️ **STEP 4: POSTGRESQL DATABASE SETUP**

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE grime_guardians;
CREATE USER ava_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE grime_guardians TO ava_user;
ALTER USER ava_user CREATEDB;
\q

# Configure PostgreSQL for network access
sudo nano /etc/postgresql/14/main/postgresql.conf
# Change: listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: local   grime_guardians   ava_user   md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## ⚙️ **STEP 5: ENVIRONMENT CONFIGURATION**

```bash
# As ava user, create production .env file
cd /opt/grime-guardians
nano .env
```

**Production .env file content:**
```bash
# Environment
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_very_secure_secret_key_here_32_chars_min

# Database (UPDATE PASSWORD)
DATABASE_URL=postgresql+asyncpg://ava_user:your_secure_password_here@localhost:5432/grime_guardians

# Discord Bot (your existing token)
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE

# OpenAI API (your existing key)
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE

# GoHighLevel (your existing credentials)
GOHIGHLEVEL_API_KEY=YOUR_GHL_API_KEY_HERE

# Notion (your existing token)
NOTION_SECRET=YOUR_NOTION_SECRET_HERE
NOTION_ATTENDANCE_DB_ID=20c8b5b8ae5180db99bae5beabe35612

# Gmail (your existing credentials)
GMAIL_CLIENT_ID=YOUR_GMAIL_CLIENT_ID_HERE
GMAIL_CLIENT_SECRET=YOUR_GMAIL_CLIENT_SECRET_HERE
GMAIL_REDIRECT_URI=http://localhost:3000/oauth/callback
GMAIL_REFRESH_TOKEN=YOUR_GMAIL_REFRESH_TOKEN_HERE

# Production Settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO

# Security
ALLOWED_HOSTS=["YOUR_DROPLET_IP", "your-domain.com"]
CORS_ORIGINS=["https://your-domain.com"]
```

**Set secure permissions:**
```bash
chmod 600 .env
```

---

## 🚀 **STEP 6: DATABASE INITIALIZATION**

```bash
# As ava user with venv activated
cd /opt/grime-guardians
source venv/bin/activate

# Initialize database tables
python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from src.config.database import init_database

async def setup():
    await init_database()
    print('Database initialized successfully!')

asyncio.run(setup())
"
```

---

## 📱 **STEP 7: DISCORD BOT SERVICE SETUP**

Create Discord bot service:
```bash
sudo nano /etc/systemd/system/grime-guardians-discord.service
```

**Service file content:**
```ini
[Unit]
Description=Grime Guardians Discord Bot
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=ava
Group=ava
WorkingDirectory=/opt/grime-guardians
Environment=PATH=/opt/grime-guardians/venv/bin
ExecStart=/opt/grime-guardians/venv/bin/python3 -m src.integrations.discord_integration
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start Discord bot:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable grime-guardians-discord
sudo systemctl start grime-guardians-discord

# Check status
sudo systemctl status grime-guardians-discord
```

---

## 🌐 **STEP 8: FASTAPI WEB SERVICE SETUP**

Create FastAPI service:
```bash
sudo nano /etc/systemd/system/grime-guardians-api.service
```

**Service file content:**
```ini
[Unit]
Description=Grime Guardians FastAPI
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=ava
Group=ava
WorkingDirectory=/opt/grime-guardians
Environment=PATH=/opt/grime-guardians/venv/bin
ExecStart=/opt/grime-guardians/venv/bin/gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start API service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable grime-guardians-api
sudo systemctl start grime-guardians-api

# Check status
sudo systemctl status grime-guardians-api
```

---

## 🔧 **STEP 9: NGINX REVERSE PROXY SETUP**

Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/grime-guardians
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP your-domain.com;

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/grime-guardians/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Default response
    location / {
        return 200 "Grime Guardians Agentic Suite - Production Ready";
        add_header Content-Type text/plain;
    }
}
```

**Enable Nginx site:**
```bash
sudo ln -s /etc/nginx/sites-available/grime-guardians /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔍 **STEP 10: TESTING AND VERIFICATION**

### **Test Discord Bot:**
```bash
# Check Discord bot status
sudo systemctl status grime-guardians-discord

# View Discord bot logs
sudo journalctl -u grime-guardians-discord -f

# Test in Discord - send these messages:
# "I need a quote for a 3 bedroom house"
# "Customer complaint about service"
# "!ava status"
```

### **Test API:**
```bash
# Test health endpoint
curl http://YOUR_DROPLET_IP/health

# Test API endpoint
curl http://YOUR_DROPLET_IP/api/v1/agents/status
```

### **Monitor System:**
```bash
# Check all services
sudo systemctl status grime-guardians-discord grime-guardians-api nginx postgresql

# Monitor logs
sudo journalctl -f

# Check resource usage
htop
```

---

## 📊 **STEP 11: MONITORING AND MAINTENANCE**

### **Log Management:**
```bash
# Create log rotation for application logs
sudo nano /etc/logrotate.d/grime-guardians

# Content:
/opt/grime-guardians/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 ava ava
    postrotate
        systemctl reload grime-guardians-discord grime-guardians-api
    endscript
}
```

### **Backup Script:**
```bash
sudo nano /opt/grime-guardians/backup.sh
```

**Backup script content:**
```bash
#!/bin/bash
# Grime Guardians Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/grime-guardians"
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump grime_guardians > $BACKUP_DIR/db_backup_$DATE.sql

# Environment backup
cp /opt/grime-guardians/.env $BACKUP_DIR/env_backup_$DATE.env

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.env" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Make executable and schedule:**
```bash
chmod +x /opt/grime-guardians/backup.sh

# Add to crontab for daily backups
sudo crontab -e
# Add: 0 2 * * * /opt/grime-guardians/backup.sh
```

---

## ✅ **DEPLOYMENT COMPLETION CHECKLIST**

- [ ] **Ubuntu droplet created and configured**
- [ ] **Python environment with all dependencies installed**
- [ ] **PostgreSQL database setup and initialized**
- [ ] **Environment variables configured for production**
- [ ] **Discord bot service running and connected**
- [ ] **FastAPI service running on port 8000**
- [ ] **Nginx reverse proxy configured**
- [ ] **All services enabled for auto-start**
- [ ] **Discord bot responding to test messages**
- [ ] **API endpoints accessible**
- [ ] **Monitoring and logging configured**
- [ ] **Backup system in place**

---

## 🎉 **SUCCESS INDICATORS**

When deployment is complete, you should see:

1. **Discord Bot Online:** Your enhanced Ava bot appears online in Discord
2. **AI Agent Responses:** Test messages trigger Dean, Emma, Brandon responses
3. **API Accessible:** Health check returns success at `http://YOUR_IP/health`
4. **Database Connected:** No database connection errors in logs
5. **Integrations Working:** GoHighLevel, Notion, Gmail integrations functional

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues:**

**Discord Bot Won't Connect:**
```bash
# Check token and intents
sudo journalctl -u grime-guardians-discord -n 50

# Verify token in .env file
sudo -u ava cat /opt/grime-guardians/.env | grep DISCORD
```

**Database Connection Issues:**
```bash
# Test database connection
sudo -u ava psql -h localhost -U ava_user -d grime_guardians

# Check PostgreSQL status
sudo systemctl status postgresql
```

**API Not Responding:**
```bash
# Check FastAPI logs
sudo journalctl -u grime-guardians-api -n 50

# Test direct connection
curl localhost:8000/health
```

---

## 🎯 **NEXT STEPS AFTER DEPLOYMENT**

1. **Domain Setup:** Point your domain to the droplet IP
2. **SSL Certificate:** Install Let's Encrypt SSL certificate
3. **Monitoring:** Set up Uptime monitoring and alerts
4. **Scaling:** Configure load balancing for high traffic
5. **Webhooks:** Update GoHighLevel webhooks to point to new server

Your Grime Guardians Agentic Suite is now ready for production use! 🚀