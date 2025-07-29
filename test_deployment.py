#!/usr/bin/env python3
"""
Deployment Test Script - Verify RAG System Functionality
Run this script to test your deployment and identify issues
"""

import asyncio
import sys
import os
from simple_rag_system import SimpleRAGSystem

async def test_deployment():
    """Comprehensive deployment test"""
    print("🧪 Testing RAG System Deployment...")
    print("=" * 50)
    
    # Initialize system
    rag = SimpleRAGSystem()
    
    # Test initialization
    print("\n1. Testing System Initialization...")
    init_success = await rag.initialize()
    
    if not init_success:
        print("❌ Initialization failed - this may cause issues")
    else:
        print("✅ Initialization successful")
    
    # Get system info
    print("\n2. System Information:")
    try:
        info = rag.get_system_info()
        print(f"   📚 Total Documents: {info['total_documents']}")
        print(f"   🧠 Embedding Model: {'✅' if info['embedding_model_available'] else '❌'}")
        print(f"   🔍 FAISS Index: {'✅' if info['faiss_index_available'] else '❌'}")
        print(f"   🌐 Web Search: {'✅' if info['web_search_available'] else '❌'}")
        print(f"   📊 Knowledge Domains: {len(info['document_categories'])}")
        print(f"   🏠 Environment: {'Streamlit Cloud' if info['environment']['streamlit_cloud'] else 'Local'}")
        
        # Show categories
        if info['document_categories']:
            print(f"   📋 Categories: {', '.join(info['document_categories'][:5])}")
            if len(info['document_categories']) > 5:
                print(f"       + {len(info['document_categories'])-5} more...")
        
    except Exception as e:
        print(f"   ❌ Failed to get system info: {e}")
    
    # Test query processing
    print("\n3. Testing Query Processing...")
    test_queries = [
        "What is the Artemis program?",
        "Tell me about artificial intelligence",
        "How do black holes work?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Test Query {i}: '{query}'")
        try:
            result = await rag.search_query(query)
            
            if result['response']:
                print(f"   ✅ Response generated ({len(result['response'])} chars)")
                print(f"   📖 Method: {result['method']}")
                print(f"   📚 Sources: {len(result['sources'])}")
                print(f"   ⚡ Time: {result['processing_time']:.2f}s")
                
                # Show first 100 chars of response
                preview = result['response'][:100] + "..." if len(result['response']) > 100 else result['response']
                print(f"   💬 Preview: {preview}")
            else:
                print("   ❌ No response generated")
                print(f"   📖 Method: {result.get('method', 'unknown')}")
        
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
    
    # Performance assessment
    print("\n4. Performance Assessment:")
    
    doc_count = len(rag.documents) if hasattr(rag, 'documents') else 0
    
    if doc_count >= 30:
        print("   🚀 Excellent: Comprehensive knowledge base available")
    elif doc_count >= 15:
        print("   ✅ Good: Adequate knowledge base for most queries")  
    elif doc_count >= 10:
        print("   ⚠️ Limited: Basic knowledge base, may miss some topics")
    else:
        print("   ❌ Poor: Very limited knowledge base")
    
    # Recommendations
    print("\n5. Recommendations:")
    
    if doc_count < 30:
        print("   📈 Knowledge base could be expanded for better coverage")
    
    if not rag.embedding_model:
        print("   🧠 Consider installing sentence-transformers for better search")
    
    if not rag.web_search_manager:
        print("   🌐 Web search fallback not available - install dependencies")
    
    # Overall status
    print("\n" + "=" * 50)
    
    if init_success and doc_count >= 10:
        print("🎉 DEPLOYMENT STATUS: FUNCTIONAL")
        print("   Your RAG system is working and should provide good results")
    elif doc_count >= 5:
        print("⚠️ DEPLOYMENT STATUS: LIMITED FUNCTIONALITY")
        print("   System works but with reduced capabilities")
    else:
        print("❌ DEPLOYMENT STATUS: ISSUES DETECTED")
        print("   System may not work properly - check logs above")
    
    print("\n💡 Tip: Run this script after deployment to verify everything works!")

if __name__ == "__main__":
    try:
        asyncio.run(test_deployment())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)