#!/usr/bin/env python3
"""
Test Web Search Logic - Verify external queries trigger web search properly
"""

import asyncio
from simple_rag_system import SimpleRAGSystem

async def test_web_search_logic():
    print("🔍 Testing Web Search Logic...")
    print("=" * 60)
    
    # Initialize system
    rag = SimpleRAGSystem()
    await rag.initialize()
    
    # Test queries that should trigger web search (low similarity to space knowledge base)
    external_queries = [
        "Wimbledon 2023 winner",
        "Current weather in New York", 
        "Latest iPhone price",
        "Who won the 2024 Super Bowl",
        "Stock price of Tesla today"
    ]
    
    # Test queries that should use local knowledge base (high similarity)
    internal_queries = [
        "What is a neutron star?",
        "Space exploration missions",
        "Mars colonization",
        "Black holes physics",
        "NASA space shuttle"
    ]
    
    print("🌐 Testing External Queries (should trigger web search):")
    for query in external_queries:
        print(f"\n--- Query: '{query}' ---")
        try:
            result = await rag.search_query(query)
            method = result.get('method', 'unknown') if result else 'failed'
            
            if method == 'web_search':
                print(f"✅ CORRECT: Used web search")
            elif method == 'local_search':
                print(f"❌ WRONG: Used local search (should be web)")
            else:
                print(f"⚠️ UNKNOWN: Method={method}")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
    
    print(f"\n📚 Testing Internal Queries (should use local knowledge):")
    for query in internal_queries:
        print(f"\n--- Query: '{query}' ---")
        try:
            result = await rag.search_query(query)
            method = result.get('method', 'unknown') if result else 'failed'
            
            if method == 'local_search':
                print(f"✅ CORRECT: Used local search")
            elif method == 'web_search':
                print(f"⚠️ ACCEPTABLE: Used web search (local similarity < 0.4)")
            else:
                print(f"⚠️ UNKNOWN: Method={method}")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_web_search_logic())
        print(f"\n🎯 Test completed!")
        print(f"Check results above - external queries should use web search")
    except Exception as e:
        print(f"\n💥 Test error: {e}")