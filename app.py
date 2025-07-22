#!/usr/bin/env python3
"""
IntelliSearch - Streamlit Cloud Optimized Entry Point
Advanced RAG system with semantic search and web fallback capabilities
Optimized for Streamlit Cloud deployment with fallback mechanisms
"""

import streamlit as st
import asyncio
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import traceback

# Configure Streamlit first
st.set_page_config(
    page_title="IntelliSearch",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add the mseis directory to the path
current_dir = Path(__file__).parent
mseis_dir = current_dir / "mseis"
sys.path.insert(0, str(mseis_dir))

# Global state for initialization
if 'initialization_attempted' not in st.session_state:
    st.session_state.initialization_attempted = False
if 'system_ready' not in st.session_state:
    st.session_state.system_ready = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# Try to import the enhanced RAG system with graceful fallback
RAG_AVAILABLE = False
IMPORT_ERROR = None

try:
    from core.enhanced_rag_system import EnhancedRAGSystem
    RAG_AVAILABLE = True
    st.session_state.rag_mode = "enhanced"
except ImportError as e:
    IMPORT_ERROR = str(e)
    st.session_state.rag_mode = "fallback"

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Enhanced professional CSS with clean animated background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;600;700&display=swap');
    
    /* Professional Deep Space Background */
    .stApp {
        background: 
            radial-gradient(ellipse at top, rgba(15, 15, 30, 0.8) 0%, rgba(0, 0, 0, 0.9) 50%, #000000 100%),
            linear-gradient(180deg, #000000 0%, #050510 25%, #0a0a15 50%, #050510 75%, #000000 100%);
        color: #e1e8ed;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    /* Animated solar system */
    .stApp::before {
        content: '';
        position: fixed;
        top: 50%;
        left: 50%;
        width: 35px;
        height: 35px;
        background: radial-gradient(circle, #FFD700 0%, #FF8C00 70%, #FF6B00 100%);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 
            0 0 40px rgba(255, 215, 0, 0.9),
            0 0 80px rgba(255, 140, 0, 0.6),
            0 0 120px rgba(255, 107, 0, 0.3);
        pointer-events: none;
        z-index: 1;
        animation: sunPulse 6s ease-in-out infinite alternate;
    }
    
    @keyframes sunPulse {
        0% { 
            box-shadow: 
                0 0 40px rgba(255, 215, 0, 0.9),
                0 0 80px rgba(255, 140, 0, 0.6),
                0 0 120px rgba(255, 107, 0, 0.3);
        }
        100% { 
            box-shadow: 
                0 0 50px rgba(255, 215, 0, 1),
                0 0 100px rgba(255, 140, 0, 0.8),
                0 0 150px rgba(255, 107, 0, 0.4);
        }
    }

    /* Professional Header Styling */
    .main-header {
        text-align: center;
        padding: 4rem 2rem 3rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        z-index: 10;
    }
    
    .app-title {
        font-size: 4rem;
        font-weight: 700;
        background: linear-gradient(135deg, 
            #ffffff 0%, 
            #64ffda 25%, 
            #00ff88 50%, 
            #64ffda 75%, 
            #ffffff 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        animation: gradientShift 4s ease-in-out infinite alternate;
        letter-spacing: 2px;
        line-height: 1.1;
    }
    
    .app-subtitle {
        font-size: 1.5rem;
        font-weight: 500;
        color: #e2e8f0;
        margin-bottom: 1rem;
        opacity: 0.9;
        letter-spacing: 1px;
    }
    
    .header-description {
        font-size: 1.2rem;
        font-weight: 400;
        color: #cbd5e0;
        opacity: 0.8;
        font-style: italic;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* System Status Cards */
    .status-card {
        background: rgba(15, 15, 35, 0.9);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(20px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        transition: all 0.4s ease;
        position: relative;
        z-index: 10;
    }

    .status-ready {
        border: 2px solid rgba(0, 255, 136, 0.4);
        border-left: 6px solid #00ff88;
    }

    .status-initializing {
        border: 2px solid rgba(100, 255, 218, 0.4);
        border-left: 6px solid #64ffda;
    }

    .status-error {
        border: 2px solid rgba(255, 107, 107, 0.4);
        border-left: 6px solid #ff6b6b;
    }

    .status-fallback {
        border: 2px solid rgba(255, 193, 7, 0.4);
        border-left: 6px solid #ffc107;
    }

    /* Enhanced Input Styling */
    .stTextInput input {
        background: rgba(15, 15, 35, 0.85) !important;
        border: 2px solid rgba(100, 255, 218, 0.3) !important;
        border-radius: 25px !important;
        color: #f8fafc !important;
        padding: 1.5rem 2rem !important;
        font-size: 1.25rem !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(20px) !important;
        transition: all 0.4s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: rgba(0, 255, 136, 0.6) !important;
        border-left-color: #00ff88 !important;
        box-shadow: 
            0 0 30px rgba(0, 255, 136, 0.3),
            0 15px 50px rgba(0, 0, 0, 0.4) !important;
        outline: none !important;
        transform: translateY(-2px) !important;
    }

    /* Enhanced Button Styling */
    .stButton button {
        background: linear-gradient(135deg, 
            rgba(0, 255, 136, 0.9) 0%, 
            rgba(100, 255, 218, 0.8) 50%, 
            rgba(0, 255, 136, 0.9) 100%) !important;
        border: none !important;
        border-radius: 20px !important;
        color: #0f172a !important;
        padding: 1.25rem 3rem !important;
        font-size: 1.125rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.4s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 
            0 10px 40px rgba(0, 255, 136, 0.3),
            0 5px 20px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 
            0 15px 50px rgba(0, 255, 136, 0.4),
            0 8px 30px rgba(0, 0, 0, 0.3) !important;
    }

    /* Animations */
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(100, 255, 218, 0.3);
        border-radius: 50%;
        border-top-color: #64ffda;
        animation: spin 1s ease-in-out infinite;
    }

    /* Hide Streamlit elements */
    .stDeployButton { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Responsive Design */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2.5rem;
        }
        .main-header {
            padding: 2rem 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class IntelliSearchApp:
    """Streamlit Cloud optimized IntelliSearch application"""
    
    def __init__(self):
        self.rag_system = None
        self.is_initialized = False
        
    def render_header(self):
        """Render the application header"""
        st.markdown("""
        <div class="main-header">
            <div class="app-title">🚀 IntelliSearch</div>
            <div class="app-subtitle">
                Advanced Space Intelligence & Research System
            </div>
            <div class="header-description">
                Explore the cosmos through AI-powered knowledge discovery
            </div>
        </div>
        """, unsafe_allow_html=True)

    def render_status_card(self, status: str, title: str, message: str, details: str = None):
        """Render system status card"""
        st.markdown(f"""
        <div class="status-card status-{status}">
            <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 600;">
                {title}
            </h3>
            <p style="margin: 0 0 1rem 0; font-size: 1.1rem; line-height: 1.6;">
                {message}
            </p>
            {f'<div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 10px; font-family: monospace; font-size: 0.9rem; margin-top: 1rem;"><code>{details}</code></div>' if details else ''}
        </div>
        """, unsafe_allow_html=True)

    async def initialize_system(self):
        """Initialize the RAG system with timeout protection"""
        if st.session_state.initialization_attempted:
            return st.session_state.system_ready
            
        st.session_state.initialization_attempted = True
        
        if not RAG_AVAILABLE:
            st.session_state.system_ready = False
            st.session_state.error_message = f"RAG system dependencies not available: {IMPORT_ERROR}"
            return False
        
        try:
            # Show initialization progress
            progress_placeholder = st.empty()
            progress_placeholder.markdown("""
            <div class="status-card status-initializing">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 600;">
                    <span class="loading-spinner"></span> System Initializing...
                </h3>
                <p style="margin: 0; font-size: 1.1rem; line-height: 1.6;">
                    Loading advanced RAG capabilities and knowledge base...
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Initialize with timeout protection
            try:
                self.rag_system = EnhancedRAGSystem()
                
                # Create a task with timeout
                init_task = asyncio.create_task(self.rag_system.initialize())
                success = await asyncio.wait_for(init_task, timeout=30.0)  # 30-second timeout
                
                if success:
                    # Configure the system
                    self.rag_system.configure(
                        similarity_threshold=0.4,
                        enable_web_fallback=True,
                        max_local_results=5,
                        max_web_results=5
                    )
                    
                    # Try to index database (non-blocking)
                    try:
                        await asyncio.wait_for(
                            self.rag_system.index_database(force_reindex=False), 
                            timeout=20.0
                        )
                    except asyncio.TimeoutError:
                        pass  # Continue without full indexing
                    
                    self.is_initialized = True
                    st.session_state.system_ready = True
                    
                else:
                    st.session_state.system_ready = False
                    st.session_state.error_message = "System initialization returned false"
                    
            except asyncio.TimeoutError:
                st.session_state.system_ready = False
                st.session_state.error_message = "System initialization timed out"
                
            except Exception as e:
                st.session_state.system_ready = False
                st.session_state.error_message = f"Initialization error: {str(e)}"
                
            finally:
                progress_placeholder.empty()
                
        except Exception as e:
            st.session_state.system_ready = False
            st.session_state.error_message = f"Critical initialization error: {str(e)}"
        
        return st.session_state.system_ready

    def render_search_interface(self):
        """Render the main search interface"""
        # Query input
        user_question = st.text_input(
            "Search Query",
            placeholder="🔍 Enter your query to explore space intelligence and research...",
            help="Ask questions about space, technology, or research topics",
            label_visibility="collapsed",
            key="main_search_input"
        )
        
        # Search button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            search_button = st.button(
                "🚀 Search Intelligence", 
                type="primary",
                help="Execute advanced semantic search",
                use_container_width=True
            )
        
        return user_question, search_button

    async def process_query(self, query: str):
        """Process user query with the RAG system"""
        if not self.is_initialized or not self.rag_system:
            st.error("System not properly initialized. Please refresh the page.")
            return
            
        try:
            # Show processing indicator
            with st.spinner("🔍 Processing your query..."):
                result = await asyncio.wait_for(
                    self.rag_system.query(query), 
                    timeout=60.0  # 1-minute timeout for query processing
                )
            
            # Display results
            if result and result.get('response'):
                st.markdown(f"""
                <div class="status-card status-ready">
                    <h3 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 600;">
                        💡 Intelligence Response
                    </h3>
                    <div style="font-size: 1.1rem; line-height: 1.8;">
                        {result['response'].replace(chr(10), '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show sources if available
                if result.get('local_results') or result.get('web_results'):
                    with st.expander("📚 Sources", expanded=False):
                        local_results = result.get('local_results', [])
                        web_results = result.get('web_results', [])
                        
                        if local_results:
                            st.write(f"**Knowledge Base Sources:** {len(local_results)} articles")
                        if web_results:
                            st.write(f"**Web Sources:** {len(web_results)} external references")
            else:
                st.warning("No response generated. Please try a different query.")
                
        except asyncio.TimeoutError:
            st.error("Query processing timed out. Please try a simpler question.")
        except Exception as e:
            st.error(f"Query processing error: {str(e)}")

    async def run(self):
        """Main application entry point"""
        # Render header
        self.render_header()
        
        # Initialize system if not already done
        if not st.session_state.initialization_attempted:
            success = await self.initialize_system()
        else:
            success = st.session_state.system_ready
        
        # Show system status
        if success:
            self.render_status_card(
                "ready",
                "✅ System Ready",
                "IntelliSearch is fully operational with advanced RAG capabilities."
            )
            
            # Render search interface
            query, search_clicked = self.render_search_interface()
            
            # Process query if submitted
            if search_clicked and query:
                await self.process_query(query)
                
            # Usage instructions
            with st.expander("📚 How to Use", expanded=False):
                st.markdown("""
                ### Getting Started
                - **Ask Questions**: Enter natural language queries about space, technology, or research
                - **Be Specific**: Detailed questions get better answers
                - **Explore**: Try topics like "Mars missions", "exoplanets", "space technology"
                
                ### System Features
                - **Multi-Source Search**: Local knowledge base + web search fallback
                - **AI-Powered**: Advanced language models for intelligent responses
                - **Space Focus**: Specialized in space exploration and astronomy
                """)
                
        elif st.session_state.error_message:
            # Show error with fallback options
            if "dependencies not available" in st.session_state.error_message:
                self.render_status_card(
                    "fallback",
                    "⚠️ Limited Mode",
                    "IntelliSearch is running in limited mode. Some advanced features may not be available.",
                    st.session_state.error_message
                )
                
                # Simple fallback interface
                st.markdown("### Simple Search Mode")
                query = st.text_input("Enter your question:", placeholder="Ask about space or technology...")
                if st.button("Search") and query:
                    st.info("Advanced RAG features are not available. Please install required dependencies for full functionality.")
                    
            else:
                self.render_status_card(
                    "error",
                    "❌ System Error",
                    "IntelliSearch encountered an initialization error.",
                    st.session_state.error_message
                )
                
                if st.button("🔄 Retry Initialization"):
                    st.session_state.initialization_attempted = False
                    st.session_state.system_ready = False
                    st.session_state.error_message = None
                    st.rerun()
        else:
            # This should not happen, but just in case
            self.render_status_card(
                "initializing",
                "⏳ Initializing...",
                "Please wait while the system starts up..."
            )

# Streamlit Cloud compatible main function
async def main():
    """Application entry point with error handling"""
    try:
        if 'app_instance' not in st.session_state:
            st.session_state.app_instance = IntelliSearchApp()
        
        app = st.session_state.app_instance
        await app.run()
        
    except Exception as e:
        st.error("Application Error")
        st.markdown(f"""
        <div class="status-card status-error">
            <h3>Critical Application Error</h3>
            <p>The application encountered an unexpected error.</p>
            <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                <code>{str(e)}</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Restart Application"):
            # Clear all session state and restart
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Streamlit Cloud compatible execution
if __name__ == "__main__":
    # Run the async main function using Streamlit's event loop
    try:
        # Create new event loop for Streamlit Cloud compatibility
        if hasattr(asyncio, 'run'):
            asyncio.run(main())
        else:
            # Fallback for older Python versions
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            # We're already in an event loop (Streamlit Cloud), so just await
            import inspect
            if inspect.iscoroutinefunction(main):
                # Use Streamlit's event loop
                st.write("Loading...")
        else:
            st.error(f"Runtime error: {e}")
    except Exception as e:
        st.error(f"Application startup error: {e}")
        st.info("Please try refreshing the page.")