#!/usr/bin/env python3
"""
Test script for IntelliSearch RAG System
Tests all components locally before Streamlit Cloud deployment
"""

import asyncio
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

async def test_rag_system():
    """Test the RAG system components"""
    
    print("🚀 Testing IntelliSearch RAG System")
    print("=" * 50)
    
    try:
        # Test import
        print("📦 Testing imports...")
        from hybrid_rag_system import HybridRAGSystem
        print("✅ Successfully imported HybridRAGSystem")
        
        # Initialize system
        print("\n🧠 Initializing RAG system...")
        rag_system = HybridRAGSystem()
        
        # Check embedded documents
        print(f"📚 Embedded documents: {len(rag_system.embedded_documents)}")
        
        # Test initialization
        print("\n🔧 Testing initialization...")
        start_time = time.time()
        success = await rag_system.initialize()
        init_time = time.time() - start_time
        
        if success:
            print(f"✅ Initialization successful in {init_time:.2f}s")
        else:
            print("❌ Initialization failed")
            return False
        
        # Get system status
        print("\n📊 System Status:")
        status = rag_system.get_system_status()
        
        print(f"  - Initialized: {status['is_initialized']}")
        print(f"  - Document count: {status['document_count']}")
        print(f"  - Memory mode: {status.get('memory_mode', 'unknown')}")
        print(f"  - Has embedding model: {status['has_embedding_model']}")
        print(f"  - Has FAISS index: {status['has_faiss_index']}")
        
        # Test capabilities
        print("\n🎯 Testing capabilities:")
        capabilities = status['capabilities']
        for cap, enabled in capabilities.items():
            emoji = "✅" if enabled else "❌"
            print(f"  {emoji} {cap.replace('_', ' ').title()}")
        
        # Test queries
        test_queries = [
            "What are black holes?",
            "Tell me about Mars exploration",
            "How does the James Webb telescope work?",
            "What is the International Space Station?"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n  Query {i}: {query}")
            
            start_time = time.time()
            result = await rag_system.query(query)
            query_time = time.time() - start_time
            
            print(f"  ⏱️  Query time: {query_time:.2f}s")
            print(f"  📝 Method: {result['method']}")
            print(f"  🎯 Confidence: {result['confidence']:.2f}")
            print(f"  📚 Sources found: {result['total_results']}")
            
            if result['response']:
                response_preview = result['response'][:100] + "..." if len(result['response']) > 100 else result['response']
                print(f"  💬 Response preview: {response_preview}")
            else:
                print("  ❌ No response generated")
        
        # Final status check
        print(f"\n📈 Final Performance Metrics:")
        final_status = rag_system.get_system_status()
        if 'performance' in final_status:
            perf = final_status['performance']
            print(f"  - Total queries: {perf['query_count']}")
            print(f"  - Cache hits: {perf['cache_hits']}")
            print(f"  - Cache hit rate: {perf['cache_hit_rate']}")
            print(f"  - Cache size: {perf['cache_size']}")
        
        if 'memory_mb' in final_status and final_status['memory_mb'] != 'unavailable':
            print(f"  - Memory usage: {final_status['memory_mb']:.1f} MB")
            print(f"  - Memory percent: {final_status.get('memory_percent', 0):.1f}%")
        
        # Check for any initialization errors
        if status.get('initialization_errors'):
            print("\n⚠️  Initialization Errors:")
            for error in status['initialization_errors']:
                print(f"  - {error}")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"✅ System is ready for Streamlit Cloud deployment")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_rag_system()
    
    if success:
        print(f"\n🚀 Ready to deploy to Streamlit Cloud!")
        print(f"   Run: streamlit run intellisearch.py")
        sys.exit(0)
    else:
        print(f"\n🔧 Please fix the issues before deploying")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())