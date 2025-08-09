
import streamlit as st
import asyncio
import random
import json
import os
from pathlib import Path
from simple_rag_system import SimpleRAGSystem
import base64

# 🎨 EASY CUSTOMIZATION OPTIONS - Edit these values to personalize your app
APP_TITLE = "CosmoRAG"
APP_SUBTITLE = "DIVING DEEP INTO THE COSMOS"
APP_ICON = "🌌"

# Background options
BACKGROUND_IMAGE = "fixed_nasa"  # Use fixed NASA background image

# Theme colors (hex codes)
PRIMARY_COLOR = "#4a90e2"      # Main blue color
ACCENT_COLOR = "#9b59b6"       # Purple accent
TEXT_COLOR = "#ffffff"         # White text
BACKGROUND_OVERLAY = "rgba(0, 0, 0, 0.2)"  # Light overlay for readability

# --- Page Configuration ---
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="centered",
)

# --- Asset Loading ---
def get_local_image_files(folder_path):
    """Get a list of image files from a local folder."""
    supported_formats = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    return [f for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in supported_formats)]

def get_image_as_base64(path):
    """Get image as base64 string."""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- Background Slideshow Logic ---
def get_background_slideshow_html(image_files, image_titles):
    """Generate HTML for a dynamic background slideshow."""
    slides_html = ""
    for i, (img_file, title) in enumerate(zip(image_files, image_titles)):
        img_path = os.path.join("static/backgrounds", img_file)
        base64_img = get_image_as_base64(img_path)
        active_class = "active" if i == 0 else ""
        slides_html += f"""
        <div class="bg-slide {active_class}" 
             style="background-image: url('data:image/jpeg;base64,{base64_img}');"
             data-title="{title}">
        </div>
        """
    return f'<div class="background-slideshow">{slides_html}</div>'

# --- Custom CSS for Styling ---
st.markdown(
    f"""
    <style>
    /* Background Slideshow */
    .background-slideshow {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -10;
        overflow: hidden;
    }}
    .bg-slide {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        opacity: 0;
        transition: opacity 2s ease-in-out;
        z-index: 1;
    }}
    .bg-slide.active {{
        opacity: 1;
        z-index: 2;
    }}
    
    /* Image Title Overlay */
    .image-title-overlay {{
        position: fixed;
        bottom: 20px;
        left: 20px;
        background: rgba(0, 0, 0, 0.3);
        color: white;
        padding: 8px 16px;
        border-radius: 12px;
        z-index: 100;
        font-size: 14px;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        opacity: 0;
        transition: opacity 1s ease-in-out;
    }}
    
    /* Enhanced cosmic overlay for better text readability */
    .cosmic-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -9;
        background: radial-gradient(ellipse at center, 
            rgba(25, 25, 112, 0.1) 0%, 
            rgba(0, 0, 0, 0.2) 30%, 
            rgba(0, 0, 0, 0.3) 60%, 
            rgba(0, 0, 0, 0.4) 100%);
        pointer-events: none;
    }}
    
    /* Additional text readability overlay specifically for content areas */
    .text-readability-overlay {{
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
    }}
    
    /* Streamlit app container - moved to main UI section above */
    
    /* Enhanced multi-layer star system with parallax */
    .star, .planet, .moon, .streaming-star, .nebula, .shooting-star, .particle {{
        position: absolute;
        pointer-events: none;
    }}
    
    /* Star Layer 1: Background twinkling stars (slowest) */
    .star-layer-1 {{
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 50%;
        animation: twinkle-slow 15s linear infinite, float-horizontal-slow 50s linear infinite;
        z-index: -7;
    }}
    
    /* Star Layer 2: Medium stars with color variation */
    .star-layer-2 {{
        border-radius: 50%;
        animation: twinkle-medium 10s linear infinite, float-horizontal-medium 40s linear infinite;
        z-index: -6;
    }}
    
    /* Star Layer 3: Foreground bright stars (fastest) */
    .star-layer-3 {{
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        animation: twinkle-fast 5s linear infinite, float-horizontal-fast 30s linear infinite;
        z-index: -5;
        box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
    }}
    
    /* Shooting stars */
    .shooting-star {{
        background: linear-gradient(45deg, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 1) 50%, 
            rgba(135, 206, 250, 0.8) 80%,
            rgba(255, 255, 255, 0) 100%);
        border-radius: 50%;
        z-index: -4;
        animation: shooting-star 15s linear infinite;
        box-shadow: 0 0 10px rgba(135, 206, 250, 0.6);
    }}
    
    /* Streaming particles for atmosphere */
    .particle {{
        background: radial-gradient(circle, 
            rgba(255, 255, 255, 0.8) 0%, 
            rgba(255, 255, 255, 0.4) 50%, 
            transparent 100%);
        border-radius: 50%;
        z-index: -4;
        animation: particle-drift 20s linear infinite;
    }}
    
    /* Legacy streaming stars for compatibility */
    .streaming-star {{
        background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 0.8) 50%, 
            rgba(255, 255, 255, 0) 100%);
        z-index: -4;
        animation: stream 10s linear infinite;
    }}
    
    /* Nebula clouds */
    .nebula {{
        border-radius: 50%;
        z-index: -6;
        animation: nebula-drift 30s linear infinite;
        filter: blur(2px);
    }}
    
    .nebula-1 {{
        background: radial-gradient(circle, 
            rgba(138, 43, 226, 0.2) 0%, 
            rgba(75, 0, 130, 0.1) 50%, 
            transparent 100%);
    }}
    
    .nebula-2 {{
        background: radial-gradient(circle, 
            rgba(220, 20, 60, 0.2) 0%, 
            rgba(139, 69, 19, 0.1) 50%, 
            transparent 100%);
    }}
    
    .nebula-3 {{
        background: radial-gradient(circle, 
            rgba(0, 191, 255, 0.2) 0%, 
            rgba(30, 144, 255, 0.1) 50%, 
            transparent 100%);
    }}
    
    /* Black hole effect */
    .black-hole {{
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
    }}
    
    /* Enhanced planet animations */
    .planet, .moon {{
        border-radius: 50%;
        background-size: cover;
        background-position: center;
        animation: orbit 120s linear infinite;
        z-index: -5;
        filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.3));
    }}
    
    .planet1 {{ background-image: url('https://i.imgur.com/CjB1g00.png'); }}
    .planet2 {{ background-image: url('https://i.imgur.com/F2g2000.png'); }}
    .moon1 {{ background-image: url('https://i.imgur.com/DkL1g00.png'); }}

    /* Enhanced Animation keyframes */
    /* Multi-layer twinkling animations */
    @keyframes twinkle-slow {{
        0% {{ opacity: 0.2; transform: scale(0.8); }}
        50% {{ opacity: 0.8; transform: scale(1.1); }}
        100% {{ opacity: 0.2; transform: scale(0.8); }}
    }}
    
    @keyframes twinkle-medium {{
        0% {{ opacity: 0.4; transform: scale(0.9); }}
        50% {{ opacity: 1; transform: scale(1.3); }}
        100% {{ opacity: 0.4; transform: scale(0.9); }}
    }}
    
    @keyframes twinkle-fast {{
        0% {{ opacity: 0.6; transform: scale(1); }}
        50% {{ opacity: 1; transform: scale(1.4); }}
        100% {{ opacity: 0.6; transform: scale(1); }}
    }}
    
    /* Horizontal floating animations for parallax effect */
    @keyframes float-horizontal-slow {{
        0% {{ transform: translateX(-10px); }}
        50% {{ transform: translateX(10px); }}
        100% {{ transform: translateX(-10px); }}
    }}
    
    @keyframes float-horizontal-medium {{
        0% {{ transform: translateX(-15px); }}
        50% {{ transform: translateX(15px); }}
        100% {{ transform: translateX(-15px); }}
    }}
    
    @keyframes float-horizontal-fast {{
        0% {{ transform: translateX(-20px); }}
        50% {{ transform: translateX(20px); }}
        100% {{ transform: translateX(-20px); }}
    }}
    
    /* Shooting star animation */
    @keyframes shooting-star {{
        0% {{ 
            transform: translateX(-200px) translateY(-100px) rotate(45deg);
            opacity: 0;
        }}
        10% {{ opacity: 1; }}
        90% {{ opacity: 1; }}
        100% {{ 
            transform: translateX(100vw) translateY(100vh) rotate(45deg);
            opacity: 0;
        }}
    }}
    
    /* Particle drift animation */
    @keyframes particle-drift {{
        0% {{ 
            transform: translateX(-50px) translateY(100vh);
            opacity: 0;
        }}
        10% {{ opacity: 0.6; }}
        90% {{ opacity: 0.6; }}
        100% {{ 
            transform: translateX(50px) translateY(-100px);
            opacity: 0;
        }}
    }}
    
    /* Legacy animations for compatibility */
    @keyframes twinkle {{
        0% {{ opacity: 0.3; transform: scale(0.8); }}
        50% {{ opacity: 1; transform: scale(1.2); }}
        100% {{ opacity: 0.3; transform: scale(0.8); }}
    }}
    
    @keyframes stream {{
        0% {{ 
            transform: translateX(-100vw) translateY(0px);
            opacity: 0;
        }}
        10% {{ opacity: 1; }}
        90% {{ opacity: 1; }}
        100% {{ 
            transform: translateX(100vw) translateY(-50px);
            opacity: 0;
        }}
    }}
    
    @keyframes nebula-drift {{
        0% {{ transform: translateX(-50px) translateY(0px) rotate(0deg); }}
        100% {{ transform: translateX(50px) translateY(-20px) rotate(360deg); }}
    }}
    
    @keyframes orbit {{
        from {{ transform: rotate(0deg) translateX(100px) rotate(0deg); }}
        to {{ transform: rotate(360deg) translateX(100px) rotate(-360deg); }}
    }}
    
    @keyframes black-hole-pulse {{
        0% {{ filter: blur(1px) brightness(1); }}
        50% {{ filter: blur(2px) brightness(1.2); }}
        100% {{ filter: blur(1px) brightness(1); }}
    }}
    
    @keyframes black-hole-rotate {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    
    /* Streamlit App Root Overrides */
    .stApp {{
        background: transparent !important;
        z-index: 1 !important;
    }}
    
    /* Main Streamlit Container Overrides */
    .main .block-container {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: none !important;
    }}
    
    /* Invisible UI Container - No Visual Elements */
    .main-ui-container {{
        position: relative;
        margin: 20px auto;
        width: 90%;
        max-width: 800px;
        /* All visual elements removed - completely transparent */
        background: transparent;
        padding: 40px;
        min-height: auto;
        overflow: visible;
        z-index: 1000;
    }}

    /* Results layout - maintain normal flow */
    .main-ui-container.with-results {{
        width: 95%;
        max-width: 1000px;
        margin-top: 20px;
    }}

    /* Results container for scrollable content */
    .results-container {{
        position: relative;
        z-index: 999;
        margin-top: 20px;
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}

    /* UI Elements styling */
    .stTextInput > div > div > input {{
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        font-size: 16px;
        padding: 12px 16px;
    }}
    
    .stButton > button {{
        background: transparent;
        color: {TEXT_COLOR};
        border-radius: 15px;
        border: 2px solid rgba(255, 255, 255, 0.2);
        padding: 14px 28px;
        font-weight: 500;
        backdrop-filter: blur(15px);
        transition: all 0.3s ease;
        font-size: 16px;
        width: 100%;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        letter-spacing: 0.5px;
    }}
    
    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.4);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.15);
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }}
    
    .response-card {{
        background-color: rgba(0, 0, 0, 0.15);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        min-height: 200px;
        font-size: 16px;
        line-height: 1.6;
        max-height: 600px;
        overflow-y: auto;
    }}
    
    .source-card {{
        background-color: rgba(0, 0, 0, 0.15);
        border-radius: 18px;
        padding: 25px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }}
    
    /* 🌌 Seamless Cosmic Text - Zero Containers, Pure Background Integration 🌌 */
    .cosmic-title-container {{
        /* Completely invisible container - no visual elements */
        text-align: center;
        margin-bottom: 50px;
        position: relative;
        z-index: 1000;
        /* ZERO styling - completely transparent */
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 20px 0;
    }}
    
    .cosmic-title {{
        font-family: 'Inter', 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
        font-size: 4.5rem;
        font-weight: 300;  /* Much lighter weight for ethereal feel */
        margin: 0;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        letter-spacing: 5px;
        
        /* Subtle semi-transparent blend with background */
        color: rgba(255, 255, 255, 0.85);
        
        /* Soft natural glow using text-shadow only */
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.3),
                     0 0 40px rgba(135, 206, 250, 0.2),
                     0 0 60px rgba(255, 255, 255, 0.1),
                     0 2px 4px rgba(0, 0, 0, 0.1);
        
        /* Gentle floating animation */
        animation: textFloat 8s ease-in-out infinite;
    }}
    
    .title-text {{
        position: relative;
        display: inline-block;
    }}
    
    .cosmic-subtitle {{
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 1.4rem;
        font-weight: 200;  /* Ultra-light weight */
        margin: 15px 0 0 0;
        letter-spacing: 3px;
        text-transform: uppercase;
        
        /* Semi-transparent white with subtle blue tint */
        color: rgba(255, 255, 255, 0.75);
        
        /* Soft text-shadow glow */
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.2),
                     0 0 30px rgba(135, 206, 250, 0.15),
                     0 1px 3px rgba(0, 0, 0, 0.1);
        
        /* Gentle breathing animation */
        animation: subtitleBreathe 10s ease-in-out infinite;
        position: relative;
    }}
    
    /* Minimal, soft animations */
    @keyframes textFloat {{
        0%, 100% {{ 
            transform: translateY(0px);
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3),
                         0 0 40px rgba(135, 206, 250, 0.2),
                         0 0 60px rgba(255, 255, 255, 0.1),
                         0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        50% {{ 
            transform: translateY(-2px);
            text-shadow: 0 0 25px rgba(255, 255, 255, 0.4),
                         0 0 45px rgba(135, 206, 250, 0.25),
                         0 0 65px rgba(255, 255, 255, 0.15),
                         0 2px 4px rgba(0, 0, 0, 0.1);
        }}
    }}
    
    @keyframes subtitleBreathe {{
        0%, 100% {{ 
            opacity: 0.75;
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.2),
                         0 0 30px rgba(135, 206, 250, 0.15),
                         0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        50% {{ 
            opacity: 0.9;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3),
                         0 0 35px rgba(135, 206, 250, 0.2),
                         0 1px 3px rgba(0, 0, 0, 0.1);
        }}
    }}
    
    
    /* Responsive seamless title design */
    @media (max-width: 768px) {{
        .cosmic-title-container {{
            margin-bottom: 40px;
            padding: 15px 0;
        }}
        .cosmic-title {{
            font-size: 3.5rem;
            letter-spacing: 4px;
            font-weight: 300;
        }}
        .cosmic-subtitle {{
            font-size: 1.2rem;
            letter-spacing: 2px;
            font-weight: 200;
            margin: 12px 0 0 0;
        }}
    }}
    
    @media (max-width: 480px) {{
        .cosmic-title-container {{
            margin-bottom: 30px;
            padding: 10px 0;
        }}
        .cosmic-title {{
            font-size: 2.8rem;
            letter-spacing: 3px;
            font-weight: 300;
        }}
        .cosmic-subtitle {{
            font-size: 1.0rem;
            letter-spacing: 2px;
            font-weight: 200;
            margin: 10px 0 0 0;
        }}
        /* Lighter animations on mobile for performance */
        .cosmic-title {{
            animation: textFloat 12s ease-in-out infinite;
        }}
        .cosmic-subtitle {{
            animation: subtitleBreathe 15s ease-in-out infinite;
        }}
    }}

    h1, h2, h3, h4, h5, h6, p, li, .stMarkdown {{
        color: white;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }}
    
    /* Enhanced response card text styling */
    .response-card p {{
        margin-bottom: 12px;
        font-size: 16px;
        line-height: 1.7;
    }}
    
    .response-card h1, .response-card h2, .response-card h3 {{
        margin-top: 20px;
        margin-bottom: 15px;
        color: #4a90e2;
    }}
    
    .response-card ul, .response-card ol {{
        margin-left: 20px;
        margin-bottom: 15px;
    }}
    
    .response-card li {{
        margin-bottom: 8px;
        line-height: 1.6;
    }}
    
    /* Deep dive section styling */
    .stTextInput[data-testid="deep_dive_input"] input {{
        background-color: rgba(74, 144, 226, 0.1) !important;
        border: 2px solid rgba(74, 144, 226, 0.3) !important;
        color: white !important;
        font-size: 16px !important;
    }}
    
    .stTextInput[data-testid="deep_dive_input"] input:focus {{
        border-color: rgba(74, 144, 226, 0.6) !important;
        box-shadow: 0 0 10px rgba(74, 144, 226, 0.3) !important;
    }}
    
    /* Style Streamlit info components to match cosmic theme */
    .stInfo {{
        background-color: rgba(0, 100, 200, 0.2) !important;
        border: 1px solid rgba(0, 150, 255, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        color: white !important;
    }}
    
    .stInfo > div {{
        color: white !important;
    }}
    
    /* Remove any potential black boxes from Streamlit components */
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }}
    
    /* Enhanced Performance optimizations with hardware acceleration */
    .background-slideshow {{
        will-change: opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
        perspective: 1000px;
    }}
    
    .bg-slide {{
        will-change: opacity, transform;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        image-rendering: optimizeSpeed;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: optimize-contrast;
    }}
    
    /* Hardware acceleration for all star layers */
    .star-layer-1, .star-layer-2, .star-layer-3, .star {{
        will-change: opacity, transform;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }}
    
    .shooting-star {{
        will-change: transform, opacity;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }}
    
    .particle {{
        will-change: transform, opacity;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }}
    
    .cosmic-title {{
        will-change: filter, transform;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
    }}
    
    .cosmic-title::before {{
        will-change: background-position, opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
    }}
    
    .black-hole {{
        will-change: transform, filter;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }}
    
    .nebula {{
        will-change: transform, opacity;
        transform: translateZ(0) translate3d(0, 0, 0);
        backface-visibility: hidden;
        contain: layout style paint;
    }}
    
    /* Memory optimization - reduce complexity on lower-end devices */
    @media (max-width: 768px) and (max-device-pixel-ratio: 2) {{
        .cosmic-title::before {{
            display: none; /* Remove glow effect on mobile */
        }}
        
        .star-layer-1, .star-layer-2 {{
            animation-duration: 20s, 60s !important; /* Slower animations */
        }}
        
        .shooting-star {{
            animation-duration: 20s !important;
        }}
    }}
    
    /* Ultra-low performance mode for older devices */
    @media (max-width: 480px) and (max-device-pixel-ratio: 1) {{
        .star-layer-1 {{
            display: none; /* Hide background layer on very low-end devices */
        }}
        
        .particle {{
            display: none; /* Hide particles on very low-end devices */
        }}
        
        .nebula {{
            animation: none !important; /* Disable nebula animation */
        }}
        
        .cosmic-title {{
            animation-duration: 8s, 4s !important; /* Slower title animation */
        }}
    }}
    
    /* Enhanced reduced motion for accessibility */
    @media (prefers-reduced-motion: reduce) {{
        .bg-slide, .star, .black-hole, .star-layer-1, .star-layer-2, .star-layer-3,
        .shooting-star, .particle, .nebula {{
            animation: none !important;
            transition: none !important;
        }}
        
        .cosmic-title, .cosmic-title::before, .title-icon, .cosmic-subtitle {{
            animation: none !important;
            transition: none !important;
        }}
        
        .image-title-overlay {{
            opacity: 0.9 !important;
        }}
        
        /* Maintain static visual interest without motion */
        .cosmic-title {{
            background: linear-gradient(45deg, #4a90e2 0%, #9b59b6 50%, #e74c3c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
    }}
    
    /* Additional Streamlit overrides for proper layout */
    .element-container {{
        z-index: inherit !important;
    }}
    
    /* Ensure Streamlit sidebar doesn't interfere */
    .css-1d391kg {{
        z-index: 999 !important;
    }}
    
    /* Streamlit header override */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 0 !important;
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .background-slideshow {{
            height: 100vh;
        }}
        
        .bg-slide {{
            background-attachment: scroll; /* Better mobile performance */
        }}
        
        .black-hole {{
            width: 80px;
            height: 80px;
        }}
        
        .image-title-overlay {{
            bottom: 15px;
            left: 15px;
            font-size: 12px;
            padding: 6px 12px;
        }}
        
        .main-ui-container {{
            width: 95%;
            padding: 25px;
            margin: 10px auto;
        }}
        .stButton > button {{
            padding: 12px 24px;
            font-size: 14px;
            border-radius: 12px;
        }}
        .stTextInput > div > div > input {{
            font-size: 14px;
            padding: 10px 14px;
        }}
    }}
    
    @media (max-width: 480px) {{
        .main-ui-container {{
            width: 98%;
            padding: 20px;
            border-radius: 15px;
            margin: 5px auto;
        }}
        
        .stButton > button {{
            padding: 10px 20px;
            font-size: 13px;
            border-radius: 10px;
        }}
        .stTextInput > div > div > input {{
            font-size: 13px;
            padding: 8px 12px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Fixed NASA Background ---
if BACKGROUND_IMAGE == "fixed_nasa":
    # Get the fixed NASA background image
    nasa_bg_path = "static/backgrounds/main_nasa_bg.jpg"
    if os.path.exists(nasa_bg_path):
        base64_img = get_image_as_base64(nasa_bg_path)
        st.markdown(
            f'''
            <div class="fixed-background" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                z-index: -10;
                background-image: url('data:image/jpeg;base64,{base64_img}');
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            "></div>
            <div class="image-title-overlay" style="opacity: 0.8;">Hubble Space Telescope Deep Field</div>
            ''',
            unsafe_allow_html=True
        )

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
        st.warning(f"⚠️ Some RAG components couldn't initialize: {{e}}")
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
if 'show_instructions' not in st.session_state:
    st.session_state.show_instructions = False

# Determine if we should show the fixed UI or normal layout
has_results = st.session_state.query and st.session_state.result
container_class = "with-results" if has_results else ""

# Start main UI container
st.markdown(f'<div class="main-ui-container {{container_class}}">', unsafe_allow_html=True)

# --- Enhanced UI Components ---
# Create the animated cosmic title
cosmic_title_html = f'''
<div class="cosmic-title-container">
    <h1 class="cosmic-title">
        <span class="title-text">{APP_TITLE}</span>
    </h1>
    <p class="cosmic-subtitle">{APP_SUBTITLE}</p>
</div>
'''

st.markdown(cosmic_title_html, unsafe_allow_html=True)

# --- System Status Indicator ---
def show_system_status():
    """Clean interface - no status display"""
    pass

# Removed status display for clean interface

# --- Search Bar and Buttons ---
query = st.text_input(
    "Ask a question:",
    placeholder="e.g., What is the Artemis program?",
    value=st.session_state.query,
    key="query_input"
)

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("Search"):
        st.session_state.query = query
        st.session_state.result = None # Reset result
        st.session_state.deep_dive_topic = None

with col2:
    if st.button("Surprise Me"):
        st.session_state.query = ""
        st.session_state.result = None
        st.session_state.deep_dive_topic = None
        
        # Define interesting space topics as fallback
        space_topics = [
            "the James Webb Space Telescope",
            "the Artemis lunar mission",
            "black holes and how they form",
            "the search for exoplanets",
            "Mars exploration and rovers",
            "the International Space Station",
            "dark matter and dark energy",
            "the formation of galaxies",
            "SpaceX Starship missions",
            "the Hubble Space Telescope discoveries",
            "solar flares and space weather",
            "the search for extraterrestrial life",
            "neutron stars and pulsars",
            "planetary formation",
            "space mining possibilities",
            "the future of human space exploration"
        ]
        
        # Try to pick a clean title from documents, otherwise use fallback
        clean_query = None
        if rag_system.documents:
            # Try multiple random documents to find a clean title
            for _ in range(5):
                random_doc = random.choice(rag_system.documents)
                title = random_doc.get('title', '')
                # Check if title looks like a file path or is problematic
                if title and not ('/' in title or '\\' in title or title.startswith('.')):
                    clean_query = f"Tell me about {title}"
                    break
        
        # Use fallback if no clean title found
        if not clean_query:
            clean_query = f"Tell me about {random.choice(space_topics)}"
        
        st.session_state.query = clean_query

with col3:
    if st.button("How to Use"):
        st.session_state.show_instructions = not st.session_state.show_instructions

# --- How to Use Instructions ---\nif st.session_state.show_instructions:\n    st.markdown(\n        \"\"\"\n        <div style='margin: 30px 0; background: rgba(0, 0, 0, 0.15); border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(20px);'>\n            <h3 style='color: rgba(255, 255, 255, 0.9); margin-bottom: 20px; text-align: center; text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4); font-weight: 300; letter-spacing: 1px;'>How to Use CosmoRAG</h3>\n            \n            <div style='margin-bottom: 25px;'>\n                <h4 style='color: #4a90e2; margin-bottom: 15px; font-weight: 400;'>🤖 What is RAG?</h4>\n                <p style='color: rgba(255, 255, 255, 0.8); line-height: 1.6; margin-bottom: 15px;'>\n                    <strong>RAG (Retrieval-Augmented Generation)</strong> combines the power of AI with a vast knowledge base. \n                    It searches through documents, finds relevant information, and generates intelligent, fact-based responses.\n                </p>\n            </div>\n            \n            <div style='margin-bottom: 25px;'>\n                <h4 style='color: #4a90e2; margin-bottom: 15px; font-weight: 400;'>🌍 Ask About Anything!</h4>\n                <p style='color: rgba(255, 255, 255, 0.8); line-height: 1.6; margin-bottom: 15px;'>\n                    While the app has a cosmic theme, <strong>you can ask questions about ANY topic</strong> - not just space! \n                    Try questions about science, technology, history, literature, or any subject you're curious about.\n                </p>\n                <div style='background: rgba(74, 144, 226, 0.1); border-radius: 10px; padding: 15px; margin: 15px 0;'>\n                    <p style='color: rgba(255, 255, 255, 0.9); margin: 0; font-style: italic;'>💡 Examples: \"Explain quantum physics\", \"What is machine learning?\", \"Tell me about ancient Rome\", \"How does photosynthesis work?\"</p>\n                </div>\n            </div>\n            \n            <div style='margin-bottom: 25px;'>\n                <h4 style='color: #4a90e2; margin-bottom: 15px; font-weight: 400;'>🚀 How to Use the Features</h4>\n                <ul style='color: rgba(255, 255, 255, 0.8); line-height: 1.8; padding-left: 20px;'>\n                    <li><strong>Search:</strong> Type any question and get AI-powered answers with sources</li>\n                    <li><strong>Surprise Me:</strong> Get a random interesting topic to explore</li>\n                    <li><strong>Deep Dive:</strong> After getting an answer, dive deeper into specific aspects</li>\n                    <li><strong>How to Use:</strong> Toggle this help section on/off</li>\n                </ul>\n            </div>\n            \n            <div style='text-align: center; margin-top: 20px;'>\n                <p style='color: rgba(255, 255, 255, 0.6); font-size: 14px; font-style: italic;'>🌌 Explore the universe of knowledge - one question at a time!</p>\n            </div>\n        </div>\n        \"\"\",\n        unsafe_allow_html=True\n    )\n\n# --- Space Facts Display ---
@st.cache_data
def load_space_facts():
    """Load space facts from the scraped data"""
    facts_path = Path("storage/space_facts.json")
    if facts_path.exists():
        try:
            with open(facts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('facts', [])
        except Exception as e:
            print(f"Error loading space facts: {e}")
    
    # Fallback facts if file doesn't exist
    return [
        {"fact": "The Sun contains 99.86% of the mass in our solar system.", "source": "Astronomical Data"},
        {"fact": "One million Earths could fit inside the Sun.", "source": "NASA"},
        {"fact": "Jupiter's Great Red Spot is larger than Earth.", "source": "Space Research"},
        {"fact": "Light from the Sun takes 8 minutes to reach Earth.", "source": "Physics"}
    ]

# Display space facts section (only when no query results are shown)
if not (st.session_state.query and st.session_state.result):
    st.markdown("---")
    st.markdown("### Did You Know? Space Facts")
    
    space_facts = load_space_facts()
    if space_facts:
        # Select a random fact to display
        fact_data = random.choice(space_facts)
        
        st.markdown(
            f"""
            <div style='margin-top: 20px; background: transparent; border: 2px solid rgba(255, 165, 0, 0.3); border-radius: 15px; padding: 25px; text-align: center; box-shadow: 0 4px 20px rgba(255, 165, 0, 0.1);'>
                <h4 style='color: #FFB347; margin-bottom: 8px; text-shadow: 0 2px 8px rgba(0, 0, 0, 0.4); font-weight: 400; letter-spacing: 1px; font-size: 1.3rem;'>⭐ Space Facts ⭐</h4>\n                <p style='font-size: 12px; color: rgba(255, 165, 0, 0.8); margin-bottom: 18px; text-transform: uppercase; letter-spacing: 2px; font-weight: 500;'>Did You Know?</p>
                <p style='font-size: 18px; line-height: 1.7; margin-bottom: 15px; color: rgba(255, 255, 255, 0.9); text-shadow: 0 2px 6px rgba(0, 0, 0, 0.4); font-weight: 400; background: rgba(255, 165, 0, 0.05); padding: 15px; border-radius: 10px; border-left: 4px solid #FFB347;'>{fact_data['fact']}</p>
                <p style='font-size: 13px; color: rgba(255, 165, 0, 0.7); margin: 0; text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3); font-style: italic;'>
                    📚 Source: {fact_data['source']}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Add a refresh button for new fact
        col1, col2, col3 = st.columns([1, 1, 2])
        with col2:
            if st.button("New Fact", key="new_fact_btn"):
                st.rerun()

# Close the main UI container
st.markdown('</div>', unsafe_allow_html=True)

# --- Simple NASA Background ---
# Simple background with NASA image
simple_background = """
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
            st.markdown("### Response")
            st.markdown(f"<div class='response-card'>{result.get('response', 'No response generated.')}</div>", unsafe_allow_html=True)

            # Display Sources
            st.markdown("### Sources")
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
                if st.button("Dive In!", key="dive_button"):
                    if deep_dive_query.strip():
                        with st.spinner("Preparing deep dive..."):
                            st.session_state.query = deep_dive_query.strip()
                            st.session_state.result = None
                            st.rerun()
                    else:
                        st.warning("Please enter a topic to explore!")

            # Close results container
            st.markdown('</div>', unsafe_allow_html=True)
