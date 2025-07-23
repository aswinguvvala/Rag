# core/enhanced_rag_system_v2.py
"""
Enhanced RAG System V2 - Robust orchestrator with comprehensive fallbacks
Handles missing dependencies gracefully while maximizing available functionality
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import time
import json
from pathlib import Path

# Feature Detection System
FEATURES = {
    'sentence_transformers': False,
    'chromadb': False,
    'sklearn': False,
    'transformers': False,
    'torch': False,
    'faiss': False,
    'langchain': False,
    'beautifulsoup4': False,
    'web_search': True  # Always available with basic requests
}

FEATURE_ERRORS = {}

# Test each feature independently
def detect_features():
    """Detect available features and log any import errors"""
    global FEATURES, FEATURE_ERRORS
    
    # Test sentence-transformers
    try:
        import sentence_transformers
        FEATURES['sentence_transformers'] = True
    except ImportError as e:
        FEATURE_ERRORS['sentence_transformers'] = str(e)
    
    # Test ChromaDB
    try:
        import chromadb
        FEATURES['chromadb'] = True
    except ImportError as e:
        FEATURE_ERRORS['chromadb'] = str(e)
    
    # Test sklearn
    try:
        import sklearn
        FEATURES['sklearn'] = True
    except ImportError as e:
        FEATURE_ERRORS['sklearn'] = str(e)
    
    # Test transformers
    try:
        import transformers
        FEATURES['transformers'] = True
    except ImportError as e:
        FEATURE_ERRORS['transformers'] = str(e)
    
    # Test torch
    try:
        import torch
        FEATURES['torch'] = True
    except ImportError as e:
        FEATURE_ERRORS['torch'] = str(e)
    
    # Test FAISS (optional)
    try:
        import faiss
        FEATURES['faiss'] = True
    except ImportError as e:
        FEATURE_ERRORS['faiss'] = str(e)
    
    # Test LangChain
    try:
        import langchain
        FEATURES['langchain'] = True
    except ImportError as e:
        FEATURE_ERRORS['langchain'] = str(e)
    
    # Test BeautifulSoup
    try:
        import bs4
        FEATURES['beautifulsoup4'] = True
    except ImportError as e:
        FEATURE_ERRORS['beautifulsoup4'] = str(e)

# Run feature detection
detect_features()

# Conditional imports based on available features
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Import vector storage managers
vector_store = None
if FEATURES['chromadb']:
    try:
        from storage.chromadb_manager import ChromaDBManager
        vector_store = ChromaDBManager()
        VECTOR_STORE_TYPE = "chromadb"
    except ImportError as e:
        logger.warning(f"ChromaDB manager import failed: {e}")

if not vector_store and FEATURES['sklearn']:
    try:
        from storage.chromadb_manager import SklearnVectorStore
        vector_store = SklearnVectorStore()
        VECTOR_STORE_TYPE = "sklearn"
    except ImportError as e:
        logger.warning(f"Sklearn vector store import failed: {e}")

if not vector_store and FEATURES['faiss']:
    try:
        from storage.faiss_manager import FAISSManager
        vector_store = FAISSManager()
        VECTOR_STORE_TYPE = "faiss"
    except ImportError as e:
        logger.warning(f"FAISS manager import failed: {e}")

# Import embedding model
embedding_model = None
if FEATURES['sentence_transformers']:
    try:
        from sentence_transformers import SentenceTransformer
        EMBEDDING_AVAILABLE = True
    except ImportError:
        EMBEDDING_AVAILABLE = False
else:
    EMBEDDING_AVAILABLE = False

# Web search capability
if FEATURES['beautifulsoup4']:
    try:
        from core.web_search import WebSearchManager
        WEB_SEARCH_AVAILABLE = True
    except ImportError:
        WEB_SEARCH_AVAILABLE = False
else:
    WEB_SEARCH_AVAILABLE = False


class EnhancedRAGSystemV2:
    """Enhanced RAG System with comprehensive fallback handling"""
    
    def __init__(self):
        self.is_initialized = False
        self.capabilities = {}
        self.vector_store = vector_store
        self.embedding_model = None
        self.web_search = None
        
        # Configuration
        self.similarity_threshold = 0.6
        self.max_local_results = 5
        self.max_web_results = 3
        self.enable_web_fallback = True
        
        # Determine system capabilities
        self._analyze_capabilities()
        
    def _analyze_capabilities(self):
        """Analyze what capabilities are available"""
        self.capabilities = {
            'semantic_search': EMBEDDING_AVAILABLE and vector_store is not None,
            'vector_storage': vector_store is not None,
            'web_search': WEB_SEARCH_AVAILABLE or True,  # Basic web search always available
            'text_processing': FEATURES['transformers'],
            'advanced_ml': FEATURES['torch'] and FEATURES['transformers'],
            'document_parsing': FEATURES['beautifulsoup4'],
            'langchain_integration': FEATURES['langchain']
        }
        
        # Determine system mode based on available capabilities
        if self.capabilities['semantic_search'] and self.capabilities['vector_storage']:
            self.system_mode = "full_semantic"
        elif self.capabilities['vector_storage']:
            self.system_mode = "vector_only"
        elif self.capabilities['web_search']:
            self.system_mode = "web_search"
        else:
            self.system_mode = "basic_text"
            
        # Log available features for debugging
        available_features = [k for k, v in FEATURES.items() if v]
        missing_features = [k for k, v in FEATURES.items() if not v]
        logger.info(f"System capabilities analysis complete")
        logger.info(f"Available features: {available_features}")
        logger.info(f"Missing features: {missing_features}")
        logger.info(f"System mode: {self.system_mode}")
    
    async def initialize(self):
        """Initialize the RAG system with available components"""
        try:
            logger.info(f"Initializing Enhanced RAG System V2...")
            logger.info(f"System mode: {self.system_mode}")
            logger.info(f"Available features: {[k for k, v in FEATURES.items() if v]}")
            
            # Initialize embedding model if available
            if EMBEDDING_AVAILABLE:
                try:
                    logger.info("Loading sentence transformer model...")
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Sentence transformer model loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load embedding model: {e}")
                    self.capabilities['semantic_search'] = False
            
            # Initialize vector store if available
            if self.vector_store:
                try:
                    success = await self.vector_store.initialize(dimension=384)
                    if success:
                        logger.info(f"Vector store initialized: {VECTOR_STORE_TYPE}")
                    else:
                        logger.warning("Vector store initialization failed")
                        self.capabilities['vector_storage'] = False
                except Exception as e:
                    logger.error(f"Vector store initialization error: {e}")
                    self.capabilities['vector_storage'] = False
            
            # Initialize web search if available
            if WEB_SEARCH_AVAILABLE:
                try:
                    self.web_search = WebSearchManager()
                    logger.info("Web search manager initialized")
                except Exception as e:
                    logger.warning(f"Web search initialization failed: {e}")
            
            self.is_initialized = True
            logger.info("Enhanced RAG System V2 initialized successfully")
            
            # Report final capabilities
            active_capabilities = [k for k, v in self.capabilities.items() if v]
            logger.info(f"Active capabilities: {active_capabilities}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced RAG System V2: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'initialized': self.is_initialized,
            'system_mode': self.system_mode,
            'capabilities': self.capabilities,
            'available_features': {k: v for k, v in FEATURES.items() if v},
            'missing_features': {k: FEATURE_ERRORS.get(k, 'Import failed') for k, v in FEATURES.items() if not v},
            'vector_store_type': VECTOR_STORE_TYPE if vector_store else None,
            'embedding_model': 'all-MiniLM-L6-v2' if self.embedding_model else None
        }
    
    async def index_database(self, force_reindex: bool = False) -> bool:
        """Index the database with available capabilities"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not self.capabilities['vector_storage']:
                logger.warning("No vector storage available - skipping indexing")
                return True  # Not a failure, just not needed
            
            # Check if already indexed
            if not force_reindex:
                try:
                    stats = await self.vector_store.get_collection_stats()
                    if stats.get('document_count', 0) > 0:
                        logger.info(f"Database already indexed with {stats['document_count']} documents")
                        return True
                except:
                    pass
            
            # Load and index documents
            documents = await self._load_default_documents()
            if not documents:
                logger.warning("No documents to index")
                return True
            
            # Generate embeddings if possible
            if self.capabilities['semantic_search']:
                embeddings = await self._generate_embeddings([doc['content'] for doc in documents])
                success = await self.vector_store.add_documents(documents, embeddings)
            else:
                # Add documents without embeddings (for text-based search)
                success = await self.vector_store.add_documents(documents, [])
            
            if success:
                logger.info(f"Successfully indexed {len(documents)} documents")
            
            return success
            
        except Exception as e:
            logger.error(f"Database indexing failed: {str(e)}")
            return False
    
    async def _load_default_documents(self) -> List[Dict[str, Any]]:
        """Load default documents for indexing"""
        # Try to load from space data
        try:
            from data_sources.space_data_loader import SpaceDataLoader
            loader = SpaceDataLoader()
            documents = await loader.load_all_data()
            if documents:
                return documents
        except Exception as e:
            logger.warning(f"Could not load space data: {e}")
        
        # Fallback to simple default documents
        return [
            {
                'id': 'welcome',
                'title': 'Welcome to IntelliSearch',
                'content': 'IntelliSearch is an advanced AI-powered search and retrieval system that combines semantic search with web fallback capabilities.',
                'source': 'system'
            },
            {
                'id': 'capabilities',
                'title': 'System Capabilities',
                'content': f'Current system mode: {self.system_mode}. Available capabilities: {", ".join([k for k, v in self.capabilities.items() if v])}.',
                'source': 'system'
            },
            {
                'id': 'ai_search',
                'title': 'AI-Powered Search',
                'content': 'The system uses advanced natural language processing and machine learning techniques to understand queries and retrieve relevant information.',
                'source': 'system'
            }
        ]
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        if not self.embedding_model:
            logger.error("No embedding model available")
            return []
            
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []
    
    async def query(self, question: str) -> Dict[str, Any]:
        """Process a query using available capabilities"""
        try:
            start_time = time.time()
            
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"Processing query in {self.system_mode} mode: {question}")
            
            # Try semantic search first if available
            if self.capabilities['semantic_search']:
                result = await self._semantic_search(question)
                if result.get('response'):
                    result['method'] = 'semantic_search'
                    result['query_time'] = time.time() - start_time
                    return result
            
            # Try vector search without semantic embeddings
            if self.capabilities['vector_storage']:
                result = await self._vector_search(question)
                if result.get('response'):
                    result['method'] = 'vector_search'
                    result['query_time'] = time.time() - start_time
                    return result
            
            # Try web search
            if self.capabilities['web_search']:
                result = await self._web_search(question)
                if result.get('response'):
                    result['method'] = 'web_search'
                    result['query_time'] = time.time() - start_time
                    return result
            
            # Basic text response
            result = await self._basic_response(question)
            result['method'] = 'basic_response'
            result['query_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            return {
                'response': f"Error processing query: {str(e)}",
                'method': 'error',
                'sources': [],
                'confidence': 0.0
            }
    
    async def _semantic_search(self, question: str) -> Dict[str, Any]:
        """Perform semantic search using embeddings"""
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings([question])
            if not query_embedding:
                return {}
            
            # Search vector store
            similar_docs = await self.vector_store.search_similar(
                query_embedding[0], 
                top_k=self.max_local_results
            )
            
            if similar_docs:
                # Generate response from similar documents
                context = "\n".join([doc['content'] for doc in similar_docs[:3]])
                response = await self._generate_response(question, context, similar_docs)
                
                return {
                    'response': response,
                    'sources': similar_docs,
                    'confidence': max([doc.get('similarity', 0) for doc in similar_docs])
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {}
    
    async def _vector_search(self, question: str) -> Dict[str, Any]:
        """Perform vector search without semantic embeddings"""
        # This would be for vector stores that can do text-based search
        # Implementation depends on the specific vector store capabilities
        return {}
    
    async def _web_search(self, question: str) -> Dict[str, Any]:
        """Perform web search as fallback"""
        try:
            if self.web_search:
                # Use the web search manager's search_web method
                results, source_urls = await self.web_search.search_web(question, max_results=self.max_web_results)
                if results:
                    response = f"Based on web search results for '{question}':\n\n"
                    for i, result in enumerate(results[:3], 1):
                        response += f"{i}. {result.get('title', 'Search Result')}: {result.get('snippet', result.get('content', 'No description available'))}\n"
                        if result.get('url'):
                            response += f"   Source: {result.get('url')}\n"
                    
                    # Format sources for display
                    formatted_sources = []
                    for result in results:
                        formatted_sources.append({
                            'title': result.get('title', 'Web Search Result'),
                            'url': result.get('url', '#'),
                            'snippet': result.get('snippet', result.get('content', 'No description available')),
                            'source': 'web_search'
                        })
                    
                    return {
                        'response': response,
                        'sources': formatted_sources,
                        'confidence': 0.7
                    }
            
            # Basic web search fallback when WebSearchManager is not available
            return {
                'response': f"""I understand you're asking about: "{question}"

While I don't have specific information about this topic in my current knowledge base, here are some suggestions:

1. **Search Strategy**: Try searching for "{question}" using web search engines
2. **Related Topics**: Consider searching for related space exploration topics
3. **Authoritative Sources**: Check NASA, ESA, or other space agency websites
4. **Academic Resources**: Look for peer-reviewed publications on this topic

For space-related queries, I have comprehensive information about space missions, planets, astronauts, and space technology. Feel free to ask about specific space topics!""",
                'sources': [],
                'confidence': 0.4
            }
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                'response': f"I apologize, but I'm unable to search the web for information about '{question}' at the moment. However, I have extensive knowledge about space exploration, astronomy, and related topics. Please feel free to ask me about specific space missions, planets, astronauts, or space technology!",
                'sources': [],
                'confidence': 0.3
            }
    
    async def _basic_response(self, question: str) -> Dict[str, Any]:
        """Generate basic response when other methods fail"""
        # Provide space-themed guidance based on common question patterns
        space_keywords = ['space', 'moon', 'mars', 'planet', 'rocket', 'astronaut', 'nasa', 'satellite', 'galaxy', 'star']
        is_space_related = any(keyword in question.lower() for keyword in space_keywords)
        
        if is_space_related:
            response = f"""I understand you're asking about: "{question}"

🚀 **Space Information Available**: I have comprehensive information about:
- **Space Missions**: NASA programs, SpaceX launches, international missions
- **Planets & Astronomy**: Solar system objects, exoplanets, deep space
- **Space Technology**: Rockets, satellites, space stations, instruments
- **Astronauts**: Biographies and achievements of space explorers
- **Space History**: Major milestones and timeline of space exploration

**Current System Status**: 
- Available capabilities: {', '.join([k.replace('_', ' ').title() for k, v in self.capabilities.items() if v])}
- System mode: {self.system_mode.replace('_', ' ').title()}

**Try asking about**: Specific space missions, planets, astronauts, or space technology topics for detailed information!"""
        else:
            response = f"""I understand you're asking about: "{question}"

While this doesn't appear to be a space-related question, I can help you in several ways:

🔍 **Search Suggestions**:
1. **Web Search**: Try searching for "{question}" using search engines
2. **Specific Sources**: Look for authoritative sources related to your topic
3. **Academic Resources**: Check for peer-reviewed information

🚀 **My Specialty**: I have extensive knowledge about space exploration, astronomy, and related topics:
- Space missions and technology
- Planets and celestial objects  
- Astronauts and space history
- Current space developments

**Current System Capabilities**: {', '.join([k.replace('_', ' ').title() for k, v in self.capabilities.items() if v])}

Feel free to ask me about space topics, or try rephrasing your question if it's space-related!"""
        
        return {
            'response': response,
            'sources': [],
            'confidence': 0.5
        }
    
    async def _generate_response(self, question: str, context: str, sources: List[Dict]) -> str:
        """Generate response from context and sources"""
        # Simple response generation - could be enhanced with language models
        response = f"Based on the available information about '{question}':\n\n"
        
        if context:
            # Extract key information from context
            sentences = context.split('. ')
            relevant_sentences = sentences[:3]  # Take first 3 sentences
            response += '. '.join(relevant_sentences)
            
            if len(sentences) > 3:
                response += "..."
        
        if sources:
            response += f"\n\nThis information comes from {len(sources)} relevant sources"
            if sources[0].get('metadata', {}).get('title'):
                response += f", including: {sources[0]['metadata']['title']}"
        
        return response
    
    def configure(self, **kwargs):
        """Configure system parameters"""
        if 'similarity_threshold' in kwargs:
            self.similarity_threshold = kwargs['similarity_threshold']
            if self.vector_store:
                self.vector_store.similarity_threshold = self.similarity_threshold
        
        if 'enable_web_fallback' in kwargs:
            self.enable_web_fallback = kwargs['enable_web_fallback']
        
        if 'max_local_results' in kwargs:
            self.max_local_results = kwargs['max_local_results']
        
        if 'max_web_results' in kwargs:
            self.max_web_results = kwargs['max_web_results']