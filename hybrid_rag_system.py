import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
import time
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional
import feedparser
import arxiv
import asyncio
import aiohttp
from urllib.parse import quote_plus, urljoin, urlparse
import re
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import openai

# Import our new LLM integration
from llm_integration import ollama_llm, LLMResponse
from confidence_evaluator import ConfidenceEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
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

@dataclass
class QueryResponse:
    """Data class for query responses"""
    answer: str
    confidence: float
    sources: List[Dict]
    method_used: str  # "local" or "web" or "hybrid"
    processing_time: float
    debug_info: Dict = None

class WebSearchManager:
    """Manages web search operations and content extraction"""
    
    def __init__(self, cache_dir: str = "web_cache"):
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
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
            with open(cache_path, 'r') as f:
                cached_results = json.load(f)
                return [SearchResult(**result) for result in cached_results]
        
        self._rate_limit()
        
        try:
            # DuckDuckGo instant answer API
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
            
            try:
                if response.status_code in [200, 202] and response.text.strip():
                    try:
                        data = response.json()
                        logger.info(f"DuckDuckGo API success: {len(data.get('RelatedTopics', []))} topics found")
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"DuckDuckGo API JSON parsing failed, trying web scraping: {json_err}")
                        data = {}
                else:
                    logger.warning(f"DuckDuckGo API returned status {response.status_code} or empty response")
                    data = {}
            except Exception as api_err:
                logger.warning(f"DuckDuckGo API call failed, trying web scraping: {api_err}")
                data = {}
            
            results = []
            
            # Extract results from DuckDuckGo response (but filter for quality)
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:num_results]:
                    if isinstance(topic, dict) and 'Text' in topic and 'FirstURL' in topic:
                        url = topic.get('FirstURL', '')
                        # Only include external URLs, not DuckDuckGo internal links
                        if url and not url.startswith('https://duckduckgo.com/'):
                            results.append(SearchResult(
                                title=topic.get('Text', '')[:100],
                                url=url,
                                snippet=topic.get('Text', ''),
                                source='duckduckgo_api'
                            ))
            
            # Always try web scraping for better quality results
            web_results = self._scrape_duckduckgo_web(query, num_results)
            results.extend(web_results)
            logger.info(f"Got {len(web_results)} results from web scraping, {len(results)} total")
            
            # Cache results
            with open(cache_path, 'w') as f:
                json.dump([result.__dict__ for result in results], f)
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def _scrape_duckduckgo_web(self, query: str, num_results: int) -> List[SearchResult]:
        """Scrape DuckDuckGo web results as fallback"""
        try:
            # Use a more direct search URL approach
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}&t=D&ia=web"
            
            # Enhanced headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            self._rate_limit()
            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"DuckDuckGo web returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Updated selectors based on actual DuckDuckGo HTML structure
            result_titles = soup.find_all('h2', class_='result__title')
            
            logger.info(f"Found {len(result_titles)} result titles")
            
            for title_elem in result_titles[:num_results]:
                try:
                    # Find the link within the title
                    link_elem = title_elem.find('a', class_='result__a')
                    
                    if link_elem:
                        title = link_elem.get_text().strip()
                        url = link_elem.get('href', '')
                        
                        # Find snippet in nearby elements
                        parent_div = title_elem.find_parent('div')
                        snippet_elem = None
                        
                        if parent_div:
                            snippet_elem = (parent_div.find('a', class_='result__snippet') or
                                           parent_div.find('span', class_='result__snippet') or
                                           parent_div.find('div', class_='result__snippet') or
                                           parent_div.find_next_sibling(['div', 'p']))
                        
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        
                        # Clean up DuckDuckGo redirect URLs (updated for current format)
                        if url.startswith('//duckduckgo.com/l/?uddg=') or url.startswith('/l/?uddg='):
                            try:
                                import urllib.parse
                                if 'uddg=' in url:
                                    encoded_url = url.split('uddg=')[1].split('&')[0]
                                    url = urllib.parse.unquote(encoded_url)
                            except:
                                continue
                        
                        # Validate URL
                        if url and url.startswith('http') and title and len(title) > 5:
                            results.append(SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet,
                                source='duckduckgo_web'
                            ))
                            
                except Exception as e:
                    logger.debug(f"Error parsing individual result: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(results)} results from DuckDuckGo web scraping")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo web scraping failed: {e}")
            # If DuckDuckGo fails, try a basic search engine alternative
            return self._fallback_search(query, num_results)
    
    def extract_content_from_url(self, url: str) -> str:
        """Extract text content from a webpage"""
        try:
            # Check if URL is valid
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ""
            
            self._rate_limit()
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Extract main content
            main_content = ""
            
            # Try to find main content areas
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '.article-body', '.post-body'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem.get_text()
                    break
            
            # Fallback to all paragraphs
            if not main_content:
                paragraphs = soup.find_all('p')
                main_content = ' '.join([p.get_text() for p in paragraphs])
            
            # Clean up text
            main_content = ' '.join(main_content.split())
            
            # Limit content length
            return main_content[:5000] if len(main_content) > 5000 else main_content
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return ""
    
    def search_and_extract(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search and extract content from top results"""
        search_results = self.search_duckduckgo(query, num_results)
        
        # Extract content from each URL
        for result in search_results:
            if result.url:
                content = self.extract_content_from_url(result.url)
                result.content = content
                
                # If content extraction failed, use snippet
                if not content:
                    result.content = result.snippet
        
        # Filter out results with no content but be more lenient
        valid_results = []
        for result in search_results:
            if result.content and len(result.content.strip()) > 20:
                valid_results.append(result)
            elif result.snippet and len(result.snippet.strip()) > 10:
                # Use snippet as content if content extraction failed
                result.content = result.snippet
                valid_results.append(result)
        
        logger.info(f"Web search returned {len(valid_results)} valid results")
        return valid_results
    
    def _fallback_search(self, query: str, num_results: int) -> List[SearchResult]:
        """Basic fallback search if DuckDuckGo fails completely"""
        try:
            # Create some basic results from query terms for demonstration
            # In a real system, you might use another search engine API here
            results = []
            
            # For now, return an informative message
            logger.warning("All web search methods failed, returning empty results")
            return []
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []



class HybridRAGSystem:
    """Enhanced RAG system with hybrid local + web search capabilities"""
    
    def __init__(self):
        # Core RAG components
        self.model = None
        self.index = None
        self.documents = []
        self.embeddings = None
        
        # Hybrid components
        self.web_search_manager = WebSearchManager()
        self.confidence_evaluator = None  # Will be initialized after model is loaded
        
        # Configuration
        self.max_web_results = 10
        self.max_local_results = 5
    
    @st.cache_resource
    def load_embedding_model(_self):
        """Load the sentence transformer model"""
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    def initialize(self):
        """Initialize the hybrid RAG system"""
        self.model = self.load_embedding_model()
        # Initialize confidence evaluator with the model for semantic understanding
        self.confidence_evaluator = ConfidenceEvaluator(
            threshold_low=0.6,   # Below this: always use web search
            threshold_high=0.8,  # Above this: local search sufficient
            model=self.model     # Pass model for semantic domain detection
        )
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load existing index or prepare for new one"""
        try:
            # Try to load existing index
            if os.path.exists('rag_data/documents.pkl'):
                with open('rag_data/documents.pkl', 'rb') as f:
                    self.documents = pickle.load(f)
                
                with open('rag_data/embeddings.pkl', 'rb') as f:
                    self.embeddings = pickle.load(f)
                
                if os.path.exists('rag_data/faiss_index.bin'):
                    self.index = faiss.read_index('rag_data/faiss_index.bin')
                    st.success(f"✅ Loaded existing knowledge base with {len(self.documents)} documents")
                else:
                    # Rebuild index if documents exist but index doesn't
                    if self.embeddings is not None:
                        self.build_index(self.embeddings)
            else:
                st.info("📝 No existing knowledge base found. Build one using the sidebar.")
        except Exception as e:
            st.warning(f"⚠️ Could not load existing index: {e}")
            self.documents = []
            self.embeddings = None
            self.index = None
    
    def create_embeddings(self, documents: List[Dict]) -> np.ndarray:
        """Create embeddings for documents"""
        texts = [f"{doc['title']} {doc['content']}" for doc in documents]
        return self.model.encode(texts)
    
    def build_index(self, embeddings: np.ndarray):
        """Build FAISS index from embeddings"""
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
    
    def save_index(self, documents: List[Dict], embeddings: np.ndarray):
        """Save documents, embeddings, and index to disk"""
        os.makedirs('rag_data', exist_ok=True)
        
        with open('rag_data/documents.pkl', 'wb') as f:
            pickle.dump(documents, f)
        
        with open('rag_data/embeddings.pkl', 'wb') as f:
            pickle.dump(embeddings, f)
        
        if self.index:
            faiss.write_index(self.index, 'rag_data/faiss_index.bin')
    
    def scrape_nasa_news(self, max_articles=20) -> List[Dict]:
        """Scrape NASA news (simplified version)"""
        documents = []
        try:
            feed = feedparser.parse('https://www.nasa.gov/news/releases/latest/index.html')
            for entry in feed.entries[:max_articles]:
                documents.append({
                    'title': entry.title,
                    'content': entry.title + ". " + entry.get('summary', ''),
                    'url': entry.link,
                    'source': 'NASA News',
                    'date': entry.get('published', '')
                })
        except Exception as e:
            st.warning(f"Could not scrape NASA news: {e}")
        return documents
    
    def scrape_arxiv_papers(self, query="space exploration", max_papers=15) -> List[Dict]:
        """Scrape arXiv papers"""
        documents = []
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_papers,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for paper in search.results():
                documents.append({
                    'title': paper.title,
                    'content': f"{paper.title}. {paper.summary}",
                    'url': paper.entry_id,
                    'source': 'arXiv',
                    'authors': ', '.join([author.name for author in paper.authors]),
                    'date': paper.published.strftime('%Y-%m-%d')
                })
        except Exception as e:
            st.warning(f"Could not scrape arXiv: {e}")
        return documents
    
    def scrape_spacex_updates(self, max_articles=15) -> List[Dict]:
        """Scrape SpaceX news and updates"""
        documents = []
        try:
            # Try SpaceX news page
            response = requests.get('https://www.spacex.com/news/', timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles (structure may vary)
            articles = soup.find_all(['article', 'div'], class_=['news-item', 'post'])[:max_articles]
            
            for article in articles:
                try:
                    title_elem = article.find(['h3', 'h2', 'h1'])
                    content_elem = article.find('p')
                    
                    if title_elem and content_elem:
                        title = title_elem.get_text().strip()
                        content = content_elem.get_text().strip()
                        
                        if len(content) > 50:
                            documents.append({
                                'title': title,
                                'content': f"{title}. {content}",
                                'url': 'https://www.spacex.com/news/',
                                'source': 'SpaceX',
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                except Exception as e:
                    continue
        except Exception as e:
            st.warning(f"Could not scrape SpaceX: {e}")
        return documents
    
    def scrape_space_com_news(self, max_articles=20) -> List[Dict]:
        """Scrape Space.com news"""
        documents = []
        try:
            feed = feedparser.parse('https://www.space.com/feeds/all')
            
            for entry in feed.entries[:max_articles]:
                documents.append({
                    'title': entry.title,
                    'content': f"{entry.title}. {entry.get('summary', '')}",
                    'url': entry.link,
                    'source': 'Space.com',
                    'date': entry.get('published', '')
                })
        except Exception as e:
            st.warning(f"Could not scrape Space.com: {e}")
        return documents
    
    def scrape_esa_news(self, max_articles=15) -> List[Dict]:
        """Scrape European Space Agency news"""
        documents = []
        try:
            feed = feedparser.parse('https://www.esa.int/rssfeed/Our_Activities/Space_Science')
            
            for entry in feed.entries[:max_articles]:
                documents.append({
                    'title': entry.title,
                    'content': f"{entry.title}. {entry.get('summary', '')}",
                    'url': entry.link,
                    'source': 'ESA',
                    'date': entry.get('published', '')
                })
        except Exception as e:
            st.warning(f"Could not scrape ESA: {e}")
        return documents
    
    def scrape_spacenews(self, max_articles=15) -> List[Dict]:
        """Scrape SpaceNews industry articles"""
        documents = []
        try:
            feed = feedparser.parse('https://spacenews.com/feed/')
            
            for entry in feed.entries[:max_articles]:
                documents.append({
                    'title': entry.title,
                    'content': f"{entry.title}. {entry.get('summary', '')}",
                    'url': entry.link,
                    'source': 'SpaceNews',
                    'date': entry.get('published', '')
                })
        except Exception as e:
            st.warning(f"Could not scrape SpaceNews: {e}")
        return documents
    
    def scrape_nature_astronomy(self, max_articles=10) -> List[Dict]:
        """Scrape Nature Astronomy research papers"""
        documents = []
        try:
            feed = feedparser.parse('https://www.nature.com/natastron.rss')
            
            for entry in feed.entries[:max_articles]:
                documents.append({
                    'title': entry.title,
                    'content': f"{entry.title}. {entry.get('summary', '')}",
                    'url': entry.link,
                    'source': 'Nature Astronomy',
                    'date': entry.get('published', '')
                })
        except Exception as e:
            st.warning(f"Could not scrape Nature Astronomy: {e}")
        return documents
    
    def scrape_blue_origin_news(self, max_articles=10) -> List[Dict]:
        """Scrape Blue Origin news (NEW SOURCE)"""
        documents = []
        try:
            # Blue Origin news page
            response = requests.get('https://www.blueorigin.com/news', timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all(['article', 'div'], class_=['news-item', 'post'])[:max_articles]
            
            for article in articles:
                try:
                    title_elem = article.find(['h3', 'h2', 'h1'])
                    content_elem = article.find('p')
                    
                    if title_elem and content_elem:
                        title = title_elem.get_text().strip()
                        content = content_elem.get_text().strip()
                        
                        if len(content) > 50:
                            documents.append({
                                'title': title,
                                'content': f"{title}. {content}",
                                'url': 'https://www.blueorigin.com/news',
                                'source': 'Blue Origin',
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                except Exception as e:
                    continue
        except Exception as e:
            st.warning(f"Could not scrape Blue Origin: {e}")
        return documents
    
    def scrape_planetary_society(self, max_articles=15) -> List[Dict]:
        """Scrape The Planetary Society blog (NEW SOURCE)"""
        documents = []
        try:
            feed = feedparser.parse('https://www.planetary.org/rss/blog.xml')
            
            for entry in feed.entries[:max_articles]:
                documents.append({
                    'title': entry.title,
                    'content': f"{entry.title}. {entry.get('summary', '')}",
                    'url': entry.link,
                    'source': 'Planetary Society',
                    'date': entry.get('published', '')
                })
        except Exception as e:
            st.warning(f"Could not scrape Planetary Society: {e}")
        return documents

    def load_custom_documents(self, custom_docs_dir: str = "custom_knowledge") -> List[Dict]:
        """Load custom documents from a directory (NEW FEATURE)"""
        documents = []
        
        if not os.path.exists(custom_docs_dir):
            os.makedirs(custom_docs_dir)
            with open(os.path.join(custom_docs_dir, "README.txt"), "w") as f:
                f.write("""Add your custom knowledge files here!

Supported formats:
- .txt files (plain text)
- .md files (markdown)
- .json files (with 'title' and 'content' fields)

Example JSON format:
{
    "title": "Your Document Title",
    "content": "Your document content here...",
    "source": "Your Source Name",
    "url": "optional_url"
}
""")
            st.info(f"📁 Created custom knowledge directory: {custom_docs_dir}")
            return documents
        
        try:
            for filename in os.listdir(custom_docs_dir):
                filepath = os.path.join(custom_docs_dir, filename)
                
                if filename.endswith('.txt'):
                    # Plain text files
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if len(content) > 50:
                            documents.append({
                                'title': filename.replace('.txt', ''),
                                'content': content,
                                'source': 'Custom Documents',
                                'url': filepath,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                
                elif filename.endswith('.md'):
                    # Markdown files
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if len(content) > 50:
                            documents.append({
                                'title': filename.replace('.md', ''),
                                'content': content,
                                'source': 'Custom Markdown',
                                'url': filepath,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                
                elif filename.endswith('.json'):
                    # JSON files with structured data
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            if isinstance(data, list):
                                # Multiple documents in one file
                                for item in data:
                                    if 'title' in item and 'content' in item:
                                        documents.append({
                                            'title': item['title'],
                                            'content': item['content'],
                                            'source': item.get('source', 'Custom JSON'),
                                            'url': item.get('url', filepath),
                                            'date': item.get('date', datetime.now().strftime('%Y-%m-%d'))
                                        })
                            else:
                                # Single document
                                if 'title' in data and 'content' in data:
                                    documents.append({
                                        'title': data['title'],
                                        'content': data['content'],
                                        'source': data.get('source', 'Custom JSON'),
                                        'url': data.get('url', filepath),
                                        'date': data.get('date', datetime.now().strftime('%Y-%m-%d'))
                                    })
                    except json.JSONDecodeError:
                        st.warning(f"Invalid JSON format in {filename}")
            
            st.write(f"✅ Loaded {len(documents)} custom documents")
        
        except Exception as e:
            st.warning(f"Error loading custom documents: {e}")
        
        return documents

    def build_knowledge_base(self):
        """Build knowledge base from various sources"""
        all_documents = []
        
        # 📁 CUSTOM DOCUMENTS (NEW!)
        with st.spinner("Loading custom documents..."):
            custom_docs = self.load_custom_documents()
            all_documents.extend(custom_docs)
            st.write(f"✅ Loaded {len(custom_docs)} custom documents")
        
        # 🛰️ SPACE AGENCIES
        with st.spinner("Scraping NASA news..."):
            nasa_docs = self.scrape_nasa_news(25)
            all_documents.extend(nasa_docs)
            st.write(f"✅ Scraped {len(nasa_docs)} NASA articles")
        
        with st.spinner("Scraping ESA news..."):
            esa_docs = self.scrape_esa_news(15)
            all_documents.extend(esa_docs)
            st.write(f"✅ Scraped {len(esa_docs)} ESA articles")
        
        # 🚀 PRIVATE SPACE COMPANIES
        with st.spinner("Scraping SpaceX updates..."):
            spacex_docs = self.scrape_spacex_updates(15)
            all_documents.extend(spacex_docs)
            st.write(f"✅ Scraped {len(spacex_docs)} SpaceX updates")
        
        with st.spinner("Scraping Blue Origin news..."):
            blue_origin_docs = self.scrape_blue_origin_news(10)
            all_documents.extend(blue_origin_docs)
            st.write(f"✅ Scraped {len(blue_origin_docs)} Blue Origin articles")
        
        # 📰 NEWS & MEDIA
        with st.spinner("Scraping Space.com news..."):
            space_com_docs = self.scrape_space_com_news(20)
            all_documents.extend(space_com_docs)
            st.write(f"✅ Scraped {len(space_com_docs)} Space.com articles")
        
        with st.spinner("Scraping SpaceNews..."):
            spacenews_docs = self.scrape_spacenews(15)
            all_documents.extend(spacenews_docs)
            st.write(f"✅ Scraped {len(spacenews_docs)} SpaceNews articles")
        
        with st.spinner("Scraping Planetary Society..."):
            planetary_docs = self.scrape_planetary_society(15)
            all_documents.extend(planetary_docs)
            st.write(f"✅ Scraped {len(planetary_docs)} Planetary Society articles")
        
        # 📑 RESEARCH PAPERS
        topics = ["space exploration", "exoplanet", "mars exploration", "space telescope", "astrophysics", "lunar exploration", "asteroid mining"]
        for topic in topics:
            with st.spinner(f"Scraping arXiv papers for '{topic}'..."):
                arxiv_docs = self.scrape_arxiv_papers(topic, 8)
                all_documents.extend(arxiv_docs)
                st.write(f"✅ Scraped {len(arxiv_docs)} papers for '{topic}'")
        
        with st.spinner("Scraping Nature Astronomy..."):
            nature_docs = self.scrape_nature_astronomy(10)
            all_documents.extend(nature_docs)
            st.write(f"✅ Scraped {len(nature_docs)} Nature Astronomy papers")
        
        if not all_documents:
            st.error("No documents were scraped. Please check your internet connection.")
            return
        
        # Create embeddings
        with st.spinner("Creating embeddings..."):
            embeddings = self.create_embeddings(all_documents)
            st.write(f"✅ Created embeddings for {len(all_documents)} documents")
        
        # Build FAISS index
        with st.spinner("Building search index..."):
            self.build_index(embeddings)
            st.write("✅ Built FAISS search index")
        
        # Save everything
        with st.spinner("Saving knowledge base..."):
            self.documents = all_documents
            self.embeddings = embeddings
            self.save_index(all_documents, embeddings)
            st.write("✅ Saved knowledge base to disk")
        
        st.success(f"🎉 Knowledge base built successfully with {len(all_documents)} documents!")
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search using the query with improved relevance filtering"""
        if self.index is None or not self.documents:
            return []
        
        # Create embedding for the query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search the index
        similarities, indices = self.index.search(query_embedding.astype('float32'), top_k * 2)  # Get more results to filter
        
        # Get the most relevant documents with strict filtering
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                # Clip similarity score to [0, 1] range due to floating-point precision
                similarity_score = max(0.0, min(1.0, float(similarities[0][i])))
                
                # Apply stricter relevance filtering
                if similarity_score > 0.5:  # Only consider results with high semantic similarity
                    # Additional keyword-based relevance check
                    content_relevance = self._check_content_relevance(query, doc)
                    
                    # Combine semantic and content relevance (ensure final score is 0-1)
                    final_score = min(1.0, similarity_score * 0.7 + content_relevance * 0.3)
                    
                    if final_score > 0.4:  # Only include truly relevant results
                        doc['relevance_score'] = final_score
                        doc['semantic_score'] = similarity_score
                        doc['content_relevance'] = content_relevance
                        results.append(doc)
        
        # Sort by final relevance score and return top_k
        results = sorted(results, key=lambda x: x['relevance_score'], reverse=True)[:top_k]
        
        return results
    
    def _check_content_relevance(self, query: str, document: Dict) -> float:
        """Check if document content is actually relevant to the query using keyword matching"""
        query_lower = query.lower()
        content = (document.get('content', '') + ' ' + document.get('title', '')).lower()
        
        # Extract key terms from query
        query_words = set(query_lower.replace('?', '').replace(',', '').split())
        
        # Common stop words to ignore
        stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'does', 'do', 'have', 'has', 'many', 'much', 'tell', 'me', 'about'}
        important_words = query_words - stop_words
        
        # ULTRA-AGGRESSIVE exoplanet filtering - must be first check
        exoplanet_indicators = [
            'exoplanet', 'exoplanets', 'extrasolar', 'hot jupiter', 'hot jupiters', 
            'super-earth', 'super earth', 'transit', 'transiting', 'orbital period', 
            'host star', 'host stars', 'stellar host', 'planet host', 'kelt-', 'wasp-', 
            'tres-', 'hd ', 'gj ', 'kepler-', 'tess-', 'k2-', 'hat-', 'qatar-', 
            'corot-', 'xo-', 'stellar system', 'planetary system', 'exo-', 'extrasolar planet',
            'radial velocity', 'doppler', 'light curve', 'photometry', 'spectroscopy',
            'stellar companion', 'binary star', 'multiple star system', 'stellar multiplicity'
        ]
        
        # If content is about exoplanets, immediately reject for moon/planet questions
        if any(indicator in content for indicator in exoplanet_indicators):
            # Only allow if query is explicitly about exoplanets
            if not any(exo_term in query_lower for exo_term in ['exoplanet', 'extrasolar', 'outside solar system']):
                return 0.01  # Extremely low score for exoplanet content when not asking about exoplanets
        
        # Check for direct keyword matches
        matches = 0
        for word in important_words:
            if word in content:
                matches += 1
        
        # Calculate relevance score based on keyword matches
        if not important_words:
            return 0.1
        
        keyword_relevance = matches / len(important_words)
        
        # Bonus for exact phrase matches
        if len(query_lower) > 3 and query_lower in content:
            keyword_relevance += 0.3
        
        # ULTRA-AGGRESSIVE filtering for moon questions
        if 'moon' in query_lower or 'moons' in query_lower:
            # For moon questions, content MUST explicitly mention moons/satellites AND the specific planet
            moon_terms = ['moon', 'moons', 'satellite', 'satellites', 'lunar']
            specific_moon_names = ['io', 'europa', 'ganymede', 'callisto', 'phobos', 'deimos', 'titan', 'enceladus', 'triton', 'miranda', 'ariel', 'umbriel', 'titania', 'oberon']
            
            has_moon_reference = any(term in content for term in moon_terms + specific_moon_names)
            
            if not has_moon_reference:
                return 0.01  # Extremely low score if no moon references
            
            # Additional check: if asking about specific planet's moons, both planet AND moon terms must be present
            if 'jupiter' in query_lower:
                jupiter_terms = ['jupiter', 'jovian']
                has_jupiter = any(term in content for term in jupiter_terms)
                has_moon_ref = any(term in content for term in moon_terms + ['io', 'europa', 'ganymede', 'callisto'])
                
                if not (has_jupiter and has_moon_ref):
                    return 0.01
        
        # AGGRESSIVE filtering for specific question types
        # If asking about specific celestial objects, content MUST mention them
        celestial_objects = {
            'jupiter': ['jupiter'],
            'mars': ['mars'],
            'saturn': ['saturn'], 
            'earth': ['earth'],
            'venus': ['venus'],
            'mercury': ['mercury'],
            'uranus': ['uranus'],
            'neptune': ['neptune'],
            'sun': ['sun', 'solar'],
            'moon': ['moon', 'satellite', 'lunar'],
            'telescope': ['telescope', 'observatory', 'hubble', 'webb', 'spitzer'],
            'asteroid': ['asteroid'],
            'comet': ['comet'],
            'galaxy': ['galaxy', 'galaxies'],
            'star': ['star', 'stellar']
        }
        
        # Check if query is about a specific celestial object
        query_object = None
        for obj, synonyms in celestial_objects.items():
            if obj in query_lower:
                query_object = obj
                required_terms = synonyms
                break
        
        if query_object:
            # If asking about a specific object, content MUST contain related terms
            has_required_term = any(term in content for term in required_terms)
            if not has_required_term:
                return 0.02  # Very low relevance if asking about Jupiter but content doesn't mention Jupiter
        
        # If asking about quantities ("how many"), content should mention numbers or quantities
        if any(word in query_lower for word in ['how many', 'number of', 'count']):
            number_indicators = ['number', 'many', 'several', 'multiple', 'total', 'count', 'few', 'some'] + [str(i) for i in range(0, 200)]
            if not any(indicator in content for indicator in number_indicators):
                keyword_relevance *= 0.1
        
        return min(keyword_relevance, 1.0)
    
    def query(self, user_query: str, expertise_level: str = "general") -> QueryResponse:
        """Main query method implementing hybrid search logic with better relevance detection"""
        start_time = time.time()
        debug_info = {}
        
        # Step 1: Search local knowledge base with improved filtering
        local_results = self.semantic_search(user_query, top_k=self.max_local_results)
        debug_info['local_results_count'] = len(local_results)
        debug_info['local_results_scores'] = [r.get('relevance_score', 0) for r in local_results]
        
        # Step 2: Evaluate if local results are actually relevant
        best_local_score = max([r.get('relevance_score', 0) for r in local_results]) if local_results else 0
        min_acceptable_score = 0.5  # Minimum score to consider results relevant
        
        has_relevant_local = best_local_score >= min_acceptable_score
        debug_info['best_local_score'] = best_local_score
        debug_info['has_relevant_local'] = has_relevant_local
        
        # Step 3: Decide on web search - trigger if no relevant local results
        if not has_relevant_local:
            should_use_web = True
            reason = f"No relevant local results (best score: {best_local_score:.2f} < {min_acceptable_score})"
        else:
            should_use_web, reason = self.confidence_evaluator.should_use_web_search(
                user_query, local_results
            )
        
        debug_info['decision_reason'] = reason
        debug_info['should_use_web'] = should_use_web
        
        web_results = []
        method_used = "local"
        
        # Step 4: Perform web search if needed
        if should_use_web:
            try:
                web_search_results = self.web_search_manager.search_and_extract(
                    user_query, num_results=self.max_web_results
                )
                
                if web_search_results:
                    web_documents = self._convert_web_results_to_documents(web_search_results)
                    web_results = self._rank_web_results(user_query, web_documents)
                    method_used = "hybrid" if has_relevant_local else "web"
                
                debug_info['web_results_count'] = len(web_results)
                
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                debug_info['web_search_error'] = str(e)
        
        # Step 5: Filter and combine results
        if has_relevant_local:
            # Use local results if they're relevant
            filtered_local = [r for r in local_results if r.get('relevance_score', 0) >= min_acceptable_score]
            all_results = self._combine_and_rank_results(filtered_local, web_results)
        else:
            # Only use web results if local results are not relevant
            all_results = web_results
            
        debug_info['total_results'] = len(all_results)
        debug_info['final_results_scores'] = [r.get('relevance_score', 0) for r in all_results[:3]]
        
        # Step 6: Generate response or return "no similar results"
        if not all_results or (all_results and max([r.get('relevance_score', 0) for r in all_results]) < 0.3):
            answer = self._generate_no_results_response(user_query)
            final_confidence = 0.0
            method_used = "no_results"
        else:
            answer = self._generate_hybrid_response(user_query, all_results, expertise_level)
            final_confidence = self._calculate_final_confidence(all_results, has_relevant_local)
        
        processing_time = time.time() - start_time
        debug_info['processing_time'] = processing_time
        debug_info['final_confidence'] = final_confidence
        
        return QueryResponse(
            answer=answer,
            confidence=final_confidence,
            sources=all_results[:5],  # Top 5 sources
            method_used=method_used,
            processing_time=processing_time,
            debug_info=debug_info
        )
    
    def _calculate_final_confidence(self, results: List[Dict], has_relevant_local: bool) -> float:
        """Calculate final confidence based on result quality"""
        if not results:
            return 0.0
            
        best_score = max([r.get('relevance_score', 0) for r in results])
        avg_score = sum([r.get('relevance_score', 0) for r in results[:3]]) / min(len(results), 3)
        
        # Base confidence on scores
        confidence = (best_score * 0.6 + avg_score * 0.4)
        
        # Boost if we have good local results
        if has_relevant_local and best_score > 0.7:
            confidence *= 1.1
            
        return min(confidence, 1.0)
    
    def _convert_web_results_to_documents(self, web_results: List[SearchResult]) -> List[Dict]:
        """Convert web search results to document format"""
        documents = []
        for result in web_results:
            doc = {
                'title': result.title,
                'content': result.content,
                'url': result.url,
                'source': f"Web ({result.source})",
                'date': datetime.now().strftime('%Y-%m-%d'),
                'snippet': result.snippet,
                'web_result': True
            }
            documents.append(doc)
        return documents
    
    def _rank_web_results(self, query: str, web_documents: List[Dict]) -> List[Dict]:
        """Rank web results using semantic similarity"""
        if not web_documents:
            return []
        
        try:
            contents = [doc['content'] for doc in web_documents if doc['content']]
            if not contents:
                return web_documents
            
            web_embeddings = self.model.encode(contents)
            query_embedding = self.model.encode([query])
            
            # Normalize for cosine similarity
            faiss.normalize_L2(web_embeddings)
            faiss.normalize_L2(query_embedding)
            
            similarities = np.dot(query_embedding, web_embeddings.T).flatten()
            
            content_index = 0
            for doc in web_documents:
                if doc['content']:
                    doc['relevance_score'] = float(similarities[content_index])
                    content_index += 1
                else:
                    doc['relevance_score'] = 0.1
            
            return sorted(web_documents, key=lambda x: x['relevance_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error ranking web results: {e}")
            for i, doc in enumerate(web_documents):
                doc['relevance_score'] = max(0.1, 1.0 - (i * 0.1))
            return web_documents
    
    def _combine_and_rank_results(self, local_results: List[Dict], 
                                web_results: List[Dict]) -> List[Dict]:
        """Combine and rank results from both sources with stricter filtering"""
        all_results = []
        
        # Only use local results with high relevance
        for result in local_results:
            if result.get('relevance_score', 0) >= 0.5:  # Stricter threshold
                result_copy = result.copy()
                result_copy['search_method'] = 'local'
                result_copy['local_result'] = True
                all_results.append(result_copy)
        
        # Add web results
        for result in web_results:
            result_copy = result.copy()
            result_copy['search_method'] = 'web'
            all_results.append(result_copy)
        
        return sorted(all_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def _generate_hybrid_response(self, query: str, results: List[Dict], expertise_level: str = "general") -> str:
        """Generate response using LLM with retrieved context"""
        if not results:
            return self._generate_no_results_response(query)
        
        # First, check if this query is within our domain
        domain, domain_confidence = ollama_llm.detect_query_domain(query)
        
        # If it's clearly outside space exploration domain, provide out-of-scope response
        if domain not in ["space_exploration", "general_science"] and domain_confidence > 0.7:
            llm_response = ollama_llm.generate_out_of_scope_response(query, domain)
            return llm_response.content
        
        # Use LLM to generate a proper answer
        llm_response = ollama_llm.generate_answer(query, results, expertise_level)
        
        # If LLM is available, use its response
        if llm_response.confidence > 0.3:
            # Add source information
            local_results = [r for r in results if r.get('search_method') == 'local']
            web_results = [r for r in results if r.get('search_method') == 'web']
            
            response = llm_response.content
            
            # Add source attribution
            response += f"\n\n---\n**Sources:**\n"
            
            for i, result in enumerate(results[:5], 1):
                source_type = "📚" if result.get('local_result') else "🌐"
                score = result.get('relevance_score', 0)
                title = result.get('title', '')
                source = result.get('source', 'Unknown')
                
                response += f"{i}. {source_type} {source}"
                if title and title != source:
                    response += f" - {title}"
                response += f" (Relevance: {score:.2f})\n"
            
            # Add methodology note
            if local_results and web_results:
                response += f"\n*Combined {len(local_results)} specialized sources with {len(web_results)} web sources*"
            elif local_results:
                response += f"\n*Based on {len(local_results)} specialized space knowledge sources*"
            else:
                response += f"\n*Based on {len(web_results)} current web sources*"
            
            return response
        
        # Fallback to original method if LLM fails
        return self._generate_fallback_response(query, results)
    
    def _generate_fallback_response(self, query: str, results: List[Dict]) -> str:
        """Fallback response generation when LLM is unavailable"""
        local_results = [r for r in results if r.get('search_method') == 'local']
        web_results = [r for r in results if r.get('search_method') == 'web']
        
        response = f"**Answer to: {query}**\n\n"
        
        # Determine primary source based on quality
        top_result = results[0] if results else None
        primary_source = top_result.get('search_method', 'unknown') if top_result else 'unknown'
        
        if web_results and not local_results:
            response += f"*Based on {len(web_results)} current web sources*\n\n"
        elif local_results and not web_results:
            response += f"*Based on {len(local_results)} specialized space knowledge sources*\n\n"
        elif primary_source == 'web':
            response += f"*Primarily from {len(web_results)} web sources, enhanced with {len(local_results)} specialized sources*\n\n"
        else:
            response += f"*Combining {len(local_results)} specialized sources with {len(web_results)} web sources*\n\n"
        
        # Include top 3 sources with better formatting
        for i, result in enumerate(results[:3], 1):
            source_type = "📚" if result.get('local_result') else "🌐"
            score = result.get('relevance_score', 0)
            response += f"**Source {i}** {source_type} {result.get('source', 'Unknown')} (Relevance: {score:.2f})\n"
            
            # Show title if available
            title = result.get('title', '')
            if title and title != result.get('source', ''):
                response += f"*{title}*\n"
            
            content = result.get('content', '')[:400]  # Slightly longer excerpts
            if len(result.get('content', '')) > 400:
                content += "..."
            
            response += f"{content}\n\n"
        
        response += "---\n"
        high_conf_count = len([r for r in results if r.get('relevance_score', 0) > 0.5])
        response += f"**Search Method:** {primary_source.title()} search with {high_conf_count} high-confidence matches."
        
        return response
    
    def _generate_no_results_response(self, query: str) -> str:
        """Generate response when no relevant results found"""
        return f"""**No similar information found for: "{query}"**

🔍 **What I searched:**
- Local space knowledge base ({len(self.documents)} documents)
- Web sources (if applicable)

❌ **Result:** No sufficiently relevant matches found

💡 **Suggestions:**
- Try rephrasing your question with different keywords
- For space topics: Ask about planets, missions, telescopes, or space agencies
- For general topics: The system will search the web automatically

🌐 **Note:** If this is a non-space topic, web search should be triggered automatically. If you're not getting web results, there may be a connectivity issue."""

# Streamlit UI functions
@st.cache_resource
def get_hybrid_rag_system():
    """Initialize and cache the hybrid RAG system"""
    system = HybridRAGSystem()
    system.initialize()
    return system

def display_response(response: QueryResponse):
    """Display query response in Streamlit"""
    st.markdown("### 🤖 Response")
    st.markdown(response.answer)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence", f"{response.confidence:.1%}")
    with col2:
        st.metric("Method", response.method_used.title())
    with col3:
        st.metric("Time", f"{response.processing_time:.1f}s")
    
    # Sources
    if response.sources:
        st.markdown("### 📚 Sources")
        for i, source in enumerate(response.sources, 1):
            emoji = "📚" if source.get('local_result') else "🌐"
            with st.expander(f"{emoji} Source {i}: {source.get('title', 'Unknown')[:50]}... "
                           f"(Score: {source.get('relevance_score', 0):.2f})"):
                st.write(f"**Source:** {source.get('source', 'Unknown')}")
                if source.get('url'):
                    st.write(f"**URL:** {source['url']}")
                if source.get('date'):
                    st.write(f"**Date:** {source['date']}")
                st.write(f"**Content:** {source.get('content', '')[:300]}...")

def main():
    """Main Streamlit application"""
    st.set_page_config(page_title="Hybrid RAG System", page_icon="🚀", layout="wide")
    
    st.title("🚀 Hybrid RAG System")
    st.markdown("*Space expertise + Web knowledge for comprehensive answers*")
    
    # Initialize system
    hybrid_system = get_hybrid_rag_system()
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ System Management")
        
        if st.button("🔨 Build Knowledge Base"):
            hybrid_system.build_knowledge_base()
        
        st.header("📊 Status")
        if hybrid_system.documents:
            st.success(f"📚 {len(hybrid_system.documents)} documents")
            st.success("🔍 Search ready")
        else:
            st.warning("📚 No documents loaded")
        
        st.header("⚙️ Thresholds")
        low_threshold = st.slider("Low Confidence", 0.0, 1.0, 0.6, 0.1)
        high_threshold = st.slider("High Confidence", 0.0, 1.0, 0.8, 0.1)
        
        hybrid_system.confidence_evaluator.threshold_low = low_threshold
        hybrid_system.confidence_evaluator.threshold_high = high_threshold
        
        st.info(f"Below {low_threshold}: Use web search\n\n"
               f"Above {high_threshold}: Local sufficient\n\n"
               f"Between: Hybrid approach")
    
    # Main interface
    st.header("💬 Ask Anything")
    
    # Examples
    with st.expander("💡 Example Queries"):
        st.write("**Space topics (local knowledge):**")
        st.write("• What is the James Webb Space Telescope?")
        st.write("• How do rockets work?")
        st.write("")
        st.write("**General topics (web search):**")
        st.write("• What is machine learning?")
        st.write("• How to bake bread?")
    
    # Query input
    query = st.text_input("Your question:", placeholder="Ask about space exploration or anything else...")
    
    if query:
        if hybrid_system.model is None:
            st.error("⚠️ System not ready. Please wait for initialization.")
        else:
            with st.spinner("🔍 Searching for information..."):
                response = hybrid_system.query(query)
            display_response(response)

if __name__ == "__main__":
    main() 