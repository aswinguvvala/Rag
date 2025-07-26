#!/usr/bin/env python3
"""
IntelliSearch - Clean Streamlit Application
A simple, working RAG system with space-themed UI
"""

import streamlit as st
import asyncio
import time
import sys
import os
from pathlib import Path
import aiohttp
import json
from typing import Dict, List, Any, Optional
import traceback

# Page configuration handled by app.py entry point

# Import the cleaned RAG system
try:
    from clean_rag_system import CleanRAGSystem
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    RAG_ERROR = str(e)

# CSS for space-themed UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3a 50%, #0f0f23 100%);
        color: #e1e8ed;
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 3rem 1rem 2rem 1rem;
        margin-bottom: 2rem;
    }
    
    .app-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #64ffda 50%, #00ff88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        letter-spacing: 2px;
    }
    
    .app-subtitle {
        font-size: 1.2rem;
        color: #64ffda;
        margin-bottom: 0.5rem;
    }
    
    .stTextInput > div > div > input {
        background: rgba(15, 15, 35, 0.9) !important;
        border: 2px solid rgba(100, 255, 218, 0.4) !important;
        border-radius: 25px !important;
        color: #f8fafc !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00ff88 !important;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3) !important;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #00ff88 0%, #64ffda 100%) !important;
        border: none !important;
        border-radius: 20px !important;
        color: #0f172a !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(0, 255, 136, 0.3) !important;
    }
    
    .response-card {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(100, 255, 218, 0.3);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        border-left: 4px solid #00ff88;
    }
    
    .source-card {
        background: rgba(15, 15, 35, 0.6);
        border: 1px solid rgba(100, 255, 218, 0.2);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .status-info {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class IntelliSearchApp:
    """Clean IntelliSearch Application"""
    
    def __init__(self):
        self.rag_system = None
        self.is_initialized = False
        
        # Initialize the RAG system
        if RAG_AVAILABLE:
            try:
                self.rag_system = CleanRAGSystem()
            except Exception as e:
                st.error(f"Failed to initialize RAG system: {e}")
                self.rag_system = None
    
    def render_header(self):
        """Render the application header"""
        st.markdown("""
        <div class="main-header">
            <div class="app-title">🚀 IntelliSearch</div>
            <div class="app-subtitle">AI-Powered Knowledge Discovery</div>
            <p style="color: #cbd5e0; font-size: 1rem; opacity: 0.8;">
                Explore space, technology, and knowledge through intelligent search
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_system_status(self):
        """Show system status"""
        if RAG_AVAILABLE and self.rag_system:
            if self.is_initialized:
                st.markdown("""
                <div class="status-info">
                    ✅ <strong>System Status:</strong> IntelliSearch is fully operational
                    <br>📚 <strong>Knowledge Base:</strong> 1100+ articles loaded
                    <br>🧠 <strong>AI Capabilities:</strong> Semantic search, web fallback
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-info">
                    🔄 <strong>System Status:</strong> Initializing IntelliSearch...
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-info">
                ⚠️ <strong>System Status:</strong> Running in basic mode
                <br>💡 <strong>Info:</strong> Advanced RAG features unavailable
            </div>
            """, unsafe_allow_html=True)
    
    async def initialize_system(self):
        """Initialize the RAG system"""
        if not self.rag_system:
            return False
        
        try:
            success = await self.rag_system.initialize()
            self.is_initialized = success
            return success
        except Exception as e:
            st.error(f"Initialization error: {e}")
            return False
    
    async def process_query(self, query: str):
        """Process user query"""
        if not self.is_initialized or not self.rag_system:
            return await self.handle_basic_query(query)
        
        try:
            # Show processing indicator
            with st.spinner("🔍 Searching knowledge base..."):
                result = await self.rag_system.query(query)
            
            # Display results
            if result and result.get('response'):
                self.display_response(result)
                self.display_sources(result.get('sources', []))
            else:
                st.warning("No results found. Try rephrasing your question.")
                
        except Exception as e:
            st.error(f"Query processing error: {e}")
            st.info("Please try a simpler query or check your connection.")
    
    async def handle_basic_query(self, query: str):
        """Handle queries when RAG system is unavailable"""
        st.markdown(f"""
        <div class="response-card">
            <h3>🔍 Basic Response Mode</h3>
            <p><strong>Your query:</strong> "{query}"</p>
            <p>⚠️ Advanced AI features are currently unavailable. This might be due to:</p>
            <ul>
                <li>Missing dependencies (install with: pip install -r requirements.txt)</li>
                <li>Initialization issues</li>
                <li>System startup still in progress</li>
            </ul>
            <p>💡 <strong>Suggestions:</strong></p>
            <ul>
                <li>Try refreshing the page</li>
                <li>Check the system diagnostics below</li>
                <li>Ensure all dependencies are installed</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    def display_response(self, result: Dict[str, Any]):
        """Display AI response"""
        response = result.get('response', '')
        method = result.get('method', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        st.markdown(f"""
        <div class="response-card">
            <h3>🤖 AI Response</h3>
            <div style="line-height: 1.6; margin: 1rem 0;">
                {response.replace(chr(10), '<br>')}
            </div>
            <div style="border-top: 1px solid rgba(100, 255, 218, 0.2); padding-top: 1rem; margin-top: 1rem;">
                <small>
                    Method: {method.replace('_', ' ').title()} | 
                    Confidence: {confidence:.1%} | 
                    Sources: {len(result.get('sources', []))}
                </small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_sources(self, sources: List[Dict]):
        """Display source information"""
        if not sources:
            return
        
        st.markdown("### 📚 Sources")
        
        for i, source in enumerate(sources, 1):
            content = source.get('content', '')[:200] + '...' if len(source.get('content', '')) > 200 else source.get('content', '')
            metadata = source.get('metadata', {})
            title = metadata.get('title', f'Source {i}')
            
            st.markdown(f"""
            <div class="source-card">
                <strong>{title}</strong><br>
                <small style="color: #64ffda;">Source {i}</small><br>
                <div style="margin-top: 0.5rem; color: #cbd5e0;">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_diagnostics(self):
        """Render system diagnostics"""
        with st.expander("🔧 System Diagnostics"):
            st.write("**Python Version:**", sys.version)
            st.write("**Streamlit Version:**", st.__version__)
            st.write("**RAG System Available:**", "✅ Yes" if RAG_AVAILABLE else "❌ No")
            
            if not RAG_AVAILABLE:
                st.error(f"RAG System Error: {RAG_ERROR}")
            
            # Test basic functionality
            if st.button("Test System"):
                if self.rag_system and self.is_initialized:
                    st.success("✅ System operational")
                else:
                    st.warning("⚠️ System not fully initialized")
    
    async def run(self):
        """Main application runner"""
        # Render header
        self.render_header()
        
        # Initialize system if needed
        if RAG_AVAILABLE and self.rag_system and not self.is_initialized:
            with st.spinner("Initializing IntelliSearch..."):
                await self.initialize_system()
            st.rerun()
        
        # Show system status
        self.render_system_status()
        
        # Main query interface
        st.markdown("### 🔍 Search")
        query = st.text_input(
            "Enter your question:",
            placeholder="Ask me about space, technology, or any topic...",
            help="Type your question and press Enter"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            search_button = st.button("🚀 Search", type="primary")
        
        # Process query
        if search_button and query:
            await self.process_query(query)
        
        # Diagnostics section
        self.render_diagnostics()

def main():
    """Main entry point"""
    try:
        # Create and run the app
        app = IntelliSearchApp()
        
        # Handle async execution properly
        if hasattr(asyncio, 'create_task'):
            # Modern asyncio approach
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Use nest_asyncio for nested loops
                    import nest_asyncio
                    nest_asyncio.apply()
                    loop.run_until_complete(app.run())
                else:
                    asyncio.run(app.run())
            except RuntimeError:
                # Create new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(app.run())
        else:
            # Fallback for older Python versions
            asyncio.run(app.run())
            
    except Exception as e:
        st.error("Application Error")
        st.error(f"Error: {str(e)}")
        
        with st.expander("Full Error Details"):
            st.code(traceback.format_exc())
        
        st.info("**Troubleshooting:**")
        st.info("1. Refresh the page")
        st.info("2. Check dependencies: pip install -r requirements.txt")
        st.info("3. Ensure you're in the correct directory")

if __name__ == "__main__":
    main()