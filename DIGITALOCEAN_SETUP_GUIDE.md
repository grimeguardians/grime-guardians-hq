# 🚀 DigitalOcean Server Setup Guide - Grime Guardians

## 📋 **COMPLETE STEP-BY-STEP SETUP (15 minutes)**

### **STEP 1: Create DigitalOcean Account**

**🔗 URL**: https://cloud.digitalocean.com/registrations/new

1. **Sign up** with your email
2. **Verify email** address
3. **Add payment method** (credit card required, but you get $200 free credit)
4. **Complete account setup**

---

### **STEP 2: Create Your Droplet (VPS)**

**🔗 URL**: https://cloud.digitalocean.com/droplets/new

#### **2.1 Choose an Image**
- Select: **Ubuntu 22.04 (LTS) x64**

#### **2.2 Choose Plan**
- **Recommended**: **Basic Plan** → **Regular Intel** → **$6/month**
  - 1 vCPU
  - 1 GB Memory  
  - 25 GB SSD Disk
  - 1000 GB Transfer

#### **2.3 Choose Datacenter Region**
- **Recommended for Minnesota**: **New York 1, 2, or 3**
- Alternative: **Chicago 1** (if available)

#### **2.4 Authentication**
- Select: **SSH Keys** (more secure) OR **Password**
- If SSH Keys: Click **"New SSH Key"** and follow instructions
- If Password: Create a strong password (save it!)

#### **2.5 Finalize Details**
- **Hostname**: `grime-guardians-server`
- **Tags**: `production`, `grime-guardians`
- Click **"Create Droplet"**

**⏱️ Wait Time**: 1-2 minutes for server creation

---

### **STEP 3: Connect to Your Server**

#### **3.1 Get Your Server IP**
**🔗 URL**: https://cloud.digitalocean.com/droplets

- Your new droplet will show with an **IP address** (e.g., `143.198.123.45`)
- **Copy this IP address**

#### **3.2 Connect via SSH**

**On Mac/Linux:**
```bash
# Replace YOUR_SERVER_IP with actual IP
ssh root@YOUR_SERVER_IP

# If using SSH key, it should connect automatically
# If using password, enter the password you created
```

**On Windows:**
- Use **PuTTY** or **Windows Terminal**
- Host: `YOUR_SERVER_IP`
- Username: `root`

---

### **STEP 4: Server Initial Setup**

**Copy and paste these commands one by one:**

#### **4.1 Update System**
```bash
apt update && apt upgrade -y
```

#### **4.2 Install Essential Software**
```bash
apt install -y curl git nginx certbot python3-certbot-nginx ufw
```

#### **4.3 Install Node.js 18 LTS**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
```

#### **4.4 Install PM2 Process Manager**
```bash
npm install -g pm2
```

#### **4.5 Configure Firewall**
```bash
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

---

### **STEP 5: Deploy Grime Guardians**

#### **5.1 First, Push Your Code to GitHub**

**On your local machine (Mac):**
```bash
# In your Grime Guardians folder
cd "/Users/BROB/Desktop/Grime Guardians/Grime Guardians HQ"

# Initialize git if not already done
git init

# Add all files
git add .

# Commit your code
git commit -m "Production ready Grime Guardians system"

# Create GitHub repository at: https://github.com/new
# Name it: grime-guardians-hq
# Set as Public or Private

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/grime-guardians-hq.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### **5.2 Clone to Server**

**Back on your DigitalOcean server:**
```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/grime-guardians-hq.git
cd grime-guardians-hq

# Install dependencies
npm install
```

#### **5.3 Configure Environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit environment file
nano .env
```

**In the nano editor, update these key values:**
```bash
# Production settings
NODE_ENV=production
WEBHOOK_PORT=3000

# Your Discord bot token
DISCORD_BOT_TOKEN=your_actual_discord_token

# Your Notion integration
NOTION_SECRET=your_actual_notion_token
NOTION_ATTENDANCE_DB_ID=your_actual_db_id
NOTION_STRIKES_DB_ID=your_actual_strikes_db_id
NOTION_CLEANER_PROFILES_DB_ID=your_actual_profiles_db_id

# Re-enable High Level for production
DISABLE_HIGHLEVEL=false
HIGHLEVEL_PRIVATE_INTEGRATION=your_actual_highlevel_token

# Your OpenAI key
OPENAI_API_KEY=your_actual_openai_key

# Operations lead Discord ID
OPS_LEAD_DISCORD_ID=1343301440864780291
```

**Save and exit nano**: `Ctrl + X`, then `Y`, then `Enter`

---

### **STEP 6: Set Up Domain (Optional but Recommended)**

#### **6.1 Get a Domain**
**🔗 Recommended Registrars**:
- **Namecheap**: https://www.namecheap.com
- **Cloudflare**: https://www.cloudflare.com/products/registrar/
- **Google Domains**: https://domains.google.com

**Suggested domains**:
- `grimeops.com`
- `grimeguardians.net`
- `cleaningops.io`

#### **6.2 Point Domain to Server**
In your domain registrar:
1. Go to **DNS Management** or **DNS Settings**
2. Add **A Record**:
   - **Name**: `@` (for root domain) 
   - **Value**: `YOUR_SERVER_IP`
   - **TTL**: `300` or `Automatic`
3. Add **A Record** for www:
   - **Name**: `www`
   - **Value**: `YOUR_SERVER_IP`
   - **TTL**: `300` or `Automatic`

**⏱️ Wait Time**: 5-30 minutes for DNS to propagate

---

### **STEP 7: Configure Nginx Web Server**

#### **7.1 Create Nginx Configuration**
```bash
# Create configuration file (replace your-domain.com with actual domain)
nano /etc/nginx/sites-available/grime-guardians
```

**Paste this configuration** (replace `your-domain.com` with your actual domain):
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /health {
        proxy_pass http://localhost:3000/health;
        access_log off;
    }
}
```

#### **7.2 Enable the Site**
```bash
# Enable site
ln -s /etc/nginx/sites-available/grime-guardians /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

#### **7.3 Set Up SSL Certificate (Free)**
```bash
# Get free SSL certificate (replace with your domain)
certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to share email with EFF
# - Select option 2 (redirect HTTP to HTTPS)
```

---

### **STEP 8: Start Your Application**

#### **8.1 Create PM2 Configuration**
```bash
# Create PM2 ecosystem file
nano ecosystem.config.js
```

**Paste this configuration:**
```javascript
module.exports = {
  apps: [{
    name: 'grime-guardians',
    script: 'src/index.js',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
```

#### **8.2 Start the Application**
```bash
# Create logs directory
mkdir -p logs

# Start application with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Set PM2 to auto-start on server reboot
pm2 startup

# The command above will show you a command to run - run it!
# It will look like: sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root
```

---

### **STEP 9: Verify Everything is Working**

#### **9.1 Check Application Status**
```bash
# Check PM2 processes
pm2 list

# Check application logs
pm2 logs grime-guardians --lines 20

# Check if port 3000 is listening
netstat -tulpn | grep :3000
```

#### **9.2 Test Your Website**
- **HTTP**: `http://your-domain.com/health`
- **HTTPS**: `https://your-domain.com/health`

**You should see**: `{"status":"healthy","timestamp":"...","database":"Notion",...}`

#### **9.3 Test High Level Webhook**
Update your High Level webhook URL to:
```
https://your-domain.com/webhook/highlevel
```

---

### **STEP 10: Configure High Level Integration**

#### **10.1 Log into High Level**
**🔗 URL**: https://app.gohighlevel.com

#### **10.2 Update Webhook Settings**
1. Go to **Settings** → **Integrations** → **Webhooks**
2. **Add New Webhook** or **Edit Existing**
3. **Webhook URL**: `https://your-domain.com/webhook/highlevel`
4. **Events**: Select `Appointment Created`, `Appointment Updated`
5. **Secret**: Use the same value as `WEBHOOK_SECRET` in your .env

#### **10.3 Test High Level Connection**
```bash
# SSH into your server and test
cd grime-guardians-hq

# Test High Level API
node -e "
const { getAllJobs } = require('./src/utils/highlevel');
getAllJobs().then(jobs => {
  console.log('✅ High Level API working! Jobs found:', jobs.length);
}).catch(err => {
  console.error('❌ High Level API Error:', err.message);
});
"
```

---

## 🎉 **CONGRATULATIONS! YOUR SYSTEM IS LIVE!**

### **📱 What You Can Do Now:**
- **Monitor**: `https://your-domain.com/health`
- **Dashboard**: `https://your-domain.com/dashboard`
- **Discord**: Your bot is now running 24/7
- **High Level**: Webhooks are being processed
- **Notion**: Data is being logged automatically

### **📊 Monitoring Commands:**
```bash
# Check system status
pm2 monit

# View logs
pm2 logs grime-guardians

# Restart if needed
pm2 restart grime-guardians

# Check server resources
htop
```

### **💰 Monthly Cost:**
- **Server**: $6/month
- **Domain**: ~$1/month  
- **Total**: ~$7/month for fully automated cleaning operations

### **🚀 Your Grime Guardians system is now running 24/7!**

All 8 agents are operational:
- ✅ **Ava** - Master orchestration
- ✅ **Keith** - Attendance tracking  
- ✅ **Maya** - Motivational coaching
- ✅ **Zara** - Bonus calculations
- ✅ **Nikolai** - Compliance monitoring
- ✅ **Iris** - Dynamic pricing
- ✅ **Jules** - Analytics and reporting
- ✅ **Schedule Manager** - Job coordination

---

## 🆘 **Need Help?**

### **Common Issues:**
- **Can't connect via SSH**: Check firewall settings, verify IP
- **Domain not working**: Wait for DNS propagation (up to 24 hours)
- **SSL certificate fails**: Ensure domain points to server first
- **Application won't start**: Check `pm2 logs` for error details

### **Support Resources:**
- **DigitalOcean Docs**: https://docs.digitalocean.com
- **PM2 Documentation**: https://pm2.keymetrics.io/docs/
- **Nginx Documentation**: https://nginx.org/en/docs/

**Your production-grade cleaning operations system is now live! 🎊**
