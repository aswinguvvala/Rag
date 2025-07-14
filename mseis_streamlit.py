# mseis_streamlit.py
import streamlit as st
import asyncio
import aiohttp
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="MSEIS - Space Exploration Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main {
    padding: 0rem 0rem;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding-left: 20px;
    padding-right: 20px;
}
.source-card {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_history" not in st.session_state:
    st.session_state.query_history = []

async def query_api(query: str, expertise_level: str) -> Dict[str, Any]:
    """Send query to API"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{API_BASE_URL}/query",
                json={
                    "query": query,
                    "expertise_level": expertise_level
                }
            ) as response:
                return await response.json()
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None

async def get_health() -> Dict[str, Any]:
    """Get system health status"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                return await response.json()
        except:
            return {"status": "offline", "agents": {}}

def main():
    # Header
    st.title("🚀 MSEIS - Multi-Modal Space Exploration Intelligence System")
    st.markdown("*Your AI-powered gateway to space exploration knowledge*")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # Expertise level selector
        expertise_level = st.selectbox(
            "Expertise Level",
            ["student", "general", "expert"],
            index=1,
            help="Adjusts the complexity of responses"
        )
        
        # System status
        st.header("System Status")
        if st.button("🔄 Refresh Status"):
            st.rerun()
            
        try:
            health = asyncio.run(get_health())
        except:
            health = {"status": "offline"}
        
        status_color = {
            "healthy": "🟢",
            "degraded": "🟡", 
            "offline": "🔴"
        }.get(health.get("status", "offline"), "🔴")
        
        st.write(f"Status: {status_color} {health.get('status', 'offline').title()}")
        
        # Query history
        if st.session_state.query_history:
            st.header("Recent Queries")
            for i, item in enumerate(reversed(st.session_state.query_history[-3:])):
                if st.button(f"📝 {item['query'][:25]}...", key=f"history_{i}"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": item["query"]
                    })
    
    # Main content tabs
    tab1, tab2 = st.tabs(["💬 Chat", "📊 Analytics"])
    
    with tab1:
        # Chat interface
        st.header("Ask about Space Exploration")
        
        # Example queries
        example_queries = [
            "What are the latest discoveries from the James Webb Space Telescope?",
            "Explain the differences between SpaceX Starship and NASA's SLS",
            "Show me images of the Crab Nebula",
            "What is the current position of the ISS?",
            "How do exoplanet detection methods work?"
        ]
        
        st.markdown("**Example queries:**")
        cols = st.columns(2)
        for i, query in enumerate(example_queries[:4]):
            with cols[i % 2]:
                if st.button(f"💡 {query}", key=f"example_{i}"):
                    st.session_state.messages.append({"role": "user", "content": query})
                    
        # Chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show metadata if available
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        st.metric("Confidence", f"{metadata.get('confidence', 0)*100:.0f}%")
                    with col2:
                        st.metric("Sources", len(metadata.get('sources', [])))
                    with col3:
                        st.metric("Agent", metadata.get('agent_used', 'Unknown'))
        
        # Chat input
        if prompt := st.chat_input("Ask me about space exploration..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = asyncio.run(query_api(prompt, expertise_level))
                        
                        if response:
                            answer = response.get("answer", "Sorry, I couldn't process your query.")
                            confidence = response.get("confidence", 0)
                            sources = response.get("sources", [])
                            processing_time = response.get("processing_time", 0)
                            agent_used = response.get("agent_used", "unknown")
                            
                            st.write(answer)
                            
                            # Add to session state
                            metadata = {
                                "confidence": confidence,
                                "sources": sources,
                                "processing_time": processing_time,
                                "agent_used": agent_used
                            }
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "metadata": metadata
                            })
                            
                            # Add to query history
                            st.session_state.query_history.append({
                                "query": prompt,
                                "response": answer,
                                "metadata": metadata,
                                "timestamp": datetime.now()
                            })
                            
                        else:
                            error_msg = "Sorry, the system is currently unavailable. Please try again later."
                            st.write(error_msg)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_msg,
                                "metadata": {}
                            })
                            
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_msg,
                            "metadata": {}
                        })
    
    with tab2:
        st.header("📊 Query Analytics")
        
        if st.session_state.query_history:
            # Create analytics
            df = pd.DataFrame([{
                "Query": item["query"],
                "Confidence": item["metadata"].get("confidence", 0),
                "Processing Time": item["metadata"].get("processing_time", 0),
                "Agent": item["metadata"].get("agent_used", "unknown"),
                "Timestamp": item["timestamp"]
            } for item in st.session_state.query_history])
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Confidence distribution
                fig_conf = px.histogram(df, x="Confidence", title="Confidence Score Distribution")
                st.plotly_chart(fig_conf, use_container_width=True)
            
            with col2:
                # Agent usage
                agent_counts = df["Agent"].value_counts()
                fig_agents = px.pie(values=agent_counts.values, names=agent_counts.index,
                                  title="Agent Usage Distribution")
                st.plotly_chart(fig_agents, use_container_width=True)
            
            # Query statistics
            st.subheader("Query Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Queries", len(df))
            with col2:
                st.metric("Average Confidence", f"{df['Confidence'].mean()*100:.0f}%")
            with col3:
                st.metric("Average Processing Time", f"{df['Processing Time'].mean():.2f}s")
        else:
            st.info("No queries yet. Start asking questions to see analytics!")

if __name__ == "__main__":
    main() 