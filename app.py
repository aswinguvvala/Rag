#!/usr/bin/env python3
"""
IntelliSearch - Main Application Entry Point
Advanced RAG system with semantic search and web fallback capabilities

This is the primary entry point referenced in CLAUDE.md documentation.
Run with: streamlit run app.py
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the main IntelliSearch application
try:
    from intellisearch import main as intellisearch_main
    
    if __name__ == "__main__":
        # Launch the IntelliSearch application
        intellisearch_main()
        
except ImportError as e:
    import streamlit as st
    
    st.error("🚨 Failed to import IntelliSearch components")
    st.error(f"Import error: {str(e)}")
    
    st.info("💡 **Troubleshooting Steps:**")
    st.info("1. Ensure you're in the correct directory (NEW_RAG)")
    st.info("2. Install dependencies: `pip install -r requirements.txt`")
    st.info("3. Check Python version compatibility (3.11+ recommended)")
    st.info("4. Verify all required files are present")
    
    # Show directory contents for debugging
    with st.expander("🔍 Directory Contents (Debugging)"):
        try:
            files = list(Path('.').iterdir())
            for file in sorted(files):
                if file.is_file():
                    st.write(f"📄 {file.name}")
                elif file.is_dir():
                    st.write(f"📁 {file.name}/")
        except Exception as e:
            st.write(f"Unable to list directory: {e}")
            
except Exception as e:
    import streamlit as st
    
    st.error("🚨 Unexpected application error")
    st.error(f"Error: {str(e)}")
    
    with st.expander("🔍 Full Error Details"):
        import traceback
        st.code(traceback.format_exc())