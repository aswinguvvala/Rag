#!/usr/bin/env python3
"""
IntelliSearch - Main Application Entry Point
Clean implementation that fixes the "about:blank" issue

This is the primary entry point referenced in CLAUDE.md documentation.
Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Set page config FIRST - this must be the very first Streamlit command
st.set_page_config(
    page_title="IntelliSearch",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add the current directory to the path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the clean streamlit app
try:
    from streamlit_app import main
    main()
except ImportError as e:
    st.error("🚨 Failed to import IntelliSearch components")
    st.error(f"Import error: {str(e)}")
    
    st.info("💡 **Troubleshooting Steps:**")
    st.info("1. Ensure you're in the correct directory (NEW_RAG)")
    st.info("2. Install dependencies: `pip install -r requirements.txt`")
    st.info("3. Check Python version compatibility (3.11+ recommended)")
    
except Exception as e:
    import traceback
    st.error("🚨 Unexpected application error")
    st.error(f"Error: {str(e)}")
    
    with st.expander("🔍 Full Error Details"):
        st.code(traceback.format_exc())