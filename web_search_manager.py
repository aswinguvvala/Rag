import requests
from bs4 import BeautifulSoup
import json
import hashlib
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from urllib.parse import quote_plus, urlparse
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Data class for search results"""
    title: str
    url: str
    snippet: str
    content: str = ""
    relevance_score: float = 0.0
    source: str = "web"

class WebSearchManager:
    """Manages web search operations and content extraction"""
    
    def __init__(self, cache_dir: str = "web_cache"):
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        os.makedirs(cache_dir, exist_ok=True)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1.0  # Minimum delay between requests
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str, max_age_hours: int = 24) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - file_time < timedelta(hours=max_age_hours)
    
    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def search_duckduckgo(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Search using DuckDuckGo (no API key required)
        This is a fallback when Google API is not available
        """
        # Check cache first
        cache_key = self._get_cache_key(f"ddg_{query}_{num_results}")
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_results = json.load(f)
                    return [SearchResult(**result) for result in cached_results]
            except:
                pass
        
        self._rate_limit()
        
        try:
            # Try DuckDuckGo instant answer API first
            results = self._try_ddg_instant_api(query, num_results)
            
            # If no good results, scrape web interface
            if len(results) < 3:
                web_results = self._scrape_duckduckgo_web(query, num_results)
                results.extend(web_results)
            
            # Remove duplicates
            seen_urls = set()
            unique_results = []
            for result in results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)
            
            # Cache results
            try:
                with open(cache_path, 'w') as f:
                    json.dump([result.__dict__ for result in unique_results], f)
            except:
                pass
            
            return unique_results[:num_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _try_ddg_instant_api(self, query: str, num_results: int) -> List[SearchResult]:
        """Try DuckDuckGo instant answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'pretty': '1',
                'no_redirect': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Extract results from DuckDuckGo response
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:num_results]:
                    if isinstance(topic, dict) and 'Text' in topic and 'FirstURL' in topic:
                        results.append(SearchResult(
                            title=topic.get('Text', '')[:100],
                            url=topic.get('FirstURL', ''),
                            snippet=topic.get('Text', ''),
                            source='duckduckgo_api'
                        ))
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo API failed: {e}")
            return []
    
    def _scrape_duckduckgo_web(self, query: str, num_results: int) -> List[SearchResult]:
        """Scrape DuckDuckGo web results as fallback"""
        try:
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            self._rate_limit()
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Find result containers (DuckDuckGo structure)
            result_divs = soup.find_all('div', class_='result')
            
            for div in result_divs[:num_results]:
                try:
                    # Extract title and URL
                    title_elem = div.find('a', class_='result__a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text().strip()
                    url = title_elem.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = div.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    
                    # Clean up DuckDuckGo redirect URLs
                    if url.startswith('/l/?uddg='):
                        url = url.split('uddg=')[1] if 'uddg=' in url else url
                    
                    if title and url and len(title) > 5:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source='duckduckgo_web'
                        ))
                        
                except Exception as e:
                    logger.debug(f"Error parsing result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo web scraping failed: {e}")
            return []
    
    def extract_content_from_url(self, url: str) -> str:
        """Extract text content from a webpage"""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ""
            
            # Skip problematic domains
            skip_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com']
            if any(domain in parsed_url.netloc.lower() for domain in skip_domains):
                return ""
            
            self._rate_limit()
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                element.decompose()
            
            # Try to find main content areas
            main_content = ""
            content_selectors = [
                'article', 'main', '[role="main"]',
                '.content', '.post-content', '.entry-content', 
                '.article-body', '.post-body', '.story-body',
                '#content', '#main-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem.get_text(separator=' ', strip=True)
                    break
            
            # Fallback to all paragraphs and headings
            if not main_content or len(main_content) < 100:
                elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                main_content = ' '.join([elem.get_text(strip=True) for elem in elements])
            
            # Clean up text
            lines = main_content.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            main_content = ' '.join(lines)
            
            # Limit content length (5000 chars should be enough for embeddings)
            if len(main_content) > 5000:
                # Try to cut at a sentence boundary
                sentences = main_content[:5000].split('.')
                if len(sentences) > 1:
                    main_content = '.'.join(sentences[:-1]) + '.'
                else:
                    main_content = main_content[:5000]
            
            return main_content
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return ""
    
    def search_and_extract(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search and extract content from top results"""
        # Get search results
        search_results = self.search_duckduckgo(query, num_results)
        
        # Extract content from each URL
        valid_results = []
        for result in search_results:
            if result.url:
                content = self.extract_content_from_url(result.url)
                
                # Use content if available, otherwise fall back to snippet
                if content and len(content) > 50:
                    result.content = content
                    valid_results.append(result)
                elif result.snippet and len(result.snippet) > 20:
                    result.content = result.snippet
                    valid_results.append(result)
        
        return valid_results 