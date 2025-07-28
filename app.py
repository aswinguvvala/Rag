
import streamlit as st
import asyncio
from simple_rag_system import SimpleRAGSystem

# Initialize the RAG system
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = SimpleRAGSystem()
    # Run the async initialization
    asyncio.run(st.session_state.rag_system.initialize())

st.title("IntelliSearch")

query = st.text_input("Ask a question:")

if st.button("Search"):
    if query:
        with st.spinner("Searching..."):
            # Run the async search query
            result = asyncio.run(st.session_state.rag_system.search_query(query))
            
            st.subheader("Response")
            st.write(result.get("response", "No response generated."))
            
            st.subheader("Sources")
            sources = result.get("sources", [])
            if sources:
                for source in sources:
                    st.write(f"- **{source.get('title', 'Unknown Title')}** (Source: {source.get('source', 'Unknown Source')})")
            else:
                st.write("No sources found.")
    else:
        st.warning("Please enter a question.")
