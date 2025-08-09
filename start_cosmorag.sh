#!/bin/bash

# CosmoRAG Production Startup Script
# Ensures reliable startup and process management

PROJECT_DIR="/home/ubuntu/NEW_RAG"
LOG_FILE="$PROJECT_DIR/cosmorag.log"
PID_FILE="$PROJECT_DIR/cosmorag.pid"

echo "🚀 Starting CosmoRAG..."

# Change to project directory
cd $PROJECT_DIR

# Kill any existing Streamlit processes
echo "🔄 Stopping existing processes..."
pkill -f "streamlit run app.py" || true
sleep 2

# Remove old PID file
rm -f $PID_FILE

# Start Streamlit with proper error handling
echo "▶️ Starting Streamlit application..."
nohup ./venv/bin/streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.runOnSave false \
    --browser.gatherUsageStats false \
    > $LOG_FILE 2>&1 &

# Save PID
echo $! > $PID_FILE

# Wait a moment and check if it started
sleep 5
if ps -p $(cat $PID_FILE) > /dev/null 2>&1; then
    echo "✅ CosmoRAG started successfully!"
    echo "📱 URL: http://0.0.0.0:8501"
    echo "📋 PID: $(cat $PID_FILE)"
    echo "📝 Logs: tail -f $LOG_FILE"
else
    echo "❌ Failed to start CosmoRAG"
    echo "📝 Check logs: cat $LOG_FILE"
    exit 1
fi