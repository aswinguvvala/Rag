#!/usr/bin/env python3
"""Test script to verify the improved RAG system with LLM integration"""

from hybrid_rag_system import HybridRAGSystem
from llm_integration import ollama_llm
import time

def test_query(rag_system, query, description):
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")
    
    start_time = time.time()
    response = rag_system.query(query, expertise_level="general")
    end_time = time.time()
    
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}")
    print(f"Method Used: {response.method_used}")
    print(f"Processing Time: {end_time - start_time:.2f}s")
    print(f"Sources: {len(response.sources)}")
    
    return response

def main():
    print("🧪 Testing Improved RAG System with LLM Integration")
    print("=" * 60)
    
    # Check if LLM is available
    print(f"LLM Service Available: {ollama_llm.is_available()}")
    
    # Initialize RAG system
    print("Initializing RAG system...")
    rag_system = HybridRAGSystem()
    rag_system.initialize()
    
    # Test 1: Out-of-domain query (should be detected and handled appropriately)
    test_query(
        rag_system,
        "Tell me about the hydrogen collider from CERN",
        "Out-of-domain query (particle physics)"
    )
    
    # Test 2: In-domain query (should use normal RAG)
    test_query(
        rag_system,
        "How many moons does Jupiter have?",
        "In-domain query (space exploration)"
    )
    
    # Test 3: General science query
    test_query(
        rag_system,
        "What is the speed of light?",
        "General science query"
    )
    
    # Test 4: Space technology query
    test_query(
        rag_system,
        "What is the James Webb Space Telescope?",
        "Space technology query"
    )
    
    print(f"\n{'='*60}")
    print("✅ Testing completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 