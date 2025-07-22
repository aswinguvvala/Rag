#!/bin/bash

echo "🚀 Starting IntelliSearch Chat Interface..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements_working.txt
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify key dependencies
echo "🔍 Verifying dependencies..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'mseis'))

try:
    import streamlit
    from core.enhanced_rag_system import EnhancedRAGSystem
    print('✅ All dependencies verified')
except Exception as e:
    print(f'❌ Dependency error: {e}')
    exit(1)
"

# Check if port is available
if lsof -i :8501 >/dev/null 2>&1; then
    echo "⚠️  Port 8501 is in use. Killing existing processes..."
    pkill -f "streamlit.*intellisearch" || true
    sleep 2
fi

echo "🌟 Starting IntelliSearch on http://localhost:8501"
echo "📱 You can also access it on your network at:"
echo "   http://$(ipconfig getifaddr en0):8501"
echo ""
echo "💡 Tips:"
echo "   - Use Cmd+C to stop the server"
echo "   - The app has a beautiful space-themed interface"
echo "   - Try queries like 'What is machine learning?' or space topics"
echo ""
echo "🎬 Starting server..."

# Start Streamlit with optimal settings
streamlit run intellisearch.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=false \
    --browser.gatherUsageStats=false \
    --server.runOnSave=true