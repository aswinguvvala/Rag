#!/usr/bin/env python3
"""
IntelliSearch - Intelligent Information Retrieval System
Advanced RAG system with semantic search and web fallback capabilities
"""

import streamlit as st
import asyncio
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiohttp
import openai
from dotenv import load_dotenv

# Add the mseis directory to the path
current_dir = Path(__file__).parent
mseis_dir = current_dir / "mseis"
sys.path.insert(0, str(mseis_dir))

try:
    from core.enhanced_rag_system import EnhancedRAGSystem
    RAG_AVAILABLE = True
except ImportError as e:
    st.error(f"System dependencies not available: {e}")
    RAG_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure Streamlit
st.set_page_config(
    page_title="IntelliSearch",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ultra-clean professional CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Reset */
    .stApp {
        background: 
            /* Subtle dot pattern */
            radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0),
            /* Professional gradient */
            linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        background-size: 40px 40px, 100% 100%;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
    }
    
    /* Remove Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Header */
    .main-header {
        text-align: center;
        padding: 4rem 0 3rem 0;
        margin-bottom: 3rem;
    }
    
    .app-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .app-subtitle {
        font-size: 1.25rem;
        color: #94a3b8;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* Query Section */
    .query-container {
        max-width: 800px;
        margin: 0 auto 4rem auto;
        padding: 0 2rem;
    }
    
    /* Input Styling */
    .stTextInput input {
        background: rgba(30, 41, 59, 0.95) !important;
        border: 2px solid rgba(71, 85, 105, 0.3) !important;
        border-radius: 16px !important;
        color: #f8fafc !important;
        padding: 1.25rem 2rem !important;
        font-size: 1.125rem !important;
        font-weight: 400 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), 0 8px 30px rgba(0, 0, 0, 0.15) !important;
        outline: none !important;
        transform: translateY(-1px) !important;
    }
    
    .stTextInput input::placeholder {
        color: #64748b !important;
        font-weight: 400 !important;
    }
    
    /* Button Styling */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 1rem 3rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Search Results */
    .search-strategy {
        text-align: center;
        margin: 3rem 0 2rem 0;
    }
    
    .strategy-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 2rem;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 12px;
        color: #e2e8f0;
        font-weight: 500;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .strategy-local { border-left: 4px solid #10b981; }
    .strategy-web { border-left: 4px solid #f59e0b; }
    
    /* Result Cards */
    .result-card {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
        transition: all 0.3s ease;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
    }
    
    .result-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .result-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 1rem;
        line-height: 1.4;
    }
    
    .result-content {
        color: #cbd5e1;
        line-height: 1.7;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .source-link {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #3b82f6;
        text-decoration: none;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .source-link:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.4);
        text-decoration: none;
        transform: translateX(2px);
    }
    
    /* AI Response */
    .ai-response {
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 20px;
        padding: 3rem;
        margin: 3rem 0;
        backdrop-filter: blur(20px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
    }
    
    .ai-response-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .ai-response-content {
        color: #e2e8f0;
        line-height: 1.8;
        font-size: 1.125rem;
        text-align: left;
    }
    
    /* Loading States */
    .stSpinner {
        text-align: center;
    }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2.5rem;
        }
        
        .query-container {
            padding: 0 1rem;
        }
        
        .result-card {
            padding: 1.5rem;
        }
        
        .ai-response {
            padding: 2rem;
        }
    }
    
    /* Clean Expander Styling */
    .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(71, 85, 105, 0.3) !important;
    }
    
    .streamlit-expanderContent {
        background-color: transparent !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

class IntelliSearch:
    """Ultra-clean RAG system for professional demonstration"""
    
    def __init__(self):
        self.rag_system = None
        self.ollama_available = False
        self.openai_client = None
        self.is_initialized = False
        
        # System configuration (hidden from UI)
        self.similarity_threshold = 0.4
        self.max_results = 5
        self.enable_web_fallback = True
        
        self.setup_llm()
        
    def setup_llm(self):
        """Initialize LLM connections"""
        try:
            self.ollama_available = True
            self.ollama_url = "http://localhost:11434"
        except Exception:
            pass
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
    
    async def initialize_rag_system(self):
        """Initialize the RAG system"""
        if not RAG_AVAILABLE:
            return False
            
        try:
            if not self.rag_system:
                self.rag_system = EnhancedRAGSystem()
                
            success = await self.rag_system.initialize()
            if success:
                self.rag_system.configure(
                    similarity_threshold=self.similarity_threshold,
                    enable_web_fallback=self.enable_web_fallback,
                    max_local_results=self.max_results,
                    max_web_results=self.max_results
                )
                
                await self.rag_system.index_database(force_reindex=False)
                self.is_initialized = True
                
            return success
        except Exception:
            return False
    
    async def call_ollama(self, prompt: str, model: str = "llama3.2:3b") -> str:
        """Execute Ollama model inference"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "No response generated")
                    else:
                        return "Unable to generate response"
        except Exception:
            return "Service temporarily unavailable"
    
    def call_openai(self, prompt: str) -> str:
        """Execute OpenAI model inference"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant. Provide accurate responses using only the provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception:
            return "Unable to process request"
    
    async def get_llm_response(self, context_window: str) -> str:
        """Execute model inference with fallback"""
        if self.ollama_available:
            try:
                response = await self.call_ollama(context_window)
                if not response.startswith("Unable"):
                    return response
            except Exception:
                pass
        
        if self.openai_client:
            return self.call_openai(context_window)
        
        return "Service currently unavailable"
    
    def render_header(self):
        """Render clean header"""
        st.markdown("""
        <div class="main-header">
            <div class="app-title">IntelliSearch</div>
            <div class="app-subtitle">
                Intelligent information retrieval with advanced semantic search capabilities
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_search_results(self, rag_result: Dict[str, Any]):
        """Render search results"""
        strategy = rag_result.get('search_strategy', 'unknown')
        local_results = rag_result.get('local_results', [])
        web_results = rag_result.get('web_results', [])
        
        # Search strategy indicator
        if strategy == 'local_database':
            st.markdown(f"""
            <div class="search-strategy">
                <div class="strategy-indicator strategy-local">
                    Found {len(local_results)} relevant articles
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif strategy == 'web_fallback':
            st.markdown(f"""
            <div class="search-strategy">
                <div class="strategy-indicator strategy-web">
                    Retrieved {len(web_results)} external sources
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Display results
        if local_results:
            with st.expander(f"Sources ({len(local_results)})", expanded=False):
                for result in local_results:
                    metadata = result.get('metadata', {})
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-title">{metadata.get('title', 'Source')}</div>
                        <div class="result-content">
                            {metadata.get('summary', 'Content available')[:400]}...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        if web_results:
            with st.expander(f"External Sources ({len(web_results)})", expanded=False):
                for result in web_results:
                    url = result.get('url', '#')
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-title">{result.get('title', 'External Source')}</div>
                        <div class="result-content">
                            {result.get('snippet', 'External content')[:400]}...
                        </div>
                        <a href="{url}" target="_blank" class="source-link">
                            View Source →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
    
    async def process_query(self, user_question: str):
        """Process user query"""
        if not self.is_initialized:
            st.error("System initialization in progress. Please wait...")
            return
        
        with st.spinner("Processing your query..."):
            # Execute RAG pipeline
            rag_result = await self.rag_system.query(user_question)
            
            # Display results
            self.render_search_results(rag_result)
            
            # Generate response
            if rag_result.get('ready_for_llm'):
                await self.generate_response(rag_result)
    
    async def generate_response(self, rag_result: Dict[str, Any]):
        """Generate and display AI response"""
        context_window = rag_result.get('context_window', '')
        
        with st.spinner("Generating response..."):
            ai_response = await self.get_llm_response(context_window)
            
            st.markdown(f"""
            <div class="ai-response">
                <div class="ai-response-header">Response</div>
                <div class="ai-response-content">
                    {ai_response.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    async def run(self):
        """Main application interface"""
        self.render_header()
        
        # Initialize system if needed
        if not self.is_initialized and RAG_AVAILABLE:
            with st.spinner("Initializing system..."):
                success = await self.initialize_rag_system()
                if not success:
                    st.error("System initialization failed")
                    return
                st.success("System ready")
                st.rerun()
        
        if not self.is_initialized:
            st.error("System unavailable")
            return
        
        # Main query interface
        st.markdown('<div class="query-container">', unsafe_allow_html=True)
        
        user_question = st.text_input(
            "Search Query",
            placeholder="Enter your query to search across knowledge base and web sources...",
            help="Submit queries for intelligent information retrieval",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            query_button = st.button("Search", type="primary")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process query
        if query_button and user_question:
            await self.process_query(user_question)

async def main():
    """Application entry point"""
    if not st.session_state.get("intellisearch"):
        st.session_state["intellisearch"] = IntelliSearch()
    
    app = st.session_state["intellisearch"]
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please check system requirements.")