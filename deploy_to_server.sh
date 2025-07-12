#!/bin/bash
# Grime Guardians Server Deployment Script
# Run this on your Digital Ocean server (64.225.27.176)

set -e  # Exit on any error

echo "🚀 Starting Grime Guardians Deployment..."
echo "================================================"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv git nginx ufw

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/grime-guardians-hq
sudo chown $USER:$USER /opt/grime-guardians-hq
cd /opt/grime-guardians-hq

# Clone the repository
echo "📥 Cloning repository..."
git clone https://github.com/grimeguardians/grime-guardians-hq.git .

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file template (you'll need to fill this with your actual values)
echo "🔐 Creating environment configuration..."
cat > .env << 'EOF'
# GoHighLevel Configuration
HIGHLEVEL_LOCATION_ID=g3gJNdESNw9SrV7NpjJl
HIGHLEVEL_API_KEY=your_api_key_here
HIGHLEVEL_API_V2_TOKEN=your_pit_token_here
HIGHLEVEL_OAUTH_ACCESS_TOKEN=your_oauth_token_here
HIGHLEVEL_OAUTH_REFRESH_TOKEN=your_refresh_token_here

# Discord Configuration
DISCORD_BOT_TOKEN_AVA=your_ava_bot_token_here
DISCORD_BOT_TOKEN_DEAN=your_dean_bot_token_here
DISCORD_CHECKIN_CHANNEL_ID=your_channel_id_here
DISCORD_OPS_LEAD_ID=your_ops_lead_id_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key_here

# Other Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Create systemd service for Ava
echo "⚙️ Creating Ava systemd service..."
sudo tee /etc/systemd/system/grime-guardians-ava.service > /dev/null << EOF
[Unit]
Description=Grime Guardians Ava Discord Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/grime-guardians-hq
Environment=PATH=/opt/grime-guardians-hq/venv/bin
ExecStart=/opt/grime-guardians-hq/venv/bin/python enhanced_discord_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Dean (if you have a separate Dean bot)
echo "⚙️ Creating Dean systemd service..."
sudo tee /etc/systemd/system/grime-guardians-dean.service > /dev/null << EOF
[Unit]
Description=Grime Guardians Dean Discord Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/grime-guardians-hq
Environment=PATH=/opt/grime-guardians-hq/venv/bin
ExecStart=/opt/grime-guardians-hq/venv/bin/python dean_discord_runner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

# Reload systemd and enable services
echo "🔄 Setting up systemd services..."
sudo systemctl daemon-reload
sudo systemctl enable grime-guardians-ava
sudo systemctl enable grime-guardians-dean

echo ""
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "🔧 NEXT STEPS:"
echo "1. Edit /opt/grime-guardians-hq/.env with your actual API keys and tokens"
echo "2. Test the application:"
echo "   cd /opt/grime-guardians-hq"
echo "   source venv/bin/activate"
echo "   python test_ava_appointments_simple.py"
echo ""
echo "3. Start the services:"
echo "   sudo systemctl start grime-guardians-ava"
echo "   sudo systemctl start grime-guardians-dean"
echo ""
echo "4. Check service status:"
echo "   sudo systemctl status grime-guardians-ava"
echo "   sudo systemctl status grime-guardians-dean"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u grime-guardians-ava -f"
echo "   sudo journalctl -u grime-guardians-dean -f"
echo ""
echo "📂 Application deployed to: /opt/grime-guardians-hq"
echo "🌐 Your server IP: 64.225.27.176"
echo ""
echo "🎉 Ready to test Ava's appointment scheduling!"