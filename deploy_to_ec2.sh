#!/bin/bash
# IntelliSearch EC2 Deployment Script
# Usage: ./deploy_to_ec2.sh your-ec2-public-ip path-to-your-key.pem

set -e  # Exit on any error

# Configuration
EC2_IP=${1:-"your-ec2-ip"}
KEY_PATH=${2:-"~/.ssh/your-key.pem"}
EC2_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/intellisearch"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 IntelliSearch EC2 Deployment Script${NC}"
echo "=================================="

# Validate inputs
if [ "$EC2_IP" == "your-ec2-ip" ]; then
    echo -e "${RED}❌ Please provide your EC2 public IP address${NC}"
    echo "Usage: ./deploy_to_ec2.sh YOUR_EC2_IP PATH_TO_KEY"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ SSH key not found at: $KEY_PATH${NC}"
    echo "Please provide the correct path to your .pem file"
    exit 1
fi

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "  EC2 IP: $EC2_IP"
echo "  SSH Key: $KEY_PATH"
echo "  Remote Directory: $REMOTE_DIR"
echo ""

# Test SSH connection
echo -e "${YELLOW}🔐 Testing SSH connection...${NC}"
if ! ssh -i "$KEY_PATH" -o ConnectTimeout=10 -o BatchMode=yes "$EC2_USER@$EC2_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to EC2 instance${NC}"
    echo "Please check:"
    echo "  - Your EC2 public IP address"
    echo "  - SSH key permissions (chmod 400 $KEY_PATH)"
    echo "  - Security group allows SSH (port 22)"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Create remote directory
echo -e "${YELLOW}📁 Creating remote directory...${NC}"
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" "mkdir -p $REMOTE_DIR"

# Create file list (exclude venv, cache, and unnecessary files)
echo -e "${YELLOW}📦 Preparing files for transfer...${NC}"
cat > /tmp/rsync_exclude.txt << EOF
venv/
__pycache__/
*.pyc
*.pyo
.git/
.DS_Store
.env.example
*.log
logs/
.pytest_cache/
.coverage
node_modules/
EOF

# Transfer files using rsync
echo -e "${YELLOW}📤 Transferring files to EC2...${NC}"
rsync -avz --progress --exclude-from=/tmp/rsync_exclude.txt \
    -e "ssh -i $KEY_PATH" \
    ./ "$EC2_USER@$EC2_IP:$REMOTE_DIR/"

# Clean up
rm /tmp/rsync_exclude.txt

# Create production environment file with secure API key handling
echo -e "${YELLOW}⚙️ Creating production environment configuration...${NC}"

# Prompt for OpenAI API key if not provided as environment variable
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}🔑 OpenAI API Key Configuration:${NC}"
    echo "Please provide your OpenAI API key (or press Enter to skip and use Ollama only):"
    read -s OPENAI_API_KEY
    echo ""
fi

# Create environment configuration on remote server
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << ENDSSH
cd /home/ubuntu/intellisearch

# Create production .env file with secure key handling
cat > .env.production << 'EOF'
# IntelliSearch Production Environment Configuration
# Auto-generated for EC2 deployment - $(date)

# OpenAI Configuration (Secure)
OPENAI_API_KEY=${OPENAI_API_KEY:-''}
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=150

# Local Ollama Configuration (Primary/Fallback)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:0.5b

# Production System Configuration
DEBUG=false
ENVIRONMENT=production

# EC2 Free Tier Optimizations
MAX_MEMORY_MB=512
CACHE_SIZE_LIMIT=50

# Search Configuration
SIMILARITY_THRESHOLD=0.4
MAX_LOCAL_RESULTS=5
MAX_WEB_RESULTS=3
ENABLE_WEB_FALLBACK=true

# Performance Settings
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF

# Set secure permissions on environment file
chmod 600 .env.production

# Copy to standard .env for application use
cp .env.production .env
chmod 600 .env

echo "✅ Environment configuration created with secure permissions"

# Display configuration status
if [ -n "${OPENAI_API_KEY}" ]; then
    echo "🔑 OpenAI API key configured"
else
    echo "⚠️  No OpenAI API key provided - system will use Ollama only"
fi
ENDSSH

# System setup and dependencies installation
echo -e "${YELLOW}🔧 Setting up system and installing dependencies...${NC}"
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << 'ENDSSH'
cd /home/ubuntu/intellisearch

# Update system packages
sudo apt-get update -qq

# Install system dependencies
sudo apt-get install -y python3-pip python3-venv curl wget unzip

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install Python dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python dependencies installed"

# Install Ollama if not present (optional for cost savings)
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama for local LLM support..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Start Ollama service
    sudo systemctl enable ollama
    sudo systemctl start ollama
    
    # Wait for service to start
    sleep 5
    
    # Pull a lightweight model for testing
    ollama pull qwen2:0.5b
    
    echo "✅ Ollama installed and configured"
else
    echo "✅ Ollama already installed"
fi

# Create required directories
mkdir -p logs storage/cache storage/faiss_db

# Set proper permissions
chmod 755 logs storage
chmod 600 .env* 2>/dev/null || true

echo "✅ System setup completed"
ENDSSH

# Set up systemd service for auto-start
echo -e "${YELLOW}⚙️ Configuring systemd service...${NC}"
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << 'ENDSSH'
# Copy service file to systemd directory
sudo cp /home/ubuntu/intellisearch/intellisearch.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable intellisearch

echo "✅ Systemd service configured"
ENDSSH

# Test deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" << 'ENDSSH'
cd /home/ubuntu/intellisearch
source venv/bin/activate

# Run deployment validation if available
if [ -f "validate_ec2_deployment.py" ]; then
    python validate_ec2_deployment.py
else
    # Basic test
    python -c "
import sys
sys.path.append('.')
try:
    from simple_rag_system import SimpleRAGSystem
    print('✅ RAG system import successful')
except Exception as e:
    print(f'⚠️ RAG system import failed: {e}')
"
fi
ENDSSH

# Get public IP for final instructions
echo -e "${YELLOW}🌐 Getting public IP address...${NC}"  
PUBLIC_IP=$(ssh -i "$KEY_PATH" "$EC2_USER@$EC2_IP" "curl -s http://checkip.amazonaws.com" 2>/dev/null || echo "$EC2_IP")

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================="
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. 🔒 Configure EC2 Security Group:"
echo "   - Open AWS Console → EC2 → Security Groups"  
echo "   - Add inbound rule: Custom TCP, Port 8501, Source 0.0.0.0/0"
echo ""
echo "2. 🚀 Start the application:"
echo "   ssh -i $KEY_PATH $EC2_USER@$EC2_IP"
echo "   cd intellisearch && ./start_production.sh"
echo ""
echo "3. 🌐 Access your application:"
echo "   http://$PUBLIC_IP:8501"
echo ""
echo -e "${YELLOW}🔧 Management Commands:${NC}"
echo "   sudo systemctl start intellisearch    # Start service"
echo "   sudo systemctl stop intellisearch     # Stop service"  
echo "   sudo systemctl status intellisearch   # Check status"
echo "   ./start_production.sh logs            # View logs"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}" 
echo "   - Service will auto-start on boot"
echo "   - Logs are in /home/ubuntu/intellisearch/logs/"
echo "   - Use 'sudo systemctl restart intellisearch' to restart"
echo ""
echo -e "${GREEN}✅ Your IntelliSearch RAG system is ready to use!${NC}"