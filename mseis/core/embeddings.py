# core/embeddings.py
from typing import List, Dict, Any, Optional
import numpy as np
from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain.embeddings import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
import torch

from core.config import config
from utils.logging_config import get_logger
from utils.monitoring import monitor_performance
from storage.cache_manager import CacheManager

logger = get_logger(__name__)

class BaseEmbedding(ABC):
    """Base class for embedding models"""
    
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        pass
        
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        pass

class CachedOpenAIEmbeddings(BaseEmbedding):
    """OpenAI embeddings with caching support"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.embeddings = OpenAIEmbeddings(
            model=config.api.openai_embedding_model,
            openai_api_key=config.api.openai_api_key
        )
        self.cache_manager = cache_manager
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    @monitor_performance("embeddings", "embed_documents")
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents with caching"""
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache
        if self.cache_manager:
            for i, text in enumerate(texts):
                cache_key = f"emb_doc_{hash(text)}"
                cached = await self.cache_manager.get(cache_key, namespace="embeddings")
                
                if cached:
                    embeddings.append(cached)
                else:
                    embeddings.append(None)
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))
            embeddings = [None] * len(texts)
            
        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.embeddings.embed_documents,
                uncached_texts
            )
            
            # Update results and cache
            for idx, emb in zip(uncached_indices, new_embeddings):
                embeddings[idx] = emb
                
                if self.cache_manager:
                    cache_key = f"emb_doc_{hash(texts[idx])}"
                    await self.cache_manager.set(
                        cache_key,
                        emb,
                        namespace="embeddings",
                        ttl=86400  # 24 hours
                    )
                    
        return embeddings
        
    @monitor_performance("embeddings", "embed_query")
    async def embed_query(self, text: str) -> List[float]:
        """Embed query with caching"""
        # Check cache
        if self.cache_manager:
            cache_key = f"emb_query_{hash(text)}"
            cached = await self.cache_manager.get(cache_key, namespace="embeddings")
            
            if cached:
                return cached
                
        # Generate embedding
        embedding = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.embeddings.embed_query,
            text
        )
        
        # Cache result
        if self.cache_manager:
            await self.cache_manager.set(
                cache_key,
                embedding,
                namespace="embeddings",
                ttl=3600  # 1 hour
            )
            
        return embedding

class MultiModalEmbedding:
    """Handles embeddings for different modalities"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.text_embeddings = CachedOpenAIEmbeddings(cache_manager)
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache_manager = cache_manager
        
    async def embed_multimodal(
        self,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[float]]:
        """Generate embeddings for multiple modalities"""
        embeddings = {}
        
        if text:
            # Primary text embedding
            embeddings["text"] = await self.text_embeddings.embed_query(text)
            
            # Secondary embedding for hybrid search
            embeddings["dense"] = self.sentence_transformer.encode(text).tolist()
            
        if metadata:
            # Create metadata embedding
            metadata_text = " ".join([f"{k}: {v}" for k, v in metadata.items()])
            embeddings["metadata"] = await self.text_embeddings.embed_query(metadata_text)
            
        return embeddings 