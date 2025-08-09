#!/usr/bin/env python3
"""
Update Space Content - Integrate scraped content into knowledge base
"""

import asyncio
import json
from pathlib import Path
from space_content_scraper import SpaceContentScraper
import time

async def update_knowledge_base():
    """Update the knowledge base with fresh space content"""
    print("🚀 Updating knowledge base with fresh space content...")
    
    # Scrape fresh content
    async with SpaceContentScraper() as scraper:
        content = await scraper.get_all_content(max_articles=25, max_facts=20)
    
    # Load existing knowledge base
    kb_path = Path("data/knowledge_base.json")
    if kb_path.exists():
        with open(kb_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = {"articles": [], "metadata": {"total_articles": 0, "sources": [], "categories": []}}
    
    # Convert scraped articles to knowledge base format
    new_articles = []
    for article in content['articles']:
        kb_article = {
            "title": article.title,
            "content": article.content,
            "category": article.category,
            "topics": article.topics or [],
            "source": f"{article.source} - {article.url}",
            "scraped_at": time.time()
        }
        new_articles.append(kb_article)
    
    # Convert facts to articles format for the knowledge base
    for fact in content['facts']:
        fact_article = {
            "title": f"Space Fact: {fact.fact[:50]}...",
            "content": fact.fact,
            "category": "space_facts",
            "topics": ["space", "facts", "astronomy"],
            "source": fact.source,
            "scraped_at": time.time()
        }
        new_articles.append(fact_article)
    
    # Add new content to existing
    existing_data["articles"].extend(new_articles)
    
    # Update metadata
    existing_categories = set(existing_data.get("metadata", {}).get("categories", []))
    new_categories = set([article.get("category", "general") for article in new_articles])
    all_categories = list(existing_categories.union(new_categories))
    
    existing_sources = set(existing_data.get("metadata", {}).get("sources", []))
    new_sources = set([article.get("source", "").split(" - ")[0] for article in new_articles])
    all_sources = list(existing_sources.union(new_sources))
    
    existing_data["metadata"] = {
        "total_articles": len(existing_data["articles"]),
        "sources": all_sources,
        "categories": all_categories,
        "last_updated": time.time(),
        "scraped_content_added": len(new_articles)
    }
    
    # Save updated knowledge base
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Knowledge base updated!")
    print(f"📊 Added {len(new_articles)} new items ({len(content['articles'])} articles + {len(content['facts'])} facts)")
    print(f"📈 Total articles in knowledge base: {existing_data['metadata']['total_articles']}")
    
    # Save space facts separately for UI display
    facts_data = {
        "facts": [{"fact": fact.fact, "source": fact.source} for fact in content['facts']],
        "metadata": {
            "total_facts": len(content['facts']),
            "updated_at": time.time()
        }
    }
    
    facts_path = Path("storage/space_facts.json")
    facts_path.parent.mkdir(exist_ok=True)
    with open(facts_path, 'w', encoding='utf-8') as f:
        json.dump(facts_data, f, indent=2, ensure_ascii=False)
    
    print(f"💫 Space facts saved to {facts_path}")

if __name__ == "__main__":
    asyncio.run(update_knowledge_base())