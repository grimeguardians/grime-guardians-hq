#!/bin/bash
# Grime Guardians Agentic Suite - File Transfer Script
# Run this script from your Mac to transfer files to Ubuntu server

set -e

echo "📁 GRIME GUARDIANS - FILE TRANSFER TO UBUNTU"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if server IP is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <server_ip> [ssh_user]"
    print_status "Example: $0 164.90.146.123"
    print_status "Example: $0 164.90.146.123 root"
    exit 1
fi

SERVER_IP="$1"
SSH_USER="${2:-root}"
PROJECT_DIR="/Users/BROB/Desktop/Grime Guardians/GG Agentic Suite/grime-guardians-agentic-suite"

print_status "Transferring Grime Guardians Agentic Suite to Ubuntu server..."
print_status "Server: $SSH_USER@$SERVER_IP"
print_status "Source: $PROJECT_DIR"

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Test SSH connection
print_status "Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_USER@$SERVER_IP" echo "SSH connection successful" 2>/dev/null; then
    print_error "Cannot connect to $SSH_USER@$SERVER_IP"
    print_status "Please ensure:"
    print_status "1. Server IP is correct"
    print_status "2. SSH key is set up or password authentication is enabled"
    print_status "3. Server is running and accessible"
    exit 1
fi

print_success "SSH connection successful"

# Create application directory on server
print_status "Creating application directory on server..."
ssh "$SSH_USER@$SERVER_IP" "mkdir -p /opt/grime-guardians"

# Transfer application files
print_status "Transferring application files..."

# Create a list of files to transfer (excluding unnecessary files)
cat > /tmp/rsync_exclude <<EOF
.git/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache/
.mypy_cache/
.DS_Store
.vscode/
.idea/
*.log
node_modules/
.env.local
.env.development
.env.production
venv/
env/
EOF

# Transfer files using rsync
rsync -avz \
    --progress \
    --exclude-from=/tmp/rsync_exclude \
    --exclude='.env' \
    . "$SSH_USER@$SERVER_IP:/opt/grime-guardians/"

print_success "Application files transferred"

# Clean up temporary file
rm -f /tmp/rsync_exclude

# Set proper ownership on server
print_status "Setting file permissions on server..."
ssh "$SSH_USER@$SERVER_IP" "chown -R ava:ava /opt/grime-guardians"

# Create production .env file from your local .env
print_status "Creating production environment file..."

# Read your local .env and create production version
if [ -f ".env" ]; then
    # Transfer your .env as a template and update database URL for production
    scp .env "$SSH_USER@$SERVER_IP:/tmp/local.env"
    
    ssh "$SSH_USER@$SERVER_IP" bash <<'EOF'
        # Get the database password from deployment info
        if [ -f /opt/grime-guardians/deployment-info.txt ]; then
            DB_PASSWORD=$(grep "Database Password:" /opt/grime-guardians/deployment-info.txt | cut -d' ' -f3)
        else
            DB_PASSWORD="CHANGE_THIS_PASSWORD"
        fi
        
        # Create production .env from local .env
        cd /opt/grime-guardians
        cp /tmp/local.env .env
        
        # Update database URL for production
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://ava_user:$DB_PASSWORD@localhost:5432/grime_guardians|" .env
        
        # Update environment to production
        sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|" .env
        sed -i "s|DEBUG=.*|DEBUG=false|" .env
        
        # Set secure permissions
        chown ava:ava .env
        chmod 600 .env
        
        # Clean up
        rm -f /tmp/local.env
        
        echo "Production .env file created"
EOF
    
    print_success "Production environment file created"
else
    print_warning ".env file not found locally"
    print_status "You'll need to create .env file on the server manually"
fi

# Make deployment scripts executable
print_status "Making deployment scripts executable..."
ssh "$SSH_USER@$SERVER_IP" "chmod +x /opt/grime-guardians/deploy/*.sh"

# Display next steps
print_success "🎉 File transfer completed successfully!"
echo ""
echo "📋 NEXT STEPS:"
echo "============="
echo ""
echo "1. SSH into your server:"
echo "   ssh $SSH_USER@$SERVER_IP"
echo ""
echo "2. Run the application deployment script:"
echo "   sudo su - ava"
echo "   cd /opt/grime-guardians"
echo "   ./deploy/deploy_app.sh"
echo ""
echo "3. Check service status:"
echo "   ./check_status.sh"
echo ""
echo "4. Test Discord bot in your Discord server:"
echo "   Send: 'I need a quote for a 3 bedroom house'"
echo "   Send: 'Customer complaint about service'"
echo "   Send: '!ava status'"
echo ""
echo "5. Verify API endpoints:"
echo "   curl http://$SERVER_IP/health"
echo ""
echo "🚀 Your Grime Guardians Agentic Suite is ready for production!"

# Create a quick connection script
cat > connect_server.sh <<EOF
#!/bin/bash
echo "🔗 Connecting to Grime Guardians Production Server..."
ssh $SSH_USER@$SERVER_IP
EOF

chmod +x connect_server.sh

print_success "Created connection script: ./connect_server.sh"
print_status "Run ./connect_server.sh to quickly connect to your server"