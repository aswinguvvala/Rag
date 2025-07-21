# core/rag_pipeline.py
"""
Enhanced RAG Pipeline with FAISS integration and Google Search fallback
Handles embedding, similarity search, and web search fallback
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from sentence_transformers import SentenceTransformer
import numpy as np

from storage.faiss_manager import FAISSManager
from core.config import config
from utils.logging_config import get_logger

logger = get_logger(__name__)

class RAGPipeline:
    """Enhanced RAG Pipeline with local embeddings and web search fallback"""
    
    def __init__(self):
        self.faiss_manager = FAISSManager()
        self.embedding_model = None
        self.embedding_dimension = 384  # for all-MiniLM-L6-v2
        self.similarity_threshold = 0.6
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the RAG pipeline"""
        try:
            # Initialize embedding model (free local model)
            logger.info("Loading sentence transformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer model loaded")
            
            # Initialize FAISS manager
            await self.faiss_manager.initialize(self.embedding_dimension)
            
            self.is_initialized = True
            logger.info("RAG Pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
            return False
    
    async def index_articles(self, articles_file: str = "space_articles_database.json") -> bool:
        """Index articles from the space articles database"""
        try:
            if not self.is_initialized:
                await self.initialize()
                
            # Load articles
            articles_path = Path(articles_file)
            if not articles_path.exists():
                logger.error(f"Articles file not found: {articles_file}")
                return False
                
            with open(articles_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                
            logger.info(f"Loaded {len(articles)} articles for indexing")
            
            # Process articles in batches
            batch_size = 50
            total_indexed = 0
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                
                # Prepare documents and texts for embedding
                documents = []
                texts_to_embed = []
                
                for article in batch:
                    # Create comprehensive text for embedding
                    title = article.get('title', '')
                    summary = article.get('summary', '')
                    content = article.get('content', '')[:2000]  # Limit content length
                    keywords = ' '.join(article.get('keywords', []))
                    
                    # Combine text components for embedding
                    combined_text = f"{title}. {summary}. {content}. Keywords: {keywords}"
                    texts_to_embed.append(combined_text)
                    
                    # Prepare document metadata
                    doc_metadata = {
                        'id': article.get('id', f"article_{i}"),
                        'title': title,
                        'category': article.get('category', 'unknown'),
                        'summary': summary,
                        'content': content,
                        'keywords': article.get('keywords', []),
                        'metadata': article.get('metadata', {}),
                        'source': 'space_articles_database'
                    }
                    documents.append(doc_metadata)
                
                # Generate embeddings
                embeddings = self.embedding_model.encode(
                    texts_to_embed, 
                    convert_to_numpy=True,
                    show_progress_bar=True
                ).tolist()
                
                # Add to FAISS index
                success = await self.faiss_manager.add_documents(documents, embeddings)
                
                if success:
                    total_indexed += len(batch)
                    logger.info(f"Indexed batch {i//batch_size + 1}: {total_indexed}/{len(articles)} articles")
                else:
                    logger.error(f"Failed to index batch {i//batch_size + 1}")
                    
            logger.info(f"Successfully indexed {total_indexed} articles")
            return total_indexed > 0
            
        except Exception as e:
            logger.error(f"Error indexing articles: {str(e)}")
            return False
    
    async def search_similar_documents(
        self, 
        query: str, 
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Search for similar documents in the local database
        Returns: (results, has_similar_docs)
        """
        try:
            if not self.is_initialized:
                await self.initialize()
                
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0].tolist()
            
            # Search in FAISS
            results, has_similar = await self.faiss_manager.similarity_search(
                query_embedding=query_embedding,
                top_k=top_k,
                similarity_threshold=threshold or self.similarity_threshold
            )
            
            return results, has_similar
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return [], False
    
    def set_similarity_threshold(self, threshold: float):
        """Update similarity threshold"""
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
            self.faiss_manager.set_similarity_threshold(threshold)
            logger.info(f"Updated similarity threshold to {threshold}")
        else:
            logger.warning("Threshold must be between 0.0 and 1.0")
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        if not self.is_initialized:
            return {"error": "Pipeline not initialized"}
            
        faiss_stats = await self.faiss_manager.get_stats()
        return {
            **faiss_stats,
            "embedding_model": "all-MiniLM-L6-v2",
            "similarity_threshold": self.similarity_threshold
        }
    
    def create_context_window(
        self, 
        user_question: str, 
        similar_docs: List[Dict[str, Any]],
        web_results: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Create structured context window for LLM"""
        
        context_parts = []
        
        # Add user question
        context_parts.append(f"USER QUESTION: {user_question}")
        context_parts.append("\n" + "="*50 + "\n")
        
        # Add similar documents from local database
        if similar_docs:
            context_parts.append("RELEVANT DOCUMENTS FROM LOCAL DATABASE:")
            for i, doc in enumerate(similar_docs, 1):
                metadata = doc.get('metadata', {})
                context_parts.append(f"\nDocument {i}:")
                context_parts.append(f"Title: {metadata.get('title', 'Unknown')}")
                context_parts.append(f"Category: {metadata.get('category', 'Unknown')}")
                context_parts.append(f"Summary: {metadata.get('summary', '')}")
                context_parts.append(f"Similarity Score: {doc.get('score', 0.0):.3f}")
                
                # Add content preview
                content = metadata.get('content', '')
                if content:
                    preview = content[:800] + "..." if len(content) > 800 else content
                    context_parts.append(f"Content: {preview}")
                
                context_parts.append("-" * 40)
        
        # Add web search results if available
        if web_results:
            context_parts.append("\nADDITIONAL INFORMATION FROM WEB SEARCH:")
            for i, result in enumerate(web_results, 1):
                context_parts.append(f"\nWeb Result {i}:")
                context_parts.append(f"Title: {result.get('title', 'Unknown')}")
                context_parts.append(f"URL: {result.get('url', 'Unknown')}")
                context_parts.append(f"Snippet: {result.get('snippet', '')}")
                context_parts.append("-" * 40)
        
        # Add instructions
        context_parts.append("\nINSTRUCTIONS:")
        context_parts.append("- Answer the user's question using ONLY the information provided above")
        context_parts.append("- If the provided information is insufficient, clearly state what's missing")
        context_parts.append("- Cite your sources (Document 1, Document 2, Web Result 1, etc.)")
        context_parts.append("- Do NOT use any knowledge outside of the provided context")
        context_parts.append("- Be specific and accurate in your response")
        
        return "\n".join(context_parts)