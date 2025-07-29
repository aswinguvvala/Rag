#!/usr/bin/env python3
"""
Quick Test - Verify the system works with large dataset
"""

import asyncio
from simple_rag_system import SimpleRAGSystem

async def quick_test():
    print("🧪 Quick Test: Large Dataset RAG System...")
    print("=" * 50)
    
    # Initialize system
    rag = SimpleRAGSystem()
    
    # Check system info before initialization
    print("📊 System Info Before Initialization:")
    info = rag.get_system_info()
    print(f"   Documents: {info['total_documents']}")
    print(f"   Data Source: {info['data_source']}")
    print(f"   Knowledge Base Available: {info['knowledge_base_available']}")
    
    print("\n🔧 Initializing system (this may take a moment for large datasets)...")
    
    # Test initialization
    init_success = await rag.initialize()
    
    if init_success:
        print("✅ Initialization successful!")
        
        # Get updated system info
        info = rag.get_system_info()
        print(f"\n📈 System Stats:")
        print(f"   📚 Total Documents: {info['total_documents']}")
        print(f"   🗃️ Data Source: {info['data_source']}")
        print(f"   📊 Categories: {info['total_categories']}")
        print(f"   📝 Content: {info['content_stats']['total_characters']}")
        
        # Quick query test
        print(f"\n🔍 Testing quick query...")
        try:
            result = await rag.search_query("What is a neutron star?")
            
            if result and result.get('response'):
                print(f"✅ Query successful!")
                print(f"   📖 Method: {result['method']}")
                print(f"   📚 Sources: {len(result['sources'])}")
                print(f"   ⚡ Time: {result['processing_time']:.2f}s")
                print(f"   💬 Response Preview: {result['response'][:150]}...")
                
                return True
            else:
                print("❌ Query failed - no response generated")
                return False
                
        except Exception as e:
            print(f"❌ Query error: {e}")
            return False
    else:
        print("❌ Initialization failed")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(quick_test())
        if success:
            print("\n🎉 SUCCESS: System working with large dataset!")
        else:
            print("\n❌ FAILED: Issues detected")
            exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        exit(1)