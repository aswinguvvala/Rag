"""
Enhanced Hybrid RAG System - Space Intelligence & Research
Streamlit Cloud-compatible RAG system with embedded knowledge base
"""

import asyncio
import time
import logging
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import json
import aiohttp
import re

# Conditional imports with fallbacks
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
    content: str
    metadata: Dict[str, Any]
    similarity: float
    source_type: str = "local"

class HybridRAGSystem:
    """Enhanced RAG system optimized for Streamlit Cloud deployment"""
    
    def __init__(self):
        # Core components
        self.embedding_model = None
        self.faiss_index = None
        self.documents = []
        self.metadata = []
        
        # Configuration with cloud optimization
        self.similarity_threshold = 0.4
        self.max_local_results = 5
        self.max_web_results = 5
        self.enable_web_fallback = True
        self.memory_mode = 'standard'  # 'standard', 'lightweight', 'minimal'
        
        # Memory management
        self.max_memory_mb = 512  # Streamlit Cloud limit approximation
        self.embedding_cache = {}  # Cache for repeated queries
        self.cache_size_limit = 50  # Maximum cached embeddings
        
        # System status with detailed tracking
        self.is_initialized = False
        self.initialization_errors = []
        self.capabilities = {
            'semantic_search': False,
            'web_search': False,
            'llm_generation': False,
            'confidence_evaluation': False,
            'document_retrieval': False
        }
        
        # Performance tracking
        self.query_count = 0
        self.cache_hits = 0
        
        # Initialize embedded knowledge base
        self._load_embedded_documents()
    
    def _load_embedded_documents(self):
        """Load embedded space exploration knowledge base"""
        self.embedded_documents = [
            {
                "content": "Black holes are among the most fascinating and mysterious objects in the universe. They are regions of spacetime where gravity is so strong that nothing, not even light, can escape once it crosses the event horizon. Black holes form when massive stars collapse at the end of their lives, creating a singularity - a point of infinite density. The event horizon is the boundary around a black hole beyond which nothing can return. Scientists have detected black holes through their gravitational effects on nearby matter and light, and recently through gravitational waves and direct imaging of their event horizons.",
                "metadata": {
                    "title": "Black Holes: The Universe's Most Mysterious Objects",
                    "category": "astronomy",
                    "source": "Space Science Knowledge Base",
                    "topics": ["black holes", "event horizon", "singularity", "gravity", "spacetime"]
                }
            },
            {
                "content": "The James Webb Space Telescope (JWST) is the most powerful space telescope ever built, launched in December 2021. It operates primarily in the infrared spectrum, allowing it to see through cosmic dust and observe the most distant galaxies in the universe. JWST has four main scientific instruments: NIRCam, NIRSpec, MIRI, and FGS/NIRISS. The telescope's 6.5-meter primary mirror is made of 18 hexagonal segments coated with gold to optimize infrared light collection. JWST has revolutionized our understanding of early galaxy formation, exoplanet atmospheres, and stellar evolution.",
                "metadata": {
                    "title": "James Webb Space Telescope: Peering Into Deep Space",
                    "category": "space_technology",
                    "source": "Space Science Knowledge Base",
                    "topics": ["James Webb", "telescope", "infrared", "galaxies", "exoplanets"]
                }
            },
            {
                "content": "Mars exploration has been a major focus of space agencies worldwide. The Red Planet has been visited by numerous robotic missions, including rovers like Curiosity, Perseverance, and the Chinese Zhurong rover. Mars has a thin atmosphere composed mostly of carbon dioxide, polar ice caps made of water and dry ice, and evidence of ancient water flows. Current missions are searching for signs of past or present microbial life, studying the planet's climate and geology, and preparing for future human missions. The Perseverance rover is collecting samples for future return to Earth.",
                "metadata": {
                    "title": "Mars Exploration: The Quest for Life on the Red Planet",
                    "category": "planetary_science",
                    "source": "Space Science Knowledge Base",
                    "topics": ["Mars", "rovers", "exploration", "life", "atmosphere", "water"]
                }
            },
            {
                "content": "The International Space Station (ISS) is humanity's permanent outpost in space, orbiting Earth at an altitude of approximately 400 kilometers. The ISS serves as a microgravity laboratory where astronauts conduct scientific experiments in biology, physics, materials science, and Earth observation. The station is a collaborative project involving NASA, Roscosmos, ESA, JAXA, and CSA. It has been continuously occupied since November 2000, making it one of humanity's greatest achievements in space exploration. The ISS completes about 16 orbits of Earth per day.",
                "metadata": {
                    "title": "International Space Station: Humanity's Home in Space",
                    "category": "space_stations",
                    "source": "Space Science Knowledge Base",
                    "topics": ["ISS", "space station", "microgravity", "experiments", "orbit"]
                }
            },
            {
                "content": "Exoplanets, or planets outside our solar system, have become one of the most exciting areas of astronomical research. Over 5,000 exoplanets have been discovered, ranging from gas giants larger than Jupiter to rocky worlds smaller than Earth. The habitable zone, or 'Goldilocks zone,' is the region around a star where liquid water could exist on a planet's surface. Notable exoplanet discoveries include Kepler-452b, Proxima Centauri b, and the TRAPPIST-1 system with seven Earth-sized planets. Advanced telescopes like JWST are now able to analyze exoplanet atmospheres for potential biosignatures.",
                "metadata": {
                    "title": "Exoplanets: Worlds Beyond Our Solar System",
                    "category": "exoplanets",
                    "source": "Space Science Knowledge Base",
                    "topics": ["exoplanets", "habitable zone", "Kepler", "TRAPPIST-1", "biosignatures"]
                }
            },
            {
                "content": "SpaceX has revolutionized space transportation with its reusable rocket technology. The Falcon 9 rocket can land its first stage booster back on Earth, dramatically reducing launch costs. The Falcon Heavy is currently the world's most powerful operational rocket, capable of sending large payloads to Mars and beyond. SpaceX's Dragon spacecraft regularly transports astronauts and cargo to the ISS. The company is developing Starship, a fully reusable super heavy-lift vehicle designed for missions to Mars and deep space exploration. SpaceX has also deployed thousands of Starlink satellites for global internet coverage.",
                "metadata": {
                    "title": "SpaceX: Pioneering Commercial Space Flight",
                    "category": "space_companies",
                    "source": "Space Science Knowledge Base",
                    "topics": ["SpaceX", "Falcon 9", "reusable rockets", "Starship", "Starlink"]
                }
            },
            {
                "content": "The Big Bang theory describes the origin and evolution of the universe from its earliest moments 13.8 billion years ago. The universe began as an extremely hot, dense singularity that rapidly expanded in an event called cosmic inflation. As the universe cooled, fundamental particles formed, followed by atoms, stars, and galaxies. Evidence for the Big Bang includes the cosmic microwave background radiation, the abundance of light elements, and the observed expansion of the universe. Dark matter and dark energy, which make up about 95% of the universe, remain mysterious components that influence cosmic evolution.",
                "metadata": {
                    "title": "The Big Bang: Origin of the Universe",
                    "category": "cosmology",
                    "source": "Space Science Knowledge Base",
                    "topics": ["Big Bang", "cosmic inflation", "cosmic microwave background", "dark matter", "dark energy"]
                }
            },
            {
                "content": "Gravitational waves are ripples in the fabric of spacetime caused by accelerating massive objects, predicted by Einstein's general relativity. The first direct detection was made by LIGO in 2015, observing waves from two merging black holes 1.3 billion light-years away. Since then, dozens of gravitational wave events have been detected, including black hole mergers, neutron star collisions, and potentially other exotic phenomena. These detections have opened a new window to study the universe, allowing us to observe cosmic events that are invisible to traditional telescopes and confirming predictions of Einstein's theory.",
                "metadata": {
                    "title": "Gravitational Waves: Listening to the Universe",
                    "category": "physics",
                    "source": "Space Science Knowledge Base",
                    "topics": ["gravitational waves", "LIGO", "Einstein", "relativity", "black hole mergers"]
                }
            }
        ]
        
        # Mark document retrieval as available
        self.capabilities['document_retrieval'] = True
    
    async def initialize(self) -> bool:
        """Initialize the enhanced RAG system with error tracking"""
        self.initialization_errors = []
        
        try:
            # Initialize embedding model with multiple fallback strategies
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Try different models in order of preference (lighter first for cloud)
                models_to_try = [
                    'paraphrase-MiniLM-L3-v2',  # Very lightweight
                    'all-MiniLM-L6-v2',        # Standard model
                    'all-MiniLM-L12-v2'        # Larger fallback
                ]
                
                for model_name in models_to_try:
                    try:
                        st.info(f"🧠 Attempting to load {model_name}...")
                        # Memory-conscious model loading
                        import gc
                        gc.collect()  # Clear memory before loading
                        
                        # Load with reduced memory footprint
                        self.embedding_model = SentenceTransformer(
                            model_name,
                            device='cpu',  # Force CPU for cloud compatibility
                            cache_folder=None  # Disable caching to save space
                        )
                        
                        # Test the model with a simple encoding
                        test_embedding = self.embedding_model.encode(["test"])
                        if test_embedding is not None and len(test_embedding) > 0:
                            self.capabilities['semantic_search'] = True
                            st.success(f"✅ Semantic search model loaded: {model_name}")
                            break
                        else:
                            raise Exception("Model loaded but failed test encoding")
                            
                    except Exception as e:
                        st.warning(f"⚠️ Failed to load {model_name}: {str(e)}")
                        self.initialization_errors.append(f"Model {model_name}: {str(e)}")
                        # Clean up failed model attempt
                        self.embedding_model = None
                        import gc
                        gc.collect()
                        continue
                
                if not self.embedding_model:
                    st.error("❌ All embedding models failed to load")
                    self.initialization_errors.append("All embedding models failed")
            else:
                self.initialization_errors.append("sentence-transformers package not available")
                st.warning("⚠️ Semantic search unavailable: missing sentence-transformers")
            
            # Initialize FAISS index with memory optimization
            if FAISS_AVAILABLE and self.embedding_model:
                try:
                    st.info("🔍 Building search index...")
                    # Check available memory before creating index
                    import psutil
                    memory_info = psutil.virtual_memory()
                    available_mb = memory_info.available / (1024 * 1024)
                    
                    if available_mb < 100:  # Less than 100MB available
                        st.warning(f"⚠️ Low memory ({available_mb:.0f}MB), using lightweight indexing")
                        await self._create_lightweight_index()
                    else:
                        await self._create_in_memory_index()
                    
                    st.success("✅ Search index created successfully")
                except ImportError:
                    # psutil not available, proceed with standard indexing
                    st.info("📊 Memory monitoring unavailable, using standard indexing")
                    await self._create_in_memory_index()
                    st.success("✅ Search index created successfully")
                except Exception as e:
                    self.initialization_errors.append(f"FAISS index: {str(e)}")
                    st.warning(f"⚠️ Advanced search unavailable: {str(e)}")
                    # Fallback to simple keyword search
                    st.info("🔄 Falling back to keyword-based search")
            else:
                self.initialization_errors.append("FAISS not available or embedding model failed")
                st.warning("⚠️ Advanced search unavailable: missing dependencies")
            
            # Initialize web search
            try:
                st.info("🌐 Initializing web search...")
                self.capabilities['web_search'] = True
                st.success("✅ Web search initialized")
            except Exception as e:
                self.initialization_errors.append(f"Web search: {str(e)}")
                st.warning(f"⚠️ Web search may be limited: {str(e)}")
            
            # Determine memory mode based on what was successfully initialized
            if self.embedding_model and self.faiss_index:
                if len(self.documents) >= len(self.embedded_documents):
                    self.memory_mode = 'standard'
                else:
                    self.memory_mode = 'lightweight'
            else:
                self.memory_mode = 'minimal'
            
            # Mark as initialized if at least basic functionality works
            if self.capabilities['document_retrieval']:
                self.is_initialized = True
                capabilities_count = sum(1 for v in self.capabilities.values() if v)
                st.success(f"🚀 IntelliSearch initialized with {capabilities_count}/5 capabilities active")
                st.info(f"📊 Memory mode: {self.memory_mode.upper()}")
                return True
            else:
                st.error("❌ Failed to initialize core document retrieval")
                return False
                
        except Exception as e:
            self.initialization_errors.append(f"Critical error: {str(e)}")
            st.error(f"❌ RAG system initialization failed: {str(e)}")
            return False
    
    async def _create_in_memory_index(self):
        """Create in-memory FAISS index from embedded documents"""
        if not self.embedding_model:
            raise Exception("Embedding model not available")
        
        try:
            # Create embeddings for all documents in batches to save memory
            documents_text = [doc["content"] for doc in self.embedded_documents]
            
            # Process in smaller batches for memory efficiency
            batch_size = 3  # Small batch size for cloud deployment
            all_embeddings = []
            
            for i in range(0, len(documents_text), batch_size):
                batch = documents_text[i:i+batch_size]
                batch_embeddings = self.embedding_model.encode(batch, show_progress_bar=False)
                all_embeddings.append(batch_embeddings)
                
                # Force garbage collection between batches
                import gc
                gc.collect()
            
            # Combine all embeddings
            embeddings = np.vstack(all_embeddings)
            
            # Create FAISS index with memory optimization
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.faiss_index.add(embeddings.astype('float32'))
            
            # Store metadata for retrieval
            self.documents = documents_text
            self.metadata = [doc["metadata"] for doc in self.embedded_documents]
            
            # Clear intermediate variables to free memory
            del all_embeddings, embeddings
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to create FAISS index: {str(e)}")
            raise e
    
    async def _create_lightweight_index(self):
        """Create lightweight index for memory-constrained environments"""
        if not self.embedding_model:
            raise Exception("Embedding model not available")
        
        try:
            # Use only first 4 documents to reduce memory usage
            limited_docs = self.embedded_documents[:4]
            documents_text = [doc["content"] for doc in limited_docs]
            
            # Create embeddings one at a time
            embeddings_list = []
            for doc_text in documents_text:
                embedding = self.embedding_model.encode([doc_text], show_progress_bar=False)
                embeddings_list.append(embedding[0])
                
                # Immediate garbage collection
                import gc
                gc.collect()
            
            embeddings = np.array(embeddings_list)
            
            # Create minimal FAISS index
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            # Normalize and add embeddings
            faiss.normalize_L2(embeddings)
            self.faiss_index.add(embeddings.astype('float32'))
            
            # Store limited metadata
            self.documents = documents_text
            self.metadata = [doc["metadata"] for doc in limited_docs]
            
            st.info(f"🔧 Lightweight index created with {len(limited_docs)} documents")
            
            # Clear memory
            del embeddings_list, embeddings
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to create lightweight index: {str(e)}")
            raise e
    
    async def query(self, query_text: str) -> Dict[str, Any]:
        """Process a query and return results"""
        start_time = time.time()
        
        try:
            # Try semantic search first if available
            if self.capabilities['semantic_search'] and self.faiss_index:
                results = await self._semantic_search(query_text)
                method = "semantic_search"
                confidence = self._calculate_confidence(results)
            else:
                # Fallback to keyword search
                results = self._keyword_search(query_text)
                method = "keyword_search"
                confidence = 0.6
            
            # Generate response using found sources
            if results:
                response = await self._generate_response(query_text, results)
                sources = [self._format_source(r, i+1) for i, r in enumerate(results[:self.max_local_results])]
            else:
                # Try web search as fallback if enabled
                if self.capabilities['web_search']:
                    web_results = await self._web_search_fallback(query_text)
                    if web_results:
                        response = await self._generate_response(query_text, web_results)
                        sources = [self._format_source(r, i+1) for i, r in enumerate(web_results)]
                        method = "web_search"
                        confidence = 0.7
                    else:
                        response = self._generate_fallback_response(query_text)
                        sources = []
                        method = "basic_response"
                        confidence = 0.3
                else:
                    response = self._generate_fallback_response(query_text)
                    sources = []
                    method = "basic_response"
                    confidence = 0.3
            
            query_time = time.time() - start_time
            
            return {
                'response': response,
                'sources': sources,
                'method': method,
                'confidence': confidence,
                'query_time': query_time,
                'total_results': len(sources)
            }
            
        except Exception as e:
            st.error(f"Query processing error: {str(e)}")
            return {
                'response': f"I apologize, but I encountered an error while processing your query: {str(e)}",
                'sources': [],
                'method': 'error',
                'confidence': 0.0,
                'query_time': time.time() - start_time,
                'total_results': 0
            }
    
    async def _semantic_search(self, query_text: str) -> List[SearchResult]:
        """Perform semantic search using FAISS with caching"""
        try:
            self.query_count += 1
            
            # Check cache first
            cache_key = hash(query_text.lower().strip())
            if cache_key in self.embedding_cache:
                query_embedding = self.embedding_cache[cache_key]
                self.cache_hits += 1
            else:
                # Create query embedding
                query_embedding = self.embedding_model.encode([query_text], show_progress_bar=False)
                
                # Cache management - remove oldest if cache is full
                if len(self.embedding_cache) >= self.cache_size_limit:
                    # Remove first item (oldest)
                    oldest_key = next(iter(self.embedding_cache))
                    del self.embedding_cache[oldest_key]
                
                # Cache the embedding
                self.embedding_cache[cache_key] = query_embedding
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(
                query_embedding.astype('float32'), 
                min(self.max_local_results, len(self.documents))  # Don't search for more than available
            )
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.documents) and score >= self.similarity_threshold:
                    results.append(SearchResult(
                        content=self.documents[idx],
                        metadata=self.metadata[idx],
                        similarity=float(score),
                        source_type="local"
                    ))
            
            return results
            
        except Exception as e:
            st.warning(f"Semantic search error: {str(e)}")
            return []
    
    def _keyword_search(self, query_text: str) -> List[SearchResult]:
        """Fallback keyword-based search"""
        try:
            query_words = set(query_text.lower().split())
            results = []
            
            for i, doc in enumerate(self.embedded_documents):
                content = doc["content"].lower()
                metadata = doc["metadata"]
                
                # Simple keyword matching
                matches = sum(1 for word in query_words if word in content)
                if matches > 0:
                    similarity = matches / len(query_words)
                    if similarity >= 0.1:  # Lower threshold for keyword search
                        results.append(SearchResult(
                            content=doc["content"],
                            metadata=metadata,
                            similarity=similarity,
                            source_type="local"
                        ))
            
            # Sort by similarity
            results.sort(key=lambda x: x.similarity, reverse=True)
            return results[:self.max_local_results]
            
        except Exception as e:
            st.warning(f"Keyword search error: {str(e)}")
            return []
    
    async def _web_search_fallback(self, query_text: str) -> List[SearchResult]:
        """Simple web search fallback"""
        try:
            # Simulate web search results for space-related queries
            if any(term in query_text.lower() for term in ['space', 'mars', 'moon', 'rocket', 'nasa', 'spacex', 'telescope', 'galaxy', 'planet']):
                return [SearchResult(
                    content=f"Web search results for '{query_text}' would appear here. This is a simulated response showcasing web integration capabilities.",
                    metadata={
                        "title": f"Web Search: {query_text}",
                        "source": "Web Search",
                        "category": "web_result",
                        "url": f"https://example.com/search?q={query_text.replace(' ', '+')}"
                    },
                    similarity=0.7,
                    source_type="web"
                )]
            return []
        except Exception:
            return []
    
    async def _generate_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate response based on retrieved sources"""
        try:
            if not sources:
                return self._generate_fallback_response(query)
            
            # Create context from sources
            context_parts = []
            for i, source in enumerate(sources[:3], 1):  # Use top 3 sources
                context_parts.append(f"[Source {i}] {source.content[:500]}...")
            
            context = "\n\n".join(context_parts)
            
            # Generate response based on query type
            if any(term in query.lower() for term in ['what is', 'define', 'explain']):
                response = self._generate_explanatory_response(query, sources)
            elif 'how' in query.lower():
                response = self._generate_procedural_response(query, sources)
            else:
                response = self._generate_informational_response(query, sources)
            
            return response
            
        except Exception as e:
            return f"I found relevant information but encountered an error generating the response: {str(e)}"
    
    def _generate_explanatory_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate explanatory response"""
        if not sources:
            return self._generate_fallback_response(query)
        
        primary_source = sources[0]
        content = primary_source.content
        
        # Extract key information
        sentences = content.split('. ')
        key_info = '. '.join(sentences[:3]) + '.'
        
        response = f"Based on the available information: {key_info}"
        
        if len(sources) > 1:
            response += f"\n\nAdditional context from other sources reveals complementary information about this topic [Source 2]."
        
        return response
    
    def _generate_procedural_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate procedural/how-to response"""
        if not sources:
            return self._generate_fallback_response(query)
        
        primary_source = sources[0]
        response = f"According to the available information [Source 1]: {primary_source.content[:400]}..."
        
        if len(sources) > 1:
            response += f"\n\nAdditional details can be found in related sources [Source 2]."
        
        return response
    
    def _generate_informational_response(self, query: str, sources: List[SearchResult]) -> str:
        """Generate general informational response"""
        if not sources:
            return self._generate_fallback_response(query)
        
        primary_source = sources[0]
        response = f"Here's what I found about your query: {primary_source.content[:400]}..."
        
        if len(sources) > 1:
            response += f"\n\nFor more comprehensive information, see additional sources [Source 2]."
        
        return response
    
    def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no sources are found"""
        return f"""I understand you're asking about "{query}". While I don't have specific information in my current knowledge base about this exact topic, I can suggest:

🔍 **For Space & Science Topics**: Try rephrasing your question or asking about related topics like black holes, space missions, telescopes, or planetary science.

🌐 **Web Search**: You might find current information by searching online for: "{query}"

💡 **Alternative**: Feel free to ask about space exploration, astronomy, NASA missions, SpaceX developments, or cosmic phenomena - these are areas where I have comprehensive information available."""
    
    def _calculate_confidence(self, sources: List[SearchResult]) -> float:
        """Calculate confidence score based on source quality"""
        if not sources:
            return 0.0
        
        avg_similarity = sum(s.similarity for s in sources) / len(sources)
        source_count_factor = min(len(sources) / 3, 1.0)  # Normalize to max 3 sources
        
        confidence = (avg_similarity * 0.7) + (source_count_factor * 0.3)
        return min(confidence, 1.0)
    
    def _format_source(self, source: SearchResult, source_num: int) -> Dict[str, Any]:
        """Format source for response"""
        return {
            'content': source.content,
            'metadata': source.metadata,
            'similarity': source.similarity,
            'source_type': source.source_type,
            'source_number': source_num
        }
    
    def configure(self, **kwargs):
        """Configure system parameters"""
        if 'similarity_threshold' in kwargs:
            self.similarity_threshold = kwargs['similarity_threshold']
        if 'enable_web_fallback' in kwargs:
            self.enable_web_fallback = kwargs['enable_web_fallback']
        if 'max_local_results' in kwargs:
            self.max_local_results = kwargs['max_local_results']
        if 'max_web_results' in kwargs:
            self.max_web_results = kwargs['max_web_results']
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information with performance metrics"""
        # Calculate memory usage if possible
        memory_info = {}
        try:
            import psutil
            process = psutil.Process()
            memory_info = {
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'memory_percent': process.memory_percent()
            }
        except (ImportError, Exception):
            memory_info = {'memory_mb': 'unavailable', 'memory_percent': 'unavailable'}
        
        # Calculate cache efficiency
        cache_hit_rate = (self.cache_hits / self.query_count) if self.query_count > 0 else 0
        
        return {
            'is_initialized': self.is_initialized,
            'capabilities': self.capabilities,
            'initialization_errors': self.initialization_errors,
            'document_count': len(self.embedded_documents),
            'has_faiss_index': self.faiss_index is not None,
            'has_embedding_model': self.embedding_model is not None,
            'memory_mode': self.memory_mode,
            'performance': {
                'query_count': self.query_count,
                'cache_hits': self.cache_hits,
                'cache_hit_rate': f"{cache_hit_rate:.2%}",
                'cache_size': len(self.embedding_cache)
            },
            **memory_info
        }
