#!/bin/bash
# Grime Guardians Agentic Suite - Application Deployment Script
# Run this script AFTER setup_server.sh to deploy your application

set -e  # Exit on any error

echo "🚀 GRIME GUARDIANS - APPLICATION DEPLOYMENT"
echo "==========================================="

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

# Check if running as ava user
if [[ "$USER" != "ava" ]]; then
   print_error "This script must be run as the 'ava' user"
   print_status "Switch to ava user: sudo su - ava"
   exit 1
fi

# Check if we're in the right directory
if [[ ! -d "/opt/grime-guardians" ]]; then
    print_error "Directory /opt/grime-guardians not found"
    print_status "Please run setup_server.sh first"
    exit 1
fi

cd /opt/grime-guardians

print_status "Starting application deployment..."

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_error ".env file not found"
    print_status "Please copy .env.template to .env and configure your credentials"
    print_status "cp .env.template .env && nano .env"
    exit 1
fi

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Install/upgrade Python dependencies
print_status "Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn uvicorn psycopg2-binary
    print_success "Dependencies installed"
else
    print_warning "requirements.txt not found, installing basic dependencies..."
    pip install --upgrade pip
    pip install \
        fastapi \
        uvicorn \
        gunicorn \
        discord.py \
        openai \
        asyncpg \
        psycopg2-binary \
        sqlalchemy \
        pydantic \
        python-dotenv \
        aiohttp \
        requests \
        redis \
        notion-client \
        google-api-python-client \
        google-auth-httplib2 \
        google-auth-oauthlib
    print_success "Basic dependencies installed"
fi

# Test database connection
print_status "Testing database connection..."
python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')

async def test_db():
    try:
        from src.config.database import get_db_session
        async with get_db_session() as session:
            print('✅ Database connection successful')
            return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

result = asyncio.run(test_db())
sys.exit(0 if result else 1)
" || {
    print_error "Database connection failed"
    print_status "Please check your .env file database configuration"
    exit 1
}

# Initialize database tables
print_status "Initializing database tables..."
python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')

async def init_db():
    try:
        from src.config.database import init_database
        await init_database()
        print('✅ Database tables initialized')
        return True
    except Exception as e:
        print(f'❌ Database initialization failed: {e}')
        return False

result = asyncio.run(init_db())
sys.exit(0 if result else 1)
" || {
    print_warning "Database initialization failed (tables may already exist)"
}

# Test Discord bot token
print_status "Testing Discord bot configuration..."
python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    from src.config.settings import get_settings
    settings = get_settings()
    
    if not settings.discord_bot_token or len(settings.discord_bot_token) < 50:
        print('❌ Discord bot token not configured or invalid')
        sys.exit(1)
    
    print(f'✅ Discord bot token configured: {settings.discord_bot_token[:20]}...')
    
    if not settings.openai_api_key or not settings.openai_api_key.startswith('sk-'):
        print('❌ OpenAI API key not configured or invalid')
        sys.exit(1)
    
    print(f'✅ OpenAI API key configured: {settings.openai_api_key[:20]}...')
    
    print('✅ Basic configuration validated')
    
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    sys.exit(1)
" || {
    print_error "Configuration validation failed"
    print_status "Please check your .env file configuration"
    exit 1
}

# Create logs directory
mkdir -p logs
touch logs/discord.log logs/api.log logs/access.log logs/error.log

print_success "Application deployment completed!"

# Reload systemd and start services
print_status "Starting services..."
sudo systemctl daemon-reload

# Start Discord bot service
print_status "Starting Discord bot service..."
sudo systemctl start grime-guardians-discord
sudo systemctl enable grime-guardians-discord

# Wait a moment for Discord bot to initialize
sleep 5

# Check Discord bot status
if sudo systemctl is-active --quiet grime-guardians-discord; then
    print_success "Discord bot service started successfully"
else
    print_warning "Discord bot service may have issues"
    print_status "Check logs: sudo journalctl -u grime-guardians-discord -n 20"
fi

# Start FastAPI service
print_status "Starting FastAPI service..."
sudo systemctl start grime-guardians-api
sudo systemctl enable grime-guardians-api

# Wait a moment for API to initialize
sleep 5

# Check FastAPI status
if sudo systemctl is-active --quiet grime-guardians-api; then
    print_success "FastAPI service started successfully"
else
    print_warning "FastAPI service may have issues"
    print_status "Check logs: sudo journalctl -u grime-guardians-api -n 20"
fi

# Test API health endpoint
print_status "Testing API health endpoint..."
sleep 2
if curl -s localhost:8000/health > /dev/null; then
    print_success "API health endpoint responding"
else
    print_warning "API health endpoint not responding"
fi

# Display service status
print_status "Service Status Summary:"
echo "========================"

services=("grime-guardians-discord" "grime-guardians-api" "nginx" "postgresql" "redis-server")
for service in "${services[@]}"; do
    if sudo systemctl is-active --quiet "$service"; then
        echo -e "✅ $service: ${GREEN}RUNNING${NC}"
    else
        echo -e "❌ $service: ${RED}STOPPED${NC}"
    fi
done

echo ""
print_success "🎉 Grime Guardians Agentic Suite Deployment Complete!"
echo ""
echo "📊 Deployment Summary:"
echo "====================="
echo "🌐 Server IP: $(curl -s ifconfig.me 2>/dev/null || echo 'Unable to detect')"
echo "🔗 API Health: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_IP')/health"
echo "🤖 Discord Bot: $(sudo systemctl is-active grime-guardians-discord)"
echo "⚡ FastAPI: $(sudo systemctl is-active grime-guardians-api)"
echo ""
echo "🧪 Testing Instructions:"
echo "========================"
echo "1. Go to your Discord server"
echo "2. Send test messages:"
echo "   • 'I need a quote for a 3 bedroom house'"
echo "   • 'Customer complaint about service'"
echo "   • '!ava status'"
echo "3. Look for AI agent responses from Dean, Emma, Brandon"
echo "4. Test approval workflow with ✅ reactions"
echo ""
echo "📋 Useful Commands:"
echo "=================="
echo "• Check service status: sudo systemctl status grime-guardians-discord grime-guardians-api"
echo "• View Discord logs: sudo journalctl -u grime-guardians-discord -f"
echo "• View API logs: sudo journalctl -u grime-guardians-api -f"
echo "• Restart services: sudo systemctl restart grime-guardians-discord grime-guardians-api"
echo "• Run backup: ./backup.sh"
echo ""
echo "🚀 Your enhanced AI cleaning service is now LIVE and ready to scale!"

# Create a quick status check script
cat > check_status.sh <<'EOF'
#!/bin/bash
echo "🤖 Grime Guardians Agentic Suite - Status Check"
echo "=============================================="

services=("grime-guardians-discord" "grime-guardians-api" "nginx" "postgresql" "redis-server")
for service in "${services[@]}"; do
    if sudo systemctl is-active --quiet "$service"; then
        echo "✅ $service: RUNNING"
    else
        echo "❌ $service: STOPPED"
    fi
done

echo ""
echo "🌐 API Health Check:"
if curl -s localhost:8000/health > /dev/null; then
    echo "✅ API responding"
else
    echo "❌ API not responding"
fi

echo ""
echo "📊 System Resources:"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
EOF

chmod +x check_status.sh

print_success "Status check script created: ./check_status.sh"
print_status "Run ./check_status.sh anytime to check system status"