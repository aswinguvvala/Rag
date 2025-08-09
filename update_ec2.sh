#!/bin/bash

# --- Configuration ---
EC2_HOST="18.117.163.37"
EC2_USER="ubuntu" # Or your EC2 username (e.g., ec2-user)
PEM_KEY_PATH="/Users/aswin/Downloads/aswin.pem" # IMPORTANT: Update this to the path of your PEM key
PROJECT_PATH="/home/ubuntu/NEW_RAG" # IMPORTANT: Update this to the project path on your EC2 instance

echo "🚀 Deploying updated space app to EC2..."

# --- DO NOT EDIT BELOW THIS LINE ---

# Create necessary directories on the EC2 instance
ssh -i "$PEM_KEY_PATH" "$EC2_USER@$EC2_HOST" "mkdir -p $PROJECT_PATH/static/backgrounds $PROJECT_PATH/storage $PROJECT_PATH/.streamlit"

# Configure Streamlit secrets
echo "🔐 Configuring Streamlit secrets..."
ssh -i "$PEM_KEY_PATH" "$EC2_USER@$EC2_HOST" "cat > $PROJECT_PATH/.streamlit/secrets.toml << 'EOF'
# Streamlit Secrets Configuration
# OpenAI API Key for enhanced RAG capabilities

OPENAI_API_KEY = \"\${OPENAI_API_KEY}\"
EOF"

# Upload the NASA background image
echo "📸 Uploading NASA background image..."
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/static/backgrounds/main_nasa_bg.jpg "$EC2_USER@$EC2_HOST:$PROJECT_PATH/static/backgrounds/"

# Upload the updated app.py file and dependencies
echo "🖥️ Uploading updated app.py and core dependencies..."
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/app.py "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/simple_rag_system.py "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/web_search_manager.py "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/requirements.txt "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"

# Upload the space content scraper
echo "🌌 Uploading space content scraper..."
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/space_content_scraper.py "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/update_space_content.py "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"

# Upload the updated knowledge base
echo "📚 Uploading updated knowledge base..."
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/data/knowledge_base.json "$EC2_USER@$EC2_HOST:$PROJECT_PATH/data/"

# Upload the space facts
echo "💫 Uploading space facts..."
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/storage/space_facts.json "$EC2_USER@$EC2_HOST:$PROJECT_PATH/storage/"

# Install/update dependencies
echo "📦 Installing/updating Python dependencies..."
ssh -i "$PEM_KEY_PATH" "$EC2_USER@$EC2_HOST" "cd $PROJECT_PATH && source venv/bin/activate && pip install -r requirements.txt --quiet"

# Upload and run the robust startup script
echo "📝 Uploading startup script..."
scp -i "$PEM_KEY_PATH" /Users/aswin/NEW_RAG/start_cosmorag.sh "$EC2_USER@$EC2_HOST:$PROJECT_PATH/"

# Restart the Streamlit app using robust script
echo "🔄 Restarting CosmoRAG with robust startup script..."
ssh -i "$PEM_KEY_PATH" "$EC2_USER@$EC2_HOST" "cd $PROJECT_PATH && chmod +x start_cosmorag.sh && ./start_cosmorag.sh"

echo "✅ Deployment to EC2 complete!"
echo "🌐 Your updated app is now live at: http://18.117.163.37:8501"
echo "📝 Check logs with: ssh -i $PEM_KEY_PATH $EC2_USER@$EC2_HOST 'tail -f $PROJECT_PATH/streamlit.log'"
