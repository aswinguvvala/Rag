#!/usr/bin/env python3
"""
Debug Search Issue - Diagnose why "No search results found" error occurs
"""

import asyncio
from simple_rag_system import SimpleRAGSystem

async def debug_search_issue():
    print("🔍 DEBUG: Investigating 'No search results found' error")
    print("=" * 70)
    
    # Initialize system
    print("1️⃣ Initializing RAG system...")
    rag = SimpleRAGSystem()
    
    # Initialize with detailed output
    success = await rag.initialize()
    print(f"   Initialization success: {success}")
    
    if not success:
        print("❌ System initialization failed - this could be the issue!")
        return
    
    # Check system state
    print(f"\n2️⃣ System state check:")
    print(f"   Documents loaded: {len(rag.documents) if rag.documents else 0}")
    print(f"   Embedding model: {rag.embedding_model is not None}")
    print(f"   FAISS index: {rag.faiss_index is not None}")
    print(f"   Web search: {rag.web_search_manager is not None}")
    print(f"   Similarity threshold: {rag.similarity_threshold}")
    print(f"   Fallback threshold: {rag.fallback_threshold}")
    
    if not rag.documents:
        print("❌ No documents loaded - this is likely the issue!")
        return
    
    # Test queries that should definitely find results
    test_queries = [
        "space",
        "NASA",
        "artificial intelligence", 
        "machine learning",
        "technology",
        "science",
        "What is space exploration?"
    ]
    
    print(f"\n3️⃣ Testing queries with detailed debug output:")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: '{query}' ---")
        try:
            result = await rag.search_query(query)
            
            if result and result.get('response'):
                print(f"✅ SUCCESS: Got response!")
                print(f"   Method: {result.get('method', 'Unknown')}")
                print(f"   Sources: {len(result.get('sources', []))}")
                print(f"   Response preview: {result['response'][:100]}...")
                break  # Found working query, no need to test more
            else:
                print(f"❌ FAILED: No response generated")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
    
    # If all queries failed, show sample document titles
    if rag.documents:
        print(f"\n4️⃣ Sample document titles from knowledge base:")
        for i, doc in enumerate(rag.documents[:10], 1):
            title = doc.get('title', 'No title')[:60]
            category = doc.get('category', 'No category')
            print(f"   {i}. [{category}] {title}...")
        
        print(f"\n💡 Try queries related to these topics!")

if __name__ == "__main__":
    try:
        asyncio.run(debug_search_issue())
        print(f"\n🎯 DEBUG COMPLETE")
        print(f"Check the detailed output above to identify the issue.")
    except Exception as e:
        print(f"\n💥 DEBUG ERROR: {e}")
        print(f"This error itself might be the root cause!")