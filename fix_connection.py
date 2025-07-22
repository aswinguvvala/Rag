#!/usr/bin/env python3
"""
IntelliSearch Connection Fix Script
Addresses common server connection issues
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout")
        return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("🚀 IntelliSearch Connection Fix Script")
    print("=====================================")
    
    # Step 1: Kill any existing Streamlit processes
    print("🧹 Cleaning up existing processes...")
    subprocess.run("pkill -f streamlit", shell=True, capture_output=True)
    time.sleep(2)
    
    # Step 2: Check virtual environment
    if not Path("venv").exists():
        print("📦 Creating virtual environment...")
        if not run_command("python3 -m venv venv", "Create virtual environment"):
            return False
    
    # Step 3: Install dependencies in virtual environment
    print("📚 Installing/updating dependencies...")
    install_cmd = """
    source venv/bin/activate && \
    pip install --upgrade pip && \
    pip install streamlit aiohttp openai python-dotenv sentence-transformers \
                faiss-cpu numpy structlog redis fastapi uvicorn
    """
    if not run_command(install_cmd, "Install dependencies"):
        print("⚠️ Some dependencies may have failed, continuing...")
    
    # Step 4: Test imports
    print("🧪 Testing critical imports...")
    test_imports = """
    source venv/bin/activate && python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'mseis'))

print('Testing imports...')
import streamlit
import aiohttp
import openai
from dotenv import load_dotenv
from core.enhanced_rag_system import EnhancedRAGSystem
print('All imports successful')
"
    """
    if not run_command(test_imports, "Test imports"):
        print("❌ Critical import failure. Check dependencies.")
        return False
    
    # Step 5: Start server with connection-friendly settings
    print("🌟 Starting IntelliSearch server...")
    print("📍 Server will be available at:")
    print("   - Local: http://localhost:8501")
    print("   - Network: http://0.0.0.0:8501")
    print("")
    print("🔄 Starting in 3 seconds... (Ctrl+C to cancel)")
    
    try:
        time.sleep(3)
        
        # Use exec to replace this process with Streamlit
        start_cmd = """
        source venv/bin/activate && \
        streamlit run intellisearch.py \
            --server.port=8501 \
            --server.address=0.0.0.0 \
            --server.headless=false \
            --server.fileWatcherType=none \
            --server.maxUploadSize=10 \
            --browser.gatherUsageStats=false
        """
        
        os.system(start_cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Startup cancelled by user")
        return True
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Fix script failed. Check the error messages above.")
        sys.exit(1)
    else:
        print("\n✅ Fix script completed successfully!")