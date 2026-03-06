#!/bin/bash
# Grime Guardians Agentic Suite - Ubuntu Server Setup Script
# Run this script on your fresh Ubuntu 22.04 Digital Ocean droplet

set -e  # Exit on any error

echo "🚀 GRIME GUARDIANS AGENTIC SUITE - UBUNTU SETUP"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting Ubuntu server setup for Grime Guardians..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
print_status "Installing essential packages..."
apt install -y \
    curl \
    wget \
    git \
    nginx \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    supervisor \
    htop \
    nano \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx \
    redis-server \
    build-essential \
    libpq-dev

print_success "Essential packages installed"

# Configure firewall
print_status "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 80
ufw allow 443
ufw --force enable

print_success "Firewall configured"

# Create application directory and user
print_status "Creating application user and directory..."
if ! id "ava" &>/dev/null; then
    useradd -r -s /bin/bash -d /opt/grime-guardians ava
fi

mkdir -p /opt/grime-guardians
mkdir -p /opt/grime-guardians/logs
mkdir -p /opt/backups/grime-guardians

chown -R ava:ava /opt/grime-guardians
chown -R ava:ava /opt/backups/grime-guardians

print_success "Application user 'ava' created"

# Setup PostgreSQL
print_status "Configuring PostgreSQL..."

# Generate a random password for the database user
DB_PASSWORD=$(openssl rand -base64 32)

sudo -u postgres psql <<EOF
CREATE DATABASE grime_guardians;
CREATE USER ava_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE grime_guardians TO ava_user;
ALTER USER ava_user CREATEDB;
\q
EOF

# Configure PostgreSQL for local connections
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf

# Add authentication for the ava_user
echo "local   grime_guardians   ava_user   md5" >> /etc/postgresql/*/main/pg_hba.conf

systemctl restart postgresql
systemctl enable postgresql

print_success "PostgreSQL configured with database 'grime_guardians'"

# Setup Redis
print_status "Configuring Redis..."
systemctl start redis-server
systemctl enable redis-server

print_success "Redis configured and started"

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
sudo -u ava bash <<EOF
cd /opt/grime-guardians
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install wheel setuptools
EOF

print_success "Python virtual environment created"

# Configure Nginx (basic setup)
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/grime-guardians <<'EOF'
server {
    listen 80;
    server_name _;

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

    # Webhooks
    location /webhooks/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Default response
    location / {
        return 200 "Grime Guardians Agentic Suite - Production Ready";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/grime-guardians /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

print_success "Nginx configured"

# Create systemd service templates
print_status "Creating systemd service templates..."

# Discord bot service
cat > /etc/systemd/system/grime-guardians-discord.service <<EOF
[Unit]
Description=Grime Guardians Discord Bot
After=network.target postgresql.service redis.service
Requires=postgresql.service

[Service]
Type=simple
User=ava
Group=ava
WorkingDirectory=/opt/grime-guardians
Environment=PATH=/opt/grime-guardians/venv/bin
ExecStart=/opt/grime-guardians/venv/bin/python3 live_discord_test.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# FastAPI service
cat > /etc/systemd/system/grime-guardians-api.service <<EOF
[Unit]
Description=Grime Guardians FastAPI
After=network.target postgresql.service redis.service
Requires=postgresql.service

[Service]
Type=simple
User=ava
Group=ava
WorkingDirectory=/opt/grime-guardians
Environment=PATH=/opt/grime-guardians/venv/bin
ExecStart=/opt/grime-guardians/venv/bin/gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --access-logfile /opt/grime-guardians/logs/access.log --error-logfile /opt/grime-guardians/logs/error.log
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

print_success "Systemd services created"

# Create log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/grime-guardians <<EOF
/opt/grime-guardians/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ava ava
    postrotate
        systemctl reload grime-guardians-discord grime-guardians-api 2>/dev/null || true
    endscript
}
EOF

print_success "Log rotation configured"

# Create backup script
print_status "Creating backup script..."
cat > /opt/grime-guardians/backup.sh <<EOF
#!/bin/bash
# Grime Guardians Backup Script

DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/grime-guardians"

# Database backup
sudo -u postgres pg_dump grime_guardians > \$BACKUP_DIR/db_backup_\$DATE.sql

# Environment backup (if exists)
if [ -f /opt/grime-guardians/.env ]; then
    cp /opt/grime-guardians/.env \$BACKUP_DIR/env_backup_\$DATE.env
fi

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.env" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x /opt/grime-guardians/backup.sh
chown ava:ava /opt/grime-guardians/backup.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/grime-guardians/backup.sh") | crontab -

print_success "Backup script created and scheduled"

# Create environment template
print_status "Creating environment template..."
cat > /opt/grime-guardians/.env.template <<EOF
# Environment
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_SECRET_KEY_32_CHARS_MIN

# Database
DATABASE_URL=postgresql+asyncpg://ava_user:$DB_PASSWORD@localhost:5432/grime_guardians

# Discord Bot Token (UPDATE THIS)
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE

# OpenAI API Key (UPDATE THIS)
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE

# GoHighLevel API Key (UPDATE THIS)
GOHIGHLEVEL_API_KEY=YOUR_GOHIGHLEVEL_API_KEY_HERE

# Notion Token (UPDATE THIS)
NOTION_SECRET=YOUR_NOTION_TOKEN_HERE
NOTION_ATTENDANCE_DB_ID=YOUR_NOTION_DATABASE_ID_HERE

# Gmail Configuration (UPDATE THESE)
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
ALLOWED_HOSTS=["$(curl -s ifconfig.me)", "localhost"]
CORS_ORIGINS=["https://yourdomain.com"]
EOF

chown ava:ava /opt/grime-guardians/.env.template

print_success "Environment template created"

# Create deployment info file
cat > /opt/grime-guardians/deployment-info.txt <<EOF
Grime Guardians Agentic Suite - Deployment Information
=====================================================

Server IP: $(curl -s ifconfig.me)
Database Password: $DB_PASSWORD
Deployment Date: $(date)

NEXT STEPS:
1. Upload your application code to /opt/grime-guardians/
2. Copy .env.template to .env and update with your credentials
3. Install Python dependencies: pip install -r requirements.txt
4. Initialize database: python3 -c "import asyncio; from src.config.database import init_database; asyncio.run(init_database())"
5. Start services: systemctl start grime-guardians-discord grime-guardians-api
6. Test Discord bot and API endpoints

USEFUL COMMANDS:
- Check service status: systemctl status grime-guardians-discord grime-guardians-api
- View logs: journalctl -u grime-guardians-discord -f
- Restart services: systemctl restart grime-guardians-discord grime-guardians-api
- Run backup: /opt/grime-guardians/backup.sh
EOF

print_success "Server setup completed!"
print_warning "Please save the database password: $DB_PASSWORD"
print_status "Next: Upload your application code and configure environment variables"
print_status "See /opt/grime-guardians/deployment-info.txt for details"

echo ""
echo "🎉 Ubuntu server is ready for Grime Guardians Agentic Suite!"
echo "📋 Server IP: $(curl -s ifconfig.me)"
echo "🔐 Database Password: $DB_PASSWORD"
echo ""
echo "Next steps:"
echo "1. Upload your application code"
echo "2. Configure environment variables"  
echo "3. Install dependencies and start services"