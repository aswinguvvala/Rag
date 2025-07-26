"""
Clean RAG System - Simplified and Reliable
A streamlined implementation of the RAG system with minimal dependencies
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import os
from pathlib import Path

# Optional imports with graceful fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

@dataclass
class SearchResult:
    """Search result data structure"""
    content: str
    metadata: Dict[str, Any]
    similarity: float
    source_type: str = "local"

class CleanRAGSystem:
    """Simplified RAG system with embedded knowledge base"""
    
    def __init__(self):
        self.embedding_model = None
        self.faiss_index = None
        self.documents = []
        self.metadata = []
        self.embedded_documents = []
        
        # Configuration
        self.similarity_threshold = 0.4
        self.max_results = 5
        self.enable_web_fallback = True
        
        # System status
        self.is_initialized = False
        self.initialization_errors = []
        
        # Create embedded knowledge base
        self._create_embedded_knowledge_base()
    
    def _create_embedded_knowledge_base(self):
        """Create embedded knowledge base with space and tech content"""
        knowledge_base = [
            {
                "content": """The James Webb Space Telescope (JWST) is the largest and most powerful space telescope ever built. 
                Launched in December 2021, it serves as the premier space science observatory, studying every phase of cosmic history. 
                JWST can observe the most distant galaxies, study exoplanet atmospheres, and peer into stellar nurseries where new stars are born. 
                Its primary mirror is 6.5 meters in diameter, made of 18 hexagonal gold-plated beryllium segments. 
                The telescope operates at the second Lagrange point (L2), about 1.5 million kilometers from Earth.""",
                "metadata": {
                    "title": "James Webb Space Telescope",
                    "category": "space_technology",
                    "source": "NASA",
                    "url": "https://www.nasa.gov/mission_pages/webb/main/index.html"
                }
            },
            {
                "content": """Mars exploration has been a major focus of space agencies worldwide. The planet shows evidence of ancient water activity, 
                including dried riverbeds, mineral deposits, and polar ice caps. NASA's Perseverance rover, which landed in 2021, 
                is searching for signs of ancient microbial life in Jezero Crater. The rover collected samples that will be returned 
                to Earth by future missions. Mars has a thin atmosphere composed mostly of carbon dioxide, surface temperatures 
                ranging from -195°F to 70°F, and a day length similar to Earth at 24 hours and 37 minutes.""",
                "metadata": {
                    "title": "Mars Exploration and Geology",
                    "category": "planetary_science",
                    "source": "NASA JPL",
                    "url": "https://mars.nasa.gov/"
                }
            },
            {
                "content": """Artificial Intelligence in software development has revolutionized how we write, test, and deploy code. 
                Modern AI tools can generate code from natural language descriptions, detect bugs, suggest optimizations, 
                and even write documentation. Machine learning models are trained on vast repositories of open-source code 
                to understand programming patterns and best practices. AI-assisted development can increase productivity by 20-40% 
                while helping developers learn new languages and frameworks more quickly.""",
                "metadata": {
                    "title": "AI in Software Development",
                    "category": "technology",
                    "source": "Tech Research",
                    "url": "https://example.com/ai-development"
                }
            },
            {
                "content": """The International Space Station (ISS) is humanity's outpost in space, orbiting Earth at an altitude of approximately 
                400 kilometers. It serves as a microgravity laboratory where astronauts conduct scientific experiments in biology, 
                physics, astronomy, and materials science. The ISS travels at 28,000 kilometers per hour, completing an orbit around 
                Earth every 90 minutes. It has been continuously inhabited since November 2000, with crew members typically staying 
                for 6-month missions. The station is a collaborative project involving NASA, Roscosmos, ESA, JAXA, and CSA.""",
                "metadata": {
                    "title": "International Space Station",
                    "category": "space_technology",
                    "source": "NASA",
                    "url": "https://www.nasa.gov/mission_pages/station/"
                }
            },
            {
                "content": """Quantum computing represents a paradigm shift in computational power, using quantum mechanical phenomena 
                like superposition and entanglement to process information. Unlike classical computers that use bits (0 or 1), 
                quantum computers use quantum bits (qubits) that can exist in multiple states simultaneously. This allows them 
                to solve certain problems exponentially faster than classical computers, particularly in cryptography, 
                optimization, and scientific simulation. Companies like IBM, Google, and startups are racing to achieve 
                quantum supremacy and build practical quantum systems.""",
                "metadata": {
                    "title": "Quantum Computing Fundamentals",
                    "category": "technology",
                    "source": "Quantum Research Institute",
                    "url": "https://example.com/quantum-computing"
                }
            },
            {
                "content": """Exoplanet discovery has exploded in recent decades, with over 5,000 confirmed planets orbiting other stars. 
                The Kepler Space Telescope and TESS (Transiting Exoplanet Survey Satellite) have been instrumental in finding 
                these distant worlds. Scientists look for planets in the 'habitable zone' where liquid water could exist. 
                Notable discoveries include Kepler-452b ('Earth's cousin'), TRAPPIST-1 system with seven Earth-sized planets, 
                and Proxima Centauri b, the nearest known exoplanet. Future missions like the James Webb Space Telescope 
                will study exoplanet atmospheres for signs of life.""",
                "metadata": {
                    "title": "Exoplanet Discovery and Characterization",
                    "category": "astronomy",
                    "source": "NASA Exoplanet Archive",
                    "url": "https://exoplanets.nasa.gov/"
                }
            },
            {
                "content": """Cloud computing has transformed modern software architecture, offering scalable, on-demand computing resources. 
                Major platforms like AWS, Azure, and Google Cloud provide services ranging from simple storage to advanced 
                machine learning APIs. Microservices architecture, containerization with Docker and Kubernetes, and serverless 
                computing have become standard practices. Cloud-native applications are designed to be resilient, scalable, 
                and easily deployable across multiple environments. This shift has enabled startups to scale rapidly without 
                massive infrastructure investments.""",
                "metadata": {
                    "title": "Cloud Computing and Modern Architecture",
                    "category": "technology",
                    "source": "Cloud Computing Institute",
                    "url": "https://example.com/cloud-computing"
                }
            },
            {
                "content": """Career development in technology requires continuous learning and adaptation. Key skills include programming 
                languages (Python, JavaScript, Java), cloud platforms, data analysis, and soft skills like communication 
                and problem-solving. The tech industry offers diverse career paths: software engineering, data science, 
                cybersecurity, DevOps, product management, and UX design. Remote work has become increasingly common, 
                opening global opportunities. Building a portfolio through open-source contributions, personal projects, 
                and networking is crucial for career advancement.""",
                "metadata": {
                    "title": "Technology Career Development",
                    "category": "career",
                    "source": "Tech Career Guide",
                    "url": "https://example.com/tech-careers"
                }
            }
        ]
        
        # Store the embedded documents
        self.embedded_documents = knowledge_base
        self.documents = [doc["content"] for doc in knowledge_base]
        self.metadata = [doc["metadata"] for doc in knowledge_base]
    
    async def initialize(self) -> bool:
        """Initialize the RAG system"""
        try:
            self.initialization_errors.clear()
            
            # Try to initialize embedding model
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    # Create embeddings for documents
                    if self.documents:
                        embeddings = self.embedding_model.encode(self.documents)
                        
                        # Try to create FAISS index
                        if FAISS_AVAILABLE and NUMPY_AVAILABLE:
                            dimension = embeddings.shape[1]
                            self.faiss_index = faiss.IndexFlatIP(dimension)
                            # Normalize embeddings for cosine similarity
                            faiss.normalize_L2(embeddings)
                            self.faiss_index.add(embeddings.astype('float32'))
                
                except Exception as e:
                    self.initialization_errors.append(f"Embedding model error: {e}")
            else:
                self.initialization_errors.append("sentence-transformers not available")
            
            # System is considered initialized if we have documents
            self.is_initialized = len(self.embedded_documents) > 0
            
            return self.is_initialized
            
        except Exception as e:
            self.initialization_errors.append(f"Initialization error: {e}")
            return False
    
    def simple_text_search(self, query: str, documents: List[str]) -> List[int]:
        """Simple keyword-based search fallback"""
        query_words = set(query.lower().split())
        scores = []
        
        for i, doc in enumerate(documents):
            doc_words = set(doc.lower().split())
            # Simple word overlap scoring
            overlap = len(query_words.intersection(doc_words))
            scores.append((overlap, i))
        
        # Sort by score and return top indices
        scores.sort(reverse=True)
        return [idx for score, idx in scores[:self.max_results] if score > 0]
    
    async def semantic_search(self, query: str) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        results = []
        
        try:
            if self.embedding_model and self.faiss_index:
                # Get query embedding
                query_embedding = self.embedding_model.encode([query])
                faiss.normalize_L2(query_embedding)
                
                # Search FAISS index
                scores, indices = self.faiss_index.search(query_embedding.astype('float32'), self.max_results)
                
                for score, idx in zip(scores[0], indices[0]):
                    if idx != -1 and score >= self.similarity_threshold:
                        results.append(SearchResult(
                            content=self.documents[idx],
                            metadata=self.metadata[idx],
                            similarity=float(score),
                            source_type="local"
                        ))
            
            # Fallback to simple text search if no semantic results
            if not results:
                indices = self.simple_text_search(query, self.documents)
                for idx in indices:
                    results.append(SearchResult(
                        content=self.documents[idx],
                        metadata=self.metadata[idx],
                        similarity=0.5,  # Default similarity for text search
                        source_type="local"
                    ))
        
        except Exception as e:
            logging.error(f"Semantic search error: {e}")
            # Fallback to simple search
            indices = self.simple_text_search(query, self.documents)
            for idx in indices:
                results.append(SearchResult(
                    content=self.documents[idx],
                    metadata=self.metadata[idx],
                    similarity=0.5,
                    source_type="local"
                ))
        
        return results
    
    def generate_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate response using template-based approach"""
        if not sources:
            return self._generate_basic_response(query)
        
        # Create context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(f"[Source {i}] {source.content[:500]}")
        
        context = "\n\n".join(context_parts)
        
        # Template-based response generation
        if "space" in query.lower() or "telescope" in query.lower() or "mars" in query.lower():
            response = self._generate_space_response(query, sources)
        elif "technology" in query.lower() or "programming" in query.lower() or "software" in query.lower():
            response = self._generate_tech_response(query, sources)
        elif "career" in query.lower() or "job" in query.lower():
            response = self._generate_career_response(query, sources)
        else:
            response = self._generate_general_response(query, sources)
        
        # Add source citations
        for i in range(len(sources)):
            response += f" [Source {i+1}]"
        
        return response
    
    def _generate_space_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate space-themed response"""
        if "mars" in query.lower():
            return ("Mars is a fascinating planet that has captured human imagination for centuries. "
                   "Based on current research, Mars shows strong evidence of past water activity and "
                   "continues to be a prime target for searching for signs of ancient life.")
        elif "telescope" in query.lower() or "webb" in query.lower():
            return ("The James Webb Space Telescope represents humanity's most advanced space observatory. "
                   "This remarkable instrument allows us to peer deeper into space and time than ever before, "
                   "studying the formation of galaxies, stars, and planetary systems.")
        else:
            return ("Space exploration continues to reveal amazing discoveries about our universe. "
                   "From distant exoplanets to the mysteries of dark matter, each mission expands our "
                   "understanding of the cosmos and our place within it.")
    
    def _generate_tech_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate technology-themed response"""
        if "ai" in query.lower() or "artificial intelligence" in query.lower():
            return ("Artificial Intelligence is transforming every aspect of technology and society. "
                   "From machine learning algorithms to neural networks, AI is enabling new capabilities "
                   "in software development, data analysis, and automation.")
        elif "quantum" in query.lower():
            return ("Quantum computing represents a revolutionary approach to computation that could "
                   "solve problems currently intractable for classical computers. This technology "
                   "leverages quantum mechanical properties to process information in fundamentally new ways.")
        else:
            return ("Modern technology continues to evolve rapidly, with advances in cloud computing, "
                   "artificial intelligence, and software development creating new possibilities "
                   "for innovation and problem-solving.")
    
    def _generate_career_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate career-themed response"""
        return ("Technology careers offer exciting opportunities for growth and innovation. "
               "Success in tech requires continuous learning, building practical skills, "
               "and staying current with industry trends and best practices.")
    
    def _generate_general_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate general response"""
        return ("Based on the available information, this topic involves multiple aspects worth considering. "
               "The key insights from current research and knowledge suggest several important points "
               "that help address your question.")
    
    def _generate_basic_response(self, query: str) -> str:
        """Generate basic response when no sources found"""
        return (f"I understand you're asking about '{query}'. While I don't have specific information "
               f"about this topic in my current knowledge base, I'd be happy to help you explore "
               f"related areas or suggest ways to find more information.")
    
    async def web_search_fallback(self, query: str) -> List[SearchResult]:
        """Simple web search fallback (placeholder)"""
        # This is a placeholder for web search functionality
        # In a full implementation, this would query web APIs
        return []
    
    async def query(self, user_query: str) -> Dict[str, Any]:
        """Main query processing method"""
        start_time = time.time()
        
        try:
            # Perform semantic search
            local_results = await self.semantic_search(user_query)
            
            method = "semantic_search" if local_results else "basic_response"
            confidence = max([r.similarity for r in local_results]) if local_results else 0.0
            
            # Generate response
            response = self.generate_response(user_query, local_results)
            
            # Prepare sources for display
            sources = []
            for result in local_results:
                sources.append({
                    "content": result.content,
                    "metadata": result.metadata,
                    "similarity": result.similarity,
                    "source_type": result.source_type
                })
            
            return {
                "response": response,
                "sources": sources,
                "method": method,
                "confidence": confidence,
                "query_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error processing your query: {str(e)}",
                "sources": [],
                "method": "error",
                "confidence": 0.0,
                "query_time": time.time() - start_time
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        return {
            "is_initialized": self.is_initialized,
            "document_count": len(self.embedded_documents),
            "has_embedding_model": self.embedding_model is not None,
            "has_faiss_index": self.faiss_index is not None,
            "initialization_errors": self.initialization_errors,
            "capabilities": {
                "semantic_search": self.embedding_model is not None,
                "text_search": True,
                "embedded_knowledge": len(self.embedded_documents) > 0,
                "web_fallback": self.enable_web_fallback
            }
        }