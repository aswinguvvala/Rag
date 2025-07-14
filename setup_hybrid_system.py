#!/usr/bin/env python3
"""
Setup script for Hybrid RAG System
This script installs dependencies and tests the system components
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "hybrid_requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🧪 Testing imports...")
    
    required_modules = [
        "streamlit",
        "requests", 
        "bs4",
        "numpy",
        "sentence_transformers",
        "faiss",
        "feedparser",
        "arxiv"
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

def test_system_components():
    """Test the hybrid system components"""
    print("\n🔧 Testing system components...")
    
    try:
        # Test web search manager
        print("Testing WebSearchManager...")
        from web_search_manager import WebSearchManager
        search_manager = WebSearchManager()
        print("✅ WebSearchManager initialized")
        
        # Test confidence evaluator
        print("Testing ConfidenceEvaluator...")
        from confidence_evaluator import ConfidenceEvaluator
        evaluator = ConfidenceEvaluator()
        
        # Test domain relevance calculation
        space_query = "What is the James Webb Space Telescope?"
        general_query = "How to cook pasta?"
        
        space_relevance = evaluator.calculate_domain_relevance(space_query)
        general_relevance = evaluator.calculate_domain_relevance(general_query)
        
        print(f"✅ Space query relevance: {space_relevance:.2f}")
        print(f"✅ General query relevance: {general_relevance:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["rag_data", "web_cache", "logs"]
    
    for dir_name in directories:
        try:
            os.makedirs(dir_name, exist_ok=True)
            print(f"✅ Created/verified {dir_name}/")
        except Exception as e:
            print(f"❌ Failed to create {dir_name}/: {e}")
            return False
    
    return True

def run_basic_test():
    """Run a basic test of the system"""
    print("\n🚀 Running basic system test...")
    
    try:
        from hybrid_rag_system import HybridRAGSystem
        
        # Initialize system
        system = HybridRAGSystem()
        print("✅ HybridRAGSystem initialized")
        
        # Test sentence transformer model
        print("Loading sentence transformer model...")
        system.initialize()
        print("✅ Model loaded successfully")
        
        # Test web search (basic)
        print("Testing web search...")
        test_query = "What is Python programming?"
        results = system.web_search_manager.search_duckduckgo(test_query, 3)
        print(f"✅ Web search returned {len(results)} results")
        
        # Test confidence evaluation
        print("Testing confidence evaluation...")
        confidence = system.confidence_evaluator.calculate_domain_relevance(test_query)
        print(f"✅ Confidence evaluation: {confidence:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Hybrid RAG System Setup")
    print("=" * 50)
    
    success = True
    
    # Step 1: Create directories
    if not create_directories():
        success = False
    
    # Step 2: Install requirements
    if not install_requirements():
        success = False
    
    # Step 3: Test imports
    if not test_imports():
        success = False
    
    # Step 4: Test components
    if not test_system_components():
        success = False
    
    # Step 5: Run basic test
    if not run_basic_test():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python3 -m streamlit run hybrid_rag_system.py")
        print("2. Build the knowledge base using the sidebar")
        print("3. Start asking questions!")
    else:
        print("❌ Setup encountered issues. Please check the errors above.")
        
    return success

if __name__ == "__main__":
    main() 