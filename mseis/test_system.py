#!/usr/bin/env python3
"""
Simple test script for the restructured MSEIS system
"""

import asyncio
import sys
import os

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing imports...")
    
    try:
        # Test core modules
        from core.config import config
        print("✓ Core config imported successfully")
        
        from core.embeddings import CachedOpenAIEmbeddings
        print("✓ Core embeddings imported successfully")
        
        from core.retrievers import HybridRetriever
        print("✓ Core retrievers imported successfully")
        
        # Test utility modules
        from utils.logging_config import setup_logging, get_logger
        print("✓ Utils logging imported successfully")
        
        from utils.monitoring import monitor_performance
        print("✓ Utils monitoring imported successfully")
        
        from utils.rate_limiter import rate_limit
        print("✓ Utils rate limiter imported successfully")
        
        # Test agent modules
        from agents.base_agent import BaseAgent, QueryContext
        print("✓ Base agent imported successfully")
        
        from agents.document_agent import DocumentAgent
        print("✓ Document agent imported successfully")
        
        from agents.image_agent import ImageAgent
        print("✓ Image agent imported successfully")
        
        # Test storage modules
        from storage.pinecone_manager import PineconeManager
        print("✓ Pinecone manager imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

async def test_config():
    """Test configuration system"""
    print("\nTesting configuration...")
    
    try:
        from core.config import config
        
        # Test configuration access
        system_name = config.system.name
        print(f"✓ System name: {system_name}")
        
        log_level = config.system.log_level
        print(f"✓ Log level: {log_level}")
        
        # Test dot notation config access
        chunk_size = config.get("agents.document.chunk_size", 1000)
        print(f"✓ Document chunk size: {chunk_size}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

async def test_logging():
    """Test logging system"""
    print("\nTesting logging...")
    
    try:
        from utils.logging_config import setup_logging, get_logger
        
        # Setup logging
        setup_logging("INFO")
        print("✓ Logging setup successful")
        
        # Test logger creation
        logger = get_logger("test")
        logger.info("Test log message")
        print("✓ Logger created and used successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Logging error: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    print("\nTesting basic functionality...")
    
    try:
        from agents.base_agent import QueryContext
        from utils.monitoring import get_all_metrics
        
        # Test QueryContext creation
        context = QueryContext(
            query_id="test-001",
            original_query="Test query",
            user_expertise_level="general"
        )
        print(f"✓ QueryContext created: {context.query_id}")
        
        # Test metrics system
        metrics = get_all_metrics()
        print(f"✓ Metrics system accessible: {type(metrics)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality error: {e}")
        return False

async def test_system_structure():
    """Test the overall system structure"""
    print("\nTesting system structure...")
    
    try:
        # Check if main entry point exists
        from main import app
        print("✓ Main FastAPI app accessible")
        
        # Check required directories exist
        import os
        required_dirs = [
            "agents", "core", "data_sources", "storage", 
            "evaluation", "utils", "tests"
        ]
        
        for directory in required_dirs:
            if os.path.exists(directory):
                print(f"✓ Directory exists: {directory}")
            else:
                print(f"✗ Missing directory: {directory}")
                
        return True
        
    except Exception as e:
        print(f"✗ System structure error: {e}")
        return False

def display_structure():
    """Display the current project structure"""
    print("\nProject Structure:")
    print("=" * 50)
    
    import os
    
    def print_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
            
        try:
            items = sorted(os.listdir(directory))
            for i, item in enumerate(items):
                if item.startswith('.'):
                    continue
                    
                path = os.path.join(directory, item)
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item}")
                
                if os.path.isdir(path) and current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(path, next_prefix, max_depth, current_depth + 1)
                    
        except PermissionError:
            pass
    
    print_tree(".")

async def main():
    """Main test function"""
    print("MSEIS System Restructuring Test")
    print("=" * 50)
    
    # Display the structure first
    display_structure()
    
    # Run all tests
    tests = [
        test_imports(),
        test_config(),
        test_logging(),
        test_basic_functionality(),
        test_system_structure()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Count successes
    successes = sum(1 for result in results if result is True)
    total_tests = len(tests)
    
    print(f"\nTest Results: {successes}/{total_tests} tests passed")
    
    if successes == total_tests:
        print("🎉 All tests passed! The system restructuring is successful.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 