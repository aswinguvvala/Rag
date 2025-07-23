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
    # Handle graceful degradation
    RAG_AVAILABLE = False
    IMPORT_ERROR = str(e)

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
        padding-bottom: 2rem;
    }
    
    /* Enhanced Solar System Animation */
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
            0 0 120px rgba(255, 107, 0, 0.3),
            0 0 160px rgba(255, 69, 0, 0.1);
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

    /* Individual Planet Orbits */
    .planet {
        position: fixed;
        top: 50%;
        left: 50%;
        pointer-events: none;
        z-index: 1;
    }

    /* Mercury */
    .planet:nth-of-type(1) {
        width: 4px;
        height: 4px;
        background: #8C7853;
        border-radius: 50%;
        transform-origin: 60px 0;
        animation: orbit-mercury 8s linear infinite;
    }

    /* Venus */
    .planet:nth-of-type(2) {
        width: 6px;
        height: 6px;
        background: #FFC649;
        border-radius: 50%;
        transform-origin: 80px 0;
        animation: orbit-venus 12s linear infinite;
    }

    /* Earth */
    .planet:nth-of-type(3) {
        width: 7px;
        height: 7px;
        background: radial-gradient(circle, #4A90E2 0%, #2E5C8A 100%);
        border-radius: 50%;
        transform-origin: 100px 0;
        animation: orbit-earth 16s linear infinite;
        box-shadow: 0 0 6px rgba(74, 144, 226, 0.6);
    }

    /* Mars */
    .planet:nth-of-type(4) {
        width: 5px;
        height: 5px;
        background: #CD5C5C;
        border-radius: 50%;
        transform-origin: 120px 0;
        animation: orbit-mars 24s linear infinite;
    }

    /* Jupiter */
    .planet:nth-of-type(5) {
        width: 14px;
        height: 14px;
        background: radial-gradient(circle, #D2691E 0%, #B8860B 100%);
        border-radius: 50%;
        transform-origin: 160px 0;
        animation: orbit-jupiter 48s linear infinite;
        box-shadow: 0 0 8px rgba(210, 105, 30, 0.7);
    }

    /* Saturn */
    .planet:nth-of-type(6) {
        width: 12px;
        height: 12px;
        background: #FAD5A5;
        border-radius: 50%;
        transform-origin: 190px 0;
        animation: orbit-saturn 60s linear infinite;
        box-shadow: 0 0 0 3px rgba(250, 213, 165, 0.3);
    }

    /* Uranus */
    .planet:nth-of-type(7) {
        width: 8px;
        height: 8px;
        background: #4FD0E3;
        border-radius: 50%;
        transform-origin: 220px 0;
        animation: orbit-uranus 84s linear infinite;
    }

    /* Neptune */
    .planet:nth-of-type(8) {
        width: 8px;
        height: 8px;
        background: #4169E1;
        border-radius: 50%;
        transform-origin: 250px 0;
        animation: orbit-neptune 120s linear infinite;
    }

    /* Pluto */
    .planet:nth-of-type(9) {
        width: 3px;
        height: 3px;
        background: #8B7355;
        border-radius: 50%;
        transform-origin: 280px 0;
        animation: orbit-pluto 160s linear infinite;
    }
    
    /* Professional Starfield */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: 
            radial-gradient(1px 1px at 20px 30px, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1px 1px at 40px 70px, rgba(255, 255, 255, 0.2), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1px 1px at 130px 80px, rgba(255, 255, 255, 0.2), transparent),
            radial-gradient(1px 1px at 160px 30px, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1px 1px at 200px 90px, rgba(255, 255, 255, 0.25), transparent),
            radial-gradient(1px 1px at 240px 50px, rgba(255, 255, 255, 0.2), transparent),
            radial-gradient(1px 1px at 280px 120px, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1px 1px at 320px 40px, rgba(255, 255, 255, 0.2), transparent),
            radial-gradient(1px 1px at 360px 90px, rgba(255, 255, 255, 0.25), transparent),
            radial-gradient(1px 1px at 400px 20px, rgba(255, 255, 255, 0.3), transparent),
            radial-gradient(1px 1px at 440px 110px, rgba(255, 255, 255, 0.2), transparent);
        background-repeat: repeat;
        background-size: 500px 200px;
        pointer-events: none;
        z-index: 0;
        opacity: 0.6;
        animation: starTwinkle 8s ease-in-out infinite alternate;
    }
    
    @keyframes starTwinkle {
        0% { opacity: 0.4; }
        100% { opacity: 0.7; }
    }
    
    /* Individual Planet Orbital Animations */
    @keyframes orbit-mercury {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(60px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(60px) rotate(-360deg); }
    }
    
    @keyframes orbit-venus {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(80px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(80px) rotate(-360deg); }
    }
    
    @keyframes orbit-earth {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(100px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(100px) rotate(-360deg); }
    }
    
    @keyframes orbit-mars {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(120px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(120px) rotate(-360deg); }
    }
    
    @keyframes orbit-jupiter {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(160px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(160px) rotate(-360deg); }
    }
    
    @keyframes orbit-saturn {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(190px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(190px) rotate(-360deg); }
    }
    
    @keyframes orbit-uranus {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(220px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(220px) rotate(-360deg); }
    }
    
    @keyframes orbit-neptune {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(250px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(250px) rotate(-360deg); }
    }
    
    @keyframes orbit-pluto {
        0% { transform: translate(-50%, -50%) rotate(0deg) translateX(280px) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg) translateX(280px) rotate(-360deg); }
    }
    
    
    
    
    
    /* Enhanced Input Styling */
    .stTextInput {
        width: 100% !important;
    }
    
    .stTextInput input {
        background: rgba(15, 15, 35, 0.85) !important;
        border: 2px solid rgba(100, 255, 218, 0.3) !important;
        border-radius: 25px !important;
        color: #f8fafc !important;
        padding: 1.5rem 5rem 1.5rem 4rem !important;
        font-size: 1.25rem !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(20px) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-align: left !important;
    }
    
    .stTextInput input:focus {
        border-color: rgba(0, 255, 136, 0.6) !important;
        border-left-color: #00ff88 !important;
        box-shadow: 
            0 0 30px rgba(0, 255, 136, 0.3),
            0 15px 50px rgba(0, 0, 0, 0.4) !important;
        outline: none !important;
        transform: translateY(-2px) !important;
        backdrop-filter: blur(25px) !important;
    }
    
    .stTextInput input:hover {
        border-color: rgba(100, 255, 218, 0.5) !important;
        box-shadow: 0 12px 45px rgba(0, 0, 0, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    .stTextInput input::placeholder {
        color: rgba(226, 232, 240, 0.6) !important;
        font-style: italic;
        font-weight: 400 !important;
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
        cursor: pointer !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 
            0 10px 40px rgba(0, 255, 136, 0.3),
            0 5px 20px rgba(0, 0, 0, 0.2) !important;
        position: relative !important;
        overflow: hidden !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 
            0 15px 50px rgba(0, 255, 136, 0.4),
            0 8px 30px rgba(0, 0, 0, 0.3) !important;
        background: linear-gradient(135deg, 
            rgba(0, 255, 136, 1) 0%, 
            rgba(100, 255, 218, 0.9) 50%, 
            rgba(0, 255, 136, 1) 100%) !important;
    }
    
    .stButton button:active {
        transform: translateY(-1px) scale(0.98) !important;
        transition: all 0.1s ease !important;
    }
    
    /* Result Cards */
    .result-card {
        background: rgba(15, 15, 35, 0.85);
        border: 1px solid rgba(100, 255, 218, 0.25);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 10px 40px rgba(0, 0, 0, 0.3),
            0 0 60px rgba(100, 255, 218, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        border-left: 4px solid transparent;
    }
    
    .result-card:hover {
        border-color: rgba(0, 255, 136, 0.4);
        border-left-color: #00ff88;
        transform: translateY(-6px) scale(1.02);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.4),
            0 0 80px rgba(0, 255, 136, 0.2);
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
        position: relative;
        overflow: hidden;
        border-left: 6px solid #00ff88;
    }
    
    .ai-response-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .ai-response-content {
        color: #e2e8f0;
        line-height: 1.8;
        font-size: 1.125rem;
        font-weight: 400;
    }
    
    /* Basic Mode Styling */
    .ai-response-container.basic-mode {
        background: rgba(255, 193, 7, 0.1);
        border: 2px solid rgba(255, 193, 7, 0.4);
        border-radius: 25px;
        padding: 2.5rem;
        margin: 2rem 0;
        border-left: 6px solid #ffc107;
    }
    
    .ai-response-container.basic-mode .ai-response-header {
        color: #ffc107;
    }
    
    .ai-response-container.basic-mode .response-indicator.basic {
        background: #ffc107;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .ai-response-container.basic-mode .response-footer {
        color: #ffc107;
        font-size: 0.9rem;
        margin-top: 1rem;
        text-align: center;
        opacity: 0.8;
    }
    
    /* System Error Styling */
    .system-error {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 60vh;
        padding: 2rem;
    }
    
    .error-container {
        background: rgba(15, 15, 35, 0.9);
        border: 2px solid rgba(255, 107, 107, 0.4);
        border-radius: 25px;
        padding: 3rem;
        max-width: 600px;
        text-align: center;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.4),
            0 0 80px rgba(255, 107, 107, 0.1);
    }
    
    .error-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .error-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ff6b6b;
        margin-bottom: 1rem;
    }
    
    .error-message {
        font-size: 1.2rem;
        color: #e1e8ed;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    .error-details {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: left;
    }
    
    .error-details p {
        margin: 0.5rem 0;
        color: #cbd5e0;
    }
    
    .error-details code {
        background: rgba(100, 255, 218, 0.1);
        border: 1px solid rgba(100, 255, 218, 0.3);
        border-radius: 8px;
        padding: 0.8rem;
        display: block;
        margin: 1rem 0;
        color: #64ffda;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
    }
    
    .error-note {
        font-size: 1rem;
        color: #a0aec0;
        font-style: italic;
        margin-top: 1.5rem;
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
        text-shadow: 0 0 30px rgba(100, 255, 218, 0.3);
        animation: gradientShift 4s ease-in-out infinite alternate, titleGlow 3s ease-in-out infinite alternate;
        letter-spacing: 2px;
        line-height: 1.1;
    }
    
    .app-subtitle {
        font-size: 1.5rem;
        font-weight: 500;
        color: #e2e8f0;
        margin-bottom: 1rem;
        opacity: 0.9;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
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

    /* CSS Animations */
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    
    @keyframes titleGlow {
        0% { text-shadow: 0 0 20px rgba(100, 255, 218, 0.2); }
        100% { text-shadow: 0 0 40px rgba(100, 255, 218, 0.5); }
    }
    
    @keyframes animate-fade-in {
        0% { 
            opacity: 0; 
            transform: translateY(30px); 
        }
        100% { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    @keyframes animate-slide-up {
        0% { 
            opacity: 0; 
            transform: translateY(50px); 
        }
        100% { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .animate-fade-in {
        animation: animate-fade-in 1.2s ease-out forwards;
    }
    
    .animate-slide-up {
        animation: animate-slide-up 1s ease-out forwards;
    }

    /* Professional Token Display */
    .token-display {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(100, 255, 218, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 10px 30px rgba(0, 0, 0, 0.3),
            0 0 40px rgba(100, 255, 218, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .token-display:hover {
        transform: translateY(-5px);
        border-color: rgba(100, 255, 218, 0.5);
        box-shadow: 
            0 15px 40px rgba(0, 0, 0, 0.4),
            0 0 60px rgba(100, 255, 218, 0.2);
    }
    
    .token-display::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(100, 255, 218, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .token-display:hover::before {
        left: 100%;
    }
    
    .token-number {
        display: block;
        font-size: 2rem;
        font-weight: 700;
        color: #64ffda;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
    }
    
    .token-label {
        display: block;
        font-size: 0.9rem;
        font-weight: 500;
        color: #cbd5e0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Query Container Styling */
    .query-container {
        padding: 2rem 0;
        position: relative;
        z-index: 10;
    }
    
    .query-wrapper {
        max-width: 800px;
        margin: 0 auto;
        position: relative;
    }
    
    .search-icon {
        position: absolute;
        left: 1.5rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5rem;
        z-index: 20;
        pointer-events: none;
    }

    /* Hide Streamlit elements */
    .stDeployButton { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .stTextInput input {
            padding: 1.25rem 3rem 1.25rem 2.5rem !important;
            font-size: 1rem !important;
        }
        
        .stButton button {
            padding: 1rem 2rem !important;
            font-size: 1rem !important;
        }
        
        .result-card {
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 16px;
        }
        
        .ai-response {
            padding: 2rem 1.5rem;
            border-radius: 20px;
        }
        
        .stApp::before {
            width: 20px;
            height: 20px;
            box-shadow: 
                0 0 20px rgba(255, 215, 0, 0.6),
                0 0 40px rgba(255, 215, 0, 0.3);
        }
        
        .planet:nth-of-type(1) { transform-origin: 40px 0; }
        .planet:nth-of-type(2) { transform-origin: 55px 0; }
        .planet:nth-of-type(3) { transform-origin: 70px 0; }
        .planet:nth-of-type(4) { transform-origin: 85px 0; }
        .planet:nth-of-type(5) { 
            transform-origin: 110px 0;
            width: 10px;
            height: 10px;
        }
        .planet:nth-of-type(6) { 
            transform-origin: 130px 0;
            width: 8px;
            height: 8px;
        }
        .planet:nth-of-type(7) { transform-origin: 150px 0; }
        .planet:nth-of-type(8) { transform-origin: 170px 0; }
        .planet:nth-of-type(9) { transform-origin: 190px 0; }
        
        .error-container {
            padding: 2rem 1.5rem;
            margin: 1rem;
            max-width: 90%;
        }
        
        .error-title {
            font-size: 1.5rem;
        }
        
        .error-message {
            font-size: 1rem;
        }
        
        .app-title {
            font-size: 2.5rem;
            letter-spacing: 1px;
        }
        
        .app-subtitle {
            font-size: 1.2rem;
        }
        
        .header-description {
            font-size: 1rem;
        }
        
        .main-header {
            padding: 2rem 1rem;
        }
        
        .token-display {
            padding: 1rem;
        }
        
        .token-number {
            font-size: 1.5rem;
        }
    }
    
    @media (max-width: 480px) {
        .stTextInput input {
            padding: 1rem 2rem !important;
            font-size: 0.875rem !important;
        }
        
        .stButton button {
            padding: 0.875rem 1.5rem !important;
            font-size: 0.875rem !important;
        }
        
        .result-card, .ai-response {
            margin: 0.75rem 0;
        }
        
        .stApp::before {
            width: 15px;
            height: 15px;
            box-shadow: 
                0 0 15px rgba(255, 215, 0, 0.4),
                0 0 30px rgba(255, 215, 0, 0.2);
        }
        
        .planet:nth-of-type(1) { transform-origin: 30px 0; width: 3px; height: 3px; }
        .planet:nth-of-type(2) { transform-origin: 40px 0; width: 4px; height: 4px; }
        .planet:nth-of-type(3) { transform-origin: 50px 0; width: 5px; height: 5px; }
        .planet:nth-of-type(4) { transform-origin: 60px 0; width: 4px; height: 4px; }
        .planet:nth-of-type(5) { 
            transform-origin: 80px 0;
            width: 8px;
            height: 8px;
        }
        .planet:nth-of-type(6) { 
            transform-origin: 95px 0;
            width: 6px;
            height: 6px;
        }
        .planet:nth-of-type(7) { transform-origin: 110px 0; width: 5px; height: 5px; }
        .planet:nth-of-type(8) { transform-origin: 125px 0; width: 5px; height: 5px; }
        .planet:nth-of-type(9) { transform-origin: 140px 0; width: 2px; height: 2px; }
        
        .error-container {
            padding: 1.5rem 1rem;
            margin: 0.5rem;
            max-width: 95%;
        }
        
        .error-icon {
            font-size: 2rem;
        }
        
        .error-title {
            font-size: 1.3rem;
        }
        
        .error-message {
            font-size: 0.9rem;
        }
        
        .error-details code {
            font-size: 0.8rem;
            padding: 0.6rem;
        }
        
        .app-title {
            font-size: 2rem;
            letter-spacing: 0.5px;
        }
        
        .app-subtitle {
            font-size: 1rem;
        }
        
        .header-description {
            font-size: 0.9rem;
        }
        
        .main-header {
            padding: 1.5rem 0.5rem;
        }
        
        .token-display {
            padding: 0.8rem;
        }
        
        .token-number {
            font-size: 1.2rem;
        }
        
        .token-label {
            font-size: 0.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class IntelliSearch:
    """Enhanced Professional RAG System with Advanced UI"""
    
    def __init__(self):
        self.rag_system = None
        self.ollama_available = False
        self.openai_client = None
        self.is_initialized = False
        
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
        """Render space-themed header"""
        # Add solar system planets to the page
        st.markdown("""
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        <div class="planet"></div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="main-header animate-fade-in">
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
                <div class="token-display">
                    <span class="token-number">{self.token_metrics['query_tokens']}</span>
                    <span class="token-label">Query Tokens</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="token-display">
                    <span class="token-number">{self.token_metrics['response_tokens']}</span>
                    <span class="token-label">Response Tokens</span>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="token-display">
                    <span class="token-number">{self.token_metrics['session_tokens']}</span>
                    <span class="token-label">Session Total</span>
                </div>
                """, unsafe_allow_html=True)
    
    def render_search_results(self, rag_result: Dict[str, Any]):
        """Render search results with enhanced animations"""
        strategy = rag_result.get('search_strategy', 'unknown')
        local_results = rag_result.get('local_results', [])
        web_results = rag_result.get('web_results', [])
        
        # Enhanced search strategy indicator with animations
        if strategy == 'local_database':
            st.markdown(f"""
            <div class="search-strategy">
                <div class="strategy-indicator strategy-local animate-slide-in">
                    <span class="strategy-icon">🔍</span>
                    <span class="strategy-text">
                        Found <span class="result-count animate-counter">{len(local_results)}</span> 
                        relevant articles
                    </span>
                    <div class="strategy-bar local-bar"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif strategy == 'web_fallback':
            st.markdown(f"""
            <div class="search-strategy">
                <div class="strategy-indicator strategy-web animate-slide-in">
                    <span class="strategy-icon">🌐</span>
                    <span class="strategy-text">
                        Retrieved <span class="result-count animate-counter">{len(web_results)}</span> 
                        external sources
                    </span>
                    <div class="strategy-bar web-bar"></div>
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
    
    async def handle_basic_query(self, user_question: str):
        """Handle queries in basic mode when full RAG is unavailable"""
        # Show processing indicator
        processing_placeholder = st.empty()
        processing_placeholder.markdown("""
        <div class="processing-container">
            <div class="processing-indicator">
                <span class="processing-icon">🔍</span>
                <span>Processing in Basic Mode...</span>
                <div class="processing-dots">
                    <span class="dot dot-1"></span>
                    <span class="dot dot-2"></span>
                    <span class="dot dot-3"></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Provide basic response with helpful information
            basic_response = f"""
            **Basic Mode Response for: "{user_question}"**
            
            🔍 **Current Status**: Running in Basic Mode
            
            📝 **Your Query**: {user_question}
            
            ⚠️ **Limited Functionality**: Advanced RAG features are currently unavailable, but here's what I can tell you:
            
            🌟 **Suggestions**:
            - Try rephrasing your question for better web search results
            - Check if you're looking for general information that might be available online
            - Consider the query context and related topics
            
            🔧 **To Enable Full Features**: The system needs additional AI packages for advanced search and retrieval capabilities.
            
            💡 **Alternative**: You can try searching the web directly for: "{user_question}"
            """
            
            processing_placeholder.empty()
            
            # Display the basic response with nice formatting
            st.markdown("""
            <div class="ai-response-container basic-mode">
                <div class="ai-response-header">
                    <span class="response-icon">🔍</span>
                    <span class="response-title">Basic Mode Response</span>
                    <div class="response-indicator basic"></div>
                </div>
                <div class="ai-response-content">
                    """ + basic_response.replace('\n', '<br>') + """
                </div>
                <div class="response-footer">
                    <span class="powered-by">Basic Mode - Limited Functionality</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            processing_placeholder.empty()
            st.error(f"Error in basic mode: {str(e)}")
    
    async def process_query(self, user_question: str):
        """Process user query with enhanced loading states"""
        if not self.is_initialized:
            # Handle degraded mode - provide basic functionality
            await self.handle_basic_query(user_question)
            return
        
        # Enhanced processing indicator
        processing_placeholder = st.empty()
        processing_placeholder.markdown("""
        <div class="processing-container">
            <div class="processing-indicator">
                <span class="processing-icon">⚡</span>
                <span>Processing your query...</span>
                <div class="processing-dots">
                    <span class="dot dot-1"></span>
                    <span class="dot dot-2"></span>
                    <span class="dot dot-3"></span>
                </div>
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
            query_time = end_time - start_time
            self.performance_metrics['total_queries'] += 1
            self.performance_metrics['avg_response_time'] = (
                (self.performance_metrics['avg_response_time'] * (self.performance_metrics['total_queries'] - 1) + query_time) /
                self.performance_metrics['total_queries']
            )
            
            # Add to query history
            self.query_history.append({
                'query': user_question,
                'timestamp': time.time(),
                'response_time': query_time
            })
            
            # Clear processing indicator
            processing_placeholder.empty()
            
            # Display results with animation
            self.render_search_results(rag_result)
            
            # Generate response
            if rag_result.get('ready_for_llm'):
                await self.generate_response(rag_result)
                
        except Exception as e:
            processing_placeholder.empty()
            # Update failure rate
            self.performance_metrics['success_rate'] = max(0, self.performance_metrics['success_rate'] - 5)
            st.error(f"Query processing failed: {str(e)}")
    
    async def generate_response(self, rag_result: Dict[str, Any]):
        """Generate and display AI response with typing animation"""
        context_window = rag_result.get('context_window', '')
        
        # Enhanced response generation indicator
        response_placeholder = st.empty()
        response_placeholder.markdown("""
        <div class="response-generating">
            <div class="ai-thinking">
                <span class="ai-icon">🤖</span>
                <span class="thinking-text">Generating intelligent response</span>
                <div class="thinking-animation">
                    <span class="brain-wave"></span>
                    <span class="brain-wave"></span>
                    <span class="brain-wave"></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            ai_response = await self.get_llm_response(context_window)
            
            # Clear generating indicator
            response_placeholder.empty()
            
            # Display response with enhanced styling and typing effect
            st.markdown(f"""
            <div class="ai-response animate-fade-in">
                <div class="ai-response-header">
                    <span class="response-icon">💡</span>
                    <span class="response-title">Intelligent Response</span>
                    <div class="response-indicator"></div>
                </div>
                <div class="ai-response-content typing-animation">
                    {ai_response.replace(chr(10), '<br>')}
                </div>
                <div class="response-footer">
                    <span class="powered-by">Powered by Advanced RAG System</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            response_placeholder.empty()
            st.error(f"Response generation failed: {str(e)}")
    
    async def run(self):
        """Main application interface"""
        self.render_header()
        
        # Enhanced system initialization
        if not self.is_initialized and RAG_AVAILABLE:
            init_placeholder = st.empty()
            init_placeholder.markdown("""
            <div class="system-initializing">
                <div class="init-container">
                    <div class="init-icon">⚡</div>
                    <div class="init-text">Initializing IntelliSearch System</div>
                    <div class="init-progress">
                        <div class="progress-bar"></div>
                    </div>
                    <div class="init-details">Loading advanced RAG capabilities...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            success = await self.initialize_rag_system()
            init_placeholder.empty()
            
            if not success:
                st.warning("⚠️ Running in Basic Mode - Advanced RAG features unavailable")
                self.is_initialized = False  # Set degraded mode flag
                
            # Success animation
            st.markdown("""
            <div class="system-ready animate-success">
                <div class="ready-icon">✨</div>
                <div class="ready-text">IntelliSearch System Ready</div>
                <div class="ready-subtext">Advanced RAG capabilities activated</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Small delay for visual effect
            import time
            time.sleep(1)
            st.rerun()
        
        # Show system status information (but don't block the interface)
        if not self.is_initialized:
            if not RAG_AVAILABLE:
                st.info("🌟 **Basic Mode Active** - Core search functionality available. Advanced RAG features are temporarily unavailable due to missing dependencies.")
            else:
                st.warning("⚠️ **Basic Mode Active** - Some advanced features may be limited. You can still use basic search functionality.")
        
        # Enhanced main query interface with perfect centering
        st.markdown('<div class="query-container animate-slide-up"><div class="query-wrapper"><div class="search-icon">🚀</div>', unsafe_allow_html=True)
        
        # Query input with enhanced styling
        user_question = st.text_input(
            "Search Query",
            placeholder="🔍 Enter your query to search across knowledge base and web sources...",
            help="Submit queries for intelligent information retrieval using advanced RAG techniques",
            label_visibility="collapsed",
            key="main_search_input"
        )
        
        # Enhanced button layout with perfect centering
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            query_button = st.button(
                "🚀 Search Intelligence", 
                type="primary",
                help="Execute advanced semantic search",
                use_container_width=True
            )
        
        # Add user guidance and instructions (removed welcome message)
        
        # How to use button
        with st.expander("📚 How to Use This System"):
            st.markdown("""
                    ### Getting Started
                    1. **Ask Questions**: Enter your query in the search box above
                    2. **Be Specific**: More detailed questions get better answers
                    3. **Explore Topics**: Try space, technology, recruitment, or scientific concepts
                    
                    ### System Capabilities
                    - **Multi-Source Search**: Searches both local knowledge bases and web sources
                    - **Space Intelligence**: Specialized in space exploration and astronomy
                    - **Technical Analysis**: Handles complex scientific and technical queries
                    - **Recruitment Insights**: Provides career and skill-related information
                    
                    ### Tips for Best Results
                    - Use natural language - ask as you would ask a human expert
                    - Include context when relevant (e.g., "for beginners" or "technical details")
                    - Ask follow-up questions to dive deeper into topics
                    """)
        
        st.markdown('</div></div></div>', unsafe_allow_html=True)
        
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