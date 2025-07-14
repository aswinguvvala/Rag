import streamlit as st
import asyncio
import time
from datetime import datetime
import sys
import os
import pandas as pd

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the existing RAG system
from hybrid_rag_system import HybridRAGSystem, QueryResponse

# Basic space facts for common queries when RAG fails
BASIC_SPACE_FACTS = {
    "jupiter moons": {
        "answer": "Jupiter has **95 known moons** as of 2023. The four largest are called the Galilean moons: **Io, Europa, Ganymede, and Callisto**, discovered by Galileo in 1610. Europa and Ganymede are particularly interesting as they may have subsurface oceans.",
        "confidence": 0.95
    },
    "sun distance": {
        "answer": "The Sun is approximately **93 million miles** (150 million kilometers) away from Earth. This distance is called an **Astronomical Unit (AU)** and is used as a standard measurement in astronomy. The distance varies slightly due to Earth's elliptical orbit, from about 91.4 million miles (perihelion) to 94.5 million miles (aphelion).",
        "confidence": 0.95
    },
    "earth sun distance": {
        "answer": "The Sun is approximately **93 million miles** (150 million kilometers) away from Earth. This distance is called an **Astronomical Unit (AU)** and is used as a standard measurement in astronomy. The distance varies slightly due to Earth's elliptical orbit, from about 91.4 million miles (perihelion) to 94.5 million miles (aphelion).",
        "confidence": 0.95
    },
    "how far sun": {
        "answer": "The Sun is approximately **93 million miles** (150 million kilometers) away from Earth. This distance is called an **Astronomical Unit (AU)** and is used as a standard measurement in astronomy. The distance varies slightly due to Earth's elliptical orbit, from about 91.4 million miles (perihelion) to 94.5 million miles (aphelion).",
        "confidence": 0.95
    },
    "mars moons": {
        "answer": "Mars has **2 small moons**: **Phobos** and **Deimos**. Both are irregularly shaped and quite small - Phobos is about 22 km across and Deimos is about 12 km across. They're thought to be captured asteroids.",
        "confidence": 0.95
    },
    "saturn moons": {
        "answer": "Saturn has **146 known moons** as of 2023. The largest is **Titan**, which is larger than Mercury and has a thick atmosphere with liquid methane lakes. **Enceladus** is another notable moon with geysers of water erupting from its south pole.",
        "confidence": 0.95
    },
    "earth moons": {
        "answer": "Earth has **1 natural satellite**: **the Moon**. It's the fifth largest moon in the Solar System and formed about 4.5 billion years ago, likely from debris after a Mars-sized object collided with early Earth.",
        "confidence": 0.95
    },
    "sun age": {
        "answer": "The Sun is approximately **4.6 billion years old**. It formed from a collapsing cloud of gas and dust and is currently in its main sequence phase, converting hydrogen to helium in its core.",
        "confidence": 0.95
    },
    "sun old": {
        "answer": "The Sun is approximately **4.6 billion years old**. It formed from a collapsing cloud of gas and dust and is currently in its main sequence phase, converting hydrogen to helium in its core.",
        "confidence": 0.95
    },
    "light speed": {
        "answer": "The speed of light in a vacuum is **299,792,458 meters per second** (approximately 300,000 km/s or 186,000 miles/s). This is a fundamental constant of physics and the maximum speed at which all matter and information can travel.",
        "confidence": 0.95
    },
    "solar system planets": {
        "answer": "Our solar system has **8 planets**: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune. Pluto was reclassified as a dwarf planet in 2006.",
        "confidence": 0.95
    },
    "closest star": {
        "answer": "The closest star to Earth (besides the Sun) is **Proxima Centauri**, located about 4.24 light-years away in the Alpha Centauri system.",
        "confidence": 0.95
    },
    "moon distance": {
        "answer": "The Moon is approximately **384,400 kilometers** (238,855 miles) away from Earth on average. This distance varies slightly due to the Moon's elliptical orbit.",
        "confidence": 0.95
    },
    "mars distance": {
        "answer": "Mars is between **54.6 million to 401 million kilometers** from Earth, depending on where both planets are in their orbits. At closest approach (opposition), it's about 54.6 million km away.",
        "confidence": 0.95
    },
    "biggest planet": {
        "answer": "**Jupiter** is the largest planet in our solar system, with a diameter of about 142,984 kilometers - more than 11 times wider than Earth.",
        "confidence": 0.95
    },
    "smallest planet": {
        "answer": "**Mercury** is the smallest planet in our solar system, with a diameter of about 4,879 kilometers - only about 38% the size of Earth.",
        "confidence": 0.95
    },
    "hottest planet": {
        "answer": "**Venus** is the hottest planet in our solar system with surface temperatures around 464°C (867°F), even hotter than Mercury despite being farther from the Sun, due to its thick atmosphere and greenhouse effect.",
        "confidence": 0.95
    },
    "coldest planet": {
        "answer": "**Neptune** is the coldest planet in our solar system, with temperatures dropping to about -214°C (-353°F) in its upper atmosphere.",
        "confidence": 0.95
    },
    "iss speed": {
        "answer": "The International Space Station orbits Earth at approximately **28,000 km/h** (17,500 mph), completing one orbit around Earth every 90 minutes.",
        "confidence": 0.95
    },
    "astronomical unit": {
        "answer": "An **Astronomical Unit (AU)** is the average distance between Earth and the Sun, approximately **93 million miles** or **150 million kilometers**. It's the standard unit for measuring distances within our solar system.",
        "confidence": 0.95
    },
    "au distance": {
        "answer": "An **Astronomical Unit (AU)** is the average distance between Earth and the Sun, approximately **93 million miles** or **150 million kilometers**. It's the standard unit for measuring distances within our solar system.",
        "confidence": 0.95
    },
    "what is au": {
        "answer": "An **Astronomical Unit (AU)** is the average distance between Earth and the Sun, approximately **93 million miles** or **150 million kilometers**. It's the standard unit for measuring distances within our solar system.",
        "confidence": 0.95
    },
    "earth rotation": {
        "answer": "Earth rotates on its axis once every **24 hours** (23 hours, 56 minutes, and 4 seconds to be precise), which gives us day and night. Earth also orbits the Sun once every **365.25 days**.",
        "confidence": 0.95
    },
    "earth orbit": {
        "answer": "Earth orbits the Sun at an average distance of **93 million miles** (1 AU) and completes one orbit every **365.25 days**. The orbital speed averages about **67,000 mph** (107,000 km/h).",
        "confidence": 0.95
    },
    "milky way": {
        "answer": "The **Milky Way** is our home galaxy, containing over **100 billion stars**. It's a spiral galaxy about **100,000 light-years** in diameter, and our solar system is located about **26,000 light-years** from the galactic center.",
        "confidence": 0.95
    },
    "galaxy size": {
        "answer": "The **Milky Way** is our home galaxy, containing over **100 billion stars**. It's a spiral galaxy about **100,000 light-years** in diameter, and our solar system is located about **26,000 light-years** from the galactic center.",
        "confidence": 0.95
    }
}

def check_basic_space_facts(query: str) -> dict:
    """Check if query matches basic space facts"""
    query_lower = query.lower()
    
    # Clean up the query by removing common question words
    query_cleaned = query_lower.replace('?', '').replace(',', '').replace('.', '')
    
    for key, fact in BASIC_SPACE_FACTS.items():
        key_words = key.split()
        
        # Standard matching: all key words must be present
        if all(word in query_cleaned for word in key_words):
            return {
                "query_id": f"basic_fact_{int(time.time())}",
                "answer": fact["answer"],
                "confidence": fact["confidence"],
                "sources": [{"content": "Basic Space Facts Database", "relevance_score": 1.0, "source": "Built-in Knowledge"}],
                "processing_time": 0.1,
                "agent_used": "BasicSpaceFacts",
                "debug_info": {"method": "basic_facts_fallback"}
            }
        
        # Additional flexible matching for moon questions
        if 'moons' in key or 'moon' in key:
            # Extract planet name from key
            planet_name = key.replace(' moons', '').replace(' moon', '')
            
            # Check if query is asking about this planet's moons
            moon_indicators = ['moon', 'moons', 'satellite', 'satellites']
            question_indicators = ['how many', 'number of', 'count', 'total']
            
            has_planet = planet_name in query_cleaned
            has_moon_indicator = any(indicator in query_cleaned for indicator in moon_indicators)
            has_question_indicator = any(indicator in query_cleaned for indicator in question_indicators)
            
            if has_planet and has_moon_indicator and has_question_indicator:
                return {
                    "query_id": f"basic_fact_{int(time.time())}",
                    "answer": fact["answer"],
                    "confidence": fact["confidence"],
                    "sources": [{"content": "Basic Space Facts Database", "relevance_score": 1.0, "source": "Built-in Knowledge"}],
                    "processing_time": 0.1,
                    "agent_used": "BasicSpaceFacts",
                    "debug_info": {"method": "basic_facts_fallback"}
                }
    
    return None

# Page configuration
st.set_page_config(
    page_title="MSEIS - Space Exploration Intelligence",
    page_icon="🚀",
    layout="wide"
)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize RAG system
@st.cache_resource
def get_rag_system():
    """Initialize and return the RAG system"""
    with st.spinner("🚀 Initializing MSEIS RAG System..."):
        rag_system = HybridRAGSystem()
        rag_system.initialize()
        
        # Build knowledge base if it doesn't exist
        if len(rag_system.documents) == 0:
            with st.spinner("📡 Building space knowledge base from web sources..."):
                rag_system.build_knowledge_base()
        
        return rag_system

async def query_api(query: str, expertise_level: str):
    """Process query using real RAG system with basic facts fallback"""
    
    # FIRST: Check basic facts for common questions (before RAG)
    basic_fact = check_basic_space_facts(query)
    if basic_fact:
        return basic_fact
    
    # If no basic fact found, try the RAG system
    rag_system = get_rag_system()
    
    # Add expertise level context to the query for better responses
    if expertise_level == "student":
        enhanced_query = f"Explain in simple terms for students: {query}"
    elif expertise_level == "expert":
        enhanced_query = f"Provide detailed technical information: {query}"
    else:
        enhanced_query = query
    
    # Get response from RAG system
    response = rag_system.query(enhanced_query, expertise_level)
    
    # If RAG system returns "no results", double-check basic facts again
    if response.method_used == "no_results":
        # Try again with original query in case enhanced query didn't match
        basic_fact = check_basic_space_facts(query)
        if basic_fact:
            return basic_fact
    
    # Convert to the format expected by our UI
    return {
        "query_id": f"rag_{int(time.time())}",
        "answer": response.answer,
        "confidence": response.confidence,
        "sources": response.sources,
        "processing_time": response.processing_time,
        "agent_used": f"HybridRAG ({response.method_used})",
        "debug_info": response.debug_info
    }

def main():
    # Header
    st.title("🚀 MSEIS - Multi-Modal Space Exploration Intelligence System")
    st.markdown("*Your AI-powered gateway to space exploration knowledge (Real RAG System with Web Scraping)*")
    
    # Initialize RAG system and show status
    try:
        rag_system = get_rag_system()
        system_healthy = True
        knowledge_base_size = len(rag_system.documents)
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        system_healthy = False
        knowledge_base_size = 0
    
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📚 Document Explorer", "🔍 Retrieval Inspector"])
    
    # Sidebar (common for all tabs)
    with st.sidebar:
        st.header("⚙️ Settings")
        
        expertise_level = st.selectbox(
            "Expertise Level",
            ["student", "general", "expert"],
            index=1,
            help="Adjusts the complexity of responses"
        )
        
        st.header("📊 System Status")
        if system_healthy:
            st.write("Status: 🟢 **Healthy**")
            st.write("RAG System: 🟢 **Active**")
            st.write(f"Knowledge Base: 🟢 **{knowledge_base_size} documents loaded**")
            st.write("Web Search: 🟢 **Enabled**")
        else:
            st.write("Status: 🔴 **Error**")
            st.write("RAG System: 🔴 **Failed**")
            st.write("Knowledge Base: 🔴 **Not loaded**")
        
        st.header("📚 Data Sources")
        st.write("**🛰️ Space Agencies:**")
        st.write("• NASA News & Updates")
        st.write("• ESA Space News")
        
        st.write("**🚀 Private Companies:**")
        st.write("• SpaceX Updates")
        st.write("• Blue Origin News")
        
        st.write("**📰 News & Media:**")
        st.write("• Space.com Articles")
        st.write("• SpaceNews Industry")
        st.write("• Planetary Society")
        
        st.write("**📑 Research Sources:**")
        st.write("• arXiv Papers (7 topics)")
        st.write("• Nature Astronomy")
        
        st.write("**🌐 Web Search:**")
        st.write("• DuckDuckGo Real-time")
        
        st.write("**⚡ Quick Facts:**")
        st.write("• Built-in Space Facts")
        
        if st.button("🔄 Refresh Knowledge Base"):
            if system_healthy:
                with st.spinner("📡 Updating knowledge base..."):
                    # Clear cache and rebuild
                    st.cache_resource.clear()
                    get_rag_system()
                st.success("Knowledge base updated!")
                st.rerun()
        
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    # TAB 1: CHAT (Original functionality)
    with tab1:
        st.header("💬 Ask about Space Exploration")
        
        # Example queries
        st.markdown("**💡 Try these example queries:**")
        example_queries = [
            "What are the latest NASA missions?",
            "Tell me about Mars exploration",
            "What is the James Webb Space Telescope discovering?",
            "What are the recent SpaceX achievements?",
            "Explain black holes",
            "What is the current status of the Artemis program?"
        ]
        
        cols = st.columns(3)
        for i, query in enumerate(example_queries):
            with cols[i % 3]:
                if st.button(f"🌟 {query}", key=f"example_{i}"):
                    st.session_state.messages.append({"role": "user", "content": query})
                    st.rerun()
        
        # Chat messages display
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show metadata for assistant messages
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    
                    # Metrics row
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🎯 Confidence", f"{metadata.get('confidence', 0)*100:.0f}%")
                    with col2:
                        st.metric("⏱️ Processing Time", f"{metadata.get('processing_time', 0):.1f}s")
                    with col3:
                        st.metric("🤖 Agent Used", metadata.get('agent_used', 'Unknown'))
                    with col4:
                        debug_info = metadata.get('debug_info', {})
                        total_sources = debug_info.get('total_results', 0)
                        st.metric("📄 Sources", total_sources)
                    
                    # Show sources if available
                    sources = metadata.get('sources', [])
                    if sources:
                        with st.expander(f"📚 View {len(sources)} Sources", expanded=False):
                            for i, source in enumerate(sources[:5], 1):
                                st.write(f"**{i}. {source.get('source', 'Unknown')}**")
                                if source.get('title'):
                                    st.write(f"*{source['title']}*")
                                if source.get('url'):
                                    st.write(f"🔗 [Link]({source['url']})")
                                if source.get('relevance_score'):
                                    st.write(f"Relevance: {source['relevance_score']:.2f}")
                                st.write("---")
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about space exploration..."):
            if not system_healthy:
                st.error("❌ RAG system is not available. Please refresh the page or check system status.")
                return
                
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get and display AI response
            with st.chat_message("assistant"):
                with st.spinner("🔄 Searching knowledge base and web sources..."):
                    try:
                        response = asyncio.run(query_api(prompt, expertise_level))
                        
                        if response:
                            answer = response.get("answer", "Sorry, I couldn't process your query.")
                            st.write(answer)
                            
                            # Add metadata to message
                            metadata = {
                                "confidence": response.get("confidence", 0),
                                "sources": response.get("sources", []),
                                "processing_time": response.get("processing_time", 0),
                                "agent_used": response.get("agent_used", "unknown"),
                                "debug_info": response.get("debug_info", {})
                            }
                            
                            # Display metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("🎯 Confidence", f"{metadata['confidence']*100:.0f}%")
                            with col2:
                                st.metric("⏱️ Processing Time", f"{metadata['processing_time']:.1f}s")
                            with col3:
                                st.metric("🤖 Agent Used", metadata['agent_used'])
                            with col4:
                                debug_info = metadata.get('debug_info', {})
                                total_sources = debug_info.get('total_results', 0)
                                st.metric("📄 Sources", total_sources)
                            
                            # Show sources
                            sources = metadata.get('sources', [])
                            if sources:
                                with st.expander(f"📚 View {len(sources)} Sources", expanded=False):
                                    for i, source in enumerate(sources[:5], 1):
                                        st.write(f"**{i}. {source.get('source', 'Unknown')}**")
                                        if source.get('title'):
                                            st.write(f"*{source['title']}*")
                                        if source.get('url'):
                                            st.write(f"🔗 [Link]({source['url']})")
                                        if source.get('relevance_score'):
                                            st.write(f"Relevance: {source['relevance_score']:.2f}")
                                        st.write("---")
                            
                            # Add assistant message with metadata
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "metadata": metadata
                            })
                            
                            st.rerun()
                            
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "metadata": {}
                        })
    
    # TAB 2: DOCUMENT EXPLORER (NEW!)
    with tab2:
        st.header("📚 Document Explorer")
        st.markdown("*Browse and search your knowledge base documents*")
        
        if not system_healthy:
            st.error("❌ RAG system is not available. Please refresh the page.")
            return
        
        # Document statistics
        col1, col2, col3, col4 = st.columns(4)
        
        sources = {}
        for doc in rag_system.documents:
            source = doc.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        with col1:
            st.metric("📄 Total Documents", len(rag_system.documents))
        with col2:
            st.metric("🏷️ Unique Sources", len(sources))
        with col3:
            avg_length = sum(len(doc.get('content', '')) for doc in rag_system.documents) / max(len(rag_system.documents), 1)
            st.metric("📝 Avg Content Length", f"{avg_length:.0f} chars")
        with col4:
            recent_docs = sum(1 for doc in rag_system.documents if doc.get('date', '').startswith('2024') or doc.get('date', '').startswith('2025'))
            st.metric("🆕 Recent Documents", recent_docs)
        
        # Source breakdown
        st.subheader("📊 Documents by Source")
        source_df = pd.DataFrame(list(sources.items()), columns=['Source', 'Count'])
        source_df = source_df.sort_values('Count', ascending=False)
        st.bar_chart(source_df.set_index('Source'))
        
        # Document browser
        st.subheader("🔍 Browse Documents")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_source = st.selectbox(
                "Filter by Source",
                ["All"] + list(sources.keys())
            )
        with col2:
            search_text = st.text_input("Search in titles/content", placeholder="Enter search terms...")
        
        # Filter documents
        filtered_docs = rag_system.documents
        
        if selected_source != "All":
            filtered_docs = [doc for doc in filtered_docs if doc.get('source') == selected_source]
        
        if search_text:
            search_lower = search_text.lower()
            filtered_docs = [
                doc for doc in filtered_docs 
                if search_lower in doc.get('title', '').lower() or search_lower in doc.get('content', '').lower()
            ]
        
        st.write(f"📋 Showing {len(filtered_docs)} documents")
        
        # Pagination
        docs_per_page = 10
        total_pages = (len(filtered_docs) - 1) // docs_per_page + 1 if filtered_docs else 1
        
        if total_pages > 1:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1
        else:
            page = 0
        
        start_idx = page * docs_per_page
        end_idx = start_idx + docs_per_page
        page_docs = filtered_docs[start_idx:end_idx]
        
        # Display documents
        for i, doc in enumerate(page_docs):
            with st.expander(f"📄 {doc.get('title', 'Untitled')[:80]}..." if len(doc.get('title', '')) > 80 else f"📄 {doc.get('title', 'Untitled')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Source:** {doc.get('source', 'Unknown')}")
                    if doc.get('date'):
                        st.write(f"**Date:** {doc.get('date')}")
                    if doc.get('url'):
                        st.write(f"**URL:** {doc.get('url')}")
                    if doc.get('authors'):
                        st.write(f"**Authors:** {doc.get('authors')}")
                
                with col2:
                    content_length = len(doc.get('content', ''))
                    st.metric("📝 Length", f"{content_length} chars")
                
                # Content preview
                content = doc.get('content', '')
                if len(content) > 500:
                    st.write("**Content Preview:**")
                    st.write(content[:500] + "...")
                    if st.button(f"Show Full Content", key=f"full_content_{start_idx + i}"):
                        st.write("**Full Content:**")
                        st.write(content)
                else:
                    st.write("**Content:**")
                    st.write(content)
    
    # TAB 3: RETRIEVAL INSPECTOR (NEW!)
    with tab3:
        st.header("🔍 Retrieval Inspector")
        st.markdown("*Test and debug document retrieval with detailed scoring*")
        
        if not system_healthy:
            st.error("❌ RAG system is not available. Please refresh the page.")
            return
        
        # Test query input
        test_query = st.text_input(
            "🔍 Test Query", 
            placeholder="Enter a query to see how documents are retrieved and scored...",
            value="How many moons does Jupiter have?"
        )
        
        if test_query and st.button("🚀 Run Retrieval Test"):
            with st.spinner("🔍 Analyzing retrieval..."):
                # Get semantic search results
                results = rag_system.semantic_search(test_query, top_k=10)
                
                st.subheader(f"📊 Results for: '{test_query}'")
                
                if not results:
                    st.warning("❌ No relevant documents found")
                else:
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📄 Documents Found", len(results))
                    with col2:
                        best_score = max(r.get('relevance_score', 0) for r in results)
                        st.metric("🎯 Best Score", f"{best_score:.3f}")
                    with col3:
                        avg_score = sum(r.get('relevance_score', 0) for r in results) / len(results)
                        st.metric("📊 Average Score", f"{avg_score:.3f}")
                    with col4:
                        high_quality = sum(1 for r in results if r.get('relevance_score', 0) > 0.5)
                        st.metric("✅ High Quality", high_quality)
                    
                    # Detailed results
                    st.subheader("📋 Detailed Retrieval Results")
                    
                    for i, result in enumerate(results, 1):
                        relevance = result.get('relevance_score', 0)
                        semantic = result.get('semantic_score', 0)
                        content_rel = result.get('content_relevance', 0)
                        
                        # Color coding based on score
                        if relevance > 0.7:
                            score_color = "🟢"
                        elif relevance > 0.5:
                            score_color = "🟡"
                        elif relevance > 0.3:
                            score_color = "🟠"
                        else:
                            score_color = "🔴"
                        
                        with st.expander(f"{score_color} Rank {i}: {result.get('title', 'Untitled')[:60]}... (Score: {relevance:.3f})"):
                            # Scoring breakdown
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("🎯 Final Score", f"{relevance:.3f}")
                            with col2:
                                st.metric("🧠 Semantic", f"{semantic:.3f}")
                            with col3:
                                st.metric("🔤 Content Match", f"{content_rel:.3f}")
                            
                            # Document details
                            st.write(f"**Source:** {result.get('source', 'Unknown')}")
                            st.write(f"**Title:** {result.get('title', 'Untitled')}")
                            
                            # Content snippet with query highlighting
                            content = result.get('content', '')
                            if content:
                                # Show first 300 chars
                                snippet = content[:300] + ("..." if len(content) > 300 else "")
                                
                                # Try to highlight query terms (simple approach)
                                query_words = test_query.lower().split()
                                highlighted = snippet
                                for word in query_words:
                                    if len(word) > 2:  # Only highlight words longer than 2 chars
                                        highlighted = highlighted.replace(
                                            word, f"**{word}**"
                                        )
                                
                                st.write("**Content Snippet:**")
                                st.write(highlighted)
                            
                            # Show why this scored high/low
                            st.write("**Scoring Analysis:**")
                            if relevance > 0.7:
                                st.success("✅ High relevance - strong semantic and keyword match")
                            elif relevance > 0.5:
                                st.info("ℹ️ Good relevance - decent match but could be better")
                            elif relevance > 0.3:
                                st.warning("⚠️ Low relevance - weak match, might be filtered out")
                            else:
                                st.error("❌ Very low relevance - likely irrelevant to query")
        
        # Query analysis tips
        st.subheader("💡 Retrieval Tips")
        st.info("""
        **Understanding Scores:**
        - **Final Score**: Combination of semantic similarity (70%) + keyword matching (30%)
        - **Semantic Score**: How similar the meaning is (using AI embeddings)
        - **Content Match**: How many keywords from your query appear in the document
        
        **Score Ranges:**
        - 🟢 **0.7-1.0**: Excellent match, will be used in response
        - 🟡 **0.5-0.7**: Good match, likely to be used
        - 🟠 **0.3-0.5**: Fair match, might be used if nothing better
        - 🔴 **0.0-0.3**: Poor match, will be filtered out
        
        **Improving Retrieval:**
        - Use specific terms (e.g., "Jupiter moons" vs "celestial bodies")
        - Include key concepts from your knowledge domain
        - Try different phrasings if results are poor
        """)

    # Footer
    st.markdown("---")
    st.markdown("**🚀 MSEIS** - Real RAG-based Space Exploration Intelligence System with Live Web Scraping")
    st.markdown("*Data sources: NASA, ESA, SpaceX, arXiv, Space.com, and real-time web search*")

if __name__ == "__main__":
    main() 