# core/enhanced_rag_system.py
"""
Enhanced RAG System - Complete orchestrator
Combines FAISS similarity search with Google Search fallback
Prevents hallucination through strict context control
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import time

from core.rag_pipeline import RAGPipeline  
from core.web_search import WebSearchManager
from utils.logging_config import get_logger

logger = get_logger(__name__)

class EnhancedRAGSystem:
    """Complete RAG system with local similarity search and web fallback"""
    
    def __init__(self):
        self.rag_pipeline = RAGPipeline()
        self.web_search = WebSearchManager()
        self.is_initialized = False
        
        # Configuration
        self.similarity_threshold = 0.6
        self.max_local_results = 5
        self.max_web_results = 3
        self.enable_web_fallback = True
        
    async def initialize(self):
        """Initialize the complete RAG system"""
        try:
            logger.info("Initializing Enhanced RAG System...")
            
            # Initialize RAG pipeline
            success = await self.rag_pipeline.initialize()
            if not success:
                logger.error("Failed to initialize RAG pipeline")
                return False
            
            self.is_initialized = True
            logger.info("Enhanced RAG System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced RAG System: {str(e)}")
            return False
    
    async def index_database(self, force_reindex: bool = False) -> bool:
        """Index the article database"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Check if already indexed (unless forcing reindex)
            stats = await self.rag_pipeline.get_index_stats()
            if stats.get('total_vectors', 0) > 0 and not force_reindex:
                logger.info(f"Database already indexed with {stats['total_vectors']} articles")
                return True
            
            logger.info("Starting database indexing...")
            success = await self.rag_pipeline.index_articles()
            
            if success:
                stats = await self.rag_pipeline.get_index_stats()
                logger.info(f"Successfully indexed {stats.get('total_vectors', 0)} articles")
            
            return success
            
        except Exception as e:
            logger.error(f"Error indexing database: {str(e)}")
            return False
    
    async def query(self, user_question: str) -> Dict[str, Any]:
        """
        Process user query through the complete RAG pipeline
        Returns comprehensive response with source attribution
        """
        start_time = time.time()
        
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"Processing query: '{user_question}'")
            
            # Phase 1: Search local database
            local_results, has_similar_docs = await self.rag_pipeline.search_similar_documents(
                query=user_question,
                top_k=self.max_local_results,
                threshold=self.similarity_threshold
            )
            
            web_results = None
            search_strategy = "local_database"
            
            # Phase 2: Web search fallback if needed
            if not has_similar_docs and self.enable_web_fallback:
                logger.info("No similar documents found locally, performing web search...")
                search_strategy = "web_fallback"
                
                web_search_result = await self.web_search.comprehensive_web_search(
                    query=user_question,
                    extract_content=True
                )
                
                if web_search_result.get('has_results'):
                    web_results = web_search_result['results'][:self.max_web_results]
                    logger.info(f"Found {len(web_results)} web results")
                else:
                    logger.info("No web results found")
            
            # Phase 3: Create context window
            context_window = self.rag_pipeline.create_context_window(
                user_question=user_question,
                similar_docs=local_results,
                web_results=web_results
            )
            
            # Phase 4: Prepare response data
            response_data = {
                'query': user_question,
                'search_strategy': search_strategy,
                'has_local_results': has_similar_docs,
                'local_results': local_results,
                'web_results': web_results or [],
                'context_window': context_window,
                'processing_time': time.time() - start_time,
                'sources': self._extract_sources(local_results, web_results),
                'ready_for_llm': True,
                'message': self._generate_status_message(search_strategy, local_results, web_results)
            }
            
            logger.info(f"Query processed in {response_data['processing_time']:.2f} seconds")
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'query': user_question,
                'search_strategy': 'error',
                'has_local_results': False,
                'local_results': [],
                'web_results': [],
                'context_window': '',
                'processing_time': time.time() - start_time,
                'sources': [],
                'ready_for_llm': False,
                'error': str(e),
                'message': f'Error processing query: {str(e)}'
            }
    
    def _extract_sources(self, local_results: List[Dict], web_results: Optional[List[Dict]]) -> List[Dict[str, str]]:
        """Extract source information for citation"""
        sources = []
        
        # Local database sources
        for i, result in enumerate(local_results, 1):
            metadata = result.get('metadata', {})
            sources.append({
                'type': 'database',
                'id': f"doc_{i}",
                'title': metadata.get('title', 'Unknown'),
                'category': metadata.get('category', 'Unknown'),
                'score': f"{result.get('score', 0.0):.3f}"
            })
        
        # Web sources
        if web_results:
            for i, result in enumerate(web_results, 1):
                sources.append({
                    'type': 'web',
                    'id': f"web_{i}",
                    'title': result.get('title', 'Unknown'),
                    'url': result.get('url', ''),
                    'source': result.get('source', 'Web')
                })
        
        return sources
    
    def _generate_status_message(self, strategy: str, local_results: List, web_results: Optional[List]) -> str:
        """Generate human-readable status message"""
        if strategy == "local_database":
            return f"Found {len(local_results)} relevant articles in local database"
        elif strategy == "web_fallback":
            web_count = len(web_results) if web_results else 0
            return f"No similar articles found locally. Retrieved {web_count} results from web search"
        else:
            return "Query processed"
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            if not self.is_initialized:
                await self.initialize()
                
            rag_stats = await self.rag_pipeline.get_index_stats()
            
            return {
                'system': {
                    'initialized': self.is_initialized,
                    'similarity_threshold': self.similarity_threshold,
                    'web_fallback_enabled': self.enable_web_fallback
                },
                'database': rag_stats,
                'capabilities': {
                    'local_search': True,
                    'web_fallback': self.enable_web_fallback,
                    'content_extraction': True,
                    'source_attribution': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return {'error': str(e)}
    
    def configure(
        self, 
        similarity_threshold: Optional[float] = None,
        enable_web_fallback: Optional[bool] = None,
        max_local_results: Optional[int] = None,
        max_web_results: Optional[int] = None
    ):
        """Configure system parameters"""
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
            self.rag_pipeline.set_similarity_threshold(similarity_threshold)
            
        if enable_web_fallback is not None:
            self.enable_web_fallback = enable_web_fallback
            
        if max_local_results is not None:
            self.max_local_results = max_local_results
            
        if max_web_results is not None:
            self.max_web_results = max_web_results
            
        logger.info(f"System configured: threshold={self.similarity_threshold}, web_fallback={self.enable_web_fallback}")
    
    async def test_system(self) -> Dict[str, Any]:
        """Run system tests"""
        test_results = {
            'initialization': False,
            'database_indexing': False,
            'local_search': False,
            'web_search': False,
            'overall_status': 'FAILED'
        }
        
        try:
            # Test initialization
            test_results['initialization'] = await self.initialize()
            
            # Test database indexing
            test_results['database_indexing'] = await self.index_database()
            
            # Test local search with known query
            query_result = await self.query("What is Mars exploration?")
            test_results['local_search'] = query_result.get('ready_for_llm', False)
            
            # Test web search with non-space query
            web_query_result = await self.query("What is quantum computing?")
            test_results['web_search'] = web_query_result.get('search_strategy') == 'web_fallback'
            
            # Overall status
            if all([test_results['initialization'], test_results['database_indexing'], test_results['local_search']]):
                test_results['overall_status'] = 'PASSED'
            
            return test_results
            
        except Exception as e:
            logger.error(f"System test failed: {str(e)}")
            test_results['error'] = str(e)
            return test_results