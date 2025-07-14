import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
import time
from typing import List, Dict, Any
import feedparser
import arxiv
import asyncio
import aiohttp

# Page configuration
st.set_page_config(
    page_title="MSEIS - True RAG System",
    page_icon="🚀",
    layout="wide"
)

class TrueRAGSystem:
    def __init__(self):
        self.model = None
        self.index = None
        self.documents = []
        self.embeddings = None
        
    @st.cache_resource
    def load_embedding_model(_self):
        """Load the sentence transformer model"""
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    def initialize(self):
        """Initialize the RAG system"""
        self.model = self.load_embedding_model()
        self.load_or_create_index()
    
    def scrape_nasa_news(self, max_articles=50) -> List[Dict]:
        """Scrape NASA news and articles"""
        documents = []
        
        try:
            # NASA RSS feed
            feed = feedparser.parse('https://www.nasa.gov/news/releases/latest/index.html')
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Get the full article content
                    response = requests.get(entry.link, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract text content
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs])
                    
                    if len(content) > 100:  # Only include substantial content
                        documents.append({
                            'title': entry.title,
                            'content': content,
                            'url': entry.link,
                            'source': 'NASA News',
                            'date': entry.get('published', '')
                        })
                except Exception as e:
                    st.write(f"Error scraping {entry.link}: {str(e)}")
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing NASA feed: {str(e)}")
            
        return documents
    
    def scrape_arxiv_papers(self, query="space exploration", max_papers=20) -> List[Dict]:
        """Scrape arXiv papers related to space"""
        documents = []
        
        try:
            # Search arXiv for space-related papers
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
            st.error(f"Error accessing arXiv: {str(e)}")
            
        return documents
    
    def scrape_nasa_technical_reports(self) -> List[Dict]:
        """Scrape NASA technical reports"""
        documents = []
        
        try:
            # NASA Technical Reports Server (sample URLs)
            base_urls = [
                'https://ntrs.nasa.gov/search.jsp?R=20220000001',
                'https://ntrs.nasa.gov/search.jsp?R=20220000002',
                # Add more NASA technical report URLs
            ]
            
            for url in base_urls:
                try:
                    response = requests.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract content (this would need to be customized for NASA's format)
                    content_divs = soup.find_all('div', class_='abstract')
                    for div in content_divs:
                        content = div.get_text().strip()
                        if len(content) > 100:
                            documents.append({
                                'title': 'NASA Technical Report',
                                'content': content,
                                'url': url,
                                'source': 'NASA Technical Reports',
                                'date': ''
                            })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing NASA technical reports: {str(e)}")
            
        return documents
    
    def scrape_esa_news(self, max_articles=30) -> List[Dict]:
        """Scrape European Space Agency news"""
        documents = []
        
        try:
            # ESA RSS feed
            feed = feedparser.parse('https://www.esa.int/rssfeed/Our_Activities/Space_Science')
            
            for entry in feed.entries[:max_articles]:
                try:
                    response = requests.get(entry.link, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract content
                    content_divs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in content_divs])
                    
                    if len(content) > 100:
                        documents.append({
                            'title': entry.title,
                            'content': content,
                            'url': entry.link,
                            'source': 'ESA',
                            'date': entry.get('published', '')
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing ESA feed: {str(e)}")
            
        return documents
    
    def scrape_spacex_updates(self) -> List[Dict]:
        """Scrape SpaceX news and updates"""
        documents = []
        
        try:
            # SpaceX news page
            response = requests.get('https://www.spacex.com/news/', timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            articles = soup.find_all('div', class_='news-item')[:20]
            
            for article in articles:
                try:
                    title_elem = article.find('h3') or article.find('h2')
                    content_elem = article.find('p')
                    
                    if title_elem and content_elem:
                        title = title_elem.get_text().strip()
                        content = content_elem.get_text().strip()
                        
                        if len(content) > 50:
                            documents.append({
                                'title': title,
                                'content': content,
                                'url': 'https://www.spacex.com/news/',
                                'source': 'SpaceX',
                                'date': ''
                            })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing SpaceX news: {str(e)}")
            
        return documents
    
    def scrape_space_com_news(self, max_articles=25) -> List[Dict]:
        """Scrape Space.com news"""
        documents = []
        
        try:
            # Space.com RSS feed
            feed = feedparser.parse('https://www.space.com/feeds/all')
            
            for entry in feed.entries[:max_articles]:
                try:
                    response = requests.get(entry.link, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract article content
                    content_divs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in content_divs])
                    
                    if len(content) > 100:
                        documents.append({
                            'title': entry.title,
                            'content': content,
                            'url': entry.link,
                            'source': 'Space.com',
                            'date': entry.get('published', '')
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing Space.com: {str(e)}")
            
        return documents
    
    def scrape_jaxa_news(self) -> List[Dict]:
        """Scrape JAXA (Japan Aerospace Exploration Agency) news"""
        documents = []
        
        try:
            # JAXA English news
            response = requests.get('https://www.jaxa.jp/news/index_e.html', timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news items
            news_items = soup.find_all('div', class_='news-item')[:15]
            
            for item in news_items:
                try:
                    title_elem = item.find('h3') or item.find('a')
                    desc_elem = item.find('p')
                    
                    if title_elem and desc_elem:
                        title = title_elem.get_text().strip()
                        content = desc_elem.get_text().strip()
                        
                        if len(content) > 50:
                            documents.append({
                                'title': title,
                                'content': content,
                                'url': 'https://www.jaxa.jp/',
                                'source': 'JAXA',
                                'date': ''
                            })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing JAXA news: {str(e)}")
            
        return documents
    
    def scrape_csa_news(self) -> List[Dict]:
        """Scrape Canadian Space Agency news"""
        documents = []
        
        try:
            # CSA news feed
            feed = feedparser.parse('https://www.asc-csa.gc.ca/eng/rss/news.xml')
            
            for entry in feed.entries[:20]:
                try:
                    response = requests.get(entry.link, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    content_divs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in content_divs])
                    
                    if len(content) > 100:
                        documents.append({
                            'title': entry.title,
                            'content': content,
                            'url': entry.link,
                            'source': 'Canadian Space Agency',
                            'date': entry.get('published', '')
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing CSA news: {str(e)}")
            
        return documents
    
    def scrape_spacenews(self, max_articles=20) -> List[Dict]:
        """Scrape SpaceNews articles"""
        documents = []
        
        try:
            # SpaceNews RSS feed
            feed = feedparser.parse('https://spacenews.com/feed/')
            
            for entry in feed.entries[:max_articles]:
                try:
                    response = requests.get(entry.link, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    content_divs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in content_divs])
                    
                    if len(content) > 100:
                        documents.append({
                            'title': entry.title,
                            'content': content,
                            'url': entry.link,
                            'source': 'SpaceNews',
                            'date': entry.get('published', '')
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing SpaceNews: {str(e)}")
            
        return documents
    
    def scrape_nature_astronomy(self) -> List[Dict]:
        """Scrape Nature Astronomy papers"""
        documents = []
        
        try:
            # Nature Astronomy RSS feed
            feed = feedparser.parse('https://www.nature.com/natastron.rss')
            
            for entry in feed.entries[:10]:
                try:
                    documents.append({
                        'title': entry.title,
                        'content': entry.summary if hasattr(entry, 'summary') else entry.title,
                        'url': entry.link,
                        'source': 'Nature Astronomy',
                        'date': entry.get('published', '')
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            st.error(f"Error accessing Nature Astronomy: {str(e)}")
            
        return documents
    
    def scrape_multiple_arxiv_categories(self) -> List[Dict]:
        """Scrape multiple arXiv categories for comprehensive coverage"""
        documents = []
        
        categories = [
            ("astro-ph", "Astrophysics"),
            ("physics.space-ph", "Space Physics"),
            ("gr-qc", "General Relativity and Quantum Cosmology"),
            ("physics.ao-ph", "Atmospheric and Oceanic Physics"),
            ("cond-mat", "Condensed Matter"),
        ]
        
        queries = [
            "exoplanet detection",
            "mars exploration", 
            "space telescope",
            "black hole",
            "neutron star",
            "galaxy formation",
            "dark matter",
            "space mission",
            "satellite",
            "rocket propulsion",
            "space debris",
            "asteroid mining",
            "lunar exploration",
            "space colonization",
            "astrobiology"
        ]
        
        for category, name in categories:
            for query in queries[:3]:  # Limit to avoid too many requests
                try:
                    search = arxiv.Search(
                        query=f"cat:{category} AND {query}",
                        max_results=5,
                        sort_by=arxiv.SortCriterion.Relevance
                    )
                    
                    for paper in search.results():
                        documents.append({
                            'title': paper.title,
                            'content': f"{paper.title}. {paper.summary}",
                            'url': paper.entry_id,
                            'source': f'arXiv ({name})',
                            'authors': ', '.join([author.name for author in paper.authors]),
                            'date': paper.published.strftime('%Y-%m-%d')
                        })
                        
                except Exception as e:
                    st.error(f"Error accessing arXiv {category}: {str(e)}")
                    continue
                    
        return documents
    
    def create_embeddings(self, documents: List[Dict]) -> np.ndarray:
        """Create embeddings for documents"""
        texts = [f"{doc['title']} {doc['content']}" for doc in documents]
        embeddings = self.model.encode(texts)
        return embeddings
    
    def build_index(self, embeddings: np.ndarray):
        """Build FAISS index for fast similarity search"""
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
    
    def save_index(self, documents: List[Dict], embeddings: np.ndarray):
        """Save the index and documents to disk"""
        os.makedirs('rag_data', exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, 'rag_data/faiss_index.bin')
        
        # Save documents and embeddings
        with open('rag_data/documents.pkl', 'wb') as f:
            pickle.dump(documents, f)
        
        with open('rag_data/embeddings.pkl', 'wb') as f:
            pickle.dump(embeddings, f)
    
    def load_or_create_index(self):
        """Load existing index or create new one"""
        if (os.path.exists('rag_data/faiss_index.bin') and 
            os.path.exists('rag_data/documents.pkl') and 
            os.path.exists('rag_data/embeddings.pkl')):
            
            # Load existing index
            self.index = faiss.read_index('rag_data/faiss_index.bin')
            
            with open('rag_data/documents.pkl', 'rb') as f:
                self.documents = pickle.load(f)
            
            with open('rag_data/embeddings.pkl', 'rb') as f:
                self.embeddings = pickle.load(f)
                
            st.success(f"Loaded existing index with {len(self.documents)} documents")
        else:
            st.warning("No existing index found. Please build the knowledge base first.")
    
    def build_knowledge_base(self):
        """Build the knowledge base by scraping multiple sources"""
        st.write("🔄 Building comprehensive knowledge base from multiple sources...")
        
        all_documents = []
        
        # Scrape NASA news
        with st.spinner("Scraping NASA news..."):
            nasa_docs = self.scrape_nasa_news(max_articles=30)
            all_documents.extend(nasa_docs)
            st.write(f"✅ Scraped {len(nasa_docs)} NASA news articles")
        
        # Scrape ESA news
        with st.spinner("Scraping European Space Agency news..."):
            esa_docs = self.scrape_esa_news(max_articles=25)
            all_documents.extend(esa_docs)
            st.write(f"✅ Scraped {len(esa_docs)} ESA articles")
        
        # Scrape SpaceX updates
        with st.spinner("Scraping SpaceX updates..."):
            spacex_docs = self.scrape_spacex_updates()
            all_documents.extend(spacex_docs)
            st.write(f"✅ Scraped {len(spacex_docs)} SpaceX updates")
        
        # Scrape Space.com news
        with st.spinner("Scraping Space.com news..."):
            space_com_docs = self.scrape_space_com_news(max_articles=20)
            all_documents.extend(space_com_docs)
            st.write(f"✅ Scraped {len(space_com_docs)} Space.com articles")
        
        # Scrape JAXA news
        with st.spinner("Scraping JAXA news..."):
            jaxa_docs = self.scrape_jaxa_news()
            all_documents.extend(jaxa_docs)
            st.write(f"✅ Scraped {len(jaxa_docs)} JAXA articles")
        
        # Scrape Canadian Space Agency
        with st.spinner("Scraping Canadian Space Agency news..."):
            csa_docs = self.scrape_csa_news()
            all_documents.extend(csa_docs)
            st.write(f"✅ Scraped {len(csa_docs)} CSA articles")
        
        # Scrape SpaceNews
        with st.spinner("Scraping SpaceNews articles..."):
            spacenews_docs = self.scrape_spacenews(max_articles=15)
            all_documents.extend(spacenews_docs)
            st.write(f"✅ Scraped {len(spacenews_docs)} SpaceNews articles")
        
        # Scrape Nature Astronomy
        with st.spinner("Scraping Nature Astronomy papers..."):
            nature_docs = self.scrape_nature_astronomy()
            all_documents.extend(nature_docs)
            st.write(f"✅ Scraped {len(nature_docs)} Nature Astronomy papers")
        
        # Scrape comprehensive arXiv papers
        with st.spinner("Scraping comprehensive arXiv papers across multiple categories..."):
            arxiv_comprehensive_docs = self.scrape_multiple_arxiv_categories()
            all_documents.extend(arxiv_comprehensive_docs)
            st.write(f"✅ Scraped {len(arxiv_comprehensive_docs)} comprehensive arXiv papers")
        
        # Basic arXiv queries for general topics
        with st.spinner("Scraping additional arXiv papers..."):
            for query in ["space telescope", "exoplanet", "dark matter", "black hole", "neutron star"]:
                arxiv_docs = self.scrape_arxiv_papers(query, max_papers=8)
                all_documents.extend(arxiv_docs)
                st.write(f"✅ Scraped {len(arxiv_docs)} papers for '{query}'")
        
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
        """Perform semantic search using the query"""
        if self.index is None or not self.documents:
            return []
        
        # Create embedding for the query
        query_embedding = self.model.encode([query])
        
        # Search the index
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Get the most relevant documents
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['relevance_score'] = 1 / (1 + distances[0][i])  # Convert distance to similarity
                results.append(doc)
        
        return results
    
    def generate_answer(self, query: str, relevant_docs: List[Dict]) -> str:
        """Generate an answer based on retrieved documents"""
        if not relevant_docs:
            return "I couldn't find relevant information in my knowledge base. Please try a different query or build the knowledge base with more documents."
        
        # Combine information from multiple sources
        answer = f"Based on my analysis of {len(relevant_docs)} relevant sources:\n\n"
        
        for i, doc in enumerate(relevant_docs[:3], 1):
            # Extract key information from each document
            content = doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content']
            answer += f"**Source {i} ({doc['source']}):**\n{content}\n\n"
        
        answer += "**Summary:** The above sources provide comprehensive information about your query. "
        answer += "Each source has been semantically matched to your question using advanced embedding models."
        
        return answer

# Initialize the RAG system
@st.cache_resource
def get_rag_system():
    rag = TrueRAGSystem()
    rag.initialize()
    return rag

def main():
    st.title("🚀 MSEIS - True RAG System")
    st.markdown("*Real Retrieval-Augmented Generation with Live Document Scraping*")
    
    # Initialize RAG system
    rag_system = get_rag_system()
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Knowledge Base Management")
        
        if st.button("🔨 Build Knowledge Base"):
            rag_system.build_knowledge_base()
        
        st.header("📊 System Status")
        if rag_system.documents:
            st.write(f"📚 Documents: {len(rag_system.documents)}")
            st.write("🔍 Search Index: ✅ Ready")
            st.write("🤖 Embeddings: ✅ Loaded")
        else:
            st.write("📚 Documents: ❌ Not loaded")
            st.write("🔍 Search Index: ❌ Not ready")
        
        st.header("📖 Document Sources")
        st.write("• NASA News & Updates")
        st.write("• arXiv Scientific Papers")
        st.write("• NASA Technical Reports")
        st.write("• European Space Agency")
        st.write("• SpaceX Updates")
        st.write("• Space.com News")
        st.write("• JAXA News")
        st.write("• Canadian Space Agency")
        st.write("• SpaceNews")
        st.write("• Nature Astronomy")
        st.write("• Multiple arXiv Categories")
    
    # Main interface
    st.header("💬 Ask Anything About Space")
    st.markdown("*This system performs real semantic search across scraped documents*")
    
    # Query input
    query = st.text_input("Enter your question:", 
                         placeholder="e.g., What are the latest Mars exploration findings?")
    
    if query and rag_system.documents:
        with st.spinner("🔍 Performing semantic search..."):
            # Perform semantic search
            relevant_docs = rag_system.semantic_search(query, top_k=5)
            
            if relevant_docs:
                # Generate answer
                answer = rag_system.generate_answer(query, relevant_docs)
                
                # Display answer
                st.markdown("### 🤖 Answer")
                st.markdown(answer)
                
                # Display sources
                st.markdown("### 📚 Retrieved Sources")
                for i, doc in enumerate(relevant_docs, 1):
                    with st.expander(f"Source {i}: {doc['title'][:60]}... (Relevance: {doc['relevance_score']:.2f})"):
                        st.write(f"**Source:** {doc['source']}")
                        st.write(f"**URL:** {doc['url']}")
                        if 'authors' in doc:
                            st.write(f"**Authors:** {doc['authors']}")
                        st.write(f"**Date:** {doc.get('date', 'Unknown')}")
                        st.write(f"**Content:** {doc['content'][:500]}...")
            else:
                st.warning("No relevant documents found. Try building the knowledge base or rephrasing your query.")
    
    elif query and not rag_system.documents:
        st.error("Please build the knowledge base first using the sidebar button.")
    
    # Footer
    st.markdown("---")
    st.markdown("**🚀 True RAG System** - Real document retrieval with semantic search")

if __name__ == "__main__":
    main() 