#!/bin/bash
# Grime Guardians Server Update Script
# Run this on your server to pull latest changes

set -e  # Exit on any error

echo "🔄 Updating Grime Guardians on Server..."
echo "========================================"

# Navigate to application directory
cd /opt/grime-guardians-hq

# Stop services
echo "⏸️ Stopping services..."
sudo systemctl stop grime-guardians-ava || true
sudo systemctl stop grime-guardians-dean || true

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment and update dependencies
echo "📚 Updating dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Start services
echo "▶️ Starting services..."
sudo systemctl start grime-guardians-ava
sudo systemctl start grime-guardians-dean

# Check status
echo "✅ Checking service status..."
sudo systemctl status grime-guardians-ava --no-pager
sudo systemctl status grime-guardians-dean --no-pager

echo ""
echo "🎉 Update complete!"
echo "📋 View logs with:"
echo "   sudo journalctl -u grime-guardians-ava -f"
echo "   sudo journalctl -u grime-guardians-dean -f"