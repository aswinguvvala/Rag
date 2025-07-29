#!/usr/bin/env python3
"""
Knowledge Base Consolidation Script
Consolidates scraped articles from multiple sources into a unified knowledge base
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Set
import hashlib

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON file with error handling"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        else:
            print(f"⚠️ File not found: {file_path}")
            return []
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return []

def clean_and_validate_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate article data"""
    # Required fields
    if not article.get('title') or not article.get('content'):
        return None
    
    # Ensure content has minimum length (avoid empty or very short articles)
    content = article.get('content', '').strip()
    if len(content) < 100:  # Minimum 100 characters
        return None
    
    # Clean and structure the article data
    cleaned_article = {
        'title': article.get('title', '').strip(),
        'content': content,
        'url': article.get('url', ''),
        'source': article.get('source', 'Unknown'),
        'category': article.get('category', 'general'),
        'topics': article.get('topics', [])
    }
    
    # Ensure topics is a list
    if not isinstance(cleaned_article['topics'], list):
        cleaned_article['topics'] = []
    
    # Add content hash for deduplication
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    cleaned_article['content_hash'] = content_hash
    
    return cleaned_article

def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate articles based on content hash"""
    seen_hashes: Set[str] = set()
    deduplicated = []
    
    for article in articles:
        content_hash = article.get('content_hash')
        if content_hash and content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            deduplicated.append(article)
        else:
            print(f"🔄 Skipping duplicate: {article.get('title', 'Unknown')[:50]}...")
    
    return deduplicated

def consolidate_knowledge_base():
    """Main consolidation function"""
    print("🚀 Starting Knowledge Base Consolidation...")
    print("=" * 60)
    
    # Define source files
    storage_dir = Path("storage")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    source_files = [
        storage_dir / "scraped_articles.json",
        storage_dir / "test_space_articles.json"
    ]
    
    all_articles = []
    total_loaded = 0
    
    # Load articles from each source
    for source_file in source_files:
        print(f"\n📖 Loading: {source_file}")
        articles = load_json_file(source_file)
        
        if articles:
            print(f"   Found {len(articles)} articles")
            
            # Clean and validate articles
            cleaned_articles = []
            for article in articles:
                cleaned = clean_and_validate_article(article)
                if cleaned:
                    cleaned_articles.append(cleaned)
            
            print(f"   ✅ {len(cleaned_articles)} articles after cleaning")
            all_articles.extend(cleaned_articles)
            total_loaded += len(cleaned_articles)
        else:
            print(f"   ⚠️ No valid articles found")
    
    print(f"\n📊 Total articles loaded: {total_loaded}")
    
    # Deduplicate articles
    print("\n🔄 Removing duplicates...")
    deduplicated_articles = deduplicate_articles(all_articles)
    print(f"✅ {len(deduplicated_articles)} unique articles after deduplication")
    
    # Add some metadata
    knowledge_base = {
        "metadata": {
            "total_articles": len(deduplicated_articles),
            "sources": [str(f) for f in source_files if f.exists()],
            "categories": list(set([article.get('category', 'general') for article in deduplicated_articles])),
            "consolidation_date": "2025-01-29",
            "description": "Consolidated knowledge base from scraped articles and space content"
        },
        "articles": deduplicated_articles
    }
    
    # Save consolidated knowledge base
    output_file = data_dir / "knowledge_base.json"
    print(f"\n💾 Saving consolidated knowledge base to: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully saved {len(deduplicated_articles)} articles")
        
        # Display statistics
        print(f"\n📈 Knowledge Base Statistics:")
        print(f"   📚 Total Articles: {len(deduplicated_articles)}")
        print(f"   📊 Categories: {len(knowledge_base['metadata']['categories'])}")
        
        # Show top categories
        category_counts = {}
        for article in deduplicated_articles:
            category = article.get('category', 'general')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"   🏷️ Top Categories:")
        for category, count in top_categories:
            print(f"      {category}: {count} articles")
        
        # Show content stats
        total_content_length = sum(len(article.get('content', '')) for article in deduplicated_articles)
        avg_content_length = total_content_length / len(deduplicated_articles)
        print(f"   📝 Average Article Length: {avg_content_length:.0f} characters")
        print(f"   📖 Total Content: {total_content_length:,} characters")
        
        print(f"\n🎉 Knowledge base consolidation completed successfully!")
        print(f"💡 Your RAG system will now have access to {len(deduplicated_articles)} high-quality articles!")
        
    except Exception as e:
        print(f"❌ Error saving knowledge base: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = consolidate_knowledge_base()
    if not success:
        exit(1)