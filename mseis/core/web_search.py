# core/web_search.py
"""
Google Search Integration for RAG fallback
Handles web search when no similar documents are found locally
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import quote_plus
import json
from bs4 import BeautifulSoup

from utils.logging_config import get_logger

logger = get_logger(__name__)

class WebSearchManager:
    """Manages web search fallback when local documents are insufficient"""
    
    def __init__(self):
        self.search_engines = {
            'duckduckgo': 'https://html.duckduckgo.com/html/',
            'bing': 'https://www.bing.com/search'
        }
        self.max_results = 5
        self.timeout = 10
        
    async def search_web(self, query: str, max_results: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Search the web for information
        Returns: (search_results, source_urls)
        """
        try:
            # Try multiple search engines for better results
            results = []
            source_urls = []
            
            # Use DuckDuckGo as primary (no API key required)
            duckduckgo_results = await self._search_duckduckgo(query, max_results)
            results.extend(duckduckgo_results)
            
            # Extract source URLs
            for result in results:
                if result.get('url'):
                    source_urls.append(result['url'])
            
            logger.info(f"Found {len(results)} web search results for query: '{query}'")
            return results[:max_results], source_urls[:max_results]
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return [], []
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return self._parse_duckduckgo_results(html_content, max_results)
                    else:
                        logger.warning(f"DuckDuckGo search failed with status: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return []
    
    def _parse_duckduckgo_results(self, html_content: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo search results"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Find result containers
            result_containers = soup.find_all('div', class_='result__body')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title
                    title_element = container.find('a', class_='result__a')
                    title = title_element.get_text(strip=True) if title_element else "No title"
                    url = title_element.get('href', '') if title_element else ""
                    
                    # Extract snippet
                    snippet_element = container.find('a', class_='result__snippet')
                    snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'DuckDuckGo'
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing individual result: {str(e)}")
                    continue
                    
            return results
            
        except Exception as e:
            logger.error(f"Error parsing DuckDuckGo results: {str(e)}")
            return []
    
    async def extract_content_from_urls(self, urls: List[str], max_content_length: int = 1000) -> List[Dict[str, str]]:
        """Extract content from web URLs"""
        content_results = []
        
        for url in urls[:3]:  # Limit to first 3 URLs to avoid overload
            try:
                content = await self._extract_single_url_content(url, max_content_length)
                if content:
                    content_results.append({
                        'url': url,
                        'content': content,
                        'length': len(content)
                    })
                    
            except Exception as e:
                logger.debug(f"Failed to extract content from {url}: {str(e)}")
                continue
                
        return content_results
    
    async def _extract_single_url_content(self, url: str, max_length: int) -> str:
        """Extract clean text content from a single URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse HTML and extract text
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style", "nav", "header", "footer"]):
                            script.decompose()
                        
                        # Get text content
                        text = soup.get_text(separator=' ', strip=True)
                        
                        # Clean up text
                        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
                        text = text[:max_length] + "..." if len(text) > max_length else text
                        
                        return text
                    else:
                        return ""
                        
        except Exception as e:
            logger.debug(f"Content extraction failed for {url}: {str(e)}")
            return ""
    
    def format_web_results_for_context(self, search_results: List[Dict[str, Any]], content_results: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Format web search results for inclusion in context window"""
        formatted_results = []
        
        # Create a mapping of URLs to content
        url_content_map = {item['url']: item['content'] for item in content_results}
        
        for result in search_results:
            url = result.get('url', '')
            formatted_result = {
                'title': result.get('title', 'Unknown'),
                'url': url,
                'snippet': result.get('snippet', ''),
                'source': result.get('source', 'Web'),
                'content': url_content_map.get(url, result.get('snippet', ''))
            }
            formatted_results.append(formatted_result)
            
        return formatted_results
    
    async def comprehensive_web_search(self, query: str, extract_content: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive web search with content extraction
        Returns complete search results with metadata
        """
        try:
            logger.info(f"🔍 Performing web search for: '{query}'")
            
            # Perform search
            search_results, source_urls = await self.search_web(query, self.max_results)
            
            if not search_results:
                return {
                    'query': query,
                    'results': [],
                    'sources': [],
                    'has_results': False,
                    'message': 'No web search results found'
                }
            
            # Extract content if requested
            content_results = []
            if extract_content and source_urls:
                content_results = await self.extract_content_from_urls(source_urls)
            
            # Format results for context
            formatted_results = self.format_web_results_for_context(search_results, content_results)
            
            return {
                'query': query,
                'results': formatted_results,
                'sources': source_urls,
                'has_results': True,
                'total_results': len(search_results),
                'content_extracted': len(content_results),
                'message': f'Found {len(search_results)} web results'
            }
            
        except Exception as e:
            logger.error(f"Comprehensive web search failed: {str(e)}")
            return {
                'query': query,
                'results': [],
                'sources': [],
                'has_results': False,
                'error': str(e),
                'message': 'Web search encountered an error'
            }