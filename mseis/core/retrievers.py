# core/retrievers.py
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from abc import ABC, abstractmethod
import asyncio

from langchain.schema import Document
from langchain.retrievers import BaseRetriever
from rank_bm25 import BM25Okapi

from storage.pinecone_manager import PineconeManager
from storage.neo4j_manager import Neo4jManager
from core.embeddings import CachedOpenAIEmbeddings
from core.config import config
from utils.logging_config import get_logger
from utils.monitoring import monitor_performance

logger = get_logger(__name__)

class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining vector, keyword, and graph search"""
    
    def __init__(
        self,
        pinecone_manager: PineconeManager,
        embeddings: CachedOpenAIEmbeddings,
        namespace: str = "default",
        neo4j_manager: Optional[Neo4jManager] = None
    ):
        self.pinecone_manager = pinecone_manager
        self.embeddings = embeddings
        self.namespace = namespace
        self.neo4j_manager = neo4j_manager
        self.weights = config.get("retrieval.hybrid", {
            "vector_weight": 0.7,
            "keyword_weight": 0.2,
            "graph_weight": 0.1
        })
        
    @monitor_performance("retriever", "get_relevant_documents")
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Async retrieval of relevant documents"""
        # Get results from different retrieval methods
        tasks = [
            self._vector_search(query),
            self._keyword_search(query)
        ]
        
        if self.neo4j_manager:
            tasks.append(self._graph_search(query))
            
        results = await asyncio.gather(*tasks)
        
        # Combine and rerank results
        combined_docs = await self._combine_results(*results)
        
        return combined_docs[:config.get("retrieval.top_k", 10)]
        
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Sync wrapper for async retrieval"""
        return asyncio.run(self.aget_relevant_documents(query))
        
    async def _vector_search(self, query: str) -> List[Tuple[Document, float]]:
        """Vector similarity search"""
        # Generate query embedding
        query_embedding = await self.embeddings.embed_query(query)
        
        # Search in Pinecone
        results = await self.pinecone_manager.query_vectors(
            query_embedding=query_embedding,
            namespace=self.namespace,
            top_k=config.get("retrieval.top_k", 20),
            include_metadata=True
        )
        
        # Convert to documents
        docs_with_scores = []
        for result in results:
            metadata = result.get("metadata", {})
            doc = Document(
                page_content=metadata.get("text", ""),
                metadata={
                    **metadata,
                    "score": result["score"],
                    "retrieval_method": "vector"
                }
            )
            docs_with_scores.append((doc, result["score"]))
            
        return docs_with_scores
        
    async def _keyword_search(self, query: str) -> List[Tuple[Document, float]]:
        """BM25 keyword search"""
        # This is a simplified version - in production, you'd have a proper BM25 index
        # For now, we'll do a metadata search in Pinecone
        
        # Search for documents with matching keywords in metadata
        keywords = query.lower().split()
        filter_conditions = {
            "$or": [
                {"title": {"$in": keywords}},
                {"keywords": {"$in": keywords}}
            ]
        }
        
        results = await self.pinecone_manager.query_vectors(
            query_embedding=[0] * 1536,  # Dummy embedding
            namespace=self.namespace,
            top_k=config.get("retrieval.top_k", 20),
            filter=filter_conditions,
            include_metadata=True
        )
        
        # Convert to documents
        docs_with_scores = []
        for result in results:
            metadata = result.get("metadata", {})
            
            # Calculate keyword score
            text = metadata.get("text", "").lower()
            keyword_score = sum(1 for kw in keywords if kw in text) / len(keywords)
            
            doc = Document(
                page_content=metadata.get("text", ""),
                metadata={
                    **metadata,
                    "score": keyword_score,
                    "retrieval_method": "keyword"
                }
            )
            docs_with_scores.append((doc, keyword_score))
            
        return docs_with_scores
        
    async def _graph_search(self, query: str) -> List[Tuple[Document, float]]:
        """Graph-based entity search"""
        if not self.neo4j_manager:
            return []
            
        # Extract entities from query (simplified)
        entities = await self._extract_entities(query)
        
        if not entities:
            return []
            
        docs_with_scores = []
        
        for entity in entities[:2]:  # Limit to top 2 entities
            # Get subgraph around entity
            subgraph = await self.neo4j_manager.get_subgraph(
                center_node_id=entity["id"],
                depth=2,
                limit=10
            )
            
            # Convert graph data to documents
            for node in subgraph["nodes"]:
                doc = Document(
                    page_content=f"{node.get('name', node['id'])}: {node.get('description', '')}",
                    metadata={
                        **node,
                        "retrieval_method": "graph",
                        "entity_id": entity["id"]
                    }
                )
                
                # Simple relevance score based on graph distance
                score = 1.0 / (1 + len(subgraph["relationships"]))
                docs_with_scores.append((doc, score))
                
        return docs_with_scores
        
    async def _extract_entities(self, query: str) -> List[Dict[str, str]]:
        """Extract entities from query (simplified)"""
        # In production, use NER or entity linking
        # For now, simple keyword matching
        known_entities = {
            "apollo 11": {"id": "apollo11", "type": "Mission"},
            "mars": {"id": "mars", "type": "CelestialBody"},
            "iss": {"id": "iss", "type": "Mission"},
            "neil armstrong": {"id": "armstrong", "type": "Astronaut"}
        }
        
        query_lower = query.lower()
        found_entities = []
        
        for entity_name, entity_info in known_entities.items():
            if entity_name in query_lower:
                found_entities.append(entity_info)
                
        return found_entities
        
    async def _combine_results(
        self,
        vector_results: List[Tuple[Document, float]],
        keyword_results: List[Tuple[Document, float]],
        graph_results: Optional[List[Tuple[Document, float]]] = None
    ) -> List[Document]:
        """Combine and rerank results from different methods"""
        # Create a unified scoring system
        all_docs = {}
        
        # Add vector results
        for doc, score in vector_results:
            doc_id = doc.metadata.get("id", doc.page_content[:50])
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    "document": doc,
                    "scores": {},
                    "final_score": 0
                }
            all_docs[doc_id]["scores"]["vector"] = score
            
        # Add keyword results
        for doc, score in keyword_results:
            doc_id = doc.metadata.get("id", doc.page_content[:50])
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    "document": doc,
                    "scores": {},
                    "final_score": 0
                }
            all_docs[doc_id]["scores"]["keyword"] = score
            
        # Add graph results if available
        if graph_results:
            for doc, score in graph_results:
                doc_id = doc.metadata.get("id", doc.page_content[:50])
                if doc_id not in all_docs:
                    all_docs[doc_id] = {
                        "document": doc,
                        "scores": {},
                        "final_score": 0
                    }
                all_docs[doc_id]["scores"]["graph"] = score
                
        # Calculate final scores
        for doc_id, doc_info in all_docs.items():
            final_score = 0
            
            if "vector" in doc_info["scores"]:
                final_score += self.weights["vector_weight"] * doc_info["scores"]["vector"]
                
            if "keyword" in doc_info["scores"]:
                final_score += self.weights["keyword_weight"] * doc_info["scores"]["keyword"]
                
            if "graph" in doc_info["scores"] and graph_results:
                final_score += self.weights["graph_weight"] * doc_info["scores"]["graph"]
                
            doc_info["final_score"] = final_score
            doc_info["document"].metadata["final_score"] = final_score
            
        # Sort by final score
        sorted_docs = sorted(
            all_docs.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )
        
        return [item["document"] for item in sorted_docs] 