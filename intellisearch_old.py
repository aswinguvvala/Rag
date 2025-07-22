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

# Enhanced professional CSS with clean animated background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;600;700&display=swap');
    
    /* Clean Space Background */
    .stApp {
        background: linear-gradient(180deg, #000511 0%, #001122 20%, #002244 40%, #003366 60%, #001a33 80%, #000000 100%);
        background-attachment: fixed;
        color: #e1e8ed;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
        padding-bottom: 2rem;
    }
    
    /* Simple Star Field Background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: 
            radial-gradient(1px 1px at 20px 30px, rgba(255,255,255,0.8), transparent 2px),
            radial-gradient(1px 1px at 90px 40px, rgba(135,206,250,0.6), transparent 2px),
            radial-gradient(1px 1px at 200px 90px, rgba(255,255,255,0.7), transparent 2px),
            radial-gradient(1px 1px at 320px 120px, rgba(173,216,230,0.5), transparent 2px);
        background-repeat: repeat;
        background-size: 400px 300px;
        animation: starTwinkle 8s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: -1;
        opacity: 0.6;
    }
    
    /* Simple floating elements */
    .stApp::after {
        content: '✦ ⭐ ★ ✦ ⭐ ★';
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        font-size: 0.8em;
        color: rgba(255, 255, 255, 0.03);
        white-space: pre-wrap;
        word-spacing: 120px;
        line-height: 8;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }
    
    @keyframes starTwinkle {
        0% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    
    /* Clean Space Background */
    .space-background-simple {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        pointer-events: none;
        z-index: -2;
        overflow: hidden;
        background: linear-gradient(180deg, #000428 0%, #004e92 50%, #000000 100%);
        
        /* Simple Starfield */
        background-image: 
            radial-gradient(1px 1px at 20px 30px, rgba(255,255,255,0.9), transparent),
            radial-gradient(1px 1px at 40px 70px, rgba(255,255,255,0.7), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.8), transparent),
            radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
            radial-gradient(1px 1px at 200px 120px, rgba(255,255,255,0.9), transparent),
            radial-gradient(1px 1px at 350px 80px, rgba(255,255,255,0.7), transparent);
        background-repeat: repeat;
        background-size: 400px 300px;
        animation: starTwinkle 6s ease-in-out infinite alternate;
    }
    
    /* Solar System using CSS box-shadow */
    .space-background-simple::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 16px;
        height: 16px;
        background: radial-gradient(circle, #FFD700 0%, #FFA500 50%, #FF6347 100%);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 
            /* Sun glow */
            0 0 30px rgba(255, 215, 0, 0.8),
            0 0 60px rgba(255, 165, 0, 0.4),
            /* Mercury */
            50px 10px 0 -6px #8C7853,
            /* Venus */
            -70px -20px 0 -4px #FFC649,
            /* Earth */
            30px -90px 0 -3px #4A90E2,
            /* Mars */
            100px 60px 0 -5px #CD5C5C,
            /* Jupiter */
            -130px 80px 0 2px #D2691E,
            /* Saturn */
            150px -70px 0 0px #FAD5A5,
            /* Uranus */
            -180px -30px 0 -4px #4FD0E3,
            /* Neptune */
            200px 20px 0 -4px #4169E1,
            /* Pluto */
            -90px 150px 0 -7px #8B7355;
        animation: solarOrbit 100s linear infinite, solarPulse 8s ease-in-out infinite alternate;
    }
    
    /* Orbital rings */
    .space-background-simple::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 250px;
        height: 250px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 
            0 0 0 50px rgba(255, 255, 255, 0.05),
            0 0 0 100px rgba(255, 255, 255, 0.03),
            0 0 0 150px rgba(255, 255, 255, 0.02);
        animation: orbitRings 80s linear infinite;
    }
    
    /* Clean Animations */
    
    @keyframes solarOrbit {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    
    @keyframes solarPulse {
        0% { filter: brightness(1); }
        100% { filter: brightness(1.2); }
    }
    
    @keyframes orbitRings {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    
    /* Enhanced Input Styling with Perfect Balance */
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
    
    .black-hole {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 60px;
        height: 60px;
        background: radial-gradient(circle, transparent 30%, rgba(0, 0, 0, 0.9) 31%, #000000 100%);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 
            0 0 40px rgba(138, 43, 226, 0.6),
            0 0 80px rgba(75, 0, 130, 0.4),
            inset 0 0 20px rgba(0, 0, 0, 1);
        animation: blackHoleSpin 8s linear infinite;
    }
    
    .accretion-disk {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 120px;
        height: 120px;
        background: conic-gradient(
            from 0deg,
            transparent 0%,
            rgba(138, 43, 226, 0.4) 10%,
            rgba(255, 20, 147, 0.6) 25%,
            rgba(255, 69, 0, 0.5) 40%,
            rgba(255, 165, 0, 0.3) 60%,
            rgba(138, 43, 226, 0.4) 75%,
            rgba(255, 20, 147, 0.5) 90%,
            transparent 100%
        );
        border-radius: 50%;
        transform: translate(-50%, -50%);
        animation: accretionSpin 4s linear infinite;
    }
    
    /* Nebula Effect */
    .nebula-container {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 400px;
        height: 400px;
        transform: translate(-50%, -50%);
        opacity: 0;
        transition: opacity 1s ease-in-out;
    }
    
    .nebula {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(
            ellipse at center,
            rgba(255, 20, 147, 0.3) 0%,
            rgba(138, 43, 226, 0.25) 30%,
            rgba(75, 0, 130, 0.15) 60%,
            transparent 80%
        );
        border-radius: 60% 40% 30% 70%;
        animation: nebulaFloat 20s ease-in-out infinite;
        filter: blur(3px);
    }
    
    @keyframes blackHoleSpin {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    
    @keyframes accretionSpin {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    
    @keyframes nebulaFloat {
        0% { 
            transform: translate(-50%, -50%) rotate(0deg) scale(1);
            filter: blur(3px) hue-rotate(0deg);
        }
        50% { 
            transform: translate(-50%, -50%) rotate(5deg) scale(1.1);
            filter: blur(4px) hue-rotate(30deg);
        }
        100% { 
            transform: translate(-50%, -50%) rotate(0deg) scale(1);
            filter: blur(3px) hue-rotate(0deg);
        }
    }
    
    /* Animation Cycle Control */
    .space-background {
        animation: backgroundCycle 45s infinite;
    }
    
    @keyframes backgroundCycle {
        0% { }
        33.33% { }  /* Solar System visible */
        33.34% { }  /* Transition to Black Hole */
        66.66% { }  /* Black Hole visible */
        66.67% { }  /* Transition to Nebula */
        99.99% { }  /* Nebula visible */
        100% { }    /* Return to Solar System */
    }
    
    /* Responsive starfield adjustments */
    @media (max-width: 768px) {
        .starfield-layer-1, .starfield-layer-2, .starfield-layer-3 {
            background-size: 150px 75px, 200px 100px, 250px 125px;
            animation-duration: 6s, 8s, 10s;
        }
    }
    
    @media (max-width: 480px) {
        .starfield-layer-1, .starfield-layer-2, .starfield-layer-3 {
            background-size: 100px 50px, 150px 75px, 200px 100px;
            opacity: 0.8, 0.6, 0.4;
        }
    }
    
    
    
    
    
    
    
    .nebula-1 {
        top: 20%;
        left: -10%;
        width: 400px;
        height: 300px;
        background: radial-gradient(
            ellipse at center,
            rgba(255, 20, 147, 0.3) 0%,
            rgba(138, 43, 226, 0.25) 30%,
            rgba(75, 0, 130, 0.15) 60%,
            transparent 80%
        );
        animation: nebulaFlow1 25s ease-in-out infinite, nebulaPulse 8s ease-in-out infinite alternate;
    }
    
    .nebula-2 {
        top: 60%;
        right: -15%;
        width: 350px;
        height: 280px;
        background: radial-gradient(
            ellipse at center,
            rgba(0, 191, 255, 0.25) 0%,
            rgba(135, 206, 250, 0.2) 40%,
            rgba(173, 216, 230, 0.15) 70%,
            transparent 90%
        );
        animation: nebulaFlow2 30s ease-in-out infinite, nebulaPulse 10s ease-in-out infinite alternate;
    }
    
    .nebula-3 {
        bottom: 10%;
        left: 30%;
        width: 500px;
        height: 200px;
        background: radial-gradient(
            ellipse at center,
            rgba(50, 205, 50, 0.2) 0%,
            rgba(173, 255, 47, 0.15) 50%,
            rgba(255, 215, 0, 0.1) 80%,
            transparent 100%
        );
        animation: nebulaFlow3 35s ease-in-out infinite, nebulaPulse 12s ease-in-out infinite alternate;
    }
    
    .nebula-4 {
        top: 5%;
        left: 60%;
        width: 300px;
        height: 250px;
        background: radial-gradient(
            ellipse at center,
            rgba(255, 165, 0, 0.2) 0%,
            rgba(255, 69, 0, 0.15) 40%,
            rgba(220, 20, 60, 0.1) 70%,
            transparent 90%
        );
        animation: nebulaFlow4 22s ease-in-out infinite, nebulaPulse 9s ease-in-out infinite alternate;
    }
    
    /* COSMIC DUST LAYERS */
    .cosmic-dust {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: -5;
        opacity: 0.1;
    }
    
    .dust-layer-1 {
        background-image: 
            radial-gradient(1px 1px at 20px 30px, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 40px 70px, rgba(255,255,255,0.2), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.3), transparent),
            radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.2), transparent);
        background-repeat: repeat;
        background-size: 200px 200px;
        animation: dustDrift1 40s linear infinite;
    }
    
    .dust-layer-2 {
        background-image: 
            radial-gradient(0.5px 0.5px at 60px 120px, rgba(135,206,250,0.2), transparent),
            radial-gradient(0.5px 0.5px at 180px 100px, rgba(173,216,230,0.15), transparent),
            radial-gradient(0.5px 0.5px at 240px 50px, rgba(255,255,255,0.1), transparent);
        background-repeat: repeat;
        background-size: 300px 300px;
        animation: dustDrift2 60s linear infinite;
    }
    
    /* Aurora Animations */
    @keyframes auroraWave1 {
        0% { 
            transform: translateY(0px) scale(1) rotate(0deg);
            opacity: 0.3;
        }
        25% { 
            transform: translateY(-20px) scale(1.1) rotate(5deg);
            opacity: 0.5;
        }
        50% { 
            transform: translateY(-10px) scale(0.9) rotate(-3deg);
            opacity: 0.4;
        }
        75% { 
            transform: translateY(-30px) scale(1.2) rotate(8deg);
            opacity: 0.6;
        }
        100% { 
            transform: translateY(-15px) scale(1.05) rotate(-2deg);
            opacity: 0.4;
        }
    }
    
    @keyframes auroraWave2 {
        0% { 
            transform: translateX(0px) scale(1) rotate(0deg);
            opacity: 0.25;
        }
        33% { 
            transform: translateX(-15px) scale(1.1) rotate(-4deg);
            opacity: 0.4;
        }
        66% { 
            transform: translateX(10px) scale(0.95) rotate(6deg);
            opacity: 0.3;
        }
        100% { 
            transform: translateX(-5px) scale(1.08) rotate(-2deg);
            opacity: 0.35;
        }
    }
    
    @keyframes auroraWave3 {
        0% { 
            transform: translateY(0px) translateX(0px) scale(1);
            opacity: 0.2;
        }
        50% { 
            transform: translateY(-25px) translateX(15px) scale(1.15);
            opacity: 0.45;
        }
        100% { 
            transform: translateY(-10px) translateX(-8px) scale(1.05);
            opacity: 0.3;
        }
    }
    
    @keyframes auroraWave4 {
        0% { 
            transform: translateX(0px) scale(1) rotate(0deg);
            opacity: 0.25;
        }
        40% { 
            transform: translateX(20px) scale(1.2) rotate(3deg);
            opacity: 0.4;
        }
        80% { 
            transform: translateX(-10px) scale(0.9) rotate(-5deg);
            opacity: 0.3;
        }
        100% { 
            transform: translateX(5px) scale(1.1) rotate(1deg);
            opacity: 0.35;
        }
    }
    
    /* Nebula Animations */
    @keyframes nebulaFlow1 {
        0% { transform: translateX(-100px) translateY(0px) rotate(0deg); }
        25% { transform: translateX(-50px) translateY(-30px) rotate(90deg); }
        50% { transform: translateX(50px) translateY(-15px) rotate(180deg); }
        75% { transform: translateX(0px) translateY(-45px) rotate(270deg); }
        100% { transform: translateX(-100px) translateY(0px) rotate(360deg); }
    }
    
    @keyframes nebulaFlow2 {
        0% { transform: translateX(100px) translateY(0px) rotate(0deg); }
        33% { transform: translateX(50px) translateY(40px) rotate(120deg); }
        66% { transform: translateX(-30px) translateY(20px) rotate(240deg); }
        100% { transform: translateX(100px) translateY(0px) rotate(360deg); }
    }
    
    @keyframes nebulaFlow3 {
        0% { transform: translateX(0px) translateY(50px) rotate(0deg); }
        50% { transform: translateX(80px) translateY(-20px) rotate(180deg); }
        100% { transform: translateX(0px) translateY(50px) rotate(360deg); }
    }
    
    @keyframes nebulaFlow4 {
        0% { transform: translateY(0px) rotate(0deg) scale(1); }
        30% { transform: translateY(-40px) rotate(108deg) scale(1.1); }
        70% { transform: translateY(20px) rotate(252deg) scale(0.9); }
        100% { transform: translateY(0px) rotate(360deg) scale(1); }
    }
    
    @keyframes nebulaPulse {
        0% { 
            filter: blur(8px) brightness(1);
            opacity: 0.15;
        }
        50% { 
            filter: blur(12px) brightness(1.3);
            opacity: 0.25;
        }
        100% { 
            filter: blur(8px) brightness(1);
            opacity: 0.2;
        }
    }
    
    /* Cosmic Dust Animations */
    @keyframes dustDrift1 {
        0% { transform: translateX(0px) translateY(0px); }
        100% { transform: translateX(-200px) translateY(-100px); }
    }
    
    @keyframes dustDrift2 {
        0% { transform: translateX(0px) translateY(0px); }
        100% { transform: translateX(-300px) translateY(50px); }
    }
    
    /* PULSAR ANIMATIONS */
    .pulsar {
        position: fixed;
        width: 12px;
        height: 12px;
        background: radial-gradient(circle, #ffffff 0%, #87ceeb 40%, #4682b4 80%, transparent 100%);
        border-radius: 50%;
        pointer-events: none;
        z-index: -3;
        box-shadow: 
            0 0 20px rgba(255, 255, 255, 0.8),
            0 0 40px rgba(135, 206, 235, 0.6),
            0 0 60px rgba(70, 130, 180, 0.4);
    }
    
    .pulsar-1 {
        top: 25%;
        left: 15%;
        animation: pulsarSpin 3s linear infinite, pulsarPulse 1.5s ease-in-out infinite;
    }
    
    .pulsar-2 {
        top: 70%;
        right: 20%;
        animation: pulsarSpin 2.2s linear infinite, pulsarPulse 1.8s ease-in-out infinite;
    }
    
    .pulsar-3 {
        bottom: 30%;
        left: 35%;
        animation: pulsarSpin 2.8s linear infinite, pulsarPulse 1.2s ease-in-out infinite;
    }
    
    /* Pulsar Light Beams */
    .pulsar::before {
        content: '';
        position: absolute;
        top: -100px;
        left: 50%;
        width: 2px;
        height: 200px;
        background: linear-gradient(
            0deg,
            transparent 0%,
            rgba(255, 255, 255, 0.3) 20%,
            rgba(135, 206, 235, 0.6) 50%,
            rgba(255, 255, 255, 0.3) 80%,
            transparent 100%
        );
        transform: translateX(-50%);
        filter: blur(1px);
        animation: pulsarBeamPulse 1.5s ease-in-out infinite;
    }
    
    .pulsar::after {
        content: '';
        position: absolute;
        top: -100px;
        left: 50%;
        width: 2px;
        height: 200px;
        background: linear-gradient(
            0deg,
            transparent 0%,
            rgba(255, 255, 255, 0.2) 30%,
            rgba(70, 130, 180, 0.4) 50%,
            rgba(255, 255, 255, 0.2) 70%,
            transparent 100%
        );
        transform: translateX(-50%) rotate(90deg);
        filter: blur(1px);
        animation: pulsarBeamPulse 1.5s ease-in-out infinite 0.75s;
    }
    
    /* BLACK HOLE EFFECTS */
    .black-hole {
        position: fixed;
        width: 60px;
        height: 60px;
        background: 
            radial-gradient(circle at center, 
                transparent 0%, 
                transparent 30%, 
                rgba(0, 0, 0, 0.9) 35%, 
                #000000 40%, 
                #000000 60%, 
                rgba(30, 30, 30, 0.8) 65%, 
                rgba(70, 70, 70, 0.3) 80%, 
                transparent 100%
            );
        border-radius: 50%;
        pointer-events: none;
        z-index: -3;
        filter: blur(2px);
    }
    
    .black-hole-1 {
        top: 15%;
        right: 25%;
        animation: blackHoleSpin 20s linear infinite, blackHolePulse 8s ease-in-out infinite;
    }
    
    .black-hole-2 {
        bottom: 40%;
        left: 25%;
        animation: blackHoleSpin 25s linear infinite reverse, blackHolePulse 10s ease-in-out infinite;
    }
    
    /* Accretion Disk */
    .black-hole::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 120px;
        height: 120px;
        background: 
            radial-gradient(ellipse at center,
                transparent 25%,
                rgba(255, 165, 0, 0.3) 35%,
                rgba(255, 69, 0, 0.4) 45%,
                rgba(255, 20, 147, 0.3) 55%,
                rgba(138, 43, 226, 0.2) 65%,
                transparent 75%
            );
        border-radius: 50%;
        transform: translate(-50%, -50%);
        animation: accretionDiskSpin 15s linear infinite, accretionDiskWarp 6s ease-in-out infinite;
    }
    
    /* Gravitational Lensing Effect */
    .gravitational-lens {
        position: absolute;
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: 
            radial-gradient(circle at center,
                transparent 0%,
                rgba(255, 255, 255, 0.05) 40%,
                rgba(135, 206, 235, 0.1) 60%,
                rgba(255, 255, 255, 0.03) 80%,
                transparent 100%
            );
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
        animation: gravitationalWave 12s ease-in-out infinite;
        filter: blur(3px);
    }
    
    /* QUANTUM FIELD FLUCTUATIONS */
    .quantum-field {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: -6;
        opacity: 0.05;
        background-image: 
            radial-gradient(2px 2px at 50px 80px, rgba(255,255,255,0.3), transparent 3px),
            radial-gradient(1px 1px at 150px 120px, rgba(135,206,250,0.2), transparent 2px),
            radial-gradient(1px 1px at 250px 60px, rgba(255,255,255,0.4), transparent 2px),
            radial-gradient(3px 3px at 350px 140px, rgba(173,216,230,0.2), transparent 4px);
        background-repeat: repeat;
        background-size: 400px 300px;
        animation: quantumFluctuations 45s ease-in-out infinite;
    }
    
    /* Pulsar Animations */
    @keyframes pulsarSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes pulsarPulse {
        0% { 
            box-shadow: 
                0 0 20px rgba(255, 255, 255, 0.8),
                0 0 40px rgba(135, 206, 235, 0.6),
                0 0 60px rgba(70, 130, 180, 0.4);
            transform: scale(1);
        }
        50% { 
            box-shadow: 
                0 0 30px rgba(255, 255, 255, 1),
                0 0 60px rgba(135, 206, 235, 0.8),
                0 0 90px rgba(70, 130, 180, 0.6);
            transform: scale(1.2);
        }
        100% { 
            box-shadow: 
                0 0 20px rgba(255, 255, 255, 0.8),
                0 0 40px rgba(135, 206, 235, 0.6),
                0 0 60px rgba(70, 130, 180, 0.4);
            transform: scale(1);
        }
    }
    
    @keyframes pulsarBeamPulse {
        0%, 100% { opacity: 0.3; transform: translateX(-50%) scaleY(1); }
        25% { opacity: 0.8; transform: translateX(-50%) scaleY(1.2); }
        50% { opacity: 1; transform: translateX(-50%) scaleY(1.5); }
        75% { opacity: 0.6; transform: translateX(-50%) scaleY(1.1); }
    }
    
    /* Black Hole Animations */
    @keyframes blackHoleSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes blackHolePulse {
        0% { 
            filter: blur(2px) brightness(1);
            transform: scale(1);
        }
        50% { 
            filter: blur(3px) brightness(1.2);
            transform: scale(1.1);
        }
        100% { 
            filter: blur(2px) brightness(1);
            transform: scale(1);
        }
    }
    
    @keyframes accretionDiskSpin {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    
    @keyframes accretionDiskWarp {
        0% { 
            transform: translate(-50%, -50%) scaleY(1) scaleX(1);
            opacity: 0.6;
        }
        25% { 
            transform: translate(-50%, -50%) scaleY(0.8) scaleX(1.2);
            opacity: 0.8;
        }
        50% { 
            transform: translate(-50%, -50%) scaleY(0.6) scaleX(1.4);
            opacity: 1;
        }
        75% { 
            transform: translate(-50%, -50%) scaleY(0.8) scaleX(1.2);
            opacity: 0.8;
        }
        100% { 
            transform: translate(-50%, -50%) scaleY(1) scaleX(1);
            opacity: 0.6;
        }
    }
    
    @keyframes gravitationalWave {
        0% { 
            transform: translate(-50%, -50%) scale(1);
            opacity: 0.1;
        }
        25% { 
            transform: translate(-50%, -50%) scale(1.2);
            opacity: 0.2;
        }
        50% { 
            transform: translate(-50%, -50%) scale(1.5);
            opacity: 0.15;
        }
        75% { 
            transform: translate(-50%, -50%) scale(1.3);
            opacity: 0.18;
        }
        100% { 
            transform: translate(-50%, -50%) scale(1);
            opacity: 0.1;
        }
    }
    
    @keyframes quantumFluctuations {
        0% { 
            transform: translateX(0px) translateY(0px) scale(1);
            opacity: 0.03;
        }
        25% { 
            transform: translateX(-50px) translateY(25px) scale(1.1);
            opacity: 0.07;
        }
        50% { 
            transform: translateX(-20px) translateY(-30px) scale(0.9);
            opacity: 0.05;
        }
        75% { 
            transform: translateX(30px) translateY(15px) scale(1.05);
            opacity: 0.06;
        }
        100% { 
            transform: translateX(0px) translateY(0px) scale(1);
            opacity: 0.03;
        }
    }
    
    /* Comet Trail System - Multiple Comets */
    .comet-trail {
        content: '☄️';
        position: fixed;
        font-size: 1.5rem;
        color: #ffa500;
        pointer-events: none;
        z-index: -1;
        filter: drop-shadow(0 0 15px rgba(255, 165, 0, 0.8)) drop-shadow(10px 0 30px rgba(255, 215, 0, 0.4));
    }
    
    .comet-trail-1 {
        top: 20%;
        left: -100px;
        animation: cometTrail 12s linear infinite;
    }
    
    .comet-trail-2 {
        top: 60%;
        left: -100px;
        animation: cometTrail 15s linear infinite 4s;
    }
    
    .comet-trail-3 {
        top: 40%;
        left: -100px;
        animation: cometTrail 18s linear infinite 8s;
    }
    
    @keyframes cometTrail {
        0% { 
            transform: translateX(-100px) translateY(0) rotate(45deg); 
            opacity: 0;
        }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { 
            transform: translateX(calc(100vw + 100px)) translateY(30vh) rotate(45deg);
            opacity: 0;
        }
    }
    
    /* Satellite Movement System */
    .satellite {
        position: fixed;
        font-size: 1.2rem;
        pointer-events: none;
        z-index: -1;
        opacity: 0.8;
    }
    
    .satellite-1 {
        top: 15%;
        right: -50px;
        animation: satelliteOrbit 25s linear infinite, satelliteGlow 4s ease-in-out infinite;
        filter: drop-shadow(0 0 12px rgba(135, 206, 235, 0.6));
    }
    
    .satellite-2 {
        bottom: 25%;
        left: -50px;
        animation: spacecraftFly 20s linear infinite 5s, spacecraftSpin 8s linear infinite;
        filter: drop-shadow(0 0 10px rgba(255, 165, 0, 0.7));
    }
    
    .satellite-3 {
        top: 70%;
        right: -50px;
        animation: ufoHover 30s linear infinite 10s, ufoWobble 3s ease-in-out infinite;
        filter: drop-shadow(0 0 15px rgba(50, 205, 50, 0.8));
    }
    
    @keyframes satelliteOrbit {
        0% { transform: translateX(50px) translateY(0) rotate(0deg); opacity: 0; }
        10% { opacity: 0.8; }
        50% { transform: translateX(-50vw) translateY(-20vh) rotate(180deg); opacity: 0.9; }
        90% { opacity: 0.8; }
        100% { transform: translateX(calc(-100vw - 50px)) translateY(-40vh) rotate(360deg); opacity: 0; }
    }
    
    @keyframes spacecraftFly {
        0% { transform: translateX(-50px) translateY(0) rotate(-15deg); opacity: 0; }
        10% { opacity: 0.9; }
        90% { opacity: 0.9; }
        100% { transform: translateX(calc(100vw + 50px)) translateY(-15vh) rotate(-15deg); opacity: 0; }
    }
    
    @keyframes ufoHover {
        0% { transform: translateX(50px) translateY(0) rotate(0deg); opacity: 0; }
        10% { opacity: 0.7; }
        25% { transform: translateX(-20vw) translateY(-10vh) rotate(90deg); }
        50% { transform: translateX(-50vw) translateY(10vh) rotate(180deg); }
        75% { transform: translateX(-80vw) translateY(-5vh) rotate(270deg); }
        90% { opacity: 0.7; }
        100% { transform: translateX(calc(-100vw - 50px)) translateY(-20vh) rotate(360deg); opacity: 0; }
    }
    
    @keyframes satelliteGlow {
        0%, 100% { filter: drop-shadow(0 0 12px rgba(135, 206, 235, 0.6)); }
        50% { filter: drop-shadow(0 0 20px rgba(135, 206, 235, 0.9)); }
    }
    
    @keyframes spacecraftSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes ufoWobble {
        0%, 100% { transform: translateY(0px); }
        33% { transform: translateY(-3px); }
        66% { transform: translateY(3px); }
    }
    
    /* Remove Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Header */
    .main-header {
        text-align: center;
        padding: 4rem 0 2rem 0;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
    }
    
    .app-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #87ceeb, #dda0dd, #add8e6, #b0e0e6);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 8s ease-in-out infinite, cosmicGlow 3s ease-in-out infinite alternate;
        text-shadow: 
            0 0 20px rgba(135, 206, 235, 0.8),
            0 0 40px rgba(135, 206, 235, 0.5),
            0 0 60px rgba(135, 206, 235, 0.3);
        position: relative;
    }
    
    .app-title::before {
        content: '';
        position: absolute;
        top: -10px;
        left: -10px;
        right: -10px;
        bottom: -10px;
        background: linear-gradient(135deg, rgba(135,206,235,0.15), rgba(173,216,230,0.15));
        border-radius: 30px;
        z-index: -1;
        filter: blur(25px);
        animation: stellarHalo 4s ease-in-out infinite alternate;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes cosmicGlow {
        0% { filter: drop-shadow(0 0 20px rgba(135, 206, 235, 0.6)); }
        100% { filter: drop-shadow(0 0 50px rgba(173, 216, 230, 0.8)); }
    }
    
    @keyframes stellarHalo {
        0% { transform: scale(0.95); opacity: 0.4; }
        100% { transform: scale(1.08); opacity: 0.7; }
    }
    
    .app-subtitle {
        font-size: 1.25rem;
        color: #b8c5d1;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    .header-description {
        font-size: 1rem;
        color: #9ca8b3;
        font-weight: 300;
        max-width: 500px;
        margin: 0.5rem auto 0;
        line-height: 1.5;
        font-style: italic;
    }
    
    /* User Guidance Section */
    .user-guidance {
        background: rgba(15, 15, 35, 0.3);
        border: 1px solid rgba(135, 206, 235, 0.2);
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .guidance-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #87ceeb;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .guidance-content {
        color: #b8c5d1;
        line-height: 1.6;
        text-align: center;
    }
    
    .example-queries {
        background: rgba(135, 206, 235, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin-top: 1rem;
        font-size: 0.9rem;
        text-align: left;
    }
    
    /* Token Display */
    .token-display {
        text-align: center;
        padding: 0.5rem;
        background: rgba(15, 15, 35, 0.2);
        border: 1px solid rgba(135, 206, 235, 0.3);
        border-radius: 10px;
        margin: 0.25rem;
    }
    
    .token-number {
        display: block;
        font-size: 1.2rem;
        font-weight: 600;
        color: #87ceeb;
        margin-bottom: 0.2rem;
    }
    
    .token-label {
        display: block;
        font-size: 0.75rem;
        color: #9ca8b3;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Enhanced Query Section with Perfect Centering */
    .query-container {
        max-width: 900px;
        margin: 1rem auto 2rem auto;
        padding: 2rem 3rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        min-height: 120px;
        z-index: 1;
    }
    
    .query-wrapper {
        width: 100%;
        max-width: 700px;
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }
    
    /* Additional Orbital Elements */
    .query-wrapper::after {
        content: '🌍';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 15px;
        height: 15px;
        transform: translate(-50%, -180px);
        font-size: 1.2rem;
        animation: orbitRotate 40s linear infinite reverse, planetBob 3s ease-in-out infinite;
        pointer-events: none;
        z-index: -1;
        filter: drop-shadow(0 0 8px rgba(34, 139, 34, 0.6));
    }
    
    /* Floating Search Icon - using a separate div */
    .search-icon {
        position: absolute;
        left: 2rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5rem;
        z-index: 10;
        pointer-events: none;
        opacity: 0.6;
        animation: rocketPulse 3s ease-in-out infinite;
        transition: all 0.3s ease;
    }
    
    .query-wrapper:hover .search-icon {
        opacity: 1;
        transform: translateY(-50%) scale(1.1);
        filter: drop-shadow(0 0 10px rgba(100, 255, 218, 0.6));
    }
    
    @keyframes rocketPulse {
        0%, 100% { transform: translateY(-50%) rotate(-5deg); }
        25% { transform: translateY(-55%) rotate(0deg); }
        50% { transform: translateY(-50%) rotate(5deg); }
        75% { transform: translateY(-45%) rotate(0deg); }
    }
    
    /* Enhanced Input Styling with Perfect Balance */
    .stTextInput {
        width: 100% !important;
    }
    
    .stTextInput input {
        background: rgba(15, 15, 35, 0.85) !important;
        border: 2px solid rgba(100, 255, 218, 0.3) !important;
        border-radius: 25px !important;
        color: #f8fafc !important;
        padding: 1.5rem 5rem 1.5rem 4rem !important;
        font-size: 1.1rem !important;
        font-weight: 400 !important;
        transition: all 0.3s ease !important;
        box-shadow: 
            0 8px 25px rgba(0, 0, 0, 0.3),
            0 0 15px rgba(100, 255, 218, 0.1) !important;
        backdrop-filter: blur(15px) !important;
        position: relative;
        width: 100% !important;
        text-align: left !important;
        margin: 0 auto !important;
    }
    
    .stTextInput input:focus {
        border-color: #00ff88 !important;
        box-shadow: 
            0 0 0 3px rgba(0, 255, 136, 0.2), 
            0 8px 30px rgba(0, 0, 0, 0.4),
            0 0 25px rgba(100, 255, 218, 0.3) !important;
        outline: none !important;
        transform: translateY(-2px) !important;
        background: rgba(15, 15, 35, 0.9) !important;
        text-align: left !important;
    }
    
    .stTextInput input:hover {
        border-color: rgba(100, 255, 218, 0.6) !important;
        transform: translateY(-2px) !important;
        box-shadow: 
            0 14px 45px rgba(0, 0, 0, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.15),
            0 0 30px rgba(100, 255, 218, 0.2) !important;
    }
    
    .stTextInput input::placeholder {
        color: #94a3b8 !important;
        font-weight: 400 !important;
        opacity: 0.8 !important;
        transition: all 0.3s ease !important;
    }
    
    /* Enhanced Button Styling */
    .stButton button {
        background: linear-gradient(135deg, #64ffda 0%, #00bcd4 100%) !important;
        color: #0f0f23 !important;
        border: none !important;
        border-radius: 16px !important;
        font-weight: 700 !important;
        padding: 1.25rem 3.5rem !important;
        font-size: 1.1rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        box-shadow: 
            0 8px 32px rgba(100, 255, 218, 0.4),
            0 0 20px rgba(100, 255, 218, 0.2) !important;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        font-family: 'Inter', sans-serif;
    }
    
    .stButton button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.6s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #00ff88 0%, #64ffda 100%) !important;
        transform: translateY(-4px) scale(1.05) !important;
        box-shadow: 
            0 16px 50px rgba(0, 255, 136, 0.5),
            0 0 30px rgba(100, 255, 218, 0.4) !important;
        color: #0a0a0a !important;
    }
    
    .stButton button:hover::before {
        left: 100%;
    }
    
    .stButton button:active {
        transform: translateY(-2px) scale(1.02) !important;
        transition: all 0.1s ease !important;
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
    
    /* Enhanced Result Cards */
    .result-card {
        background: rgba(15, 15, 35, 0.85);
        border: 1px solid rgba(100, 255, 218, 0.25);
        border-radius: 20px;
        padding: 2.5rem;
        margin: 2rem 0;
        backdrop-filter: blur(25px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 10px 35px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1),
            0 0 20px rgba(100, 255, 218, 0.1);
        position: relative;
        overflow: hidden;
        border-left: 4px solid transparent;
        background-clip: padding-box;
    }
    
    .result-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(100, 255, 218, 0.8), transparent);
        animation: cardPulse 3s ease-in-out infinite;
    }
    
    .result-card:hover {
        border-color: rgba(0, 255, 136, 0.4);
        border-left-color: #00ff88;
        transform: translateY(-6px) scale(1.02);
        box-shadow: 
            0 20px 50px rgba(0, 0, 0, 0.4),
            0 0 30px rgba(0, 255, 136, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        background: rgba(15, 15, 35, 0.95);
    }
    
    @keyframes cardPulse {
        0%, 100% { opacity: 0.3; transform: scaleX(0); }
        50% { opacity: 1; transform: scaleX(1); }
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
    
    /* Enhanced AI Response */
    .ai-response {
        background: rgba(15, 15, 35, 0.9);
        border: 2px solid rgba(100, 255, 218, 0.3);
        border-radius: 25px;
        padding: 4rem;
        margin: 4rem 0;
        backdrop-filter: blur(30px);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1),
            0 0 40px rgba(100, 255, 218, 0.15);
        position: relative;
        overflow: hidden;
        animation: responseGlow 4s ease-in-out infinite alternate;
    }
    
    .ai-response::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00ff88, #64ffda, #00bcd4, #2196f3);
        background-size: 400% 400%;
        border-radius: 25px;
        z-index: -1;
        animation: gradientShift 6s ease-in-out infinite;
        opacity: 0.7;
    }
    
    @keyframes responseGlow {
        0% { 
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.4),
                0 0 40px rgba(100, 255, 218, 0.15);
        }
        100% { 
            box-shadow: 
                0 25px 70px rgba(0, 0, 0, 0.5),
                0 0 50px rgba(0, 255, 136, 0.25);
        }
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
    
    /* Enhanced Loading States */
    .stSpinner {
        text-align: center;
        position: relative;
    }
    
    .stSpinner > div {
        border-top-color: #00ff88 !important;
        border-right-color: #64ffda !important;
        border-bottom-color: #00bcd4 !important;
        border-left-color: transparent !important;
        animation: techSpin 1s linear infinite !important;
    }
    
    @keyframes techSpin {
        0% { 
            transform: rotate(0deg);
            filter: drop-shadow(0 0 10px rgba(0, 255, 136, 0.5));
        }
        50% { 
            filter: drop-shadow(0 0 20px rgba(100, 255, 218, 0.8));
        }
        100% { 
            transform: rotate(360deg);
            filter: drop-shadow(0 0 10px rgba(0, 255, 136, 0.5));
        }
    }
    
    /* Processing Animation */
    .processing-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #00ff88;
        font-family: 'JetBrains Mono', monospace;
        animation: processingPulse 1.5s ease-in-out infinite;
    }
    
    @keyframes processingPulse {
        0%, 100% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.05); }
    }
    
    /* Enhanced Mobile Responsiveness with Performance Optimizations */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2.2rem;
            margin-bottom: 0.5rem;
        }
        
        .app-subtitle {
            font-size: 1rem;
            padding: 0 1rem;
        }
        
        .query-container {
            padding: 1rem;
            max-width: 95%;
            margin: 0.5rem auto 1rem auto;
        }
        
        .main-header {
            padding: 2rem 0 1rem 0;
            margin-bottom: 1rem;
        }
        
        .query-wrapper {
            max-width: 100%;
        }
        
        .stTextInput input {
            padding: 1.4rem 4rem 1.4rem 3.5rem !important;
            font-size: 1rem !important;
            border-radius: 20px !important;
        }
        
        .search-icon {
            left: 1.5rem;
            font-size: 1.2rem;
        }
        
        .stButton button {
            padding: 1rem 2.5rem !important;
            font-size: 0.95rem !important;
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
        
        .strategy-indicator {
            padding: 1rem 1.5rem;
            font-size: 0.9rem;
        }
        
        .suggestions-grid {
            flex-direction: column;
            align-items: center;
        }
        
        .suggestion-tag {
            margin: 0.25rem 0;
        }
        
        /* Optimize animations for mobile performance */
        .stApp::before {
            background-size: 200px 150px;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.6), transparent 3px),
                radial-gradient(1px 1px at 90px 40px, rgba(135,206,250,0.5), transparent 2px),
                radial-gradient(1px 1px at 160px 80px, rgba(173,216,230,0.4), transparent 2px),
                radial-gradient(0.5px 0.5px at 240px 50px, rgba(255,255,255,0.3), transparent 1px);
            animation: starTwinkle 10s ease-in-out infinite alternate, starDrift 30s linear infinite;
            opacity: 0.3;
        }
        
        .stApp::after {
            font-size: 0.6em;
            line-height: 5;
            animation: floatingSpace 40s linear infinite;
        }
        
        /* Reduce orbital complexity on mobile */
        .query-container::before {
            width: 300px;
            height: 300px;
            animation: orbitRotate 80s linear infinite;
        }
        
        .query-container::after {
            animation: orbitRotate 80s linear infinite, planetBob 6s ease-in-out infinite;
        }
        
        .query-wrapper::after {
            animation: orbitRotate 60s linear infinite reverse, planetBob 5s ease-in-out infinite;
        }
        
        /* Reduce comet frequency on mobile */
        .comet-trail-1 {
            animation: cometTrail 16s linear infinite;
        }
        
        .comet-trail-2 {
            animation: cometTrail 20s linear infinite 6s;
        }
        
        .comet-trail-3 {
            animation: cometTrail 24s linear infinite 12s;
        }
        
        /* Simplify satellite movements */
        .satellite-1 {
            animation: satelliteOrbit 35s linear infinite;
        }
        
        .satellite-2 {
            animation: spacecraftFly 30s linear infinite 8s;
        }
        
        .satellite-3 {
            animation: ufoHover 40s linear infinite 15s;
        }
        
        /* Reduce nebula animation complexity */
        .stApp {
            animation: nebulaShift 30s ease-in-out infinite alternate;
        }
    }
    
    @media (max-width: 480px) {
        .app-title {
            font-size: 1.8rem;
        }
        
        .main-header {
            padding: 2rem 0 1.5rem 0;
        }
        
        .query-container {
            padding: 0 0.5rem;
        }
        
        .result-card, .ai-response {
            margin: 0.75rem 0;
        }
        
        .processing-container, .response-generating {
            padding: 1rem;
        }
        
        .init-container {
            padding: 1.5rem;
        }
        
        .init-progress {
            width: 150px;
        }
    }
    
    /* Enhanced Expander Styling */
    .streamlit-expanderHeader {
        background: rgba(15, 15, 35, 0.8) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(100, 255, 218, 0.3) !important;
        backdrop-filter: blur(15px) !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: rgba(0, 255, 136, 0.5) !important;
        background: rgba(15, 15, 35, 0.9) !important;
        box-shadow: 0 6px 25px rgba(0, 255, 136, 0.1) !important;
        transform: translateY(-1px) !important;
    }
    
    .streamlit-expanderContent {
        background-color: transparent !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Success Message Enhancement */
    .stSuccess {
        background: rgba(0, 255, 136, 0.1) !important;
        border: 1px solid rgba(0, 255, 136, 0.3) !important;
        border-radius: 12px !important;
        color: #00ff88 !important;
        backdrop-filter: blur(15px) !important;
    }
    
    /* Error Message Enhancement */
    .stError {
        background: rgba(255, 107, 107, 0.1) !important;
        border: 1px solid rgba(255, 107, 107, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(15px) !important;
    }
    
    /* New Animation Styles */
    @keyframes animate-slide-in {
        0% { transform: translateX(-50px); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes animate-slide-up {
        0% { transform: translateY(30px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes animate-fade-in {
        0% { opacity: 0; transform: scale(0.95); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    @keyframes animate-counter {
        0% { transform: scale(0.8); color: #64748b; }
        50% { transform: scale(1.2); color: #00ff88; }
        100% { transform: scale(1); color: #f1f5f9; }
    }
    
    @keyframes animate-success {
        0% { transform: scale(0.8) rotate(-5deg); opacity: 0; }
        50% { transform: scale(1.1) rotate(2deg); }
        100% { transform: scale(1) rotate(0deg); opacity: 1; }
    }
    
    /* Enhanced Strategy Indicators */
    .animate-slide-in { animation: animate-slide-in 0.6s ease-out; }
    .animate-slide-up { animation: animate-slide-up 0.8s ease-out; }
    .animate-fade-in { animation: animate-fade-in 0.8s ease-out; }
    .animate-counter { animation: animate-counter 1s ease-out; }
    .animate-success { animation: animate-success 0.8s ease-out; }
    
    .strategy-indicator {
        position: relative;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        overflow: hidden;
    }
    
    .strategy-icon {
        font-size: 1.2em;
        margin-right: 0.75rem;
        animation: pulse 2s infinite;
    }
    
    .strategy-bar {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        width: 100%;
        animation: fillBar 1.5s ease-out;
    }
    
    .local-bar {
        background: linear-gradient(90deg, #10b981, #34d399);
    }
    
    .web-bar {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
    }
    
    @keyframes fillBar {
        0% { transform: scaleX(0); }
        100% { transform: scaleX(1); }
    }
    
    /* Processing Animations */
    .processing-container {
        text-align: center;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .processing-dots {
        margin-left: 1rem;
        display: inline-flex;
        gap: 0.3rem;
    }
    
    .dot {
        width: 6px;
        height: 6px;
        background: #00ff88;
        border-radius: 50%;
        animation: dotPulse 1.4s infinite ease-in-out;
    }
    
    .dot-1 { animation-delay: -0.32s; }
    .dot-2 { animation-delay: -0.16s; }
    .dot-3 { animation-delay: 0s; }
    
    @keyframes dotPulse {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1.2); opacity: 1; }
    }
    
    /* Response Generation Animations */
    .response-generating {
        text-align: center;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .ai-thinking {
        display: inline-flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem 2rem;
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(100, 255, 218, 0.3);
        border-radius: 16px;
        backdrop-filter: blur(15px);
        animation: thinkingPulse 1.5s ease-in-out infinite;
    }
    
    .thinking-animation {
        display: flex;
        gap: 0.2rem;
    }
    
    .brain-wave {
        width: 4px;
        height: 20px;
        background: linear-gradient(180deg, #00ff88, #64ffda);
        border-radius: 2px;
        animation: brainWave 1.2s ease-in-out infinite;
    }
    
    .brain-wave:nth-child(2) { animation-delay: 0.1s; }
    .brain-wave:nth-child(3) { animation-delay: 0.2s; }
    
    @keyframes brainWave {
        0%, 100% { transform: scaleY(0.4); opacity: 0.6; }
        50% { transform: scaleY(1); opacity: 1; }
    }
    
    @keyframes thinkingPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    /* Search Suggestions */
    .search-suggestions {
        text-align: center;
        margin: 2rem 0;
        padding: 1.5rem;
    }
    
    .suggestions-header {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    
    .suggestions-grid {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.75rem;
    }
    
    .suggestion-tag {
        background: rgba(100, 255, 218, 0.1);
        border: 1px solid rgba(100, 255, 218, 0.2);
        color: #64ffda;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        transition: all 0.3s ease;
        cursor: pointer;
        backdrop-filter: blur(10px);
    }
    
    .suggestion-tag:hover {
        background: rgba(100, 255, 218, 0.2);
        border-color: rgba(100, 255, 218, 0.4);
        transform: translateY(-2px) scale(1.05);
        box-shadow: 0 4px 15px rgba(100, 255, 218, 0.2);
    }
    
    /* System Initialization */
    .system-initializing {
        text-align: center;
        padding: 3rem;
        margin: 2rem 0;
    }
    
    .init-container {
        display: inline-block;
        padding: 2rem;
        background: rgba(15, 15, 35, 0.9);
        border: 2px solid rgba(100, 255, 218, 0.3);
        border-radius: 20px;
        backdrop-filter: blur(20px);
        animation: initPulse 2s ease-in-out infinite;
    }
    
    .init-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        animation: rotate 2s linear infinite;
    }
    
    .init-progress {
        width: 200px;
        height: 4px;
        background: rgba(100, 255, 218, 0.2);
        border-radius: 2px;
        margin: 1rem auto;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #00ff88, #64ffda);
        border-radius: 2px;
        animation: progressFill 3s ease-in-out infinite;
    }
    
    @keyframes progressFill {
        0% { width: 0%; }
        50% { width: 70%; }
        100% { width: 100%; }
    }
    
    @keyframes initPulse {
        0%, 100% { box-shadow: 0 0 20px rgba(100, 255, 218, 0.3); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.5); }
    }
    
    .system-ready {
        text-align: center;
        padding: 1.5rem;
        margin: 1rem 0;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 16px;
        backdrop-filter: blur(15px);
    }
    
    .ready-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .ready-text {
        color: #00ff88;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .ready-subtext {
        color: #64d39a;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    }
    
    /* Enhanced Response Styling */
    .response-icon {
        font-size: 1.2rem;
        margin-right: 0.5rem;
    }
    
    .response-title {
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .response-indicator {
        position: absolute;
        top: 1rem;
        right: 1rem;
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    .response-footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(100, 255, 218, 0.2);
        text-align: center;
    }
    
    .powered-by {
        color: #64748b;
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .typing-animation {
        animation: typeIn 0.8s ease-out;
    }
    
    @keyframes typeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    /* ENHANCED PERFORMANCE OPTIMIZATIONS */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        box-sizing: border-box;
    }
    
    /* Core GPU acceleration for main container */
    .stApp {
        will-change: background, filter;
        transform: translateZ(0);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
        contain: layout style paint;
    }
    
    /* GPU acceleration for background layers */
    .stApp::before, .stApp::after {
        will-change: transform, opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
        contain: strict;
    }
    
    /* Enhanced GPU acceleration for space elements */
    .space-background, .starfield-layer-1, .starfield-layer-2, .starfield-layer-3,
    .query-container::before, .query-container::after,
    .query-wrapper::after {
        will-change: transform, opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
        contain: layout;
    }
    
    /* UI elements GPU acceleration */
    .stTextInput input {
        will-change: transform, box-shadow;
        transform: translateZ(0);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }
    
    .stButton button {
        will-change: transform, background, box-shadow;
        transform: translateZ(0);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }
    
    /* BATTERY & PERFORMANCE AWARE OPTIMIZATIONS */
    
    /* Detect low battery and reduce animations */
    @media (max-resolution: 1dppx) and (max-width: 768px) {
        .space-background { opacity: 0.3; }
        /* Reduce background complexity on low-end devices */
        
        /* Slower, less complex animations on low-end devices */
        .starfield-layer-1, .starfield-layer-2, .starfield-layer-3 { 
            animation-duration: 8s; 
        }
    }
    
    /* High performance mode for capable devices */
    @media (min-resolution: 2dppx) and (min-width: 1200px) {
        .space-background { opacity: 0.8; }
        /* Enhanced background for high-res displays */
    }
    
    /* Intersection Observer optimization classes */
    .space-element-hidden {
        opacity: 0;
        transform: scale(0.8);
        transition: opacity 0.5s ease, transform 0.5s ease;
    }
    
    .space-element-visible {
        opacity: 1;
        transform: scale(1);
    }
    
    /* CSS Custom Properties for dynamic animation control */
    :root {
        --animation-speed-multiplier: 1;
        --visual-complexity: 1;
        --battery-saver: 0;
    }
    
    /* Battery saver mode */
    @media (prefers-reduced-data: reduce) {
        :root {
            --animation-speed-multiplier: 0.5;
            --visual-complexity: 0.3;
            --battery-saver: 1;
        }
    }
    
    /* Apply performance variables */
    .orbit {
        animation-duration: calc(var(--orbit-duration, 20s) / var(--animation-speed-multiplier));
        opacity: calc(0.6 * var(--visual-complexity));
    }
    
    .starfield-layer-2, .starfield-layer-3 {
        opacity: calc(0.4 * var(--visual-complexity));
    }
    
    /* Memory optimization - limit simultaneous animations */
    .performance-optimized {
        animation-fill-mode: forwards;
        animation-iteration-count: finite;
    }
    
    /* Efficient rendering hints */
    .space-background {
        isolation: isolate;
        contain: layout style paint;
        content-visibility: auto;
        contain-intrinsic-size: 100vw 100vh;
    }
    
    /* Layer optimization */
    .z-background { z-index: -10; }
    .z-space-deep { z-index: -6; }
    .z-space-mid { z-index: -4; }
    .z-space-front { z-index: -2; }
    .z-ui { z-index: 1; }
    .z-overlay { z-index: 10; }
    
    /* Critical path CSS - prioritize visible elements */
    .critical-ui {
        content-visibility: visible;
        contain: none;
    }
    
    /* Non-critical background elements */
    .non-critical {
        content-visibility: auto;
        contain-intrinsic-size: 200px 200px;
    }
    
    /* Enhanced Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        line-height: 1.3;
        color: #f1f5f9;
    }
    
    p, span, div {
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace;
        background: rgba(15, 15, 35, 0.6);
        border-radius: 6px;
        padding: 0.2em 0.4em;
        border: 1px solid rgba(100, 255, 218, 0.2);
    }
    
    /* Improved Glassmorphism */
    .glass-effect {
        background: rgba(15, 15, 35, 0.7);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    /* Accessibility Improvements */
    .stButton button:focus {
        outline: 2px solid #00ff88 !important;
        outline-offset: 2px !important;
    }
    
    .stTextInput input:focus {
        outline: 2px solid #00ff88 !important;
        outline-offset: 2px !important;
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .stApp {
            background: #000000;
        }
        
        .app-title {
            color: #ffffff;
            text-shadow: none;
        }
        
        .result-card, .ai-response {
            border: 2px solid #ffffff;
            background: #111111;
        }
        
        .stButton button {
            border: 2px solid #ffffff;
        }
    }
    
    /* ACCESSIBILITY IMPROVEMENTS */
    
    /* Enhanced reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        /* Disable all space animations for accessibility */
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.3s !important;
            animation-play-state: paused !important;
        }
        
        /* Hide complex visual effects */
        .stApp::before, .stApp::after,
        .space-background {
            opacity: 0.1 !important;
        }
        
        /* Keep essential UI animations but make them gentle */
        .stTextInput input:focus,
        .stButton button:hover,
        .result-card:hover,
        .ai-response {
            transition: all 0.3s ease !important;
            animation: none !important;
        }
        
        /* Simple fade for interactive elements */
        .main-header, .query-container {
            animation: simpleFade 0.5s ease-out !important;
        }
        
        /* Provide static cosmic background without motion */
        .stApp {
            background: 
                linear-gradient(180deg, #000511 0%, #001122 50%, #000000 100%) !important;
            animation: none !important;
        }
    }
    
    @keyframes simpleFade {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .stApp {
            background: #000000 !important;
        }
        
        .app-title {
            color: #ffffff !important;
            text-shadow: none !important;
            background: none !important;
            -webkit-text-fill-color: #ffffff !important;
        }
        
        .app-subtitle, .header-description {
            color: #e0e0e0 !important;
        }
        
        .result-card, .ai-response {
            border: 2px solid #ffffff !important;
            background: #111111 !important;
            color: #ffffff !important;
        }
        
        .stButton button {
            border: 2px solid #ffffff !important;
            color: #000000 !important;
            background: #ffffff !important;
        }
        
        .stTextInput input {
            border: 2px solid #ffffff !important;
            background: #000000 !important;
            color: #ffffff !important;
        }
        
        /* Hide decorative elements in high contrast mode */
        .space-background {
            display: none !important;
        }
    }
    
    /* Dark theme preference support */
    @media (prefers-color-scheme: light) {
        .stApp {
            background: 
                linear-gradient(180deg, #f0f4f8 0%, #e2e8f0 50%, #cbd5e1 100%) !important;
            color: #1e293b !important;
        }
        
        .app-title {
            background: linear-gradient(135deg, #1e40af, #7c3aed, #db2777) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }
        
        .result-card, .ai-response {
            background: rgba(255, 255, 255, 0.9) !important;
            color: #1e293b !important;
            border-color: rgba(148, 163, 184, 0.3) !important;
        }
    }
    
    /* Focus management for keyboard navigation */
    .stButton button:focus,
    .stTextInput input:focus {
        outline: 3px solid #00ff88 !important;
        outline-offset: 2px !important;
        box-shadow: 
            0 0 0 6px rgba(0, 255, 136, 0.25),
            0 0 30px rgba(0, 255, 136, 0.4) !important;
    }
    
    /* Enhanced focus indicators for interactive elements */
    .suggestion-tag:focus,
    .source-link:focus {
        outline: 2px solid #64ffda !important;
        outline-offset: 2px !important;
    }
    
    /* Skip links for screen readers */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 6px;
        background: #00ff88;
        color: #0f0f23;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 1000;
        font-weight: 600;
    }
    
    .skip-link:focus {
        top: 6px;
    }
    
    /* Screen reader optimizations */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    
    /* Announce dynamic content changes */
    .live-region {
        position: absolute;
        left: -10000px;
        width: 1px;
        height: 1px;
        overflow: hidden;
    }
    
    /* Reduced transparency for better readability */
    @media (prefers-reduced-transparency: reduce) {
        .result-card, .ai-response,
        .stTextInput input, .stButton button {
            background-color: rgb(15, 15, 35) !important;
            backdrop-filter: none !important;
        }
        
        .space-background {
            opacity: 0.1 !important;
        }
    }
    
    /* Data saver mode */
    @media (prefers-reduced-data: reduce) {
        /* Disable all non-essential visual effects */
        .space-background { opacity: 0.1 !important; }
        
        /* Simplified backgrounds */
        .stApp::before, .stApp::after { display: none !important; }
        
        /* Reduce image quality and effects */
        .comet-trail, .satellite { filter: none !important; }
    }
    
    /* Forced colors mode support */
    @media (forced-colors: active) {
        .stApp {
            background: Canvas !important;
            color: CanvasText !important;
        }
        
        .stButton button {
            background: ButtonFace !important;
            color: ButtonText !important;
            border: 1px solid ButtonBorder !important;
        }
        
        .stTextInput input {
            background: Field !important;
            color: FieldText !important;
            border: 1px solid FieldText !important;
        }
        
        /* Hide decorative elements */
        .space-background {
            display: none !important;
        }
    }
    
    /* Touch device optimizations */
    @media (hover: none) and (pointer: coarse) {
        /* Larger touch targets */
        .stButton button {
            min-height: 48px !important;
            min-width: 48px !important;
            padding: 1rem 2rem !important;
        }
        
        .suggestion-tag {
            min-height: 40px !important;
            padding: 0.75rem 1.25rem !important;
        }
        
        /* Remove hover effects on touch devices */
        .result-card:hover,
        .stButton button:hover,
        .suggestion-tag:hover {
            transform: none !important;
        }
    }
    
    /* Voice control and speech recognition support */
    .voice-control-active .stApp {
        animation-play-state: paused !important;
    }
    
    .voice-control-active .space-background {
        animation-play-state: paused !important;
    }
    
    /* Print styles */
    @media print {
        .stApp::before, .stApp::after {
            display: none;
        }
        
        .stApp {
            background: white !important;
            color: black !important;
        }
        
        .result-card, .ai-response {
            border: 1px solid #ccc;
            background: white;
            box-shadow: none;
        }
    }
    
    /* Additional UI Components */
    .tech-stack {
        margin-top: 1rem;
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .tech-badge {
        background: rgba(100, 255, 218, 0.15);
        border: 1px solid rgba(100, 255, 218, 0.3);
        color: #64ffda;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .tech-badge:hover {
        background: rgba(100, 255, 218, 0.25);
        transform: translateY(-1px);
    }
    
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        justify-content: center;
        padding: 0.75rem;
        background: rgba(15, 15, 35, 0.6);
        border-radius: 12px;
        border: 1px solid rgba(71, 85, 105, 0.3);
        backdrop-filter: blur(15px);
        transition: all 0.3s ease;
    }
    
    .status-indicator:hover {
        background: rgba(15, 15, 35, 0.8);
        transform: translateY(-1px);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: statusPulse 2s infinite;
    }
    
    .status-text {
        font-size: 0.8rem;
        font-weight: 500;
        color: #cbd5e1;
    }
    
    .metric-display {
        text-align: center;
        padding: 0.75rem;
        background: rgba(15, 15, 35, 0.6);
        border-radius: 12px;
        border: 1px solid rgba(71, 85, 105, 0.3);
        backdrop-filter: blur(15px);
        transition: all 0.3s ease;
    }
    
    .metric-display:hover {
        background: rgba(15, 15, 35, 0.8);
        transform: translateY(-1px);
    }
    
    .metric-number {
        display: block;
        font-size: 1.2rem;
        font-weight: 700;
        color: #00ff88;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-label {
        font-size: 0.7rem;
        color: #64748b;
        font-weight: 500;
        margin-top: 0.2rem;
        display: block;
    }
    
    @keyframes statusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
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
        
        <!-- Simple Space Background -->
        <div class="space-background-simple"></div>
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
    
    async def process_query(self, user_question: str):
        """Process user query with enhanced loading states"""
        if not self.is_initialized:
            st.error("System initialization in progress. Please wait...")
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
                st.error("System initialization failed")
                return
                
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
        
        if not self.is_initialized:
            st.error("System unavailable")
            return
        
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