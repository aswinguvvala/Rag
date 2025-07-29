#!/usr/bin/env python3
"""
Test OpenAI Integration - Verify the cost-optimized OpenAI setup works
"""

import asyncio
import os
from simple_rag_system import SimpleRAGSystem

async def test_openai_integration():
    print("🧪 Testing OpenAI Integration for RAG System...")
    print("=" * 60)
    
    # Check environment variables
    print("🔧 Environment Check:")
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"   ✅ OPENAI_API_KEY: {'*' * 10}{api_key[-4:]}")
    else:
        print("   ❌ OPENAI_API_KEY: Not set")
        print("   💡 Tip: Set your OpenAI API key with:")
        print("       export OPENAI_API_KEY='your-key-here'")
        return False
    
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    max_tokens = os.getenv('OPENAI_MAX_TOKENS', '150')
    print(f"   🤖 Model: {model}")
    print(f"   🎯 Max Tokens: {max_tokens}")
    print(f"   💰 Est. Cost per Query: ~$0.001")
    
    # Initialize RAG system
    print(f"\n🚀 Initializing RAG System...")
    rag = SimpleRAGSystem()
    
    # Check OpenAI availability
    print(f"   OpenAI Available: {rag.openai_available}")
    print(f"   OpenAI Client: {rag.openai_client is not None}")
    
    if not rag.openai_available:
        print("❌ OpenAI not available - check your setup")
        return False
    
    # Initialize the system
    print(f"\n⚙️ Initializing system components...")
    init_success = await rag.initialize()
    
    if not init_success:
        print("❌ System initialization failed")
        return False
    
    print("✅ System initialized successfully!")
    
    # Get system info
    info = rag.get_system_info()
    print(f"\n📊 System Status:")
    print(f"   📚 Documents: {info['total_documents']}")
    print(f"   🗃️ Data Source: {info['data_source']}")
    config = info.get('configuration', {})
    print(f"   🤖 AI Model: {config.get('openai_model', 'N/A')}")
    print(f"   💰 Cost per Query: {config.get('estimated_cost_per_query', 'N/A')}")
    
    # Test a simple query
    print(f"\n🔍 Testing Query Processing...")
    test_query = "What is artificial intelligence?"
    
    print(f"   Query: '{test_query}'")
    print(f"   Processing... (this may take a moment)")
    
    try:
        result = await rag.search_query(test_query)
        
        if result and result.get('response'):
            print(f"✅ Query successful!")
            print(f"   📖 Method: {result.get('method', 'Unknown')}")
            print(f"   📚 Sources: {len(result.get('sources', []))}")
            print(f"   ⚡ Time: {result.get('processing_time', 0):.2f}s")
            print(f"   💬 Response Preview: {result['response'][:100]}...")
            
            # Show cost tracking (from console output)
            print(f"\n💰 Cost Tracking:")
            print(f"   Check console output above for actual token usage and cost")
            
            return True
        else:
            print(f"❌ Query failed - no response generated")
            return False
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def show_setup_instructions():
    """Show setup instructions for OpenAI integration"""
    print("\n" + "=" * 60)
    print("🚀 OPENAI SETUP INSTRUCTIONS")
    print("=" * 60)
    print()
    print("1. Get OpenAI API Key:")
    print("   - Visit: https://platform.openai.com/api-keys")
    print("   - Create a new secret key")
    print("   - Add some credits ($5-10 minimum)")
    print()
    print("2. Set Environment Variable:")
    print("   export OPENAI_API_KEY='your-key-here'")
    print()
    print("3. Optional Configuration:")
    print("   export OPENAI_MODEL='gpt-4o-mini'     # Cheapest model")
    print("   export OPENAI_MAX_TOKENS='150'        # Cost control")
    print()
    print("4. For Streamlit Cloud:")
    print("   - Go to app settings")
    print("   - Add OPENAI_API_KEY to secrets")
    print("   - Format: OPENAI_API_KEY = \"your-key-here\"")
    print()
    print("💰 Cost Analysis:")
    print("   - gpt-4o-mini: ~$0.001 per query")
    print("   - $10 budget: ~10,000 queries")
    print("   - Perfect for recruiter showcase!")

if __name__ == "__main__":
    try:
        success = asyncio.run(test_openai_integration())
        if success:
            print(f"\n🎉 SUCCESS: OpenAI integration working perfectly!")
            print(f"💡 Your RAG system is now ready for recruiter showcase!")
        else:
            print(f"\n❌ SETUP NEEDED: OpenAI integration requires configuration")
            show_setup_instructions()
    except KeyboardInterrupt:
        print(f"\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        show_setup_instructions()