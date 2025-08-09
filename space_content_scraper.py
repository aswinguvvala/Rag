#!/usr/bin/env python3
"""
Space Content Scraper - Web scraping for space articles and facts
Scrapes from NASA, Space.com, and other reliable space sources
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import random
import time

@dataclass
class SpaceArticle:
    """Structure for scraped space articles"""
    title: str
    content: str
    source: str
    url: str
    category: str = "space"
    topics: List[str] = None

@dataclass
class SpaceFact:
    """Structure for space facts"""
    fact: str
    source: str
    category: str = "general"

class SpaceContentScraper:
    """Scraper for space articles and facts"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_nasa_news(self, max_articles: int = 10) -> List[SpaceArticle]:
        """Scrape latest news from NASA"""
        articles = []
        try:
            print("🔭 Scraping NASA news...")
            
            # NASA RSS feed approach for reliability
            rss_url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
            
            async with self.session.get(rss_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'xml')
                    
                    items = soup.find_all('item')[:max_articles]
                    for item in items:
                        try:
                            title = item.find('title').text.strip()
                            description = item.find('description').text.strip()
                            link = item.find('link').text.strip()
                            
                            # Clean up the description
                            description = re.sub(r'<[^>]+>', '', description)
                            
                            articles.append(SpaceArticle(
                                title=title,
                                content=description,
                                source="NASA",
                                url=link,
                                category="nasa_news",
                                topics=["nasa", "space", "exploration"]
                            ))
                            print(f"  ✅ Scraped: {title[:50]}...")
                            
                        except Exception as e:
                            print(f"  ⚠️ Error parsing NASA article: {e}")
                            continue
                            
        except Exception as e:
            print(f"❌ Error scraping NASA news: {e}")
            
        return articles
    
    async def scrape_space_com_articles(self, max_articles: int = 8) -> List[SpaceArticle]:
        """Scrape articles from Space.com"""
        articles = []
        try:
            print("🚀 Scraping Space.com articles...")
            
            # Space.com homepage to get article links
            base_url = "https://www.space.com"
            
            async with self.session.get(f"{base_url}/news") as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find article links (common pattern for news sites)
                    article_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        if href and ('/news/' in href or '/science/' in href):
                            full_url = urljoin(base_url, href)
                            if full_url not in article_links:
                                article_links.append(full_url)
                    
                    # Scrape individual articles
                    for i, url in enumerate(article_links[:max_articles]):
                        try:
                            await asyncio.sleep(1)  # Be respectful to the server
                            article = await self._scrape_space_com_article(url)
                            if article:
                                articles.append(article)
                                print(f"  ✅ Scraped: {article.title[:50]}...")
                                
                        except Exception as e:
                            print(f"  ⚠️ Error scraping article {url}: {e}")
                            continue
                            
        except Exception as e:
            print(f"❌ Error scraping Space.com: {e}")
            
        return articles
    
    async def _scrape_space_com_article(self, url: str) -> Optional[SpaceArticle]:
        """Scrape individual Space.com article"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract title
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "Space Article"
                    
                    # Extract article content
                    content_text = ""
                    
                    # Try different content selectors
                    content_selectors = [
                        'div.article-content',
                        'div.entry-content', 
                        'article p',
                        'div.content p'
                    ]
                    
                    for selector in content_selectors:
                        paragraphs = soup.select(selector)
                        if paragraphs:
                            content_text = ' '.join([p.get_text().strip() for p in paragraphs[:3]])
                            break
                    
                    if not content_text:
                        # Fallback: get first few paragraphs
                        paragraphs = soup.find_all('p')[:3]
                        content_text = ' '.join([p.get_text().strip() for p in paragraphs])
                    
                    # Clean up content
                    content_text = re.sub(r'\s+', ' ', content_text).strip()
                    
                    if title and content_text and len(content_text) > 50:
                        return SpaceArticle(
                            title=title,
                            content=content_text[:500] + "..." if len(content_text) > 500 else content_text,
                            source="Space.com",
                            url=url,
                            category="space_news",
                            topics=["space", "astronomy", "science"]
                        )
                        
        except Exception as e:
            print(f"Error scraping individual article: {e}")
            
        return None
    
    async def scrape_space_facts(self, max_facts: int = 15) -> List[SpaceFact]:
        """Scrape interesting space facts"""
        facts = []
        
        # Curated space facts (reliable source)
        curated_facts = [
            "One day on Venus is longer than its year - Venus rotates so slowly that a day lasts 243 Earth days, while its year is only 225 Earth days.",
            "Neutron stars are so dense that a teaspoon of neutron star material would weigh about 6 billion tons on Earth.",
            "The Milky Way galaxy is on a collision course with the Andromeda galaxy, expected to merge in about 4.5 billion years.",
            "Jupiter's Great Red Spot is a storm that has been raging for at least 350 years and is larger than Earth.",
            "Saturn's moon Titan has lakes and rivers of liquid methane and ethane instead of water.",
            "The Sun contains 99.86% of the mass in our solar system, with Jupiter containing most of the remainder.",
            "Space is completely silent because sound needs a medium to travel through, and there's no air in space.",
            "The International Space Station travels at 17,500 mph and orbits Earth every 90 minutes.",
            "A black hole's gravity is so strong that not even light can escape once it crosses the event horizon.",
            "Mars has the largest volcano in the solar system - Olympus Mons is 13.6 miles high, nearly three times taller than Mount Everest.",
            "The observable universe contains at least 2 trillion galaxies, each with billions of stars.",
            "Light from the Sun takes 8 minutes and 20 seconds to reach Earth.",
            "Pluto takes 248 Earth years to complete one orbit around the Sun.",
            "The Hubble Space Telescope has traveled more than 4 billion miles in its orbit around Earth.",
            "One million Earths could fit inside the Sun, and 1,300 Earths could fit inside Jupiter.",
            "The coldest place in the universe is the Boomerang Nebula at -458°F (-272°C).",
            "Astronauts can grow up to 2 inches taller in space due to the lack of gravity compressing their spine.",
            "A day on Mercury lasts 59 Earth days, but its year is only 88 Earth days.",
            "The footprints left by Apollo astronauts on the Moon will last millions of years due to no wind or water erosion.",
            "Galaxies are moving away from us due to the expansion of the universe, discovered by Edwin Hubble in 1929."
        ]
        
        # Select random facts
        selected_facts = random.sample(curated_facts, min(max_facts, len(curated_facts)))
        
        for fact in selected_facts:
            facts.append(SpaceFact(
                fact=fact,
                source="Curated Space Knowledge",
                category="space_facts"
            ))
            
        print(f"📚 Generated {len(facts)} space facts")
        return facts
    
    async def get_all_content(self, max_articles: int = 20, max_facts: int = 15) -> Dict[str, Any]:
        """Get all space content - articles and facts"""
        all_articles = []
        all_facts = []
        
        print("🌌 Starting space content collection...")
        
        try:
            # Scrape NASA articles
            nasa_articles = await self.scrape_nasa_news(max_articles // 2)
            all_articles.extend(nasa_articles)
            
            # Scrape Space.com articles  
            space_com_articles = await self.scrape_space_com_articles(max_articles // 2)
            all_articles.extend(space_com_articles)
            
            # Get space facts
            all_facts = await self.scrape_space_facts(max_facts)
            
        except Exception as e:
            print(f"❌ Error during content collection: {e}")
        
        print(f"✅ Collection complete: {len(all_articles)} articles, {len(all_facts)} facts")
        
        return {
            "articles": all_articles,
            "facts": all_facts,
            "metadata": {
                "scraped_at": time.time(),
                "total_articles": len(all_articles),
                "total_facts": len(all_facts),
                "sources": ["NASA", "Space.com", "Curated"]
            }
        }

async def main():
    """Test the scraper"""
    async with SpaceContentScraper() as scraper:
        content = await scraper.get_all_content(max_articles=10, max_facts=10)
        
        print("\n📊 Summary:")
        print(f"Articles: {len(content['articles'])}")
        print(f"Facts: {len(content['facts'])}")
        
        # Show samples
        if content['articles']:
            print(f"\n📰 Sample article: {content['articles'][0].title}")
        if content['facts']:
            print(f"🌟 Sample fact: {content['facts'][0].fact[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())