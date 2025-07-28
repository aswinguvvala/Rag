#!/usr/bin/env python3
"""
Simple RAG System - Clean implementation of RAG + Web Search
Direct implementation: Query -> Vector Search -> Local/Web -> Ollama Response
"""

import asyncio
import aiohttp
import numpy as np
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import pickle
import os
from pathlib import Path

# Import dependencies with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ faiss not available")

try:
    from web_search_manager import UniversalWebSearchManager
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print("⚠️ web_search_manager not available")

@dataclass
class SearchResult:
    """Simple search result structure"""
    content: str
    title: str
    source: str
    similarity: float
    source_type: str  # 'local' or 'web'

class SimpleRAGSystem:
    """Clean, simple RAG system implementation"""
    
    def __init__(self):
        print("🚀 Initializing Simple RAG System...")
        
        # Core components
        self.embedding_model = None
        self.faiss_index = None
        self.documents = []
        self.document_metadata = []
        
        # Web search manager
        self.web_search_manager = None
        if WEB_SEARCH_AVAILABLE:
            self.web_search_manager = UniversalWebSearchManager()
        
        # Ollama configuration
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "llama3.2:3b"  # Default model
        
        # Search configuration
        self.similarity_threshold = 0.45  # If similarity < 0.45, use web search
        self.max_local_results = 3
        self.max_web_results = 5
        
        # Storage paths
        self.storage_dir = Path("storage/simple_rag")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_path = self.storage_dir / "faiss_index.bin"
        self.metadata_path = self.storage_dir / "metadata.pkl"
        self.documents_path = self.storage_dir / "documents.pkl"
        
        print("✅ Simple RAG System initialized")
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        print("🔧 Initializing RAG components...")
        
        try:
            # Initialize embedding model
            if not await self._init_embedding_model():
                return False
            
            # Load or create document index
            if not await self._init_document_index():
                return False
            
            # Test Ollama connection
            if not await self._test_ollama():
                print("⚠️ Ollama not available, but continuing...")
            
            print("✅ RAG System fully initialized")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def _init_embedding_model(self) -> bool:
        """Initialize sentence transformer model"""
        if not EMBEDDINGS_AVAILABLE:
            print("❌ Cannot initialize embedding model - sentence-transformers not available")
            return False
        
        try:
            print("📦 Loading sentence transformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")
            return True
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return False
    
    async def _init_document_index(self) -> bool:
        """Load existing index or create new one"""
        if not FAISS_AVAILABLE or not self.embedding_model:
            print("❌ Cannot initialize FAISS index - requirements not met")
            return False
        
        try:
            # Try to load existing index
            if self.faiss_path.exists() and self.metadata_path.exists() and self.documents_path.exists():
                print("🔄 Loading existing FAISS index...")
                self.faiss_index = faiss.read_index(str(self.faiss_path))
                
                with open(self.metadata_path, 'rb') as f:
                    self.document_metadata = pickle.load(f)
                
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                print(f"✅ Loaded {len(self.documents)} documents from existing index")
                return True
            else:
                print("🆕 Creating new document index...")
                await self._create_initial_index()
                return True
                
        except Exception as e:
            print(f"❌ Failed to initialize document index: {e}")
            return False
    
    async def _create_initial_index(self):
        """Create initial FAISS index with space-related documents"""
        print("📚 Creating initial space document collection...")
        
        # Comprehensive space-related documents
        space_documents = [
            {
                "title": "NASA Artemis Program",
                "content": "The Artemis program is NASA's ambitious plan to return humans to the Moon by 2026 and establish a sustainable lunar presence. Named after the Greek goddess of the hunt and twin sister of Apollo, Artemis aims to land the first woman and the next man on the lunar surface. The program includes the Space Launch System (SLS) rocket, the Orion spacecraft, and the Lunar Gateway space station. Artemis will serve as a stepping stone for future Mars missions and will focus on the lunar South Pole region where water ice has been detected.",
                "category": "space_missions",
                "topics": ["NASA", "Artemis", "Moon", "lunar missions", "space exploration", "SLS", "Orion"]
            },
            {
                "title": "SpaceX Starship Development",
                "content": "SpaceX's Starship is a fully reusable super heavy-lift launch vehicle designed for missions to Mars, the Moon, and beyond. Standing 120 meters tall when combined with its Super Heavy booster, Starship is the most powerful rocket ever built. The vehicle uses Raptor engines burning liquid methane and liquid oxygen, chosen for their ability to be produced on Mars. Starship has completed several test flights and is central to NASA's Artemis program as the Human Landing System for lunar missions.",
                "category": "space_technology",
                "topics": ["SpaceX", "Starship", "Mars", "reusable rockets", "Raptor engines", "Super Heavy", "lunar landing"]
            },
            {
                "title": "International Space Station Operations",
                "content": "The International Space Station (ISS) is a multinational collaborative project involving NASA, Roscosmos, ESA, JAXA, and CSA. Orbiting Earth at approximately 408 kilometers altitude, the ISS serves as a microgravity laboratory for scientific research in biology, physics, materials science, and astronomy. The station has been continuously occupied since November 2000, with crew rotations every six months. Experiments conducted on the ISS have led to advances in medicine, agriculture, and technology that benefit life on Earth.",
                "category": "space_stations",
                "topics": ["ISS", "microgravity", "space research", "international cooperation", "orbital laboratory", "Earth observation"]
            },
            {
                "title": "Mars Exploration Rovers",
                "content": "NASA's Mars exploration program has deployed several successful rovers including Spirit, Opportunity, Curiosity, and Perseverance. These robotic explorers have revolutionized our understanding of Mars geology, climate, and potential for past life. Perseverance, launched in 2020, is actively searching for signs of ancient microbial life and collecting samples for future return to Earth. The Ingenuity helicopter, deployed from Perseverance, achieved the first powered flight on another planet, opening new possibilities for aerial exploration of Mars.",
                "category": "planetary_exploration",
                "topics": ["Mars", "rovers", "Perseverance", "Curiosity", "Ingenuity", "astrobiology", "sample return"]
            },
            {
                "title": "James Webb Space Telescope Discoveries",
                "content": "The James Webb Space Telescope (JWST), launched in 2021, is the most powerful space telescope ever built. Operating at the L2 Lagrange point, JWST observes the universe in infrared light, allowing it to see through cosmic dust and study the first galaxies formed after the Big Bang. Its discoveries include detailed images of exoplanet atmospheres, star formation regions, and the most distant galaxies ever observed. JWST's data is revolutionizing our understanding of galaxy formation, stellar evolution, and planetary systems.",
                "category": "space_telescopes",
                "topics": ["JWST", "infrared astronomy", "exoplanets", "early universe", "Hubble successor", "L2 point", "cosmic observations"]
            },
            {
                "title": "Exoplanet Discovery and Characterization",
                "content": "The search for exoplanets has discovered over 5,000 worlds orbiting other stars, with potentially habitable planets in the 'Goldilocks zone' where liquid water could exist. The Kepler Space Telescope and TESS (Transiting Exoplanet Survey Satellite) have identified thousands of candidate planets using the transit method. Future missions like the Roman Space Telescope will directly image exoplanets and analyze their atmospheres for biosignatures. The discovery of potentially habitable worlds like Proxima Centauri b and TRAPPIST-1 system planets has revolutionized our understanding of planetary systems.",
                "category": "exoplanets",
                "topics": ["exoplanets", "habitable zone", "Kepler", "TESS", "biosignatures", "Proxima Centauri", "TRAPPIST-1"]
            },
            {
                "title": "Space Propulsion Technologies",
                "content": "Advanced propulsion systems are crucial for future deep space missions. Ion drives, used by missions like Dawn and Hayabusa, provide efficient long-term thrust for interplanetary travel. Nuclear thermal propulsion could reduce Mars transit times from 9 months to 3-4 months. Breakthrough Starshot proposes using light sails accelerated by lasers to reach nearby stars. Solar sails, demonstrated by missions like IKAROS and LightSail, use radiation pressure for propellantless propulsion. These technologies will enable faster, more efficient exploration of the solar system and beyond.",
                "category": "propulsion",
                "topics": ["ion propulsion", "nuclear thermal", "solar sails", "light sails", "interplanetary travel", "propulsion efficiency"]
            },
            {
                "title": "Lunar Resources and ISRU",
                "content": "The Moon contains valuable resources for future space exploration, including water ice in permanently shadowed craters at the poles, rare earth elements, and Helium-3 for potential fusion power. In-Situ Resource Utilization (ISRU) technologies aim to extract and process these materials to support sustained lunar presence. Water can be split into hydrogen and oxygen for rocket fuel, while lunar regolith can be used for construction materials. The Moon's low gravity and lack of atmosphere make it an ideal staging ground for missions to Mars and the outer solar system.",
                "category": "lunar_resources",
                "topics": ["lunar water", "ISRU", "Helium-3", "lunar mining", "space resources", "lunar base", "fuel production"]
            },
            {
                "title": "Commercial Space Industry",
                "content": "The commercial space industry has transformed space access with companies like SpaceX, Blue Origin, Virgin Galactic, and others. SpaceX's Falcon 9 reusability has dramatically reduced launch costs, while Dragon capsules provide crew transportation to the ISS. Blue Origin's New Shepard offers suborbital tourism flights. The commercial sector is developing space manufacturing, satellite constellations like Starlink, and asteroid mining ventures. This commercialization is making space more accessible and driving innovation in launch systems, spacecraft, and space services.",
                "category": "commercial_space",
                "topics": ["SpaceX", "Blue Origin", "commercial crew", "space tourism", "satellite constellations", "launch costs", "space economy"]
            },
            {
                "title": "Astrobiology and Search for Life",
                "content": "Astrobiology studies the possibility of life beyond Earth, focusing on extremophile organisms that thrive in harsh conditions similar to those on other planets. Jupiter's moon Europa and Saturn's moon Enceladus have subsurface oceans that may harbor life. Mars shows evidence of ancient water activity and organic compounds detected by rovers. The search for biosignatures in exoplanet atmospheres using telescopes like JWST could reveal signs of life around other stars. Missions like Europa Clipper and Dragonfly will directly search for signs of life in our solar system.",
                "category": "astrobiology",
                "topics": ["astrobiology", "Europa", "Enceladus", "extremophiles", "biosignatures", "Mars life", "ocean moons"]
            }
        ]
        
        # Create embeddings for all documents
        print("🔄 Creating embeddings for space documents...")
        document_texts = [doc["content"] for doc in space_documents]
        embeddings = self.embedding_model.encode(document_texts, convert_to_numpy=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)
        
        # Store documents and metadata
        self.documents = space_documents
        self.document_metadata = [{"id": i, **doc} for i, doc in enumerate(space_documents)]
        
        # Save to disk
        await self._save_index()
        
        print(f"✅ Created FAISS index with {len(space_documents)} space documents")
    
    async def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.faiss_index, str(self.faiss_path))
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.document_metadata, f)
            
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            print("💾 Index saved to disk")
        except Exception as e:
            print(f"⚠️ Failed to save index: {e}")
    
    async def _test_ollama(self) -> bool:
        """Test Ollama connection and available models"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                # Test connection
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status != 200:
                        return False
                    
                    models_data = await response.json()
                    available_models = [model['name'] for model in models_data.get('models', [])]
                    print(f"🤖 Available Ollama models: {', '.join(available_models)}")
                    
                    # Choose best available model (prioritize small models to prevent crashes)
                    preferred_models = ["llama3.2:3b", "llama3.2:1b"]
                    for model in preferred_models:
                        if model in available_models:
                            self.ollama_model = model
                            break
                    
                    print(f"✅ Using Ollama model: {self.ollama_model}")
                    return True
                    
        except Exception as e:
            print(f"⚠️ Ollama test failed: {e}")
            return False
    
    async def search_query(self, query: str) -> Dict[str, Any]:
        """Main search function - the core of the RAG system"""
        print(f"\n🔍 Processing query: '{query[:50]}...'")
        start_time = time.time()
        
        try:
            # Step 1: Convert query to embeddings
            if not self.embedding_model:
                return self._error_response("Embedding model not available")
            
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            # Step 2: Search local FAISS index
            print("📚 Searching local space documents...")
            local_results = await self._search_local(query_embedding, query)
            
            # Step 3: Decide local vs web search based on similarity
            if local_results and local_results[0].similarity >= self.similarity_threshold:
                print(f"✅ Using local results (similarity: {local_results[0].similarity:.3f})")
                search_results = local_results[:self.max_local_results]
                search_method = "local_search"
            else:
                best_similarity = local_results[0].similarity if local_results else 0.0
                print(f"🌐 Using web search (best local similarity: {best_similarity:.3f})")
                web_results = await self._search_web(query)
                search_results = web_results[:self.max_web_results]
                search_method = "web_search"
            
            if not search_results:
                return self._error_response("No search results found")
            
            # Step 4: Generate response with Ollama
            print("🤖 Generating response with Ollama...")
            response = await self._generate_ollama_response(query, search_results)
            
            processing_time = time.time() - start_time
            print(f"⚡ Query processed in {processing_time:.2f}s")
            
            return {
                "response": response,
                "sources": [{"title": r.title, "content": r.content[:200] + "...", "source": r.source, "similarity": r.similarity, "source_type": r.source_type} for r in search_results],
                "method": search_method,
                "processing_time": processing_time,
                "query": query
            }
            
        except Exception as e:
            print(f"❌ Query processing failed: {e}")
            return self._error_response(f"Query processing failed: {str(e)}")
    
    async def _search_local(self, query_embedding: np.ndarray, query: str) -> List[SearchResult]:
        """Search local FAISS index"""
        if not self.faiss_index or len(self.documents) == 0:
            print("⚠️ No local documents available")
            return []
        
        try:
            # Search FAISS index
            similarities, indices = self.faiss_index.search(query_embedding, min(self.max_local_results * 2, len(self.documents)))
            
            results = []
            for sim, idx in zip(similarities[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append(SearchResult(
                        content=doc["content"],
                        title=doc["title"],
                        source=f"Local Knowledge Base - {doc['category']}",
                        similarity=float(sim),
                        source_type="local"
                    ))
            
            return results
            
        except Exception as e:
            print(f"⚠️ Local search failed: {e}")
            return []
    
    async def _search_web(self, query: str) -> List[SearchResult]:
        """Search web using DuckDuckGo"""
        if not self.web_search_manager:
            print("⚠️ Web search not available")
            return []
        
        try:
            # Use web search manager
            web_results = await self.web_search_manager.search(query, max_results=self.max_web_results)
            
            results = []
            for result in web_results:
                # Extract content from web SearchResult object
                content = result.content if hasattr(result, 'content') and result.content else (
                    result.snippet if hasattr(result, 'snippet') and result.snippet else ""
                )
                title = result.title if hasattr(result, 'title') and result.title else "Web Result"
                url = result.url if hasattr(result, 'url') and result.url else "Web Search"
                
                results.append(SearchResult(
                    content=content[:1000] if content else "",  # Limit content size
                    title=title,
                    source=url,
                    similarity=0.8,  # Default similarity for web results
                    source_type="web"
                ))
            
            print(f"🌐 Found {len(results)} web results")
            return results
            
        except Exception as e:
            print(f"⚠️ Web search failed: {e}")
            return []
    
    async def _check_ollama_health(self) -> bool:
        """Check if Ollama service is healthy and responsive"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            print(f"🔍 Ollama health check failed: {e}")
            return False
    
    async def _generate_ollama_response(self, query: str, search_results: List[SearchResult]) -> str:
        """Generate response using Ollama with search results as context"""
        # Health check before making request
        if not await self._check_ollama_health():
            return "Ollama service is currently unavailable. Please try again in a moment or check if the Ollama service is running."
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Prepare context from search results
                context_parts = []
                for i, result in enumerate(search_results, 1):
                    # Limit individual context size to prevent token overflow
                    content = result.content[:800] if result.content else ""
                    context_parts.append(f"[Source {i}] {result.title}\n{content}\n")
                
                context = "\n".join(context_parts)
                
                # Limit total context size for better Ollama performance
                if len(context) > 4000:
                    context = context[:4000] + "\n[Context truncated for performance]"
                
                # Create confident, direct prompt
                prompt = f"""Answer the user's question directly and confidently based on the provided information. When sources clearly state facts (like 'Team A defeated Team B'), respond definitively ('Team A won'). Only mention uncertainty if sources genuinely contradict each other or information is missing.

CONTEXT:
{context}

QUESTION: {query}

Provide a clear, direct answer. Cite sources using [Source X] format when relevant."""

                # Call Ollama API with appropriate timeout
                timeout = 120 if attempt == 0 else 180  # Increase timeout on retry
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    payload = {
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,  # More decisive, less random
                            "top_p": 0.8,        # More focused responses
                            "max_tokens": 600    # Force conciseness
                        }
                    }
                    
                    async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            generated_response = result.get("response", "").strip()
                            
                            if generated_response:
                                return generated_response
                            else:
                                print(f"⚠️ Ollama returned empty response on attempt {attempt + 1}")
                                if attempt < max_retries:
                                    continue
                                return "I received your request but couldn't generate a meaningful response. Please try rephrasing your question."
                        else:
                            print(f"⚠️ Ollama HTTP error {response.status} on attempt {attempt + 1}")
                            if attempt < max_retries:
                                await asyncio.sleep(2)  # Brief delay before retry
                                continue
                            return f"Ollama service error (HTTP {response.status}). Please try again later."
                
            except asyncio.TimeoutError:
                print(f"⚠️ Ollama timeout on attempt {attempt + 1}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                return "The request timed out while processing. This might be due to a complex query or high server load. Please try a simpler question or wait a moment before trying again."
            
            except Exception as e:
                print(f"⚠️ Ollama generation failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                return f"I found relevant information but couldn't generate a response due to a technical issue: {str(e)}. Please check that Ollama is running and try again."
        
        # This shouldn't be reached, but just in case
        return "Unable to generate response after multiple attempts. Please try again later."
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "response": f"Error: {message}",
            "sources": [],
            "method": "error",
            "processing_time": 0,
            "query": ""
        }

# Test function
async def test_simple_rag():
    """Test the simple RAG system"""
    print("🧪 Testing Simple RAG System...")
    
    rag = SimpleRAGSystem()
    
    if await rag.initialize():
        # Test query
        result = await rag.search_query("What is the Artemis program?")
        print(f"\n📊 Test Result:")
        print(f"Response: {result['response'][:200]}...")
        print(f"Method: {result['method']}")
        print(f"Sources: {len(result['sources'])}")
        print(f"Time: {result['processing_time']:.2f}s")
    else:
        print("❌ RAG system initialization failed")

if __name__ == "__main__":
    asyncio.run(test_simple_rag())