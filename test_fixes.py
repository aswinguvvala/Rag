#!/usr/bin/env python3
"""
Test script to validate the fixes for Earth-Sun distance and scoring system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import check_basic_space_facts
from hybrid_rag_system import HybridRAGSystem

def test_basic_facts():
    """Test that basic facts now catch Earth-Sun distance queries"""
    print("🧪 Testing Basic Facts Coverage...")
    
    test_queries = [
        "How far is the Sun from the Earth?",
        "What is the distance between Earth and the Sun?",
        "How far away is the sun?",
        "Earth sun distance",
        "astronomical unit",
        "what is an AU?"
    ]
    
    passed = 0
    failed = 0
    
    for query in test_queries:
        result = check_basic_space_facts(query)
        if result:
            print(f"✅ '{query}' -> Found basic fact")
            passed += 1
        else:
            print(f"❌ '{query}' -> Not found in basic facts")
            failed += 1
    
    print(f"\n📊 Basic Facts Test Results: {passed} passed, {failed} failed")
    return failed == 0

def test_semantic_search_scoring():
    """Test that semantic search scoring is now within 0-1 range"""
    print("\n🧪 Testing Semantic Search Scoring...")
    
    # Initialize RAG system
    rag = HybridRAGSystem()
    rag.initialize()
    
    # Test queries
    test_queries = [
        "How far is the Sun from the Earth?",
        "What are Jupiter's moons?",
        "Tell me about Mars exploration",
        "Recent SpaceX missions"
    ]
    
    all_scores_valid = True
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        results = rag.semantic_search(query, top_k=5)
        
        if not results:
            print(f"  ⚠️  No results found")
            continue
        
        for i, result in enumerate(results[:3], 1):
            score = result.get('relevance_score', 0)
            semantic = result.get('semantic_score', 0)
            content = result.get('content_relevance', 0)
            title = result.get('title', 'No title')[:50]
            
            print(f"  {i}. Score: {score:.3f} (Semantic: {semantic:.3f}, Content: {content:.3f})")
            print(f"     Title: {title}...")
            
            # Check if scores are in valid range
            if score > 1.0 or score < 0.0:
                print(f"     ❌ Invalid score: {score}")
                all_scores_valid = False
            elif semantic > 1.0 or semantic < 0.0:
                print(f"     ❌ Invalid semantic score: {semantic}")
                all_scores_valid = False
            elif content > 1.0 or content < 0.0:
                print(f"     ❌ Invalid content score: {content}")
                all_scores_valid = False
            else:
                print(f"     ✅ Valid scores")
    
    print(f"\n📊 Scoring Test Results: {'All scores valid' if all_scores_valid else 'Some scores invalid'}")
    return all_scores_valid

def test_end_to_end():
    """Test end-to-end query processing"""
    print("\n🧪 Testing End-to-End Query Processing...")
    
    # Initialize RAG system
    rag = HybridRAGSystem()
    rag.initialize()
    
    # Test the specific problematic query
    query = "How far is the Sun from the Earth?"
    print(f"Testing: '{query}'")
    
    response = rag.query(query)
    
    print(f"✅ Answer: {response.answer[:200]}...")
    print(f"✅ Confidence: {response.confidence:.2f}")
    print(f"✅ Method: {response.method_used}")
    print(f"✅ Processing time: {response.processing_time:.2f}s")
    print(f"✅ Sources: {len(response.sources)}")
    
    # Check if answer contains the expected information
    answer_lower = response.answer.lower()
    expected_terms = ['93 million', '150 million', 'astronomical unit', 'au', 'miles', 'kilometers']
    
    contains_expected = any(term in answer_lower for term in expected_terms)
    
    print(f"📊 End-to-End Test: {'✅ PASSED' if contains_expected else '❌ FAILED'}")
    print(f"   Expected to find distance information in answer: {contains_expected}")
    
    return contains_expected

def main():
    """Run all tests"""
    print("🚀 Running MSEIS RAG System Tests\n")
    
    # Run tests
    test1_passed = test_basic_facts()
    test2_passed = test_semantic_search_scoring()
    test3_passed = test_end_to_end()
    
    # Summary
    print("\n" + "="*60)
    print("📋 FINAL TEST SUMMARY")
    print("="*60)
    
    total_tests = 3
    passed_tests = sum([test1_passed, test2_passed, test3_passed])
    
    print(f"🧪 Basic Facts Coverage: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"🧪 Semantic Search Scoring: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"🧪 End-to-End Processing: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The Earth-Sun distance issue has been fixed.")
    else:
        print("⚠️  Some tests failed. Additional fixes may be needed.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    main() 