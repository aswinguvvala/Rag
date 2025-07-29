#!/usr/bin/env python3
"""
Test Wimbledon Query - Verify the complete fix works end-to-end
"""

import asyncio
from simple_rag_system import SimpleRAGSystem

async def test_wimbledon_query():
    print("🔍 Testing Complete Wimbledon Query Fix")
    print("=" * 60)
    
    # Initialize system
    rag = SimpleRAGSystem()
    await rag.initialize()
    
    # Test the problematic query
    query = "Wimbledon 2023 winner"
    print(f"🎾 Testing query: '{query}'")
    
    try:
        result = await rag.search_query(query)
        
        if result and result.get('response'):
            print(f"✅ SUCCESS!")
            print(f"   Method: {result.get('method', 'Unknown')}")
            print(f"   Sources: {len(result.get('sources', []))}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   Response: {result['response'][:200]}...")
            
            # Show sources
            sources = result.get('sources', [])
            if sources:
                print(f"\n📚 Sources used:")
                for i, source in enumerate(sources[:3], 1):
                    print(f"   {i}. {source.get('title', 'No title')[:50]}...")
                    print(f"      Type: {source.get('source_type', 'unknown')}")
            
            return True
        else:
            print(f"❌ FAILED: No response generated")
            return False
            
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_wimbledon_query())
        if success:
            print(f"\n🎉 The fix is working! Wimbledon query now returns proper results.")
        else:
            print(f"\n❌ Fix still needs work - check debug output above.")
    except Exception as e:
        print(f"\n💥 Test error: {e}")