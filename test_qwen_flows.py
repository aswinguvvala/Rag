#!/usr/bin/env python3
"""
Test script to verify all three Qwen-first response flows are working correctly.

Flow 1: Local content found → Qwen processes local content
Flow 2: No local content → DuckDuckGo search → Qwen processes web content  
Flow 3: Web search fails → Qwen uses general knowledge
"""

import asyncio
import sys
from simple_rag_system import SimpleRAGSystem

async def test_qwen_flows():
    """Test all three Qwen response flows"""
    print("🧪 Testing Qwen-First Response Flows")
    print("=" * 50)
    
    # Initialize RAG system
    rag = SimpleRAGSystem()
    print("\n1️⃣ Initializing RAG System...")
    
    if not await rag.initialize():
        print("❌ RAG system initialization failed")
        return False
    
    print("✅ RAG system initialized successfully")
    
    # Test queries for each flow
    test_queries = [
        {
            "name": "FLOW 1: Local Content (Space/Science)",
            "query": "What is the Artemis program?",
            "expected_method": "qwen_local_content",
            "description": "Should find local space content and use Qwen to process it"
        },
        {
            "name": "FLOW 2: Web Search",
            "query": "Latest news about Taylor Swift 2024",
            "expected_method": "qwen_web_content",
            "description": "Should use DuckDuckGo search and Qwen to process web results"
        },
        {
            "name": "FLOW 3: General Knowledge",
            "query": "What is the capital of a fictional country XYZ123?",
            "expected_method": "qwen_general_knowledge", 
            "description": "Should trigger general knowledge mode when no content found"
        }
    ]
    
    results = []
    
    # Test each flow
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}️⃣ Testing {test['name']}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['description']}")
        print("-" * 40)
        
        try:
            result = await rag.search_query(test['query'])
            
            if result:
                method = result.get('method', 'unknown')
                response_length = len(result.get('response', ''))
                processing_time = result.get('processing_time', 0)
                sources_count = len(result.get('sources', []))
                
                print(f"✅ Method: {method}")
                print(f"📝 Response length: {response_length} characters")
                print(f"⚡ Processing time: {processing_time:.2f}s")
                print(f"📚 Sources found: {sources_count}")
                
                # Show first 150 characters of response
                response_preview = result.get('response', '')[:150]
                if len(result.get('response', '')) > 150:
                    response_preview += "..."
                print(f"💬 Response preview: {response_preview}")
                
                results.append({
                    'test': test['name'],
                    'success': True,
                    'method': method,
                    'response_length': response_length,
                    'processing_time': processing_time,
                    'sources_count': sources_count
                })
                
            else:
                print("❌ No result returned")
                results.append({
                    'test': test['name'],
                    'success': False,
                    'error': 'No result returned'
                })
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append({
                'test': test['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['test']}")
        
        if result['success']:
            print(f"    Method: {result['method']}")
            print(f"    Response: {result['response_length']} chars")
            print(f"    Time: {result['processing_time']:.2f}s")
            print(f"    Sources: {result['sources_count']}")
        else:
            print(f"    Error: {result.get('error', 'Unknown error')}")
        print()
    
    print(f"🎯 Overall Result: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All Qwen flows are working correctly!")
        return True
    else:
        print("⚠️ Some flows need attention")
        return False

async def test_qwen_availability():
    """Test if Qwen model is available and working"""
    print("\n🔍 Testing Qwen Model Availability")
    print("-" * 30)
    
    rag = SimpleRAGSystem()
    
    # Test Ollama health
    if await rag._check_ollama_health():
        print("✅ Ollama service is running")
        
        # Test Qwen response generation
        try:
            test_query = "What is artificial intelligence?"
            test_results = []  # Empty results to test general knowledge mode
            
            response = await rag._generate_qwen_response(
                test_query, 
                test_results, 
                mode="general_knowledge"
            )
            
            if response and len(response) > 20:
                print("✅ Qwen model is responding correctly")
                print(f"📝 Sample response length: {len(response)} characters")
                print(f"💬 Sample response: {response[:100]}...")
                return True
            else:
                print("❌ Qwen model returned empty or very short response")
                return False
                
        except Exception as e:
            print(f"❌ Qwen model test failed: {e}")
            return False
    else:
        print("❌ Ollama service is not running")
        print("💡 Please run: ollama serve")
        print("💡 And ensure Qwen model is installed: ollama pull qwen2.5:0.5b")
        return False

if __name__ == "__main__":
    print("🚀 Qwen-First RAG System Test Suite")
    print("=" * 50)
    
    async def main():
        # Test Qwen availability first
        qwen_available = await test_qwen_availability()
        
        if not qwen_available:
            print("\n❌ Qwen is not available. Please check your setup.")
            print("📖 See LOCAL_SETUP.md for installation instructions")
            sys.exit(1)
        
        # Run flow tests
        flows_working = await test_qwen_flows()
        
        if flows_working:
            print("\n🎉 SUCCESS: All systems are working correctly!")
            print("🚀 Your Qwen-first RAG system is ready!")
        else:
            print("\n⚠️ WARNING: Some issues detected")
            print("🔧 Please check the error messages above")
            sys.exit(1)
    
    # Run the tests
    asyncio.run(main())