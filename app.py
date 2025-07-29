
import streamlit as st
import asyncio
import random
import json
import os
from simple_rag_system import SimpleRAGSystem
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="IntelliSearch",
    page_icon="🌌",
    layout="centered",
)

# --- Custom CSS for Styling ---


# --- Custom CSS for Simple NASA Background ---
st.markdown(
    """
    <style>
    /* Simple NASA background system */
    .nasa-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -10;
        background-image: url('https://science.nasa.gov/wp-content/uploads/2023/06/solar-system-model.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.85;
    }
    
    /* Enhanced cosmic overlay for better text readability */
    .cosmic-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -9;
        background: radial-gradient(ellipse at center, 
            rgba(25, 25, 112, 0.2) 0%, 
            rgba(0, 0, 0, 0.5) 30%, 
            rgba(0, 0, 0, 0.7) 60%, 
            rgba(0, 0, 0, 0.9) 100%);
        pointer-events: none;
    }
    
    /* Additional text readability overlay specifically for content areas */
    .text-readability-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -8;
        background: linear-gradient(
            135deg,
            rgba(0, 0, 0, 0.1) 0%,
            rgba(0, 0, 0, 0.3) 25%,
            rgba(0, 0, 0, 0.2) 50%,
            rgba(0, 0, 0, 0.3) 75%,
            rgba(0, 0, 0, 0.1) 100%
        );
        pointer-events: none;
    }
    
    /* Streamlit app container - moved to main UI section above */
    
    /* Enhanced multi-layer star system with parallax */
    .star, .planet, .moon, .streaming-star, .nebula, .shooting-star, .particle {
        position: absolute;
        pointer-events: none;
    }
    
    /* Star Layer 1: Background twinkling stars (slowest) */
    .star-layer-1 {
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 50%;
        animation: twinkle-slow linear infinite, float-horizontal-slow linear infinite;
        z-index: -7;
    }
    
    /* Star Layer 2: Medium stars with color variation */
    .star-layer-2 {
        border-radius: 50%;
        animation: twinkle-medium linear infinite, float-horizontal-medium linear infinite;
        z-index: -6;
    }
    
    /* Star Layer 3: Foreground bright stars (fastest) */
    .star-layer-3 {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        animation: twinkle-fast linear infinite, float-horizontal-fast linear infinite;
        z-index: -5;
        box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
    }
    
    /* Shooting stars */
    .shooting-star {
        background: linear-gradient(45deg, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 1) 50%, 
            rgba(135, 206, 250, 0.8) 80%,
            rgba(255, 255, 255, 0) 100%);
        border-radius: 50%;
        z-index: -4;
        animation: shooting-star linear infinite;
        box-shadow: 0 0 10px rgba(135, 206, 250, 0.6);
    }
    
    /* Streaming particles for atmosphere */
    .particle {
        background: radial-gradient(circle, 
            rgba(255, 255, 255, 0.8) 0%, 
            rgba(255, 255, 255, 0.4) 50%, 
            transparent 100%);
        border-radius: 50%;
        z-index: -4;
        animation: particle-drift linear infinite;
    }
    
    /* Legacy streaming stars for compatibility */
    .streaming-star {
        background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 0.8) 50%, 
            rgba(255, 255, 255, 0) 100%);
        z-index: -4;
        animation: stream linear infinite;
    }
    
    /* Nebula clouds */
    .nebula {
        border-radius: 50%;
        z-index: -6;
        animation: nebula-drift linear infinite;
        filter: blur(2px);
    }
    
    .nebula-1 {
        background: radial-gradient(circle, 
            rgba(138, 43, 226, 0.2) 0%, 
            rgba(75, 0, 130, 0.1) 50%, 
            transparent 100%);
    }
    
    .nebula-2 {
        background: radial-gradient(circle, 
            rgba(220, 20, 60, 0.2) 0%, 
            rgba(139, 69, 19, 0.1) 50%, 
            transparent 100%);
    }
    
    .nebula-3 {
        background: radial-gradient(circle, 
            rgba(0, 191, 255, 0.2) 0%, 
            rgba(30, 144, 255, 0.1) 50%, 
            transparent 100%);
    }
    
    /* Black hole effect */
    .black-hole {
        position: fixed;
        width: 150px;
        height: 150px;
        border-radius: 50%;
        background: radial-gradient(circle, 
            rgba(0, 0, 0, 1) 30%, 
            rgba(139, 69, 19, 0.8) 50%, 
            rgba(255, 140, 0, 0.4) 70%,
            transparent 100%);
        animation: black-hole-pulse 8s ease-in-out infinite, 
                   black-hole-rotate 20s linear infinite;
        z-index: -3;
        filter: blur(1px);
    }
    
    /* Enhanced planet animations */
    .planet, .moon {
        border-radius: 50%;
        background-size: cover;
        background-position: center;
        animation: orbit linear infinite;
        z-index: -5;
        filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.3));
    }
    
    .planet1 { background-image: url('https://i.imgur.com/CjB1g00.png'); }
    .planet2 { background-image: url('https://i.imgur.com/F2g2000.png'); }
    .moon1 { background-image: url('https://i.imgur.com/DkL1g00.png'); }

    /* Enhanced Animation keyframes */
    /* Multi-layer twinkling animations */
    @keyframes twinkle-slow {
        0% { opacity: 0.2; transform: scale(0.8); }
        50% { opacity: 0.8; transform: scale(1.1); }
        100% { opacity: 0.2; transform: scale(0.8); }
    }
    
    @keyframes twinkle-medium {
        0% { opacity: 0.4; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.3); }
        100% { opacity: 0.4; transform: scale(0.9); }
    }
    
    @keyframes twinkle-fast {
        0% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.4); }
        100% { opacity: 0.6; transform: scale(1); }
    }
    
    /* Horizontal floating animations for parallax effect */
    @keyframes float-horizontal-slow {
        0% { transform: translateX(-10px); }
        50% { transform: translateX(10px); }
        100% { transform: translateX(-10px); }
    }
    
    @keyframes float-horizontal-medium {
        0% { transform: translateX(-15px); }
        50% { transform: translateX(15px); }
        100% { transform: translateX(-15px); }
    }
    
    @keyframes float-horizontal-fast {
        0% { transform: translateX(-20px); }
        50% { transform: translateX(20px); }
        100% { transform: translateX(-20px); }
    }
    
    /* Shooting star animation */
    @keyframes shooting-star {
        0% { 
            transform: translateX(-200px) translateY(-100px) rotate(45deg);
            opacity: 0;
        }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { 
            transform: translateX(100vw) translateY(100vh) rotate(45deg);
            opacity: 0;
        }
    }
    
    /* Particle drift animation */
    @keyframes particle-drift {
        0% { 
            transform: translateX(-50px) translateY(100vh);
            opacity: 0;
        }
        10% { opacity: 0.6; }
        90% { opacity: 0.6; }
        100% { 
            transform: translateX(50px) translateY(-100px);
            opacity: 0;
        }
    }
    
    /* Legacy animations for compatibility */
    @keyframes twinkle {
        0% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 0.3; transform: scale(0.8); }
    }
    
    @keyframes stream {
        0% { 
            transform: translateX(-100vw) translateY(0px);
            opacity: 0;
        }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { 
            transform: translateX(100vw) translateY(-50px);
            opacity: 0;
        }
    }
    
    @keyframes nebula-drift {
        0% { transform: translateX(-50px) translateY(0px) rotate(0deg); }
        100% { transform: translateX(50px) translateY(-20px) rotate(360deg); }
    }
    
    @keyframes orbit {
        from { transform: rotate(0deg) translateX(100px) rotate(0deg); }
        to { transform: rotate(360deg) translateX(100px) rotate(-360deg); }
    }
    
    @keyframes black-hole-pulse {
        0% { filter: blur(1px) brightness(1); }
        50% { filter: blur(2px) brightness(1.2); }
        100% { filter: blur(1px) brightness(1); }
    }
    
    @keyframes black-hole-rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* Streamlit App Root Overrides */
    .stApp {
        background: transparent !important;
        z-index: 1 !important;
    }
    
    /* Main Streamlit Container Overrides */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: none !important;
    }
    
    /* Simplified UI Container - Normal Document Flow */
    .main-ui-container {
        position: relative;
        margin: 20px auto;
        width: 90%;
        max-width: 800px;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 40px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        min-height: auto;
        overflow: visible;
        z-index: 1000;
    }

    /* Results layout - maintain normal flow */
    .main-ui-container.with-results {
        width: 95%;
        max-width: 1000px;
        margin-top: 20px;
    }

    /* Results container for scrollable content */
    .results-container {
        position: relative;
        z-index: 999;
        margin-top: 20px;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* UI Elements styling */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        font-size: 16px;
        padding: 12px 16px;
    }
    
    .stButton > button {
        background-color: rgba(74, 144, 226, 0.8);
        color: white;
        border-radius: 12px;
        border: 1px solid rgba(74, 144, 226, 0.6);
        padding: 12px 24px;
        font-weight: bold;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        font-size: 16px;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: rgba(53, 122, 189, 0.9);
        border: 1px solid rgba(53, 122, 189, 0.8);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(74, 144, 226, 0.4);
    }
    
    .response-card {
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        min-height: 200px;
        font-size: 16px;
        line-height: 1.6;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .source-card {
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    /* Simplified Cosmic Title Styling */
    .cosmic-title-container {
        text-align: center;
        margin-bottom: 30px;
        position: relative;
        z-index: 1000;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
    }
    
    .cosmic-title {
        font-family: 'Arial', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        margin: 0;
        padding: 20px 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        color: white;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8),
                     0 0 30px rgba(74, 144, 226, 0.6),
                     0 0 50px rgba(255, 255, 255, 0.4);
        position: relative;
    }
    
    .title-icon {
        font-size: 3.2rem;
        filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.6));
    }
    
    .title-text {
        position: relative;
        letter-spacing: 2px;
    }
    
    .cosmic-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.95);
        margin: 10px 0 0 0;
        letter-spacing: 1px;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9),
                     0 0 20px rgba(74, 144, 226, 0.6);
        background: rgba(0, 0, 0, 0.4);
        padding: 8px 16px;
        border-radius: 12px;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    
    /* Responsive title design */
    @media (max-width: 768px) {
        .cosmic-title {
            font-size: 2.5rem;
            gap: 10px;
        }
        .title-icon {
            font-size: 2.2rem;
        }
        .cosmic-subtitle {
            font-size: 1.1rem;
        }
    }
    
    @media (max-width: 480px) {
        .cosmic-title {
            font-size: 2rem;
            gap: 8px;
        }
        .title-icon {
            font-size: 1.8rem;
        }
        .cosmic-subtitle {
            font-size: 1rem;
        }
    }

    h1, h2, h3, h4, h5, h6, p, li, .stMarkdown {
        color: white;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    /* Enhanced response card text styling */
    .response-card p {
        margin-bottom: 12px;
        font-size: 16px;
        line-height: 1.7;
    }
    
    .response-card h1, .response-card h2, .response-card h3 {
        margin-top: 20px;
        margin-bottom: 15px;
        color: #4a90e2;
    }
    
    .response-card ul, .response-card ol {
        margin-left: 20px;
        margin-bottom: 15px;
    }
    
    .response-card li {
        margin-bottom: 8px;
        line-height: 1.6;
    }
    
    /* Deep dive section styling */
    .stTextInput[data-testid="deep_dive_input"] input {
        background-color: rgba(74, 144, 226, 0.1) !important;
        border: 2px solid rgba(74, 144, 226, 0.3) !important;
        color: white !important;
        font-size: 16px !important;
    }
    
    .stTextInput[data-testid="deep_dive_input"] input:focus {
        border-color: rgba(74, 144, 226, 0.6) !important;
        box-shadow: 0 0 10px rgba(74, 144, 226, 0.3) !important;
    }
    
    /* Style Streamlit info components to match cosmic theme */
    .stInfo {
        background-color: rgba(0, 100, 200, 0.2) !important;
        border: 1px solid rgba(0, 150, 255, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        color: white !important;
    }
    
    .stInfo > div {
        color: white !important;
    }
    
    /* Remove any potential black boxes from Streamlit components */
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
        background-color: rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    
    /* Enhanced Performance optimizations with hardware acceleration */
    .background-slideshow {
        will-change: opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
        perspective: 1000px;
    }
    
    .bg-slide {
        will-change: opacity, transform;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        image-rendering: optimizeSpeed;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: optimize-contrast;
    }
    
    /* Hardware acceleration for all star layers */
    .star-layer-1, .star-layer-2, .star-layer-3, .star {
        will-change: opacity, transform;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }
    
    .shooting-star {
        will-change: transform, opacity;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }
    
    .particle {
        will-change: transform, opacity;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }
    
    .cosmic-title {
        will-change: filter, transform;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
    }
    
    .cosmic-title::before {
        will-change: background-position, opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
    }
    
    .black-hole {
        will-change: transform, filter;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }
    
    .nebula {
        will-change: transform, opacity;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }
    
    /* Memory optimization - reduce complexity on lower-end devices */
    @media (max-width: 768px) and (max-device-pixel-ratio: 2) {
        .cosmic-title::before {
            display: none; /* Remove glow effect on mobile */
        }
        
        .star-layer-1, .star-layer-2 {
            animation-duration: 20s, 60s !important; /* Slower animations */
        }
        
        .shooting-star {
            animation-duration: 20s !important;
        }
    }
    
    /* Ultra-low performance mode for older devices */
    @media (max-width: 480px) and (max-device-pixel-ratio: 1) {
        .star-layer-1 {
            display: none; /* Hide background layer on very low-end devices */
        }
        
        .particle {
            display: none; /* Hide particles on very low-end devices */
        }
        
        .nebula {
            animation: none !important; /* Disable nebula animation */
        }
        
        .cosmic-title {
            animation-duration: 8s, 4s !important; /* Slower title animation */
        }
    }
    
    /* Enhanced reduced motion for accessibility */
    @media (prefers-reduced-motion: reduce) {
        .bg-slide, .star, .black-hole, .star-layer-1, .star-layer-2, .star-layer-3,
        .shooting-star, .particle, .nebula {
            animation: none !important;
            transition: none !important;
        }
        
        .cosmic-title, .cosmic-title::before, .title-icon, .cosmic-subtitle {
            animation: none !important;
            transition: none !important;
        }
        
        .image-title-overlay {
            opacity: 0.9 !important;
        }
        
        /* Maintain static visual interest without motion */
        .cosmic-title {
            background: linear-gradient(45deg, #4a90e2 0%, #9b59b6 50%, #e74c3c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    }
    
    /* Additional Streamlit overrides for proper layout */
    .element-container {
        z-index: inherit !important;
    }
    
    /* Ensure Streamlit sidebar doesn't interfere */
    .css-1d391kg {
        z-index: 999 !important;
    }
    
    /* Streamlit header override */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .background-slideshow {
            height: 100vh;
        }
        
        .bg-slide {
            background-attachment: scroll; /* Better mobile performance */
        }
        
        .black-hole {
            width: 80px;
            height: 80px;
        }
        
        .image-title-overlay {
            bottom: 15px;
            left: 15px;
            font-size: 12px;
            padding: 6px 12px;
        }
        
        .main-ui-container {
            width: 95%;
            padding: 25px;
            margin: 10px auto;
        }
        .stButton > button {
            padding: 10px 20px;
            font-size: 14px;
        }
        .stTextInput > div > div > input {
            font-size: 14px;
            padding: 10px 14px;
        }
    }
    
    @media (max-width: 480px) {
        .main-ui-container {
            width: 98%;
            padding: 20px;
            border-radius: 15px;
            margin: 5px auto;
        }
        
        .stButton > button {
            padding: 8px 16px;
            font-size: 13px;
        }
        .stTextInput > div > div > input {
            font-size: 13px;
            padding: 8px 12px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Removed complex background cycling functions - using simple NASA background now

# Legacy function for video background (kept for compatibility)
def get_base64_video(video_file):
    with open(video_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- Initialize RAG System ---
@st.cache_resource
def get_rag_system():
    system = SimpleRAGSystem()
    # Use synchronous initialization to avoid event loop conflicts
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(system.initialize())
        loop.close()
    except Exception as e:
        st.warning(f"⚠️ Some RAG components couldn't initialize: {e}")
        st.info("🌐 The system will use web search mode when local components aren't available.")
    return system

rag_system = get_rag_system()

# --- Session State Management ---
if 'query' not in st.session_state:
    st.session_state.query = ""
if 'result' not in st.session_state:
    st.session_state.result = None
if 'deep_dive_topic' not in st.session_state:
    st.session_state.deep_dive_topic = None

# Determine if we should show the fixed UI or normal layout
has_results = st.session_state.query and st.session_state.result
container_class = "with-results" if has_results else ""

# Start main UI container
st.markdown(f'<div class="main-ui-container {container_class}">', unsafe_allow_html=True)

# --- Enhanced UI Components ---
# Create the animated cosmic title
cosmic_title_html = '''
<div class="cosmic-title-container">
    <h1 class="cosmic-title">
        <span class="title-icon">🌌</span>
        <span class="title-text">IntelliSearch</span>
    </h1>
    <p class="cosmic-subtitle">Your intelligent guide to the cosmos and beyond</p>
</div>
'''

st.markdown(cosmic_title_html, unsafe_allow_html=True)

# --- System Status Indicator ---
def show_system_status():
    """Show enhanced system status with detailed information"""
    try:
        status_items = []
        details = []
        
        # Check embedding model
        if hasattr(rag_system, 'embedding_model') and rag_system.embedding_model:
            status_items.append("🧠 AI Embeddings")
        
        # Check web search
        if hasattr(rag_system, 'web_search_manager') and rag_system.web_search_manager:
            status_items.append("🌐 Web Search")
        
        # Check documents with detailed info
        if hasattr(rag_system, 'documents') and rag_system.documents:
            doc_count = len(rag_system.documents)
            status_items.append(f"📚 {doc_count} Documents")
            
            # Get detailed system information
            if hasattr(rag_system, 'get_system_info'):
                try:
                    system_info = rag_system.get_system_info()
                    
                    # Show data source information
                    data_source = system_info.get('data_source', 'Unknown')
                    details.append(f"🗃️ Data Source: {data_source}")
                    
                    # Show categories if we have substantial content
                    categories = system_info.get('document_categories', [])
                    total_categories = system_info.get('total_categories', 0)
                    
                    if categories and doc_count > 10:
                        # Show top categories
                        category_display = ', '.join(categories[:4])
                        if total_categories > 4:
                            category_display += f" (+{total_categories-4} more)"
                        details.append(f"📊 Knowledge Domains: {category_display}")
                        
                        # Show content statistics for large datasets
                        if doc_count > 100:
                            content_stats = system_info.get('content_stats', {})
                            total_chars = content_stats.get('total_characters', 'N/A')
                            avg_length = content_stats.get('avg_content_length', 0)
                            details.append(f"📈 Content: {total_chars} chars, avg {avg_length} per article")
                    
                    # Show environment info
                    env_info = system_info.get('environment', {})
                    if env_info.get('streamlit_cloud'):
                        if doc_count > 1000:
                            details.append("🌐 Streamlit Cloud with Consolidated Knowledge Base")
                        else:
                            details.append("🌐 Streamlit Cloud with Enhanced Fallback Dataset")
                    else:
                        details.append("💻 Local Environment with Full Knowledge Base")
                        
                    # Show knowledge base availability
                    if system_info.get('knowledge_base_available'):
                        details.append("✅ Consolidated knowledge base loaded successfully")
                    
                    # Show AI model configuration (OpenAI/Ollama status)
                    config_info = system_info.get('configuration', {})
                    if config_info.get('openai_available'):
                        status_items.append("🤖 OpenAI Ready")
                    else:
                        # Check if we're on Streamlit Cloud and missing API key
                        if env_info.get('streamlit_cloud'):
                            details.append("⚠️ OpenAI API key needed for cloud deployment")
                        else:
                            details.append("🤖 Local AI: Ollama fallback mode")
                    
                except Exception as e:
                    details.append(f"⚠️ System info error: {str(e)[:50]}...")
        
        if status_items:
            status_text = " | ".join(status_items)
            st.markdown(f"<div style='text-align: center; color: #4a90e2; font-size: 14px; margin-bottom: 10px;'>✅ Active: {status_text}</div>", unsafe_allow_html=True)
            
            # Show additional details if available
            if details:
                details_text = "<br>".join(details)
                st.markdown(f"<div style='text-align: center; color: #7a7a7a; font-size: 12px; margin-bottom: 20px;'>{details_text}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; color: #ff6b6b; font-size: 14px; margin-bottom: 20px;'>⚠️ Limited functionality - some services unavailable</div>", unsafe_allow_html=True)
    except Exception as e:
        # Show minimal fallback info
        st.markdown(f"<div style='text-align: center; color: #7a7a7a; font-size: 12px; margin-bottom: 20px;'>ℹ️ System initializing...</div>", unsafe_allow_html=True)

show_system_status()

# --- Search Bar and Buttons ---
query = st.text_input(
    "Ask a question:",
    placeholder="e.g., What is the Artemis program?",
    value=st.session_state.query,
    key="query_input"
)

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🔍 Search"):
        st.session_state.query = query
        st.session_state.result = None # Reset result
        st.session_state.deep_dive_topic = None

with col2:
    if st.button("✨ Surprise Me"):
        st.session_state.query = ""
        st.session_state.result = None
        st.session_state.deep_dive_topic = None
        # Pick a random document from the local knowledge base
        if rag_system.documents:
            random_doc = random.choice(rag_system.documents)
            st.session_state.query = f"Tell me about {random_doc['title']}"

# Remove info message to prevent empty box display

# Close the main UI container
st.markdown('</div>', unsafe_allow_html=True)

# --- Simple NASA Background ---
# Simple background with NASA image
simple_background = """
<div class="nasa-background"></div>
<div class="cosmic-overlay"></div>
<div class="text-readability-overlay"></div>
"""

st.markdown(simple_background, unsafe_allow_html=True)


# --- Async Query Handler ---
def run_search_query(query: str):
    """Run search query with proper event loop handling"""
    try:
        # Try to get existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new one
                import threading
                result = [None]
                exception = [None]
                
                def run_in_thread():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result[0] = new_loop.run_until_complete(rag_system.search_query(query))
                        new_loop.close()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()
                
                if exception[0]:
                    raise exception[0]
                return result[0]
            else:
                return loop.run_until_complete(rag_system.search_query(query))
        except RuntimeError:
            # No event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(rag_system.search_query(query))
            loop.close()
            return result
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            user_msg = "🌐 Network connection issue. Please check your internet connection and try again."
        elif "ollama" in error_msg.lower():
            user_msg = "🤖 AI service temporarily unavailable. Using basic search results instead."
        else:
            user_msg = f"⚠️ Search encountered an issue: {error_msg}"
        
        st.warning(user_msg)
        return {
            "response": f"I encountered a technical issue while processing your search: {user_msg}\n\nPlease try:\n• Checking your internet connection\n• Refreshing the page\n• Trying a simpler question\n• Waiting a moment and trying again",
            "sources": [],
            "method": "error", 
            "processing_time": 0,
            "query": query
        }

# --- Main Logic ---
if st.session_state.query:
    with st.spinner("Searching the cosmos..."):
        if not st.session_state.result:
             st.session_state.result = run_search_query(st.session_state.query)

        result = st.session_state.result
        
        if result:
            # Start results container
            st.markdown('<div class="results-container">', unsafe_allow_html=True)
            
            # Display Response
            st.markdown("### 🚀 Response")
            st.markdown(f"<div class='response-card'>{result.get('response', 'No response generated.')}</div>", unsafe_allow_html=True)

            # Display Sources
            st.markdown("### 📚 Sources")
            sources = result.get("sources", [])
            if sources:
                for source in sources:
                    with st.container():
                        st.markdown(
                            f"""
                            <div class='source-card'>
                                <h4>{source.get('title', 'Unknown Title')}</h4>
                                <p><b>Source:</b> <a href='{source.get('source')}' target='_blank'>{source.get('source')}</a></p>
                                <p><b>Type:</b> {source.get('source_type', 'N/A')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.info("No sources found.")

            # Deep Dive Feature
            st.markdown("---")
            st.markdown("### 💫 Deep Dive")
            st.markdown("Want to learn more? Enter a topic from the response to dive deeper.")
            
            # Enhanced deep dive styling with columns
            col1, col2 = st.columns([3, 1])
            with col1:
                deep_dive_query = st.text_input(
                    "Enter a topic for a Deep Dive:",
                    placeholder="e.g., Artemis lunar missions, Mars rovers, etc.",
                    key="deep_dive_input"
                )
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                if st.button("🌊 Dive In!", key="dive_button"):
                    if deep_dive_query.strip():
                        with st.spinner("Preparing deep dive..."):
                            st.session_state.query = deep_dive_query.strip()
                            st.session_state.result = None
                            st.rerun()
                    else:
                        st.warning("Please enter a topic to explore!")

            # Close results container
            st.markdown('</div>', unsafe_allow_html=True)
