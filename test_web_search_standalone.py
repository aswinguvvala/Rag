#!/usr/bin/env python3
"""
Test Web Search Standalone - Isolate web search issues
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_web_search_standalone():
    print("🔍 Testing Web Search Functionality Standalone")
    print("=" * 60)
    
    # Test 1: Check imports
    print("1️⃣ Testing imports...")
    try:
        from web_search_manager import UniversalWebSearchManager
        print("✅ web_search_manager imported successfully")
        WEB_SEARCH_AVAILABLE = True
    except ImportError as e:
        print(f"❌ web_search_manager import failed: {e}")
        WEB_SEARCH_AVAILABLE = False
        return False
    
    # Test 2: Initialize web search manager
    print("\n2️⃣ Testing web search manager initialization...")
    try:
        web_manager = UniversalWebSearchManager()
        print("✅ UniversalWebSearchManager initialized")
    except Exception as e:
        print(f"❌ UniversalWebSearchManager init failed: {e}")
        return False
    
    # Test 3: Test simple search
    test_queries = [
        "Wimbledon 2023 winner",
        "Python programming",
        "weather today"
    ]
    
    print("\n3️⃣ Testing web searches...")
    for query in test_queries:
        print(f"\n--- Testing: '{query}' ---")
        try:
            print(f"🔍 Calling web_manager.search('{query}', max_results=3)...")
            results = await web_manager.search(query, max_results=3)
            
            print(f"📊 Results returned: {len(results) if results else 0}")
            
            if results:
                print(f"📋 First result type: {type(results[0])}")
                print(f"📋 First result attributes: {dir(results[0])}")
                
                for i, result in enumerate(results[:2], 1):
                    print(f"   {i}. Title: {getattr(result, 'title', 'No title')[:50]}...")
                    
                    # Check for content
                    content = getattr(result, 'content', None)
                    snippet = getattr(result, 'snippet', None)
                    print(f"      Content: {len(content) if content else 0} chars")
                    print(f"      Snippet: {len(snippet) if snippet else 0} chars")
                    print(f"      URL: {getattr(result, 'url', 'No URL')[:50]}...")
                
                print(f"✅ Web search working for: {query}")
            else:
                print(f"⚠️ No results returned for: {query}")
                
        except Exception as e:
            print(f"❌ Web search failed for '{query}': {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
    
    print(f"\n4️⃣ Testing edge cases...")
    
    # Test empty query
    try:
        print(f"🔍 Testing empty query...")
        results = await web_manager.search("", max_results=1)
        print(f"📊 Empty query results: {len(results) if results else 0}")
    except Exception as e:
        print(f"❌ Empty query failed: {e}")
    
    # Test very specific query
    try:
        print(f"🔍 Testing very specific query...")
        results = await web_manager.search("asdjkalsjdklajsdkl", max_results=1)
        print(f"📊 Nonsense query results: {len(results) if results else 0}")
    except Exception as e:
        print(f"❌ Nonsense query failed: {e}")
    
    return True

async def test_rag_system_web_search():
    """Test web search through the RAG system"""
    print(f"\n5️⃣ Testing web search through RAG system...")
    
    try:
        from simple_rag_system import SimpleRAGSystem
        
        rag = SimpleRAGSystem()
        print(f"📊 RAG System - WEB_SEARCH_AVAILABLE: {getattr(rag, 'web_search_manager', None) is not None}")
        
        # Initialize just enough to test web search
        if hasattr(rag, 'web_search_manager') and rag.web_search_manager:
            print(f"🔍 Testing RAG system web search...")
            results = await rag._search_web("Wimbledon 2023")
            print(f"📊 RAG web search results: {len(results) if results else 0}")
            
            if results:
                print(f"✅ RAG web search working")
                for i, result in enumerate(results[:2], 1):
                    print(f"   {i}. Title: {result.title[:50]}...")
                    print(f"      Content: {len(result.content)} chars")
            else:
                print(f"⚠️ RAG web search returned no results")
        else:
            print(f"❌ RAG system has no web search manager")
            
    except Exception as e:
        print(f"❌ RAG system web search test failed: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    try:
        success = asyncio.run(test_web_search_standalone())
        if success:
            asyncio.run(test_rag_system_web_search())
        
        print(f"\n🎯 Web Search Test Complete!")
        print(f"Check output above to identify web search issues.")
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        print(f"💥 Traceback: {traceback.format_exc()}")