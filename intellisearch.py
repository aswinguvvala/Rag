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

# Add the current directory to the path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from hybrid_rag_system import HybridRAGSystem
    RAG_SYSTEM = HybridRAGSystem()
    RAG_AVAILABLE = True
    RAG_ERROR = None
except ImportError as e:
    # Handle graceful degradation
    RAG_SYSTEM = None
    RAG_AVAILABLE = False
    RAG_ERROR = str(e)

# Load environment variables
load_dotenv()

# Configure Streamlit
st.set_page_config(
    page_title="IntelliSearch",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced professional CSS with clean animated background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;600;700&display=swap');
    
    /* Professional Deep Space Background with Image */
    .stApp {
        background: 
            /* Image overlay gradients for readability */
            radial-gradient(ellipse at top, rgba(15, 15, 30, 0.85) 0%, rgba(0, 0, 0, 0.9) 50%, rgba(0, 0, 0, 0.95) 100%),
            linear-gradient(180deg, rgba(0, 0, 0, 0.8) 0%, rgba(5, 5, 16, 0.85) 25%, rgba(10, 10, 21, 0.9) 50%, rgba(5, 5, 16, 0.85) 75%, rgba(0, 0, 0, 0.8) 100%),
            /* Space background image */
            url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80'),
            /* Fallback gradients if image fails to load */
            radial-gradient(ellipse at top, rgba(15, 15, 30, 0.8) 0%, rgba(0, 0, 0, 0.9) 50%, #000000 100%),
            linear-gradient(180deg, #000000 0%, #050510 25%, #0a0a15 50%, #050510 75%, #000000 100%);
        background-size: cover, cover, cover, cover, cover;
        background-position: center, center, center, center, center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: #e1e8ed;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
        padding-bottom: 2rem;
    }
    
    /* Optimized Space Elements */
    .stApp::before {
        content: '';
        position: fixed;
        top: 50%;
        left: 50%;
        width: 30px;
        height: 30px;
        background: radial-gradient(circle, #FFD700 0%, #FF8C00 70%, #FF6B00 100%);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.6);
        pointer-events: none;
        z-index: -1;
        animation: gentlePulse 4s ease-in-out infinite alternate;
        will-change: opacity;
    }
    
    @keyframes gentlePulse {
        0% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
    }

    /* Efficient Starfield */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: 
            radial-gradient(1px 1px at 25px 25px, rgba(255, 255, 255, 0.4), transparent),
            radial-gradient(1px 1px at 75px 75px, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1px 1px at 125px 25px, rgba(255, 255, 255, 0.4), transparent),
            radial-gradient(1px 1px at 175px 75px, rgba(255, 255, 255, 0.2), transparent);
        background-repeat: repeat;
        background-size: 200px 100px;
        pointer-events: none;
        z-index: -2;
        opacity: 0.5;
        animation: subtleTwinkle 6s ease-in-out infinite alternate;
        will-change: opacity;
    }
    
    @keyframes subtleTwinkle {
        0% { opacity: 0.3; }
        100% { opacity: 0.6; }
    }
    
    /* Enhanced Input Styling - Fixed to prevent text cutoff */
    .stTextInput > div > div > input {
        background: rgba(15, 15, 35, 0.95) !important;
        border: 2px solid rgba(100, 255, 218, 0.4) !important;
        border-radius: 25px !important;
        color: #f8fafc !important;
        padding: 1.2rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(20px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin: 0 !important;
        min-height: 3.2rem !important;
        line-height: 1.4 !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    
    .stTextInput > div {
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        overflow: visible !important;
    }
    
    .stTextInput > div > div {
        overflow: visible !important;
        position: relative !important;
    }
    
    .stTextInput {
        margin: 2rem auto !important;
        padding: 0 1rem !important;
        max-width: 1200px !important;
        width: 100% !important;
        overflow: visible !important;
    }
    
    /* Query input container improvements */
    .query-container {
        padding: 2rem 1rem !important;
        margin: 0 auto !important;
        max-width: 1200px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(0, 255, 136, 0.6) !important;
        border-left-color: #00ff88 !important;
        box-shadow: 
            0 0 25px rgba(0, 255, 136, 0.4),
            0 8px 30px rgba(0, 0, 0, 0.3) !important;
        outline: none !important;
        transform: none !important;
        z-index: 10 !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(226, 232, 240, 0.6) !important;
        font-style: italic;
    }
    
    /* Optimized Button Styling */
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
        cursor: pointer !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 8px 25px rgba(0, 255, 136, 0.25) !important;
        will-change: transform;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 35px rgba(0, 255, 136, 0.35) !important;
    }
    
    /* Optimized Result Cards */
    .result-card {
        background: rgba(15, 15, 35, 0.85);
        border: 1px solid rgba(100, 255, 218, 0.25);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        border-left: 4px solid transparent;
        will-change: transform;
    }
    
    .result-card:hover {
        border-color: rgba(0, 255, 136, 0.4);
        border-left-color: #00ff88;
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
    }
    
    /* AI Response */
    .ai-response {
        background: rgba(15, 15, 35, 0.9);
        border: 2px solid rgba(100, 255, 218, 0.3);
        border-radius: 25px;
        padding: 2.5rem;
        margin: 2rem 0;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(25px);
        box-shadow: 
            0 15px 50px rgba(0, 0, 0, 0.4),
            0 0 80px rgba(100, 255, 218, 0.15);
        border-left: 6px solid #00ff88;
    }
    
    /* Professional Header Styling */
    .main-header {
        text-align: center;
        padding: 4rem 2rem 3rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        z-index: 50;
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
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        text-shadow: 0 0 20px rgba(100, 255, 218, 0.3);
        animation: gradientShift 6s ease-in-out infinite alternate;
        letter-spacing: 2px;
        line-height: 1.1;
        will-change: background-position;
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

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    
    /* Help Button Styling */
    .help-button {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 1000;
        background: linear-gradient(135deg, 
            rgba(100, 255, 218, 0.9) 0%, 
            rgba(0, 255, 136, 0.8) 100%) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        font-size: 1.5rem !important;
        color: #0f172a !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 8px 25px rgba(0, 255, 136, 0.3),
            0 4px 15px rgba(0, 0, 0, 0.2) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .help-button:hover {
        transform: translateY(-3px) scale(1.1) !important;
        box-shadow: 
            0 12px 35px rgba(0, 255, 136, 0.4),
            0 6px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Help Modal Styling */
    .help-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.8);
        z-index: 2000;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(10px);
    }
    
    .help-content {
        background: rgba(15, 15, 35, 0.95);
        border: 2px solid rgba(100, 255, 218, 0.3);
        border-radius: 25px;
        padding: 3rem;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(25px);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.5),
            0 0 100px rgba(100, 255, 218, 0.2);
        border-left: 6px solid #00ff88;
        position: relative;
    }
    
    .help-close {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: none;
        border: none;
        color: #64ffda;
        font-size: 2rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .help-close:hover {
        color: #00ff88;
        transform: scale(1.1);
    }
    
    /* Enhanced details/summary styling */
    details summary {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    details summary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 
            0 8px 25px rgba(0, 255, 136, 0.3),
            0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }
    
    details[open] summary {
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Hide Streamlit elements */
    .stDeployButton { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

class IntelliSearch:
    """Enhanced Professional RAG System with Advanced UI"""
    
    def __init__(self):
        self.rag_system = RAG_SYSTEM
        self.ollama_available = False
        self.openai_client = None
        self.is_initialized = False
        self.system_status = None
        
        # Enhanced system configuration
        self.similarity_threshold = 0.4
        self.max_results = 5
        self.enable_web_fallback = True
        self.query_history = []
        self.performance_metrics = {
            'total_queries': 0,
            'avg_response_time': 0,
            'success_rate': 100
        }
        self.token_metrics = {
            'session_tokens': 0,
            'query_tokens': 0,
            'response_tokens': 0
        }
        
        self.setup_llm()
    
    def count_tokens(self, text: str) -> int:
        """Simple token counting approximation (1 token ≈ 4 characters)"""
        return len(text) // 4 if text else 0
        
    def update_token_metrics(self, query: str, response: str):
        """Update token usage metrics"""
        query_tokens = self.count_tokens(query)
        response_tokens = self.count_tokens(response)
        
        self.token_metrics['query_tokens'] = query_tokens
        self.token_metrics['response_tokens'] = response_tokens
        self.token_metrics['session_tokens'] += query_tokens + response_tokens
    
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
        if not RAG_AVAILABLE or not self.rag_system:
            return False
            
        try:
            success = await self.rag_system.initialize()
            
            if success:
                self.rag_system.configure(
                    similarity_threshold=self.similarity_threshold,
                    enable_web_fallback=self.enable_web_fallback,
                    max_local_results=self.max_results,
                    max_web_results=self.max_results
                )
                
                self.system_status = self.rag_system.get_system_status()
                self.is_initialized = True
                
            return success
        except Exception as e:
            print(f"RAG system initialization error: {e}")
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
                    {"role": "system", "content": "You are an intelligent assistant. Provide accurate responses using the provided context."},
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
        """Render space-themed header"""
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
        
        # Add token metrics display
        if self.token_metrics['session_tokens'] > 0:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown(f"""
                <div style="background: rgba(15, 15, 35, 0.8); border: 1px solid rgba(100, 255, 218, 0.3); border-radius: 15px; padding: 1rem; text-align: center; backdrop-filter: blur(20px);">
                    <span style="display: block; font-size: 1.5rem; font-weight: 700; color: #64ffda; margin-bottom: 0.5rem;">{self.token_metrics['query_tokens']}</span>
                    <span style="display: block; font-size: 0.9rem; font-weight: 500; color: #cbd5e0; text-transform: uppercase; letter-spacing: 1px;">Query Tokens</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: rgba(15, 15, 35, 0.8); border: 1px solid rgba(100, 255, 218, 0.3); border-radius: 15px; padding: 1rem; text-align: center; backdrop-filter: blur(20px);">
                    <span style="display: block; font-size: 1.5rem; font-weight: 700; color: #64ffda; margin-bottom: 0.5rem;">{self.token_metrics['response_tokens']}</span>
                    <span style="display: block; font-size: 0.9rem; font-weight: 500; color: #cbd5e0; text-transform: uppercase; letter-spacing: 1px;">Response Tokens</span>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background: rgba(15, 15, 35, 0.8); border: 1px solid rgba(100, 255, 218, 0.3); border-radius: 15px; padding: 1rem; text-align: center; backdrop-filter: blur(20px);">
                    <span style="display: block; font-size: 1.5rem; font-weight: 700; color: #64ffda; margin-bottom: 0.5rem;">{self.token_metrics['session_tokens']}</span>
                    <span style="display: block; font-size: 0.9rem; font-weight: 500; color: #cbd5e0; text-transform: uppercase; letter-spacing: 1px;">Session Total</span>
                </div>
                """, unsafe_allow_html=True)
    
    def render_search_results(self, rag_result: Dict[str, Any]):
        """Render Sources & References section with enhanced linking"""
        method = rag_result.get('method', 'unknown')
        sources = rag_result.get('sources', [])
        confidence = rag_result.get('confidence', 0.0)
        
        # Display sources if available
        if sources:
            # Create dedicated Sources & References section
            st.markdown("""
            <div style="margin: 2rem 0; text-align: center;">
                <h2 style="color: #00ff88; font-size: 1.8rem; font-weight: 600; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                    📚 Sources & References
                </h2>
                <p style="color: #cbd5e0; font-size: 1rem; opacity: 0.8; margin-bottom: 1.5rem;">
                    Click on any source to view the full article
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display method info
            if method == 'semantic_search':
                st.info(f"🧠 **Semantic Search** - Found {len(sources)} relevant sources (Confidence: {confidence:.1%})")
            elif method == 'web_search':
                st.info(f"🌐 **Web Search** - Retrieved {len(sources)} external sources")
            elif method == 'basic_response':
                st.info("💡 **Basic Response Mode** - Guidance provided")
            
            # Display each source with enhanced formatting
            for i, source in enumerate(sources, 1):
                if isinstance(source, dict):
                    content = source.get('content', '')[:400]
                    similarity = source.get('similarity', 0.0)
                    metadata = source.get('metadata', {})
                    source_type = source.get('source_type', 'local')
                    
                    # Extract source information
                    title = metadata.get('title', f'Source {i}')
                    source_name = metadata.get('source', 'Unknown Source')
                    category = metadata.get('category', 'general')
                    url = metadata.get('url', '')
                    
                    # Create enhanced source display
                    if source_type == 'web' and url:
                        # Web source with full URL display
                        source_header = f"""
                        <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                            <div style="margin-bottom: 0.5rem;">
                                <a href="{url}" target="_blank" style="color: #00ff88; text-decoration: none; font-weight: 700; display: inline-flex; align-items: center; gap: 0.5rem; font-size: 1.1rem;">
                                    🔗 {title}
                                </a>
                            </div>
                            <div style="font-size: 0.9rem; color: #64ffda; font-family: 'JetBrains Mono', monospace; background: rgba(100, 255, 218, 0.1); padding: 0.5rem 1rem; border-radius: 8px; border-left: 3px solid #64ffda; word-break: break-all;">
                                📄 Full Article: <a href="{url}" target="_blank" style="color: #00ff88; text-decoration: underline;">{url}</a>
                            </div>
                        </div>
                        """
                    else:
                        # Local source
                        source_header = f"""
                        <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                            <div style="margin-bottom: 0.5rem;">
                                <span style="color: #64ffda; font-weight: 700; display: inline-flex; align-items: center; gap: 0.5rem; font-size: 1.1rem;">
                                    📚 {title}
                                </span>
                            </div>
                            <div style="font-size: 0.9rem; color: #a0aec0; font-family: 'JetBrains Mono', monospace; background: rgba(160, 174, 192, 0.1); padding: 0.5rem 1rem; border-radius: 8px; border-left: 3px solid #a0aec0;">
                                📂 Local Knowledge Base
                            </div>
                        </div>
                        """
                    
                    # Source type and metadata
                    type_indicator = "🌐 Web Source" if source_type == 'web' else "📖 Local Knowledge"
                    
                    # Create the complete source card
                    st.markdown(f"""
                    <div class="result-card" style="margin: 1.5rem 0; border-left: 4px solid {'#00ff88' if source_type == 'web' else '#64ffda'};">
                        <div style="border-bottom: 1px solid rgba(100, 255, 218, 0.2); padding-bottom: 1rem; margin-bottom: 1rem;">
                            {source_header}
                            <div style="font-size: 0.85rem; color: #a0aec0; display: flex; gap: 1.5rem; align-items: center; flex-wrap: wrap;">
                                <span style="background: rgba({'0, 255, 136' if source_type == 'web' else '100, 255, 218'}, 0.2); padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: 600;">{type_indicator}</span>
                                <span>📂 {category.replace('_', ' ').title()}</span>
                                {f'<span>⚡ Relevance: {similarity:.1%}</span>' if similarity > 0 else ''}
                                <span>🔢 Source #{i}</span>
                            </div>
                        </div>
                        <div class="result-content" style="line-height: 1.7; font-size: 1rem; color: #f1f5f9;">
                            {content}{'...' if len(source.get('content', '')) > 400 else ''}
                        </div>
                        <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(100, 255, 218, 0.2); font-size: 0.85rem; color: #64ffda; text-align: right; font-style: italic;">
                            Source: {source_name}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    async def handle_basic_query(self, user_question: str):
        """Handle queries in basic mode when full RAG is unavailable"""
        st.info("🔍 Running in Basic Mode - Advanced RAG features unavailable")
        
        basic_response = f"""
        **Basic Mode Response for: "{user_question}"**
        
        ⚠️ **Limited Functionality**: Advanced RAG features are currently unavailable.
        
        🌟 **Suggestions**:
        - Try rephrasing your question for better results
        - Check if you're looking for general information
        - Consider the query context and related topics
        
        💡 **Alternative**: You can try searching the web directly for: "{user_question}"
        """
        
        st.markdown(f"""
        <div class="ai-response">
            <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem;">
                🔍 Basic Mode Response
            </div>
            <div style="line-height: 1.8; font-size: 1.125rem;">
                {basic_response.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    async def process_query(self, user_question: str):
        """Process user query"""
        if not self.is_initialized:
            await self.handle_basic_query(user_question)
            return
        
        # Enhanced processing indicator
        processing_placeholder = st.empty()
        processing_placeholder.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; padding: 2rem;">
            <div style="background: rgba(15, 15, 35, 0.9); border: 2px solid rgba(100, 255, 218, 0.3); border-radius: 20px; padding: 2rem; text-align: center; backdrop-filter: blur(20px);">
                <div style="font-size: 2rem; margin-bottom: 1rem;">⚡</div>
                <div style="font-size: 1.2rem; color: #64ffda; font-weight: 600; margin-bottom: 0.5rem;">Processing Your Query</div>
                <div style="font-size: 1rem; color: #cbd5e0;">Searching knowledge base and generating response...</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Track query metrics
            start_time = time.time()
            
            # Execute RAG pipeline
            rag_result = await self.rag_system.query(user_question)
            
            # Update token metrics
            response_text = rag_result.get('response', '')
            self.update_token_metrics(user_question, response_text)
                
            # Update performance metrics
            end_time = time.time()
            query_time = rag_result.get('query_time', end_time - start_time)
            self.performance_metrics['total_queries'] += 1
            self.performance_metrics['avg_response_time'] = (
                (self.performance_metrics['avg_response_time'] * (self.performance_metrics['total_queries'] - 1) + query_time) /
                self.performance_metrics['total_queries']
            )
            
            # Add to query history
            self.query_history.append({
                'query': user_question,
                'timestamp': time.time(),
                'response_time': query_time,
                'method': rag_result.get('method', 'unknown'),
                'confidence': rag_result.get('confidence', 0.0)
            })
            
            # Clear processing indicator
            processing_placeholder.empty()
            
            # Generate and display AI response FIRST
            if rag_result.get('response'):
                await self.display_response(rag_result)
            else:
                st.warning("🔍 No response generated. Please try rephrasing your query or check if the topic is covered in our knowledge base.")
            
            # Display sources AFTER the AI response
            self.render_search_results(rag_result)
                
        except Exception as e:
            processing_placeholder.empty()
            # Enhanced error handling with more helpful messages
            self.performance_metrics['success_rate'] = max(0, self.performance_metrics['success_rate'] - 5)
            
            # Categorize error types for better user guidance
            if "timeout" in str(e).lower():
                st.error("⏱️ **Timeout Error**: The request took too long to process. Please try a simpler query or try again in a moment.")
            elif "connection" in str(e).lower() or "network" in str(e).lower():
                st.error("🌐 **Connection Error**: Unable to connect to required services. Please check your internet connection and try again.")
            elif "model" in str(e).lower() or "embedding" in str(e).lower():
                st.error("🤖 **AI Model Error**: There was an issue with the AI processing. Please try rephrasing your query.")
            else:
                st.error(f"⚠️ **Processing Error**: {str(e)}")
                
            # Provide helpful suggestions
            st.info("💡 **Suggestions**: Try a simpler query, check your spelling, or wait a moment and try again.")
    
    def _process_source_citations(self, text: str, sources: List[Dict]) -> str:
        """Convert [Source X] citations to enhanced clickable links with article information"""
        import re
        
        def replace_citation(match):
            source_num = int(match.group(1))
            if 1 <= source_num <= len(sources):
                source = sources[source_num - 1]
                metadata = source.get('metadata', {})
                title = metadata.get('title', f'Source {source_num}')
                source_type = source.get('source_type', 'local')
                
                # Create enhanced citation with hover information
                if source_type == 'web' and metadata.get('url'):
                    url = metadata.get('url')
                    # Enhanced web source citation with full article link indication
                    return f'''<a href="{url}" target="_blank" 
                        style="color: #00ff88; text-decoration: none; font-weight: 600; 
                               border: 1px solid rgba(0, 255, 136, 0.4); 
                               padding: 0.3rem 0.7rem; border-radius: 0.7rem; 
                               background: rgba(0, 255, 136, 0.15); 
                               font-size: 0.95rem; display: inline-flex; 
                               align-items: center; gap: 0.3rem;
                               transition: all 0.3s ease;
                               box-shadow: 0 2px 8px rgba(0, 255, 136, 0.2);"
                        title="🔗 {title} - Click to view full article: {url}"
                        onmouseover="this.style.background='rgba(0, 255, 136, 0.25)'; this.style.transform='translateY(-1px)'"
                        onmouseout="this.style.background='rgba(0, 255, 136, 0.15)'; this.style.transform='translateY(0px)'">
                        🔗 Source {source_num}
                        <span style="font-size: 0.8rem; opacity: 0.8;">📄</span>
                    </a>'''
                else:
                    # Enhanced local source citation
                    return f'''<span 
                        style="color: #64ffda; font-weight: 600; 
                               border: 1px solid rgba(100, 255, 218, 0.4); 
                               padding: 0.3rem 0.7rem; border-radius: 0.7rem; 
                               background: rgba(100, 255, 218, 0.15); 
                               font-size: 0.95rem; display: inline-flex; 
                               align-items: center; gap: 0.3rem;
                               box-shadow: 0 2px 8px rgba(100, 255, 218, 0.2);"
                        title="📚 {title} - Local knowledge base">
                        📚 Source {source_num}
                        <span style="font-size: 0.8rem; opacity: 0.8;">📂</span>
                    </span>'''
            return match.group(0)
        
        # Replace [Source X] patterns with enhanced clickable links
        return re.sub(r'\[Source (\d+)\]', replace_citation, text)

    async def display_response(self, rag_result: Dict[str, Any]):
        """Display response from RAG System with clickable source citations"""
        response_text = rag_result.get('response', 'No response available')
        method = rag_result.get('method', 'unknown')
        confidence = rag_result.get('confidence', 0.0)
        query_time = rag_result.get('query_time', 0.0)
        sources = rag_result.get('sources', [])
        
        # Process source citations to make them clickable
        processed_response = self._process_source_citations(response_text, sources)
        
        # Display response
        st.markdown(f"""
        <div class="ai-response">
            <div style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem;">
                🤖 AI Response
            </div>
            <div style="line-height: 1.8; font-size: 1.125rem; margin-bottom: 2rem;">
                {processed_response.replace(chr(10), '<br>')}
            </div>
            <div style="border-top: 1px solid rgba(100, 255, 218, 0.2); padding-top: 1.5rem; font-size: 0.9rem; color: #a0aec0;">
                <div style="display: flex; gap: 1.5rem; margin-bottom: 1rem;">
                    <span>Method: {method.replace('_', ' ').title()}</span>
                    <span>Confidence: {confidence:.1%}</span>
                    <span>Response Time: {query_time:.2f}s</span>
                </div>
                {f'<div style="margin-bottom: 1rem; color: #64ffda;">📖 References: {len(sources)} sources used in this response</div>' if sources else ''}
                <div style="text-align: center; font-style: italic;">
                    Powered by IntelliSearch RAG System
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    async def run(self):
        """Main application interface"""
        self.render_header()
        
        # System initialization
        if not self.is_initialized and RAG_AVAILABLE:
            with st.spinner("Initializing IntelliSearch System..."):
                success = await self.initialize_rag_system()
                
                if not success:
                    st.warning("⚠️ Running in Basic Mode - Advanced RAG features unavailable")
                    self.is_initialized = False
                else:
                    st.success("✨ IntelliSearch System Ready - Advanced RAG capabilities activated")
                    time.sleep(1)
                    st.rerun()
        
        # System status - simplified without mode announcements
        if self.system_status:
            capabilities = self.system_status.get('capabilities', {})
            active_caps = [k.replace('_', ' ').title() for k, v in capabilities.items() if v]
            
            total_articles = "1100+"
            
            # Enhanced status messaging with performance info
            if len(active_caps) >= 3:
                avg_time = self.performance_metrics.get('avg_response_time', 0)
                success_rate = self.performance_metrics.get('success_rate', 100)
                # Status message removed to clean up UI
            elif len(active_caps) >= 2:
                st.info(f"📊 **Search System Active** - {total_articles} space articles available | {len(active_caps)} features operational")
            else:
                st.warning(f"🔍 **Limited Capability Mode** - {total_articles} articles accessible | {len(active_caps)} feature(s) available")
                
        elif not self.is_initialized:
            if not RAG_AVAILABLE:
                st.info("🌟 **Basic Mode Active** - Core search functionality available. Advanced RAG features are temporarily unavailable due to missing dependencies.")
            else:
                st.warning("⚠️ **Initializing System** - Some advanced features may be limited during startup. Full capabilities will be available shortly.")
        
        # Main query interface
        st.markdown("""
        <div class="query-container">
            <div style="text-align: center; margin: 2rem 0; position: relative; z-index: 100;">
                <h2 style="color: #64ffda; font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem;">
                    🔍 Enter Your Query
                </h2>
                <p style="color: #cbd5e0; font-size: 1rem; opacity: 0.8;">
                    Ask anything about space, technology, careers, or general knowledge
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Query input
        user_question = st.text_input(
            "Search Query",
            placeholder="🚀 What would you like to explore today?",
            help="Submit queries for intelligent information retrieval using advanced RAG techniques",
            label_visibility="collapsed",
            key="main_search_input"
        )
        
        # Search button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            query_button = st.button(
                "🚀 SEARCH", 
                type="primary",
                help="Execute advanced semantic search",
                use_container_width=True
            )
        
        # Help section with better button design
        st.markdown("""
        <div style="text-align: center; margin: 3rem 0 2rem 0;">
            <details style="background: rgba(15, 15, 35, 0.8); border: 2px solid rgba(100, 255, 218, 0.3); border-radius: 20px; padding: 0; margin: 0 auto; max-width: 700px; backdrop-filter: blur(20px);">
                <summary style="background: linear-gradient(135deg, rgba(100, 255, 218, 0.9) 0%, rgba(0, 255, 136, 0.8) 100%); color: #0f172a; padding: 1.5rem 2rem; border-radius: 18px; cursor: pointer; font-weight: 600; font-size: 1.2rem; text-align: center; transition: all 0.3s ease; user-select: none; list-style: none; display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                    📚 How to Use IntelliSearch 
                    <span style="font-size: 0.9rem; opacity: 0.8;">(Click to expand)</span>
                </summary>
                <div style="padding: 2.5rem; color: #f1f5f9; line-height: 1.7;">
                    <h3 style="color: #00ff88; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">🚀 Getting Started</h3>
                    <ul style="margin-bottom: 2rem; padding-left: 1.5rem;">
                        <li style="margin-bottom: 0.75rem;"><strong style="color: #64ffda;">Ask Questions</strong>: Enter your query in the search box above</li>
                        <li style="margin-bottom: 0.75rem;"><strong style="color: #64ffda;">Be Specific</strong>: More detailed questions get better answers</li>
                        <li style="margin-bottom: 0.75rem;"><strong style="color: #64ffda;">Explore Topics</strong>: Try space, technology, recruitment, or scientific concepts</li>
                    </ul>
                    
                    <h3 style="color: #00ff88; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">⚡ System Capabilities</h3>
                    <ul style="margin-bottom: 2rem; padding-left: 1.5rem;">
                        <li style="margin-bottom: 0.75rem;"><strong style="color: #64ffda;">Multi-Source Search</strong>: Searches both local knowledge bases and web sources</li>
                        <li style="margin-bottom: 0.75rem;"><strong style="color: #64ffda;">Space Intelligence</strong>: Specialized in space exploration and astronomy</li>
                        <li style="margin-bottom: 0.75rem;"><strong style="color: #64ffda;">Technical Analysis</strong>: Handles complex scientific and technical queries</li>
                    </ul>
                    
                    <h3 style="color: #00ff88; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">💡 Tips for Best Results</h3>
                    <ul style="padding-left: 1.5rem;">
                        <li style="margin-bottom: 0.75rem;">Use natural language - ask as you would ask a human expert</li>
                        <li style="margin-bottom: 0.75rem;">Include context when relevant (e.g., "for beginners" or "technical details")</li>
                        <li style="margin-bottom: 0.75rem;">Ask follow-up questions to dive deeper into topics</li>
                    </ul>
                </div>
            </details>
        </div>
        """, unsafe_allow_html=True)
        
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