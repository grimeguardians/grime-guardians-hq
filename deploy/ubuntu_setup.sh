#!/bin/bash
# Grime Guardians Agentic Suite - Ubuntu Server Setup Script
# For Ubuntu 24.10 x64 on Digital Ocean droplet

set -e  # Exit on any error

echo "🚀 Starting Grime Guardians Agentic Suite setup..."
echo "Server: $(hostname) ($(uname -a))"
echo "Date: $(date)"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor \
    htop \
    tree \
    jq

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /opt
sudo mkdir -p grime-guardians
sudo chown $USER:$USER grime-guardians
cd grime-guardians

# Clone or copy the application
echo "📁 Setting up application directory..."
# In production, you would clone from your git repository
# git clone https://github.com/yourusername/grime-guardians-agent-system.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
# pip install -r requirements.txt

# Core dependencies for the agentic suite
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    openai==1.3.8 \
    anthropic==0.7.8 \
    discord.py==2.3.2 \
    notion-client==2.2.1 \
    httpx==0.25.2 \
    python-dotenv==1.0.0 \
    structlog==23.2.0 \
    sqlalchemy==2.0.23 \
    alembic==1.13.1 \
    asyncpg==0.29.0 \
    psycopg2-binary==2.9.9 \
    redis==5.0.1 \
    gunicorn==21.2.0

# Set up PostgreSQL database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres createuser --createdb --login grime_guardians || true
sudo -u postgres createdb grime_guardians_db --owner=grime_guardians || true
sudo -u postgres psql -c "ALTER USER grime_guardians WITH PASSWORD 'secure_password_change_this';" || true

# Configure Redis
echo "🔴 Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Create application directories
echo "📁 Creating application structure..."
mkdir -p logs
mkdir -p data
mkdir -p config
mkdir -p scripts

# Create systemd service for the application
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/grime-guardians.service > /dev/null <<EOF
[Unit]
Description=Grime Guardians Agentic Suite
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/grime-guardians
Environment=PATH=/opt/grime-guardians/venv/bin
EnvironmentFile=/opt/grime-guardians/.env
ExecStart=/opt/grime-guardians/venv/bin/gunicorn src.api.main:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile /opt/grime-guardians/logs/access.log \
    --error-logfile /opt/grime-guardians/logs/error.log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx reverse proxy
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/grime-guardians > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/grime-guardians /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Create environment file template
echo "🔧 Creating environment configuration..."
tee .env.template > /dev/null <<EOF
# Grime Guardians Agentic Suite Environment Configuration
# Copy this to .env and fill in your actual values

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://grime_guardians:secure_password_change_this@localhost:5432/grime_guardians_db

# AI APIs
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHECKIN_CHANNEL_ID=your_checkin_channel_id_here
DISCORD_OPS_LEAD_ID=your_ops_lead_id_here

# GoHighLevel
HIGHLEVEL_API_KEY=your_ghl_api_key_here
HIGHLEVEL_LOCATION_ID=your_ghl_location_id_here
HIGHLEVEL_OAUTH_ACCESS_TOKEN=your_ghl_oauth_token_here
HIGHLEVEL_OAUTH_REFRESH_TOKEN=your_ghl_refresh_token_here

# Notion
NOTION_SECRET=your_notion_integration_token_here
NOTION_ATTENDANCE_DB_ID=your_notion_database_id_here

# Gmail
GMAIL_CLIENT_ID=your_gmail_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_client_secret_here
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token_here
GMAIL_EMAILS=your_monitored_emails_here

# Webhooks
WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_PORT=3000

# Business Configuration
BUSINESS_NAME=Grime Guardians
BUSINESS_EMAIL=brandonr@grimeguardians.com
TAX_RATE=0.08125
ANNUAL_REVENUE_TARGET=300000

# Feature Flags
ENABLE_PHOTO_VALIDATION=true
ENABLE_3_STRIKE_SYSTEM=true
ENABLE_AUTOMATED_COACHING=true
ENABLE_BONUS_TRACKING=true

# Monitoring
COST_MONITORING_ENABLED=true
LOG_LEVEL=INFO
EOF

echo "⚠️  IMPORTANT: Copy your actual .env file to /opt/grime-guardians/.env"
echo "   Template created at .env.template"

# Create log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/grime-guardians > /dev/null <<EOF
/opt/grime-guardians/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0644 $USER $USER
    postrotate
        systemctl reload grime-guardians
    endscript
}
EOF

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Create deployment script
echo "🚀 Creating deployment script..."
tee scripts/deploy.sh > /dev/null <<'EOF'
#!/bin/bash
# Deployment script for Grime Guardians Agentic Suite

set -e

echo "🚀 Deploying Grime Guardians Agentic Suite..."

# Navigate to application directory
cd /opt/grime-guardians

# Activate virtual environment
source venv/bin/activate

# Pull latest code (uncomment when using git)
# git pull origin main

# Install/update dependencies
pip install --upgrade -r requirements.txt

# Run database migrations (when implemented)
# alembic upgrade head

# Restart services
sudo systemctl restart grime-guardians
sudo systemctl restart nginx

# Check service status
echo "📊 Service Status:"
sudo systemctl status grime-guardians --no-pager -l

echo "✅ Deployment complete!"
echo "🔗 Health check: curl http://localhost/health"
EOF

chmod +x scripts/deploy.sh

# Create monitoring script
echo "📊 Creating monitoring script..."
tee scripts/monitor.sh > /dev/null <<'EOF'
#!/bin/bash
# Monitoring script for Grime Guardians Agentic Suite

echo "📊 Grime Guardians System Status"
echo "=============================="
echo "Date: $(date)"
echo ""

# System resources
echo "💾 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')" 
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
echo ""

# Service status
echo "⚙️  Service Status:"
sudo systemctl is-active grime-guardians && echo "✅ Grime Guardians: Running" || echo "❌ Grime Guardians: Stopped"
sudo systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Stopped"
sudo systemctl is-active postgresql && echo "✅ PostgreSQL: Running" || echo "❌ PostgreSQL: Stopped"
sudo systemctl is-active redis && echo "✅ Redis: Running" || echo "❌ Redis: Stopped"
echo ""

# Application health
echo "🏥 Application Health:"
if curl -s http://localhost/health > /dev/null; then
    echo "✅ HTTP Health Check: Passed"
    curl -s http://localhost/health | jq '.status' 2>/dev/null || echo "API responding"
else
    echo "❌ HTTP Health Check: Failed"
fi
echo ""

# Recent logs
echo "📝 Recent Application Logs (last 10 lines):"
tail -10 /opt/grime-guardians/logs/error.log 2>/dev/null || echo "No error logs found"
echo ""

# Process info
echo "🔍 Process Information:"
ps aux | grep -E '(gunicorn|python)' | grep -v grep || echo "No Python processes found"
EOF

chmod +x scripts/monitor.sh

# Create backup script
echo "💾 Creating backup script..."
tee scripts/backup.sh > /dev/null <<'EOF'
#!/bin/bash
# Backup script for Grime Guardians Agentic Suite

BACKUP_DIR="/opt/grime-guardians/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "💾 Creating backup: $DATE"

# Backup database
echo "📊 Backing up PostgreSQL database..."
pg_dump -h localhost -U grime_guardians grime_guardians_db > "$BACKUP_DIR/database_$DATE.sql"

# Backup application data
echo "📁 Backing up application data..."
tar -czf "$BACKUP_DIR/app_data_$DATE.tar.gz" -C /opt/grime-guardians data/ logs/ .env 2>/dev/null || true

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR"
ls -la $BACKUP_DIR
EOF

chmod +x scripts/backup.sh

# Set up daily backup cron job
echo "⏰ Setting up daily backups..."
(crontab -l 2>/dev/null || true; echo "0 2 * * * /opt/grime-guardians/scripts/backup.sh >> /opt/grime-guardians/logs/backup.log 2>&1") | crontab -

# Create SSL certificate script (for future use)
echo "🔒 Creating SSL setup script..."
tee scripts/setup_ssl.sh > /dev/null <<'EOF'
#!/bin/bash
# SSL Certificate setup script
# Run this after pointing your domain to the server

DOMAIN="your-domain.com"
EMAIL="brandonr@grimeguardians.com"

echo "🔒 Setting up SSL certificate for $DOMAIN"

# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

# Set up auto-renewal
sudo systemctl enable certbot.timer

echo "✅ SSL certificate installed for $DOMAIN"
EOF

chmod +x scripts/setup_ssl.sh

# Final setup
echo "🔧 Final configuration..."

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable grime-guardians

# Note: Don't start the service yet - need .env file first

# Set proper permissions
sudo chown -R $USER:$USER /opt/grime-guardians
chmod -R 755 /opt/grime-guardians
chmod 600 .env.template

echo ""
echo "🎉 ============================================="
echo "🎉 Grime Guardians Agentic Suite Setup Complete!"
echo "🎉 ============================================="
echo ""
echo "📋 Next Steps:"
echo "1. Copy your .env file to /opt/grime-guardians/.env"
echo "2. Update the database connection string in .env"
echo "3. Add all your API keys and secrets to .env"
echo "4. Start the service: sudo systemctl start grime-guardians"
echo "5. Check status: sudo systemctl status grime-guardians"
echo "6. Monitor: /opt/grime-guardians/scripts/monitor.sh"
echo ""
echo "🔗 Important URLs:"
echo "   Health Check: http://$(curl -s ifconfig.me)/health"
echo "   API Docs: http://$(curl -s ifconfig.me)/docs"
echo ""
echo "📁 Important Directories:"
echo "   Application: /opt/grime-guardians"
echo "   Logs: /opt/grime-guardians/logs"
echo "   Scripts: /opt/grime-guardians/scripts"
echo ""
echo "📊 Management Commands:"
echo "   Deploy: /opt/grime-guardians/scripts/deploy.sh"
echo "   Monitor: /opt/grime-guardians/scripts/monitor.sh"
echo "   Backup: /opt/grime-guardians/scripts/backup.sh"
echo ""
echo "⚠️  Remember to:"
echo "   - Configure your domain DNS (if using a domain)"
echo "   - Set up SSL certificate (scripts/setup_ssl.sh)"
echo "   - Test all integrations after starting the service"
echo "   - Monitor the logs for any startup issues"
echo ""
echo "🚀 Ready to deploy the 8-agent Grime Guardians system!"
